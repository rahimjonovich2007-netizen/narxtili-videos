"""Day 7 - Talab va taklif.  Look: amber theme, top gradient, diag overlay.
Visual metaphor: gul bozori tarozisi (talab = xaridorlar, taklif = gullar), narx yorlig'i ko'tariladi va tushadi,
uch kartada (kvartira / dollar / pomidor) xuddi shu qoida, oxirida talab va taklif chiziqlari kesishadi.
Animated explainer (objects move and transform with the words) - NOT text-only."""
import math
from functools import lru_cache

from nt_kit import *

DRED = (168, 28, 32)            # dark red: readable on amber
DGRN = (8, 104, 62)             # dark green
SLATE2 = (52, 86, 140)
PINK = (226, 70, 130)
TRED = (200, 40, 52)
WARM = (255, 244, 205)


# ----------------------------------------------------------------------------- easing / helpers
def bounce(p):
    p = clamp(p)
    if p < 1 / 2.75: return 7.5625 * p * p
    if p < 2 / 2.75: p -= 1.5 / 2.75; return 7.5625 * p * p + .75
    if p < 2.5 / 2.75: p -= 2.25 / 2.75; return 7.5625 * p * p + .9375
    p -= 2.625 / 2.75; return 7.5625 * p * p + .984375


def pop(cv, layer, cx, cy, t, t0, al=1.0, yo=0.0, dur=0.35, rot=0.0, base=1.0, rise=30, s0=0.85, scale=1.0):
    p = (t - t0) / dur
    if p <= 0:
        return
    e = ease_out_cubic(p)
    sc = (s0 + (1 - s0) * clamp(ease_out_back(p, 1.3), 0, 1.25)) * scale
    put(cv, layer, cx, cy + yo + (1 - e) * rise, al * e * base, sc, rot)


def chip(text, bg, fg=NAVY, size=40, maxw=700):
    t = txt(text, size, fg, "xb", maxw=maxw)
    w, h = t.width + 56, t.height + 14
    base = rrect(w, h, h // 2, tuple(bg)).copy()
    base.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2))
    return base


def words_line(cv, words, size, y, times, t, al, yo, col=None, gap=24, dur=0.3):
    """one line made of words that each appear at their own time (exactly the spoken words)"""
    while True:
        layers = [txt(w, size, col) for w in words]
        widths = [l.width - 16 for l in layers]
        total = sum(widths) + gap * (len(words) - 1)
        if total <= 880 or size <= 40:
            break
        size -= 4
    x = 540 - total / 2
    for l, w, t0 in zip(layers, widths, times):
        item(cv, l, x + w / 2, y, t, t0, al, yo, dur=dur)
        x += w + gap


def sub(t, a, b, al, yo, fo=0.12):
    """sub-window inside a scene: returns (alpha, y offset) combined with the scene's, or None"""
    v = vis(t, a, b, fo)
    if not v:
        return None
    return al * v[0], yo + v[1]


