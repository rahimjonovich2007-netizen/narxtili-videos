"""Day 11 - Langar effekti.  Look: navy theme, spot background, diagonal-line overlay.
Visual metaphor: cloche reveal -> menu card with two dishes (250 000 anchor price makes 120 000 look "oqilona") ->
number line with the first number as the fixed point -> anchor drops -> tariff cards (premium next to standard,
honest checklist + stars) -> mini menu card flies to a shop (CTA).  Animated explainer, not text-only."""
import math
from functools import lru_cache

import numpy as np

from nt_kit import *


def bounce(p):
    p = clamp(p)
    if p < 1 / 2.75: return 7.5625 * p * p
    if p < 2 / 2.75: p -= 1.5 / 2.75; return 7.5625 * p * p + .75
    if p < 2.5 / 2.75: p -= 2.25 / 2.75; return 7.5625 * p * p + .9375
    p -= 2.625 / 2.75; return 7.5625 * p * p + .984375


def _cv(w, h, s=4):
    return Image.new("RGBA", (int(w * s), int(h * s)), (0, 0, 0, 0)), s


def ellipse_pts(cx, cy, rx, ry, n=56):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]


# ----------------------------------------------------------------------------- icons
@lru_cache(None)
def cloche_lid(w):
    h = int(w * 0.62)
    im, s = _cv(w, h)
    dr = ImageDraw.Draw(im)
    Wd, Hd = w * s, h * s
    dr.pieslice([0, Hd * 0.16, Wd - 1, Hd * 0.16 + Hd * 1.6], 180, 360, fill=(206, 214, 226, 255))
    dr.arc([Wd * 0.10, Hd * 0.27, Wd * 0.90, Hd * 0.27 + Hd * 1.3], 195, 252, fill=(255, 255, 255, 210), width=int(Hd * 0.05))
    dr.rounded_rectangle([Wd * 0.485, Hd * 0.10, Wd * 0.515, Hd * 0.21], radius=int(Hd * 0.01), fill=(150, 160, 178, 255))
    dr.ellipse([Wd * 0.5 - Hd * 0.075, Hd * 0.02, Wd * 0.5 + Hd * 0.075, Hd * 0.02 + Hd * 0.15], fill=(160, 170, 186, 255))
    dr.rounded_rectangle([0, Hd * 0.92, Wd - 1, Hd - 1], radius=int(Hd * 0.04), fill=(150, 160, 178, 255))
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def plate_side(w):
    h = int(w * 0.34)
    im, s = _cv(w, h)
    dr = ImageDraw.Draw(im)
    Wd, Hd = w * s, h * s
    dr.ellipse([0, Hd * 0.42, Wd - 1, Hd - 1], fill=(205, 212, 226, 255))
    dr.ellipse([Wd * 0.02, Hd * 0.40, Wd * 0.98, Hd * 0.90], fill=(250, 252, 255, 255))
    dr.ellipse([Wd * 0.12, Hd * 0.48, Wd * 0.88, Hd * 0.82], fill=(232, 237, 246, 255))
    dr.ellipse([Wd * 0.28, Hd * 0.20, Wd * 0.72, Hd * 0.70], fill=(150, 78, 48, 255))
    dr.ellipse([Wd * 0.32, Hd * 0.24, Wd * 0.68, Hd * 0.62], fill=(178, 102, 66, 255))
    for x in (0.40, 0.50, 0.60):
        dr.line([(Wd * (x - 0.04), Hd * 0.30), (Wd * (x + 0.04), Hd * 0.56)], fill=(112, 54, 32, 255), width=int(Hd * 0.04))
    dr.ellipse([Wd * 0.62, Hd * 0.14, Wd * 0.80, Hd * 0.34], fill=(80, 170, 90, 255))
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def plate_top(d, kind):
    im, s = _cv(d, d)
    dr = ImageDraw.Draw(im)
    D = d * s
    dr.ellipse([0, 0, D - 1, D - 1], fill=(216, 222, 234, 255))
    dr.ellipse([D * .06, D * .06, D * .94, D * .94], fill=(250, 252, 255, 255), outline=(205, 212, 224, 255), width=int(D * .02))
    if kind == "steak":
        dr.rounded_rectangle([D * .24, D * .30, D * .76, D * .70], radius=int(D * .2), fill=(150, 78, 48, 255))
        dr.rounded_rectangle([D * .30, D * .35, D * .70, D * .65], radius=int(D * .15), fill=(178, 102, 66, 255))
        for x in (.38, .5, .62):
            dr.line([(D * (x - .05), D * .38), (D * (x + .05), D * .62)], fill=(110, 52, 30, 255), width=int(D * .03))
        dr.ellipse([D * .58, D * .16, D * .80, D * .34], fill=(80, 170, 90, 255))
    else:  # pasta
        dr.ellipse([D * .24, D * .26, D * .76, D * .74], fill=(244, 208, 110, 255))
        for k in range(4):
            r = D * (.09 + .05 * k)
            dr.arc([D * .5 - r, D * .5 - r * .85, D * .5 + r, D * .5 + r * .85], 20 + k * 55, 300 + k * 20, fill=(212, 164, 58, 255), width=int(D * .025))
        dr.ellipse([D * .41, D * .40, D * .59, D * .56], fill=(214, 70, 56, 255))
        dr.ellipse([D * .54, D * .30, D * .64, D * .39], fill=(80, 170, 90, 255))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def anchor(h, col=AMBER):
    w = int(h * 0.9)
    im, s = _cv(w, h)
    dr = ImageDraw.Draw(im)
    Wd, Hd = w * s, h * s
    cx = Wd / 2
    c = tuple(col) + (255,)
    lw = int(Hd * 0.07)
    r = Hd * 0.07
    dr.ellipse([cx - r, Hd * 0.02, cx + r, Hd * 0.02 + 2 * r], outline=c, width=int(Hd * 0.032))
    dr.rounded_rectangle([cx - lw / 2, Hd * 0.15, cx + lw / 2, Hd * 0.90], radius=int(lw / 2), fill=c)
    sy = Hd * 0.26
    dr.rounded_rectangle([cx - Hd * 0.24, sy - lw * .4, cx + Hd * 0.24, sy + lw * .4], radius=int(lw * .4), fill=c)
    for sx in (-1, 1):
        ex = cx + sx * Hd * 0.24
        dr.ellipse([ex - lw * .72, sy - lw * .72, ex + lw * .72, sy + lw * .72], fill=c)
    R = Hd * 0.34
    ccy = Hd * 0.56
    dr.arc([cx - R, ccy - R, cx + R, ccy + R], 8, 172, fill=c, width=lw)
    for sx in (-1, 1):
        ex = cx + sx * R * math.cos(math.radians(8))
        ey = ccy + R * math.sin(math.radians(8))
        dr.polygon([(ex - sx * Hd * 0.045, ey + Hd * 0.01), (ex + sx * Hd * 0.115, ey - Hd * 0.13), (ex + sx * Hd * 0.065, ey + Hd * 0.045)], fill=c)
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def star(d, col):
    im, s = _cv(d, d)
    dr = ImageDraw.Draw(im)
    D = d * s
    pts = []
    for i in range(10):
        r = D * 0.5 * (1 if i % 2 == 0 else 0.42)
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((D / 2 + r * math.cos(a), D * 0.53 + r * math.sin(a)))
    dr.polygon(pts, fill=tuple(col) + (255,))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def shield(d, col=GREEN):
    im, s = _cv(d, d)
    dr = ImageDraw.Draw(im)
    D = d * s
    P = lambda x, y: (D * x, D * y)
    dr.polygon([P(.5, .02), P(.90, .15), P(.90, .50), P(.78, .72), P(.5, .98), P(.22, .72), P(.10, .50), P(.10, .15)], fill=tuple(col) + (255,))
    inner = tuple(mixc(col, (255, 255, 255), 0.14)) + (255,)
    dr.polygon([P(.5, .10), P(.82, .20), P(.82, .49), P(.72, .67), P(.5, .89), P(.28, .67), P(.18, .49), P(.18, .20)], fill=inner)
    dr.line([P(.32, .50), P(.46, .64), P(.70, .34)], fill=(255, 255, 255, 255), width=int(D * .075), joint="curve")
    r = D * .0375
    for q in ((.32, .50), (.70, .34)):
        x, y = P(*q)
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 255))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def crown(d, col=AMBER):
    h = int(d * 0.78)
    im, s = _cv(d, h)
    dr = ImageDraw.Draw(im)
    Wd, Hd = d * s, h * s
    P = lambda x, y: (Wd * x, Hd * y)
    dr.polygon([P(.05, .86), P(.05, .26), P(.28, .52), P(.5, .10), P(.72, .52), P(.95, .26), P(.95, .86)], fill=tuple(col) + (255,))
    dr.rectangle([Wd * .05, Hd * .74, Wd * .95, Hd * .90], fill=(214, 138, 0, 255))
    for x in (.05, .5, .95):
        px, py = P(x, .16 if x == .5 else .24)
        rr = Hd * 0.075
        dr.ellipse([px - rr, py - rr, px + rr, py + rr], fill=(255, 220, 130, 255))
    return im.resize((d, h), Image.LANCZOS)


