"""Kun 19: "Bepul" effekti (Marketing). PREMIUM uslub: "NEON SOVG'A" (neon dunyo, sovg'a qutisi = magnit, 0 narx).
Jumboq: "Nega 'bepul' sehrli?" -> sovg'a qutisi odamlarni tortadi -> bepul sinov xavfni olib tashlaydi -> yo'qotish qo'rquvi ->
shokolad tajribasi: 2 sent -> 1 sent (deyarli o'zgarmaydi), 1 sent -> 0 (talab sakraydi) -> eshik: qiymat bo'lmasa odam ketadi ->
"Bepul - eshik. Qiymat - qolish sababi." -> do'stga yubor, obuna.
Personaj: nt_char Host (yangi libos: teal kamzul, pushti galstuk), lablar ovozga mos.
"""
import math
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

from nt_kit import *      # noqa
from nt_fx import *       # noqa
import nt_char
from nt_char import Host, speech_env, head_shake, nod, wave    # noqa

CY, PK, YL, GR, RD = (0, 229, 255), (255, 64, 160), (255, 214, 90), (84, 236, 168), (255, 92, 104)
WHITE, MUTE, DARK = (244, 246, 255), (176, 170, 214), (34, 12, 66)
CX = 540

# a new look for the (same) host: teal jacket + pink tie, neon rim lights
nt_char.PALETTES["bepul"] = dict(
    nt_char.PALETTES["ali"],
    jacket=(30, 104, 132), jacket_d=(14, 60, 82), jacket_l=(92, 186, 208),
    shirt=(250, 250, 253), shirt_d=(200, 204, 216),
    tie=(255, 84, 170), tie_d=(186, 40, 116),
    hair=(52, 30, 22), hair_l=(130, 86, 64),
    iris=(40, 66, 82), iris_l=(96, 150, 172),
    rim=(255, 120, 200), rim2=(80, 230, 255))


def win(t, a, b, fi=0.10, fo=0.20):
    if t < a or t >= b:
        return 0.0
    return clamp((t - a) / fi) * clamp((b - t) / fo) if fi > 0 else clamp((b - t) / fo)


# ----------------------------------------------------------------------------- text
@lru_cache(None)
def X(s, size, col=WHITE, maxw=900, w="xb"):
    return txt(s, size, col, w, maxw)


@lru_cache(None)
def G(s, size, c0=(200, 255, 255), c1=(255, 120, 205), maxw=900):
    z = size
    while z > 30:
        im = gtext(s, z, c0, c1)
        if im.width <= maxw + 16:
            return im
        z -= 4
    return gtext(s, z, c0, c1)


@lru_cache(None)
def GG(s, size, c0=(200, 255, 255), c1=(255, 120, 205), maxw=900, r=24, k=1.2, col=(70, 220, 255)):
    return glow(G(s, size, c0, c1, maxw), col, r, k)


@lru_cache(None)
def card(w, h, r=46, a=30, ba=100, blur=26, off=16, sh=0.55, border=(150, 225, 255)):
    return shadowed(glass(w, h, r, (255, 255, 255), a, border, ba), blur, (0, off), sh)


# ----------------------------------------------------------------------------- icons
def _shade(im, k0=1.12, k1=0.80):
    a = np.asarray(im, np.float32).copy()
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = ((xx / w) * 0.35 + (yy / h) * 0.65)[..., None]
    a[..., :3] = np.clip(a[..., :3] * (k0 + (k1 - k0) * g), 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


@lru_cache(None)
def gift_body(w):
    s, h = 3, int(w * 0.62)
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=int(w * 0.05 * s), fill=PK + (255,))
    rw = int(w * 0.17 * s)
    x0 = (w * s - rw) // 2
    d.rectangle([x0, 0, x0 + rw, h * s], fill=YL + (255,))
    for i in range(6):                                  # little dots pattern
        for j in range(2):
            px, py = (0.10 + i * 0.16) * w * s, (0.30 + j * 0.38) * h * s
            if abs(px - w * s / 2) > rw:
                d.ellipse([px - 7 * s, py - 7 * s, px + 7 * s, py + 7 * s], fill=(255, 150, 210, 255))
    return _shade(im).resize((w, h), Image.LANCZOS)


@lru_cache(None)
def gift_lid(w):
    lw, lh, bowh = int(w * 1.10), int(w * 0.20), int(w * 0.34)
    s, Hh = 3, int(w * 0.20) + int(w * 0.34)
    im = Image.new("RGBA", (lw * s, Hh * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, bowh * s, lw * s - 1, Hh * s - 1], radius=int(lh * 0.3 * s), fill=(255, 104, 188, 255))
    rw = int(w * 0.17 * s)
    x0 = (lw * s - rw) // 2
    d.rectangle([x0, bowh * s, x0 + rw, Hh * s], fill=YL + (255,))
    cx = lw * s / 2
    for sg in (-1, 1):
        bx, by = cx + sg * w * 0.15 * s, bowh * s - w * 0.10 * s
        d.ellipse([bx - w * 0.15 * s, by - w * 0.13 * s, bx + w * 0.15 * s, by + w * 0.13 * s], outline=YL + (255,), width=int(w * 0.055 * s))
    d.ellipse([cx - w * 0.07 * s, bowh * s - w * 0.15 * s, cx + w * 0.07 * s, bowh * s + w * 0.02 * s], fill=(255, 190, 40, 255))
    return _shade(im, 1.10, 0.86).resize((lw, Hh), Image.LANCZOS)


def gift(cv, cx, cy, w, al=1.0, lift=0.0, lid_rot=0.0, sc=1.0):
    """gift box centred (body centre) at (cx, cy); lid lifts by `lift` px"""
    body, lid = gift_body(w), gift_lid(w)
    bh = body.height
    put(cv, body, cx, cy, al, sc)
    lid_cy = cy - bh / 2 + 0.03 * w - lid.height / 2 - lift
    put(cv, lid, cx, lid_cy * sc + cy * (1 - sc), al, sc, lid_rot)


