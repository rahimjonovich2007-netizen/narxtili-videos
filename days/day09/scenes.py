"""Day 9 - 50/30/20 qoidasi (Shaxsiy moliya).  Look: slate theme, flat background, grid overlay.
Visual metaphor: maosh xaltasidan tangalar uchib ketadi -> maosh chizig'i uch rangli ulushga bo'linadi (50 / 30 / 20) ->
har ulush o'z bankasini to'ldiradi (ikonkalar bankaga sakraydi) -> 5 000 000 so'm doira diagrammada yoyma-yoy chiziladi ->
foizlar siljiydi ("senda boshqacha") -> avval jamg'arma, keyin sarf -> "shu yetarli" -> taqvim va xatcho'p.
Animated explainer (objects move and transform with the words) - NOT text-only."""
import math
from functools import lru_cache

from PIL import ImageChops

from nt_kit import *

NEED, WANT, SAVE = (120, 190, 255), AMBER, GREEN
INK = (14, 26, 48)
SH = (50, 30, 20)
COLS = (NEED, WANT, SAVE)


# ----------------------------------------------------------------------------- small helpers
def bez(P0, P1, P2, s):
    return ((1 - s) ** 2 * P0[0] + 2 * (1 - s) * s * P1[0] + s * s * P2[0],
            (1 - s) ** 2 * P0[1] + 2 * (1 - s) * s * P1[1] + s * s * P2[1])


def bounce(p):
    p = clamp(p)
    if p < 1 / 2.75: return 7.5625 * p * p
    if p < 2 / 2.75: p -= 1.5 / 2.75; return 7.5625 * p * p + .75
    if p < 2.5 / 2.75: p -= 2.25 / 2.75; return 7.5625 * p * p + .9375
    p -= 2.625 / 2.75; return 7.5625 * p * p + .984375


def chip(text, bg, fg=INK, size=44, maxw=620):
    t = txt(text, size, fg, "xb", maxw=maxw)
    w, h = t.width + 60, t.height + 14
    base = rrect(w, h, h // 2, tuple(bg)).copy()
    base.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2))
    return base


def qfmt(v, step=50000):
    return fmt(round(v / step) * step)


def _c(w, h, s=4):
    return Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0)), s


