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
    "ali": dict(skin=(236, 184, 144), skin_d=(206, 146, 108), hair=(30, 24, 24), hair_l=(66, 54, 52), jacket=(38, 42, 56),
                jacket_d=(26, 29, 40), jacket_l=(64, 70, 90), shirt=(247, 243, 233), shirt_d=(214, 208, 194), tie=(244, 196, 92),
                tie_d=(190, 140, 44), iris=(78, 48, 30), lip=(190, 104, 94), rim=(255, 206, 120)),
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


# ----------------------------------------------------------------------------- drawing helpers
def _S(pts):
    return [(x * SS, y * SS) for x, y in pts]


def _cap(d, p0, p1, w, fill):
    d.line([(p0[0] * SS, p0[1] * SS), (p1[0] * SS, p1[1] * SS)], fill=fill, width=int(w * SS))
    r = w * SS / 2
    for p in (p0, p1):
        d.ellipse([p[0] * SS - r, p[1] * SS - r, p[0] * SS + r, p[1] * SS + r], fill=fill)


def _ell(d, cx, cy, rx, ry, fill, outline=None, ow=0):
    d.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=fill, outline=outline, width=int(ow * SS))


def _bez(p0, p1, p2, n=18):
    out = []
    for i in range(n + 1):
        u = i / n
        out.append(((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
                    (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]))
    return out


def _ik(S, T, l1, l2, side, cxm=320):
    """two-bone IK; the elbow is the solution farther from the body centre line (outward)"""
    dx, dy = T[0] - S[0], T[1] - S[1]
    d = max(abs(l1 - l2) + 2.0, min(l1 + l2 - 1.0, math.hypot(dx, dy)))
    th = math.atan2(dy, dx)
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    al = math.acos(clamp(c, -1, 1))
    cands = []
    for sgn in (-1, 1):
        a = th + sgn * al
        cands.append((S[0] + l1 * math.cos(a), S[1] + l1 * math.sin(a)))
    E = max(cands, key=lambda p: 0.5 * abs(p[0] - cxm) + 0.9 * p[1])
    wd = (T[0] - E[0], T[1] - E[1])
    ln = math.hypot(*wd) or 1.0
    Wp = (E[0] + wd[0] / ln * l2, E[1] + wd[1] / ln * l2)
    return E, Wp


def _head(st, pal, mouth_open):
    """head layer (380 x 400 local), head centre at (190, 190)"""
    HW, HH = 380, 400
    im = Image.new("RGBA", (HW * SS, HH * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = 190, 190
    skin, skin_d, hair, hair_l = pal["skin"] + (255,), pal["skin_d"] + (255,), pal["hair"] + (255,), pal["hair_l"] + (255,)
    # hair back
    _ell(d, cx, cy - 14, 124, 128, hair)
    # ears
    for sx in (-1, 1):
        _ell(d, cx + sx * 112, cy + 6, 22, 32, skin_d)
        _ell(d, cx + sx * 112, cy + 6, 12, 20, pal["lip"] + (120,))
    # face
    _ell(d, cx, cy, 112, 124, skin)
    _ell(d, cx, cy + 62, 90, 66, skin)
    # soft face shade (left side) and chin
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    _ell(sd, cx - 70, cy + 20, 70, 120, skin_d[:3] + (70,))
    _ell(sd, cx, cy + 118, 70, 26, skin_d[:3] + (60,))
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).ellipse([(cx - 112) * SS, (cy - 124) * SS, (cx + 112) * SS, (cy + 124) * SS], fill=255)
    ImageDraw.Draw(mask).ellipse([(cx - 90) * SS, (cy - 4) * SS, (cx + 90) * SS, (cy + 128) * SS], fill=255)
    sh.putalpha(Image.fromarray((np.array(sh.getchannel("A"), np.float32) * (np.array(mask, np.float32) / 255)).astype(np.uint8)))
    sh = sh.filter(ImageFilter.GaussianBlur(10 * SS))
    im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    # blush
    if st["blush"] > 0.02:
        bl = Image.new("RGBA", im.size, (0, 0, 0, 0))
        bd = ImageDraw.Draw(bl)
        for sx in (-1, 1):
            _ell(bd, cx + sx * 70, cy + 46, 30, 18, (244, 120, 110, int(110 * st["blush"])))
        im.alpha_composite(bl.filter(ImageFilter.GaussianBlur(8 * SS)))
        d = ImageDraw.Draw(im)
    # hair front (side-swept fringe + sideburns)
    fr = [(-118, -4), (-122, -58), (-96, -104), (-40, -132), (30, -136), (92, -112), (120, -64), (118, -2),
          (104, -34), (88, -62), (40, -84), (-6, -78), (-52, -66), (-94, -40)]
    d.polygon(_S([(cx + x, cy + y) for x, y in fr]), fill=hair)
    d.polygon(_S([(cx - 118, cy - 4), (cx - 108, cy + 40), (cx - 96, cy + 8), (cx - 98, cy - 36)]), fill=hair)
    d.polygon(_S([(cx + 118, cy - 4), (cx + 108, cy + 40), (cx + 96, cy + 8), (cx + 98, cy - 36)]), fill=hair)
    d.polygon(_S([(cx - 40, cy - 128), (cx + 10, cy - 134), (cx + 60, cy - 120), (cx + 4, cy - 108)]), fill=hair_l[:3] + (140,))
    # eyebrows
    for sx, k in ((-1, 0), (1, 1)):
        raise_ = st["brow"] + (st["asym"] if k else 0.0)
        by_ = cy - 52 - raise_ * 17
        bx = cx + sx * 44
        L = 30
        inner = (bx - sx * L, by_ - st["tilt"] * 11)
        outer = (bx + sx * L, by_ + st["tilt"] * 8)
        _cap(d, inner, outer, 11, hair)
    # eyes
    for sx, k in ((-1, 0), (1, 1)):
        ex, ey = cx + sx * 44, cy - 6
        eo = st["eo"] * (1 - (st["wink"] if k else 0.0))
        eo = clamp(eo, 0, 1.3)
        if eo < 0.16:
            if st["smile"] > 0.4:
                d.arc([(ex - 22) * SS, (ey - 14) * SS, (ex + 22) * SS, (ey + 14) * SS], 200, 340, fill=hair, width=int(7 * SS))
            else:
                d.arc([(ex - 22) * SS, (ey - 12) * SS, (ex + 22) * SS, (ey + 12) * SS], 20, 160, fill=hair, width=int(7 * SS))
            continue
        ry = 21 * eo
        _ell(d, ex, ey, 25, ry, (251, 249, 245, 255))
        ix = ex + st["lx"] * 8
        iy = ey + st["ly"] * 7
        ir = 13
        # clip iris to the eye by drawing on a mask
        eye = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ed = ImageDraw.Draw(eye)
        _ell(ed, ix, iy, ir, min(ir * 1.05, ry + 2), pal["iris"] + (255,))
        _ell(ed, ix, iy, ir * 0.5, min(ir * 0.55, ry), (18, 12, 10, 255))
        _ell(ed, ix - 4, iy - 5, 3.4, 3.4, (255, 255, 255, 235))
        em = Image.new("L", im.size, 0)
        ImageDraw.Draw(em).ellipse([(ex - 25) * SS, (ey - ry) * SS, (ex + 25) * SS, (ey + ry) * SS], fill=255)
        eye.putalpha(Image.fromarray((np.array(eye.getchannel("A"), np.float32) * (np.array(em, np.float32) / 255)).astype(np.uint8)))
        im.alpha_composite(eye)
        d = ImageDraw.Draw(im)
        # lids
        lid = hair[:3] + (255,)
        d.arc([(ex - 25) * SS, (ey - ry) * SS, (ex + 25) * SS, (ey + ry) * SS], 195, 345, fill=lid, width=int(5 * SS))
        if eo < 0.7:
            d.chord([(ex - 26) * SS, (ey - ry - 2) * SS, (ex + 26) * SS, (ey + ry + 2) * SS], 180, 360, fill=skin_d[:3] + (255,))
            d.arc([(ex - 25) * SS, (ey - ry) * SS, (ex + 25) * SS, (ey + ry) * SS], 195, 345, fill=lid, width=int(5 * SS))
    # nose
    d.arc([(cx - 12) * SS, (cy + 14) * SS, (cx + 12) * SS, (cy + 44) * SS], 20, 160, fill=skin_d[:3] + (255,), width=int(5 * SS))
    # mouth
    mo = clamp(mouth_open, 0, 1)
    sm = st["smile"]
    hw = 44 * st["mw"] * (1 + 0.12 * max(0, sm))
    my = cy + 74
    yc = my - sm * 17
    ym = my + (2 if sm >= 0 else -4 * -sm) - (0 if sm >= 0 else 6 * -sm)
    up = _bez((cx - hw, yc), (cx, ym + (6 * sm if sm > 0 else -8 * -sm)), (cx + hw, yc))
    lw_ = my + mo * 50 + max(0, sm) * 10 + 4
    lo = _bez((cx + hw, yc), (cx, lw_ + mo * 16 + 2), (cx - hw, yc))
    if mo > 0.06:
        poly = _S(up + lo)
        mouth = Image.new("RGBA", im.size, (0, 0, 0, 0))
        md = ImageDraw.Draw(mouth)
        md.polygon(poly, fill=(74, 24, 32, 255))
        # tongue
        tg = _bez((cx - hw * 0.55, lw_ + 6), (cx, lw_ - 22 + mo * 8), (cx + hw * 0.55, lw_ + 6))
        md.polygon(_S(tg + [(cx + hw * 0.5, lw_ + 30), (cx - hw * 0.5, lw_ + 30)]), fill=(222, 108, 116, 255))
        # teeth
        th = min(16, 6 + mo * 22)
        md.polygon(_S(up + [(x, y + th) for x, y in reversed(up)]), fill=(252, 250, 246, 255))
        mm = Image.new("L", im.size, 0)
        ImageDraw.Draw(mm).polygon(poly, fill=255)
        mouth.putalpha(Image.fromarray((np.array(mouth.getchannel("A"), np.float32) * (np.array(mm, np.float32) / 255)).astype(np.uint8)))
        im.alpha_composite(mouth)
        d = ImageDraw.Draw(im)
        d.line(_S(up), fill=pal["lip"] + (255,), width=int(5 * SS), joint="curve")
        d.line(_S(lo), fill=pal["lip"] + (255,), width=int(5 * SS), joint="curve")
    else:
        d.line(_S(up), fill=pal["lip"] + (255,), width=int(7 * SS), joint="curve")
        if sm > 0.6:
            d.line(_S(_bez((cx - hw * 0.7, yc + 2), (cx, my + 14 + sm * 10), (cx + hw * 0.7, yc + 2))), fill=pal["lip"][:3] + (120,), width=int(3 * SS))
    # sweat drop
    if st["sweat"] > 0.03:
        k = st["sweat"]
        tx, ty = cx + 104, cy - 70 + 18 * math.sin(st.get("_t", 0) * 2.2)
        s = 0.6 + 0.4 * k
        d.polygon(_S([(tx, ty - 26 * s), (tx - 13 * s, ty + 4 * s), (tx + 13 * s, ty + 4 * s)]), fill=(150, 214, 255, int(230 * k)))
        _ell(d, tx, ty + 6 * s, 13 * s, 13 * s, (150, 214, 255, int(230 * k)))
        _ell(d, tx - 4 * s, ty + 3 * s, 3.5 * s, 5 * s, (255, 255, 255, int(200 * k)))
    return im


def draw_char(st, pal, t=0.0, mouth_open=0.0):
    """returns (RGBA layer CW x CH, anchors in local coords)"""
    st = dict(st)
    st["_t"] = t
    im = Image.new("RGBA", (LW * SS, CH * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lean = st["lean"]
    sx, sy = lean + OX, st["bob"]
    jacket, jd, jl = pal["jacket"] + (255,), pal["jacket_d"] + (255,), pal["jacket_l"] + (255,)
    shirt, shd = pal["shirt"] + (255,), pal["shirt_d"] + (255,)
    # torso
    d.rounded_rectangle([(120 + sx) * SS, (380 + sy) * SS, (520 + sx) * SS, 800 * SS], radius=int(96 * SS), fill=jacket)
    hl = Image.new("RGBA", im.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.rounded_rectangle([(122 + sx) * SS, (382 + sy) * SS, (518 + sx) * SS, 800 * SS], radius=int(94 * SS), outline=jl[:3] + (90,), width=int(4 * SS))
    _ell(hd, 400 + sx, 440 + sy, 110, 60, jl[:3] + (46,))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(3 * SS)))
    d = ImageDraw.Draw(im)
    # neck + shirt V + collar + tie
    d.rounded_rectangle([(274 + sx) * SS, (296 + sy) * SS, (366 + sx) * SS, (396 + sy) * SS], radius=int(30 * SS), fill=pal["skin_d"] + (255,))
    d.polygon(_S([(256 + sx, 380 + sy), (384 + sx, 380 + sy), (320 + sx, 560 + sy)]), fill=shirt)
    d.polygon(_S([(256 + sx, 380 + sy), (300 + sx, 392 + sy), (320 + sx, 440 + sy), (268 + sx, 424 + sy)]), fill=shd)
    d.polygon(_S([(384 + sx, 380 + sy), (340 + sx, 392 + sy), (320 + sx, 440 + sy), (372 + sx, 424 + sy)]), fill=shirt)
    d.polygon(_S([(234 + sx, 392 + sy), (276 + sx, 380 + sy), (320 + sx, 560 + sy), (252 + sx, 470 + sy)]), fill=jd)
    d.polygon(_S([(406 + sx, 392 + sy), (364 + sx, 380 + sy), (320 + sx, 560 + sy), (388 + sx, 470 + sy)]), fill=jd)
    tie, tie_d = pal["tie"] + (255,), pal["tie_d"] + (255,)
    d.polygon(_S([(304 + sx, 398 + sy), (336 + sx, 398 + sy), (342 + sx, 420 + sy), (298 + sx, 420 + sy)]), fill=tie)
    d.polygon(_S([(300 + sx, 420 + sy), (340 + sx, 420 + sy), (354 + sx, 540 + sy), (320 + sx, 572 + sy), (286 + sx, 540 + sy)]), fill=tie)
    d.polygon(_S([(320 + sx, 420 + sy), (340 + sx, 420 + sy), (354 + sx, 540 + sy), (320 + sx, 572 + sy)]), fill=tie_d)
    # head
    hcx, hcy = 320 + sx + st["head_dx"], 222 + sy + st["head_dy"]
    head = _head(st, pal, mouth_open)
    HS = 1.2
    head = head.resize((int(head.width * HS), int(head.height * HS)), Image.BICUBIC)
    tilt = st["head_tilt"]
    if abs(tilt) > 0.05:
        head = head.rotate(-tilt, resample=Image.BICUBIC, center=(190 * SS * HS, 300 * SS * HS))
    # chin shadow on neck
    sd = Image.new("RGBA", im.size, (0, 0, 0, 0))
    _ell(ImageDraw.Draw(sd), 320 + sx, 360 + sy, 70, 22, (60, 30, 20, 120))
    im.alpha_composite(sd.filter(ImageFilter.GaussianBlur(8 * SS)))
    im.alpha_composite(head, (int((hcx - 190 * HS) * SS), int((hcy - 190 * HS - 8) * SS)))
    d = ImageDraw.Draw(im)
    # arms
    anchors = {"head": (hcx, hcy)}
    for side, shx, hxk, hyk, gk, pk in ((-1, 175, "lhx", "lhy", "lg", "lpa"), (1, 465, "rhx", "rhy", "rg", "rpa")):
        S = (shx + sx, 412 + sy)
        T = (st[hxk] + OX + lean * 0.3, st[hyk])
        E, Wp = _ik(S, T, 172, 160, side, 320 + OX)
        _cap(d, S, E, 70, jacket)
        _cap(d, E, Wp, 64, jacket)
        fd = (Wp[0] - E[0], Wp[1] - E[1])
        fl = math.hypot(*fd) or 1.0
        ux, uy = fd[0] / fl, fd[1] / fl
        cuff0 = (Wp[0] - ux * 14, Wp[1] - uy * 14)
        _cap(d, cuff0, (Wp[0] + ux * 4, Wp[1] + uy * 4), 62, shirt)
        g = int(round(st[gk]))
        pa = math.radians(st[pk])
        hx0, hy0 = Wp[0] + ux * 6, Wp[1] + uy * 6
        c, s_ = math.cos(pa), math.sin(pa)
        vx, vy = ux * c - uy * s_, ux * s_ + uy * c
        skin = pal["skin"] + (255,)
        if g == 2:        # pointing finger
            _cap(d, (hx0, hy0), (hx0 + vx * 34, hy0 + vy * 34), 52, skin)
            _cap(d, (hx0 + vx * 20, hy0 + vy * 20), (hx0 + vx * 82, hy0 + vy * 82), 20, skin)
            hc = (hx0 + vx * 82, hy0 + vy * 82)
        elif g == 1:      # fist
            _cap(d, (hx0, hy0), (hx0 + vx * 28, hy0 + vy * 28), 62, skin)
            hc = (hx0 + vx * 22, hy0 + vy * 22)
            d.arc([(hc[0] - 24) * SS, (hc[1] - 24) * SS, (hc[0] + 24) * SS, (hc[1] + 24) * SS], 0, 360, fill=pal["skin_d"] + (255,), width=int(3 * SS))
        else:             # open hand (mitten + thumb + finger hint)
            _cap(d, (hx0, hy0), (hx0 + vx * 46, hy0 + vy * 46), 66, skin)
            nx, ny = -vy * side, vx * side
            _cap(d, (hx0 + vx * 14 + nx * 26, hy0 + vy * 14 + ny * 26), (hx0 + vx * 46 + nx * 34, hy0 + vy * 46 + ny * 34), 24, skin)
            hc = (hx0 + vx * 40, hy0 + vy * 40)
        anchors["hand_l" if side < 0 else "hand_r"] = (hc[0], hc[1], vx, vy)
    out = im.resize((LW, CH), Image.LANCZOS)
    # warm rim light on the right edge
    a = np.array(out.getchannel("A"), np.float32) / 255.0
    k = 6
    sh_ = np.roll(a, -k, axis=1)
    sh_[:, -k:] = 0
    rim = np.clip(a - sh_, 0, 1) * 0.65 * st["rim"]
    rim = np.array(Image.fromarray((rim * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255.0
    arr = np.array(out, np.float32)
    rc = np.array(pal["rim"], np.float32)
    arr[..., :3] = arr[..., :3] * (1 - rim[..., None]) + rc * rim[..., None]
    ramp = np.clip((CH - np.arange(CH, dtype=np.float32)) / 110.0, 0, 1)[:, None]
    arr[..., 3] = arr[..., 3] * ramp
    out = Image.fromarray(arr.astype(np.uint8), "RGBA")
    return out, anchors


# ----------------------------------------------------------------------------- the animated host
class Host:
    def __init__(self, track, env=None, palette="ali", blinks=(0.9, 3.45, 5.8, 8.7, 11.6, 15.1, 18.0, 21.0, 23.9),
                 mods=(), props=(), halo=True, mouth_gain=1.0):
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
        sc = st["sc"]
        cx, by = st["cx"], st["by"] + st["rise"]
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