@lru_cache(None)
def choco_art(w):
    s, h = 3, int(w * 0.62)
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=int(w * 0.05 * s), fill=(78, 42, 30, 255))
    cols, rows = 4, 3
    pad = w * 0.045 * s
    cw, ch = (w * s - 2 * pad) / cols, (h * s - 2 * pad) / rows
    for r in range(rows):
        for c in range(cols):
            x0, y0 = pad + c * cw + 5 * s, pad + r * ch + 5 * s
            x1, y1 = pad + (c + 1) * cw - 5 * s, pad + (r + 1) * ch - 5 * s
            d.rounded_rectangle([x0, y0, x1, y1], radius=int(w * 0.02 * s), fill=(122, 70, 46, 255))
            d.rounded_rectangle([x0 + 8 * s, y0 + 8 * s, x1 - 8 * s, y1 - 8 * s], radius=int(w * 0.015 * s), fill=(144, 86, 58, 255))
            d.line([(x0 + 4 * s, y0 + 3 * s), (x1 - 4 * s, y0 + 3 * s)], fill=(190, 128, 92, 255), width=3 * s)
    return _shade(im, 1.10, 0.84).resize((w, h), Image.LANCZOS)


@lru_cache(None)
def gem_art(d):
    s, w, h = 3, d, int(d * 0.86)
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    P = lambda x, y: (x * w * s, y * h * s)
    facets = [
        ([(0.25, 0.0), (0.75, 0.0), (0.62, 0.32), (0.38, 0.32)], (206, 255, 255)),
        ([(0.25, 0.0), (0.38, 0.32), (0.0, 0.32)], (120, 238, 252)),
        ([(0.75, 0.0), (1.0, 0.32), (0.62, 0.32)], (70, 206, 240)),
        ([(0.0, 0.32), (0.38, 0.32), (0.5, 1.0)], (34, 172, 220)),
        ([(0.38, 0.32), (0.62, 0.32), (0.5, 1.0)], (0, 214, 248)),
        ([(0.62, 0.32), (1.0, 0.32), (0.5, 1.0)], (22, 138, 204)),
    ]
    for pts, col in facets:
        dr.polygon([P(*p) for p in pts], fill=col + (255,))
        dr.line([P(*p) for p in pts] + [P(*pts[0])], fill=(235, 255, 255, 255), width=int(w * 0.010 * s), joint="curve")
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def arch_mask(w, h):
    s = 3
    m = Image.new("L", (w * s, h * s), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=int(w * 0.5 * s), fill=255, corners=(True, True, False, False))
    return m


@lru_cache(None)
def door_room(w, h):
    """lit room visible through the open door (warm radial light, arch shaped)"""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h * 0.62) / (h * 0.62)) ** 2)
    k = np.clip(1 - r, 0, 1)[..., None]
    col = np.array((255, 238, 176), np.float32) * (0.35 + 0.65 * k) + np.array((255, 150, 70), np.float32) * (1 - k) * 0.7
    im = Image.fromarray(np.dstack([np.clip(col, 0, 255), np.full((h, w), 255, np.float32)]).astype(np.uint8), "RGBA")
    m = arch_mask(w, h).resize((w, h), Image.LANCZOS)
    im.putalpha(m)
    return im


@lru_cache(None)
def door_leaf(w, h):
    s = 3
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=int(w * 0.5 * s), fill=(122, 58, 204, 255), corners=(True, True, False, False))
    inset = 0.10
    d.rounded_rectangle([w * inset * s, h * 0.20 * s, w * (1 - inset) * s, h * 0.55 * s], radius=int(w * 0.28 * s), fill=(150, 88, 232, 255),
                        corners=(True, True, True, True))
    d.rounded_rectangle([w * inset * s, h * 0.62 * s, w * (1 - inset) * s, h * 0.94 * s], radius=int(w * 0.06 * s), fill=(150, 88, 232, 255))
    kx, ky = w * 0.82 * s, h * 0.58 * s
    d.ellipse([kx - 11 * s, ky - 11 * s, kx + 11 * s, ky + 11 * s], fill=YL + (255,))
    return _shade(im, 1.10, 0.84).resize((w, h), Image.LANCZOS)


@lru_cache(None)
def door_frame(w, h, th=16):
    s = 3
    W_, H_ = (w + 2 * th) * s, (h + th) * s
    im = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W_ - 1, H_ - 1], radius=int((w / 2 + th) * s), fill=(236, 230, 255, 255), corners=(True, True, False, False))
    hole = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    ImageDraw.Draw(hole).rounded_rectangle([th * s, th * s, (w + th) * s, H_ - 1], radius=int(w / 2 * s), fill=(0, 0, 0, 255), corners=(True, True, False, False))
    a = np.asarray(im.getchannel("A"), np.float32) * (1 - np.asarray(hole.getchannel("A"), np.float32) / 255)
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im.resize((w + 2 * th, h + th), Image.LANCZOS)


@lru_cache(None)
def ticket_art(w, h):
    s = 3
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=int(h * 0.22 * s), fill=CY + (255,))
    for xx in (0, w * s):
        r = h * 0.20 * s
        d.ellipse([xx - r, h * s / 2 - r, xx + r, h * s / 2 + r], fill=(0, 0, 0, 0))
    for y in range(int(h * 0.16), int(h * 0.86), int(h * 0.12)):
        d.line([(w * 0.18 * s, y * s), (w * 0.18 * s, (y + h * 0.06) * s)], fill=(10, 80, 100, 255), width=3 * s)
    return _shade(im, 1.10, 0.86).resize((w, h), Image.LANCZOS)


