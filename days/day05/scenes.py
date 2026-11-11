"""Day 5 - "Qimmat" e'tirozi (kichik biznes).  Look: ink theme, spot background, rings overlay.
Visual metaphor: mijoz va sotuvchi dialogi (nutq pufakchalari), narx yorlig'i tushmaydi, qiymat belgilari bir-bir paydo bo'ladi,
kichik tarif qutisi mijozga uzatiladi, oxirida natija (yashil belgi + o'suvchi strelka).
Animated explainer (objects move and transform with the words) - NOT text-only."""
import math
from functools import lru_cache

from nt_kit import *

MUTL = (160, 168, 196)          # light muted text colour that reads on the dark ink theme
SKY = (118, 204, 255)
HOLE = (16, 18, 32)
CARTON, CARTON_D = (226, 172, 98), (170, 116, 52)


# ----------------------------------------------------------------------------- local helpers / icons
def pop(cv, layer, cx, cy, t, t0, al=1.0, yo=0.0, dur=0.35, rot=0.0, base=1.0, rise=30, s0=0.85):
    """entrance like nt_kit.item, but with rotation"""
    p = (t - t0) / dur
    if p <= 0:
        return
    e = ease_out_cubic(p)
    sc = s0 + (1 - s0) * clamp(ease_out_back(p, 1.3), 0, 1.25)
    put(cv, layer, cx, cy + yo + (1 - e) * rise, al * e * base, sc, rot)


def chip(text, bg, fg=NAVY, size=40, maxw=700):
    t = txt(text, size, fg, "xb", maxw=maxw)
    w, h = t.width + 56, t.height + 14
    base = rrect(w, h, h // 2, tuple(bg)).copy()
    base.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2))
    return base


@lru_cache(None)
def bubble(text, size, fill, tcol, side="l", maxw=700):
    """speech bubble with a tail (tip at 7% / 93% of the width, bottom edge)"""
    t = txt(text, size, tcol, "xb", maxw=maxw)
    w, h = t.width + 70, t.height + 34
    tail, s = 46, 3
    im = Image.new("RGBA", (w * s, (h + tail) * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    col = tuple(fill) + (255,)
    dr.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=int(h * 0.42 * s), fill=col)
    pts = [(w * .12, h - 4), (w * .30, h - 4), (w * .07, h + tail)] if side == "l" else [(w * .70, h - 4), (w * .88, h - 4), (w * .93, h + tail)]
    dr.polygon([(x * s, y * s) for x, y in pts], fill=col)
    im = im.resize((w, h + tail), Image.LANCZOS)
    im.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2))
    return im


def say(cv, layer, tip, side, t, t0, al, yo, dur=0.32):
    """place a bubble so its tail tip sits on `tip`"""
    w, h = layer.size
    fx = 0.07 if side == "l" else 0.93
    item(cv, layer, tip[0] - fx * w + w / 2, tip[1] - h / 2, t, t0, al, yo, dur=dur, rise=20)


@lru_cache(None)
def gem(d, col=SKY):
    s = 4
    im = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    P = lambda x, y: (x * d * s, y * d * s)
    light = tuple(min(255, c + 70) for c in col)
    dark = tuple(max(0, c - 55) for c in col)
    dr.polygon([P(.22, .12), P(.78, .12), P(1.0, .40), P(.5, .96), P(0, .40)], fill=tuple(col) + (255,))
    dr.polygon([P(.22, .12), P(.78, .12), P(.64, .40), P(.36, .40)], fill=light + (255,))
    dr.polygon([P(0, .40), P(.36, .40), P(.5, .96)], fill=dark + (255,))
    dr.polygon([P(1.0, .40), P(.64, .40), P(.5, .96)], fill=tuple(max(0, c - 25) for c in col) + (255,))
    dr.line([P(.22, .12), P(.36, .40), P(.5, .96)], fill=(255, 255, 255, 120), width=int(d * .008 * s) + 1)
    dr.line([P(.78, .12), P(.64, .40), P(.5, .96)], fill=(255, 255, 255, 90), width=int(d * .008 * s) + 1)
    dr.line([P(0, .40), P(1.0, .40)], fill=(255, 255, 255, 110), width=int(d * .008 * s) + 1)
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def crate(d):
    """cardboard box with tape, width d, height 0.9 d"""
    s = 4
    h = int(d * 0.9)
    im = Image.new("RGBA", (d * s, h * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.rectangle([0, 0, d * s, h * s], fill=CARTON + (255,))
    dr.rectangle([0, 0, d * s, int(h * .24 * s)], fill=(240, 196, 128, 255))
    dr.line([(0, int(h * .24 * s)), (d * s, int(h * .24 * s))], fill=CARTON_D + (255,), width=int(d * .018 * s) + 1)
    dr.rectangle([int(d * .43 * s), 0, int(d * .57 * s), h * s], fill=(255, 224, 160, 255))
    dr.rectangle([int(d * .18 * s), int(h * .56 * s), int(d * .36 * s), int(h * .60 * s)], fill=CARTON_D + (255,))
    dr.rectangle([int(d * .18 * s), int(h * .66 * s), int(d * .30 * s), int(h * .70 * s)], fill=CARTON_D + (255,))
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, d * s - 1, h * s - 1], radius=int(d * .09 * s), fill=255)
    im.putalpha(mask)
    return im.resize((d, h), Image.LANCZOS)


