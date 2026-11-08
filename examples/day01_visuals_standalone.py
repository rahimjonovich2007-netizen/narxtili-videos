"""Kinetic-text Reel, 1080x1920 @30 fps: Narx Tili, day 1 'Chap raqam effekti'.
Usage: visuals.py stills t1 t2 ...   -> PNGs in work/stills
       visuals.py full               -> out/day1_chap_raqam.mp4 (+ cover.jpg)
"""
import json
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

D = "/home/claude/narxtili/day1"
W, H, FPS = 1080, 1920, 30
NAVY, AMBER, CREAM, SLATE, CARD = (11, 31, 58), (255, 176, 32), (247, 243, 234), (59, 79, 107), (21, 46, 82)
FONT = {"xb": "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
        "b": "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
        "sb": "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"}

TIM = json.load(open(f"{D}/work/timing.json"))
words = TIM["words"]
segs = {s["name"]: s for s in TIM["segs"]}
END0 = TIM["last_word_end"] + 0.55
T_TOTAL = END0 + 2.3
NF = int(round(T_TOTAL * FPS))


def ws(i): return words[i]["s2"]
def we(i): return words[i]["e2"]
def S(n): return segs[n]["s2"]
def E(n): return segs[n]["e2"]


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out_cubic(p): p = clamp(p); return 1 - (1 - p) ** 3
def ease_in_out(p): p = clamp(p); return p * p * (3 - 2 * p)
def ease_out_back(p, s=1.4):
    p = clamp(p)
    return 1 + (s + 1) * (p - 1) ** 3 + s * (p - 1) ** 2


@lru_cache(None)
def F(w, size): return ImageFont.truetype(FONT[w], size)


@lru_cache(None)
def rich(parts, size, weight="xb"):
    font = F(weight, size)
    widths = [font.getlength(p[0]) for p in parts]
    asc, desc = font.getmetrics()
    img = Image.new("RGBA", (int(sum(widths)) + 16, asc + desc + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 8.0
    for (txt, col), w in zip(parts, widths):
        d.text((x, 8), txt, font=font, fill=col + (255,))
        x += w
    return img


def fit(parts, size, weight="xb", maxw=900):
    s = size
    while s > 28:
        layer = rich(parts, s, weight)
        if layer.width - 16 <= maxw:
            return layer
        s -= 4
    return rich(parts, s, weight)


def txt(s, size, col=CREAM, weight="xb", maxw=900): return fit(((s, col),), size, weight, maxw)


def put(cv, layer, cx, cy, alpha=1.0, scale=1.0):
    if alpha <= 0.004:
        return
    if abs(scale - 1.0) > 1e-3:
        w, h = layer.size
        layer = layer.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR)
    if alpha < 0.999:
        r, g, b, a = layer.split()
        layer = Image.merge("RGBA", (r, g, b, a.point(lambda v: int(v * alpha))))
    w, h = layer.size
    x, y = int(round(cx - w / 2)), int(round(cy - h / 2))
    x = max(0, min(W - w, x))
    y = max(0, min(H - h, y))
    cv.alpha_composite(layer, (x, y))


def item(cv, layer, cx, cy, t, t0, al, yo, dur=0.30, base=1.0, rise=34):
    p = (t - t0) / dur
    if p <= 0:
        return
    e = ease_out_cubic(p)
    sc = 0.88 + 0.12 * clamp(ease_out_back(p, 1.2), 0, 1.2)
    put(cv, layer, cx, cy + yo + (1 - e) * rise, al * e * base, sc)


def vis(t, a, b, fo=0.14):
    if t < a or t >= b:
        return None
    al = clamp((b - t) / fo)
    return al, -(1 - al) * 28


@lru_cache(None)
def logo(size, bubble, ncol, dot):
    s4 = size * 4
    sc = s4 / 400.0
    im = Image.new("RGBA", (s4, s4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    P = lambda x, y: (x * sc, (y - 11) * sc)
    d.rounded_rectangle([P(40, 70), P(360, 280)], radius=56 * sc, fill=bubble + (255,))
    d.polygon([P(190, 280), P(96, 352), P(112, 280)], fill=bubble + (255,))
    pts = [(130, 235), (130, 115), (172, 115), (236, 191), (236, 115), (270, 115), (270, 235),
           (228, 235), (164, 159), (164, 235)]
    d.polygon([P(*p) for p in pts], fill=ncol + (255,))
    cx, cy = P(88, 112)
    r = 14 * sc
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=dot + (255,))
    return im.resize((size, size), Image.LANCZOS)


@lru_cache(None)
def rrect(w, h, r, fill, outline=None, ow=0):
    s = 2
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=r * s, fill=fill + (255,),
                        outline=(outline + (255,)) if outline else None, width=ow * s)
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def chip(text, fg, bg, size=44):
    t = txt(text, size, fg, "xb", maxw=600)
    w, h = t.width + 64, t.height + 18
    base = rrect(w, h, h // 2, bg).copy()
    base.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2))
    return base


