"""Kun 17: Favqulodda zaxira. PREMIUM uslub: "SEYF" (qorong'u oltin seyf, jumboq: bitta son).
Savol -> raqamlar aylanadi -> "?" -> hisoblash -> seyf eshigi ochiladi: 3-6 OY -> avtomatik chetga ol -> xotirjamlik (sovuq nur) -> izoh.
"""
import math
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from nt_kit import *      # noqa
from nt_fx import *       # noqa
from nt_char import Host, speech_env, head_shake, nod, wave, tap, LW, CH as CHH   # noqa

GOLD0, GOLD1 = (255, 241, 190), (216, 150, 38)
RED2, TEAL = (242, 86, 74), (110, 232, 216)
CX = 540


def win(t, a, b, fi=0.10, fo=0.20):
    if t < a or t >= b:
        return 0.0
    return clamp((t - a) / fi) * clamp((b - t) / fo) if fi > 0 else clamp((b - t) / fo)


# ----------------------------------------------------------------------------- cached art
@lru_cache(None)
def G(s, size, maxw=900):
    z = size
    while z > 30:
        im = gtext(s, z, GOLD0, GOLD1)
        if im.width <= maxw:
            return im
        z -= 4
    return gtext(s, z, GOLD0, GOLD1)


@lru_cache(None)
def GG(s, size, r=26, k=1.3):
    return glow(G(s, size), (255, 190, 70), r, k)


@lru_cache(None)
def X(s, size, col, maxw=900, w="xb"):
    return txt(s, size, col, w, maxw)