@lru_cache(None)
def storefront(w):
    h = int(w * 0.95)
    im, s = _cv(w, h)
    dr = ImageDraw.Draw(im)
    Wd, Hd = w * s, h * s
    dr.rounded_rectangle([Wd * .08, Hd * .34, Wd * .92, Hd * .98], radius=int(Wd * .03), fill=(247, 243, 234, 255))
    dr.rounded_rectangle([Wd * .16, Hd * .54, Wd * .50, Hd * .84], radius=int(Wd * .02), fill=(120, 170, 220, 255))
    dr.rounded_rectangle([Wd * .60, Hd * .54, Wd * .84, Hd * .98], radius=int(Wd * .02), fill=(196, 132, 60, 255))
    dr.ellipse([Wd * .64, Hd * .76, Wd * .67, Hd * .79], fill=(255, 210, 120, 255))
    n = 5
    sw = Wd * .9 / n
    for i in range(n):
        x0 = Wd * .05 + i * sw
        col = (232, 80, 70, 255) if i % 2 == 0 else (255, 255, 255, 255)
        dr.polygon([(x0, Hd * .12), (x0 + sw, Hd * .12), (x0 + sw * 1.02, Hd * .38), (x0 - sw * .02, Hd * .38)], fill=col)
        dr.pieslice([x0 - sw * .02, Hd * .31, x0 + sw * 1.02, Hd * .45], 0, 180, fill=col)
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def mini_menu(w=170, h=210):
    im = rrect(w, h, 24, CREAM, (214, 138, 0), 5).copy()
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([w * .22, h * .10, w * .78, h * .18], radius=4, fill=NAVY)
    for y in (.36, .56, .76):
        d.ellipse([w * .14, h * y - 15, w * .14 + 30, h * y + 15], fill=(214, 138, 0))
        d.rounded_rectangle([w * .42, h * y - 6, w * .84, h * y + 6], radius=6, fill=(170, 164, 148))
    return im