@lru_cache(None)
def tag_layer():
    num = txt("99 000", 250, NAVY, "xb", maxw=680)
    cur = txt("so‘m", 84, SLATE, "sb")
    w, h = 820, 70 + num.height - 30 + cur.height + 60
    im = rrect(w, h, 48, CREAM).copy()
    ImageDraw.Draw(im).ellipse([62, 46, 104, 88], fill=NAVY + (255,))
    im.alpha_composite(num, ((w - num.width) // 2, 70))
    im.alpha_composite(cur, ((w - cur.width) // 2, 70 + num.height - 30))
    return im.rotate(4, resample=Image.BICUBIC, expand=True)


@lru_cache(None)
def bookmark(w, h):
    s = 4
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(0, 0), (w, 0), (w, h), (w / 2, h * 0.72), (0, h)]
    d.polygon([(x * s, y * s) for x, y in pts], fill=AMBER + (255,))
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def arrow_head():
    s = 4
    im = Image.new("RGBA", (44 * s, 64 * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).polygon([(0, 0), (44 * s, 32 * s), (0, 64 * s)], fill=AMBER + (255,))
    return im.resize((44, 64), Image.LANCZOS)


def draw_bar(cv, cx, base, w, h, color, alpha=1.0):
    h = int(h)
    if h < 6:
        return
    s = 2
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=26 * s, fill=color + (255,),
                                         corners=(True, True, False, False))
    put(cv, im.resize((w, h), Image.LANCZOS), cx, base - h / 2, alpha)


@lru_cache(None)
def build_bg():
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2)
    t = np.clip(r * 1.6, 0, 1)[..., None]
    c0, c1 = np.array([19, 46, 86], float), np.array([8, 21, 41], float)
    base = c0 * (1 - t) + c1 * t
    # static dither so the smooth navy gradient survives Instagram's re-compression without banding
    base = base + np.random.default_rng(5).normal(0, 1.3, (H, W, 1))
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")


@lru_cache(None)
def dots():
    im = Image.new("RGBA", (W + 60, H + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y in range(0, H + 60, 60):
        for x in range(0, W + 60, 60):
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=CREAM + (26,))
    return im


# ------------------------------------------------------------------ scene windows
A_HOOK, B_HOOK = 0.0, S("shop") - 0.10
A_SHOP, B_SHOP = B_HOOK - 0.08, S("left") - 0.10
A_LEFT, B_LEFT = B_SHOP - 0.08, S("n99") - 0.10
A_NUM, B_NUM = B_LEFT - 0.08, S("diff") - 0.10
A_DIFF, B_DIFF = B_NUM - 0.08, S("term") - 0.10
A_TERM, B_TERM = B_DIFF - 0.08, S("seller") - 0.10
A_PAIR, B_PAIR = B_TERM - 0.08, S("cta") - 0.10
A_CTA, B_CTA = B_PAIR - 0.08, END0


def sc_hook(cv, t):
    v = vis(t, A_HOOK, B_HOOK)
    if not v:
        return
    al, yo = v
    p0 = clamp(t / 0.32)
    put(cv, txt("99 000", 340, AMBER, "xb"), 540, 640 + yo + (1 - ease_out_cubic(p0)) * 26,
        al * (0.55 + 0.45 * ease_out_cubic(p0)), 0.9 + 0.1 * clamp(ease_out_back(p0, 1.1), 0, 1.2))
    item(cv, txt("so‘m", 120, CREAM, "sb"), 540, 880, t, 0.12, al, yo, base=0.8)
    item(cv, fit((("Nega ", CREAM), ("100 000", AMBER), (" emas?", CREAM)), 124, "xb"), 540, 1110, t,
         max(0.25, ws(2) - 0.12), al, yo)


def sc_shop(cv, t):
    v = vis(t, A_SHOP, B_SHOP)
    if not v:
        return
    al, yo = v
    item(cv, txt("Do‘konda narx:", 76, CREAM, "sb"), 540, 520, t, A_SHOP + 0.10, al, yo, base=0.85)
    item(cv, tag_layer(), 540, 900, t, A_SHOP + 0.18, al, yo, dur=0.40)


def sc_left(cv, t):
    v = vis(t, A_LEFT, B_LEFT)
    if not v:
        return
    al, yo = v
    item(cv, txt("Miyamiz raqamni", 88, CREAM, "xb"), 540, 580, t, A_LEFT + 0.10, al, yo)
    item(cv, fit((("chapdan", AMBER), (" o‘qiydi.", CREAM)), 88, "xb"), 540, 690, t, max(A_LEFT + 0.14, ws(11) - 0.10), al, yo)
    xs = [175, 340, 575, 740, 905]
    t_s, t_e = ws(11), we(12)
    q = ease_in_out((t - t_s) / max(0.1, t_e - t_s))
    sweep_x = 105 + 870 * q
    for i, ch in enumerate("99000"):
        lit = 1.0 if i == 0 else clamp((sweep_x - (xs[i] - 70)) / 60.0) * 0.65 + 0.35
        col = AMBER if i == 0 else CREAM
        sc_extra = 1.0 + (0.08 * np.sin(clamp((t - t_s) / 0.5) * np.pi) if i == 0 else 0)
        p = (t - (A_LEFT + 0.2)) / 0.3
        if p > 0:
            put(cv, txt(ch, 224, col, "xb"), xs[i], 925 + yo + (1 - ease_out_cubic(p)) * 30,
                al * ease_out_cubic(p) * lit, (0.9 + 0.1 * ease_out_cubic(p)) * sc_extra)
    bw = int(870 * q)
    if t > A_LEFT + 0.2:
        put(cv, rrect(870, 14, 7, SLATE), 540, 1090 + yo, al * 0.5)
    if bw >= 8:
        put(cv, rrect(bw, 14, 7, AMBER), 105 + bw / 2, 1090 + yo, al)
        put(cv, arrow_head(), 105 + bw + 14, 1090 + yo, al)


def sc_num(cv, t):
    v = vis(t, A_NUM, B_NUM)
    if not v:
        return
    al, yo = v
    item(cv, txt("99", 330, AMBER, "xb"), 540, 610, t, A_NUM + 0.08, al, yo, dur=0.34)
    item(cv, txt("90 ming bo‘lib tuyuladi", 70, CREAM, "sb"), 540, 810, t, max(A_NUM + 0.12, ws(14) - 0.10), al, yo)
    if t > S("n100") - 0.2:
        put(cv, rrect(700, 6, 3, SLATE), 540, 930 + yo, al * clamp((t - (S("n100") - 0.2)) / 0.25))
    item(cv, txt("100", 330, CREAM, "xb"), 540, 1090, t, S("n100") - 0.06, al, yo, dur=0.34)
    item(cv, txt("yuz ming", 70, AMBER, "sb"), 540, 1290, t, max(S("n100") + 0.05, ws(18) - 0.10), al, yo)


def sc_diff(cv, t):
    v = vis(t, A_DIFF, B_DIFF)
    if not v:
        return
    al, yo = v
    item(cv, fit((("Farq atigi ", CREAM), ("1 000 so‘m", AMBER), (",", CREAM)), 80, "xb"), 540, 440, t, A_DIFF + 0.08, al, yo)
    t_l = max(A_DIFF + 0.2, ws(23) - 0.10)
    item(cv, txt("lekin miyaga ancha katta tuyuladi.", 60, CREAM, "sb"), 540, 530, t, t_l, al, yo, base=0.92)
    base_y = 1330
    pb = clamp((t - (A_DIFF + 0.15)) / 0.4)
    if pb > 0:
        e = ease_out_cubic(pb)
        draw_bar(cv, 330, base_y + yo, 240, 460 * e, CREAM, al)
        hb = 480 + 240 * ease_out_back(clamp((t - ws(24)) / 0.9), 1.1) if t > ws(24) else 480
        draw_bar(cv, 650, base_y + yo, 240, hb * e, AMBER, al)
        put(cv, rrect(760, 6, 3, SLATE), 490, base_y + 14 + yo, al * 0.6 * e)
        put(cv, txt("99 000", 52, CREAM, "b"), 330, base_y + 62 + yo, al * e * 0.9)
        put(cv, txt("100 000", 52, AMBER, "b"), 650, base_y + 62 + yo, al * e * 0.9)
        if t > ws(24) + 0.35:
            g = clamp((t - ws(24) - 0.35) / 0.3)
            ghost_top = base_y - 480
            dash = Image.new("RGBA", (300, 8), (0, 0, 0, 0))
            dd = ImageDraw.Draw(dash)
            for x in range(0, 300, 30):
                dd.rectangle([x, 0, x + 16, 7], fill=AMBER + (255,))
            put(cv, dash, 650, ghost_top + yo, al * g * 0.85)
            put(cv, txt("haqiqiy", 40, AMBER, "sb"), 905, ghost_top + yo, al * g * 0.9)
            put(cv, txt("miyada", 46, NAVY, "xb"), 650, base_y - hb + 58 + yo, al * g)


def sc_term(cv, t):
    v = vis(t, A_TERM, B_TERM)
    if not v:
        return
    al, yo = v
    item(cv, txt("Bunga", 74, CREAM, "sb"), 540, 560, t, A_TERM + 0.10, al, yo, base=0.85)
    item(cv, txt("chap raqam", 176, AMBER, "xb"), 540, 770, t, max(A_TERM + 0.15, ws(29) - 0.12), al, yo, dur=0.34)
    t_e = max(A_TERM + 0.25, ws(31) - 0.12)
    item(cv, txt("effekti", 176, AMBER, "xb"), 540, 945, t, t_e, al, yo, dur=0.34)
    uw = int(560 * ease_out_cubic((t - t_e - 0.15) / 0.5))
    if uw > 8:
        put(cv, rrect(uw, 12, 6, AMBER), 540, 1050 + yo, al)
    item(cv, txt("deyiladi.", 74, CREAM, "sb"), 540, 1140, t, ws(32) - 0.10, al, yo, base=0.85)
    item(cv, txt("Manba: Thomas va Morwitz, 2005", 40, CREAM, "sb", maxw=860), 540, 1300, t, ws(32) + 0.15, al, yo, base=0.6)
    item(cv, txt("Journal of Consumer Research", 36, CREAM, "sb", maxw=860), 540, 1352, t, ws(32) + 0.25, al, yo, base=0.5)


def sc_pair(cv, t):
    v = vis(t, A_PAIR, B_PAIR)
    if not v:
        return
    al, yo = v
    item(cv, rrect(900, 350, 44, CARD, SLATE, 3), 540, 700, t, A_PAIR + 0.08, al, yo, dur=0.35)
    item(cv, chip("SOTUVCHI", NAVY, AMBER, 44), 540, 600, t, A_PAIR + 0.14, al, yo)
    item(cv, txt("ishlat", 170, CREAM, "xb"), 540, 765, t, max(S("seller") + 0.05, ws(35) - 0.12), al, yo, dur=0.34)
    item(cv, rrect(900, 420, 44, CARD, SLATE, 3), 540, 1200, t, S("buyer") - 0.10, al, yo, dur=0.35)
    item(cv, chip("XARIDOR", NAVY, CREAM, 44), 540, 1080, t, S("buyer") - 0.05, al, yo)
    item(cv, txt("haqiqiy narxni", 98, AMBER, "xb"), 540, 1210, t, max(S("buyer") + 0.05, ws(38) - 0.10), al, yo)
    item(cv, txt("hisobla", 98, AMBER, "xb"), 540, 1325, t, max(S("buyer") + 0.2, ws(40) - 0.20), al, yo)


def sc_cta(cv, t):
    v = vis(t, A_CTA, B_CTA, fo=0.25)
    if not v:
        return
    al, yo = v
    bump = 1.0 + 0.07 * np.sin(clamp((t - ws(41)) / 0.45) * np.pi)
    item(cv, bookmark(190, 250), 540, 600, t, A_CTA + 0.10, al, yo, dur=0.36)
    if t > ws(41):
        pass
    item(cv, txt("Saqlab qo‘y", 168, AMBER, "xb"), 540, 905, t, max(A_CTA + 0.15, ws(41) - 0.12), al, yo, dur=0.34)
    item(cv, txt("keyingi safar", 76, CREAM, "sb"), 540, 1070, t, ws(43) - 0.10, al, yo, base=0.9)
    item(cv, txt("do‘konda eslaysan.", 76, CREAM, "sb"), 540, 1165, t, ws(45) - 0.10, al, yo, base=0.9)


def sc_end(cv, t):
    if t < END0:
        return
    lt = t - END0
    fo = clamp((T_TOTAL - t) / 0.25)
    item(cv, logo(300, AMBER, NAVY, NAVY), 540, 650, lt, 0.0, fo, 0, dur=0.45)
    item(cv, txt("Narx Tili", 132, CREAM, "xb"), 540, 905, lt, 0.12, fo, 0)
    item(cv, txt("Iqtisod va marketing, oddiy tilda", 52, CREAM, "sb", maxw=880), 540, 1030, lt, 0.24, fo, 0, base=0.8)
    item(cv, txt("@narxtili", 74, AMBER, "xb"), 540, 1150, lt, 0.36, fo, 0)
    item(cv, txt("Har 2 kunda bitta Reels", 46, CREAM, "sb"), 540, 1260, lt, 0.48, fo, 0, base=0.6)


def draw(t):
    cv = build_bg().copy()
    ox, oy = int((t * 9) % 60), int((t * 6) % 60)
    cv.alpha_composite(dots().crop((ox, oy, ox + W, oy + H)))
    hdr = clamp((END0 - 0.2 - t) / 0.25) if t > END0 - 0.45 else 1.0
    if hdr > 0:
        tl = txt("Narx Tili", 38, CREAM, "b")
        total = 58 + 14 + tl.width
        x0 = 540 - total / 2
        put(cv, logo(58, AMBER, NAVY, NAVY), x0 + 29, 300, hdr * 0.9)
        put(cv, tl, x0 + 72 + tl.width / 2, 300, hdr * 0.9)
        put(cv, rrect(900, 6, 3, SLATE), 540, 1488, hdr * 0.5)
        pw = int(900 * clamp(t / END0))
        if pw >= 6:
            put(cv, rrect(pw, 6, 3, AMBER), 90 + pw / 2, 1488, hdr * 0.9)
    for fn in (sc_hook, sc_shop, sc_left, sc_num, sc_diff, sc_term, sc_pair, sc_cta, sc_end):
        fn(cv, t)
    return cv


def render_frame(i):
    return draw(i / FPS).convert("RGB").tobytes()


if __name__ == "__main__":
    mode = sys.argv[1]
    os.makedirs(f"{D}/work/stills", exist_ok=True)
    if mode == "stills":
        for tv in sys.argv[2:]:
            draw(float(tv)).convert("RGB").save(f"{D}/work/stills/t{float(tv):05.2f}.png")
        print("stills done; T_TOTAL", round(T_TOTAL, 3), "frames", NF)
    else:
        os.makedirs(f"{D}/out", exist_ok=True)
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
               "-i", "-", "-i", f"{D}/work/mix.wav",
               "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
               "-c:v", "libx264", "-preset", "slow", "-crf", "11", "-profile:v", "high", "-level", "4.2",
               "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-r", str(FPS),
               "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
               "-t", f"{T_TOTAL:.3f}", "-movflags", "+faststart", f"{D}/out/day1_chap_raqam.mp4"]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        with Pool(2) as pool:
            for k, fr in enumerate(pool.imap(render_frame, range(NF), chunksize=6)):
                pr.stdin.write(fr)
        pr.stdin.close()
        pr.wait()
        draw(2.95).convert("RGB").save(f"{D}/out/day1_cover.jpg", quality=95, subsampling=0)
        print("rendered", NF, "frames")