@lru_cache(None)
def house_icon(w, col=(255, 236, 170), dark=(60, 44, 20)):
    s = 3
    im = Image.new("RGBA", (w * s, w * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    Wd = w * s
    d.polygon([(Wd * .5, Wd * .06), (Wd * .97, Wd * .48), (Wd * .03, Wd * .48)], fill=tuple(col) + (255,))
    d.rectangle([Wd * .15, Wd * .46, Wd * .85, Wd * .93], fill=tuple(col) + (255,))
    d.rectangle([Wd * .42, Wd * .62, Wd * .58, Wd * .93], fill=tuple(dark) + (255,))
    return im.resize((w, w), Image.LANCZOS)


@lru_cache(None)
def loop_icon(d, col=(255, 236, 170), th=14):
    s = 3
    D = d * s
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    box = [th * s, th * s, D - th * s, D - th * s]
    dr.arc(box, 40, 300, fill=tuple(col) + (255,), width=th * s)
    R = D / 2 - th * s
    ang = math.radians(300)
    px, py = D / 2 + R * math.cos(ang), D / 2 + R * math.sin(ang)
    tx, ty = -math.sin(ang), math.cos(ang)
    nx, ny = math.cos(ang), math.sin(ang)
    h, wd = th * s * 2.4, th * s * 1.8
    dr.polygon([(px + tx * h, py + ty * h), (px + nx * wd, py + ny * wd), (px - nx * wd, py - ny * wd)], fill=tuple(col) + (255,))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def shield_icon(w, col=TEAL, dark=(8, 40, 52)):
    s = 3
    h = int(w * 1.15)
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    Wd, Hd = w * s, h * s
    pts = [(Wd * .5, Hd * .02), (Wd * .92, Hd * .16), (Wd * .90, Hd * .52), (Wd * .5, Hd * .98), (Wd * .10, Hd * .52), (Wd * .08, Hd * .16)]
    d.polygon(pts, fill=tuple(col) + (255,))
    inner = [(Wd * .5, Hd * .12), (Wd * .80, Hd * .23), (Wd * .78, Hd * .50), (Wd * .5, Hd * .84), (Wd * .22, Hd * .50), (Wd * .20, Hd * .23)]
    d.polygon(inner, fill=tuple(mixc(col, dark, 0.35)) + (255,))
    d.line([(Wd * .34, Hd * .48), (Wd * .46, Hd * .60), (Wd * .68, Hd * .34)], fill=(255, 255, 255, 255), width=int(w * .07 * s), joint="curve")
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def plane_icon(w, col=(255, 236, 170)):
    s = 3
    im = Image.new("RGBA", (w * s, w * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    Wd = w * s
    d.polygon([(Wd * .04, Wd * .46), (Wd * .96, Wd * .08), (Wd * .62, Wd * .92), (Wd * .46, Wd * .60)], fill=tuple(col) + (255,))
    d.polygon([(Wd * .46, Wd * .60), (Wd * .96, Wd * .08), (Wd * .52, Wd * .50)], fill=(190, 150, 70, 255))
    return im.resize((w, w), Image.LANCZOS)


@lru_cache(None)
def vault_body(d):
    s = 2
    D = d * s
    yy, xx = np.mgrid[0:D, 0:D].astype(np.float32)
    c = (D - 1) / 2
    r = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (D / 2)
    ang = np.arctan2(yy - c, xx - c)
    light = (0.5 + 0.5 * np.cos(ang + math.radians(135)))[..., None]
    face = np.array((58, 62, 74), np.float32) * (0.62 + 0.62 * light) * (1.05 - 0.12 * r[..., None])
    rim = np.array((214, 160, 60), np.float32) * (0.55 + 0.7 * light)
    groove = np.array((18, 18, 24), np.float32) * np.ones_like(light)
    col = face.copy()
    col = np.where((r > 0.93)[..., None], rim, col)
    col = np.where(((r > 0.895) & (r <= 0.93))[..., None], groove, col)
    col = np.where((r < 0.56)[..., None], face * 1.14, col)
    col = np.where(((r > 0.555) & (r < 0.575))[..., None], groove, col)
    a = np.clip((1 - r) * (D / 2) / 2.0, 0, 1)
    im = Image.fromarray(np.dstack([np.clip(col, 0, 255), a * 255]).astype(np.uint8), "RGBA")
    dr = ImageDraw.Draw(im)
    for k in range(12):
        an = math.radians(k * 30 + 15)
        bx, by = c + math.cos(an) * D / 2 * 0.77, c + math.sin(an) * D / 2 * 0.77
        rb = D * 0.021
        dr.ellipse([bx - rb, by - rb, bx + rb, by + rb], fill=(24, 24, 30, 255))
        dr.ellipse([bx - rb * 0.65, by - rb * 0.65 - rb * 0.12, bx + rb * 0.65, by + rb * 0.65 - rb * 0.12], fill=(190, 150, 74, 255))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(maxsize=160)
def vault_wheel(d, angq):
    s = 2
    D = d * s
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    c = D / 2
    gold, dark = (232, 178, 72, 255), (40, 30, 14, 255)
    R = D * 0.30
    for k in range(3):
        an = math.radians(k * 120 + 90)
        ex, ey = c + math.cos(an) * R * 1.32, c + math.sin(an) * R * 1.32
        dr.line([(c, c), (ex, ey)], fill=gold, width=int(D * 0.034))
        dr.ellipse([ex - D * .035, ey - D * .035, ex + D * .035, ey + D * .035], fill=gold)
        an2 = an + math.pi
        ex2, ey2 = c + math.cos(an2) * R, c + math.sin(an2) * R
        dr.line([(c, c), (ex2, ey2)], fill=gold, width=int(D * 0.034))
    dr.ellipse([c - R, c - R, c + R, c + R], outline=gold, width=int(D * 0.034))
    dr.ellipse([c - D * .075, c - D * .075, c + D * .075, c + D * .075], fill=gold)
    dr.ellipse([c - D * .035, c - D * .035, c + D * .035, c + D * .035], fill=dark)
    return im.rotate(-angq, resample=Image.BICUBIC).resize((d, d), Image.LANCZOS)


@lru_cache(None)
def inner_light(d):
    D = d
    yy, xx = np.mgrid[0:D, 0:D].astype(np.float32)
    r = np.sqrt((xx - D / 2) ** 2 + (yy - D / 2) ** 2) / (D / 2)
    k = np.clip(1 - r, 0, 1)
    col = np.array((255, 226, 140), np.float32) * (0.55 + 0.6 * k[..., None]) + np.array((120, 60, 10), np.float32) * (1 - k[..., None]) * 0.4
    a = (np.clip((1 - r) * 2.4, 0, 1) ** 1.4) * 255
    return Image.fromarray(np.dstack([np.clip(col, 0, 255), a]).astype(np.uint8), "RGBA")


def vault(cv, cx, cy, d, t, spin, open_p=0.0, alpha=1.0, glow_a=0.0):
    """closed/opening vault door centred at (cx, cy); door hinges on its left edge"""
    if glow_a > 0 or open_p > 0:
        put(cv, inner_light(d), cx, cy, alpha * clamp(0.25 + open_p * 0.75) * (0.7 + glow_a * 0.3))
    body, wheel = vault_body(d), vault_wheel(d, int(spin // 3) * 3 % 360)
    sx = 1 - 0.9 * ease_in_out(open_p)
    left = cx - d / 2
    if sx > 0.99:
        put(cv, body, cx, cy, alpha)
        put(cv, wheel, cx, cy, alpha)
    else:
        put_xs(cv, body, left + d * sx / 2, cy, sx, alpha)
        put_xs(cv, wheel, left + d * sx / 2, cy, sx, alpha)


@lru_cache(None)
def orect(w, h, r, col, ow):
    s = 3
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=r * s, outline=tuple(col) + (255,), width=ow * s)
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def card(w, h, r=46, a=30, ba=100, blur=28, off=18, sh=0.55, border=(255, 220, 140)):
    """glass card with a soft drop shadow (cached)"""
    return shadowed(glass(w, h, r, (255, 255, 255), a, border, ba), blur, (0, off), sh)


@lru_cache(None)
def GS(s, size):
    return shadowed(GG(s, size, 26), 30, (0, 16), 0.5)


@lru_cache(None)
def BAGL():
    b = bag(380, 440, (226, 160, 48), (150, 96, 20))
    b.alpha_composite(coin(190, (255, 224, 130), (176, 118, 20), "so'm", (120, 74, 8)), (95, 150))
    return glow(b, (255, 190, 70), 26, 0.7)


@lru_cache(None)
def SEG(glowing):
    base = rrect(210, 118, 36, (244, 196, 92))
    return glow(base, (255, 190, 70), 18, 1.4) if glowing else base


# ----------------------------------------------------------------------------- props
@lru_cache(None)
def calc_art():
    s = 3
    w, h = 250, 330
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=34 * s, fill=(244, 196, 92, 255))
    d.rounded_rectangle([5 * s, 5 * s, (w - 5) * s, (h - 5) * s], radius=30 * s, fill=(46, 50, 64, 255))
    d.rounded_rectangle([22 * s, 22 * s, (w - 22) * s, 92 * s], radius=14 * s, fill=(150, 226, 200, 255))
    for r in range(4):
        for c in range(4):
            x0, y0 = (24 + c * 52) * s, (112 + r * 50) * s
            col = (244, 196, 92, 255) if c == 3 else (88, 94, 112, 255)
            d.rounded_rectangle([x0, y0, x0 + 42 * s, y0 + 38 * s], radius=10 * s, fill=col)
    return im.resize((w, h), Image.LANCZOS)


def calc_screen(txt):
    base = calc_art().copy()
    dd = ImageDraw.Draw(base)
    f = F("xb", 46)
    tw = dd.textlength(txt, font=f)
    dd.text((250 - 30 - tw, 28), txt, font=f, fill=(20, 60, 50, 255))
    return base


@lru_cache(None)
def bubble_art():
    return card(440, 330, 150, 40, 130, 30, 16, 0.5)


# ----------------------------------------------------------------------------- the video
def build(tim, env=None):
    w = tim.ws
    END = tim.end0
    D = os.path.dirname(os.path.abspath(__file__))
    env = speech_env(f"{D}/work/voice_st.wav")

    # ---------------- the host: one continuous character; position, face and hands are keyframed
    HANDS_HEAD = dict(lhx=212, lhy=185, rhx=428, rhy=185)
    CELEB = dict(lhx=110, lhy=300, rhx=530, rhy=300)
    track = [
        (0.0, "calm", dict(cx=360, by=1470, sc=1.0, lx=0.0, ly=0.0, brow=0.3, rhx=470, rhy=700)),
        (0.9, "worried", dict(cx=360, by=1470, sc=1.0, lx=0.0, ly=0.0), 0.35),
        (1.5, "worried", dict(cx=360, by=1470, sc=1.0, lx=0.9, ly=-0.6, sweat=1.0), 0.4),
        (2.62, "shock", dict(cx=360, by=1470, sc=1.0, lx=0.9, ly=-0.6), 0.16, "back"),
        (2.95, "worried", dict(cx=540, by=1470, sc=0.92, lx=0.0, ly=-0.7), 0.4),
        (3.35, "panic", dict(cx=540, by=1470, sc=0.92, lx=0.0, ly=-0.5, **HANDS_HEAD), 0.22, "back"),
        (5.6, "panic", dict(cx=540, by=1470, sc=0.92, lx=0.0, ly=0.5, **HANDS_HEAD), 0.5),
        (6.3, "think", dict(cx=540, by=1470, sc=0.88, rhx=392, rhy=374), 0.5),
        (6.95, "think", dict(cx=540, by=1470, sc=0.88, rhx=392, rhy=374, brow=0.8, asym=0.0, ly=-0.9, lx=-0.3), 0.25),
        (7.75, "smile", dict(cx=540, by=1470, sc=0.85, lhx=262, lhy=650, rhx=378, rhy=650, ly=0.6, lx=0.0, smile=0.4), 0.45),
        (9.25, "smile", dict(cx=540, by=1470, sc=0.85, lhx=262, lhy=650, rhx=378, rhy=650, ly=-0.7, lx=0.0, brow=0.7, smile=0.5), 0.3),
        (9.95, "grin", dict(cx=540, by=1470, sc=0.85, lhx=262, lhy=650, rhx=378, rhy=650, ly=-0.4, brow=0.6), 0.25),
        (10.6, "worried", dict(cx=250, by=1282, sc=0.52, ly=-0.5, lx=0.6), 0.5),
        (11.08, "shock", dict(cx=250, by=1282, sc=0.52, lx=0.6, ly=-0.5), 0.14, "back"),
        (12.15, "awe", dict(cx=250, by=1282, sc=0.52, lx=0.6, ly=-0.4), 0.3),
        (13.0, "grin", dict(cx=250, by=1282, sc=0.52, **CELEB), 0.3, "back"),
        (14.25, "grin", dict(cx=540, by=1470, sc=0.85), 0.4),
        (14.7, "no", dict(cx=540, by=1470, sc=0.85, rhx=520, rhy=330), 0.22),
        (15.25, "smile", dict(cx=540, by=1470, sc=0.85, rhx=522, rhy=320, rg=2, rpa=-20, lx=0.3, ly=-0.8), 0.35),
        (16.35, "smile", dict(cx=540, by=1470, sc=0.85, rhx=506, rhy=420, rg=2, rpa=-5, lx=0.2, ly=0.3, brow=0.3), 0.4),
        (17.42, "calm", dict(cx=540, by=1470, sc=0.85, ly=-0.4, smile=0.2), 0.4),
        (17.85, "calm", dict(cx=540, by=1470, sc=0.85, lhx=70, lhy=470, rhx=570, rhy=470, brow=0.6, tilt=0.6, smile=-0.1), 0.35),
        (18.6, "no", dict(cx=540, by=1470, sc=0.85, lhx=70, lhy=470, rhx=570, rhy=470, tilt=0.4), 0.3),
        (19.3, "relief", dict(cx=540, by=1470, sc=0.85), 0.6),
        (20.3, "wink", dict(cx=540, by=1470, sc=0.88, rhx=524, rhy=330, rg=2, rpa=-25, lx=0.0, ly=-0.5), 0.5),
        (21.2, "smile", dict(cx=540, by=1470, sc=0.88, rhx=524, rhy=330, rg=2, rpa=-25, lx=0.4, ly=-0.7), 0.4),
        (22.4, "grin", dict(cx=540, by=1470, sc=0.9, rhx=470, rhy=520, rg=2, rpa=0, lx=0.0, ly=0.0, brow=0.5), 0.35),
        (23.1, "wink", dict(cx=540, by=1470, sc=0.9, rhx=520, rhy=330, rg=0), 0.35),
    ]
    mods = [head_shake(14.17, 0.9, 16, 3.6), nod(16.272, 0.8, 9), nod(22.4, 0.7, 10), wave("r", 23.2, 1.6, 30, 14, 2.4),
            nod(12.2, 0.9, 8)]

    def p_calc(cv, t, host, al):
        a, b = 7.6, 10.6
        if t < a or t > b + 0.2:
            return
        k = ease_out_back(clamp((t - a) / 0.45), 1.0)
        fo = clamp((b + 0.2 - t) / 0.2)
        gx, gy = host.g(320 + 100, 560)
        sc = host.sc_now * 0.78
        txt = "0"
        for t0_, lab_ in ((8.082, "2.5"), (8.40, "4.3"), (8.72, "4.6"), (9.04, "4.9"), (9.815, "5.0")):
            if t >= t0_:
                txt = lab_
        put(cv, calc_screen(txt), gx, gy + (1 - k) * 300 * sc, al * fo * clamp(k * 2), sc, -5)

    host = Host(track, env=env, mods=mods, props=[p_calc], gscale=1.12, gdy=48)

    # ---------------- A. hook (question + thought bubble with the rolling "days" ring)
    def sc_hook(cv, t):
        al = win(t, -0.2, 2.9, 0.05, 0.22)
        if al <= 0:
            return
        t = t + 0.18
        pop(cv, X("Ertaga ishsiz", 118, (250, 246, 236), 940), CX, 405, t, -0.12, 0.40, al)
        pop(cv, G("qolsang,", 126), CX, 548, t, 0.02, 0.40, al)
        bx, by_ = 800, 780
        pop(cv, bubble_art(), bx, by_, t, 0.1, 0.45, al, rise=40)
        for (dx, dy, dd, aa) in ((-150, 150, 54, 0.30), (-205, 205, 34, 0.26)):
            pop(cv, disc(dd, (255, 240, 200)), bx + dx, by_ + dy, t, 0.2, 0.3, al * aa)
        p = prog(t, 0, 2.55)
        put(cv, ring(262, p, (244, 196, 92), (255, 255, 255, 34), 18), bx, by_ - 22, al)
        lock = t >= 2.55
        s = rolling_digits(t, 2.55, "?", 2, 5, 24)
        sz = 220 if lock else 150
        sc = 1.0 + (0.22 * (1 - clamp((t - 2.55) / 0.25)) if lock else 0.0)
        put(cv, GG(s, sz, 30), bx, by_ - 24, al, sc)
        put(cv, X("KUN", 44, (190, 186, 176), 300), bx, by_ + 132, al * 0.95)

    # ---------------- B. salary stops, bills continue (notification cards above the host)
    def sc_bills(cv, t):
        al = win(t, 2.75, 6.25)
        if al <= 0:
            return
        dim = 1.0 - 0.5 * ease_out_cubic((t - 3.207) / 0.25)
        card_ = card(880, 130, 44, 32, 100, 28, 18)
        pop(cv, card_, CX, 430, t, 2.78, 0.36, al * dim, rise=60)
        pop(cv, coin(98, mark="so'm"), 205, 430, t, 2.86, 0.36, al * dim)
        pop(cv, X("MAOSH", 78, (250, 246, 236), 300), 430, 430, t, 2.9, 0.36, al * dim)
        if t >= 3.207:
            p = (t - 3.207) / 0.16
            st = orect(350, 92, 22, RED2, 9)
            lab = X("TO'XTADI", 54, RED2, 300)
            sc = 1 + 1.4 * (1 - ease_out_cubic(p))
            put(cv, st, 795, 440, al * clamp(p * 3), sc, 7)
            put(cv, lab, 795, 440, al * clamp(p * 3), sc, 7)
        for k, (label, y, t0) in enumerate((("IJARA", 590, 4.306), ("OVQAT", 750, 4.806))):
            if t < t0:
                continue
            x_in = lerp(1500, CX, ease_out_back((t - t0) / 0.45, 1.0))
            put(cv, card_, x_in, y, al)
            icon = house_icon(92) if k == 0 else basket(120, 78)
            put(cv, icon, x_in - 335, y + (0 if k == 0 else 12), al)
            put(cv, X(label, 78, (250, 246, 236), 330), x_in - 130, y, al)
            if t >= 5.207:
                p = clamp((t - 5.207 - k * 0.12) / 0.3)
                put(cv, loop_icon(62), x_in + 125, y, al * p, 1.0, -t * 140)
                pop(cv, X("HAR OY", 52, (244, 196, 92), 220), x_in + 270, y, t, 5.207 + k * 0.12, 0.3, al)

    # ---------------- C. the answer is one number
    def sc_one(cv, t):
        al = win(t, 6.15, 7.75)
        if al <= 0:
            return
        pop(cv, G("JAVOB:", 104), CX, 410, t, 6.2, 0.36, al)
        put(cv, ring(330, 1.0, (244, 196, 92), (255, 255, 255, 34), 16), CX, 620, al)
        pulse = 1 + 0.05 * math.sin((t - 6.2) * 9)
        put(cv, GG("?", 240, 30), CX, 615, al, pulse)
        if t >= 6.607:
            pop(cv, X("BITTA SON", 92, (250, 246, 236), 760), CX, 826, t, 6.607, 0.34, al)

    # ---------------- D. the calculator (MISOL)
    rows = (("Ijara", 2500000, 8.082), ("Ovqat", 1800000, 8.40), ("Yo'l", 300000, 8.72), ("Kommunal", 400000, 9.04))

    def sc_calc(cv, t):
        al = win(t, 7.6, 10.55)
        if al <= 0:
            return
        panel = card(920, 500, 52, 28, 90, 34, 26, 0.6)
        pop(cv, panel, CX, 630, t, 7.62, 0.4, al, rise=50)
        pop(cv, rrect(250, 64, 32, (244, 196, 92)), CX, 380, t, 7.65, 0.3, al)
        pop(cv, X("MISOL", 40, (30, 24, 12), 220), CX, 380, t, 7.65, 0.3, al)
        pop(cv, X("OYLIK MAJBURIY XARAJAT", 42, (190, 186, 176), 820, "b"), CX, 450, t, 7.78, 0.3, al)
        for k, (lab, val, t0) in enumerate(rows):
            y = 525 + k * 68
            if t < t0:
                continue
            v = count_up(t, t0, 0.32, 0, val)
            lw_ = X(lab, 52, (250, 246, 236), 380, "sb")
            pop(cv, lw_, 160 + lw_.width / 2, y, t, t0, 0.28, al)
            vl = X(fmt(v), 54, (244, 196, 92), 420)
            put(cv, vl, 850 - vl.width / 2, y, al * clamp((t - t0) / 0.15))
        if t >= 9.15:
            put(cv, rrect(780, 5, 2, (255, 255, 255)), CX, 782, al * 0.35)
            pop(cv, X("JAMI", 60, (250, 246, 236), 260), 240, 835, t, 9.2, 0.3, al)
        if t >= 9.815:
            v = count_up(t, 9.815, 0.55, 0, 5000000)
            lay = G(fmt(v), 76, 440)
            put(cv, glow(lay, (255, 190, 70), 18, 1.1), 735, 835, al, 1.0 + 0.1 * math.sin(clamp((t - 9.815) / 0.6) * math.pi))
        elif t >= 9.2:
            put(cv, G("?", 90), 735, 835, al)

    # ---------------- E. the vault opens: 3-6 oy (host reacts in the corner)
    VY = 690

    def sc_vault(cv, t):
        al = win(t, 10.45, 14.15, 0.15, 0.22)
        if al <= 0:
            return
        recede = ease_in_out((t - 11.0) / 0.35)
        d = int(720 * (1 + 0.28 * recede))
        a_door = al * (1 - 0.55 * recede)
        spin = t * 38 + (max(0, t - 11.9) ** 2) * 160
        op = clamp((t - 12.05) / 0.95)
        if op > 0:
            rays(cv, CX, VY + 20, t, (255, 214, 130), 14, 0.20 * op, 14)
        vault(cv, CX, VY, d, t, spin, op, a_door, glow_a=op)
        if t >= 12.05:
            sparks(cv, t, 12.35, CX, VY, 46, (255, 214, 120), 7, 1.1, 620, 8, r0=340)
        for s_, x_, t0 in (("3", 320, 11.015), ("6", 760, 11.615)):
            if t >= t0:
                p = clamp((t - t0) / 0.20)
                sc = 1 + 1.3 * (1 - ease_out_cubic(p))
                put(cv, GS(s_, 420), x_, VY, al * clamp(p * 3), sc)
        if t >= 11.8:
            pop(cv, G("–", 230), CX, VY, t, 11.8, 0.25, al)
        if t >= 12.015:
            pop(cv, X("OY", 160, (250, 246, 236), 500), CX, 985, t, 12.015, 0.34, al)
        if t >= 12.815:
            pop(cv, G("ZAXIRA", 118, 800), CX, 420, t, 12.815, 0.34, al)
        if t >= 13.215:
            pill = card(900, 84, 42, 30, 120, 20, 10, 0.5)
            pop(cv, pill, CX, 1318, t, 13.215, 0.3, al)
            pop(cv, X("ODATDA TAVSIYA QILINADI", 38, (250, 246, 236), 840, "b"), CX, 1318, t, 13.215, 0.3, al)

    # ---------------- F. not at once: a slice of salary flows automatically into the vault
    def sc_auto(cv, t):
        al = win(t, 14.1, 17.35, 0.12, 0.22)
        if al <= 0:
            return
        if t < 15.2:
            pop(cv, BAGL(), CX, 570, t, 14.15, 0.4, al, rise=60)
            pop(cv, X("BIRDANIGA", 100, (250, 246, 236), 860), CX, 800, t, 14.2, 0.3, al)
            if t >= 14.672:
                p = (t - 14.672) / 0.18
                put(cv, cross(440, RED2, 34), CX, 580, al * clamp(p * 3), 1 + 1.2 * (1 - ease_out_cubic(p)))
            return
        k = clamp((t - 15.17) / 0.3)
        bar_c = card(900, 130, 44, 30, 100, 28, 18, 0.55)
        put(cv, bar_c, CX, 400, al * k)
        put(cv, X("MAOSH", 62, (250, 246, 236), 400), 300, 400, al * k)
        seg_x0, seg_y0 = 832, 400
        move = ease_in_out((t - 15.62) / 0.62)
        lift = ease_out_cubic((t - 15.30) / 0.3)
        sx, sy = lerp(seg_x0, CX, move), lerp(seg_y0, 740, move)
        if t >= 15.30:
            put(cv, SEG(True), sx, sy - 18 * lift * (1 - move), al, (1 + 0.06 * lift) * (1 - 0.35 * move))
        else:
            put(cv, SEG(False), seg_x0, seg_y0, al * k)
        if t >= 15.5:
            kv = clamp((t - 15.5) / 0.35)
            vault(cv, CX, 740, 300, t, t * 20, 0.0, al * kv)
            put(cv, ring(380, clamp((t - 16.3) / 0.9) * 0.55 + 0.02, TEAL, (255, 255, 255, 30), 14), CX, 740, al * kv)
        if t >= 16.272:
            pop(cv, loop_icon(72), 285, 520, t, 16.272, 0.3, al, 1.0)
            pop(cv, X("AVTOMATIK", 66, (244, 196, 92), 560), 640, 520, t, 16.272, 0.3, al)
            for j in range(6):
                tt = (t - 16.4 - j * 0.28) % 1.4
                if tt < 0.6 and t > 16.4 + j * 0.28:
                    y = lerp(620, 690, tt / 0.6)
                    put(cv, coin(48, mark=""), CX + (j % 3 - 1) * 24, y, al * (1 - tt / 0.6) * 0.95)
        if t >= 17.0:
            sparks(cv, t, 17.0, CX, 740, 22, (255, 214, 120), 11, 0.7, 330, 6)

    # ---------------- G. not for income: calm
    def sc_calm(cv, t):
        al = win(t, 17.3, 20.3, 0.12, 0.22)
        if al <= 0:
            return
        if t < 19.2:
            pts = curve(lambda x: 830 - (x - 140) * 0.42 + 34 * math.sin(x / 55.0), 140, 940, 40)
            fade = 1 - 0.65 * ease_out_cubic((t - 18.54) / 0.3)
            pop(cv, X("DAROMAD", 64, (250, 246, 236), 700), CX, 400, t, 17.64, 0.3, al * fade)
            poly(cv, pts, (244, 196, 92), 26, prog(t, 17.84, 0.7), al * fade)
            if t >= 18.54:
                p = (t - 18.54) / 0.18
                put(cv, cross(440, RED2, 36), CX, 650, al * clamp(p * 3), 1 + 1.2 * (1 - ease_out_cubic(p)))
            return
        k = ease_out_cubic((t - 19.14) / 0.5)
        breathe = 1 + 0.04 * math.sin((t - 19.14) * 3.2)
        for rr, aa in ((680, 0.20), (540, 0.30)):
            put(cv, ring(rr, 1.0, TEAL, (255, 255, 255, 0), 10), CX, 600, al * k * aa, breathe * (rr / 700))
        put(cv, glow(shield_icon(340), TEAL, 36, 1.1), CX, 595, al * k, breathe * (0.85 + 0.15 * k))
        pop(cv, gtext("XOTIRJAMLIK", 98, (214, 255, 248), (96, 210, 196)), CX, 840, t, 19.2, 0.4, al)

    # ---------------- H. call to action: write it in the comments
    def sc_cta(cv, t):
        al = win(t, 20.2, 99, 0.12, 0.2)
        if al <= 0:
            return
        pop(cv, rrect(380, 64, 32, (244, 196, 92)), CX, 385, t, 20.3, 0.3, al)
        pop(cv, X("IZOHDA YOZ", 40, (30, 24, 12), 340), CX, 385, t, 20.3, 0.3, al)
        card_ = card(920, 250, 50, 30, 110, 30, 22, 0.6)
        pop(cv, card_, CX, 555, t, 20.4, 0.4, al, rise=50)
        pop(cv, disc(96, (244, 196, 92)), 170, 495, t, 20.5, 0.3, al)
        pop(cv, person(60, (40, 30, 12)), 170, 502, t, 20.5, 0.3, al)
        pop(cv, X("sen", 44, (190, 186, 176), 300, "b"), 270, 490, t, 20.55, 0.3, al)
        pop(cv, X("Zaxiram:", 70, (250, 246, 236), 460), 325, 590, t, 20.7, 0.3, al)
        if int(t * 2.4) % 2 == 0 and t > 21.0:
            put(cv, rrect(8, 72, 3, (244, 196, 92)), 548, 590, al)
        if t >= 21.4:
            put(cv, X("oy", 70, (150, 146, 138), 160), 625, 590, al * clamp((t - 21.4) / 0.3))
        if t >= 22.342:
            pop(cv, GG("NECHA OY?", 150, 22, 1.2), CX, 760, t, 22.342, 0.42, al)
        if t >= 22.9:
            pill = card(760, 92, 46, 30, 120, 20, 10, 0.5)
            pop(cv, pill, CX, 1322, t, 22.9, 0.3, al)
            put(cv, plane_icon(50), 250, 1322, al * clamp((t - 22.9) / 0.3))
            pop(cv, X("Do'stingga ham yubor", 44, (250, 246, 236), 600, "b"), 590, 1322, t, 22.9, 0.3, al)

    cam = (Cam(1.04).key(2.8, 1.07, 0, 20).key(6.2, 1.05, 0, -6).key(7.7, 1.07).key(10.4, 1.04).key(11.0, 1.10)
           .key(12.9, 1.06).key(14.2, 1.05, 0, 12).key(17.3, 1.07, -14, 0).key(20.2, 1.04).key(24.4, 1.10))
    cam.shake(3.207, 22, 0.6).punch(9.815, 0.04).punch(11.015, 0.07).punch(11.615, 0.06).shake(12.0, 16, 0.7)
    cam.shake(14.672, 14, 0.5).shake(16.9, 8, 0.4)

    def tint(t):
        k = ease_in_out((t - 19.1) / 0.7)
        return (lerp(1.04, 0.90, k), 1.0, lerp(0.94, 1.10, k))

    caps = lambda cv, t: captions(cv, tim, t, y=1405, size=72, maxw=940, n=3)
    def host_back(cv, t):
        if not (10.4 <= t <= 14.25):
            host.draw(cv, t)

    def host_front(cv, t):
        if 10.4 <= t <= 14.25:
            host.draw(cv, t)

    return PremiumReel(tim, [host_back, sc_hook, sc_bills, sc_one, sc_calc, sc_vault, host_front, sc_auto, sc_calm, sc_cta], world="gold", cam=cam,
                       seed=17, bokeh_n=44, vignette=0.55, grain=0.45, bloom=0.30, tint=tint,
                       flashes=[(6.15, 0.12), (12.4, 0.22)], chroma_at=[(3.207, 14, 0.35), (6.15, 12, 0.25), (11.015, 10, 0.3)],
                       whips=[(2.78, 0.30, 90, 90), (6.15, 0.26, 110, 90), (7.62, 0.26, 80, 0), (10.45, 0.28, 90, 90), (14.15, 0.30, 100, 0), (17.3, 0.28, 90, 0), (20.2, 0.30, 90, 90)],
                       sweeps=[(7.5, 0.55), (14.05, 0.6), (19.1, 0.7)],
                       top=[caps], disclaimer="Bu umumiy ma‘lumot, shaxsiy maslahat emas.")


# ----------------------------------------------------------------------------- sound design
def sfx(tim):
    w = tim.ws
    ev = [(0.02, "whoosh", 0.55)]
    ev += [(0.1 + i * 0.11, "tick", 0.30) for i in range(22)]
    ev += [(2.58, "thump", 0.95), (2.78, "whoosh", 0.5), (3.207, "stamp", 0.95), (3.207, "glitch", 0.5)]
    ev += [(7.5, "whoosh", 0.35), (4.306, "whoosh", 0.4), (4.4, "pop", 0.7), (4.806, "pop", 0.7), (5.207, "pop", 0.7)]
    ev += [(6.1, "whoosh_dn", 0.5), (6.3, "pop", 0.7), (6.906, "ding", 0.55)]
    ev += [(8.082, "pop", 0.5), (8.40, "pop", 0.5), (8.72, "pop", 0.5), (9.04, "pop", 0.5)]
    ev += [(9.15 + i * 0.07, "tick", 0.25) for i in range(8)] + [(9.82, "coin", 0.8), (10.0, "coin", 0.6)]
    ev += [(11.0, "riser:1.6", 0.8), (11.015, "impact", 0.95), (11.615, "impact", 0.8)]
    ev += [(12.0, "clank", 0.9), (12.1, "whoosh", 0.6), (12.35, "sparkle", 0.9), (12.4, "ding", 0.75)]
    ev += [(14.17, "whoosh", 0.45), (14.672, "stamp", 0.85), (15.17, "whoosh", 0.4), (15.9, "whoosh", 0.35)]
    ev += [(16.4 + i * 0.28, "coin", 0.5) for i in range(5)] + [(16.9, "clank", 0.7), (17.0, "sparkle", 0.6)]
    ev += [(17.64, "pop", 0.5), (18.54, "stamp", 0.7), (19.14, "whoosh", 0.4), (19.3, "ding", 0.6), (19.35, "sparkle", 0.6)]
    ev += [(20.3, "pop", 0.6), (20.4, "whoosh", 0.4), (22.342, "ding", 0.65), (22.4, "sparkle", 0.7), (22.9, "pop", 0.6)]
    ev += [(tim.end0, "whoosh", 0.4), (tim.end0 + 0.1, "ding", 0.5)]
    return ev
