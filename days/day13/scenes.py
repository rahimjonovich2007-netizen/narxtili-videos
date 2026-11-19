"""Day 13 - Birinchi 10 mijoz (Kichik biznes).  Look: cream theme, top gradient, dots overlay.
Visual metaphor: a switchback road map; 10 customer markers gather one by one (counter 0 -> 10), every step has its own small
animation (warning sign -> person, typing bubble -> messages, gift + review stars, '?' bubble hopping along the road, post card + hearts).
Animated explainer (objects move and transform with the words) - NOT text-only."""
import math
from functools import lru_cache

import numpy as np
from PIL import ImageFilter
from scipy.spatial import cKDTree

from nt_kit import *

# ----------------------------------------------------------------------------- road geometry (canvas px)
RAD = 130
Y1, Y2, Y3 = 1400, 1140, 880          # three horizontal runs (bottom -> top)
XR, XL = 810, 250                      # centres of the right / left U-turns
X0, X3 = 120, 900                      # road start / end
HW = 28                                # half width of the road
AMBER_D = (222, 128, 0)
PCOL = [(31, 64, 115), (222, 128, 0), (48, 160, 104), (200, 70, 90), (104, 84, 186),
        (20, 140, 160), (236, 150, 40), (60, 100, 180), (186, 78, 138), (40, 120, 90)]


def _build_path():
    pts = []

    def seg(a, b, step=2.0):
        L = math.dist(a, b)
        n = max(1, int(round(L / step)))
        for i in range(n):
            pts.append((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n))

    def arc(cx, cy, sign):
        n = int(round(math.pi * RAD / 2.0))
        for i in range(n):
            a = -math.pi / 2 + math.pi * i / n
            pts.append((cx + sign * RAD * math.cos(a), cy - RAD * math.sin(a)))

    seg((X0, Y1), (XR, Y1))
    arc(XR, (Y1 + Y2) / 2, +1)
    seg((XR, Y2), (XL, Y2))
    arc(XL, (Y2 + Y3) / 2, -1)
    seg((XL, Y3), (X3, Y3))
    pts.append((X3, Y3))
    Pn = np.array(pts, float)
    Dn = np.r_[0.0, np.cumsum(np.hypot(*np.diff(Pn, axis=0).T))]
    return Pn, Dn


PATH, DIST = _build_path()
LPATH = float(DIST[-1])
STOP_S = [(i + 0.5) / 10 * LPATH for i in range(10)]


def pos(s):
    s = min(max(s, 0.0), LPATH)
    return float(np.interp(s, DIST, PATH[:, 0])), float(np.interp(s, DIST, PATH[:, 1]))


POS = [pos(s) for s in STOP_S]
RX0, RY0, RX1, RY1 = 50, 800, 1030, 1480     # raster box of the road
RCX, RCY = (RX0 + RX1) / 2, (RY0 + RY1) / 2


@lru_cache(None)
def road_raster():
    yy, xx = np.mgrid[RY0:RY1, RX0:RX1]
    q = np.column_stack([xx.ravel(), yy.ravel()]).astype(np.float64)
    dist, idx = cKDTree(PATH).query(q)
    dist = dist.reshape(yy.shape).astype(np.float32)
    lab = DIST[idx].reshape(yy.shape).astype(np.float32)
    a_case = np.clip(HW + 7 - dist + 0.5, 0, 1)
    a_fill = np.clip(HW - dist + 0.5, 0, 1)
    ph = lab % 58
    dash = np.clip(np.minimum(ph, 32 - ph) + 0.5, 0, 1)
    a_dash = np.clip(4.5 - dist + 0.5, 0, 1) * dash
    pm = np.array((255, 255, 255), np.float32) * a_case[..., None]
    A = a_case.copy()
    for col, a in (((40, 56, 86), a_fill), ((255, 190, 60), a_dash)):
        c = np.array(col, np.float32)
        pm = c * a[..., None] + pm * (1 - a[..., None])
        A = a + A * (1 - a)
    rgb = pm / np.maximum(A[..., None], 1e-6)
    arr = np.dstack([rgb, A * 255]).clip(0, 255).astype(np.uint8)
    return arr, lab


@lru_cache(None)
def road_full():
    return Image.fromarray(road_raster()[0], "RGBA")


def road_partial(s_cur):
    arr, lab = road_raster()
    a = arr.copy()
    a[..., 3] = np.where(lab <= s_cur, a[..., 3], 0)
    return Image.fromarray(a, "RGBA")


# ----------------------------------------------------------------------------- helpers / icons
def _c(w, h, s=4): return Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0)), s


def with_shadow(im, pad=18, off=7, blur=8, a=70):
    w, h = im.size
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sh.paste((24, 34, 56, a), (pad, pad + off), im.getchannel("A"))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    out.alpha_composite(im, (pad, pad))
    return out


def bez(p0, p1, p2, s):
    return ((1 - s) ** 2 * p0[0] + 2 * (1 - s) * s * p1[0] + s * s * p2[0],
            (1 - s) ** 2 * p0[1] + 2 * (1 - s) * s * p1[1] + s * s * p2[1])


def pop(cv, layer, cx, cy, t, t0, al=1.0, yo=0.0, dur=0.45, s0=0.15, over=2.0, rot=0.0):
    p = (t - t0) / dur
    if p <= 0:
        return
    sc = s0 + (1 - s0) * ease_out_back(p, over)
    put(cv, layer, cx, cy + yo, al * ease_out_cubic(p * 2.5), max(0.02, sc), rot)