# ----------------------------------------------------------------------------- local icons (drawn with PIL)
@lru_cache(None)
def tulip(h, col=TRED):
    w = int(h * 0.62)
    s = 4
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    P = lambda x, y: (x * w * s, y * h * s)
    g, g2 = (8, 104, 62), (22, 146, 88)
    dr.line([P(.5, .46), P(.5, 1.0)], fill=g + (255,), width=max(2, int(w * .08 * s)))
    dr.polygon([P(.5, .98), P(.08, .68), P(.19, .60), P(.50, .80)], fill=g2 + (255,))
    dr.polygon([P(.5, .98), P(.92, .72), P(.81, .64), P(.50, .84)], fill=g + (255,))
    light = tuple(min(255, c + 50) for c in col)
    dark = tuple(max(0, c - 45) for c in col)
    dr.polygon([P(.06, .16), P(.30, .30), P(.5, .04), P(.70, .30), P(.94, .16), P(.94, .34), P(.78, .50), P(.5, .56), P(.22, .50), P(.06, .34)], fill=tuple(col) + (255,))
    dr.polygon([P(.30, .30), P(.5, .04), P(.70, .30), P(.64, .52), P(.5, .56), P(.36, .52)], fill=light + (255,))
    dr.polygon([P(.06, .16), P(.30, .30), P(.36, .52), P(.22, .50), P(.06, .34)], fill=dark + (255,))
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def bouquet(h):
    """bucket full of tulips (a flower stall), width ~ h"""
    w = int(h * 1.0)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    specs = [(-0.28, 0.50, -16, TRED), (0.28, 0.50, 16, PINK), (-0.10, 0.58, -6, WHITE), (0.12, 0.60, 7, TRED), (0.0, 0.44, 0, PINK)]
    for fx, fy, rot, col in specs:
        t = tulip(int(h * 0.64), col).rotate(rot, resample=Image.BICUBIC, expand=True)
        im.alpha_composite(t, (int(w * (0.5 + fx) - t.width / 2), int(h * fy - t.height / 2)))
    bw, bh = int(w * .58), int(h * .30)
    b = Image.new("RGBA", (bw * 3, bh * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    d.polygon([(0, 0), (bw * 3, 0), (bw * 3 * .86, bh * 3), (bw * 3 * .14, bh * 3)], fill=NAVY + (255,))
    d.rectangle([0, 0, bw * 3, int(bh * 3 * .17)], fill=SLATE2 + (255,))
    b = b.resize((bw, bh), Image.LANCZOS)
    im.alpha_composite(b, (int((w - bw) / 2), h - bh))
    return im


@lru_cache(None)
def calendar(w=300, h=340):
    s = 3
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=34 * s, fill=WHITE + (255,))
    d.rounded_rectangle([0, 0, w * s - 1, int(h * .30 * s)], radius=34 * s, fill=DRED + (255,))
    d.rectangle([0, int(h * .18 * s), w * s - 1, int(h * .30 * s)], fill=DRED + (255,))
    for x in (.28, .72):
        d.rounded_rectangle([x * w * s - 10 * s, -8 * s, x * w * s + 10 * s, 34 * s], radius=10 * s, fill=NAVY + (255,))
    im = im.resize((w, h), Image.LANCZOS)
    t = txt("MART", 50, WHITE, "xb")
    im.alpha_composite(t, ((w - t.width) // 2, int(h * .165) - t.height // 2 + 6))
    n = txt("8", 170, NAVY, "xb")
    im.alpha_composite(n, ((w - n.width) // 2, int(h * .30) + (int(h * .70) - n.height) // 2 + 6))
    return im


@lru_cache(None)
def building(h):
    w = int(h * 0.64)
    s = 3
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, int(h * .03 * s), w * s - 1, h * s - 1], radius=int(w * .07 * s), fill=NAVY + (255,))
    for r in range(5):
        for c in range(3):
            x0, y0 = w * (.14 + .28 * c), h * (.11 + .155 * r)
            d.rounded_rectangle([x0 * s, y0 * s, (x0 + w * .18) * s, (y0 + h * .09) * s], radius=int(w * .02 * s), fill=(255, 205, 100, 255) if (r + c) % 3 else WARM + (255,))
    d.rounded_rectangle([w * .38 * s, h * .87 * s, w * .62 * s, h * s], radius=int(w * .03 * s), fill=WHITE + (255,))
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def tomato(d):
    s = 4
    im = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    D = d * s
    dr.ellipse([D * .04, D * .16, D * .96, D * .96], fill=(214, 46, 40, 255))
    dr.ellipse([D * .16, D * .28, D * .36, D * .46], fill=(255, 255, 255, 80))
    c = (D * .5, D * .22)
    pts = []
    for i in range(10):
        a = i * math.pi / 5
        r = D * (.22 if i % 2 == 0 else .09)
        pts.append((c[0] + r * math.sin(a), c[1] - r * math.cos(a) * .7))
    dr.polygon(pts, fill=(22, 146, 88, 255))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def melon(d):
    """watermelon slice (half disc), width d, height ~ d/2"""
    s = 4
    hh = int(d * .52)
    im = Image.new("RGBA", (d * s, hh * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    D = d * s
    dr.pieslice([0, -D / 2, D - 1, D / 2 - 1], 0, 180, fill=(22, 146, 88, 255))
    r = D * .07
    dr.pieslice([r, -D / 2 + r, D - 1 - r, D / 2 - 1 - r], 0, 180, fill=(238, 70, 80, 255))
    for x, y in ((.28, .20), (.46, .30), (.64, .20), (.38, .12), (.56, .12), (.74, .28)):
        dr.ellipse([D * x - D * .02, D * y - D * .03, D * x + D * .02, D * y + D * .03], fill=(40, 30, 30, 255))
    return im.resize((d, hh), Image.LANCZOS)


@lru_cache(None)
def sun(d):
    s = 4
    im = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    c = d * s / 2
    wd = int(d * .07 * s)
    for i in range(8):
        a = i * math.pi / 4
        p0 = (c + math.cos(a) * c * .62, c + math.sin(a) * c * .62)
        p1 = (c + math.cos(a) * c * .94, c + math.sin(a) * c * .94)
        dr.line([p0, p1], fill=NAVY + (255,), width=wd)
        for q in (p0, p1):
            dr.ellipse([q[0] - wd / 2, q[1] - wd / 2, q[0] + wd / 2, q[1] + wd / 2], fill=NAVY + (255,))
    r = c * .46
    dr.ellipse([c - r, c - r, c + r, c + r], fill=WARM + (255,), outline=NAVY + (255,), width=int(d * .05 * s))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def snow(d):
    s = 4
    im = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    c = d * s / 2
    wd = int(d * .06 * s)
    for k in range(3):
        a = k * math.pi / 3
        p0 = (c - math.cos(a) * c * .94, c - math.sin(a) * c * .94)
        p1 = (c + math.cos(a) * c * .94, c + math.sin(a) * c * .94)
        dr.line([p0, p1], fill=NAVY + (255,), width=wd)
        for sg in (-1, 1):
            bx, by = c + sg * math.cos(a) * c * .62, c + sg * math.sin(a) * c * .62
            for da in (-0.75, 0.75):
                b = a + (math.pi if sg < 0 else 0) + da
                dr.line([(bx, by), (bx + math.cos(b) * c * .24, by + math.sin(b) * c * .24)], fill=NAVY + (255,), width=wd)
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def dish(w=320, h=48):
    s = 3
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.pieslice([0, -h * s, w * s - 1, h * s - 1], 0, 180, fill=CREAM + (255,), outline=NAVY + (255,), width=4 * s)
    dr.rounded_rectangle([0, 0, w * s - 1, 9 * s], radius=4 * s, fill=NAVY + (255,))
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def talk_box(w, h):
    s = 3
    tail = 46
    im = Image.new("RGBA", (w * s, (h + tail) * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.polygon([(w * .10 * s, (h - 20) * s), (w * .27 * s, (h - 20) * s), (w * .07 * s, (h + tail) * s)], fill=NAVY + (255,))
    dr.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=int(h * .34 * s), fill=WHITE + (255,), outline=NAVY + (255,), width=6 * s)
    dr.polygon([(w * .115 * s, (h - 26) * s), (w * .25 * s, (h - 26) * s), (w * .085 * s, (h + tail - 14) * s)], fill=WHITE + (255,))
    return im.resize((w, h + tail), Image.LANCZOS)


def tag_layers():
    return (pricetag(300, 136, WHITE, NAVY, "NARX", NAVY, 70),
            pricetag(300, 136, DRED, NAVY, "NARX", WHITE, 70),
            pricetag(300, 136, DGRN, NAVY, "NARX", WHITE, 70))


# ----------------------------------------------------------------------------- the balance scale
DISH_W, STR_DX = 320, 146


def draw_scale(cv, al, yo, th, cx=540, py=1060, L=250, S_=190, post_h=290, wd=20, small=False):
    """beam + post + strings + dishes. th > 0 : left end goes down.  returns (left rim centre, right rim centre)."""
    a = math.radians(th)
    ex, ey = L * math.cos(a), L * math.sin(a)
    le, re_ = (cx - ex, py + ey + yo), (cx + ex, py - ey + yo)
    if not small:
        put(cv, rrect(30, post_h, 12, NAVY), cx, py + post_h / 2 + yo, al)
        put(cv, rrect(330, 36, 18, NAVY), cx, py + post_h + 12 + yo, al)
    poly(cv, [le, re_], NAVY, wd, 1.0, al)
    put(cv, disc(int(wd * 2.9), NAVY), cx, py + yo, al)
    put(cv, disc(int(wd * 1.1), AMBER), cx, py + yo, al)
    rims = []
    dw = DISH_W if not small else int(DISH_W * L / 250)
    dx = STR_DX if not small else int(STR_DX * L / 250)
    for e in (le, re_):
        rim = e[1] + S_
        for sgn in (-1, 1):
            poly(cv, [(e[0], e[1]), (e[0] + sgn * dx, rim)], NAVY, 5 if not small else 3, 1.0, al, caps=False)
        put(cv, dish(dw, int(48 * dw / DISH_W)), e[0], rim + int(24 * dw / DISH_W), al)
        put(cv, disc(int(wd * 1.3), NAVY), e[0], e[1], al)
        rims.append((e[0], rim))
    return rims


def build(tim):
    S, E, ws, we = tim.S, tim.E, tim.ws, tim.we
    END0 = tim.end0
    TAGS = tag_layers()

    W0 = (0.0, S(1) - 0.08)
    W1 = (S(1) - 0.18, S(2) - 0.10)
    WS = (S(2) - 0.18, S(5) - 0.10)
    WE = (S(5) - 0.18, S(6) - 0.10)
    WF = (S(6) - 0.18, S(7) - 0.10)
    WG = (S(7) - 0.18, END0)

    # ------------------------------------------------------------------ 0. hook: "Gulning narxini kim belgilaydi?"
    def sc_hook(cv, t):
        v = vis(t, *W0)
        if not v: return
        al, yo = v
        item(cv, txt("Gulning narxini", 108, TH.fg, "xb", 900), 540, 500, t, -0.12, al, yo)
        item(cv, txt("kim belgilaydi?", 100, DRED, "xb", 900), 540, 618, t, ws(2) - 0.18, al, yo, dur=0.3)
        pop(cv, bouquet(430), 330, 1040, t, -0.05, al, yo, dur=0.4, rot=3 * math.sin(t * 4.2))
        sw = 9 * math.sin(t * 5.0)
        pop(cv, pricetag(430, 200, WHITE, NAVY, "NARX", NAVY, 104), 745, 1060, t, 0.05, al, yo, dur=0.4, rot=sw)
        k = prog(t, ws(2) - 0.05, 0.35)
        if k > 0:
            put(cv, disc(150, DRED), 880, 840 + yo + 10 * math.sin(t * 7), al * ease_out_cubic(k), 0.7 + 0.3 * clamp(ease_out_back(k, 1.8), 0, 1.4))
            put(cv, txt("?", 120, WHITE), 880, 842 + yo + 10 * math.sin(t * 7), al * ease_out_cubic(k), 0.7 + 0.3 * clamp(ease_out_back(k, 1.8), 0, 1.4))

    # ------------------------------------------------------------------ 1. 8-mart oldidan hamma gul olmoqchi
    def sc_crowd(cv, t):
        v = vis(t, *W1)
        if not v: return
        al, yo = v
        item(cv, txt("8-mart oldidan", 90, TH.fg, "xb", 900), 540, 500, t, S(1) - 0.14, al, yo)
        item(cv, txt("hamma gul olmoqchi.", 78, DRED, "xb", 900), 540, 605, t, ws(6) - 0.15, al, yo)
        pop(cv, calendar(), 265, 930, t, S(1) - 0.12, al, yo, dur=0.45, rot=-4 * (1 - ease_out_cubic(prog(t, S(1) - 0.12, 0.6))), rise=-60)
        pop(cv, bouquet(330), 790, 960, t, S(1) + 0.2, al, yo, dur=0.4, rot=2.5 * math.sin(t * 4))
        xs = [150, 300, 450, 600, 750, 900]
        for i, x in enumerate(xs):
            t0 = ws(6) + i * 0.1
            pop(cv, person(150, NAVY if i % 2 == 0 else SLATE2), x, 1290, t, t0, al, yo, dur=0.35, rise=90)
            pop(cv, tulip(88, [TRED, PINK, WHITE][i % 3]), x, 1150, t, t0 + 0.3, al, yo, dur=0.3, rise=20, rot=6 * math.sin(t * 5 + i))

    # ------------------------------------------------------------------ 2-4. tarozi: talab / taklif / narx
    ext_in = [ws(10) - 0.2 + i * 0.22 for i in range(4)]
    ext_out = [ws(24) - 0.10 + i * 0.28 for i in range(4)]

    def extra(t):
        a = sum(ease_in_out(prog(t, d + 0.2, 0.30)) for d in ext_in)
        b = sum(ease_in_out(prog(t, d + 0.05, 0.32)) for d in ext_out)
        return a - b

    def tilt(t):
        th = 11.0 * extra(t) / 4
        for t0, amp in ((ext_in[-1] + 0.5, 1.6), (ext_out[-1] + 0.37, 1.4)):
            if t > t0:
                th += amp * math.sin(15 * (t - t0)) * math.exp(-4.2 * (t - t0))
        return th

    FRONT = [-112, -56, 0, 56, 112]
    BACK = [-84, -28, 28, 84]

    def sc_scale(cv, t):
        v = vis(t, *WS, fo=0.2)
        if not v: return
        al, yo = v
        enter = ease_out_cubic(prog(t, WS[0], 0.35))
        a0, y0 = al * enter, yo + (1 - enter) * 40
        rims = draw_scale(cv, a0, y0, tilt(t))
        (lx, ly), (rx, ry) = rims
        # buyers (front row) and flowers appear with the scale
        for i, off in enumerate(FRONT):
            pop(cv, person(76, NAVY if i % 2 == 0 else SLATE2), lx + off, ly - 8 - 38, t, WS[0] + 0.12 + i * 0.05, al, yo + (ly - ly), dur=0.3, rise=30)
        # extra buyers drop in behind them, then leave
        for i, off in enumerate(BACK):
            d0 = ext_in[i]
            p = (t - d0) / 0.38
            if p <= 0: continue
            lv = prog(t, ext_out[i], 0.4)
            if lv >= 1: continue
            x = lx + off - 150 * ease_in_out(lv)
            y = ly - 8 - 56 - 38 - (1 - bounce(p)) * 260 - 40 * ease_in_out(lv)
            put(cv, person(76, SLATE2 if i % 2 == 0 else NAVY), x, y + yo, al * clamp(p * 5) * (1 - lv))
        # flowers
        cols = [TRED, PINK, WHITE, TRED, PINK]
        wig = prog(t, ws(11), 1.6) * (1 - prog(t, ws(16) - 0.1, 0.2))
        for i, off in enumerate(FRONT):
            pop(cv, tulip(122, cols[i]), rx + off, ry - 4 - 61, t, WS[0] + 0.18 + i * 0.05, al, yo, dur=0.3, rise=30, rot=5 * wig * math.sin(t * 9 + i * 1.3))

        # ---- chips under the dishes
        item(cv, chip("TALAB", NAVY, CREAM, 42), 290, 1425, t, WS[0] + 0.3, al, yo, dur=0.3, rise=16)
        item(cv, chip("TAKLIF", WHITE, NAVY, 42), 790, 1425, t, WS[0] + 0.35, al, yo, dur=0.3, rise=16)
        up = ease_out_cubic(prog(t, ws(16), 0.3)) * (1 - ease_out_cubic(prog(t, ws(24) - 0.05, 0.15)))
        dn = ease_out_cubic(prog(t, ws(24), 0.3))
        bob = 6 * math.sin(t * 8)
        if up > 0:
            put(cv, arrow(74, 17, DRED), 124, 1425 + bob, al * up, 1.0, 90)
        if dn > 0:
            put(cv, arrow(74, 17, DGRN), 124, 1425 - bob, al * dn, 1.0, -90)
        eq = ease_out_cubic(prog(t, ws(18), 0.3))
        if eq > 0:
            put(cv, rrect(52, 11, 5, NAVY), 950, 1414, al * eq, 1.0 + 0.06 * math.sin(t * 7))
            put(cv, rrect(52, 11, 5, NAVY), 950, 1438, al * eq, 1.0 + 0.06 * math.sin(t * 7))

        # ---- text per sentence
        q = sub(t, S(2), S(3) - 0.08, al, yo)
        if q:
            item(cv, txt("Xaridor ko‘p,", 84, TH.fg, "xb", 900), 540, 500, t, S(2) + 0.0, *q)
            item(cv, txt("gul esa deyarli o‘sha miqdorda.", 62, DRED, "xb", 900), 540, 600, t, ws(11) - 0.12, *q)
        q = sub(t, S(3) - 0.08, S(4) - 0.08, al, yo)
        if q:
            item(cv, txt("Talab oshdi,", 74, TH.fg, "xb", 900), 540, 500, t, S(3), *q)
            item(cv, txt("taklif o‘zgarmadi,", 74, TH.fg, "xb", 900), 540, 585, t, ws(18) - 0.12, *q)
            item(cv, txt("narx ko‘tariladi.", 78, DRED, "xb", 900), 540, 675, t, ws(20) - 0.12, *q)
        q = sub(t, S(4) - 0.08, WS[1], al, yo, fo=0.2)
        if q:
            item(cv, txt("Bayramdan keyin", 74, TH.fg, "xb", 900), 540, 500, t, S(4), *q)
            item(cv, txt("talab tushadi,", 74, TH.fg, "xb", 900), 540, 585, t, ws(24) - 0.12, *q)
            item(cv, txt("narx ham pasayadi.", 78, DGRN, "xb", 900), 540, 675, t, ws(26) - 0.12, *q)

        # ---- price tag (rides up and down above the scale)
        if t >= S(3) - 0.02:
            lvl = ease_in_out(prog(t, ws(20) - 0.1, 1.0)) - ease_in_out(prog(t, ws(26), 0.9))
            k_up = ease_out_cubic(prog(t, ws(20) + 0.3, 0.35)) * (1 - ease_out_cubic(prog(t, ws(26) - 0.1, 0.2)))
            k_dn = ease_out_cubic(prog(t, ws(26) + 0.2, 0.35))
            cy = lerp(950, 840, lvl)
            sc = lerp(1.0, 1.18, lvl)
            ent = ease_out_cubic(prog(t, S(3), 0.35))
            aa = al * ent
            rot = 3 * math.sin(t * 6) * (0.3 + lvl)
            put(cv, TAGS[0], 540, cy + yo + (1 - ent) * 30, aa, sc, rot)
            if k_up > 0.01: put(cv, TAGS[1], 540, cy + yo + (1 - ent) * 30, aa * k_up, sc, rot)
            if k_dn > 0.01: put(cv, TAGS[2], 540, cy + yo + (1 - ent) * 30, aa * k_dn, sc, rot)
            if k_up > 0.01:
                put(cv, arrow(120, 24, DRED), 790, cy + yo + 8 * math.sin(t * 9), aa * k_up, 1.0, 90)
            if k_dn > 0.01:
                put(cv, arrow(120, 24, DGRN), 790, cy + yo - 8 * math.sin(t * 9), aa * k_dn, 1.0, -90)

    # ------------------------------------------------------------------ 5. xuddi shu qoida: kvartira, dollar, pomidor
    def sc_cards(cv, t):
        v = vis(t, *WE)
        if not v: return
        al, yo = v
        q = sub(t, S(5), ws(32) - 0.12, al, yo, fo=0.12)
        if q:
            item(cv, txt("Xuddi shu qoida", 96, TH.fg, "xb", 900), 540, 500, t, S(5), *q)
        if t >= ws(32) - 0.12:
            words_line(cv, ["kvartira,", "dollar,", "pomidorga"], 74, 500, [ws(32) - 0.1, ws(33) - 0.1, ws(34) - 0.1], t, al, yo)
        item(cv, txt("ham tegadi.", 84, DRED, "xb", 900), 540, 600, t, ws(35) - 0.1, al, yo)
        # mini scale that rocks above the cards
        mk = ease_out_cubic(prog(t, S(5) + 0.05, 0.4))
        if mk > 0:
            draw_scale(cv, al * mk, yo + (1 - mk) * 30, 10 * math.sin(t * 3.0), cx=540, py=770, L=130, S_=95, post_h=0, wd=12, small=True)
        icons = [(215, ws(32) - 0.15, lambda: building(190)), (540, ws(33) - 0.15, lambda: coin(170, NAVY, (6, 18, 36), "$", AMBER)), (865, ws(34) - 0.15, lambda: tomato(170))]
        for i, (x, t0, mk_icon) in enumerate(icons):
            pop(cv, rrect(250, 380, 40, WHITE, NAVY, 6), x, 1150, t, S(5) + 0.25 + i * 0.12, al, yo, dur=0.4, rise=60)
            pop(cv, mk_icon(), x, 1085, t, t0 + 0.08, al, yo, dur=0.4, rise=60)
            ph = (t - t0 - 0.5)
            if ph > 0:
                # price tag bobs up (red) and down (green) in turns
                sw = math.sin(ph * 4.2 + i * 0.9)
                up = sw >= 0
                lift = -22 * sw
                col = DRED if up else DGRN
                a2 = al * ease_out_cubic(clamp(ph * 3))
                put(cv, pricetag(176, 78, WHITE, NAVY, "NARX", NAVY, 40), x - 22, 1262 + lift + yo, a2, 1.0)
                put(cv, rrect(176, 78, 20, CREAM, NAVY, 3), x - 22, 1262 + lift + yo, 0, 1.0)
                put(cv, arrow(56, 14, col), x + 84, 1262 + lift + yo, a2, 1.0, 90 if up else -90)

    # ------------------------------------------------------------------ 6. narx = talab va taklif uchrashgan joy
    X0, X1, Y0, Y1 = 220, 910, 780, 1290

    def y_d(u): return Y0 + (Y1 - Y0) * (1 - (1 - u) ** 2.2)

    def y_s(u): return Y1 - (Y1 - Y0) * u ** 1.5

    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if y_d(mid) < y_s(mid): lo = mid
        else: hi = mid
    UX = (lo + hi) / 2
    PX, PY = X0 + (X1 - X0) * UX, y_d(UX)

    def sc_chart(cv, t):
        v = vis(t, *WF)
        if not v: return
        al, yo = v
        item(cv, txt("Narx —", 86, TH.fg, "xb", 900), 540, 500, t, WF[0] + 0.12, al, yo)
        words_line(cv, ["talab", "va", "taklif"], 78, 590, [ws(38) - 0.08, ws(39) - 0.08, ws(40) - 0.08], t, al, yo)
        item(cv, txt("uchrashgan joy.", 84, DRED, "xb", 900), 540, 685, t, ws(41) - 0.1, al, yo)
        # axes
        pa = ease_out_cubic(prog(t, WF[0] + 0.1, 0.4))
        poly(cv, [(X0 - 30, Y0 - 40 + yo), (X0 - 30, Y1 + 40 + yo), (X1 + 30, Y1 + 40 + yo)], NAVY, 9, pa, al)
        # demand / supply curves draw themselves with the words
        dp = ease_in_out(prog(t, ws(38) - 0.05, 0.8))
        sp = ease_in_out(prog(t, ws(40) - 0.05, 0.8))
        poly(cv, [(X0 + (X1 - X0) * u / 40, y_d(u / 40) + yo) for u in range(41)], DRED, 14, dp, al)
        poly(cv, [(X0 + (X1 - X0) * u / 40, y_s(u / 40) + yo) for u in range(41)], DGRN, 14, sp, al)
        pop(cv, chip("TALAB", DRED, WHITE, 34), X0 + 95, Y0 + 70, t, ws(38) + 0.55, al, yo, dur=0.3, rise=10)
        pop(cv, chip("TAKLIF", DGRN, WHITE, 34), X1 - 90, Y0 + 70, t, ws(40) + 0.55, al, yo, dur=0.3, rise=10)
        # meeting point
        k = prog(t, ws(41) + 0.1, 0.4)
        if k > 0:
            e = ease_out_cubic(k)
            sc = 0.5 + 0.5 * clamp(ease_out_back(k, 1.8), 0, 1.4)
            ring = 1 + 0.14 * math.sin(t * 8)
            put(cv, disc(120, None, NAVY, 7), PX, PY + yo, al * e * 0.55, ring * sc)
            put(cv, disc(58, NAVY), PX, PY + yo, al * e, sc)
            put(cv, disc(26, WARM), PX, PY + yo, al * e, sc)
            dashed_line(cv, (X0 - 30, PY + yo), (PX - 40, PY + yo), NAVY, 6, 18, 12, ease_out_cubic(prog(t, ws(41) + 0.35, 0.4)), al * 0.8)
            dashed_line(cv, (PX, PY + 40 + yo), (PX, Y1 + 40 + yo), NAVY, 6, 18, 12, ease_out_cubic(prog(t, ws(41) + 0.35, 0.4)), al * 0.8)
            pop(cv, pricetag(210, 92, WHITE, NAVY, "NARX", NAVY, 46), X0 + 112, PY, t, ws(42) - 0.05, al, yo, dur=0.35, rise=0)

    # ------------------------------------------------------------------ 7. CTA: mavsumga qarab narxi o'zgaradigan mahsulotni izohda yoz
    def sc_cta(cv, t):
        v = vis(t, *WG, fo=0.25)
        if not v: return
        al, yo = v
        item(cv, txt("Mavsumga qarab", 80, TH.fg, "xb", 900), 540, 490, t, WG[0] + 0.1, al, yo)
        item(cv, txt("narxi o‘zgaradigan", 68, TH.fg, "xb", 900), 540, 575, t, ws(45) - 0.1, al, yo)
        item(cv, txt("mahsulotni", 68, DRED, "xb", 900), 540, 655, t, ws(47) - 0.12, al, yo)
        # sun <-> tag <-> snowflake : the season changes, the price follows
        sp = prog(t, S(7) - 0.05, 0.45)
        if sp > 0:
            pop(cv, sun(190), 235, 900, t, S(7) - 0.05, al, yo, dur=0.45, rot=40 * t)
        pop(cv, snow(180), 845, 900, t, ws(44) - 0.05, al, yo, dur=0.45, rot=-25 * t)
        ph = t - ws(45)
        if ph > -0.2:
            sw = math.sin(max(0, ph) * 3.6)
            up = sw >= 0
            ent = ease_out_cubic(clamp((ph + 0.2) * 3))
            put(cv, pricetag(300, 136, WHITE, NAVY, "NARX", NAVY, 70), 540 + 14 * sw, 900 - 26 * sw + yo, al * ent, 1.0, -5 * sw)
            put(cv, arrow(92, 20, DRED if up else DGRN), 540 + 14 * sw, 800 - 14 * sw + yo, al * ent, 1.0, 90 if up else -90)
        pop(cv, tomato(150), 330, 1090, t, ws(47) - 0.05, al, yo, dur=0.4, rise=60, rot=6 * math.sin(t * 4))
        pop(cv, melon(210), 750, 1100, t, ws(47) + 0.1, al, yo, dur=0.4, rise=60, rot=-5 * math.sin(t * 4))
        # comment box with the typed answer
        bp = prog(t, ws(48) - 0.3, 0.4)
        if bp > 0:
            e = ease_out_cubic(bp)
            put(cv, talk_box(780, 200), 540, 1330 + (1 - e) * 50 + yo, al * e, 0.9 + 0.1 * clamp(ease_out_back(bp, 1.5), 0, 1.3))
            lay = txt("izohda yoz.", 92, NAVY, "xb", 640)
            pp = prog(t, ws(48) - 0.1, 0.95)
            w_, h_ = lay.size
            cw = int(8 + (w_ - 16) * pp) + 4
            if pp > 0:
                crop = lay.crop((0, 0, min(w_, cw), h_))
                left = 540 - (w_ - 16) / 2 - 8
                put(cv, crop, left + crop.width / 2, 1318 + yo, al * e)
                if int(t * 3) % 2 == 0 or pp < 1:
                    put(cv, rrect(9, int(h_ * .62), 4, DRED), left + crop.width - 4 + 6, 1322 + yo, al * e)

    # ------------------------------------------------------------------ "soddalashtirib aytganda" badge
    def sc_badge(cv, t):
        v = vis(t, 0.2, END0 - 0.45, fo=0.3)
        if not v: return
        al, yo = v
        pop(cv, chip("Soddalashtirib aytganda", NAVY, CREAM, 32), 540, 392, t, 0.25, al, yo, dur=0.3, rise=14)

    return Reel(tim, [sc_hook, sc_crowd, sc_scale, sc_cards, sc_chart, sc_cta, sc_badge],
                theme="amber", bg="top", overlay_kind="diag", disclaimer="Bu umumiy ma‘lumot, shaxsiy maslahat emas.")
