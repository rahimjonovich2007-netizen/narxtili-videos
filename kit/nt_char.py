"""nt_char: an animated, rigged "host" character (flat-vector bust, premium shading) for Narx Tili reels.

    from nt_char import Host, speech_env, EXPR
    host = Host(track=[(0.0, "neutral", dict(cx=540, by=1440, sc=0.95)), (1.0, "worried", {}, 0.4), ...],
                env=speech_env(f"{D}/work/voice_st.wav"), props=[...], mods=[...])
    host.draw(cv, t)               # draws the character (idle breathing, blinking, lip-sync from the voice) on the RGBA canvas

A track key is (t_arrive, preset-or-dict, overrides-dict, transition_seconds[, ease]).  The state is held until
t_arrive - transition, then eased to the new state, so reactions are snappy.  Everything numeric is interpolated:
expression (brow, tilt, eo, lx, ly, smile, mo, mw, blush, sweat), pose (hand targets, lean, head_*), placement (cx, by, sc, al).
Local coordinates: layer is CW x CH (640 x 700); head centre (320, 215); shoulders (175, 410) and (465, 410).
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from nt_kit import W, H, clamp, lerp, ease_in_out, ease_out_back, ease_out_cubic, put

CW, CH, SS = 640, 700, 2
OX = 100
LW = CW + 2 * OX

PALETTES = {
    # warm skin, dark hair, charcoal blazer, cream shirt, gold tie  (house look of the host)
    "ali": dict(skin=(244, 194, 154), skin_d=(222, 152, 118), skin_l=(255, 228, 196), hair=(34, 26, 26), hair_l=(110, 90, 84),
                jacket=(42, 47, 64), jacket_d=(26, 29, 40), jacket_l=(70, 78, 102), shirt=(247, 243, 233), shirt_d=(206, 200, 188),
                tie=(244, 196, 92), tie_d=(176, 124, 36), iris=(66, 40, 26), iris_l=(158, 104, 56), lip=(198, 108, 98), lip_d=(160, 82, 76),
                rim=(255, 206, 120), rim2=(120, 210, 230)),
    # Sirli Hikoyalar cast.  outfit: suit | blazer | hoodie;  hair_style: quiff | girl
    "jasur": dict(skin=(226, 170, 128), skin_d=(198, 132, 96), skin_l=(247, 208, 172), hair=(28, 22, 26), hair_l=(96, 84, 92),
                  jacket=(226, 116, 46), jacket_d=(146, 66, 24), jacket_l=(255, 164, 92), shirt=(238, 232, 220), shirt_d=(192, 184, 170),
                  tie=(255, 238, 204), tie_d=(204, 184, 142), iris=(70, 44, 28), iris_l=(150, 100, 56), lip=(190, 104, 92), lip_d=(150, 78, 70),
                  rim=(255, 206, 120), rim2=(110, 196, 240), outfit="hoodie", hair_style="quiff"),
    "malika": dict(skin=(238, 188, 150), skin_d=(210, 150, 114), skin_l=(253, 224, 192), hair=(58, 34, 30), hair_l=(140, 96, 76),
                   jacket=(40, 148, 150), jacket_d=(20, 88, 92), jacket_l=(90, 200, 194), shirt=(248, 242, 230), shirt_d=(204, 196, 184),
                   tie=(232, 66, 92), tie_d=(160, 38, 60), iris=(58, 84, 52), iris_l=(138, 172, 98), lip=(212, 96, 108), lip_d=(166, 66, 82),
                   rim=(255, 206, 120), rim2=(110, 196, 240), outfit="blazer", hair_style="girl"),
}

BASE = dict(brow=0.0, tilt=0.0, asym=0.0, eo=1.0, wink=0.0, lx=0.0, ly=0.0, smile=0.1, mo=0.0, mw=1.0, blush=0.0, sweat=0.0,
            head_tilt=0.0, head_dx=0.0, head_dy=0.0, lean=0.0, bob=0.0,
            lhx=138.0, lhy=748.0, rhx=502.0, rhy=748.0, lg=0.0, rg=0.0, lpa=0.0, rpa=0.0,
            cx=540.0, by=1440.0, sc=1.0, al=1.0, rise=0.0, rim=1.0)


def _ex(**kw):
    d = dict(BASE)
    d.update(kw)
    return d


EXPR = {
    "neutral": dict(),
    "calm": dict(smile=0.35, eo=0.9),
    "worried": dict(brow=0.45, tilt=1.0, smile=-0.75, eo=1.0, sweat=0.9, mw=0.9),
    "panic": dict(brow=0.9, tilt=1.0, smile=-0.5, eo=1.22, mo=0.45, mw=0.85, sweat=1.0),
    "shock": dict(brow=1.0, tilt=0.3, smile=-0.1, eo=1.25, mo=0.85, mw=0.62, lx=0, ly=0),
    "think": dict(brow=0.3, asym=-0.5, tilt=0.2, smile=-0.15, eo=0.9, lx=-0.7, ly=-0.8, mw=0.7, head_tilt=-5),
    "smile": dict(brow=0.2, smile=0.85, eo=0.9, blush=0.6),
    "grin": dict(brow=0.35, smile=1.0, eo=0.9, mo=0.38, mw=1.05, blush=0.7),
    "relief": dict(brow=0.15, tilt=0.5, smile=0.7, eo=0.22, blush=0.6, head_tilt=3),
    "wink": dict(brow=0.3, smile=0.95, eo=0.95, wink=1.0, blush=0.7, mo=0.2),
    "no": dict(brow=0.1, tilt=-0.4, smile=-0.5, eo=0.9),
    "awe": dict(brow=0.85, tilt=0.5, smile=0.3, eo=1.2, mo=0.7, mw=0.8, blush=0.4),
}


def state_of(x):
    if isinstance(x, str):
        return _ex(**EXPR[x])
    return _ex(**x)


def speech_env(wav_path, fps=30, smooth=3):
    """mouth openness 0..1 from the voice track (RMS per frame, normalised, lightly smoothed)"""
    from scipy.io import wavfile
    sr, x = wavfile.read(wav_path)
    x = x.astype(np.float32)
    if x.ndim > 1:
        x = x.mean(axis=1)
    hop = int(sr / fps)
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    rms = rms / (np.percentile(rms, 95) + 1e-9)
    env = np.clip(rms, 0, 1.0) ** 0.75
    if smooth > 1:
        k = np.ones(smooth) / smooth
        env = np.convolve(env, k, mode="same")
    env = np.where(rms < 0.06, 0.0, env)

    def f(t):
        i = t * fps
        i0 = int(math.floor(i))
        if i0 < 0 or i0 + 1 >= len(env):
            return 0.0
        return float(lerp(env[i0], env[i0 + 1], i - i0))
    return f


# ----------------------------------------------------------------------------- drawing helpers (v2: volumetric shading)
from scipy.ndimage import gaussian_filter

HS = 2          # head supersampling
BS = 2          # body supersampling


def _arr(im):
    return np.asarray(im, np.float32)


def _alpha(im):
    return np.asarray(im.getchannel("A"), np.float32) / 255.0


def _smooth(pts, n=10, closed=True):
    """Catmull-Rom spline through pts"""
    out = []
    N = len(pts)
    rng = range(N) if closed else range(N - 1)
    for i in rng:
        p0, p1, p2, p3 = pts[(i - 1) % N], pts[i], pts[(i + 1) % N], pts[(i + 2) % N]
        for k in range(n):
            u = k / n
            u2, u3 = u * u, u * u * u
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u3) for j in (0, 1)))
    return out


def pillow(im, sigma, strength=0.5, light=(-0.55, -0.8), spec=0.0, sh_col=(30, 16, 28), hi_col=(255, 244, 228), down=4):
    """volumetric shading from the blurred alpha (a soft 'pillow' height map): shadow away from the light, highlight toward it.
    Works on the bounding box of the shape only (big speed-up on the full-size layers)."""
    bb = im.getchannel("A").getbbox()
    if bb is None:
        return im
    pad = int(sigma * 4) + 8
    box = (max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad))
    if (box[2] - box[0]) * (box[3] - box[1]) > 0.8 * im.width * im.height:
        return _pillow_core(im, sigma, strength, light, spec, sh_col, hi_col, down)
    res = _pillow_core(im.crop(box), sigma, strength, light, spec, sh_col, hi_col, down)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(res, (box[0], box[1]))
    return out


def _pillow_core(im, sigma, strength, light, spec, sh_col, hi_col, down):
    a = _alpha(im)
    H_, W_ = a.shape
    sm = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((max(2, W_ // down), max(2, H_ // down)), Image.BILINEAR), np.float32) / 255
    h = gaussian_filter(sm, sigma / down)
    gy, gx = np.gradient(h)
    s = sigma / down * 1.7
    nx, ny = -gx * s, -gy * s
    ln = np.sqrt(nx * nx + ny * ny + 1.0)
    lx, ly, lz = light[0], light[1], 0.85
    lln = math.sqrt(lx * lx + ly * ly + lz * lz)
    lam = (nx * lx + ny * ly + lz) / ln / lln
    sh = lam - lz / lln
    sh = np.asarray(Image.fromarray(sh.astype(np.float32), "F").resize((W_, H_), Image.BICUBIC))
    arr = _arr(im).copy()
    neg = np.clip(-sh * 2.4, 0, 1)[..., None]
    pos = np.clip(sh * 2.4, 0, 1)[..., None]
    rgb = arr[..., :3]
    rgb = rgb * (1 - neg * strength) + np.array(sh_col, np.float32) * neg * strength
    if spec > 0:
        rgb = rgb + (np.array(hi_col, np.float32) - rgb) * pos * spec
    arr[..., :3] = np.clip(rgb, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def _clip_to(layer, mask_im):
    """multiply layer alpha with another image's alpha (only inside the mask's bounding box)"""
    bb = mask_im.getchannel("A").getbbox()
    if bb is None:
        return Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sub = layer.crop(bb)
    arr = _arr(sub).copy()
    arr[..., 3] *= _alpha(mask_im.crop(bb))
    res = Image.fromarray(arr.astype(np.uint8), "RGBA")
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.paste(res, (bb[0], bb[1]))
    return out


def _soft(size1, draw_fn, blur, S):
    """draw soft shapes at 1x resolution, blur there (cheap), upscale to S x"""
    im = Image.new("RGBA", size1, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(im))
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return im.resize((size1[0] * S, size1[1] * S), Image.BICUBIC)


def _capS(d, p0, p1, w, fill, S):
    d.line([(p0[0] * S, p0[1] * S), (p1[0] * S, p1[1] * S)], fill=fill, width=int(w * S))
    r = w * S / 2
    for p in (p0, p1):
        d.ellipse([p[0] * S - r, p[1] * S - r, p[0] * S + r, p[1] * S + r], fill=fill)


def _polyS(d, pts, fill, S):
    d.polygon([(x * S, y * S) for x, y in pts], fill=fill)


def _ellS(d, cx, cy, rx, ry, fill, S, outline=None, ow=0):
    d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=fill, outline=outline, width=int(ow * S))


def _bez(p0, p1, p2, n=20):
    out = []
    for i in range(n + 1):
        u = i / n
        out.append(((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
                    (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]))
    return out


def _ik(S_, T, l1, l2, side, cxm=320):
    dx, dy = T[0] - S_[0], T[1] - S_[1]
    d = max(abs(l1 - l2) + 2.0, min(l1 + l2 - 1.0, math.hypot(dx, dy)))
    th = math.atan2(dy, dx)
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    al = math.acos(clamp(c, -1, 1))
    cands = []
    for sgn in (-1, 1):
        a = th + sgn * al
        cands.append((S_[0] + l1 * math.cos(a), S_[1] + l1 * math.sin(a)))
    E = max(cands, key=lambda p: 0.5 * abs(p[0] - cxm) + 0.9 * p[1])
    wd = (T[0] - E[0], T[1] - E[1])
    ln = math.hypot(*wd) or 1.0
    return E, (E[0] + wd[0] / ln * l2, E[1] + wd[1] / ln * l2)


def _face_outline(cx, cy, n=120):
    pts = []
    for i in range(n):
        th = 2 * math.pi * i / n
        c, s = math.cos(th), math.sin(th)
        if s > 0:
            p = 2.7
            c2 = math.copysign(abs(c) ** (2 / p), c)
            s2 = abs(s) ** (2 / p)
            k = 1 - 0.20 * (s ** 1.4)
            pts.append((cx + 112 * c2 * k, cy + 124 * s2))
        else:
            pts.append((cx + 112 * c, cy + 118 * s))
    return pts


def _head(st, pal, mouth_open):
    """head layer (380 x 400 local), head centre (190, 190); supersampled x3"""
    S = HS
    HW, HH = 380, 400
    cx, cy = 190, 190
    skin, skin_d, skin_l = pal["skin"], pal["skin_d"], pal["skin_l"]
    hair, hair_l = pal["hair"], pal["hair_l"]
    size = (HW * S, HH * S)
    out = Image.new("RGBA", size, (0, 0, 0, 0))

    # ---------------------------------------------------------------- hair (back mass)
    back = Image.new("RGBA", size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(back)
    _ellS(bd, cx, cy - 22, 130, 140, hair + (255,), S)
    girl = pal.get("hair_style") == "girl"
    if girl:                                              # long hair: fuller crown + two panels falling behind the shoulders
        _ellS(bd, cx, cy - 26, 146, 158, hair + (255,), S)
        for sx in (-1, 1):
            _polyS(bd, [(cx + sx * 96, cy - 20), (cx + sx * 150, cy + 10), (cx + sx * 152, cy + 150), (cx + sx * 134, cy + 196),
                        (cx + sx * 96, cy + 176), (cx + sx * 80, cy + 60)], hair + (255,), S)
    back = pillow(back, 26 * S, 0.6, light=(-0.4, -0.9), spec=0.35, sh_col=(8, 6, 8), hi_col=hair_l, down=6)
    out.alpha_composite(back)

    # ---------------------------------------------------------------- ears
    ears = Image.new("RGBA", size, (0, 0, 0, 0))
    ed = ImageDraw.Draw(ears)
    for sx in (-1, 1):
        _ellS(ed, cx + sx * 112, cy + 8, 22, 32, skin_d + (255,), S)
    ears = pillow(ears, 9 * S, 0.5, spec=0.15, sh_col=(120, 60, 50), down=3)
    out.alpha_composite(ears)
    inner = _soft((HW, HH), lambda d: [d.ellipse([cx + sx * 112 - 9, cy - 6, cx + sx * 112 + 9, cy + 26], fill=pal["lip"] + (110,)) for sx in (-1, 1)], 3, S)
    out.alpha_composite(inner)

    # ---------------------------------------------------------------- face skin with volume
    face = Image.new("RGBA", size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(face)
    fo = _face_outline(cx, cy)
    fd.polygon([(x * S, y * S) for x, y in fo], fill=skin + (255,))
    face = pillow(face, 34 * S, 0.40, light=(-0.45, -0.8), spec=0.30, sh_col=skin_d, hi_col=skin_l, down=6)
    # soft anatomy overlays (1x, blurred)
    sm = st["smile"]

    def anat(d):
        for sx in (-1, 1):
            d.ellipse([cx + sx * 44 - 38, cy - 28, cx + sx * 44 + 38, cy + 12], fill=skin_d + (26,))          # eye sockets
            d.ellipse([cx + sx * 74 - 30, cy + 34, cx + sx * 74 + 30, cy + 70], fill=(244, 128, 112, int(18 + 110 * st["blush"])))   # cheeks
            d.ellipse([cx + sx * 25 - 8, cy + 30, cx + sx * 25 + 8, cy + 58], fill=skin_d + (26,))           # nose sides
        d.ellipse([cx - 56, cy + 108, cx + 56, cy + 142], fill=skin_d + (60,))                                  # under chin / jaw
        d.ellipse([cx - 36, cy + 56, cx + 36, cy + 82], fill=skin_d + (34,))                                     # under nose
    face = Image.alpha_composite(face, _clip_to(_soft((HW, HH), anat, 7, S), face))

    def hl(d):
        d.ellipse([cx - 26, cy - 64, cx + 26, cy - 18], fill=skin_l + (34,))        # forehead sheen
        d.ellipse([cx - 84, cy + 22, cx - 48, cy + 54], fill=skin_l + (30,))
        d.ellipse([cx + 48, cy + 22, cx + 84, cy + 54], fill=skin_l + (30,))
        d.ellipse([cx - 10, cy + 33, cx + 10, cy + 47], fill=skin_l + (90,))        # nose tip
    face = Image.alpha_composite(face, _clip_to(_soft((HW, HH), hl, 10, S), face))
    out.alpha_composite(face)
    d = ImageDraw.Draw(out)

    # ---------------------------------------------------------------- nose details
    for sx in (-1, 1):
        d.arc([(cx + sx * 11 - 7) * S, (cy + 44) * S, (cx + sx * 11 + 7) * S, (cy + 54) * S], 20 if sx < 0 else 160, 200 if sx < 0 else 340, fill=skin_d + (200,), width=int(3 * S))
    d.arc([(cx - 14) * S, (cy + 30) * S, (cx + 14) * S, (cy + 54) * S], 25, 155, fill=skin_d + (230,), width=int(3.5 * S))

    # ---------------------------------------------------------------- eyes (clean cartoon: white + big dark iris + highlights)
    for sx, k in ((-1, 0), (1, 1)):
        ex, ey = cx + sx * 46, cy - 2
        eo = clamp(st["eo"] * (1 - (st["wink"] if k else 0.0)), 0, 1.3)
        if eo < 0.18:                                                       # closed eye: lash line
            if sm > 0.35:
                d.arc([(ex - 22) * S, (ey - 10) * S, (ex + 22) * S, (ey + 14) * S], 200, 340, fill=hair + (255,), width=int(6.5 * S))
            else:
                d.arc([(ex - 22) * S, (ey - 14) * S, (ex + 22) * S, (ey + 8) * S], 18, 162, fill=hair + (255,), width=int(6.5 * S))
            continue
        rx, ry = 24, 22 * eo
        sc = Image.new("RGBA", size, (0, 0, 0, 0))
        scd = ImageDraw.Draw(sc)
        _ellS(scd, ex, ey, rx, ry, (252, 250, 247, 255), S)
        sh = _soft((HW, HH), lambda dd: dd.ellipse([ex - rx - 4, ey - ry - 22, ex + rx + 4, ey - ry * 0.3], fill=(90, 60, 60, 120)), 4, S)
        sc = Image.alpha_composite(sc, _clip_to(sh, sc))
        ix, iy = ex + st["lx"] * 8, ey + st["ly"] * 6
        ir = 15.5
        yy, xx = np.mgrid[0:int(ir * 2 * S) + 2, 0:int(ir * 2 * S) + 2].astype(np.float32)
        c0 = ir * S
        rr = np.sqrt((xx - c0) ** 2 + (yy - c0) ** 2) / c0
        base = np.array(pal["iris"], np.float32)
        light_ = np.array(pal["iris_l"], np.float32)
        t_ = np.clip((rr - 0.25) / 0.7, 0, 1)[..., None]
        col = light_ * (1 - t_) + base * t_
        col = np.where((rr < 0.40)[..., None], np.array((14, 10, 10), np.float32), col)
        al_ = np.clip((1 - rr) * c0 / 1.5, 0, 1)
        iris = Image.fromarray(np.dstack([col, al_ * 255]).astype(np.uint8), "RGBA")
        irl = Image.new("RGBA", size, (0, 0, 0, 0))
        irl.alpha_composite(iris, (int((ix - ir) * S), int((iy - ir) * S)))
        irl = _clip_to(irl, sc)
        sc.alpha_composite(irl)
        scd = ImageDraw.Draw(sc)
        hx_, hy_ = ix - 5.5, iy - 6
        scd.ellipse([(hx_ - 4.2) * S, (hy_ - 4.2) * S, (hx_ + 4.2) * S, (hy_ + 4.2) * S], fill=(255, 255, 255, 250))
        scd.ellipse([(ix + 5) * S - 2 * S, (iy + 5.5) * S - 2 * S, (ix + 5) * S + 2 * S, (iy + 5.5) * S + 2 * S], fill=(255, 255, 255, 150))
        out.alpha_composite(sc)
        d = ImageDraw.Draw(out)
        d.arc([(ex - rx) * S, (ey - ry) * S, (ex + rx) * S, (ey + ry) * S], 190, 350, fill=hair + (255,), width=int(5 * S))

    # ---------------------------------------------------------------- eyebrows (tapered)
    for sx, k in ((-1, 0), (1, 1)):
        raise_ = st["brow"] + (st["asym"] if k else 0.0)
        by_ = cy - 47 - raise_ * 17
        bx = cx + sx * 46
        L = 33
        inner = (bx - sx * L, by_ - st["tilt"] * 12)
        outer = (bx + sx * L, by_ + st["tilt"] * 9 + 1)
        mid = ((inner[0] + outer[0]) / 2, (inner[1] + outer[1]) / 2 - 4)
        # polygon with thickness profile
        def side(p, th):
            return (p[0], p[1] - th)
        top = _bez((inner[0], inner[1] - 7), (mid[0], mid[1] - 9), (outer[0], outer[1] - 3.5), 12)
        bot = _bez((outer[0], outer[1] + 3.5), (mid[0], mid[1] + 5), (inner[0], inner[1] + 7), 12)
        bl = Image.new("RGBA", size, (0, 0, 0, 0))
        _polyS(ImageDraw.Draw(bl), top + bot, hair + (255,), S)
        bl = bl.filter(ImageFilter.GaussianBlur(0.8 * S))
        out.alpha_composite(bl)
    d = ImageDraw.Draw(out)

    # ---------------------------------------------------------------- mouth
    mo = clamp(mouth_open, 0, 1)
    hw = 44 * st["mw"] * (1 + 0.14 * max(0, sm))
    my = cy + 76
    yc = my - sm * 17
    ym = my + (2 if sm >= 0 else -10 * -sm) + (6 * sm if sm > 0 else 0)
    up = _bez((cx - hw, yc), (cx, ym), (cx + hw, yc), 24)
    lip, lip_d = pal["lip"], pal["lip_d"]
    if mo > 0.06:
        lw_ = my + mo * 52 + max(0, sm) * 10 + 4
        lo = _bez((cx + hw, yc), (cx, lw_ + mo * 18 + 4), (cx - hw, yc), 24)
        poly = up + lo
        mouth = Image.new("RGBA", size, (0, 0, 0, 0))
        md = ImageDraw.Draw(mouth)
        _polyS(md, poly, (66, 20, 28, 255), S)
        tg = _bez((cx - hw * 0.6, lw_ + 8), (cx, lw_ - 24 + mo * 10), (cx + hw * 0.6, lw_ + 8), 16)
        tg_layer = Image.new("RGBA", size, (0, 0, 0, 0))
        _polyS(ImageDraw.Draw(tg_layer), tg + [(cx + hw * 0.6, lw_ + 40), (cx - hw * 0.6, lw_ + 40)], (226, 112, 120, 255), S)
        tg_layer = tg_layer.filter(ImageFilter.GaussianBlur(1.5 * S))
        mouth.alpha_composite(tg_layer)
        md = ImageDraw.Draw(mouth)
        th = min(17, 6 + mo * 24)
        teeth = up + [(x, y + th) for x, y in reversed(up)]
        _polyS(md, teeth, (250, 248, 244, 255), S)
        _polyS(md, [(x, y + th - 5) for x, y in up] + [(x, y + th) for x, y in reversed(up)], (226, 220, 214, 255), S)
        mm = Image.new("RGBA", size, (0, 0, 0, 0))
        _polyS(ImageDraw.Draw(mm), poly, (255, 255, 255, 255), S)
        mouth = _clip_to(mouth, mm)
        out.alpha_composite(mouth)
        d = ImageDraw.Draw(out)
        d.line([(x * S, y * S) for x, y in up], fill=lip_d + (255,), width=int(5.5 * S), joint="curve")
        d.line([(x * S, y * S) for x, y in lo], fill=lip + (255,), width=int(6.5 * S), joint="curve")
    else:
        d.line([(x * S, y * S) for x, y in up], fill=lip_d + (255,), width=int(6.5 * S), joint="curve")
        if sm > 0.5:      # closed smile: soft lower lip
            lo2 = _bez((cx + hw * 0.92, yc + 1), (cx, my + 22 + sm * 6), (cx - hw * 0.92, yc + 1), 20)
            lipl = Image.new("RGBA", size, (0, 0, 0, 0))
            _polyS(ImageDraw.Draw(lipl), up + lo2, lip + (150,), S)
            out.alpha_composite(lipl.filter(ImageFilter.GaussianBlur(1.2 * S)))
            d = ImageDraw.Draw(out)
            d.line([(x * S, y * S) for x, y in up], fill=lip_d + (255,), width=int(6.5 * S), joint="curve")
        for sx2 in (-1, 1):
            _ellS(d, cx + sx2 * hw, yc, 3.2, 3.2, lip_d + (255,), S)

    # ---------------------------------------------------------------- hair (front)
    fr = [(-116, 10), (-128, -40), (-112, -102), (-66, -140), (-4, -154), (58, -148), (106, -122), (128, -68), (122, 8),
          (108, -30), (96, -52), (70, -70), (32, -78), (-4, -72), (-48, -76), (-90, -44)]
    if girl:                                         # side-swept fringe, locks framing the face down to the shoulders
        fr = [(-128, 40), (-136, -40), (-116, -108), (-64, -146), (0, -158), (62, -150), (112, -120), (134, -64), (132, 40),
              (112, -6), (98, -44), (62, -82), (14, -96), (-30, -86), (-72, -58), (-104, -20)]
    frp = [(cx + x, cy + y) for x, y in _smooth(fr, 8)]
    hr = Image.new("RGBA", size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hr)
    hd.polygon([(x * S, y * S) for x, y in frp], fill=hair + (255,))
    if girl:
        for sx in (-1, 1):
            _polyS(hd, [(cx + sx * 126, cy - 10), (cx + sx * 138, cy + 90), (cx + sx * 128, cy + 176), (cx + sx * 104, cy + 150),
                        (cx + sx * 100, cy + 60), (cx + sx * 104, cy - 30)], hair + (255,), S)
    else:
        for sx in (-1, 1):                           # sideburns
            _polyS(hd, [(cx + sx * 124, cy + 4), (cx + sx * 112, cy + 52), (cx + sx * 100, cy + 14), (cx + sx * 102, cy - 40)], hair + (255,), S)
    hr = pillow(hr, 18 * S, 0.55, light=(-0.4, -0.9), spec=0.5, sh_col=(6, 4, 6), hi_col=hair_l, down=6)
    # soft highlight sweeping over the quiff
    strk = Image.new("RGBA", size, (0, 0, 0, 0))
    sd_ = ImageDraw.Draw(strk)
    crv = _smooth([(cx - 84, cy - 112), (cx - 30, cy - 146), (cx + 40, cy - 148), (cx + 96, cy - 118)], 10, closed=False)
    sd_.line([(x * S, y * S) for x, y in crv], fill=hair_l + (170,), width=int(15 * S), joint="curve")
    strk = _clip_to(strk.filter(ImageFilter.GaussianBlur(4.5 * S)), hr)
    hr.alpha_composite(strk)
    # soft shadow of the fringe on the forehead
    shadow = _soft((HW, HH), lambda dd: dd.polygon([(x, y + 9) for x, y in frp], fill=(110, 50, 40, 70)), 6, S)
    out.alpha_composite(_clip_to(shadow, face))
    out.alpha_composite(hr)
    if girl:                                         # hair clip
        clip = Image.new("RGBA", size, (0, 0, 0, 0))
        cd_ = ImageDraw.Draw(clip)
        _polyS(cd_, [(cx + 84, cy - 112), (cx + 124, cy - 92), (cx + 118, cy - 70), (cx + 80, cy - 92)], pal["tie"] + (255,), S)
        clip = pillow(clip, 5 * S, 0.5, spec=0.5, sh_col=pal["tie_d"], hi_col=(255, 220, 226), down=2)
        out.alpha_composite(clip)

    # ---------------------------------------------------------------- sweat
    if st["sweat"] > 0.03:
        k = st["sweat"]
        tx, ty = cx + 106, cy - 66 + 20 * math.sin(st.get("_t", 0) * 2.2)
        s_ = 0.62 + 0.38 * k
        dr_ = ImageDraw.Draw(out)
        _polyS(dr_, [(tx, ty - 28 * s_), (tx - 13 * s_, ty + 4 * s_), (tx + 13 * s_, ty + 4 * s_)], (140, 208, 255, int(235 * k)), S)
        _ellS(dr_, tx, ty + 6 * s_, 13 * s_, 13 * s_, (140, 208, 255, int(235 * k)), S)
        _ellS(dr_, tx - 4 * s_, ty + 3 * s_, 3.5 * s_, 5.5 * s_, (255, 255, 255, int(220 * k)), S)
    return out


def _hand(layer_d, pal, wrist, u, g, pa, S):
    """hand in a local frame (wrist origin, u = forearm direction); g: 0 open, 1 fist, 2 point. returns centre of the hand"""
    skin = pal["skin"] + (255,)
    c, s_ = math.cos(math.radians(pa)), math.sin(math.radians(pa))
    ux, uy = u[0] * c - u[1] * s_, u[0] * s_ + u[1] * c
    vx, vy = -uy, ux

    def P(a, b):
        return (wrist[0] + ux * a + vx * b, wrist[1] + uy * a + vy * b)
    if g == 1:     # fist
        _capS(layer_d, P(6, 0), P(34, 0), 66, skin, S)
        for k in (-1.5, -0.5, 0.5, 1.5):
            _capS(layer_d, P(30, k * 15), P(44, k * 15), 17, skin, S)
        _capS(layer_d, P(14, -30), P(38, -22), 20, skin, S)
        return P(30, 0)
    if g == 2:     # pointing
        _capS(layer_d, P(6, 0), P(34, 0), 60, skin, S)
        _capS(layer_d, P(30, -2), P(88, -2), 19, skin, S)
        for k in (0.9, 1.9, 2.9):
            _capS(layer_d, P(30, k * 13), P(46, k * 13), 16, skin, S)
        _capS(layer_d, P(14, -28), P(40, -20), 20, skin, S)
        return P(88, -2)
    _capS(layer_d, P(4, 0), P(34, 0), 66, skin, S)      # open hand: palm + four fingers + thumb
    for k, ln in ((-1.5, 36), (-0.5, 44), (0.5, 42), (1.5, 33)):
        _capS(layer_d, P(30, k * 15.5), P(30 + ln, k * 15.5 + k * 2.5), 16.5, skin, S)
    _capS(layer_d, P(12, -30), P(46, -46), 20, skin, S)
    return P(50, 0)


def _torso(pal, sx, sy, S, size):
    jacket, jd, jl = pal["jacket"], pal["jacket_d"], pal["jacket_l"]
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    o = [(96, 820), (98, 560), (108, 466), (142, 418), (204, 390), (262, 376), (378, 376), (436, 390), (498, 418), (532, 466), (542, 560), (544, 820)]
    outline = [(x + sx, y + sy) for x, y in _smooth(o, 8, closed=False)]
    d.polygon([(x * S, y * S) for x, y in outline], fill=jacket + (255,))
    im = pillow(im, 56 * S, 0.7, light=(-0.55, -0.8), spec=0.14, sh_col=(8, 8, 14), hi_col=jl, down=8)
    # fabric weave + soft folds
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 1, (size[1] // 6, size[0] // 6)).astype(np.float32)
    noise = np.asarray(Image.fromarray(gaussian_filter(noise, 0.8)).resize(size, Image.BILINEAR), np.float32)
    arr = _arr(im).copy()
    arr[..., :3] = np.clip(arr[..., :3] * (1 + 0.045 * noise[..., None]), 0, 255)
    im = Image.fromarray(arr.astype(np.uint8), "RGBA")

    def folds(dd):
        for sgn in (-1, 1):
            for (x0, y0, x1, y1) in ((152, 560, 176, 700), (176, 520, 196, 640)):
                xx0, xx1 = (320 + sgn * (320 - x0) + sx), (320 + sgn * (320 - x1) + sx)
                dd.line([(xx0, y0 + sy), (xx1, y1 + sy)], fill=(0, 0, 0, 70), width=7)
        dd.ellipse([210 + sx, 470 + sy, 262 + sx, 560 + sy], fill=(255, 255, 255, 14))
    fl = _soft((size[0] // S, size[1] // S), folds, 7, S)
    im.alpha_composite(_clip_to(fl, im))
    return im


_BODY = {}


def _body_cached(pal, S, size):
    k = (id(pal), S)
    if k not in _BODY:
        _BODY[k] = _body(pal, S, size)
    return _BODY[k]


def _body(pal, S, size):
    """torso + neck + shirt + lapels + tie, rendered once at rest (shifted per frame by lean / bob)"""
    sx, sy = OX, 0
    shirt, shd = pal["shirt"], pal["shirt_d"]
    jacket, jd, jl = pal["jacket"], pal["jacket_d"], pal["jacket_l"]
    tie, tie_d = pal["tie"], pal["tie_d"]
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    im.alpha_composite(_torso(pal, sx, sy, S, size))
    # ------------------------------------------------------------ neck
    neck = Image.new("RGBA", size, (0, 0, 0, 0))
    nd = ImageDraw.Draw(neck)
    nd.rounded_rectangle([(272 + sx) * S, (292 + sy) * S, (368 + sx) * S, (404 + sy) * S], radius=int(34 * S), fill=pal["skin_d"] + (255,))
    neck = pillow(neck, 22 * S, 0.5, spec=0.1, sh_col=(120, 60, 50), down=4)
    im.alpha_composite(neck)
    outfit = pal.get("outfit", "suit")
    if outfit == "hoodie":
        # cowl collar in front of the neck base + two drawstrings
        hc = Image.new("RGBA", size, (0, 0, 0, 0))
        hdr = ImageDraw.Draw(hc)
        hdr.arc([(170 + sx) * S, (352 + sy) * S, (470 + sx) * S, (452 + sy) * S], 8, 172, fill=jacket + (255,), width=int(52 * S))
        hc = pillow(hc, 16 * S, 0.7, light=(-0.4, -0.9), spec=0.2, sh_col=jd, hi_col=jl, down=4)
        im.alpha_composite(hc)
        d = ImageDraw.Draw(im)
        for sg in (-1, 1):
            x0 = 320 + sg * 30 + sx
            d.line([(x0 * S, 432 * S), ((x0 + sg * 6) * S, 560 * S)], fill=pal["tie"] + (255,), width=int(9 * S))
            _ellS(d, x0 + sg * 6, 566 + sy, 8, 12, pal["tie_d"] + (255,), S)
        return im
    # ------------------------------------------------------------ shirt, collar, lapels, tie
    d = ImageDraw.Draw(im)
    v = Image.new("RGBA", size, (0, 0, 0, 0))
    vd = ImageDraw.Draw(v)
    _polyS(vd, [(254 + sx, 378 + sy), (386 + sx, 378 + sy), (320 + sx, 580 + sy)], shirt + (255,), S)
    v = pillow(v, 40 * S, 0.45, light=(-0.2, -1.0), sh_col=shd, down=6)
    im.alpha_composite(v)
    lap = Image.new("RGBA", size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lap)
    for sg in (-1, 1):
        def X(x):
            return 320 + sg * (320 - x) + sx
        _polyS(ld, [(X(232), 388 + sy), (X(262), 376 + sy), (X(320), 580 + sy), (X(268), 534 + sy), (X(222), 462 + sy), (X(246), 430 + sy)], jl + (255,), S)
    lap = pillow(lap, 14 * S, 0.5, light=(-0.4, -0.9), spec=0.22, sh_col=jd, hi_col=(150, 158, 182), down=4)
    im.alpha_composite(lap)
    d = ImageDraw.Draw(im)
    for sg in (-1, 1):                          # lapel edge stitching
        def X(x):
            return 320 + sg * (320 - x) + sx
        d.line([(X(240) * S, (392 + sy) * S), (X(300) * S, (540 + sy) * S)], fill=(130, 138, 162, 120), width=int(2.2 * S))
        _polyS(d, [(X(254), 374 + sy), (X(298), 390 + sy), (X(320), 446 + sy), (X(268), 420 + sy)], shirt + (255,), S)     # collar wings
        d.line([(X(254) * S, (374 + sy) * S), (X(268) * S, (420 + sy) * S), (X(320) * S, (446 + sy) * S)], fill=shd + (255,), width=int(2.2 * S))
    if outfit == "blazer":                      # no tie / pocket square: a small pendant instead
        d = ImageDraw.Draw(im)
        d.line([(300 + sx) * S, 400 * S, (320 + sx) * S, 470 * S], fill=(230, 210, 150, 255), width=int(4 * S))
        d.line([(340 + sx) * S, 400 * S, (320 + sx) * S, 470 * S], fill=(230, 210, 150, 255), width=int(4 * S))
        _ellS(d, 320 + sx, 480 + sy, 11, 11, tie + (255,), S)
        return im
    # tie (satin)
    tl = Image.new("RGBA", size, (0, 0, 0, 0))
    td = ImageDraw.Draw(tl)
    _polyS(td, [(302 + sx, 396 + sy), (338 + sx, 396 + sy), (344 + sx, 420 + sy), (296 + sx, 420 + sy)], tie + (255,), S)
    _polyS(td, [(298 + sx, 420 + sy), (342 + sx, 420 + sy), (358 + sx, 548 + sy), (320 + sx, 584 + sy), (282 + sx, 548 + sy)], tie + (255,), S)
    tl = pillow(tl, 12 * S, 0.7, light=(-0.9, -0.3), spec=0.55, sh_col=tie_d, hi_col=(255, 240, 190), down=4)
    td = ImageDraw.Draw(tl)
    tl = _clip_to(tl, tl)
    im.alpha_composite(tl)
    # pocket square
    d = ImageDraw.Draw(im)
    _polyS(d, [(436 + sx, 500 + sy), (478 + sx, 494 + sy), (470 + sx, 520 + sy), (452 + sx, 508 + sy), (440 + sx, 520 + sy)], (250, 244, 232, 255), S)
    _polyS(d, [(440 + sx, 520 + sy), (452 + sx, 508 + sy), (470 + sx, 520 + sy)], tie + (255,), S)

    return im


_HEADC = {}


def _head_resized(st, pal, mouth_open, t, HSC, S):
    """head layer rendered at the supersampled size and cached by a quantised expression key (a few hundred distinct heads per video)"""
    def q(v, m):
        return round(v / m) * m
    key = (id(pal), q(st["brow"], .04), q(st["tilt"], .05), q(st["asym"], .05), q(st["eo"], .06), q(st["wink"], .1), q(st["lx"], .08), q(st["ly"], .08),
           q(st["smile"], .05), q(st["mw"], .05), q(st["blush"], .08), q(st["sweat"], .1), q(mouth_open, .06), int(t * 8) if st["sweat"] > 0.03 else 0)
    h = _HEADC.get(key)
    if h is None:
        if len(_HEADC) > 600:
            _HEADC.clear()
        st2 = dict(st)
        st2["_t"] = t
        h = _head(st2, pal, mouth_open)
        hw_, hh_ = h.size
        h = h.resize((int(hw_ * HSC * S / HS), int(hh_ * HSC * S / HS)), Image.LANCZOS)
        _HEADC[key] = h
    return h


def draw_char(st, pal, t=0.0, mouth_open=0.0):
    """returns (RGBA layer LW x CH, anchors in local coords)"""
    st = dict(st)
    st["_t"] = t
    S = BS
    size = (LW * S, CH * S)
    lean = st["lean"]
    sx, sy = lean + OX, st["bob"]
    shirt, shd = pal["shirt"], pal["shirt_d"]
    jacket, jd, jl = pal["jacket"], pal["jacket_d"], pal["jacket_l"]
    tie, tie_d = pal["tie"], pal["tie_d"]

    im = Image.new("RGBA", size, (0, 0, 0, 0))
    im.paste(_body_cached(pal, S, size), (int(round(lean * S)), int(round(st["bob"] * S))))
    shirt, shd, tie, tie_d = pal["shirt"], pal["shirt_d"], pal["tie"], pal["tie_d"]
    sx, sy = lean + OX, st["bob"]
    neck = Image.new("RGBA", size, (0, 0, 0, 0))
    nd = ImageDraw.Draw(neck)
    nd.rounded_rectangle([(272 + sx) * S, (292 + sy) * S, (368 + sx) * S, (404 + sy) * S], radius=int(34 * S), fill=(0, 0, 0, 255))
    # ------------------------------------------------------------ head
    hcx, hcy = 320 + sx + st["head_dx"], 222 + sy + st["head_dy"]
    HSC = 1.2
    head = _head_resized(st, pal, mouth_open, t, HSC, S)
    tilt = st["head_tilt"]
    if abs(tilt) > 0.05:
        head = head.rotate(-tilt, resample=Image.BICUBIC, center=(190 * HSC * S, 300 * HSC * S))
    sd = _soft((LW, CH), lambda dd: dd.ellipse([320 + sx - 76, 350 + sy, 320 + sx + 76, 392 + sy], fill=(40, 16, 12, 170)), 8, S)
    im.alpha_composite(_clip_to(sd, neck))
    im.alpha_composite(head, (int((hcx - 190 * HSC) * S), int((hcy - 190 * HSC - 8) * S)))

    # ------------------------------------------------------------ arms (volumetric sleeves + hands)
    anchors = {"head": (hcx, hcy)}
    for side, shx, hxk, hyk, gk, pk in ((-1, 188, "lhx", "lhy", "lg", "lpa"), (1, 452, "rhx", "rhy", "rg", "rpa")):
        Sh = (shx + sx, 446 + sy)
        T = (st[hxk] + OX + lean * 0.3, st[hyk])
        E, Wp = _ik(Sh, T, 180, 168, side, 320 + OX)
        arm = Image.new("RGBA", size, (0, 0, 0, 0))
        ad = ImageDraw.Draw(arm)
        _capS(ad, Sh, E, 72, jacket + (255,), S)
        _capS(ad, E, Wp, 64, jacket + (255,), S)
        arm = pillow(arm, 20 * S, 0.62, light=(-0.55, -0.8), spec=0.16, sh_col=(6, 6, 12), hi_col=jl, down=4)
        # elbow crease
        crease = _soft((LW, CH), lambda dd: dd.ellipse([E[0] - 20, E[1] - 8, E[0] + 20, E[1] + 24], fill=(0, 0, 0, 80)), 6, S)
        arm.alpha_composite(_clip_to(crease, arm))
        im.alpha_composite(arm)
        fd = (Wp[0] - E[0], Wp[1] - E[1])
        fl = math.hypot(*fd) or 1.0
        u = (fd[0] / fl, fd[1] / fl)
        d = ImageDraw.Draw(im)
        cuff = Image.new("RGBA", size, (0, 0, 0, 0))
        cd = ImageDraw.Draw(cuff)
        _capS(cd, (Wp[0] - u[0] * 16, Wp[1] - u[1] * 16), (Wp[0] + u[0] * 6, Wp[1] + u[1] * 6), 62, shirt + (255,), S)
        cuff = pillow(cuff, 8 * S, 0.5, sh_col=shd, down=3)
        im.alpha_composite(cuff)
        d = ImageDraw.Draw(im)
        cl = (Wp[0] - u[1] * 20 * side * -1 + u[0] * -4, Wp[1] + u[0] * 20 * side * -1 + u[1] * -4)
        _ellS(d, cl[0], cl[1], 5, 5, tie + (255,), S)
        hand = Image.new("RGBA", size, (0, 0, 0, 0))
        hd = ImageDraw.Draw(hand)
        g = int(round(st[gk]))
        hc = _hand(hd, pal, (Wp[0] + u[0] * 6, Wp[1] + u[1] * 6), u, g, st[pk], S)
        hand = pillow(hand, 7 * S, 0.34, spec=0.25, sh_col=pal["skin_d"], hi_col=pal["skin_l"], down=3)
        im.alpha_composite(hand)
        anchors["hand_l" if side < 0 else "hand_r"] = (hc[0], hc[1], u[0], u[1])

    out = im.resize((LW, CH), Image.LANCZOS)
    a = np.array(out.getchannel("A"), np.float32) / 255.0
    arr = np.array(out, np.float32)
    # key light from the upper-left, soft vertical falloff
    yy = np.linspace(1.10, 0.86, CH, dtype=np.float32)[:, None]
    xx = np.linspace(1.04, 0.94, LW, dtype=np.float32)[None, :]
    arr[..., :3] = np.clip(arr[..., :3] * (yy * xx)[..., None], 0, 255)
    # rim lights: warm on the right, cool on the left
    for sgn, col, k_, amt in ((1, np.array(pal["rim"], np.float32), 7, 0.7 * st["rim"]), (-1, np.array(pal["rim2"], np.float32), 6, 0.38 * st["rim"])):
        sh_ = np.roll(a, -k_ * sgn, axis=1)
        if sgn > 0:
            sh_[:, -k_:] = 0
        else:
            sh_[:, :k_] = 0
        rim = np.clip(a - sh_, 0, 1) * amt
        rim = np.array(Image.fromarray((rim * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.3)), np.float32) / 255.0
        arr[..., :3] = arr[..., :3] * (1 - rim[..., None]) + col * rim[..., None]
    ramp = np.clip((CH - np.arange(CH, dtype=np.float32)) / 120.0, 0, 1)[:, None]
    arr[..., 3] = arr[..., 3] * ramp
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA"), anchors


# ----------------------------------------------------------------------------- the animated host
class Host:
    def __init__(self, track, env=None, palette="ali", blinks=(0.9, 3.45, 5.8, 8.7, 11.6, 15.1, 18.0, 21.0, 23.9),
                 mods=(), props=(), halo=True, mouth_gain=1.0, gscale=1.0, gdy=0.0):
        self.keys = []
        for k in track:
            t, ex, ov = k[0], k[1], (k[2] if len(k) > 2 else {})
            dur = k[3] if len(k) > 3 else 0.5
            ease = k[4] if len(k) > 4 else "io"
            s = state_of(ex) if isinstance(ex, str) else _ex(**ex)
            s.update(ov)
            self.keys.append((t, s, dur, ease))
        self.pal = PALETTES[palette]
        self.env = env
        self.blinks = blinks
        self.mods = list(mods)
        self.props = list(props)
        self.halo = halo
        self.mg = mouth_gain
        self.gscale, self.gdy = gscale, gdy
        self.anchors = {}
        self._halo = None

    def state(self, t):
        cur = dict(self.keys[0][1])
        for i in range(1, len(self.keys)):
            t1, s1, dur, ease = self.keys[i]
            start = t1 - dur
            if t <= start:
                break
            p = clamp((t - start) / max(dur, 1e-3))
            e = ease_out_back(p, 1.2) if ease == "back" else ease_out_cubic(p) if ease == "out" else ease_in_out(p)
            prev = self.keys[i - 1][1]
            cur = {k: (lerp(prev[k], s1[k], e) if isinstance(prev[k], (int, float)) else s1[k]) for k in prev}
            if p < 1:
                break
        return cur

    def blink_amt(self, t):
        for b in self.blinks:
            u = (t - b) / 0.16
            if 0 <= u <= 1:
                return 1 - abs(2 * u - 1)
        return 0.0

    def layer(self, t):
        st = self.state(t)
        st["bob"] += 4.5 * math.sin(t * 2.0)
        st["head_tilt"] += 1.2 * math.sin(t * 1.1 + 0.6)
        st["head_dy"] += 2.0 * math.sin(t * 2.0 + 0.3)
        for m in self.mods:
            m(t, st)
        st["eo"] = st["eo"] * (1 - 0.95 * self.blink_amt(t))
        mo = st["mo"]
        if self.env is not None:
            mo = clamp(max(mo, self.env(t) * 0.85 * self.mg), 0, 1)
        return draw_char(st, self.pal, t, mo), st

    def _halo_layer(self):
        if self._halo is None:
            D = 900
            yy, xx = np.mgrid[0:D, 0:D].astype(np.float32)
            r = np.sqrt((xx - D / 2) ** 2 + (yy - D / 2) ** 2) / (D / 2)
            a = np.clip(1 - r, 0, 1) ** 2.2
            col = np.array((255, 206, 120), np.float32)
            self._halo = Image.fromarray(np.dstack([np.ones((D, D, 3), np.float32) * col, a * 150]).astype(np.uint8), "RGBA")
        return self._halo

    def draw(self, cv, t):
        (lay, anchors), st = self.layer(t)
        al = st["al"]
        if al <= 0.01:
            return
        sc = st["sc"] * self.gscale
        cx, by = st["cx"], st["by"] + st["rise"] + self.gdy
        cy = by - CH * sc / 2
        if self.halo:
            put(cv, self._halo_layer(), cx, cy - 60 * sc, al * 0.55, 1.0 * sc * 1.1)
        put(cv, lay, cx, cy, al, sc)

        def g(lx, ly):
            return cx + (lx - LW / 2) * sc, cy + (ly - CH / 2) * sc
        self.anchors = {k: ((g(v[0], v[1]) + v[2:]) if len(v) > 2 else g(v[0], v[1])) for k, v in anchors.items()}
        self.g, self.sc_now, self.st = g, sc, st
        for pr in self.props:
            pr(cv, t, self, al)


# ----------------------------------------------------------------------------- modifiers
def head_shake(t0, dur, amp=14, freq=4.2):
    def f(t, st):
        if t0 <= t <= t0 + dur:
            u = (t - t0) / dur
            st["head_dx"] += amp * math.sin((t - t0) * freq * math.pi) * (1 - u)
            st["head_tilt"] += 4 * math.sin((t - t0) * freq * math.pi) * (1 - u)
    return f


def nod(t0, dur, amp=10, freq=2.6):
    def f(t, st):
        if t0 <= t <= t0 + dur:
            u = (t - t0) / dur
            st["head_dy"] += amp * abs(math.sin((t - t0) * freq * math.pi)) * (1 - u * 0.5)
    return f


def wave(side, t0, dur, ax=26, ay=10, freq=3.2):
    kx, ky = ("rhx", "rhy") if side == "r" else ("lhx", "lhy")

    def f(t, st):
        if t0 <= t <= t0 + dur:
            u = (t - t0) / dur
            w = math.sin(u * math.pi)
            st[kx] += ax * math.sin((t - t0) * freq * 2 * math.pi) * w
            st[ky] += ay * math.cos((t - t0) * freq * 2 * math.pi) * w
    return f


def tap(side, t0, times, amp=16, dur=0.14):
    ky = "rhy" if side == "r" else "lhy"

    def f(t, st):
        for tt in times:
            u = (t - tt) / dur
            if 0 <= u <= 1:
                st[ky] += amp * math.sin(u * math.pi)
    return f