@lru_cache(None)
def spark(d, col=AMBER):
    s = 4
    im = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    c = d * s / 2
    pts = []
    for i in range(8):
        a = i * math.pi / 4
        r = c if i % 2 == 0 else c * 0.26
        pts.append((c + r * math.sin(a), c - r * math.cos(a)))
    ImageDraw.Draw(im).polygon(pts, fill=tuple(col) + (255,))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def flat_coin(w):
    h = int(w * 0.36)
    im = Image.new("RGBA", (w * 3, h * 3), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.ellipse([0, h * 0.35 * 3, w * 3 - 1, h * 3 - 1], fill=(214, 138, 0, 255))
    dr.ellipse([0, 0, w * 3 - 1, h * 3 * 0.72], fill=(255, 176, 32, 255))
    dr.ellipse([w * 3 * .18, h * 3 * .12, w * 3 * .82, h * 3 * .60], outline=(214, 138, 0, 255), width=6)
    return im.resize((w, h), Image.LANCZOS)


def build(tim):
    S, E, ws, we = tim.S, tim.E, tim.ws, tim.we
    END0 = tim.end0
    # scene windows (a, b); neighbours overlap by ~0.08 s so there is a short cross-fade
    WA = (0.0, S(2) - 0.10)
    WB = (S(2) - 0.18, S(3) - 0.10)
    WC = (S(3) - 0.18, S(4) - 0.10)
    WD = (S(4) - 0.18, S(5) - 0.10)
    WE = (S(5) - 0.18, S(6) - 0.10)
    WF = (S(6) - 0.18, S(7) - 0.10)
    WG = (S(7) - 0.18, S(9) - 0.10)        # tarif: "narxni emas, tarifni o'zgartir" + "arzonroq kichik variant"
    WI = (S(9) - 0.18, S(10) - 0.10)
    WJ = (S(10) - 0.18, END0)

    # ------------------------------------------------------------------ persistent characters (mijoz / sotuvchi)
    def sc_chars(cv, t):
        v = vis(t, 0.0, S(7) - 0.10, fo=0.25)
        if not v: return
        al, yo = v
        cm = "worried" if t < S(4) else ("neutral" if t < ws(24) else "happy")
        sm = "worried" if t < ws(5) else ("neutral" if t < S(4) else ("wink" if t < ws(23) else "happy"))
        bob = lambda k: 6 * math.sin(t * 3.3 + k)
        item(cv, face(210, cm, CREAM, NAVY), 230, 1300 + bob(0), t, -0.1, al, yo, dur=0.35)
        item(cv, face(210, sm, AMBER, NAVY), 850, 1300 + bob(2), t, 0.05, al, yo, dur=0.35)
        item(cv, txt("Mijoz", 34, MUTL, "sb"), 230, 1432, t, 0.25, al, yo, base=0.9)
        item(cv, txt("Sotuvchi", 34, MUTL, "sb"), 850, 1432, t, 0.35, al, yo, base=0.9)

    # ------------------------------------------------------------------ 1. hook: "Mijoz qimmat dedi, narxni tushirma."
    def sc_hook(cv, t):
        v = vis(t, *WA)
        if not v: return
        al, yo = v
        item(cv, txt("Mijoz “qimmat” dedi.", 84, TH.fg, "xb", 900), 540, 505, t, -0.12, al, yo)
        item(cv, txt("Narxni tushirma.", 84, TH.acc, "xb", 900), 540, 615, t, ws(3) - 0.12, al, yo)
        pop(cv, pricetag(520, 230, CREAM, HOLE, "NARX", NAVY, 96), 470, 860, t, 0.05, al, yo, dur=0.4, rot=3 * math.sin(t * 4.5))
        say(cv, bubble("Qimmat!", 66, CREAM, RED, "l"), (255, 1188), "l", t, ws(1) - 0.15, al, yo)
        if t < ws(4) - 0.02:
            a0 = prog(t, ws(3) - 0.1, 0.3)
            if a0 > 0:
                put(cv, arrow(220, 34, RED), 870, 840 + yo + 16 * math.sin(t * 8), al * ease_out_cubic(a0), 1.0, -90)
        else:
            k = prog(t, ws(4) - 0.02, 0.3)
            put(cv, arrow(220, 34, MUTL), 870, 855 + yo, al * 0.5, 1.0, -90)
            sc = 0.8 + 0.2 * clamp(ease_out_back(k, 1.6), 0, 1.3)
            put(cv, disc(230, None, RED, 16), 870, 855 + yo, al * ease_out_cubic(k), sc)
            put(cv, cross(130, RED, 24), 870, 855 + yo, al * ease_out_cubic(k), sc)

    # ------------------------------------------------------------------ 2. "Qimmat" = "foydasini tushunmadim"
    def sc_flip(cv, t):
        v = vis(t, *WB)
        if not v: return
        al, yo = v
        item(cv, txt("“Qimmat” ko‘pincha", 80, TH.fg, "xb", 900), 540, 505, t, S(2), al, yo)
        item(cv, txt("“foydasini tushunmadim”", 70, TH.acc, "xb", 900), 540, 615, t, ws(7) - 0.12, al, yo)
        pop(cv, chip("Qimmat", RED, WHITE, 64), 265, 910, t, S(2) + 0.05, al, yo)
        ak = ease_out_cubic(prog(t, ws(6), 0.35))
        if ak > 0:
            put(cv, arrow(180, 28, MUTL), 515 + 10 * ak, 910 + yo, al * ak, 1.0)
        pop(cv, disc(330, TH.card, TH.acc, 8), 800, 910, t, ws(7) - 0.2, al, yo, dur=0.4)
        pop(cv, bag(130, 150, AMBER), 800, 925, t, ws(7) - 0.1, al, yo, base=0.5)
        qk = prog(t, ws(8) - 0.15, 0.4)
        if qk > 0:
            put(cv, txt("?", 200, TH.acc), 800, 905 + yo, al * ease_out_cubic(qk), (0.7 + 0.3 * clamp(ease_out_back(qk, 1.8), 0, 1.4)) * (1 + 0.05 * math.sin(t * 8)))

    # ------------------------------------------------------------------ 3. narxni tushirish: eng oson, lekin eng zararli
    def sc_drop(cv, t):
        v = vis(t, *WC)
        if not v: return
        al, yo = v
        item(cv, txt("Narxni tushirish", 80, TH.fg, "xb", 900), 540, 505, t, S(3), al, yo)
        item(cv, txt("eng oson,", 72, GREEN, "xb", 900), 540, 605, t, ws(12) - 0.12, al, yo)
        item(cv, txt("lekin eng zararli yo‘l", 66, RED, "xb", 900), 540, 705, t, ws(14) - 0.12, al, yo)
        p0, p1 = (250, 840), (560, 1060)
        dashed_line(cv, p0, p1, MUTL, 6, 22, 14, ease_out_cubic(prog(t, S(3) + 0.1, 0.5)), al * 0.8)
        m = ease_in_out(prog(t, ws(11), 1.3))
        pop(cv, pricetag(300, 135, CREAM, HOLE, "NARX", NAVY, 62), lerp(p0[0], p1[0], m), lerp(p0[1], p1[1], m) - 10, t, S(3) + 0.1, al, yo, rot=-16 * m)
        for i in range(5):
            vq = prog(t, ws(15) + (4 - i) * 0.17, 0.3) if i > 0 else 0
            if vq >= 1:
                continue
            put_y = 1130 - i * 28 + 60 * ease_in_cubic(vq)
            pop(cv, flat_coin(190), 830, put_y, t, S(3) + 0.2 + i * 0.08, al * (1 - vq), yo, dur=0.3, rise=40)
        a = prog(t, ws(15) - 0.05, 0.3)
        if a > 0:
            put(cv, arrow(170, 30, RED), 905, 880 + yo + 14 * math.sin(t * 8), al * ease_out_cubic(a), 1.0, -90)

    # ------------------------------------------------------------------ 4. avval so'ra: nimaga nisbatan qimmat?
    def sc_why(cv, t):
        v = vis(t, *WD)
        if not v: return
        al, yo = v
        item(cv, txt("Avval so‘ra:", 84, TH.fg, "xb", 900), 540, 505, t, S(4), al, yo)
        pop(cv, pricetag(330, 148, CREAM, HOLE, "NARX", NAVY, 68), 260, 880, t, S(4) + 0.12, al, yo)
        dashed_line(cv, (470, 880 + yo), (620, 880 + yo), MUTL, 7, 20, 14, ease_out_cubic(prog(t, ws(21) - 0.1, 0.4)), al)
        pop(cv, rrect(330, 230, 44, TH.card, TH.acc, 6), 800, 880, t, ws(21) + 0.05, al, yo, dur=0.4)
        qk = prog(t, ws(21) + 0.15, 0.4)
        if qk > 0:
            put(cv, txt("?", 180, TH.acc), 800, 880 + yo, al * ease_out_cubic(qk), (0.7 + 0.3 * clamp(ease_out_back(qk, 1.8), 0, 1.4)) * (1 + 0.05 * math.sin(t * 8)))
        say(cv, bubble("Nimaga nisbatan qimmat?", 52, AMBER, NAVY, "r"), (805, 1188), "r", t, ws(20) - 0.3, al, yo)

    # ------------------------------------------------------------------ 5. keyin qiymatni ko'rsat
    def sc_value(cv, t):
        v = vis(t, *WE)
        if not v: return
        al, yo = v
        item(cv, txt("Keyin qiymatni", 82, TH.fg, "xb", 900), 540, 505, t, S(5), al, yo)
        item(cv, txt("ko‘rsat.", 82, TH.acc, "xb", 900), 540, 615, t, ws(25) - 0.1, al, yo)
        g = prog(t, S(5) + 0.05, 0.5)
        if g > 0:
            e = ease_out_cubic(g)
            pulse = 1 + 0.04 * math.sin(t * 7)
            put(cv, disc(430, None, SKY, 5), 540, 960 + yo, al * e * (0.35 + 0.2 * math.sin(t * 6)), 0.9 + 0.1 * e)
            put(cv, gem(340), 540, 960 + yo + (1 - e) * 60, al * e, (0.7 + 0.3 * clamp(ease_out_back(g, 1.5), 0, 1.3)) * pulse, 4 * math.sin(t * 4))
        for i, (x, y, d) in enumerate([(320, 790, 70), (765, 780, 90), (805, 1105, 64), (290, 1110, 80)]):
            k = prog(t, ws(25) + i * 0.07 - 0.2, 0.3)
            if k > 0:
                put(cv, spark(d, AMBER), x, y + yo, al * ease_out_cubic(k), (0.6 + 0.4 * clamp(ease_out_back(k, 1.6), 0, 1.3)) * (1 + 0.1 * math.sin(t * 9 + i)), 25 * math.sin(t * 3 + i))

    # ------------------------------------------------------------------ 6. nimani tejaydi, nimani hal qiladi (qiymat belgilari)
    def sc_marks(cv, t):
        v = vis(t, *WF)
        if not v: return
        al, yo = v
        pop(cv, chip("QIYMAT", GREEN, NAVY, 44), 540, 495, t, S(6), al, yo)
        # card 1: tejaydi
        pop(cv, rrect(860, 200, 44, TH.card, GREEN, 5), 540, 760, t, ws(26) + 0.1, al, yo, dur=0.4)
        pop(cv, coin(120), 250, 760, t, ws(26) + 0.2, al, yo)
        item(cv, txt("tejaydi", 88, TH.fg), 590, 760, t, ws(27) - 0.15, al, yo)
        pop(cv, check(100, GREEN, 18), 880, 760, t, ws(27) + 0.3, al, yo, dur=0.4, s0=0.5)
        # card 2: hal qiladi (muammo -> yechim)
        pop(cv, rrect(860, 200, 44, TH.card, GREEN, 5), 540, 1000, t, ws(29) - 0.3, al, yo, dur=0.4)
        solved = t >= ws(30) - 0.02
        if not solved:
            pop(cv, disc(120, RED), 250, 1000, t, ws(29) - 0.2, al, yo)
            pop(cv, txt("!", 90, WHITE), 250, 1000, t, ws(29) - 0.2, al, yo)
        else:
            k = prog(t, ws(30) - 0.02, 0.35)
            sc = 0.7 + 0.3 * clamp(ease_out_back(k, 1.8), 0, 1.4)
            put(cv, disc(120, GREEN), 250, 1000 + yo, al, sc)
            put(cv, check(80, WHITE, 14), 250, 1000 + yo, al, sc)
        item(cv, txt("hal qiladi", 88, TH.fg), 610, 1000, t, ws(29) - 0.12, al, yo)
        pop(cv, check(100, GREEN, 18), 880, 1000, t, ws(30) + 0.3, al, yo, dur=0.4, s0=0.5)

    # ------------------------------------------------------------------ 7+8. narxni emas, tarifni o'zgartir -> arzonroq kichik variant
    crate_pos = {0: (250, 1313, 150), 1: (540, 1286, 210), 2: (830, 1254, 280)}

    def sc_tarif(cv, t):
        v = vis(t, *WG)
        if not v: return
        al, yo = v
        gend = S(8) - 0.02
        vg = vis(t, WG[0], gend, fo=0.14)            # phase-G lines fade out when phase H starts
        if vg:
            ga, gy = al * vg[0], yo + vg[1]
            item(cv, txt("Kerak bo‘lsa,", 62, MUTL, "sb", 900), 540, 495, t, S(7), ga, gy)
            item(cv, txt("narxni emas,", 82, TH.fg, "xb", 900), 540, 600, t, ws(33) - 0.12, ga, gy)
            item(cv, txt("tarifni o‘zgartir", 82, TH.acc, "xb", 900), 540, 705, t, ws(35) - 0.15, ga, gy)
            dim = 1 - 0.55 * ease_out_cubic(prog(t, ws(35), 0.3))
            pop(cv, pricetag(400, 180, CREAM, HOLE, "NARX", NAVY, 82), 540, 905, t, S(7) + 0.1, ga, gy, base=dim)
            k = prog(t, ws(34), 0.3)
            if k > 0:
                sc = 0.8 + 0.2 * clamp(ease_out_back(k, 1.6), 0, 1.3)
                put(cv, disc(290, None, RED, 16), 540, 905 + gy, ga * ease_out_cubic(k), sc)
                put(cv, cross(170, RED, 28), 540, 905 + gy, ga * ease_out_cubic(k), sc)
        # phase H lines
        item(cv, txt("Arzonroq,", 84, TH.fg, "xb", 900), 540, 495, t, S(8), al, yo)
        item(cv, txt("kichik variant", 82, TH.acc, "xb", 900), 540, 600, t, ws(38) - 0.12, al, yo)
        item(cv, txt("taklif qil.", 74, TH.fg, "sb", 900), 540, 705, t, ws(40) - 0.1, al, yo)

        # three tariff boxes (small / medium / large), then the small one is offered to the customer
        # the medium and large boxes fade away when "kichik variant" is said (the small one is drawn in sc_tarif_small)
        fade = ease_in_out(prog(t, ws(38), 0.4))
        for i in (2, 1):
            x, y, d = crate_pos[i]
            pop(cv, crate(d), x, y + 30 * fade, t, ws(35) + 0.05 + 0.12 * i, al, yo, dur=0.35, rise=60, base=(1 - fade))

    def sc_tarif_small(cv, t):
        """the small tariff box + its 'arzonroq' chip, the two people and the hand-over (scale/position animated explicitly)"""
        v = vis(t, *WG)
        if not v: return
        al, yo = v
        x, y, d = crate_pos[0]
        tx = ws(38)
        m = ease_in_out(prog(t, tx, 0.5))
        n = ease_in_out(prog(t, ws(40) - 0.2, 0.55))
        cx, cy, sc = lerp(x, 540, m), lerp(y, 1060, m), lerp(1.0, 1.55, m)
        if n > 0:
            cx, cy = lerp(540, 410, n), lerp(1060, 1120, n) - 70 * math.sin(math.pi * n)
        ch = d * 0.9 * sc
        # persons arrive
        pa = prog(t, ws(39) - 0.2, 0.4)
        if pa > 0:
            put(cv, person(230, CREAM), 200, 1190 + (1 - ease_out_cubic(pa)) * 70, al * ease_out_cubic(pa))
            put(cv, person(230, AMBER), 880, 1190 + (1 - ease_out_cubic(pa)) * 70, al * ease_out_cubic(pa))
        # the small box (always on top of the faded ones)
        e = ease_out_cubic(prog(t, ws(35) + 0.05, 0.35))
        if e > 0:
            put(cv, crate(d), cx, cy + (1 - e) * 60, al * e, sc * (0.88 + 0.12 * clamp(ease_out_back(prog(t, ws(35) + 0.05, 0.35), 1.2), 0, 1.2)))
        # 'arzonroq' chip follows the box
        pop(cv, chip("arzonroq", GREEN, NAVY, 38), cx, cy - ch / 2 - 46, t, S(8) + 0.05, al, yo, dur=0.3, rise=14)
        if n >= 0.999 or t > ws(40) - 0.2 + 0.55:
            k = prog(t, ws(40) - 0.2 + 0.55, 0.3)
            put(cv, check(130, GREEN, 22), 200, 1020 + yo, al * ease_out_cubic(k), 0.6 + 0.4 * clamp(ease_out_back(k, 1.8), 0, 1.4))

    # ------------------------------------------------------------------ 9. mijoz mahsulotni emas, natijani sotib oladi
    def sc_result(cv, t):
        v = vis(t, *WI)
        if not v: return
        al, yo = v
        item(cv, txt("Mijoz mahsulotni emas,", 70, TH.fg, "xb", 900), 540, 505, t, S(9), al, yo)
        item(cv, txt("natijani sotib oladi.", 78, TH.acc, "xb", 900), 540, 615, t, ws(45) - 0.12, al, yo)
        dim = 1 - 0.6 * ease_out_cubic(prog(t, ws(44), 0.3))
        pop(cv, crate(230), 270, 940, t, S(9) + 0.1, al, yo, base=dim)
        k = prog(t, ws(44), 0.3)
        if k > 0:
            sc = 0.8 + 0.2 * clamp(ease_out_back(k, 1.6), 0, 1.3)
            put(cv, disc(300, None, RED, 16), 270, 940 + yo, al * ease_out_cubic(k), sc)
            put(cv, cross(170, RED, 28), 270, 940 + yo, al * ease_out_cubic(k), sc)
        g = prog(t, ws(45) - 0.05, 0.5)
        if g > 0:
            e = ease_out_cubic(g)
            put(cv, disc(340, GREEN), 790, 940 + yo + (1 - e) * 40, al * e, (0.7 + 0.3 * clamp(ease_out_back(g, 1.5), 0, 1.3)) * (1 + 0.03 * math.sin(t * 6)))
            put(cv, check(200, WHITE, 34), 790, 940 + yo + (1 - e) * 40, al * e, (0.7 + 0.3 * clamp(ease_out_back(g, 1.5), 0, 1.3)))
        for i, (x, y, d) in enumerate([(640, 780, 64), (950, 800, 80), (960, 1090, 56)]):
            sk = prog(t, ws(45) + 0.15 + i * 0.1, 0.3)
            if sk > 0:
                put(cv, spark(d, AMBER), x, y + yo, al * ease_out_cubic(sk), (0.6 + 0.4 * clamp(ease_out_back(sk, 1.6), 0, 1.3)) * (1 + 0.1 * math.sin(t * 9 + i)), 25 * math.sin(t * 3 + i))
        # coin flies from the product to the result
        cf = ease_in_out(prog(t, ws(46) - 0.1, 0.6))
        if 0 < cf < 1:
            put(cv, coin(110), lerp(300, 770, cf), lerp(960, 940, cf) - 150 * math.sin(cf * math.pi) + yo, al * (1 - 0.6 * cf), lerp(1.0, 0.7, cf))
        # rising line (result grows)
        pts = [(140, 1370), (380, 1320), (560, 1340), (780, 1260), (940, 1190)]
        rp = ease_in_out(prog(t, ws(45) + 0.15, 1.5))
        poly(cv, [(x, y + yo) for x, y in pts], GREEN, 14, rp, al)
        if rp > 0.97:
            ak = ease_out_cubic(prog(t, ws(45) + 0.15 + 1.45, 0.25))
            put(cv, arrow(96, 24, GREEN), 934, 1186 + yo, al * ak, 1.0, math.degrees(math.atan2(70, 160)))

    # ------------------------------------------------------------------ 10. CTA: sotuvchi do'sting bo'lsa, yubor
    def sc_cta(cv, t):
        v = vis(t, *WJ, fo=0.25)
        if not v: return
        al, yo = v
        item(cv, txt("Sotuvchi do‘sting bo‘lsa,", 62, TH.fg, "sb", 900), 540, 490, t, S(10), al, yo)
        item(cv, txt("yubor", 150, TH.acc, "xb", 900), 540, 630, t, ws(51) - 0.45, al, yo, dur=0.34)
        pop(cv, person(300, AMBER), 250, 1070, t, S(10) + 0.1, al, yo, dur=0.35)
        pop(cv, person(300, CREAM), 830, 1070, t, S(10) + 0.2, al, yo, dur=0.35)
        item(cv, txt("Sotuvchi", 38, MUTL, "sb"), 250, 1270, t, S(10) + 0.3, al, yo, base=0.9)
        item(cv, txt("do‘sting", 38, MUTL, "sb"), 830, 1270, t, ws(49) - 0.1, al, yo, base=0.9)
        P0, P1, P2 = (250, 845), (540, 720), (830, 845)
        bez = lambda s: ((1 - s) ** 2 * P0[0] + 2 * (1 - s) * s * P1[0] + s * s * P2[0], (1 - s) ** 2 * P0[1] + 2 * (1 - s) * s * P1[1] + s * s * P2[1])
        fl = ease_in_out(prog(t, ws(49) + 0.1, 0.95))
        if fl > 0:
            pts = [(x, y + yo) for x, y in (bez(fl * i / 30) for i in range(31))]
            poly(cv, pts, MUTL, 6, 1.0, al * 0.7)
            x, y = bez(fl)
            if fl < 0.999:
                put(cv, logo(130, TH.lb, TH.ln, TH.ln), x, y + yo, al, 1.0 + 0.1 * math.sin(fl * math.pi), 8 * math.sin(fl * 6))
        if fl >= 0.999:
            q = prog(t, ws(49) + 0.1 + 0.95, 0.3)
            put(cv, logo(130, TH.lb, TH.ln, TH.ln), P2[0], P2[1] + yo, al, 1.0)
            put(cv, disc(96, GREEN), 950, 800 + yo, al * ease_out_cubic(q), 0.6 + 0.4 * clamp(ease_out_back(q, 1.8), 0, 1.4))
            put(cv, check(60, WHITE, 10), 950, 800 + yo, al * ease_out_cubic(q), 0.6 + 0.4 * clamp(ease_out_back(q, 1.8), 0, 1.4))

    # ------------------------------------------------------------------ "maslahat" badge (practical advice, not statistics)
    def sc_badge(cv, t):
        v = vis(t, 0.2, END0 - 0.45, fo=0.3)
        if not v: return
        al, yo = v
        pop(cv, chip("MASLAHAT", AMBER, NAVY, 34), 540, 392, t, 0.25, al, yo, dur=0.3, rise=14)

    return Reel(tim, [sc_chars, sc_hook, sc_flip, sc_drop, sc_why, sc_value, sc_marks, sc_tarif, sc_tarif_small, sc_result, sc_cta, sc_badge],
                theme="ink", bg="spot", overlay_kind="rings", disclaimer="")