@lru_cache(None)
def glow(d, col):
    yy, xx = np.mgrid[0:d, 0:d]
    r = np.sqrt((xx - d / 2) ** 2 + (yy - d / 2) ** 2) / (d / 2)
    a = np.clip(1 - r, 0, 1) ** 2
    arr = np.zeros((d, d, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = col
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def chip(text, bg, fg=WHITE):
    t = txt(text, 44, fg, "xb", maxw=620)
    w, h = t.width + 64, t.height + 18
    base = rrect(w, h, h // 2, bg).copy()
    base.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2))
    return base


def put_left(cv, layer, x_left, cy, alpha=1.0):
    put(cv, layer, x_left - 8 + layer.width / 2, cy, alpha)


GREYLINE = (150, 170, 200)


def build(tim):
    S, E, ws, we = tim.S, tim.E, tim.ws, tim.we
    END0 = tim.end0
    WA = (0.0, S(1) - 0.10)
    WM = (WA[1] - 0.08, S(3) - 0.10)
    WD = (WM[1] - 0.08, S(4) - 0.10)
    WE = (WD[1] - 0.08, S(5) - 0.10)
    WT = (WE[1] - 0.08, S(8) - 0.10)
    WC = (WT[1] - 0.08, END0)

    # ------------------------------------------------------------------ hook: cloche reveal
    def sc_hook(cv, t):
        v = vis(t, *WA)
        if not v: return
        al, yo = v
        item(cv, txt("Menyudagi", 112), 540, 505, t, 0.08, al, yo)
        item(cv, txt("eng qimmat taom", 100, TH.acc, "xb", 900), 540, 625, t, ws(1) - 0.08, al, yo)
        item(cv, txt("nega kerak?", 112), 540, 750, t, ws(4) - 0.08, al, yo)
        pcx, pcy, pw = 540, 1240, 640
        p = prog(t, -0.05, 0.60)
        dy = -(1 - bounce(p)) * 640
        a = al * clamp(p * 6)
        lift = ease_out_cubic(prog(t, ws(5) - 0.05, 0.55))
        gk = ease_out_cubic(prog(t, ws(5) - 0.05, 0.5))
        if gk > 0:
            put(cv, glow(760, TH.acc), pcx, pcy - 170 + yo, al * 0.55 * gk, 1.0 + 0.04 * math.sin(t * 6))
        pl = plate_side(pw)
        put(cv, pl, pcx, pcy + dy + yo, a)
        lid = cloche_lid(560)
        closed_cy = pcy - pl.height / 2 + pl.height * 0.66 - lid.height / 2
        shake = 0.0
        if ws(3) < t < ws(5) - 0.05:
            shake = 3.2 * math.sin((t - ws(3)) * 34) * clamp((t - ws(3)) / 0.5)
        put(cv, lid, pcx + 60 * lift, closed_cy + dy - 400 * lift + yo, a * (1 - lift), 1.0, 18 * lift + shake)
        q = prog(t, ws(5) + 0.0, 0.5)
        if q > 0:
            sc = 0.3 + 0.7 * ease_out_back(q, 1.8)
            put(cv, txt("?", 320, TH.acc), pcx, pcy - 245 + yo + 10 * math.sin(t * 6), al * ease_out_cubic(q), sc)

    # ------------------------------------------------------------------ menu card: 250 000 vs 120 000
    def sc_menu(cv, t):
        v = vis(t, *WM)
        if not v: return
        al, yo = v
        item(cv, chip("MISOL", TH.acc, NAVY), 540, 440, t, WM[0] + 0.10, al, yo)
        ph2 = t >= S(2) - 0.05
        ph3 = t >= ws(16) - 0.12
        if not ph2:
            item(cv, txt("Menyuda", 88), 540, 560, t, WM[0] + 0.05, al, yo)
            item(cv, txt("250 000 so‘mlik taom", 84, TH.acc, "xb", 900), 540, 665, t, ws(7) - 0.12, al, yo)
        elif not ph3:
            item(cv, txt("Uning yonidagi", 88), 540, 560, t, S(2) + 0.0, al, yo)
            item(cv, txt("120 000 so‘mlik taom", 84, TH.acc, "xb", 900), 540, 665, t, ws(13) - 0.12, al, yo)
        else:
            item(cv, txt2("endi ", "oqilona", 100, TH.fg, GREEN), 540, 560, t, ws(16) - 0.12, al, yo)
            item(cv, txt("ko‘rinadi.", 88), 540, 665, t, ws(18) - 0.08, al, yo)
        cpop = ease_out_cubic(prog(t, WM[0] + 0.15, 0.45))
        ccy = 1070 + (1 - cpop) * 80
        put(cv, rrect(860, 620, 46, (0, 0, 0)), 548, ccy + 16 + yo, al * cpop * 0.30)
        put(cv, rrect(860, 620, 46, CREAM), 540, ccy + yo, al * cpop)
        put(cv, txt("MENYU", 56, NAVY, "xb"), 540, ccy - 245 + yo, al * cpop)
        put(cv, rrect(200, 7, 3, (214, 138, 0)), 540, ccy - 196 + yo, al * cpop)
        put(cv, rrect(760, 4, 2, (222, 216, 200)), 540, ccy + 45 + yo, al * cpop * 0.9)
        g = ease_in_out(prog(t, ws(17) - 0.08, 0.45))      # "oqilona" -> green
        dim = ease_in_out(prog(t, ws(16) - 0.05, 0.4))
        a1 = al * cpop * (1 - 0.55 * dim)

        def draw_row(name, kind, ry, t_in, c0, cdur, target, a, fill, tcol):
            pr = ease_out_cubic(prog(t, t_in, 0.4))
            if pr <= 0: return
            put(cv, plate_top(160, kind), 215, ry + yo + (1 - pr) * 40, a * pr, 0.85 + 0.15 * clamp(ease_out_back(pr, 1.3), 0, 1.3))
            nm = txt(name, 64, NAVY, "xb", 300)
            put_left(cv, nm, 320, ry + yo, a * pr)
            tagp = ease_out_cubic(prog(t, c0 - 0.1, 0.3))
            if tagp > 0:
                val = target * ease_out_cubic(prog(t, c0, cdur))
                put(cv, pricetag(340, 130, fill, CREAM, fmt(round(val, -3)), tcol, 60), 765, ry + yo, a * tagp, 0.9 + 0.1 * tagp)

        r1, r2 = ccy - 70, ccy + 160
        draw_row("Steyk", "steak", r1, ws(6) - 0.05, ws(7) - 0.05, 1.1, 250000, a1, AMBER, NAVY)
        if g > 0:
            put(cv, rrect(820, 200, 34, (222, 246, 232), GREEN, 6), 540, r2 + yo, al * cpop * g)
        fill2 = mixc(AMBER, GREEN, g)
        tcol2 = mixc(NAVY, WHITE, g)
        draw_row("Pasta", "pasta", r2, ws(11) - 0.05, ws(13) - 0.05, 0.75, 120000, al * cpop, fill2, tcol2)
        ar = ease_out_cubic(prog(t, ws(15) - 0.15, 0.3))
        if ar > 0:
            put(cv, arrow(100, 18, (214, 138, 0)), 765, ccy + 45 + yo, al * ar * (1 - 0.5 * dim), 1.0, -90)
        gb = prog(t, ws(17) - 0.05, 0.4)
        if gb > 0:
            sc = 0.6 + 0.4 * clamp(ease_out_back(gb, 1.7), 0, 1.4)
            put(cv, disc(104, GREEN), 935, r2 - 62 + yo, al * ease_out_cubic(gb), sc)
            put(cv, check(70, WHITE, 14), 935, r2 - 62 + yo, al * ease_out_cubic(gb), sc)

    # ------------------------------------------------------------------ number line: first number = fixed point
    def sc_ruler(cv, t):
        v = vis(t, *WD)
        if not v: return
        al, yo = v
        item(cv, chip("MISOL", TH.acc, NAVY), 540, 440, t, WD[0] + 0.10, al, yo)
        item(cv, txt("Birinchi ko‘rgan raqam", 72), 540, 545, t, WD[0] + 0.05, al, yo)
        item(cv, txt("keyingisini baholash", 72, TH.acc), 540, 640, t, ws(22) - 0.12, al, yo)
        item(cv, txt("uchun nuqta bo‘lib qoladi.", 68), 540, 735, t, ws(24) - 0.10, al, yo)
        LY, XA, XB, TY = 1110, 790, 290, 985
        pl = ease_in_out(prog(t, WD[0] + 0.12, 0.5))
        poly(cv, [(110, LY + yo), (970, LY + yo)], GREYLINE, 8, pl, al)
        for i in range(11):
            poly(cv, [(110 + 86 * i, LY - 18 + yo), (110 + 86 * i, LY + 18 + yo)], GREYLINE, 4, 1.0, al * pl * 0.7)
        item(cv, txt("arzon", 44, (160, 180, 208), "sb"), 175, LY + 85, t, WD[0] + 0.3, al, yo, base=0.9)
        item(cv, txt("qimmat", 44, (160, 180, 208), "sb"), 905, LY + 85, t, WD[0] + 0.3, al, yo, base=0.9)
        # tag A: first number lands and becomes the fixed point
        t0a = ws(19) + 0.02
        pa = prog(t, t0a, 0.62)
        if pa > 0:
            ya = TY - (1 - bounce(pa)) * 190
            ga = al * clamp(pa * 6)
            poly(cv, [(XA, TY + 70 + yo), (XA, LY + yo)], GREYLINE, 5, ease_out_cubic(prog(t, t0a + 0.25, 0.3)), al)
            put(cv, pricetag(360, 140, AMBER, NAVY, "250 000", NAVY, 62), XA, ya + yo, ga)
            put(cv, disc(72, CREAM), XA - 172, ya - 62 + yo, ga)
            put(cv, txt("1", 46, NAVY), XA - 172, ya - 62 + yo, ga)
            dp = ease_out_cubic(prog(t, t0a + 0.25, 0.3))
            big = ease_out_back(prog(t, ws(25) - 0.05, 0.4), 1.8) if t > ws(25) - 0.05 else 0
            put(cv, disc(40, AMBER), XA, LY + yo, al * dp, 1.0 + 0.9 * big)
            for k in range(3):
                pk = prog(t, ws(25) - 0.05 + k * 0.24, 0.9)
                if 0 < pk < 1:
                    put(cv, disc(400, None, AMBER, 6), XA, LY + yo, al * (1 - pk) * 0.75, (30 + 140 * ease_out_cubic(pk)) / 200)
        # tag B: next number measured against it
        pb = ease_out_cubic(prog(t, ws(22) - 0.1, 0.5))
        if pb > 0:
            xb = lerp(40, XB, pb)
            put(cv, pricetag(360, 140, CREAM, NAVY, "120 000", NAVY, 62), xb, TY + yo, al * pb)
            put(cv, disc(72, AMBER), xb - 172, TY - 62 + yo, al * pb)
            put(cv, txt("2", 46, NAVY), xb - 172, TY - 62 + yo, al * pb)
            poly(cv, [(XB, TY + 70 + yo), (XB, LY + yo)], GREYLINE, 5, ease_out_cubic(prog(t, ws(22) + 0.2, 0.3)), al)
            put(cv, disc(40, CREAM), XB, LY + yo, al * ease_out_cubic(prog(t, ws(22) + 0.2, 0.3)))
        dl = prog(t, ws(23) - 0.1, 0.85)
        if dl > 0:
            dashed_line(cv, (XA - 24, LY + yo), (XB + 24, LY + yo), AMBER, 8, 26, 16, p=ease_in_out(dl), alpha=al)
            qq = ease_out_cubic(prog(t, ws(23) + 0.25, 0.3))
            put(cv, txt("?", 96, TH.acc), 540, TY + 6 + yo + 8 * math.sin(t * 6), al * qq, 0.6 + 0.4 * qq)

    # ------------------------------------------------------------------ the anchor
    def sc_anchor(cv, t):
        v = vis(t, *WE)
        if not v: return
        al, yo = v
        item(cv, chip("ATAMA", TH.acc, NAVY), 540, 450, t, WE[0] + 0.10, al, yo)
        ACX, ACY = 540, 800
        t0 = ws(28) - 0.55
        p = prog(t, t0, 0.62)
        land = t0 + 0.62 * (1 / 2.75)
        yy = ACY - (1 - bounce(p)) * 1250
        rot = 0.0
        if t > land:
            rot = 7 * math.exp(-(t - land) * 2.0) * math.sin((t - land) * 10)
        if p > 0:
            put(cv, anchor(480), ACX, yy + yo, al * clamp(p * 8), 1.0, rot)
        GY = 1065
        for k in range(3):
            pk = prog(t, land + k * 0.20, 0.95)
            if 0 < pk < 1:
                rx = 90 + 230 * ease_out_cubic(pk)
                poly(cv, ellipse_pts(ACX, GY + yo, rx, rx * 0.18), TH.fg, 5, 1.0, al * (1 - pk) * 0.65)
        item(cv, txt("Bunga", 70), 540, 1185, t, ws(28) - 0.05, al, yo)
        item(cv, txt("langar effekti", 118, TH.acc, "xb", 900), 540, 1285, t, ws(29) - 0.12, al, yo, dur=0.34)
        item(cv, txt("deyiladi.", 66), 540, 1380, t, ws(31) - 0.05, al, yo)

    # ------------------------------------------------------------------ tariffs: premium next to standard, honest
    def card_std(cv, cx, cy, k, a):
        w, h = int(380 * k), int(430 * k)
        put(cv, rrect(w, h, int(40 * k), (0, 0, 0)), cx + 8, cy + 14, a * 0.28)
        put(cv, rrect(w, h, int(40 * k), CREAM), cx, cy, a)
        put(cv, txt("Standart", max(20, int(50 * k)), NAVY), cx, cy - 140 * k, a)
        put(cv, rrect(int(260 * k), int(7 * k) + 1, 3, (190, 196, 208)), cx, cy - 95 * k, a)
        for yy, ww in ((-40, 260), (20, 200), (80, 260)):
            put(cv, rrect(int(ww * k), int(18 * k), int(9 * k), (214, 219, 229)), cx, cy + yy * k, a)
        put(cv, rrect(int(230 * k), int(58 * k), int(29 * k), (205, 212, 224)), cx, cy + 160 * k, a)

    def card_prem(cv, cx, cy, k, a, gl, t):
        w, h = int(400 * k), int(500 * k)
        put(cv, glow(int(780 * k), TH.acc), cx, cy, a * 0.40 * gl)
        put(cv, rrect(w, h, int(42 * k), (0, 0, 0)), cx + 8, cy + 14, a * 0.30)
        put(cv, rrect(w, h, int(42 * k), CREAM, (255, 176, 32), max(2, int(9 * k))), cx, cy, a)
        put(cv, crown(int(92 * k)), cx, cy - 195 * k, a)
        put(cv, txt("Premium", max(20, int(54 * k)), NAVY), cx, cy - 125 * k, a)
        put(cv, rrect(int(300 * k), int(7 * k) + 1, 3, (255, 176, 32)), cx, cy - 78 * k, a)
        g = ease_in_out(prog(t, S(7) - 0.05, 0.35))
        if g < 1:
            for yy, ww in ((-30, 280), (30, 220), (90, 280)):
                put(cv, rrect(int(ww * k), int(18 * k), int(9 * k), (214, 219, 229)), cx, cy + yy * k, a * (1 - g))
        if g > 0:
            put_left(cv, txt("Mavjud", max(20, int(46 * k)), NAVY, "xb", 300), cx - 160 * k, cy - 28 * k, a * g)
            put_left(cv, txt("Sifatli", max(20, int(46 * k)), NAVY, "xb", 300), cx - 160 * k, cy + 42 * k, a * g)
            put(cv, disc(max(8, int(60 * k)), None, (190, 196, 208), max(2, int(6 * k))), cx + 140 * k, cy - 28 * k, a * g)
            c1 = prog(t, ws(45) - 0.05, 0.35)
            if c1 > 0:
                sc = 0.5 + 0.5 * clamp(ease_out_back(c1, 1.8), 0, 1.4)
                put(cv, disc(max(8, int(64 * k)), GREEN), cx + 140 * k, cy - 28 * k, a * ease_out_cubic(c1), sc)
                put(cv, check(max(8, int(46 * k)), WHITE, max(2, int(10 * k))), cx + 140 * k, cy + 0 - 28 * k, a * ease_out_cubic(c1), sc)
            for i in range(5):
                sx = cx + (i - 2) * 70 * k
                put(cv, star(max(8, int(56 * k)), (205, 210, 222)), sx, cy + 125 * k, a * g)
                si = prog(t, ws(47) - 0.02 + i * 0.15, 0.3)
                if si > 0:
                    put(cv, star(max(8, int(56 * k)), AMBER), sx, cy + 125 * k, a * ease_out_cubic(si), 0.6 + 0.4 * clamp(ease_out_back(si, 2.0), 0, 1.5))
        put(cv, rrect(int(250 * k), int(58 * k), int(29 * k), (255, 176, 32)), cx, cy + 205 * k, a)

    def sc_tariff(cv, t):
        v = vis(t, *WT)
        if not v: return
        al, yo = v
        gA = vis(t, WT[0], S(6) - 0.06, 0.10)
        if gA:
            a2, y2 = gA
            aa, yy = al * a2, yo + y2
            item(cv, txt("Do‘koningda ham", 82), 540, 530, t, WT[0] + 0.08, aa, yy)
            item(cv, txt("eng qimmat tarifni", 82, TH.acc, "xb", 900), 540, 630, t, ws(34) - 0.15, aa, yy)
            item(cv, txt("yoniga qo‘y.", 82), 540, 730, t, ws(37) - 0.12, aa, yy)
        gB = vis(t, S(6) - 0.08, S(7) - 0.10, 0.10)
        if gB:
            a2, y2 = gB
            aa, yy = al * a2, yo + y2
            item(cv, txt("Faqat", 84), 540, 540, t, S(6) - 0.05, aa, yy)
            item(cv, txt("halol bo‘l.", 124, GREEN, "xb", 900), 540, 665, t, ws(40) - 0.12, aa, yy, dur=0.34)
        gC = vis(t, S(7) - 0.12, WT[1], 0.14)
        if gC:
            a2, y2 = gC
            aa, yy = al * a2, yo + y2
            item(cv, txt("Qimmat variant", 84), 540, 530, t, S(7) - 0.08, aa, yy)
            item(cv, txt2("haqiqatan ", "mavjud", 84, TH.fg, GREEN), 540, 630, t, ws(44) - 0.10, aa, yy)
            item(cv, fit((("va ", TH.fg), ("sifatli", TH.acc), (" bo‘lsin.", TH.fg)), 84, "xb", 900), 540, 730, t, ws(46) - 0.10, aa, yy)
        # standard card: enters centre, shifts left to make room, leaves when only the premium matters
        enter = ease_out_cubic(prog(t, ws(32) - 0.05, 0.45))
        mv = ease_in_out(prog(t, ws(34) - 0.05, 0.7))
        out = ease_in_out(prog(t, S(7) - 0.02, 0.45))
        sa = al * enter * (1 - out)
        if sa > 0.01:
            card_std(cv, lerp(540, 310, mv) - 280 * out, 1060 + yo + (1 - enter) * 60, 1.0, sa)
        # premium card
        pe = prog(t, ws(34) - 0.12, 0.95)
        if pe > 0:
            gcen = ease_in_out(prog(t, S(7) + 0.02, 0.6))
            px = lerp(lerp(1260, 770, ease_out_cubic(pe)), 540, gcen)
            py = lerp(1040, 1135, gcen)
            card_prem(cv, px, py + yo, lerp(1.0, 1.2, gcen), al * clamp(pe * 6), ease_out_cubic(prog(t, ws(37), 0.5)), t)
        # halol seal
        sp = prog(t, S(6) + 0.0, 0.45)
        sf = 1 - prog(t, S(7) - 0.05, 0.25)
        if sp > 0 and sf > 0:
            sc = 0.5 + 0.5 * clamp(ease_out_back(sp, 1.8), 0, 1.4)
            put(cv, shield(180), 540, 1385 + yo, al * ease_out_cubic(sp) * sf, sc)
            for k in range(2):
                pk = prog(t, S(6) + 0.15 + k * 0.22, 0.7)
                if 0 < pk < 1:
                    put(cv, disc(400, None, GREEN, 6), 540, 1385 + yo, al * (1 - pk) * 0.6 * sf, (60 + 90 * ease_out_cubic(pk)) / 200)

    # ------------------------------------------------------------------ CTA: send to a friend with a business
    def sc_cta(cv, t):
        v = vis(t, *WC, fo=0.25)
        if not v: return
        al, yo = v
        item(cv, txt("Biznesi bor", 96), 540, 530, t, WC[0] + 0.08, al, yo)
        item(cv, txt2("do‘stingga ", "yubor", 108, TH.fg, TH.acc), 540, 650, t, ws(51) - 0.15, al, yo, dur=0.34)
        item(cv, person(280, CREAM), 250, 1190, t, WC[0] + 0.15, al, yo, dur=0.35)
        arrive = ws(52) - 0.05
        sp = ease_out_cubic(prog(t, WC[0] + 0.25, 0.4))
        pulse = 1.0 + 0.10 * math.sin(clamp((t - arrive) / 0.35) * math.pi) if t > arrive else 1.0
        if sp > 0:
            put(cv, storefront(300), 830, 1190 + yo + (1 - sp) * 50, al * sp, pulse)
        P0, P1, P2 = (430, 1030), (580, 690), (735, 1080)
        bez = lambda s: ((1 - s) ** 2 * P0[0] + 2 * (1 - s) * s * P1[0] + s * s * P2[0], (1 - s) ** 2 * P0[1] + 2 * (1 - s) * s * P1[1] + s * s * P2[1])
        fl = ease_in_out(prog(t, ws(49) + 0.05, 1.0))
        if fl > 0:
            pts = [bez(fl * i / 30) for i in range(31)]
            poly(cv, [(x, y + yo) for x, y in pts], TH.mut if False else (110, 134, 168), 6, 1.0, al * 0.8)
            x, y = bez(fl)
            fade = 1.0 if fl < 0.98 else clamp(1 - (t - arrive) / 0.15)
            put(cv, mini_menu(), x, y + yo, al * fade, lerp(1.0, 0.6, fl), lerp(18, -22, fl))
        cb = prog(t, arrive, 0.45)
        if cb > 0:
            sc = 0.5 + 0.5 * clamp(ease_out_back(cb, 1.8), 0, 1.4)
            put(cv, disc(112, GREEN), 935, 1030 + yo, al * ease_out_cubic(cb), sc)
            put(cv, check(76, WHITE, 15), 935, 1030 + yo, al * ease_out_cubic(cb), sc)
            for k in range(2):
                pk = prog(t, arrive + k * 0.2, 0.7)
                if 0 < pk < 1:
                    put(cv, disc(400, None, GREEN, 6), 830, 1190 + yo, al * (1 - pk) * 0.5, (90 + 80 * ease_out_cubic(pk)) / 200)

    return Reel(tim, [sc_hook, sc_menu, sc_ruler, sc_anchor, sc_tariff, sc_cta],
                theme="navy", bg="spot", overlay_kind="diag")