# ----------------------------------------------------------------------------- icons drawn with PIL
@lru_cache(None)
def house(d):
    im, s = _c(d, d)
    dr = ImageDraw.Draw(im)
    D = d * s
    wall, roof, door, win = (244, 230, 200, 255), (220, 90, 72, 255), (120, 76, 42, 255), (110, 170, 235, 255)
    dr.rectangle([D * .70, D * .12, D * .80, D * .34], fill=roof)
    dr.rectangle([D * .16, D * .46, D * .84, D * .92], fill=wall)
    dr.polygon([(D * .06, D * .50), (D * .50, D * .10), (D * .94, D * .50)], fill=roof)
    dr.rectangle([D * .43, D * .62, D * .60, D * .92], fill=door)
    dr.rectangle([D * .24, D * .56, D * .37, D * .70], fill=win)
    dr.rectangle([D * .66, D * .56, D * .78, D * .70], fill=win)
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def bread(d):
    im, s = _c(d, d)
    dr = ImageDraw.Draw(im)
    D = d * s
    dr.rounded_rectangle([D * .02, D * .28, D * .98, D * .88], radius=int(D * .3), fill=(226, 170, 92, 255))
    for x in (.30, .48, .66):
        dr.line([(D * (x - .05), D * .42), (D * (x + .03), D * .66)], fill=(180, 120, 50, 255), width=int(D * .05))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def bus(d):
    w, h = d, int(d * 0.75)
    im, s = _c(w, h)
    dr = ImageDraw.Draw(im)
    Wd, Hd = w * s, h * s
    body, dark, glass = (255, 196, 40, 255), (40, 50, 70, 255), (150, 205, 245, 255)
    dr.rounded_rectangle([Wd * .04, Hd * .08, Wd * .96, Hd * .80], radius=int(Wd * .09), fill=body)
    for i in range(4):
        x0 = Wd * (.10 + i * .205)
        dr.rounded_rectangle([x0, Hd * .20, x0 + Wd * .16, Hd * .46], radius=int(Wd * .02), fill=glass)
    dr.rectangle([Wd * .04, Hd * .56, Wd * .96, Hd * .62], fill=(230, 150, 20, 255))
    for cx in (.26, .74):
        dr.ellipse([Wd * cx - Wd * .085, Hd * .66, Wd * cx + Wd * .085, Hd * .66 + Wd * .17], fill=dark)
        dr.ellipse([Wd * cx - Wd * .035, Hd * .66 + Wd * .05, Wd * cx + Wd * .035, Hd * .66 + Wd * .12], fill=(200, 205, 215, 255))
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def cup(d):
    im, s = _c(d, d)
    dr = ImageDraw.Draw(im)
    D = d * s
    cream, brown = (250, 244, 232, 255), (120, 78, 44, 255)
    dr.ellipse([D * .04, D * .80, D * .96, D * .96], fill=(206, 212, 226, 255))
    dr.arc([D * .60, D * .42, D * .92, D * .74], -85, 95, fill=cream, width=int(D * .07))
    dr.rounded_rectangle([D * .16, D * .34, D * .74, D * .86], radius=int(D * .14), fill=cream)
    dr.rectangle([D * .19, D * .36, D * .71, D * .46], fill=brown)
    for x in (.30, .45, .60):
        pts = [((x + math.sin(i / 2.4) * .03) * D, (.26 - i * .028) * D) for i in range(8)]
        dr.line(pts, fill=(235, 240, 248, 210), width=int(D * .035), joint="curve")
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def shirt(d):
    im, s = _c(d, d)
    dr = ImageDraw.Draw(im)
    D = d * s
    pts = [(.30, .12), (.40, .12), (.50, .20), (.60, .12), (.70, .12), (.96, .30), (.84, .52), (.72, .44), (.72, .90), (.28, .90), (.28, .44), (.16, .52), (.04, .30)]
    dr.polygon([(x * D, y * D) for x, y in pts], fill=(236, 98, 120, 255))
    dr.arc([D * .38, D * .02, D * .62, D * .34], 0, 180, fill=(184, 56, 84, 255), width=int(D * .045))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def pad(d):
    w, h = d, int(d * 0.70)
    im, s = _c(w, h)
    dr = ImageDraw.Draw(im)
    Wd, Hd = w * s, h * s
    dr.rounded_rectangle([Wd * .02, Hd * .16, Wd * .98, Hd * .94], radius=int(Hd * .40), fill=(124, 132, 214, 255))
    cx, cy, arm, th = Wd * .27, Hd * .54, Hd * .22, Hd * .13
    dr.rounded_rectangle([cx - arm, cy - th / 2, cx + arm, cy + th / 2], radius=int(th / 3), fill=(40, 44, 96, 255))
    dr.rounded_rectangle([cx - th / 2, cy - arm, cx + th / 2, cy + arm], radius=int(th / 3), fill=(40, 44, 96, 255))
    for bx, by, col in ((.72, .42, (255, 204, 70, 255)), (.83, .58, (240, 92, 92, 255))):
        r = Hd * .085
        dr.ellipse([Wd * bx - r, Hd * by - r, Wd * bx + r, Hd * by + r], fill=col)
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def bookmark(w=110, h=160, col=RED):
    im, s = _c(w, h)
    dr = ImageDraw.Draw(im)
    Wd, Hd = w * s, h * s
    dr.polygon([(0, 0), (Wd, 0), (Wd, Hd), (Wd / 2, Hd * .74), (0, Hd)], fill=tuple(col) + (255,))
    dr.rectangle([Wd * .12, 0, Wd * .24, Hd * .70], fill=(255, 255, 255, 60))
    return im.resize((w, h), Image.LANCZOS)


CALW, CALH = 560, 620
CAL_CELL, CAL_GAP, CAL_X0, CAL_Y0 = 84, 16, 38, 160
HI = (1, 2)   # highlighted cell (row, col)


