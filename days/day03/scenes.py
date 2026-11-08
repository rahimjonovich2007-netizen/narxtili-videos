"""Day 3 - Inflyatsiya.  Look: cream theme, diagonal gradient, grid overlay.  Visual metaphor: food basket + coin pile + balloon + race chart.
Animated explainer (objects move and transform with the words) - NOT text-only."""
import math
from functools import lru_cache

from nt_kit import *


def bounce(p):
    p = clamp(p)
    if p < 1 / 2.75: return 7.5625 * p * p
    if p < 2 / 2.75: p -= 1.5 / 2.75; return 7.5625 * p * p + .75
    if p < 2.5 / 2.75: p -= 2.25 / 2.75; return 7.5625 * p * p + .9375
    p -= 2.625 / 2.75; return 7.5625 * p * p + .984375


@lru_cache(None)
def produce(kind, d):
    s = 4
    im = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    D = d * s
    if kind == "apple":
        dr.ellipse([D * .08, D * .18, D * .92, D * .96], fill=(224, 64, 56, 255))
        dr.ellipse([D * .2, D * .28, D * .36, D * .46], fill=(255, 255, 255, 70))
        dr.line([(D * .5, D * .2), (D * .55, D * .03)], fill=(110, 70, 30, 255), width=int(D * .05))
        dr.ellipse([D * .55, D * .03, D * .82, D * .2], fill=(80, 170, 90, 255))
    elif kind == "bread":
        dr.rounded_rectangle([D * .02, D * .28, D * .98, D * .88], radius=int(D * .3), fill=(226, 170, 92, 255))
        for x in (.32, .5, .68):
            dr.line([(D * (x - .05), D * .42), (D * (x + .03), D * .66)], fill=(180, 120, 50, 255), width=int(D * .045))
    elif kind == "milk":
        dr.polygon([(D * .22, D * .32), (D * .5, D * .04), (D * .78, D * .32)], fill=(90, 140, 200, 255))
        dr.rounded_rectangle([D * .22, D * .30, D * .78, D * .98], radius=int(D * .08), fill=(236, 244, 252, 255), outline=(90, 140, 200, 255), width=int(D * .04))
        dr.rectangle([D * .30, D * .55, D * .70, D * .78], fill=(90, 140, 200, 255))
    elif kind == "orange":
        dr.ellipse([D * .08, D * .1, D * .92, D * .94], fill=(255, 150, 40, 255))
        dr.ellipse([D * .2, D * .2, D * .36, D * .38], fill=(255, 255, 255, 70))
        dr.ellipse([D * .42, D * .0, D * .62, D * .16], fill=(80, 170, 90, 255))
    else:  # lemon
        dr.ellipse([D * .02, D * .22, D * .98, D * .86], fill=(250, 214, 60, 255))
        dr.ellipse([D * .16, D * .32, D * .32, D * .48], fill=(255, 255, 255, 80))
    return im.resize((d, d), Image.LANCZOS)


KINDS = ["apple", "bread", "milk", "orange", "lemon"]


