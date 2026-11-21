"""Day 15 - Imkoniyat narxi (Iqtisod).  Look: ink theme, radial gradient, diag overlay.
Visual metaphor: vaqt (soat) ikki yo'lga ajraladi (A: serial, B: yangi ko'nikma). Tanlangan yo'l yorishadi,
tanlanmagan yo'l xira bo'lib qoladi - o'sha xira yo'l = "imkoniyat narxi". Soat va tanga ikonkalari.
Animated explainer (objects move and transform with the words) - NOT text-only."""
import math
from functools import lru_cache

from PIL import ImageChops

from nt_kit import *

INKCARD = (32, 36, 60)
EDGE = (92, 100, 142)
PATHN = (150, 160, 196)
CARD_W, CARD_H = 392, 380
CA, CB = (286, 1255), (794, 1255)          # card centres (A = serial, B = yangi ko'nikma)
NODE = (540, 850)                           # the "2 soat" clock where the road forks
L1, L2, L3 = 470, 580, 690                  # top text lines


# ----------------------------------------------------------------------------- helpers
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
        if total <= 820 or size <= 40:
            break
        size -= 4
    x = 540 - total / 2
    for l, w, t0 in zip(layers, widths, times):
        item(cv, l, x + w / 2, y, t, t0, al, yo, dur=dur)
        x += w + gap


def bez(p0, p1, p2, p3, n=48):
    out = []
    for i in range(n + 1):
        s = i / n
        a, b, c, d = (1 - s) ** 3, 3 * (1 - s) ** 2 * s, 3 * (1 - s) * s * s, s ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def along(pts, p):
    f = clamp(p) * (len(pts) - 1)
    i = min(int(f), len(pts) - 2)
    q = f - i
    return (lerp(pts[i][0], pts[i + 1][0], q), lerp(pts[i][1], pts[i + 1][1], q))


PATH_A = bez((540, 925), (540, 1000), (286, 990), (286, 1066))
PATH_B = bez((540, 925), (540, 1000), (794, 990), (794, 1066))
TOKEN_PATH = [(540, 850), (540, 890)] + PATH_A


def pulse(cv, cx, cy, d, t, t0, col=AMBER, dur=0.8, al=1.0, ow=8):
    p = (t - t0) / dur
    if p <= 0 or p >= 1:
        return
    put(cv, disc(d, None, col, ow), cx, cy, al * (1 - p) * 0.9, 0.75 + 0.5 * ease_out_cubic(p))


# ----------------------------------------------------------------------------- local icons (PIL)
@lru_cache(None)
def clock_face(d):
    s = 3
    D = d * s
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.ellipse([0, 0, D - 1, D - 1], fill=AMBER + (255,))
    dr.ellipse([D * .045, D * .045, D * .955, D * .955], fill=CREAM + (255,))
    for i in range(12):
        a = math.radians(i * 30)
        big = i % 3 == 0
        r0, r1 = (D * .38, D * .45) if big else (D * .42, D * .45)
        w = max(2, int(D * (.024 if big else .013)))
        dr.line([(D / 2 + r0 * math.sin(a), D / 2 - r0 * math.cos(a)), (D / 2 + r1 * math.sin(a), D / 2 - r1 * math.cos(a))],
                fill=NAVY + (255,), width=w)
    return im.resize((d, d), Image.LANCZOS)


def clock_layer(d, hour_deg, min_deg, wedge=None):
    """analog clock; angles in degrees clockwise from 12; wedge=(a0,a1) paints the span between (the 'spent' hours)"""
    base = clock_face(d).copy()
    s = 2
    D = d * s
    ov = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    if wedge and wedge[1] - wedge[0] > 0.8:
        dr.pieslice([D * .10, D * .10, D * .90, D * .90], wedge[0] - 90, wedge[1] - 90, fill=(255, 150, 20, 175))
    c = D / 2

    def hand(deg, L, wd, col):
        a = math.radians(deg)
        x1, y1 = c + L * math.sin(a), c - L * math.cos(a)
        x0, y0 = c - L * .14 * math.sin(a), c + L * .14 * math.cos(a)
        dr.line([(x0, y0), (x1, y1)], fill=col, width=int(wd))
        for qx, qy in ((x0, y0), (x1, y1)):
            dr.ellipse([qx - wd / 2, qy - wd / 2, qx + wd / 2, qy + wd / 2], fill=col)

    hand(hour_deg, D * .27, max(3, D * .040), NAVY + (255,))
    hand(min_deg, D * .385, max(2, D * .026), NAVY + (255,))
    r = D * .035
    dr.ellipse([c - r, c - r, c + r, c + r], fill=(222, 128, 0, 255))
    base.alpha_composite(ov.resize((d, d), Image.LANCZOS))
    return base