@lru_cache(None)
def calendar():
    im, s = _c(CALW, CALH, 3)
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle([0, 0, CALW * s - 1, CALH * s - 1], radius=40 * s, fill=tuple(CREAM) + (255,))
    dr.rounded_rectangle([0, 0, CALW * s - 1, 118 * s], radius=40 * s, fill=tuple(AMBER) + (255,), corners=(True, True, False, False))
    for x in (150, 410):
        dr.rounded_rectangle([(x - 12) * s, -10 * s, (x + 12) * s, 40 * s], radius=12 * s, fill=(40, 50, 76, 255))
    for r in range(4):
        for c in range(5):
            x0 = CAL_X0 + c * (CAL_CELL + CAL_GAP)
            y0 = CAL_Y0 + r * (CAL_CELL + CAL_GAP)
            dr.rounded_rectangle([x0 * s, y0 * s, (x0 + CAL_CELL) * s, (y0 + CAL_CELL) * s], radius=18 * s, fill=(232, 226, 212, 255))
    im = im.resize((CALW, CALH), Image.LANCZOS)
    t = txt("MAOSH KUNI", 50, INK, "xb", maxw=420)
    im.alpha_composite(t, ((CALW - t.width) // 2, 74 - t.height // 2))
    return im


def cal_cell_center(cx, cy, rc=HI):
    r, c = rc
    return (cx - CALW / 2 + CAL_X0 + c * (CAL_CELL + CAL_GAP) + CAL_CELL / 2,
            cy - CALH / 2 + CAL_Y0 + r * (CAL_CELL + CAL_GAP) + CAL_CELL / 2)


# ----------------------------------------------------------------------------- jar (the "bucket")
JW, JH = 380, 520
JI_X0, JI_X1, JI_Y0, JI_Y1 = 38, 342, 104, 494     # liquid interior


@lru_cache(None)
def jar_glass(kind):
    s = 3
    im = Image.new("RGBA", (JW * s, JH * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    if kind == "back":
        dr.rounded_rectangle([24 * s, 90 * s, 356 * s, 508 * s], radius=60 * s, fill=tuple(CREAM) + (36,))
    else:
        dr.rounded_rectangle([24 * s, 90 * s, 356 * s, 508 * s], radius=60 * s, outline=tuple(CREAM) + (205,), width=8 * s)
        dr.rounded_rectangle([34 * s, 44 * s, 346 * s, 100 * s], radius=18 * s, fill=(222, 228, 240, 255))
        dr.rounded_rectangle([34 * s, 44 * s, 346 * s, 62 * s], radius=9 * s, fill=(246, 248, 252, 255))
        dr.rounded_rectangle([58 * s, 132 * s, 72 * s, 420 * s], radius=7 * s, fill=(255, 255, 255, 72))
    return im.resize((JW, JH), Image.LANCZOS)


@lru_cache(None)
def _jar_mask(s):
    m = Image.new("L", (JW * s, JH * s), 0)
    ImageDraw.Draw(m).rounded_rectangle([JI_X0 * s, JI_Y0 * s, JI_X1 * s, JI_Y1 * s], radius=46 * s, fill=255)
    return m


def jar_liquid(level, color, phase):
    level = clamp(level)
    if level <= 0.004:
        return None
    s = 2
    top = JI_Y1 - level * (JI_Y1 - JI_Y0)
    im = Image.new("RGBA", (JW * s, JH * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    amp = 5 * min(1.0, level * 6)
    pts = [((JI_X0 + (JI_X1 - JI_X0) * i / 60) * s, (top + amp * math.sin((JI_X0 + (JI_X1 - JI_X0) * i / 60) / 36 + phase)) * s) for i in range(61)]
    dr.polygon(pts + [(JI_X1 * s, (JI_Y1 + 8) * s), (JI_X0 * s, (JI_Y1 + 8) * s)], fill=tuple(color) + (238,))
    dr.line(pts, fill=tuple(mixc(color, WHITE, .5)) + (255,), width=4 * s)
    im.putalpha(ImageChops.multiply(im.getchannel("A"), _jar_mask(s)))
    return im.resize((JW, JH), Image.LANCZOS)


def draw_jar(cv, cx, cy, level, color, t, al=1.0, sc=1.0):
    put(cv, jar_glass("back"), cx, cy, al, sc)
    liq = jar_liquid(level, color, t * 3.2)
    if liq is not None:
        put(cv, liq, cx, cy, al, sc)
    put(cv, jar_glass("front"), cx, cy, al, sc)


# ----------------------------------------------------------------------------- donut + stat cards
def donut(cv, cx, cy, R, th, vals, cols, sweeps, alpha=1.0):
    s, pad_ = 3, 6
    size = int(2 * R + 2 * pad_)
    im = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    bbox = [pad_ * s, pad_ * s, (pad_ + 2 * R) * s - 1, (pad_ + 2 * R) * s - 1]
    a = 0.0
    tot = float(sum(vals))
    for v, col, sw in zip(vals, cols, sweeps):
        span = v / tot * 360.0
        a0, a1 = a, a + span * clamp(sw)
        a += span
        if sw <= 0.002:
            continue
        g = 1.3 if (a1 - a0) > 5 else 0.0
        dr.arc(bbox, a0 + g - 90, a1 - g - 90, fill=tuple(col) + (255,), width=int(th * s))
    put(cv, im.resize((size, size), Image.LANCZOS), cx, cy, alpha)


@lru_cache(None)
def stat_card(pct, amt, col):
    w, h = 280, 170
    base = rrect(w, h, 30, tuple(TH.card)).copy()
    if amt:
        p = txt(pct, 58, col, "xb", maxw=220)
        a = txt(amt, 50, TH.fg, "xb", maxw=250)
        base.alpha_composite(p, ((w - p.width) // 2, 14))
        base.alpha_composite(rrect(110, 8, 4, tuple(col)), ((w - 110) // 2, 88))
        base.alpha_composite(a, ((w - a.width) // 2, 100))
    else:
        p = txt(pct, 96, col, "xb", maxw=240)
        base.alpha_composite(p, ((w - p.width) // 2, (h - p.height) // 2))
    return base


def fly(cv, layer, P0, P1, P2, t, t0, dur, al, yo=0.0, s_end=0.42):
    """layer arcs from P0 over P1 into P2 (the jar mouth), shrinking and fading as it drops in"""
    p = (t - t0) / dur
    if p <= 0 or p >= 1:
        return
    x, y = bez(P0, P1, P2, ease_in_out(p))
    sc = lerp(1.0, s_end, ease_in_cubic(p)) * (0.6 + 0.4 * clamp(ease_out_back(clamp(p * 5), 1.4), 0, 1.3))
    a = al * ease_out_cubic(clamp(p * 7)) * (1.0 if p < 0.82 else (1 - p) / 0.18)
    put(cv, layer, x, y + yo, a, sc, 0)


# ----------------------------------------------------------------------------- the reel
def build(tim):
    S, E, ws, we = tim.S, tim.E, tim.ws, tim.we
    END0 = tim.end0
    # scene windows (a, b)
    W_HOOK = (0.0, S(1) - 0.10)
    W_RULE = (W_HOOK[1] - 0.08, S(2) - 0.12)
    W_NEED = (W_RULE[1] - 0.08, S(3) - 0.10)
    W_WANT = (W_NEED[1] - 0.08, S(4) - 0.10)
    W_SAVE = (W_WANT[1] - 0.08, S(5) - 0.10)
    W_DON = (W_SAVE[1] - 0.08, S(7) - 0.10)
    W_FIRST = (W_DON[1] - 0.08, S(8) - 0.10)
    W_ENOUGH = (W_FIRST[1] - 0.08, S("cta") - 0.10)
    W_CTA = (W_ENOUGH[1] - 0.08, END0)
    T_FLEX0 = ws(44) - 0.15
    WINS = (W_NEED, W_WANT, W_SAVE)

    # ------------------------------------------------------------- hook: salary bag, coins fly away
    coin_dst = [(-470, 360), (430, 330), (-300, 400), (500, 380), (-150, 350), (260, 390), (-540, 330), (380, 340)]

    def sc_hook(cv, t):
        v = vis(t, *W_HOOK)
        if not v: return
        al, yo = v
        item(cv, txt("Maoshing qayerga", 100), 540, 460, t, -0.12, al, yo)
        item(cv, txt("ketayotganini", 118, TH.acc), 540, 590, t, max(0.3, ws(2) - 0.2), al, yo)
        item(cv, txt("bilasanmi?", 118), 540, 715, t, max(0.5, ws(3) - 0.15), al, yo)
        for i, (dx, up) in enumerate(coin_dst):
            t0 = 0.10 + 0.17 * i
            p = (t - t0) / 1.05
            if 0 < p < 1:
                P0, P1, P2 = (540, 950), (540 + dx * 0.55, 950 - up), (540 + dx, 1040 + 380 * (i % 3 + 1) / 3)
                x, y = bez(P0, P1, P2, ease_in_out(p) * 0.5 + p * 0.5)
                a = al * ease_out_cubic(clamp(p * 6)) * (1.0 if p < 0.8 else (1 - p) / 0.2)
                put(cv, coin(118, AMBER), x, y + yo, a, 0.8 + 0.2 * (1 - p), (-1) ** i * 330 * p)
        e = ease_out_back(prog(t, -0.1, 0.5), 1.3)
        wob = 4 * math.sin(t * 9) * clamp((t - 0.1) * 3)
        put(cv, bag(330, 380, AMBER, (214, 138, 0)), 540, 1090 + yo + (1 - clamp(e, 0, 1.2)) * 120, al * ease_out_cubic(prog(t, -0.1, 0.3)), 1.0, wob)
        item(cv, txt("MAOSH", 66, (140, 84, 0)), 540, 1160, t, -0.05, al, yo)
        q = prog(t, ws(3) - 0.05, 0.35)
        if q > 0:
            put(cv, txt("?", 230, TH.acc), 820, 930 + yo + 12 * math.sin(t * 6), al * ease_out_cubic(q), 0.7 + 0.3 * clamp(ease_out_back(q, 1.6), 0, 1.4), 8)
            put(cv, txt("?", 140, TH.fg), 250, 1000 + yo - 10 * math.sin(t * 5 + 1), al * ease_out_cubic(q) * 0.8, 0.7 + 0.3 * clamp(ease_out_back(q, 1.6), 0, 1.4), -10)

    # ------------------------------------------------------------- the salary bar (spans rule + the three buckets)
    T_BAR0, T_SPLIT = W_RULE[0] + 0.03, ws(5) - 0.30
    T_MOVE, T_OFF = W_RULE[1] - 0.32, W_SAVE[1] - 0.22

    def sc_bar(cv, t):
        if t < T_BAR0 or t > T_OFF + 0.3: return
        al = ease_out_cubic(prog(t, T_BAR0, 0.35)) * (1 - ease_in_out(prog(t, T_OFF, 0.25)))
        sp = ease_in_out(prog(t, T_SPLIT, 0.4))
        mv = ease_in_out(prog(t, T_MOVE, 0.38))
        cy = lerp(900, 385, mv)
        h = int(lerp(110, 26, mv))
        dim = ease_in_out(prog(t, W_NEED[0] - 0.05, 0.3))
        if sp < 0.01:
            put(cv, rrect(900, h, h // 2, tuple(CREAM)), 540, cy, al)
        else:
            gap = max(2, int(lerp(0, 12, sp)))
            tot = 900 - 2 * gap
            x = 90.0
            for i in range(3):
                wi = int(round(tot * SH[i] / 100))
                on = ease_in_out(prog(t, WINS[i][0] - 0.05, 0.2)) * (1 - ease_in_out(prog(t, WINS[i][1] - 0.18, 0.2)))
                if i == 2:
                    on = ease_in_out(prog(t, WINS[i][0] - 0.05, 0.2))
                a_i = lerp(1.0, lerp(0.30, 1.0, on), dim)
                put(cv, rrect(wi, h, h // 2, tuple(mixc(CREAM, COLS[i], sp))), x + wi / 2, cy, al * a_i)
                if h > 70:
                    put(cv, txt(f"{SH[i]}%", 62, INK, "xb", maxw=wi - 30), x + wi / 2, cy, al * clamp((sp - 0.55) * 2.2) * (1 - mv))
                x += wi + gap
        if h > 70:
            put(cv, txt("MAOSH", 56, INK), 540, cy, al * (1 - clamp(sp * 3.0)) * (1 - mv))

    def sc_rule(cv, t):
        v = vis(t, *W_RULE, fo=0.30)
        if not v: return
        al, yo = v
        item(cv, txt2("Oddiy ", "qoida", 108), 540, 560, t, W_RULE[0], al, yo)
        item(cv, fit((("50", NEED), (" / ", TH.fg), ("30", WANT), (" / ", TH.fg), ("20", SAVE)), 168, "xb", 900), 540, 1150, t, ws(5) - 0.1, al, yo)
        item(cv, chip("BOSHLANG‘ICH NUQTA", TH.card, TH.fg, 36), 540, 1390, t, ws(5) + 0.15, al, yo, base=0.9)

    # ------------------------------------------------------------- the three buckets (50 / 30 / 20)
    def bucket(win, k, pct, label, t_pct, t_label, items, chips_x=None):
        col, share = COLS[k], SH[k] / 100.0
        n = len(items)
        chips = [chip(it[2], col) if it[2] else None for it in items]
        shown = [c for c in chips if c is not None]

        def fn(cv, t):
            v = vis(t, *win)
            if not v: return
            al, yo = v
            item(cv, txt(pct, 230, col), 540, 545, t, t_pct, al, yo, dur=0.36)
            item(cv, txt(label, 66, TH.fg, "xb", maxw=900), 540, 700, t, t_label, al, yo)
            e = ease_out_cubic(prog(t, win[0] + 0.05, 0.45))
            level = 0.0
            for i, it in enumerate(items):
                level += share / n * ease_in_out(prog(t, it[1] + 0.42, 0.40))
            draw_jar(cv, 540, 1010 + yo + (1 - e) * 80, level, col, t, al * e)
            # items hop into the jar, chips appear under it
            for i, it in enumerate(items):
                side = -1 if i % 2 == 0 else 1
                P0 = (540 + side * 360, 1000)
                P1 = (540 + side * 190, 745)
                P2 = (540, 880)
                fly(cv, it[0], P0, P1, P2, t, it[1], 0.55, al, yo)
            tot = sum(c.width for c in shown) + 18 * (len(shown) - 1)
            x = 540 - tot / 2
            for i, c in enumerate(chips):
                if c is None:
                    continue
                cx = x + c.width / 2 if chips_x is None else chips_x[i]
                item(cv, c, cx, 1345, t, items[i][1] - 0.05, al, yo)
                x += c.width + 18

        return fn

    f_need = bucket(W_NEED, 0, "50%", "majburiy xarajat", ws(6) - 0.05, ws(8) - 0.12,
                    [(house(150), ws(10), "ijara"), (bread(150), ws(11), "ovqat"), (bus(170), ws(12), "yo‘l")])
    f_want = bucket(W_WANT, 1, "30%", "xohlagan narsang", ws(13) - 0.05, ws(15) - 0.12,
                    [(cup(150), ws(17), "kafe"), (shirt(150), ws(18), "kiyim"), (pad(170), ws(19), "ko‘ngilochar")])
    tag = pricetag(330, 130, RED, (150, 40, 36), "QARZ", WHITE, 70)
    cross_l = cross(120, WHITE, 20)

    def sc_need(cv, t): f_need(cv, t)

    def sc_want(cv, t): f_want(cv, t)

    f_save = bucket(W_SAVE, 2, "20%", "jamg‘arma va qarzni yopish", ws(20) - 0.05, ws(22) - 0.12,
                    [(coin(130, AMBER), ws(22) + 0.00, "jamg‘arma"), (coin(130, AMBER), ws(22) + 0.22, ""), (coin(130, AMBER), ws(22) + 0.44, "")],
                    chips_x=[330, 0, 0])

    def sc_save(cv, t):
        f_save(cv, t)
        v = vis(t, *W_SAVE)
        if not v: return
        al, yo = v
        # the debt tag appears at "qarzni", is crossed out at "yopish"
        tp = prog(t, ws(24) - 0.05, 0.35)
        gone = ease_in_out(prog(t, ws(25) + 0.35, 0.35))
        if tp > 0:
            sc = (0.7 + 0.3 * clamp(ease_out_back(tp, 1.5), 0, 1.4)) * (1 - 0.25 * gone)
            put(cv, tag, 790, 1345 + yo, al * ease_out_cubic(tp) * (1 - gone * 0.85), sc, -3)
        cp = prog(t, ws(25), 0.3)
        if cp > 0:
            put(cv, cross_l, 790, 1345 + yo, al * ease_out_cubic(cp) * (1 - gone * 0.85), 0.6 + 0.4 * clamp(ease_out_back(cp, 1.8), 0, 1.4))

    # ------------------------------------------------------------- example: 5 000 000 -> donut + three cards
    DC, R, RTH = (540, 890), 270, 92
    CARD_Y = 1310
    CARD_X = (245, 540, 835)
    T_S1, T_S2, T_S3 = ws(32), ws(36), ws(41)

    def vals_at(t):
        k1 = ease_in_out(prog(t, ws(45), 0.45))
        k2 = ease_in_out(prog(t, ws(47) - 0.05, 0.45))
        a, b, c = (50, 30, 20), (60, 25, 15), (40, 30, 30)
        return [lerp(lerp(a[i], b[i], k1), c[i], k2) for i in range(3)]

    def sc_donut(cv, t):
        v = vis(t, *W_DON, fo=0.18)
        if not v: return
        al, yo = v
        flex = t >= T_FLEX0
        # headline chips / text
        chip_a = al * (1 - ease_in_out(prog(t, T_FLEX0 - 0.08, 0.16)))
        item(cv, chip("MISOL", TH.acc, INK, 52), 540, 470, t, W_DON[0] + 0.02, chip_a, yo)
        item(cv, txt("Foizlar senda", 86), 540, 455, t, T_FLEX0, al, yo)
        item(cv, txt("boshqacha bo‘lishi mumkin", 62, TH.acc, "xb", maxw=900), 540, 546, t, ws(46) - 0.12, al, yo)
        # centre disc
        pc = prog(t, W_DON[0] + 0.06, 0.4)
        if pc > 0:
            put(cv, disc(340, tuple(TH.card), None, 0), DC[0], DC[1] + yo, al * ease_out_cubic(pc), 0.85 + 0.15 * clamp(ease_out_back(pc, 1.3), 0, 1.3))
        swap = ease_in_out(prog(t, T_FLEX0, 0.25))
        cnt = ease_out_cubic(prog(t, ws(28), 0.62))
        if pc > 0 and swap < 1:
            a = al * (1 - swap)
            item(cv, txt("maosh", 46, TH.fg, "sb"), DC[0], DC[1] - 92, t, ws(27) - 0.05, a, yo, base=0.75)
            put(cv, txt(fmt(5000000 * cnt) if cnt >= 0.999 else qfmt(5000000 * cnt, 100000), 66, TH.acc), DC[0], DC[1] + yo - 2, a * clamp(prog(t, ws(28) - 0.05, 0.2)), 1.0)
            item(cv, txt("so‘m", 50, TH.fg, "sb"), DC[0], DC[1] + 86, t, ws(30) - 0.05, a, yo, base=0.85)
        if swap > 0:
            put(cv, person(150, TH.fg), DC[0], DC[1] - 20 + yo, al * swap, 0.8 + 0.2 * swap)
            put(cv, txt("sen", 54, TH.acc), DC[0], DC[1] + 96 + yo, al * swap, 1.0)
        # donut arcs
        sw = [ease_in_out(prog(t, T_S1, 0.95)), ease_in_out(prog(t, T_S2, 0.95)), ease_in_out(prog(t, T_S3, 0.75))]
        if any(x > 0 for x in sw):
            donut(cv, DC[0], DC[1] + yo, R, RTH, vals_at(t), COLS, sw, al)
        # stat cards
        amts = (2500000, 1500000, 1000000)
        starts = (T_S1, T_S2, T_S3)
        vs = vals_at(t)
        for i in range(3):
            t0 = starts[i] - 0.12
            if t < t0:
                continue
            cprog = ease_out_cubic(prog(t, starts[i], 0.9))
            if not flex:
                card = stat_card(f"{SH[i]}%", fmt(amts[i]) if cprog >= 0.999 else qfmt(amts[i] * cprog, 50000), COLS[i])
            else:
                card = stat_card(f"{int(round(vs[i]))}%", "", COLS[i])
            item(cv, card, CARD_X[i], CARD_Y, t, t0, al, yo, dur=0.32)

    # ------------------------------------------------------------- first save, then spend
    def sc_first(cv, t):
        v = vis(t, *W_FIRST)
        if not v: return
        al, yo = v
        item(cv, txt("Muhimi:", 58, TH.fg, "sb"), 540, 430, t, W_FIRST[0] + 0.02, al, yo, base=0.85)
        item(cv, txt2("avval ", "jamg‘arma,", 88, TH.fg, SAVE), 540, 530, t, ws(50) - 0.12, al, yo)
        item(cv, txt2("keyin ", "sarf", 88, TH.fg, TH.acc), 540, 635, t, ws(52) - 0.12, al, yo)
        pc = prog(t, W_FIRST[0] + 0.05, 0.4)
        # salary coin
        item(cv, coin(170, AMBER, mark="MAOSH"), 540, 810, t, W_FIRST[0], al, yo, dur=0.3)
        # jar (1) and bag (2)
        e1 = ease_out_cubic(prog(t, ws(49) + 0.1, 0.45))
        lvl = 0.10 + 0.45 * ease_in_out(prog(t, ws(50) + 0.45, 0.5))
        draw_jar(cv, 300, 1120 + yo + (1 - e1) * 60, lvl, SAVE, t, al * e1, 0.62)
        item(cv, disc(88, tuple(SAVE)), 300, 925, t, ws(50) - 0.1, al, yo, dur=0.3)
        item(cv, txt("1", 62, INK), 300, 925, t, ws(50) - 0.1, al, yo, dur=0.3)
        item(cv, txt("jamg‘arma", 50, SAVE), 300, 1330, t, ws(51) - 0.1, al, yo)
        e2 = ease_out_cubic(prog(t, ws(49) + 0.2, 0.45))
        bounce_b = 1 + 0.06 * math.sin(clamp((t - ws(52) - 0.5) / 0.35, 0, 1) * math.pi) if t > ws(52) + 0.5 else 1.0
        put(cv, bag(250, 290, AMBER, (214, 138, 0)), 790, 1130 + yo + (1 - e2) * 60, al * e2, bounce_b)
        item(cv, disc(88, tuple(TH.acc)), 790, 925, t, ws(52) - 0.1, al, yo, dur=0.3)
        item(cv, txt("2", 62, INK), 790, 925, t, ws(52) - 0.1, al, yo, dur=0.3)
        item(cv, txt("sarf", 50, TH.acc), 790, 1330, t, ws(53) - 0.1, al, yo)
        # coin -> jar (avval)
        fly(cv, coin(120, AMBER), (540, 810), (470, 1010), (300, 1030), t, ws(50), 0.62, al, yo, s_end=0.5)
        # coins -> bag (keyin)
        for i in range(3):
            fly(cv, coin(84, AMBER), (540, 810), (760 - 40 * i, 900), (790, 1050), t, ws(52) + 0.12 * i, 0.55, al, yo, s_end=0.55)
        ar = ease_out_cubic(prog(t, ws(52) - 0.05, 0.35))
        put(cv, arrow(130, 22, TH.fg), 545, 1215, al * ar * 0.85, 0.6 + 0.4 * ar)

    # ------------------------------------------------------------- "boshlash uchun shu yetarli"
    def sc_enough(cv, t):
        v = vis(t, *W_ENOUGH, fo=0.14)
        if not v: return
        al, yo = v
        item(cv, txt("Boshlash uchun", 88), 540, 500, t, W_ENOUGH[0] + 0.02, al, yo)
        item(cv, txt("shu yetarli.", 124, TH.acc), 540, 640, t, ws(56) - 0.15, al, yo, dur=0.34)
        cp = prog(t, ws(55), 0.5)
        if cp > 0:
            put(cv, disc(330, tuple(TH.card), tuple(GREEN), 10), 540, 1000 + yo, al * ease_out_cubic(cp), 0.8 + 0.2 * clamp(ease_out_back(cp, 1.4), 0, 1.3))
            put(cv, check(190, GREEN, 30), 540, 1000 + yo, al * ease_out_cubic(prog(t, ws(55) + 0.1, 0.35)), 0.5 + 0.5 * clamp(ease_out_back(prog(t, ws(55) + 0.1, 0.5), 1.8), 0, 1.4))
        sp = prog(t, ws(57) - 0.25, 0.35)
        if sp > 0:
            put(cv, chip("BOSHLANG‘ICH NUQTA", TH.acc, INK, 46), 540, 1280 + yo, al * ease_out_cubic(sp), 0.8 + 0.2 * clamp(ease_out_back(sp, 1.6), 0, 1.4), 4)

    # ------------------------------------------------------------- CTA: bookmark + calendar
    def sc_cta(cv, t):
        v = vis(t, *W_CTA, fo=0.25)
        if not v: return
        al, yo = v
        item(cv, txt("Saqlab qo‘y", 120), 540, 470, t, ws(58) - 0.15, al, yo, dur=0.34)
        item(cv, txt2("maosh kuni ", "qayta ko‘r", 80, TH.fg, TH.acc), 540, 600, t, ws(61) - 0.12, al, yo)
        CX, CY = 540, 1080
        ce = ease_out_cubic(prog(t, W_CTA[0] + 0.05, 0.45))
        put(cv, calendar(), CX, CY + yo + (1 - ce) * 70, al * ce, 0.92 + 0.08 * ce)
        hx, hy = cal_cell_center(CX, CY)
        cell_p = prog(t, ws(61) - 0.1, 0.4)
        if cell_p > 0:
            put(cv, rrect(CAL_CELL, CAL_CELL, 18, tuple(AMBER)), hx, hy + yo, al * ease_out_cubic(cell_p), 0.8 + 0.2 * ease_out_cubic(cell_p))
            put(cv, coin(60, AMBER, (214, 138, 0)), hx, hy + yo, al * ease_out_cubic(cell_p), 0.8 + 0.2 * ease_out_cubic(cell_p))
        rp = prog(t, ws(62), 0.5)
        if rp > 0:
            ring = [(hx + 64 * math.cos(math.radians(-90 + 360 * i / 40)), hy + yo + 64 * math.sin(math.radians(-90 + 360 * i / 40))) for i in range(41)]
            poly(cv, ring, RED, 9, ease_in_out(rp), al)
        for k in range(2):
            pp = (t - ws(63) - k * 0.35) / 0.9
            if 0 < pp < 1:
                put(cv, disc(int(110 + 160 * pp), None, tuple(RED), 5), hx, hy + yo, al * 0.7 * (1 - pp))
        # bookmark drops in at "qo'y" and bounces into place
        bp = prog(t, ws(59) - 0.05, 0.75)
        if bp > 0:
            y = lerp(520, 800, bounce(bp))
            put(cv, bookmark(110, 160, RED), 772, y + yo, al * ease_out_cubic(clamp(bp * 4)), 1.0, 3)

    scenes = [sc_hook, sc_bar, sc_rule, sc_need, sc_want, sc_save, sc_donut, sc_first, sc_enough, sc_cta]
    return Reel(tim, scenes, theme="slate", bg="flat", overlay_kind="grid",
                disclaimer="Bu umumiy ma‘lumot, shaxsiy maslahat emas.")