@lru_cache(None)
def xavf_art():
    w, h, s = 360, 116, 3
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=int(h * 0.3 * s), fill=RD + (255,))
    tx, ty, tr = 62 * s, h * s / 2, 36 * s
    d.polygon([(tx, ty - tr), (tx + tr * 1.05, ty + tr * 0.8), (tx - tr * 1.05, ty + tr * 0.8)], fill=(255, 244, 240, 255))
    d.rectangle([tx - 4 * s, ty - tr * 0.4, tx + 4 * s, ty + tr * 0.25], fill=RD + (255,))
    d.ellipse([tx - 5 * s, ty + tr * 0.38, tx + 5 * s, ty + tr * 0.38 + 10 * s], fill=RD + (255,))
    im = im.resize((w, h), Image.LANCZOS)
    t = txt("XAVF", 66, (255, 244, 240), "xb", 200)
    im.alpha_composite(t, (118, (h - t.height) // 2))
    return im


@lru_cache(None)
def shop_art(w):
    s, h = 3, int(w * 0.92)
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([w * 0.06 * s, h * 0.36 * s, w * 0.94 * s, h * s - 1], fill=(236, 240, 255, 255))
    stripes = 6
    sw = w * 0.96 * s / stripes
    for i in range(stripes):
        col = PK + (255,) if i % 2 == 0 else (250, 250, 255, 255)
        x0 = w * 0.02 * s + i * sw
        d.polygon([(x0 + w * 0.02 * s, h * 0.06 * s), (x0 + sw + w * 0.02 * s, h * 0.06 * s), (x0 + sw, h * 0.34 * s), (x0, h * 0.34 * s)], fill=col)
        d.pieslice([x0, h * 0.28 * s, x0 + sw, h * 0.42 * s], 0, 180, fill=col)
    d.rounded_rectangle([w * 0.40 * s, h * 0.52 * s, w * 0.60 * s, h * s], radius=int(w * 0.03 * s), fill=CY + (255,))
    d.rounded_rectangle([w * 0.12 * s, h * 0.52 * s, w * 0.34 * s, h * 0.76 * s], radius=int(w * 0.02 * s), fill=(150, 200, 255, 255))
    d.rounded_rectangle([w * 0.66 * s, h * 0.52 * s, w * 0.88 * s, h * 0.76 * s], radius=int(w * 0.02 * s), fill=(150, 200, 255, 255))
    return _shade(im, 1.06, 0.88).resize((w, h), Image.LANCZOS)


@lru_cache(None)
def bell_art(d):
    s = 3
    im = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.ellipse([d * .18 * s, d * .10 * s, d * .82 * s, d * .84 * s], fill=YL + (255,))
    dr.rounded_rectangle([d * .08 * s, d * .64 * s, d * .92 * s, d * .80 * s], radius=int(d * .07 * s), fill=(255, 190, 40, 255))
    dr.ellipse([d * .40 * s, d * .78 * s, d * .60 * s, d * .96 * s], fill=(255, 150, 30, 255))
    dr.ellipse([d * .42 * s, d * .00 * s, d * .58 * s, d * .16 * s], fill=(255, 190, 40, 255))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def plane_icon(w, col=(255, 240, 200)):
    s = 3
    im = Image.new("RGBA", (w * s, w * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    Wd = w * s
    d.polygon([(Wd * .04, Wd * .46), (Wd * .96, Wd * .08), (Wd * .62, Wd * .92), (Wd * .46, Wd * .60)], fill=tuple(col) + (255,))
    d.polygon([(Wd * .46, Wd * .60), (Wd * .96, Wd * .08), (Wd * .52, Wd * .50)], fill=(190, 170, 210, 255))
    return im.resize((w, w), Image.LANCZOS)


@lru_cache(None)
def face_i(d, mood, col=YL):
    return face(d, mood, col, DARK)


@lru_cache(None)
def tag_i(text, w=250, h=125, col=YL, size=84):
    return pricetag(w, h, col, DARK, text, DARK, size)


@lru_cache(None)
def aura(d, col, power=2.0, amax=170):
    yy, xx = np.mgrid[0:d, 0:d].astype(np.float32)
    r = np.sqrt((xx - d / 2) ** 2 + (yy - d / 2) ** 2) / (d / 2)
    a = np.clip(1 - r, 0, 1) ** power * amax
    arr = np.dstack([np.full((d, d), col[0], np.float32), np.full((d, d), col[1], np.float32), np.full((d, d), col[2], np.float32), a])
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def gauge(cv, cx, cy, w, h, level, al, jitter=0.0):
    put(cv, card(w, h, 60, 26, 90, 28, 16, 0.5), cx + jitter, cy, al)
    inner_h = h - 70
    base = cy + h / 2 - 35
    put(cv, rrect(w - 70, inner_h, 28, (255, 255, 255)), cx + jitter, cy, al * 0.10)
    hh = clamp(level, 0, 1.0) * inner_h
    if hh > 8:
        col = mixc(CY, PK, clamp((level - 0.35) / 0.65))
        bar(cv, cx + jitter, base, w - 70, hh, col, al, r=28)
    for k in range(1, 5):
        put(cv, rrect(30, 4, 2, (255, 255, 255)), cx + w / 2 - 38 + jitter, base - inner_h * k / 5, al * 0.3)


# ----------------------------------------------------------------------------- the video
def build(tim, env=None):
    D = os.path.dirname(os.path.abspath(__file__))
    env = speech_env(f"{D}/work/voice_st.wav") if os.path.exists(f"{D}/work/voice_st.wav") else speech_env("/home/claude/narxtili/day19/work/voice_st.wav")
    end0 = tim.end0

    # ---------------- host (one continuous character)
    HB = dict(cx=540, by=1480)
    PRESENT = dict(lhx=262, lhy=650, rhx=378, rhy=650)
    CELEB = dict(lhx=110, lhy=300, rhx=530, rhy=300)
    track = [
        (0.0, "think", dict(cx=540, by=1560, sc=0.80, lx=0.5, ly=-0.9, brow=0.55, rhx=392, rhy=374)),
        (1.0, "awe", dict(cx=540, by=1560, sc=0.80, lx=0.0, ly=-0.8, **PRESENT), 0.35, "back"),
        (1.95, "smile", dict(HB, sc=0.86, lx=-0.4, ly=-0.7, smile=0.5, **PRESENT), 0.4),
        (3.12, "worried", dict(HB, sc=0.86, lx=0.3, ly=-0.6, brow=0.4, smile=-0.3), 0.3),
        (3.80, "relief", dict(HB, sc=0.86, lx=0.0, ly=-0.5), 0.35, "back"),
        (4.45, "calm", dict(HB, sc=0.86, lx=-0.5, ly=-0.6, smile=0.2), 0.3),
        (5.20, "worried", dict(HB, sc=0.86, lx=0.0, ly=-0.7, sweat=1.0, lhx=212, lhy=185, rhx=428, rhy=185), 0.3),
        (5.80, "smile", dict(HB, sc=0.86, lx=0.3, ly=-0.7, smile=0.7, **PRESENT), 0.35, "back"),
        (7.13, "grin", dict(HB, sc=0.86, lx=0.0, ly=-0.6, **PRESENT), 0.3),
        (7.85, "think", dict(HB, sc=0.86, lx=0.7, ly=-0.8, brow=0.4, rhx=392, rhy=374), 0.4),
        (10.0, "no", dict(HB, sc=0.86, lx=0.5, ly=-0.7, rhx=392, rhy=374), 0.3),
        (12.72, "shock", dict(HB, sc=0.86, lx=0.5, ly=-0.7), 0.16, "back"),
        (13.62, "awe", dict(HB, sc=0.88, lx=0.4, ly=-0.7), 0.3),
        (14.22, "grin", dict(HB, sc=0.88, **CELEB), 0.25, "back"),
        (15.05, "calm", dict(HB, sc=0.86, lx=0.0, ly=-0.7, smile=0.3), 0.45),
        (17.05, "worried", dict(HB, sc=0.86, lx=0.5, ly=-0.6), 0.3),
        (18.06, "awe", dict(HB, sc=0.86, lx=0.0, ly=-0.7), 0.2, "back"),
        (18.75, "smile", dict(HB, sc=0.86, lx=-0.3, ly=-0.6, smile=0.7), 0.3),
        (19.33, "grin", dict(HB, sc=0.86, lhx=96, lhy=330, lg=2, lpa=18, lx=-0.6, ly=-0.6), 0.3),
        (20.80, "smile", dict(HB, sc=0.86, rhx=544, rhy=330, rg=2, rpa=-18, lx=0.6, ly=-0.6, smile=0.8), 0.35),
        (22.60, "grin", dict(HB, sc=0.88, lx=0.0, ly=-0.5), 0.3),
        (23.85, "wink", dict(HB, sc=0.88, rhx=524, rhy=330, rg=2, rpa=-25, lx=0.3, ly=-0.7), 0.4),
        (25.95, "grin", dict(HB, sc=0.9, rhx=524, rhy=330, rg=2, rpa=-25, lx=0.0, ly=-0.6, brow=0.5), 0.3),
        (26.45, "wink", dict(HB, sc=0.9, rhx=470, rhy=520, rg=0), 0.3),
    ]
    mods = [head_shake(10.2, 0.9, 14, 3.4), nod(16.45, 0.8, 8), nod(18.1, 0.7, 9), nod(26.1, 0.7, 9), wave("r", 22.7, 1.0, 26, 12, 2.6)]
    host = Host(track, env=env, palette="bepul", mods=mods, props=[], gscale=1.12, gdy=48)

    # ---------------- A. hook: gift box pulls people in like a magnet
    PEOPLE = [(YL, 0.00), (CY, 0.13), (PK, 0.26), (GR, 0.39), (WHITE, 0.52), (YL, 0.65), (CY, 0.78), (PK, 0.91)]

    def sc_hook(cv, t):
        al = win(t, -0.2, 2.05, 0.05, 0.22)
        if al <= 0:
            return
        gx, gy = CX, 840
        for k in range(3):                                        # magnetic pulses converge on the gift
            ph = (t * 0.75 + k / 3.0) % 1.0
            r = 620 * (1 - ph) + 120
            put(cv, ring(620, 1.0, CY, (0, 0, 0, 0), 8), gx, gy - 40, al * math.sin(math.pi * ph) ** 1.2 * 0.55, r / 620)
        for j, (col, off) in enumerate(PEOPLE):                    # faces swirl into the box
            ph = (t * 0.55 + off) % 1.0
            R = 470 * (1 - ph) + 70
            a = math.radians(j * 45 + ph * 150)
            x, y = gx + math.cos(a) * R, gy - 40 + math.sin(a) * R * 0.42
            put(cv, face_i(86, "happy", col), x, y, al * math.sin(math.pi * ph) ** 0.5, 0.55 + 0.6 * (1 - ph))
        put(cv, aura(760, PK), gx, gy - 20, al * 0.6)
        wob = 1.0 + 0.025 * math.sin(t * 7)
        gift(cv, gx, gy, 340, al * clamp((t + 0.3) / 0.12), sc=wob)
        sw = 7 * math.sin(t * 3.4)
        pop(cv, glow(tag_i("0", 270, 135, YL, 96), YL, 14, 0.8), gx + 215, 700, t, 0.0, 0.4, al, 0.0)
        # headline
        pop(cv, txt2("Nega ", "“bepul”", 118, WHITE, CY, "xb", 940), CX, 388, t + 0.18, 0.0, 0.40, al, rise=0)
        pop(cv, GG("so‘zi sehrli?", 128, maxw=940), CX, 500, t + 0.18, 0.12, 0.40, al, rise=0)

    # ---------------- B. free trial removes the risk
    def sc_risk(cv, t):
        al = win(t, 1.85, 4.5, 0.12, 0.22)
        if al <= 0:
            return
        pop(cv, glow(ticket_art(780, 150), CY, 18, 0.9), CX, 430, t, 1.953, 0.4, al * (1 - clamp((t - 3.6) / 0.2)), rise=50)
        pop(cv, X("BEPUL SINOV", 74, DARK, 560), 590, 430, t, 1.953, 0.4, al * (1 - clamp((t - 3.6) / 0.2)), rise=50)
        pop(cv, card(900, 330, 56, 28, 90, 30, 20, 0.55), CX, 750, t, 2.45, 0.4, al, rise=50)
        mood = "worried" if t < 3.75 else "happy"
        pop(cv, face_i(170, mood), 195, 750, t, 2.5, 0.35, al)
        pop(cv, X("QAROR", 88, WHITE, 300), 430, 750, t, 2.553, 0.35, al)
        if t < 3.153:
            pop(cv, X("?", 110, YL, 100), 612, 740, t, 2.9, 0.3, al)
        # XAVF tag stamps on, then the ticket kills it
        if t >= 3.152:
            p = (t - 3.152) / 0.18
            fade = 1 - clamp((t - 3.95) / 0.3)
            put(cv, xavf_art(), 805 + 8 * math.sin((t - 3.152) * 30) * max(0, 1 - (t - 3.152) * 3), 760 + (t > 3.95) * (t - 3.95) * 90,
                al * clamp(p * 3) * fade, 0.9 + 1.0 * (1 - ease_out_cubic(p)) - 0.1 * clamp((t - 3.8) / 0.3), -6)
        if 3.553 <= t < 3.9:
            q = ease_in_out((t - 3.553) / 0.2)
            put(cv, glow(ticket_art(780, 150), CY, 18, 0.9), lerp(CX, 805, q), lerp(430, 760, q), al * (1 - clamp((t - 3.753) / 0.15)), lerp(1.0, 0.36, q))
        if t >= 3.753:
            p = (t - 3.753) / 0.16
            put(cv, cross(280, RD, 32), 805, 760, al * clamp(p * 3) * (1 - clamp((t - 4.1) / 0.3)), 1 + 1.3 * (1 - ease_out_cubic(p)), 0)
        if t >= 3.95:
            pop(cv, check(150, GR, 24), 805, 760, t, 3.95, 0.35, al)
        if t >= 3.753:
            sparks(cv, t, 3.753, 805, 760, 30, (120, 255, 235), 5, 0.9, 520, 7)

    # ---------------- C. fear of losing vs. nothing to lose
    def sc_fear(cv, t):
        al = win(t, 4.25, 7.95, 0.12, 0.25)
        if al <= 0:
            return
        wx, wy, gx, gy = 265, 695, 815, 705
        pop(cv, bag(290, 340, (255, 176, 60), (214, 120, 20)), wx, wy, t, 4.33, 0.4, al, rise=50)
        pop(cv, coin(84, mark=""), wx - 40, wy - 175, t, 4.45, 0.3, al * (1 - clamp((t - 4.73) / 0.1)))
        gift_al = al * clamp((t - 4.4) / 0.2)
        gift(cv, gx, gy, 270, gift_al)
        # coins fly from the wallet into the gift (money lost) ...
        for k in range(3):
            t0 = 4.73 + k * 0.17
            if t0 <= t < t0 + 0.55:
                p = (t - t0) / 0.55
                x = lerp(wx + 20, gx, ease_in_out(p))
                y = lerp(wy - 100, gy - 20, p) - math.sin(math.pi * p) * 150
                put(cv, coin(92, mark=""), x, y, al * (1 - ease_in_cubic(max(0, p - 0.7) / 0.3)), 1.0, p * 360)
        # ... then the price tag turns 0 and coins stay
        for k in range(3):
            t0 = 5.95 + k * 0.17
            if t0 <= t < t0 + 0.45:
                p = (t - t0) / 0.45
                x = lerp(gx, wx + 20, ease_in_out(p))
                y = lerp(gy - 20, wy - 100, p) - math.sin(math.pi * p) * 120
                put(cv, coin(92, mark=""), x, y, al * clamp(p * 4), 1.0, -p * 360)
        if t >= 6.4:
            pop(cv, coin(84, mark=""), wx - 40, wy - 175, t, 6.4, 0.3, al)
        mood = "worried" if t < 5.73 else "happy"
        pop(cv, face_i(230, mood), CX, 475, t, 4.4, 0.35, al, 0.0)
        if mood == "worried":
            put(cv, X("!", 100, RD, 90), 690 + 6 * math.sin(t * 40), 420, al * clamp((t - 5.2) / 0.1), 1.0, 12 * math.sin(t * 25))
        tagtxt = "?" if t < 5.73 else "0"
        pop(cv, glow(tag_i(tagtxt, 230, 116, YL if t >= 5.73 else (190, 186, 214), 80), YL if t >= 5.73 else (120, 110, 190), 14, 0.7),
            gx + 30, gy - 215, t, 4.6, 0.35, al, 0.0)
        if t >= 5.73 and t < 5.95:
            sparks(cv, t, 5.73, gx + 30, gy - 215, 20, (255, 224, 120), 9, 0.5, 300, 5)
        # loss meter
        if t >= 4.73:
            red = t < 6.33
            lab = "YO‘QOTISH" if red else "YO‘QOTISH: 0"
            col = RD if red else GR
            w_ = 560 if red else 760
            put(cv, card(w_, 100, 50, 70, 200, 22, 12, 0.5, border=col), CX, 892, al * clamp((t - 4.73) / 0.15))
            if t < 6.33:
                put(cv, X(lab, 60, col, 520), CX, 892, al)
            if t >= 6.33:
                p = (t - 6.33) / 0.2
                put(cv, X(lab, 60, col, 700), CX - 20, 892, al * clamp(p * 3), 1 + 0.1 * (1 - ease_out_cubic(p)))
        if t >= 7.132:
            pop(cv, check(96, GR, 16), CX + 345, 892, t, 7.132, 0.3, al)
            sparks(cv, t, 7.132, CX + 345, 892, 16, (120, 255, 190), 3, 0.5, 260, 5)

    # ---------------- D/E. the chocolate experiment (2 sent -> 1 sent: flat; 1 sent -> 0: jump)
    def level(t):
        if t < 8.1:
            return 0.0
        base = 0.30 * ease_out_cubic((t - 8.1) / 0.5)
        if t >= 9.93:
            base = 0.30 + 0.015 * ease_out_cubic((t - 9.93) / 0.2)
        if t >= 13.62:
            base = lerp(0.315, 1.0, ease_out_cubic((t - 13.62) / 0.62))
        return base

    CROWD = [(-80, 0.00, YL), (1160, 0.07, CY), (-80, 0.14, PK), (1160, 0.21, GR), (-80, 0.28, WHITE), (1160, 0.35, YL)]

    def sc_choco(cv, t):
        al = win(t, 7.7, 15.15, 0.12, 0.22)
        if al <= 0:
            return
        chx, chy = 305, 735
        gxx, gyy = 835, 745
        pop(cv, rrect(250, 62, 31, YL), CX, 398, t, 7.75, 0.3, al)
        pop(cv, X("TAJRIBA", 40, DARK, 220), CX, 398, t, 7.75, 0.3, al)
        pop(cv, X("Shampanier, Mazar va Ariely, 2007", 36, MUTE, 780, "b"), CX, 456, t, 7.9, 0.3, al)
        SPOTS = [(-175, -95), (180, -95), (-190, 60), (200, 60), (-95, -150), (100, -150)]
        for j, (x0, d0, col) in enumerate(CROWD):          # crowd rushes in once it is free (peeks out from behind the bar)
            ts = 13.62 + d0
            if t < ts:
                continue
            p = ease_out_cubic((t - ts) / 0.7)
            tx, ty = chx + SPOTS[j][0], chy + SPOTS[j][1]
            put(cv, face_i(110, "happy", col), lerp(x0, tx, p), lerp(ty + 160, ty, p), al * clamp(p * 2), 1.0)
        pop(cv, glow(choco_art(380), (255, 150, 90), 20, 0.5), chx, chy, t, 7.833, 0.42, al, rise=50)
        pop(cv, X("SHOKOLAD", 50, WHITE, 340), chx, chy + 160, t, 8.13, 0.3, al)
        pop(cv, X("TALAB", 50, WHITE, 240), gxx, 520, t, 8.2, 0.3, al)
        jit = 0.0
        if 13.0 <= t < 13.62:
            jit = 5 * math.sin(t * 70) * (t - 13.0) / 0.62
        gauge(cv, gxx, gyy, 200, 390, level(t), al * clamp((t - 8.1) / 0.2), jit)
        # price tag
        tt = "2¢" if t < 9.93 else ("1¢" if t < 12.722 else "0")
        t0_ = 9.132 if t < 9.93 else (9.93 if t < 12.722 else 12.722)
        if t >= 9.132:
            zero = tt == "0"
            lay = tag_i(tt, 250, 125, YL if zero else (206, 200, 235), 88)
            if zero:
                lay = glow(lay, YL, 22, 1.2)
            k_ = clamp((t - t0_) / 0.3)
            sc = 1 + (0.9 if zero else 0.4) * (1 - ease_out_cubic(k_)) * (1 if k_ < 1 else 0)
            put(cv, lay, chx + 150, chy - 95, al * clamp(k_ * 3), sc * (1.1 if zero else 1.0), 10 + 4 * math.sin(t * 3))
        if t >= 12.722 and t < 14.4:
            sparks(cv, t, 12.722, chx + 150, chy - 95, 26, (255, 224, 120), 3, 0.9, 520, 7)
        # "about the same"
        if 11.03 <= t < 12.9:
            pop(cv, G("≈", 150, (255, 244, 190), YL), gxx, gyy - 40, t, 11.032, 0.3, al * (1 - clamp((t - 12.7) / 0.2)))
        # the jump
        if t >= 13.62:
            ph = clamp((t - 13.62) / 0.62)
            ar = arrow(240, 26, GR)
            put(cv, ar, gxx + 150, gyy + 40 - 130 * ease_out_cubic(ph), al * clamp(ph * 3), 1.0, 90)
        if t >= 14.22:
            sparks(cv, t, 14.222, gxx, gyy - 200, 46, (255, 120, 205), 11, 1.0, 700, 8)
            rays(cv, gxx, gyy - 190, t, (255, 140, 220), 12, 0.12 * clamp((15.0 - t) / 0.8), 14)

    # ---------------- F. the door: free gets them in, only value makes them stay
    def sc_door(cv, t):
        al = win(t, 15.0, 19.4, 0.14, 0.22)
        if al <= 0:
            return
        dw, dh = 300, 420
        dx, dy = CX, 676
        pop(cv, door_frame(dw, dh), dx, dy + dh / 2 - dh / 2 + 8, t, 15.05, 0.4, al, rise=50)
        op = ease_in_out((t - 15.62) / 0.5)
        if op > 0:
            put(cv, door_room(dw, dh), dx, dy, al * clamp(op * 3))
            rays(cv, dx, dy, t, YL, 10, 0.07 * op, 10)
        sx = 1 - 0.86 * op
        left = dx - dw / 2
        if t >= 15.05:
            lk = clamp((t - 15.05) / 0.3)
            put_xs(cv, door_leaf(dw, dh), left + dw * sx / 2, dy, sx, al * lk)
        # sign
        pop(cv, glow(X("BEPUL", 86, CY, 420), CY, 18, 1.1 + 0.3 * math.sin(t * 9)), CX, 412, t, 15.456, 0.35, al, rise=0)
        face_y = dy + 140
        # person walks in
        if 15.9 <= t < 17.0:
            p = clamp((t - 15.9) / 0.6)
            x = lerp(110, dx, ease_in_out(p))
            sc = lerp(1.0, 0.45, ease_in_cubic(clamp((t - 16.3) / 0.35)))
            a_ = 1 - clamp((t - 16.55) / 0.2)
            put(cv, face_i(150, "happy", WHITE), x, face_y - 10 * (1 - sc), al * a_, sc)
        # empty room: "?" then he walks out unhappy
        if 16.7 <= t < 17.9:
            pop(cv, X("?", 150, (255, 244, 214), 120), dx, dy - 20, t, 16.7, 0.3, al * (1 - clamp((t - 17.6) / 0.25)))
        if 17.05 <= t < 18.15:
            p = clamp((t - 17.05) / 0.8)
            put(cv, face_i(150, "sad", WHITE), lerp(dx + 10, 960, ease_in_out(p)), face_y, al * (1 - clamp((t - 17.7) / 0.35)))
        # value arrives (gem) -> he comes back and stays
        if t >= 18.056:
            kp = clamp((t - 18.056) / 0.45)
            put(cv, glow(gem_art(170), CY, 26, 1.1), dx, dy - 25 + 12 * math.sin(t * 5), al * clamp(kp * 3), (0.4 + 0.6 * ease_out_back(kp, 1.6)))
            sparks(cv, t, 18.056, dx, dy - 25, 30, (160, 255, 255), 6, 0.9, 520, 6)
            rays(cv, dx, dy - 25, t, (160, 250, 255), 12, 0.09 * clamp((19.4 - t) / 0.8), 12)
        if t >= 18.3:
            p = clamp((t - 18.3) / 0.45)
            put(cv, face_i(150, "happy", WHITE), lerp(960, dx + 70, ease_out_cubic(p)), face_y, al * clamp(p * 3), lerp(1.0, 0.7, p))
        if t >= 18.756:
            pop(cv, check(120, GR, 20), dx + 215, dy + 150, t, 18.756, 0.3, al)

    # ---------------- G. "Bepul - eshik. Qiymat - qolish sababi."
    def sc_lock(cv, t):
        al = win(t, 19.2, 22.55, 0.12, 0.22)
        if al <= 0:
            return
        pop(cv, card(900, 168, 56, 28, 100, 26, 16, 0.5, border=CY), CX, 450, t, 19.3, 0.35, al, rise=50)
        pop(cv, GG("BEPUL", 100, (210, 255, 255), CY, 360, r=20, k=1.0), 270, 450, t, 19.326, 0.35, al)
        if t >= 19.926:
            pop(cv, arrow(100, 22, MUTE), 500, 450, t, 19.926, 0.25, al)
            pop(cv, X("ESHIK", 100, WHITE, 280), 715, 450, t, 19.926, 0.35, al)
            put(cv, door_leaf(70, 100), 915, 450, al * clamp((t - 19.926) / 0.2) * 0.9)
        pop(cv, card(900, 330, 56, 28, 100, 26, 16, 0.5, border=PK), CX, 700, t, 20.75, 0.35, al, rise=50)
        pop(cv, GG("QIYMAT", 100, (255, 236, 200), (255, 90, 190), 400, r=20, k=1.0, col=(255, 90, 190)), 300, 640, t, 20.826, 0.35, al)
        if t >= 20.826:
            put(cv, glow(gem_art(120), CY, 20, 1.0), 850, 640 + 6 * math.sin(t * 4), al * clamp((t - 20.826) / 0.25))
        if t >= 21.526:
            pop(cv, arrow(110, 22, MUTE), 190, 770, t, 21.526, 0.25, al)
            pop(cv, X("QOLISH SABABI", 80, WHITE, 690), 600, 770, t, 21.526, 0.35, al)
        if t >= 21.926:
            sparks(cv, t, 21.926, CX, 860, 34, (255, 150, 220), 4, 0.9, 520, 6)

    # ---------------- H. call to action: send it, comment, subscribe
    def sc_cta(cv, t):
        al = win(t, 22.45, 99, 0.12, 0.2)
        if al <= 0:
            return
        if t < 23.9:
            fa = al * (1 - clamp((t - 23.65) / 0.25))
            pop(cv, face_i(190, "happy", YL), 230, 610, t, 22.6, 0.35, fa)
            pop(cv, shop_art(300), 830, 610, t, 22.75, 0.4, fa)
            if 22.95 <= t < 23.45:
                p = (t - 22.95) / 0.5
                x = lerp(300, 780, ease_in_out(p))
                y = 600 - math.sin(math.pi * p) * 200
                put(cv, plane_icon(110), x, y, fa, 1.0 - 0.3 * p, -18)
            if t >= 23.45:
                pop(cv, check(120, GR, 20), 830, 440, t, 23.45, 0.3, fa)
                sparks(cv, t, 23.45, 830, 600, 24, (160, 255, 220), 5, 0.7, 380, 6)
            pill = card(780, 92, 46, 30, 120, 20, 10, 0.5, border=CY)
            pop(cv, pill, CX, 860, t, 22.9, 0.3, fa)
            put(cv, plane_icon(52), 270, 860, fa * clamp((t - 22.9) / 0.3))
            pop(cv, X("Do‘stingga ham yubor", 44, WHITE, 560, "b"), 600, 860, t, 22.9, 0.3, fa)
        if t >= 23.8:
            pop(cv, rrect(380, 64, 32, YL), CX, 372, t, 23.85, 0.3, al)
            pop(cv, X("IZOHDA YOZ", 40, DARK, 340), CX, 372, t, 23.85, 0.3, al)
            pop(cv, card(940, 170, 52, 30, 110, 26, 16, 0.55, border=YL), CX, 480, t, 23.9, 0.35, al, rise=40)
            pop(cv, X("Bepul sinov berganmisan?", 58, WHITE, 860), CX, 480, t, 24.0, 0.35, al)
            pop(cv, card(940, 250, 52, 30, 110, 26, 16, 0.55, border=CY), CX, 700, t, 24.3, 0.4, al, rise=50)
            pop(cv, logo(140, CY, (6, 4, 26), (6, 4, 26)), 175, 700, t, 24.4, 0.35, al)
            pop(cv, X("@narxtili", 60, WHITE, 340), 440, 672, t, 24.5, 0.3, al)
            pop(cv, X("Har 2 kunda bitta dars", 32, MUTE, 340, "b"), 440, 738, t, 24.6, 0.3, al)
            sub = t >= 26.017
            press = clamp((t - 26.017) / 0.14)
            bc = GR if sub else CY
            bs = 1.0 - 0.10 * math.sin(math.pi * min(1, press * 1.4)) if sub else 1.0
            pop(cv, rrect(260, 100, 50, bc), 835, 700, t, 24.7, 0.3, al, 0.0)
            if sub:
                put(cv, rrect(260, 100, 50, bc), 835, 700, al, bs)
                put(cv, check(70, DARK, 14), 835, 700, al * clamp(press * 3), bs)
            else:
                pop(cv, X("OBUNA BO‘L", 38, DARK, 220), 835, 700, t, 24.7, 0.3, al)
            if t >= 26.1:
                swing = 22 * math.sin((t - 26.1) * 16) * math.exp(-(t - 26.1) * 3)
                put(cv, glow(bell_art(100), YL, 16, 0.9), 890, 566, al * clamp((t - 26.1) / 0.12), 1.0, swing)
            if t >= 26.017:
                sparks(cv, t, 26.017, 835, 700, 26, (140, 255, 200), 6, 0.8, 420, 6)

    cam = (Cam(1.04).key(1.9, 1.06, 0, 16).key(4.3, 1.05, -10, 0).key(7.7, 1.06, 0, -12).key(9.9, 1.08, 24, 0).key(12.3, 1.05, 0, 0)
           .key(13.62, 1.09, -6, 10).key(15.1, 1.05, 0, 0).key(17.0, 1.07, 0, -10).key(19.2, 1.06, -12, 0).key(22.5, 1.04, 0, 0)
           .key(24.4, 1.06, 0, 10).key(27.0, 1.09))
    cam.shake(3.753, 18, 0.55).shake(5.23, 8, 0.4).shake(12.722, 16, 0.5).shake(14.222, 26, 0.65).shake(18.056, 9, 0.4).shake(21.926, 12, 0.5)
    cam.punch(13.62, 0.05).punch(14.222, 0.07).punch(19.326, 0.04).punch(26.017, 0.04)

    caps = lambda cv, t: captions(cv, tim, t, y=1405, size=72, maxw=940, n=3)

    return PremiumReel(tim, [host_layer(host), sc_hook, sc_risk, sc_fear, sc_choco, sc_door, sc_lock, sc_cta], world="neon", cam=cam,
                       seed=19, bokeh_n=46, vignette=0.55, grain=0.42, bloom=0.30,
                       flashes=[(1.95, 0.10), (12.722, 0.14), (14.222, 0.22), (18.056, 0.10), (21.926, 0.12)],
                       chroma_at=[(3.753, 12, 0.3), (12.722, 10, 0.25), (14.222, 14, 0.35)],
                       whips=[(1.85, 0.28, 90, 90), (4.25, 0.28, 100, 0), (7.7, 0.28, 90, 90), (15.0, 0.30, 100, 0), (19.2, 0.28, 90, 90), (22.45, 0.30, 100, 0)],
                       sweeps=[(7.6, 0.55), (15.0, 0.6), (19.3, 0.6)],
                       top=[caps])


def host_layer(host):
    def f(cv, t):
        host.draw(cv, t)
    return f


# ----------------------------------------------------------------------------- sound design
def sfx(tim):
    ev = [(0.02, "whoosh", 0.55), (1.1, "ding", 0.5)]
    ev += [(0.15 + i * 0.26, "tick", 0.20) for i in range(7)]
    ev += [(1.85, "whoosh", 0.5), (1.953, "pop", 0.7), (2.5, "pop", 0.55), (3.152, "stamp", 0.7), (3.553, "whoosh", 0.4),
           (3.753, "stamp", 0.95), (3.753, "glitch", 0.4), (3.95, "ding", 0.7), (3.96, "sparkle", 0.6)]
    ev += [(4.25, "whoosh", 0.5), (4.33, "pop", 0.6), (4.4, "pop", 0.5), (4.73, "coin", 0.6), (4.9, "coin", 0.6), (5.07, "coin", 0.6),
           (5.23, "thump", 0.5), (5.73, "pop", 0.7), (5.75, "sparkle", 0.5), (5.95, "coin", 0.5), (6.12, "coin", 0.5), (6.29, "coin", 0.5),
           (6.33, "pop", 0.6), (7.132, "ding", 0.75), (7.14, "sparkle", 0.6)]
    ev += [(7.7, "whoosh", 0.5), (7.833, "pop", 0.7), (8.13, "pop", 0.5), (8.2, "pop", 0.5), (9.132, "pop", 0.6), (9.93, "pop", 0.6),
           (9.95, "tick", 0.4), (11.032, "pop", 0.5)]
    ev += [(12.722, "impact", 0.75), (12.73, "sparkle", 0.7), (14.222, "riser:1.5", 0.7), (14.222, "impact", 0.95), (14.23, "sparkle", 0.9), (14.3, "ding", 0.7)]
    ev += [(13.62 + i * 0.07, "tick", 0.25) for i in range(6)] + [(13.7 + i * 0.1, "whoosh", 0.18) for i in range(0, 5, 2)]
    ev += [(15.0, "whoosh", 0.5), (15.05, "pop", 0.6), (15.456, "pop", 0.6), (15.62, "clank", 0.6), (15.95, "whoosh", 0.3), (16.7, "pop", 0.5),
           (17.05, "whoosh_dn", 0.4), (18.056, "ding", 0.85), (18.06, "sparkle", 0.8), (18.3, "whoosh", 0.3), (18.756, "ding", 0.6)]
    ev += [(19.2, "whoosh", 0.5), (19.326, "pop", 0.7), (19.926, "stamp", 0.75), (20.75, "whoosh", 0.35), (20.826, "pop", 0.7),
           (21.526, "pop", 0.6), (21.926, "impact", 0.8), (21.93, "sparkle", 0.9), (21.95, "ding", 0.7)]
    ev += [(22.45, "whoosh", 0.5), (22.6, "pop", 0.6), (22.75, "pop", 0.5), (22.95, "whoosh", 0.4), (23.45, "ding", 0.7), (23.46, "sparkle", 0.6),
           (23.9, "pop", 0.6), (24.3, "pop", 0.6), (24.7, "pop", 0.5), (26.017, "pop", 0.85), (26.02, "ding", 0.8), (26.1, "ding", 0.55), (26.1, "sparkle", 0.6)]
    ev += [(tim.end0, "whoosh", 0.4), (tim.end0 + 0.1, "ding", 0.5)]
    return ev