@lru_cache(None)
def flat_coin(w):
    h = int(w * 0.36)
    im = Image.new("RGBA", (w * 3, h * 3), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.ellipse([0, h * 0.35 * 3, w * 3 - 1, h * 3 - 1], fill=(214, 138, 0, 255))
    dr.ellipse([0, 0, w * 3 - 1, h * 3 * 0.72], fill=(255, 176, 32, 255))
    dr.ellipse([w * 3 * .18, h * 3 * .12, w * 3 * .82, h * 3 * .60], outline=(214, 138, 0, 255), width=6)
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def plane(sz):
    s = 4
    im = Image.new("RGBA", (sz * s, sz * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    P = lambda x, y: (x * sz * s, y * sz * s)
    dr.polygon([P(0.02, 0.5), P(0.98, 0.1), P(0.40, 0.62)], fill=(222, 128, 0, 255))
    dr.polygon([P(0.40, 0.62), P(0.98, 0.1), P(0.52, 0.92)], fill=(255, 176, 32, 255))
    dr.polygon([P(0.40, 0.62), P(0.52, 0.92), P(0.50, 0.66)], fill=(170, 96, 0, 255))
    return im.resize((sz, sz), Image.LANCZOS)


def label_chip(text, bg):
    t = txt(text, 44, WHITE, "xb", maxw=620)
    w, h = t.width + 64, t.height + 18
    base = rrect(w, h, h // 2, bg).copy()
    base.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2))
    return base


def basket_with_items(cv, cx, cy, sc, t, drops, alpha=1.0, n=5):
    """items first (so they sit inside), then the basket on top. drops = list of start times per item (None = already in)."""
    bk = basket(520, 320)
    bh = bk.height
    top = cy - bh * sc / 2
    xs = [-170, -85, 0, 85, 170]
    for i in range(n):
        d = int(118 * sc)
        fy = top + (bh - 320) * sc + 4 * sc
        x = cx + xs[i] * sc
        if drops[i] is None:
            y = fy
            a = alpha
        else:
            p = (t - drops[i]) / 0.45
            if p <= 0:
                continue
            y = fy - (1 - bounce(p)) * 330 * sc
            a = alpha * clamp(p * 6)
        put(cv, produce(KINDS[i % 5], d), x, y, a)
    put(cv, bk, cx, cy, alpha, sc)


def build(tim):
    S, E, ws, we = tim.S, tim.E, tim.ws, tim.we
    END0 = tim.end0
    # windows: (a, b)
    W0 = (0.0, S(1) - 0.10)
    W12 = (W0[1] - 0.08, S(3) - 0.10)
    W3 = (W12[1] - 0.08, S(4) - 0.10)
    W45 = (W3[1] - 0.08, S(6) - 0.10)
    W6 = (W45[1] - 0.08, S(7) - 0.10)
    W7 = (W6[1] - 0.08, S(8) - 0.10)
    W8 = (W7[1] - 0.08, END0)

    def sc_hook(cv, t):
        v = vis(t, *W0)
        if not v: return
        al, yo = v
        item(cv, txt("Pul turibdi.", 116), 540, 520, t, -0.12, al, yo)
        item(cv, txt("Lekin kamayyapti.", 98, TH.acc), 540, 650, t, max(0.5, ws(2) - 0.15), al, yo)
        k = ease_in_out(prog(t, ws(2) + 0.05, 0.85))
        d0 = 440
        ring_a = al * 0.55 * ease_out_cubic(prog(t, ws(2), 0.3))
        put(cv, disc(d0, None, TH.mut, 6), 540, 1010 + yo, ring_a)
        p0 = prog(t, -0.1, 0.4)
        if p0 > 0:
            sc = (0.9 + 0.1 * clamp(ease_out_back(p0, 1.2), 0, 1.2)) * lerp(1.0, 0.62, k)
            put(cv, coin(d0, AMBER), 540, 1010 + yo, al * ease_out_cubic(p0), sc)
            put(cv, txt("100 000", 76, (140, 84, 0)), 540, 1010 + yo, al * ease_out_cubic(p0), sc)
        if k > 0:
            bob = 14 * math.sin(t * 7)
            put(cv, arrow(150, 26, RED), 885, 1010 + yo + bob, al * k, 1.0, -90)

    def sc_basket(cv, t):
        v = vis(t, *W12)
        if not v: return
        al, yo = v
        phase2 = t >= S(2) - 0.05
        # chip
        if not phase2:
            item(cv, label_chip("BUGUN", TH.acc), 540, 470, t, W12[0] + 0.12, al, yo)
            item(cv, txt("bitta oziq-ovqat savati", 66), 540, 585, t, ws(9) - 0.1, al, yo)
        else:
            item(cv, label_chip("KEYINGI YIL", RED), 540, 470, t, S(2) + 0.0, al, yo)
        # basket position / scale
        m = ease_in_out(prog(t, S(2) + 0.05, 0.5))
        cx, sc = lerp(540, 690, m), lerp(1.0, 0.9, m)
        cy = 1050 + yo
        enter = ease_out_cubic(prog(t, ws(10) - 0.2, 0.4))
        drops = [ws(12) - 0.05 + i * 0.13 for i in range(5)]
        if enter > 0:
            basket_with_items(cv, cx, cy + (1 - enter) * 90, sc, t, drops, al * enter)
        # coin that "pays" for the basket
        pc = prog(t, ws(5) - 0.05, 0.35)
        if pc > 0 and t < ws(12) + 0.2:
            mv = ease_in_out(prog(t, ws(11), 0.6))
            x, y = lerp(230, 540, mv), lerp(760, 940, mv) - 120 * math.sin(mv * math.pi)
            put(cv, coin(210, AMBER), x, y + yo, al * ease_out_cubic(pc) * (1 - mv * 0.9), lerp(1, 0.45, mv))
            put(cv, txt("100 000", 50, (140, 84, 0)), x, y + yo, al * ease_out_cubic(pc) * (1 - mv * 0.9), lerp(1, 0.45, mv))
        if phase2:
            item(cv, txt("Narxlar oshsa,", 76), 540, 585, t, S(2) + 0.1, al, yo)
            item(cv, txt("ko‘proq pul ketadi", 76, TH.acc), 540, 680, t, ws(19) - 0.25, al, yo)
            up = ease_out_cubic(prog(t, S(2) + 0.2, 0.3))
            put(cv, arrow(130, 24, RED), 905, 790 + yo + 10 * math.sin(t * 6), al * up, 1.0, 90)
            # coin pile
            pp = ease_out_cubic(prog(t, S(2) + 0.2, 0.3))
            for i in range(4):
                put(cv, flat_coin(190), 235, 1200 - i * 30 + yo, al * pp)
            dp = prog(t, ws(19) - 0.1, 0.6)
            if dp > 0:
                y5 = 1200 - 4 * 30 - (1 - bounce(dp)) * 380
                put(cv, flat_coin(190), 235, y5 + yo, al * clamp(dp * 5))
                put(cv, txt("+1", 64, RED), 235, 1010 + yo, al * ease_out_cubic(prog(t, ws(19) + 0.35, 0.3)))

    def sc_example(cv, t):
        v = vis(t, *W3)
        if not v: return
        al, yo = v
        item(cv, label_chip("MISOL", TH.acc), 540, 470, t, W3[0] + 0.12, al, yo)
        item(cv, fit((("narxlar yiliga ", TH.fg), ("10%", RED), (" oshsa", TH.fg)), 64, "xb", 900), 540, 575, t, ws(23) - 0.1, al, yo)
        # left basket (today)
        pl = ease_out_cubic(prog(t, S(3) + 0.35, 0.4))
        if pl > 0:
            basket_with_items(cv, 290, 1010 + yo + (1 - pl) * 60, 0.62, t, [None] * 5, al * pl)
            put(cv, pricetag(380, 140, TH.card, TH.mut, "100 000", NAVY, 66), 290, 1250 + yo, al * pl)
            put(cv, txt("bugun", 44, TH.mut, "sb"), 290, 1360 + yo, al * pl)
        pr = ease_out_cubic(prog(t, ws(24) - 0.05, 0.4))
        if pr > 0:
            put(cv, arrow(170, 24, TH.acc), 540, 1010 + yo, al * pr)
            basket_with_items(cv, 790, 1010 + yo + (1 - pr) * 60, 0.62, t, [None] * 5, al * pr)
            c = ease_in_out(prog(t, ws(27) + 0.1, 1.15))
            val = lerp(100000, 110000, c)
            put(cv, pricetag(380, 140, TH.card, TH.mut, fmt(round(val, -2)), RED if c > 0.02 else NAVY, 66), 790, 1250 + yo, al * pr)
            put(cv, txt("keyingi yil", 44, TH.mut, "sb"), 790, 1360 + yo, al * pr)
            b = prog(t, ws(25), 0.4)
            if b > 0:
                put(cv, disc(170, RED), 905, 790 + yo, al * ease_out_cubic(b), 0.85 + 0.15 * clamp(ease_out_back(b, 1.4), 0, 1.3))
                put(cv, txt("+10%", 56, WHITE), 905, 790 + yo, al * ease_out_cubic(b))

    def sc_power(cv, t):
        v = vis(t, *W45)
        if not v: return
        al, yo = v
        item(cv, txt("Sening 100 000 so‘ming", 62, TH.fg, "xb", 900), 540, 500, t, S(4) + 0.0, al, yo)
        p0 = prog(t, S(4) + 0.05, 0.4)
        shrink = ease_in_out(prog(t, ws(42), 0.7))
        if p0 > 0:
            sc = (0.88 + 0.12 * clamp(ease_out_back(p0, 1.2), 0, 1.2)) * lerp(1.0, 0.82, shrink)
            put(cv, coin(320, AMBER), 540, 790 + yo, al * ease_out_cubic(p0), sc)
            put(cv, txt("100 000", 68, (140, 84, 0)), 540, 790 + yo, al * ease_out_cubic(p0), sc)
        # purchasing power row: 10 products today
        r0 = S(5) - 0.05
        item(cv, label_chip("MISOL", TH.acc), 540, 1010, t, r0, al, yo)
        gone = ease_in_out(prog(t, ws(42) + 0.05, 0.5))
        for i in range(10):
            pi = prog(t, r0 + 0.05 + i * 0.045, 0.3)
            if pi <= 0: continue
            a = al * ease_out_cubic(pi)
            if i == 9:
                a *= (1 - 0.85 * gone)
            put(cv, produce(KINDS[i % 5], 78), 135 + i * 90, 1140 + yo + (1 - ease_out_cubic(pi)) * 30, a, 0.8 + 0.2 * ease_out_cubic(pi))
        if gone > 0.02:
            put(cv, cross(70, RED, 12), 135 + 9 * 90, 1140 + yo, al * gone)
        lab = "10 ta mahsulot" if t < ws(42) + 0.1 else "≈ 9 ta mahsulot"
        col = TH.mut if t < ws(42) + 0.1 else RED
        item(cv, txt(lab, 52, col, "sb"), 540, 1265, t, r0 + 0.3 if t < ws(42) + 0.1 else ws(42) + 0.1, al, yo)
        item(cv, txt("≈ 9% kamroq", 78, RED), 540, 1370, t, ws(42) + 0.2, al, yo, dur=0.3)

    def sc_term(cv, t):
        v = vis(t, *W6, fo=0.18)
        if not v: return
        al, yo = v
        item(cv, txt("Bunga", 70, TH.fg, "sb"), 540, 470, t, W6[0] + 0.08, al, yo, base=0.85)
        g = prog(t, ws(45) - 0.35, 1.0)
        if g > 0:
            sc = (0.30 + 0.70 * ease_out_back(g, 1.1)) * (1 + 0.025 * math.sin(t * 9) * g)
            put(cv, balloon(300, AMBER), 540, 880 + yo + (1 - ease_out_cubic(g)) * 80, al * ease_out_cubic(clamp(g * 3)), sc, 3 * math.sin(t * 5))
        item(cv, txt("inflyatsiya", 148, TH.acc), 540, 1290, t, ws(45) - 0.12, al, yo, dur=0.34)
        item(cv, txt("deyiladi.", 66, TH.fg, "sb"), 540, 1415, t, ws(46) - 0.05, al, yo, base=0.85)

    def sc_chart(cv, t):
        v = vis(t, *W7)
        if not v: return
        al, yo = v
        item(cv, txt("Jamg‘armangni", 88), 540, 470, t, W7[0] + 0.1, al, yo)
        item(cv, txt("inflyatsiyadan oldinda saqlash", 60, TH.acc, "xb", 900), 540, 575, t, ws(49) - 0.45, al, yo)
        pa = prog(t, W7[0] + 0.15, 0.45)
        poly(cv, [(150, 720 + yo), (150, 1330 + yo), (950, 1330 + yo)], TH.mut, 8, ease_out_cubic(pa), al)
        u = lambda x: (x - 150) / 800
        red_y = lambda x: 1250 - 190 * u(x) - 40 * u(x) ** 2 + yo
        grn_y = lambda x: 1250 - 330 * u(x) - 190 * u(x) ** 2 + yo
        pr = ease_in_out(prog(t, ws(48) - 0.1, 1.0))
        pg = ease_in_out(prog(t, ws(49) - 0.1, 1.2))
        poly(cv, curve(red_y, 150, 950, 50), RED, 12, pr, al)
        poly(cv, curve(grn_y, 150, 950, 50), GREEN, 14, pg, al)
        item(cv, txt("narxlar", 50, RED, "xb"), 830, 1130 + yo, t, ws(48) + 0.8, al, 0)
        item(cv, txt("jamg‘arma", 50, GREEN, "xb"), 740, 705 + yo, t, ws(49) + 1.0, al, 0)

    def sc_cta(cv, t):
        v = vis(t, *W8, fo=0.25)
        if not v: return
        al, yo = v
        item(cv, txt("Inflyatsiyani hali bilmaydigan", 54, TH.fg, "sb", 900), 540, 470, t, W8[0] + 0.1, al, yo, base=0.9)
        item(cv, txt2("do‘stingga ", "yubor", 118, TH.fg, TH.acc), 540, 590, t, ws(56) - 0.5, al, yo, dur=0.34)
        for x, col, t0 in ((260, TH.acc, W8[0] + 0.25), (820, NAVY, W8[0] + 0.35)):
            item(cv, person(300, col), x, 1060, t, t0, al, yo, dur=0.35)
        P0, P1, P2 = (330, 930), (540, 560), (750, 930)
        bez = lambda s: ((1 - s) ** 2 * P0[0] + 2 * (1 - s) * s * P1[0] + s * s * P2[0], (1 - s) ** 2 * P0[1] + 2 * (1 - s) * s * P1[1] + s * s * P2[1])
        fl = ease_in_out(prog(t, ws(55), 1.0))
        if fl > 0:
            pts = [bez(fl * i / 30) for i in range(31)]
            pts = [(x, y + yo) for x, y in pts]
            poly(cv, pts, TH.mut, 6, 1.0, al * 0.8)
            x, y = bez(fl)
            x2, y2 = bez(min(1, fl + 0.02))
            ang = -math.degrees(math.atan2(y2 - y, x2 - x))
            put(cv, plane(120), x, y + yo, al, 1.0, ang - 12)
        q = prog(t, ws(56), 0.5) if fl >= 0.999 or t > ws(56) + 0.9 else 0
        if t < ws(56) + 1.0:
            put(cv, txt("?", 130, TH.mut), 820, 800 + yo, al * 0.8)
        else:
            qq = prog(t, ws(56) + 1.0, 0.35)
            put(cv, check(130, GREEN, 22), 820, 800 + yo, al * ease_out_cubic(qq), 0.7 + 0.3 * clamp(ease_out_back(qq, 1.6), 0, 1.4))

    return Reel(tim, [sc_hook, sc_basket, sc_example, sc_power, sc_term, sc_chart, sc_cta],
                theme="cream", bg="diag", overlay_kind="grid",
                disclaimer="Bu umumiy ma‘lumot, shaxsiy maslahat emas.")