def chip(text, bg, fg=WHITE, size=36):
    t = txt(text, size, fg, "xb", maxw=620)
    w, h = t.width + 56, t.height + 14
    base = rrect(w, h, h // 2, bg).copy()
    base.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2))
    return base


@lru_cache(None)
def marker(i, d=100):
    col = PCOL[i % len(PCOL)]
    s, pad = 3, 22
    S = d + 2 * pad
    im = Image.new("RGBA", (S * s, S * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.ellipse([pad * s, pad * s, (pad + d) * s, (pad + d) * s], fill=(255, 255, 255, 255))
    ins = max(4, int(d * 0.07))
    dr.ellipse([(pad + ins) * s, (pad + ins) * s, (pad + d - ins) * s, (pad + d - ins) * s], fill=tuple(col) + (255,))
    im = im.resize((S, S), Image.LANCZOS)
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([pad, pad + 8, pad + d, pad + d + 8], fill=(24, 34, 56, 80))
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.alpha_composite(sh)
    out.alpha_composite(im)
    pr = person(int(d * 0.54), WHITE)
    out.alpha_composite(pr, ((S - pr.width) // 2, int(S / 2 - pr.height / 2 + d * 0.03)))
    return out


@lru_cache(None)
def slot(d=40):
    return disc(d, None, (176, 168, 146), 5)


@lru_cache(None)
def megaphone(sz):
    im, s = _c(sz, sz)
    dr = ImageDraw.Draw(im)
    P = lambda x, y: (x * sz * s, y * sz * s)
    amber, dark, navy = AMBER + (255,), (214, 138, 0, 255), NAVY + (255,)
    dr.rounded_rectangle([*P(0.17, 0.58), *P(0.31, 0.92)], radius=int(0.04 * sz * s), fill=navy)
    dr.rounded_rectangle([*P(0.06, 0.34), *P(0.30, 0.66)], radius=int(0.06 * sz * s), fill=dark)
    dr.polygon([P(0.28, 0.34), P(0.80, 0.10), P(0.80, 0.90), P(0.28, 0.66)], fill=amber)
    dr.rounded_rectangle([*P(0.76, 0.08), *P(0.86, 0.92)], radius=int(0.05 * sz * s), fill=dark)
    return im.resize((sz, sz), Image.LANCZOS)


@lru_cache(None)
def wave(sz, k):
    im, s = _c(sz, sz)
    dr = ImageDraw.Draw(im)
    r = sz * (0.16 + 0.12 * k)
    c = sz * 0.5
    dr.arc([(c - r) * s, (c - r) * s, (c + r) * s, (c + r) * s], -42, 42, fill=NAVY + (255,), width=int(sz * 0.032 * s))
    return im.resize((sz, sz), Image.LANCZOS)


@lru_cache(None)
def magnifier(sz):
    im, s = _c(sz, sz)
    dr = ImageDraw.Draw(im)
    cx = cy = sz * 0.40 * s
    r = sz * 0.30 * s
    navy = NAVY + (255,)
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 80), outline=navy, width=int(sz * 0.06 * s))
    a = math.radians(45)
    p0 = (cx + (r + sz * 0.02 * s) * math.cos(a), cy + (r + sz * 0.02 * s) * math.sin(a))
    p1 = (sz * 0.90 * s, sz * 0.90 * s)
    dr.line([p0, p1], fill=navy, width=int(sz * 0.10 * s))
    for q in (p1,):
        rr = sz * 0.05 * s
        dr.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=navy)
    return im.resize((sz, sz), Image.LANCZOS)


@lru_cache(None)
def warn(sz):
    im, s = _c(sz, sz)
    dr = ImageDraw.Draw(im)
    P = lambda x, y: (x * sz * s, y * sz * s)
    red = RED + (255,)
    dr.polygon([P(0.5, 0.10), P(0.93, 0.86), P(0.07, 0.86)], fill=red)
    dr.line([P(0.5, 0.10), P(0.93, 0.86), P(0.07, 0.86), P(0.5, 0.10)], fill=red, width=int(sz * 0.07 * s), joint="curve")
    im = im.resize((sz, sz), Image.LANCZOS)
    t = txt("!", int(sz * 0.52), WHITE, "xb")
    im.alpha_composite(t, ((sz - t.width) // 2, int(sz * 0.60 - t.height / 2)))
    return im


@lru_cache(None)
def reticle(sz, col):
    im, s = _c(sz, sz)
    dr = ImageDraw.Draw(im)
    c = sz * s / 2
    for r, w in ((0.46, 0.035), (0.30, 0.03), (0.13, 0.03)):
        R = r * sz * s
        dr.ellipse([c - R, c - R, c + R, c + R], outline=tuple(col) + (255,), width=int(w * sz * s))
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        dr.line([(c + dx * 0.34 * sz * s, c + dy * 0.34 * sz * s), (c + dx * 0.50 * sz * s, c + dy * 0.50 * sz * s)], fill=tuple(col) + (255,), width=int(0.035 * sz * s))
    return im.resize((sz, sz), Image.LANCZOS)


@lru_cache(None)
def gift(sz):
    im, s = _c(sz, sz)
    dr = ImageDraw.Draw(im)
    P = lambda x, y: (x * sz * s, y * sz * s)
    dr.rounded_rectangle([*P(0.12, 0.46), *P(0.88, 0.94)], radius=int(0.05 * sz * s), fill=(232, 80, 70, 255))
    dr.rounded_rectangle([*P(0.06, 0.30), *P(0.94, 0.50)], radius=int(0.05 * sz * s), fill=(200, 58, 50, 255))
    dr.rectangle([*P(0.44, 0.30), *P(0.56, 0.94)], fill=AMBER + (255,))
    dr.ellipse([*P(0.24, 0.08), *P(0.50, 0.32)], outline=AMBER + (255,), width=int(0.055 * sz * s))
    dr.ellipse([*P(0.50, 0.08), *P(0.76, 0.32)], outline=AMBER + (255,), width=int(0.055 * sz * s))
    return im.resize((sz, sz), Image.LANCZOS)


@lru_cache(None)
def star(d, fill):
    im, s = _c(d, d)
    dr = ImageDraw.Draw(im)
    pts = []
    for k in range(10):
        r = 0.5 if k % 2 == 0 else 0.23
        a = -math.pi / 2 + k * math.pi / 5
        pts.append((d * s * (0.5 + r * math.cos(a)), d * s * (0.54 + r * math.sin(a))))
    if fill:
        dr.polygon(pts, fill=tuple(fill) + (255,))
        dr.line(pts + [pts[0]], fill=tuple(fill) + (255,), width=int(d * 0.06 * s), joint="curve")
    else:
        dr.line(pts + [pts[0]], fill=(196, 188, 168, 255), width=int(d * 0.07 * s), joint="curve")
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def heart(d, col):
    im, s = _c(d, d)
    dr = ImageDraw.Draw(im)
    c = tuple(col) + (255,)
    r = d * 0.22 * s
    for cx in (0.30, 0.70):
        dr.ellipse([cx * d * s - r, 0.34 * d * s - r, cx * d * s + r, 0.34 * d * s + r], fill=c)
    dr.polygon([(0.095 * d * s, 0.43 * d * s), (0.905 * d * s, 0.43 * d * s), (0.5 * d * s, 0.90 * d * s)], fill=c)
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def bubble(w, h, fill, tail="l"):
    th = int(h * 0.30)
    im, s = _c(w, h + th)
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=int(h * 0.36 * s), fill=tuple(fill) + (255,))
    if tail == "l":
        dr.polygon([(w * 0.12 * s, (h - 8) * s), (w * 0.32 * s, (h - 8) * s), (w * 0.10 * s, (h + th) * s)], fill=tuple(fill) + (255,))
    else:
        dr.polygon([(w * 0.88 * s, (h - 8) * s), (w * 0.68 * s, (h - 8) * s), (w * 0.90 * s, (h + th) * s)], fill=tuple(fill) + (255,))
    return with_shadow(im.resize((w, h + th), Image.LANCZOS), pad=16, off=6, blur=7, a=60)


@lru_cache(None)
def review_card():
    w, h = 420, 160
    im, s = _c(w, h, 3)
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=30 * s, fill=(255, 255, 255, 255))
    base = im.resize((w, h), Image.LANCZOS)
    av = marker(1, 62)
    base.alpha_composite(av.crop((22, 22, 22 + 62, 22 + 62)), (20, 14))
    d2 = ImageDraw.Draw(base)
    d2.rounded_rectangle([102, 26, 380, 38], radius=6, fill=(222, 215, 198, 255))
    d2.rounded_rectangle([102, 50, 330, 62], radius=6, fill=(222, 215, 198, 255))
    return with_shadow(base, pad=16, off=6, blur=8, a=60)


@lru_cache(None)
def post_card():
    w, h = 320, 176
    im, s = _c(w, h, 3)
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=28 * s, fill=(255, 255, 255, 255))
    dr.ellipse([18 * s, 14 * s, 50 * s, 46 * s], fill=AMBER + (255,))
    dr.rounded_rectangle([60 * s, 20 * s, 190 * s, 30 * s], radius=5 * s, fill=(222, 215, 198, 255))
    dr.rounded_rectangle([60 * s, 36 * s, 140 * s, 44 * s], radius=4 * s, fill=(232, 226, 212, 255))
    dr.rounded_rectangle([18 * s, 58 * s, (w - 18) * s, 126 * s], radius=14 * s, fill=(255, 228, 164, 255))
    base = im.resize((w, h), Image.LANCZOS)
    pr = person(46, (255, 255, 255))
    base.alpha_composite(pr, (w // 2 - pr.width // 2 - 40, 66))
    base.alpha_composite(pr, (w // 2 - pr.width // 2 + 40, 66))
    base.alpha_composite(heart(30, RED), (18, 134))
    for k in range(5):
        base.alpha_composite(star(26, AMBER), (150 + k * 30, 136))
    return with_shadow(base, pad=16, off=6, blur=8, a=60)


def burst(cv, cx, cy, t, t0, n=16, dur=0.9, al=1.0, spread=0):
    p = (t - t0) / dur
    if p <= 0 or p >= 1:
        return
    cols = (AMBER, RED, GREEN, (60, 100, 180), (255, 255, 255))
    for k in range(n):
        if spread:     # fan outwards (sideways and up) from the edge of the counter card
            a = (-math.pi / 2 + spread * (0.25 + 1.0 * k / max(1, n - 1))) if spread > 0 else (-math.pi / 2 - (0.25 + 1.0 * k / max(1, n - 1)))
        else:
            a = 2 * math.pi * k / n + 0.4 * (k % 3)
        r = (30 + 95 * (1 + (k % 3) * 0.25)) * ease_out_cubic(p)
        put(cv, disc(16 + 6 * (k % 3), cols[k % 5]), cx + r * math.cos(a), cy + r * math.sin(a), al * (1 - p))


# ----------------------------------------------------------------------------- the video
def build(tim):
    set_theme("cream")       # layers below are built before Reel() sets the theme
    S, ws = tim.S, tim.ws
    END0 = tim.end0
    road_raster()            # warm the cache before the render pool forks

    RS, RD = S(2) - 0.15, 1.5                       # road drawing
    # arrival times of the 10 markers
    A1 = [ws(18) - 0.10 + 0.46, ws(18) + 0.03 + 0.46, ws(18) + 0.16 + 0.46]
    T4 = ws(29) + 0.12
    HOP0, HOP1 = ws(34), ws(34) + 0.30             # '?' bubble leaves the dialog / lands on the road at marker 4
    HOPD = 1.06
    s4, s7 = STOP_S[4], STOP_S[7]
    hop_t = lambda s: HOP1 + HOPD * (s - s4) / (s7 - s4)
    ARR = [ws(12), A1[0], A1[1], A1[2], T4, hop_t(STOP_S[5]), hop_t(STOP_S[6]), hop_t(STOP_S[7]), ws(40) + 0.55, ws(40) + 0.70]
    GIFT0 = ws(22)
    GIFT_ARR = GIFT0 + 0.62
    WAVE0 = S(8) + 0.12
    PULSE0, PULSED = ws(47) + 0.02, 1.2
    CARD0 = S(9) - 0.0

    # ---------------------------------------------------------------- text scenes
    def tscene(a, b, items, fo=0.10):
        def fn(cv, t):
            v = vis(t, a, b, fo)
            if not v:
                return
            al, yo = v
            for layer, y, t0 in items:
                item(cv, layer, 540, y, t, t0, al, yo)
        return fn

    def cscene(a, b, text, bg=None, size=34):
        lay = chip(text, bg or TH.acc, WHITE, size)

        def fn(cv, t):
            v = vis(t, a, b, 0.14)
            if not v:
                return
            al, yo = v
            item(cv, lay, 540, 392, t, a + 0.06, al, yo, dur=0.3, rise=14)
        return fn

    WA = (0.0, S(1) - 0.10)
    WB = (WA[1], S(2) - 0.10)
    T1a = (WB[1], ws(9) - 0.04)
    T1b = (T1a[1], S(3) - 0.10)
    T2a = (T1b[1], S(4) - 0.10)
    T2b = (T2a[1], S(5) - 0.10)
    T3a = (T2b[1], ws(25) - 0.05)
    T3b = (T3a[1], S(6) - 0.10)
    T4a = (T3b[1], ws(34) - 0.05)
    T4b = (T4a[1], S(7) - 0.10)
    T5 = (T4b[1], S(8) - 0.10)
    T6a = (T5[1], ws(45) - 0.05)
    T6b = (T6a[1], ws(47) - 0.05)
    T6c = (T6b[1], S(9) - 0.10)
    T7 = (T6c[1], END0)

    Y_A, Y_B, Y_C = 490, 602, 546           # top text lines (two lines / a single line)

    # ---------------------------------------------------------------- hook
    def sc_hook_a(cv, t):
        v = vis(t, *WA)
        if not v:
            return
        al, yo = v
        item(cv, txt("Reklama", 128), 540, 520, t, -0.12, al, yo)
        item(cv, txt2("byudjeting ", "yo‘q.", 104, TH.fg, RED), 540, 655, t, max(0.3, ws(1) - 0.15), al, yo)
        mx, my, sz = 470, 1090, 400
        p0 = prog(t, -0.1, 0.5)
        stamp = ws(2) - 0.02
        sh = 0.0
        if t > stamp:
            sh = math.exp(-(t - stamp) * 5) * math.sin((t - stamp) * 38) * 7
        dim = 1 - 0.55 * ease_out_cubic(prog(t, stamp, 0.25))
        if p0 > 0:
            put(cv, megaphone(sz), mx, my + yo, al * ease_out_cubic(p0) * dim, 0.85 + 0.15 * clamp(ease_out_back(p0, 1.3), 0, 1.3), sh)
        if t < stamp + 0.05:
            wx, wy = mx + 0.36 * sz, my
            for k in range(3):
                a_ = 0.30 + 0.70 * max(0.0, math.sin(t * 10 - k * 1.1))
                put(cv, wave(sz, k), wx + 6 * k, wy + yo, al * a_ * clamp(1 - (t - stamp + 0.05) * 10))
        q = prog(t, stamp, 0.4)
        if q > 0:
            put(cv, cross(330, RED, 44), mx + 20, my + yo, al * ease_out_cubic(q * 2), 0.6 + 0.4 * clamp(ease_out_back(q, 2.2), 0, 1.3))

    def sc_hook_b(cv, t):
        v = vis(t, *WB)
        if not v:
            return
        al, yo = v
        item(cv, txt("Mijozni", 112), 540, 520, t, WB[0] + 0.06, al, yo)
        item(cv, txt2("qanday ", "topasan?", 104, TH.fg, TH.acc), 540, 650, t, ws(4) - 0.15, al, yo)
        pg = ease_out_cubic(prog(t, WB[0] + 0.1, 0.4))
        put(cv, person(380, (214, 206, 186)), 540, 1090 + yo, al * pg, 0.9 + 0.1 * pg)
        qy = 14 * math.sin(t * 6)
        put(cv, txt("?", 200, TH.acc), 540, 1075 + yo + qy, al * ease_out_cubic(prog(t, ws(5) - 0.4, 0.3)))
        mg = ease_out_cubic(prog(t, ws(3) - 0.1, 0.35))
        mxp = 540 + 150 * math.cos(t * 3.0)
        myp = 1110 + 85 * math.sin(t * 4.1)
        put(cv, magnifier(260), mxp, myp + yo, al * mg, 0.8 + 0.2 * mg, -14 * math.sin(t * 3.0))

    # ---------------------------------------------------------------- step texts
    def mk_texts():
        out = []
        # step 1
        out.append(tscene(*T1a, [(fit((("Bitta aniq ", TH.fg), ("muammo", RED)), 96, "xb", 900), Y_C, ws(6) - 0.10)]))
        out.append(tscene(*T1b, [(txt("va bitta aniq", 92), Y_A, T1b[0] + 0.06),
                                 (txt("odamni tanla.", 100, TH.acc), Y_B, ws(12) - 0.15)]))
        # step 2
        out.append(tscene(*T2a, [(txt("Tanishlaringga", 100), Y_A, S(3) - 0.08),
                                 (txt("yoz:", 100, TH.acc), Y_B, ws(15) - 0.15)]))
        out.append(tscene(*T2b, [(txt("“Sinab ko‘rmoqchimisan?", 72, TH.fg, "xb", 900), Y_A, S(4) - 0.06),
                                 (txt("Yordam beray.”", 100, TH.acc), Y_B, ws(18) - 0.12)]))
        # step 3
        out.append(tscene(*T3a, [(txt("Birinchi mijozga", 92), Y_A, S(5) - 0.06),
                                 (txt("sinov sifatida ber,", 92, TH.acc, "xb", 900), Y_B, ws(22) - 0.12)]))
        out.append(tscene(*T3b, [(txt("evaziga fikr", 100), Y_A, ws(25) - 0.10),
                                 (txt("va sharh so‘ra.", 100, TH.acc), Y_B, ws(27) - 0.10)]))
        # step 4
        out.append(tscene(*T4a, [(fit((("Har suhbat ", TH.fg), ("oxirida", TH.acc)), 96, "xb", 900), Y_C, S(6) - 0.06)]))
        out.append(tscene(*T4b, [(txt("yana kimga kerak", 96), Y_A, ws(34) - 0.10),
                                 (txt("bo‘lishi mumkin?", 100, TH.acc), Y_B, ws(37) - 0.12)]))
        # step 5
        out.append(tscene(*T5, [(txt("Natijani", 104), Y_A, S(7) - 0.06),
                                (txt("Instagramda ko‘rsat.", 100, TH.acc, "xb", 900), Y_B, ws(40) - 0.10)]))
        # payoff
        out.append(tscene(*T6a, [(txt("Dastlabki mijozlar", 92), Y_A, S(8) - 0.06),
                                 (txt("ko‘pincha", 104, TH.acc), Y_B, ws(44) - 0.10)]))
        lay = txt("reklamadan emas,", 96, TH.fg, "xb", 900)

        def sc_not(cv, t):
            v = vis(t, *T6b)
            if not v:
                return
            al, yo = v
            item(cv, lay, 540, Y_C, t, ws(45) - 0.10, al, yo)
            k = ease_out_cubic(prog(t, ws(45) + 0.30, 0.45))
            if k > 0:
                x0 = 540 - (lay.width - 16) / 2
                x1 = x0 + (lay.width - 16) * k
                poly(cv, [(x0, Y_C + yo + 2), (x1, Y_C + yo + 2)], RED, 12, 1.0, al)
        out.append(sc_not)
        out.append(tscene(*T6c, [(txt("suhbatdan", 112, TH.acc), Y_A, ws(47) - 0.10),
                                 (txt("keladi.", 112), Y_B - 2, ws(48) - 0.12)]))
        # CTA
        out.append(tscene(*T7, [(txt("Boshlayotgan", 100), Y_A, S(9) - 0.04),
                                (txt2("do‘stingga ", "yubor.", 100, TH.fg, TH.acc), Y_B, ws(50) - 0.10)], fo=0.25))
        return out

    TEXTS = mk_texts()
    CHIPS = [cscene(T1a[0], T1b[1], "1-QADAM"), cscene(T2a[0], T2b[1], "2-QADAM"), cscene(T3a[0], T3b[1], "3-QADAM"),
             cscene(T4a[0], T4b[1], "4-QADAM"), cscene(T5[0], T5[1], "5-QADAM")]
    advice = chip("MASLAHAT", AMBER, NAVY, 28)

    def sc_advice(cv, t):
        v = vis(t, 0.5, END0 - 0.3, 0.2)
        if not v:
            return
        al, yo = v
        item(cv, advice, 868, 300, t, 0.55, al * 0.95, yo, dur=0.3, rise=10)

    # ---------------------------------------------------------------- the map (road + markers + counter)
    WM = (S(2) - 0.18, END0)
    P0 = POS[0]
    BADGE = (P0[0] + 40, P0[1] - 46)
    cnt_card = {False: rrect(420, 124, 62, WHITE, (230, 222, 204), 3), True: rrect(420, 124, 62, AMBER_D)}

    def draw_counter(cv, t, al, yo):
        done = [a for a in ARR if t >= a]
        n = len(done)
        last = max(done) if done else -9
        full = n == 10
        cy = 745
        put(cv, cnt_card[full], 540, cy + yo, al)
        put(cv, person(62, WHITE if full else TH.acc), 372, cy + yo, al)
        pp = prog(t, last, 0.4)
        sc = 1 + 0.45 * (1 - ease_out_cubic(pp)) * (1 if n else 0)
        put(cv, txt(str(n), 92, WHITE if full else NAVY), 480, cy + yo, al, sc)
        put(cv, txt("/ 10", 54, WHITE if full else (150, 142, 120)), 636, cy + 3 + yo, al)

    def map_draw(cv, t, al, yo, card=0.0):
        if card > 0:
            put(cv, rrect(1000, 800, 46, WHITE, (230, 222, 204), 4), 540, 1075 + yo, al * card)
        p = prog(t, RS, RD)
        if p <= 0:
            return
        sc = LPATH * p
        put(cv, road_full() if p >= 1 else road_partial(sc), RCX, RCY + yo, al)
        if 0 < p < 1:
            x, y = pos(sc)
            put(cv, disc(44, AMBER, WHITE, 6), x, y + yo, al)
        for i in range(10):
            x, y = POS[i]
            ts = RS + RD * STOP_S[i] / LPATH
            dy = -16 * math.sin(math.pi * clamp((t - (WAVE0 + i * 0.065)) / 0.45)) if t >= WAVE0 else 0
            if ts <= t < ARR[i] + 0.18:
                fo = 1 - prog(t, ARR[i], 0.18)
                pop(cv, slot(), x, y, t, ts, al * fo, yo, dur=0.3, over=1.6)
            if t >= ARR[i]:
                pop(cv, marker(i), x, y + dy, t, ARR[i], al, yo, dur=0.5, over=2.2)
                rp = (t - ARR[i]) / 0.5
                if 0 < rp < 1:
                    put(cv, disc(112, None, AMBER, 7), x, y + yo, al * 0.9 * (1 - rp), 0.8 + 1.1 * ease_out_cubic(rp))
        # badge on the first marker: warning -> check once the trial is handed over
        if t >= ARR[0] + 0.0 and t >= RS:
            bt = max(ARR[0], 4.85)
            if t < GIFT_ARR:
                pop(cv, warn(46), BADGE[0], BADGE[1], t, bt, al, yo, dur=0.35, s0=0.3, over=2.0)
            else:
                pop(cv, disc(46, GREEN, WHITE, 4), BADGE[0], BADGE[1], t, GIFT_ARR, al, yo, dur=0.4, s0=0.3, over=2.4)
                pop(cv, check(34, WHITE, 6), BADGE[0], BADGE[1], t, GIFT_ARR, al, yo, dur=0.4, s0=0.3, over=2.4)
        # payoff pulse: a light travelling along the road, each marker flashes as it passes
        pp = (t - PULSE0) / PULSED
        if 0 < pp < 1:
            x, y = pos(LPATH * pp)
            put(cv, disc(78, AMBER), x, y + yo, al * 0.55)
            put(cv, disc(44, WHITE), x, y + yo, al * 0.9)
        for i in range(10):
            tr = PULSE0 + PULSED * STOP_S[i] / LPATH
            rp = (t - tr) / 0.6
            if 0 < rp < 1:
                x, y = POS[i]
                put(cv, disc(116, None, AMBER, 8), x, y + yo, al * (1 - rp), 1.0 + 0.8 * ease_out_cubic(rp))
        if t >= RS + 1.0:
            draw_counter(cv, t, al, yo)
            burst(cv, 318, 745 + yo, t, ARR[9], n=9, dur=0.9, al=al, spread=-1)
            burst(cv, 762, 745 + yo, t, ARR[9], n=9, dur=0.9, al=al, spread=1)

    def sc_map(cv, t):
        v = vis(t, WM[0], WM[1], 0.25)
        if not v:
            return
        al, yo = v
        if t < CARD0:
            map_draw(cv, t, al, yo)
            return
        # CTA: the whole map becomes a card that shrinks and is handed to a friend
        c = ease_out_cubic(prog(t, CARD0, 0.3))
        tc = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        map_draw(tc, t, 1.0, 0.0, card=c)
        k = ease_in_out(prog(t, ws(50) - 0.25, 0.6))
        scl = lerp(1.0, 0.44, k)
        tx, ty = 540, lerp(1075, 960, k)
        put(cv, tc, tx, ty - scl * 115, al, scl)

    # ---------------------------------------------------------------- step overlays
    def sc_warn_fly(cv, t):
        a, b = ws(8) - 0.05, ws(12) + 0.1
        if not (a <= t < b):
            return
        if t < ws(9):
            pop(cv, warn(150), 640, 1010 + 6 * math.sin(t * 7), t, ws(8), 1.0, 0.0, dur=0.45, over=2.2)
        else:
            s = ease_in_out(prog(t, ws(9), ws(12) - ws(9) - 0.02))
            ctrl = (420, 1000)
            x, y = bez((640, 1010), ctrl, BADGE, s)
            put(cv, warn(150), x, y, clamp(1 - (s - 0.92) * 12) if s > 0.92 else 1.0, lerp(1.0, 0.31, s))

    def sc_reticle(cv, t):
        a, b = RS + RD - 0.05, ws(12) + 0.75
        v = vis(t, a, b, 0.25)
        if not v:
            return
        al, yo = v
        k = ease_out_cubic(prog(t, a, ws(12) - a))
        sz = 190
        put(cv, reticle(sz, TH.acc), P0[0], P0[1] + yo, al * ease_out_cubic(prog(t, a, 0.25)), lerp(2.6, 1.0, k), 40 * (1 - k))

    sx, sy = 410, 1272                     # centre of the step 2 chat bubble (region A)
    chat_a = bubble(220, 120, AMBER, "l")
    mini = bubble(92, 56, AMBER, "l").copy()
    for _k in range(3):
        mini.alpha_composite(disc(9, WHITE), (mini.width // 2 - 24 + _k * 19, 16 + 16 + 4))

    def sc_chat(cv, t):
        a, b = S(3) - 0.05, ws(20) + 0.1
        v = vis(t, a, b, 0.2)
        if not v:
            return
        al, yo = v
        pop(cv, chat_a, sx, sy, t, a, al, yo, dur=0.45)
        for k in range(3):
            dy = 9 * math.sin(t * 10 - k * 0.9)
            put(cv, disc(18, WHITE), sx - 40 + k * 40, sy - 16 + dy + yo, al * ease_out_cubic(prog(t, a + 0.25, 0.2)))
        for j, dep in enumerate((ws(18) - 0.10, ws(18) + 0.03, ws(18) + 0.16)):
            s = prog(t, dep, 0.46)
            if 0 < s < 1:
                tgt = POS[j + 1]
                ctrl = ((sx + tgt[0]) / 2, min(sy, tgt[1]) - 150)
                x, y = bez((sx + 30, sy - 30), ctrl, tgt, ease_in_out(s))
                put(cv, mini, x, y + yo, al * clamp((1 - s) * 5), lerp(1.15, 0.7, s), -10 * math.sin(s * 6))

    gift_img = gift(170)
    GX, GY = 400, 1268

    def sc_gift(cv, t):
        a, b = ws(20) - 0.05, GIFT_ARR + 0.05
        if not (a <= t < b):
            return
        if t < GIFT0:
            pop(cv, gift_img, GX, GY + 5 * math.sin(t * 8), t, ws(20), 1.0, 0.0, dur=0.45, over=2.2)
            return
        s = prog(t, GIFT0, GIFT_ARR - GIFT0)
        x, y = bez((GX, GY), (260, 1190), BADGE, ease_in_out(s))
        put(cv, gift_img, x, y, clamp((1 - s) * 6) if s > 0.83 else 1.0, lerp(1.0, 0.36, s), -20 * math.sin(s * 3.1))

    RCX0, RCY0 = 480, 1268
    card_img = review_card()
    stars_t = [ws(26) + 0.04 + 0.2 * k for k in range(5)]

    def sc_review(cv, t):
        a, b = ws(25) - 0.12, S(6) - 0.10
        v = vis(t, a, b, 0.2)
        if not v:
            return
        al, yo = v
        e = prog(t, a, 0.45)
        x, y = lerp(BADGE[0], RCX0, ease_out_cubic(e)), lerp(BADGE[1] - 20, RCY0, ease_out_cubic(e))
        put(cv, card_img, x, y + yo, al * ease_out_cubic(e * 2.5), lerp(0.3, 1.0, ease_out_back(e, 1.3)))
        if e >= 0.9:
            for k in range(5):
                px, py = RCX0 - 150 + 60 * k + 0, RCY0 + 44 + yo
                put(cv, star(46, None), px, py, al)
                p = prog(t, stars_t[k], 0.35)
                if p > 0:
                    put(cv, star(46, AMBER), px, py, al * ease_out_cubic(p * 3), 0.5 + 0.5 * clamp(ease_out_back(p, 2.6), 0, 1.4))

    bub_w = bubble(230, 118, WHITE, "l")
    bub_a = bubble(230, 118, AMBER, "r")
    HOPPER = disc(84, AMBER, WHITE, 6).copy()
    _q = txt("?", 62, WHITE)
    HOPPER.alpha_composite(_q, ((84 - _q.width) // 2, (84 - _q.height) // 2))
    LX, LY, RXb, RYb = 380, 1262, 590, 1298

    def sc_dialog(cv, t):
        a, b = S(6) - 0.05, HOP1 + 0.1
        v = vis(t, a, b, 0.15)
        if not v:
            return
        al, yo = v
        pop(cv, bub_w, LX, LY, t, a, al, yo, dur=0.4)
        pop(cv, bub_a, RXb, RYb, t, a + 0.35, al * (1 - prog(t, HOP0 + 0.05, 0.2)), yo, dur=0.4)
        for k in range(3):
            put(cv, disc(18, NAVY), LX - 40 + k * 40, LY - 14 + 8 * math.sin(t * 10 - k * 0.9) + yo, al * ease_out_cubic(prog(t, a + 0.2, 0.2)) * (1 if t < HOP0 else 0.4))
            put(cv, disc(18, WHITE), RXb - 40 + k * 40, RYb - 14 + 8 * math.sin(t * 10 - k * 0.9 + 2) + yo, al * ease_out_cubic(prog(t, a + 0.55, 0.2)) * (1 - prog(t, HOP0 - 0.05, 0.15)))

    def sc_hopper(cv, t):
        a, b = HOP0 - 0.05, hop_t(STOP_S[7]) + 0.35
        if not (a <= t < b):
            return
        end = hop_t(STOP_S[7])
        fo = 1 - prog(t, end, 0.3)
        if t < HOP1:
            s = ease_in_out(prog(t, HOP0, HOP1 - HOP0))
            x, y = bez((RXb, RYb), (RXb + 10, 1170), POS[4], s)
            put(cv, HOPPER, x, y, 1.0, lerp(0.7, 1.0, s))
            return
        s = lerp(s4, s7, clamp((t - HOP1) / HOPD))
        # amber trail along the road
        i0 = int(np.searchsorted(DIST, s4))
        i1 = int(np.searchsorted(DIST, s))
        if i1 - i0 > 2:
            pts = [tuple(p) for p in PATH[i0:i1:6]] + [pos(s)]
            poly(cv, pts, AMBER, 14, 1.0, 0.75 * fo)
        x, y = pos(s)
        put(cv, HOPPER, x, y - 10 * math.sin((t - HOP1) * 14), fo, 1.0 + 0.08 * math.sin((t - HOP1) * 14))

    pcard = post_card()
    PCX, PCY = 520, 1012

    def sc_post(cv, t):
        a, b = S(7) - 0.05, S(8) - 0.05
        v = vis(t, a, b, 0.2)
        if not v:
            return
        al, yo = v
        pop(cv, pcard, PCX, PCY, t, a, al, yo, dur=0.45)
        for j, (h0, tgt) in enumerate(((ws(40) + 0.18, POS[8]), (ws(40) + 0.33, POS[9]))):
            s = prog(t, h0, 0.42)
            if 0 < s < 1:
                src = (PCX - 70 + 140 * j, PCY - 60)
                x, y = bez(src, ((src[0] + tgt[0]) / 2, src[1] - 40), (tgt[0], tgt[1] + 20), ease_in_out(s))
                put(cv, heart(64, RED), x, y + yo, al * clamp((1 - s) * 4), lerp(1.0, 0.7, s))
        for k in range(3):
            q = ((t - a - 0.5 - k * 0.28) % 1.1) / 1.1
            if t > a + 0.5:
                put(cv, heart(30, RED), PCX - 90 + 90 * k, PCY - 50 - 70 * q + yo, al * (1 - q) * 0.9)

    # ---------------------------------------------------------------- payoff + CTA objects
    mega = megaphone(210)
    bub_p1 = bubble(190, 100, AMBER, "l")
    bub_p2 = bubble(190, 100, WHITE, "r")

    def sc_payoff(cv, t):
        a, b = ws(45) - 0.1, CARD0 - 0.05
        v = vis(t, a, b, 0.2)
        if not v:
            return
        al, yo = v
        fo = 1 - ease_out_cubic(prog(t, ws(47) - 0.08, 0.2))
        pop(cv, mega, 540, 1010, t, ws(45), al * fo, yo, dur=0.45, over=2.0)
        k = prog(t, ws(46) + 0.02, 0.4)
        if k > 0:
            put(cv, cross(200, RED, 30), 560, 1010 + yo, al * fo * ease_out_cubic(k * 2), 0.6 + 0.4 * clamp(ease_out_back(k, 2.2), 0, 1.3))
        pop(cv, bub_p1, 430, 1000, t, ws(47) - 0.05, al, yo, dur=0.45, over=2.2)
        pop(cv, bub_p2, 650, 1030, t, ws(47) + 0.12, al, yo, dur=0.45, over=2.2)
        for kk in range(3):
            put(cv, disc(16, WHITE), 430 - 36 + kk * 36, 990 + 7 * math.sin(t * 11 - kk) + yo, al * ease_out_cubic(prog(t, ws(47) + 0.2, 0.2)))
            put(cv, disc(16, NAVY), 650 - 36 + kk * 36, 1020 + 7 * math.sin(t * 11 - kk + 2) + yo, al * ease_out_cubic(prog(t, ws(47) + 0.3, 0.2)))

    friend = marker(1, 220)

    def sc_cta(cv, t):
        a = ws(50) + 0.05
        v = vis(t, a, END0, 0.25)
        if not v:
            return
        al, yo = v
        pop(cv, friend, 540, 1330, t, a, al, yo, dur=0.5, over=2.0)
        k = prog(t, a + 0.55, 0.4)
        if k > 0:
            put(cv, check(100, GREEN, 18), 680, 1250 + yo, al * ease_out_cubic(k * 2), 0.5 + 0.5 * clamp(ease_out_back(k, 2.4), 0, 1.4))
            put(cv, disc(250, None, AMBER, 8), 540, 1330 + yo, al * (1 - prog(t, a + 0.55, 0.5)), 0.9 + 0.5 * ease_out_cubic(prog(t, a + 0.55, 0.5)))
        d = ease_out_cubic(prog(t, a + 0.25, 0.25)) * (1 - ease_out_cubic(prog(t, a + 0.62, 0.2)))
        if d > 0:
            put(cv, arrow(70, 20, TH.acc), 540, 1178 + yo + 6 * math.sin(t * 9), al * d, 1.0, -90)

    scenes = [sc_hook_a, sc_hook_b] + TEXTS + CHIPS + [sc_advice, sc_map, sc_warn_fly, sc_reticle, sc_chat, sc_gift,
                                                       sc_review, sc_dialog, sc_hopper, sc_post, sc_payoff, sc_cta]
    return Reel(tim, scenes, theme="cream", bg="top", overlay_kind="dots",
                disclaimer="Bu amaliy maslahat, natija kafolati emas.")