@lru_cache(None)
def moon(d, col=(255, 232, 160)):
    s = 4
    D = d * s
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([0, 0, D - 1, D - 1], fill=col + (255,))
    cut = Image.new("L", (D, D), 0)
    ImageDraw.Draw(cut).ellipse([D * .32, -D * .06, D * 1.12, D * .76], fill=255)
    im.putalpha(ImageChops.subtract(im.getchannel("A"), cut))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def sparkle(d, col=AMBER):
    s = 4
    D = d * s
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    P = [(D / 2, 0), (D * .58, D * .42), (D, D / 2), (D * .58, D * .58), (D / 2, D), (D * .42, D * .58), (0, D / 2), (D * .42, D * .42)]
    ImageDraw.Draw(im).polygon(P, fill=tuple(col) + (255,))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def tv(w):
    h = int(w * 0.84)
    s = 4
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    fr = (214, 220, 236, 255)
    bh = h * 0.80
    dr.rounded_rectangle([0, 0, w * s - 1, bh * s], radius=int(w * .10 * s), fill=fr)
    dr.rounded_rectangle([w * .06 * s, w * .06 * s, w * .94 * s, (bh - w * .06) * s], radius=int(w * .06 * s), fill=(30, 52, 108, 255))
    dr.polygon([(w * .40 * s, bh * s), (w * .60 * s, bh * s), (w * .66 * s, h * .92 * s), (w * .34 * s, h * .92 * s)], fill=fr)
    dr.rounded_rectangle([w * .26 * s, h * .90 * s, w * .74 * s, (h - 1) * s], radius=int(w * .03 * s), fill=fr)
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def play(d, col=AMBER):
    s = 4
    D = d * s
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    ImageDraw.Draw(im).polygon([(D * .22, D * .08), (D * .22, D * .92), (D * .94, D * .5)], fill=tuple(col) + (255,))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def book(w):
    h = int(w * 0.72)
    s = 4
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    P = lambda x, y: (x * w * s, y * h * s)
    dr.polygon([P(0.0, 0.10), P(0.5, 0.24), P(1.0, 0.10), P(1.0, 0.90), P(0.5, 1.0), P(0.0, 0.90)], fill=(206, 126, 0, 255))
    dr.polygon([P(0.04, 0.06), P(0.5, 0.20), P(0.5, 0.92), P(0.04, 0.78)], fill=(247, 243, 234, 255))
    dr.polygon([P(0.96, 0.06), P(0.5, 0.20), P(0.5, 0.92), P(0.96, 0.78)], fill=(234, 227, 210, 255))
    for k in range(4):
        dr.line([P(0.10, 0.20 + k * .12), P(0.44, 0.303 + k * .12)], fill=(150, 140, 120, 255), width=int(w * .016 * s))
        dr.line([P(0.56, 0.303 + k * .12), P(0.90, 0.20 + k * .12)], fill=(150, 140, 120, 255), width=int(w * .016 * s))
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def bookmark(w, h, col):
    s = 4
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).polygon([(0, 0), (w * s, 0), (w * s, h * s), (w * s / 2, h * .78 * s), (0, h * s)], fill=tuple(col) + (255,))
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def pause_badge(d):
    s = 4
    D = d * s
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.ellipse([0, 0, D - 1, D - 1], fill=AMBER + (255,))
    for x0 in (0.31, 0.54):
        dr.rounded_rectangle([D * x0, D * 0.27, D * (x0 + 0.15), D * 0.73], radius=int(D * 0.04), fill=NAVY + (255,))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def ring_rect(w, h, r, col, ow):
    s = 2
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=r * s, outline=tuple(col) + (255,), width=ow * s)
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def bubble(w, h, fill, outline, tail_h=44):
    """speech bubble with a tail pointing UP from the top centre; layer height = h + tail_h"""
    s = 2
    H2 = h + tail_h
    im = Image.new("RGBA", (w * s, H2 * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle([2 * s, tail_h * s, (w - 2) * s, (H2 - 2) * s], radius=48 * s, fill=tuple(fill) + (255,), outline=tuple(outline) + (255,), width=4 * s)
    cx = w / 2
    dr.polygon([((cx - 38) * s, (tail_h + 8) * s), (cx * s, 3 * s), ((cx + 38) * s, (tail_h + 8) * s)], fill=tuple(fill) + (255,))
    dr.line([((cx - 38) * s, (tail_h + 3) * s), (cx * s, 3 * s), ((cx + 38) * s, (tail_h + 3) * s)], fill=tuple(outline) + (255,), width=4 * s, joint="curve")
    return im.resize((w, H2), Image.LANCZOS)


@lru_cache(None)
def qbubble(d):
    """thought bubble with a '?'; the little tail dots point down-left"""
    im = Image.new("RGBA", (d + 50, d + 70), (0, 0, 0, 0))
    im.alpha_composite(disc(d, CREAM), (50, 0))
    im.alpha_composite(disc(int(d * .17), CREAM), (24, int(d * .93)))
    im.alpha_composite(disc(int(d * .10), CREAM), (2, int(d * 1.10)))
    q = txt("?", int(d * .70), NAVY)
    im.alpha_composite(q, (50 + (d - q.width) // 2, (d - q.height) // 2 - 2))
    return im


def build(tim):
    S, E, ws, we = tim.S, tim.E, tim.ws, tim.we
    END0 = tim.end0
    W_H = (0.0, S("soat2") - 0.10)
    W_F = (W_H[1] - 0.08, S("ask") - 0.10)
    W_A = (W_F[1] - 0.08, S("cta") - 0.10)
    W_C = (W_A[1] - 0.08, END0)
    tP = ws(20)

    def line(cv, layer, y, t, t0, t1, al, yo, dur=0.3, fo=0.1):
        """a text line shown between t0 and t1 (entrance at t0, short fade before t1)"""
        if t < t0 or t >= t1:
            return
        item(cv, layer, 540, y, t, t0, al * clamp((t1 - t) / fo), yo, dur=dur)

    # ------------------------------------------------------------------ hook: free coin + a clock that starts ticking
    def sc_hook(cv, t):
        v = vis(t, *W_H)
        if not v: return
        al, yo = v
        item(cv, txt("Bepul narsaning", 104), 540, 490, t, -0.12, al, yo)
        item(cv, txt2("ham ", "narxi bor.", 104, TH.fg, TH.acc), 540, 612, t, ws(2) - 0.15, al, yo)
        t3 = ws(3) - 0.05
        k = ease_in_out(prog(t, t3, 0.5))
        p0 = prog(t, -0.1, 0.5)
        shake = 6 * math.sin(t * 38) * (1 - k) * clamp(prog(t, 0.45, 0.1))
        put(cv, coin(400, AMBER, mark="0"), lerp(540, 350, k) + shake, 1090 + yo, al * ease_out_cubic(p0),
            (0.85 + 0.15 * clamp(ease_out_back(p0, 1.3), 0, 1.3)) * lerp(1.0, 0.80, k))
        put(cv, txt("bepul", 54, TH.acc, "sb"), lerp(540, 350, k), 1330 + yo, al * ease_out_cubic(prog(t, 0.3, 0.3)) * (1 - 0.3 * k))
        pc = prog(t, t3, 0.45)
        if pc > 0:
            ch = (t - t3)
            hd = 210 + ch * 70
            put(cv, clock_layer(340, hd, (hd - 210) * 12), 745, 1090 + yo, al * ease_out_cubic(pc), 0.8 + 0.2 * clamp(ease_out_back(pc, 1.5), 0, 1.4))
            pulse(cv, 745, 1090 + yo, 340, t, t3 + 0.05, AMBER, 0.5, al)
            put(cv, txt("vaqt", 54, TH.acc, "sb"), 745, 1330 + yo, al * ease_out_cubic(prog(t, t3 + 0.25, 0.3)))

    # ------------------------------------------------------------------ the fork: 2 hours -> A / B -> choose -> the dim road is the price
    def sc_fork(cv, t):
        v = vis(t, *W_F)
        if not v: return
        al, yo = v
        tA, tV, tN0, tN1 = ws(9), ws(11), ws(12), ws(13)
        tB, tBy, tBk, tBo = ws(15), ws(17), ws(18), ws(19)
        tTan, tIkk, tVoz, tKech = ws(21), ws(22), ws(23), ws(24)
        tIq, tImk, tNarx, tDeydi = ws(25), ws(27), ws(28), ws(29)
        tKq, t2 = ws(5), ws(6)

        # --- top text lines
        line(cv, txt("Kechqurun", 100), L1, t, tKq - 0.05, tA - 0.18, al, yo)
        line(cv, txt2("2 ", "soating bor.", 104, TH.acc, TH.fg), L2, t, t2 - 0.12, tA - 0.18, al, yo)
        line(cv, txt("A variant:", 70, TH.fg, "sb"), L1, t, tA, tN0 - 0.02, al, yo)
        line(cv, txt("serial", 124, TH.acc), L2, t, tV - 0.04, tN0 - 0.02, al, yo)
        line(cv, txt("Narxi:", 70, TH.fg, "sb"), L1, t, tN0, tB - 0.02, al, yo)
        line(cv, txt("0 so‘m", 124, TH.acc), L2, t, tN1 - 0.06, tB - 0.02, al, yo)
        line(cv, txt("B variant:", 70, TH.fg, "sb"), L1, t, tB, tP - 0.02, al, yo)
        line(cv, txt("yangi ko‘nikmani", 96, TH.acc), L2, t, tBy - 0.05, tP - 0.02, al, yo)
        line(cv, txt("o‘rganish", 96, TH.fg), L3, t, tBo - 0.05, tP - 0.02, al, yo)
        line(cv, txt("Birini tanlasang,", 64, TH.fg, "sb"), L1, t, tP, tIq - 0.02, al, yo)
        line(cv, txt("ikkinchisidan", 92, TH.fg), L2, t, tIkk - 0.05, tIq - 0.02, al, yo)
        line(cv, txt("voz kechasan", 92, TH.acc), L3, t, tVoz - 0.05, tIq - 0.02, al, yo)
        line(cv, txt("Iqtisodchilar buni", 60, TH.fg, "sb"), L1, t, tIq, 99, al, yo)
        line(cv, txt("imkoniyat narxi", 104, TH.acc, "xb", 900), L2, t, tImk - 0.1, 99, al, yo, dur=0.34)
        line(cv, txt("deydi.", 72, TH.fg, "sb"), L3, t, tDeydi - 0.05, 99, al, yo)

        # --- states
        mv = prog(t, tTan, 0.75)                                         # token travelling down road A
        chosen = ease_in_out(prog(t, tTan + 0.3, 0.5))
        dimB = ease_in_out(prog(t, tVoz - 0.05, 0.55))
        node_a = 1 - 0.45 * ease_in_out(prog(t, tTan + 0.7, 0.4))

        # --- the two roads
        pa = ease_in_out(prog(t, tA + 0.05, 0.55))
        pb = ease_in_out(prog(t, tB + 0.05, 0.55))
        ptsA = [(x, y + yo) for x, y in PATH_A]
        ptsB = [(x, y + yo) for x, y in PATH_B]
        if pa > 0:
            col = mixc(PATHN, AMBER, chosen)
            if chosen > 0.02:
                poly(cv, ptsA, AMBER, 52, pa, al * chosen * 0.13)
                poly(cv, ptsA, AMBER, 34, pa, al * chosen * 0.22)
            poly(cv, ptsA, col, 14 + 6 * chosen, pa, al)
        if pb > 0:
            col = mixc(PATHN, (62, 68, 100), dimB)
            poly(cv, ptsB, col, 14, pb, al * (1 - 0.5 * dimB))

        # --- cards
        def card(cx, cy, letter, t0, dim, kind, t_icon):
            e = ease_out_cubic(prog(t, t0, 0.42))
            if e <= 0: return
            ga = al * e * (1 - 0.72 * dim)
            y0 = cy + yo + (1 - e) * 60
            put(cv, rrect(CARD_W, CARD_H, 44, INKCARD, EDGE, 4), cx, y0, ga)
            pc = prog(t, t0, 0.36)
            put(cv, disc(86, AMBER), cx - 150, y0 - 150, ga * ease_out_cubic(pc), 0.8 + 0.2 * clamp(ease_out_back(pc, 1.6), 0, 1.4))
            put(cv, txt(letter, 56, NAVY), cx - 150, y0 - 150, ga * ease_out_cubic(pc))
            pi = prog(t, t_icon, 0.4)
            sc = 0.8 + 0.2 * clamp(ease_out_back(pi, 1.5), 0, 1.4)
            if kind == "tv":
                put(cv, tv(220), cx, y0 - 45, ga * ease_out_cubic(clamp(prog(t, t0 + 0.1, 0.3))))
                if pi > 0:
                    glow = 0.75 + 0.25 * math.sin(t * 6)
                    put(cv, disc(120, AMBER), cx + 4, y0 - 64, ga * ease_out_cubic(pi) * 0.18 * glow, sc * 1.1)
                    put(cv, play(76, AMBER), cx + 6, y0 - 64, ga * ease_out_cubic(pi), sc)
            else:
                put(cv, book(230), cx, y0 - 40, ga * ease_out_cubic(clamp(prog(t, t_icon - 0.1, 0.4))), 0.85 + 0.15 * ease_out_cubic(pi))
                for dx, dy, dt, d in ((-110, -118, 0.10, 46), (118, -108, 0.25, 36), (92, 14, 0.40, 30)):
                    pp = prog(t, t_icon + dt, 0.3)
                    if pp > 0:
                        put(cv, sparkle(d, AMBER), cx + dx, y0 + dy, ga * ease_out_cubic(pp) * (0.7 + 0.3 * math.sin(t * 8 + dx)),
                            (0.6 + 0.4 * clamp(ease_out_back(pp, 1.8), 0, 1.5)) * (0.9 + 0.1 * math.sin(t * 8 + dx)))
            return ga, y0

        pg = prog(t, tA + 0.45, 0.5)
        if pg > 0 and t < tB + 0.45:
            gb = ease_out_cubic(pg) * 0.38 * (1 - ease_out_cubic(prog(t, tB + 0.2, 0.25)))
            put(cv, ring_rect(CARD_W, CARD_H, 44, EDGE, 4), CB[0], CB[1] + yo, al * gb)
            put(cv, txt("?", 170, EDGE), CB[0], CB[1] + yo, al * gb * 0.9, 0.9 + 0.05 * math.sin(t * 4))
        card(CA[0], CA[1], "A", tA + 0.2, 0.0, "tv", tV)
        card(CB[0], CB[1], "B", tB + 0.2, dimB, "book", tBk)

        # price tag "0 so'm" dropped onto card A
        pp = prog(t, tN1 - 0.05, 0.5)
        if pp > 0:
            put(cv, pricetag(300, 110, CREAM, NAVY, "0 so‘m", NAVY, 46), CA[0], CA[1] + 120 + yo - (1 - bounce(pp)) * 90, al * clamp(pp * 5))

        # chosen: highlight ring around card A + the "2 soat" chip lands on it
        if chosen > 0.01:
            y0 = CA[1] + yo
            put(cv, ring_rect(CARD_W + 8, CARD_H + 8, 48, AMBER, 7), CA[0], y0, al * chosen)
            put(cv, ring_rect(CARD_W + 28, CARD_H + 28, 58, AMBER, 6), CA[0], y0, al * chosen * (0.20 + 0.10 * math.sin(t * 7)))
        pcp = prog(t, tTan + 0.85, 0.35)
        if pcp > 0:
            pop(cv, chip("2 soat", AMBER, NAVY, 36), CA[0] + 112, CA[1] - 190 + yo, t, tTan + 0.85, al, 0, dur=0.35, rise=16)

        # unchosen: cross + the amber "narx" ring and tag (the price!)
        if t >= tVoz + 0.15:
            pcx = prog(t, tVoz + 0.15, 0.35)
            put(cv, cross(150, RED, 22), CB[0], CB[1] + yo, al * ease_out_cubic(pcx) * (1 - 0.35 * prog(t, tIq, 0.4)), 0.8 + 0.2 * clamp(ease_out_back(pcx, 1.6), 0, 1.4))
        pr = prog(t, tImk - 0.05, 0.4)
        if pr > 0:
            yb = CB[1] + yo
            put(cv, ring_rect(CARD_W + 8, CARD_H + 8, 48, RED, 7), CB[0], yb, al * ease_out_cubic(pr) * (0.80 + 0.20 * math.sin(t * 7)))
            put(cv, ring_rect(CARD_W + 28, CARD_H + 28, 58, RED, 6), CB[0], yb, al * ease_out_cubic(pr) * (0.20 + 0.10 * math.sin(t * 7)))
        pop(cv, pricetag(224, 92, AMBER, NAVY, "narx", NAVY, 50), CB[0] + 76, CB[1] - 194 + yo, t, tNarx - 0.05, al, 0, dur=0.38, rot=-9, rise=30, s0=0.7)

        # --- the clock node (big at first, then shrinks into the fork)
        m = ease_in_out(prog(t, tA - 0.22, 0.42))
        dc = int(lerp(520, 150, m))
        ccy = lerp(1010, NODE[1], m)
        ps = prog(t, W_F[0] + 0.02, 0.4)
        hd = 210 + 60 * ease_in_out(prog(t, t2 - 0.05, 0.75))
        md = (hd - 210) * 12
        if ps > 0:
            put(cv, clock_layer(dc, hd, md, (210, hd)), 540, ccy + yo, al * ease_out_cubic(ps) * node_a,
                0.85 + 0.15 * clamp(ease_out_back(ps, 1.3), 0, 1.3))
        # moon for "kechqurun"
        pm = prog(t, tKq, 0.4)
        if pm > 0 and t < tA - 0.1:
            put(cv, moon(140), 820, 800 + yo, al * ease_out_cubic(pm) * clamp((tA - 0.1 - t) / 0.12), 0.8 + 0.2 * clamp(ease_out_back(pm, 1.5), 0, 1.4), -10)
            for dx, dy, dt, d in ((905, 745, 0.15, 34), (745, 735, 0.3, 26), (915, 850, 0.4, 24)):
                pp2 = prog(t, tKq + dt, 0.3)
                if pp2 > 0:
                    put(cv, sparkle(d, (255, 232, 160)), dx, dy + yo, al * ease_out_cubic(pp2) * (0.7 + 0.3 * math.sin(t * 9 + dx)) * clamp((tA - 0.1 - t) / 0.12))
        # label next to the node
        item(cv, txt("2 soat", 58, TH.acc, "xb"), 720, NODE[1], t, tA + 0.1, al * node_a, yo, dur=0.3)

        # --- the token that chooses road A
        tk_in = ease_out_cubic(prog(t, tP, 0.3))
        if tk_in > 0:
            fade = 1 - ease_out_cubic(prog(t, tTan + 0.78, 0.25))
            px, py = along(TOKEN_PATH, ease_in_out(mv))
            sc = 0.75 + 0.25 * clamp(ease_out_back(prog(t, tP, 0.3), 1.6), 0, 1.4)
            put(cv, disc(150, AMBER), px, py + yo, al * 0.20 * tk_in * fade, sc)
            put(cv, disc(100, AMBER), px, py + yo, al * tk_in * fade, sc)
            put(cv, person(56, NAVY), px, py + yo + 4, al * tk_in * fade, sc)

    # ------------------------------------------------------------------ "Vaqt sarflashdan oldin so'ra: ..."
    def sc_ask(cv, t):
        v = vis(t, *W_A)
        if not v: return
        al, yo = v
        tV, tOld, tSora = ws(30), ws(32), ws(33)
        tBu, tEv, tNim, tVoz, tKech = ws(34), ws(35), ws(36), ws(37), ws(38)
        t_sw = tBu - 0.34
        line(cv, txt("Vaqt sarflashdan", 88), L1, t, tV, t_sw, al, yo)
        line(cv, txt("oldin so‘ra:", 100, TH.acc), L2, t, tOld - 0.05, t_sw, al, yo)

        m = ease_in_out(prog(t, tBu - 0.38, 0.37))
        d = int(lerp(420, 190, m))
        cx, cy = 540, lerp(960, 520, m)
        ps = prog(t, W_A[0] + 0.02, 0.4)
        ta = tSora - 0.25
        md = 600 * (min(t, ta) - W_A[0]) + 70 * ease_out_cubic(prog(t, ta, 0.35))
        hd = 210 + md / 12
        if ps > 0:
            put(cv, clock_layer(d, hd, md, (210, hd)), cx, cy + yo, al * ease_out_cubic(ps), 0.85 + 0.15 * clamp(ease_out_back(ps, 1.3), 0, 1.3))
            pulse(cv, cx, cy + yo, d, t, tSora, AMBER, 0.8, al)
            pb = prog(t, tSora, 0.35)
            if pb > 0:
                bd = int(d * 0.30)
                put(cv, pause_badge(bd), cx + d * 0.36, cy - d * 0.36 + yo, al * ease_out_cubic(pb), 0.7 + 0.3 * clamp(ease_out_back(pb, 1.8), 0, 1.5))

        # the question bubble
        pq = prog(t, tBu - 0.05, 0.4)
        if pq > 0:
            put(cv, bubble(900, 400, INKCARD, AMBER), 540, 862 + yo + (1 - ease_out_cubic(pq)) * 40, al * ease_out_cubic(pq))
            item(cv, txt("Buning evaziga", 78, TH.fg, "xb", 820), 540, 770, t, tBu, al, yo, dur=0.3)
            words_line(cv, ["nimadan", "voz"], 78, 872, [tNim, tVoz], t, al, yo, col=None, gap=24)
            item(cv, txt("kechayapman?", 82, TH.acc, "xb", 820), 540, 974, t, tKech - 0.05, al, yo, dur=0.3)
        # the things you would give up
        for x0, kind, t0 in ((390, "tv", tNim), (690, "book", tNim + 0.12)):
            pg = prog(t, t0, 0.4)
            if pg <= 0: continue
            sl = ease_in_out(prog(t, tVoz, 0.5))
            x = x0 + (-34 if x0 < 540 else 34) * sl
            a = al * ease_out_cubic(pg) * (1 - 0.55 * sl)
            put(cv, disc(250, None, (84, 92, 136), 5), x, 1275 + yo, a * 0.9, 0.85 + 0.15 * ease_out_cubic(pg))
            if kind == "tv":
                put(cv, tv(130), x, 1285 + yo, a, 0.85 + 0.15 * ease_out_cubic(pg))
                put(cv, play(44, AMBER), x + 4, 1272 + yo, a, 0.85 + 0.15 * ease_out_cubic(pg))
            else:
                put(cv, book(150), x, 1280 + yo, a, 0.85 + 0.15 * ease_out_cubic(pg))
        pqq = prog(t, tKech, 0.4)
        if pqq > 0:
            put(cv, txt("?", 150, TH.acc), 540, 1270 + yo, al * ease_out_cubic(pqq), 0.7 + 0.3 * clamp(ease_out_back(pqq, 1.8), 0, 1.5))

    # ------------------------------------------------------------------ CTA: save + tonight + ask yourself
    def sc_cta(cv, t):
        v = vis(t, *W_C, fo=0.25)
        if not v: return
        al, yo = v
        tS, tQ, tVa, tBug, tKe, tOz, tSo = ws(39), ws(40), ws(41), ws(42), ws(43), ws(44), ws(45)
        item(cv, txt("Saqlab qo‘y", 128, TH.acc), 540, L1, t, tS, al, yo, dur=0.34)
        words_line(cv, ["bugun", "kechqurun"], 80, L2 + 6, [tBug, tKe], t, al, yo, col=None, gap=26)

        # bookmark drops in, gets ticked, then steps aside
        mb = ease_in_out(prog(t, tVa + 0.05, 0.4))
        pbk = prog(t, tS, 0.5)
        if pbk > 0:
            bx, by = lerp(540, 255, mb), lerp(915, 940, mb)
            sc = lerp(1.0, 0.72, mb)
            drop = (1 - bounce(pbk)) * -260
            put(cv, bookmark(210, 300, AMBER), bx, by + yo + drop, al * clamp(pbk * 5), sc)
            pk = prog(t, tQ, 0.35)
            if pk > 0:
                put(cv, check(100, NAVY, 18), bx, by - 40 + yo, al * ease_out_cubic(pk), sc * (0.6 + 0.4 * clamp(ease_out_back(pk, 1.8), 0, 1.5)))
            pulse(cv, bx, by + yo, 300, t, tQ, AMBER, 0.7, al)
        # tonight: clock at 7 pm + moon
        pc = prog(t, tBug, 0.45)
        if pc > 0:
            put(cv, clock_layer(250, 210 + 60, 0, (210, 270)), 540, 940 + yo, al * ease_out_cubic(pc), 0.8 + 0.2 * clamp(ease_out_back(pc, 1.5), 0, 1.4))
        pmn = prog(t, tKe, 0.4)
        if pmn > 0:
            put(cv, moon(190), 835, 925 + yo, al * ease_out_cubic(pmn), 0.8 + 0.2 * clamp(ease_out_back(pmn, 1.5), 0, 1.4), -10)
            for dx, dy, dt, dd in ((925, 840, 0.15, 34), (780, 830, 0.3, 26), (940, 975, 0.4, 24)):
                pp2 = prog(t, tKe + dt, 0.3)
                if pp2 > 0:
                    put(cv, sparkle(dd, (255, 232, 160)), dx, dy + yo, al * ease_out_cubic(pp2) * (0.7 + 0.3 * math.sin(t * 9 + dx)))
        # ask yourself
        pf = prog(t, tOz, 0.45)
        if pf > 0:
            put(cv, face(190, "neutral", AMBER), 470, 1190 + yo, al * ease_out_cubic(pf), 0.8 + 0.2 * clamp(ease_out_back(pf, 1.5), 0, 1.4))
            pq = prog(t, tOz + 0.2, 0.45)
            if pq > 0:
                bob = 6 * math.sin(t * 5)
                put(cv, qbubble(140), 690, 1140 + yo + bob, al * ease_out_cubic(pq), 0.7 + 0.3 * clamp(ease_out_back(pq, 1.6), 0, 1.5))
            item(cv, txt("o‘zingdan so‘ra.", 96, TH.acc), 540, 1372, t, tOz, al, yo, dur=0.34)

    # ------------------------------------------------------------------ tags: MISOL (the 2 hours are an example) -> Soddalashtirib aytganda
    def sc_tags(cv, t):
        for a, b, text, bg, fg in ((ws(5) - 0.05, tP - 0.10, "MISOL", AMBER, NAVY),
                                   (tP - 0.05, W_F[1], "Soddalashtirib aytganda", CREAM, NAVY)):
            if a <= t < b:
                al = clamp((b - t) / 0.15)
                pop(cv, chip(text, bg, fg, 32), 540, 392, t, a, al, 0, dur=0.3, rise=14)

    return Reel(tim, [sc_hook, sc_fork, sc_ask, sc_cta, sc_tags], theme="ink", bg="radial", overlay_kind="diag")
