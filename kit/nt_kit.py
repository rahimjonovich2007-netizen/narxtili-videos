"""Narx Tili video kit: drawing, animation and render helpers for 1080x1920 @30 fps Reels.

A day's `scenes.py` does `from nt_kit import *`, defines `build(tim) -> Reel`, and render.py does the rest.
Everything is drawn with PIL (anti-aliased through supersampling) and piped into ffmpeg.
Design rule: every video gets its OWN look (theme / background / overlay / visual metaphor / motion),
but keeps the brand frame: header logo, progress bar, safe zone, end card.
"""
import json
import math
import os
import subprocess
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
END_PAD, TAIL = 0.55, 2.3          # seconds: last spoken word -> end card -> end of video
SAFE_Y0, SAFE_Y1, SAFE_X = 250, 1500, 90   # keep text/objects inside this box (Instagram UI overlays the rest)

NAVY, AMBER, CREAM, SLATE, CARD = (11, 31, 58), (255, 176, 32), (247, 243, 234), (59, 79, 107), (21, 46, 82)
WHITE, RED, GREEN = (255, 255, 255), (232, 80, 70), (64, 190, 120)

_FONTS = {
    "xb": ["/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "b": ["/usr/share/fonts/opentype/inter/Inter-Bold.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "sb": ["/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
}

# ----------------------------------------------------------------------------- themes
THEMES = {
    "navy":  dict(bg0=(19, 46, 86), bg1=(8, 21, 41), fg=CREAM, acc=AMBER, mut=SLATE, card=CARD, ink=NAVY, dot=CREAM, dota=26, lb=AMBER, ln=NAVY),
    "ink":   dict(bg0=(24, 26, 44), bg1=(6, 8, 16), fg=CREAM, acc=AMBER, mut=(72, 78, 104), card=(32, 36, 60), ink=(6, 8, 16), dot=CREAM, dota=22, lb=AMBER, ln=NAVY),
    "slate": dict(bg0=(56, 80, 114), bg1=(24, 38, 62), fg=CREAM, acc=AMBER, mut=(104, 126, 158), card=(38, 56, 86), ink=NAVY, dot=CREAM, dota=24, lb=AMBER, ln=NAVY),
    "cream": dict(bg0=(251, 248, 241), bg1=(234, 227, 211), fg=NAVY, acc=(222, 128, 0), mut=(170, 164, 148), card=WHITE, ink=NAVY, dot=NAVY, dota=16, lb=NAVY, ln=AMBER),
    "amber": dict(bg0=(255, 198, 74), bg1=(244, 156, 18), fg=NAVY, acc=NAVY, mut=(205, 128, 8), card=(255, 228, 156), ink=NAVY, dot=NAVY, dota=18, lb=NAVY, ln=AMBER),
}


class _Theme:
    pass


TH = _Theme()


def set_theme(name):
    TH.__dict__.update(THEMES[name])
    TH.name = name


set_theme("navy")


# ----------------------------------------------------------------------------- math / easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, p): return a + (b - a) * p
def ease_out_cubic(p): p = clamp(p); return 1 - (1 - p) ** 3
def ease_in_cubic(p): p = clamp(p); return p ** 3
def ease_in_out(p): p = clamp(p); return p * p * (3 - 2 * p)
def ease_out_back(p, s=1.4): p = clamp(p); return 1 + (s + 1) * (p - 1) ** 3 + s * (p - 1) ** 2
def ease_out_elastic(p):
    p = clamp(p)
    if p in (0, 1): return p
    return 2 ** (-9 * p) * math.sin((p * 10 - 0.75) * (2 * math.pi) / 3) + 1
def mixc(c0, c1, p): return tuple(int(round(lerp(a, b, clamp(p)))) for a, b in zip(c0, c1))
def fmt(n): return f"{int(round(n)):,}".replace(",", " ")      # 100000 -> "100 000"
def prog(t, a, dur): return clamp((t - a) / dur)                # 0..1 progress of an action starting at a


# ----------------------------------------------------------------------------- timing
class Timing:
    """Word/sentence times (after silence trimming) from work/timing.json written by audio.py."""

    def __init__(self, path):
        d = json.load(open(path))
        self.words, self.segs = d["words"], d["segs"]
        self.by = {s["name"]: s for s in self.segs}
        self.last = d["last_word_end"]
        self.end0 = self.last + END_PAD
        self.total = self.end0 + TAIL

    def ws(self, i): return self.words[i]["s2"]
    def we(self, i): return self.words[i]["e2"]
    def seg(self, k): return self.segs[k] if isinstance(k, int) else self.by[k]
    def S(self, k): return self.seg(k)["s2"]          # sentence start (k = index or name)
    def E(self, k): return self.seg(k)["e2"]
    def first(self, k): return self.seg(k)["a"]       # index of the sentence's first word
    def lastw(self, k): return self.seg(k)["b"]
    def find(self, text, start=0):
        """index of the first word at/after `start` whose text contains `text` (case-insensitive)"""
        for i in range(start, len(self.words)):
            if text.lower() in self.words[i]["t"].lower():
                return i
        raise KeyError(text)

    @property
    def nf(self): return int(round(self.total * FPS))


# ----------------------------------------------------------------------------- text
def _fp(w):
    for p in _FONTS[w]:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("no usable font")


@lru_cache(None)
def F(w, size): return ImageFont.truetype(_fp(w), size)


@lru_cache(None)
def rich(parts, size, weight="xb"):
    """parts = ((text, (r,g,b)), ...) -> one RGBA text layer with mixed colours"""
    font = F(weight, size)
    widths = [font.getlength(p[0]) for p in parts]
    asc, desc = font.getmetrics()
    img = Image.new("RGBA", (int(sum(widths)) + 16, asc + desc + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 8.0
    for (t, col), w in zip(parts, widths):
        d.text((x, 8), t, font=font, fill=tuple(col) + (255,))
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


def txt(s, size, col=None, weight="xb", maxw=900): return fit(((s, col or TH.fg),), size, weight, maxw)


def txt2(a, b, size, ca=None, cb=None, weight="xb", maxw=900):
    """two-colour text: a in ca, b in cb"""
    return fit(((a, ca or TH.fg), (b, cb or TH.acc)), size, weight, maxw)


# ----------------------------------------------------------------------------- compositing
def put(cv, layer, cx, cy, alpha=1.0, scale=1.0, rot=0.0):
    """Composite an RGBA layer centred at (cx, cy); scale, rotate (deg, counter-clockwise), fade; clipped to canvas."""
    if alpha <= 0.004 or scale <= 0.01:
        return
    if abs(scale - 1.0) > 1e-3:
        w, h = layer.size
        layer = layer.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR)
    if abs(rot) > 0.05:
        layer = layer.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = layer.getchannel("A").point(lambda v: int(v * alpha))
        layer = layer.copy()
        layer.putalpha(a)
    w, h = layer.size
    x, y = int(round(cx - w / 2)), int(round(cy - h / 2))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    if (x0, y0, x1, y1) != (x, y, x + w, y + h):
        layer = layer.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    cv.alpha_composite(layer, (x0, y0))


def item(cv, layer, cx, cy, t, t0, al=1.0, yo=0.0, dur=0.30, base=1.0, rise=34):
    """standard entrance: fade + rise + tiny overshoot pop. `al`,`yo` come from vis()."""
    p = (t - t0) / dur
    if p <= 0:
        return
    e = ease_out_cubic(p)
    sc = 0.88 + 0.12 * clamp(ease_out_back(p, 1.2), 0, 1.2)
    put(cv, layer, cx, cy + yo + (1 - e) * rise, al * e * base, sc)


def vis(t, a, b, fo=0.14):
    """scene window: returns (alpha, y_offset) while a <= t < b with a short fade/slide at the end, else None"""
    if t < a or t >= b:
        return None
    al = clamp((b - t) / fo)
    return al, -(1 - al) * 28


# ----------------------------------------------------------------------------- shapes
@lru_cache(None)
def rrect(w, h, r, fill, outline=None, ow=0):
    s = 2
    im = Image.new("RGBA", (max(1, w * s), max(1, h * s)), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=r * s, fill=tuple(fill) + (255,),
                                         outline=(tuple(outline) + (255,)) if outline else None, width=ow * s)
    return im.resize((max(1, w), max(1, h)), Image.LANCZOS)


@lru_cache(None)
def disc(d, fill, outline=None, ow=0):
    s = 3
    im = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([0, 0, d * s - 1, d * s - 1], fill=(tuple(fill) + (255,)) if fill else None,
                               outline=(tuple(outline) + (255,)) if outline else None, width=ow * s)
    return im.resize((d, d), Image.LANCZOS)


def bar(cv, cx, base, w, h, color, alpha=1.0, r=26):
    """vertical bar growing up from `base` (rounded top)"""
    h = int(h)
    if h < 6:
        return
    s = 2
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=min(r, h // 2, w // 2) * s,
                                         fill=tuple(color) + (255,), corners=(True, True, False, False))
    put(cv, im.resize((w, h), Image.LANCZOS), cx, base - h / 2, alpha)


def hbar(cv, x0, cy, w, h, color, alpha=1.0):
    """horizontal bar growing right from x0"""
    w = int(w)
    if w < 6:
        return
    put(cv, rrect(w, h, h // 2, tuple(color)), x0 + w / 2, cy, alpha)


def poly(cv, pts, color, width=10, p=1.0, alpha=1.0, caps=True):
    """Polyline drawn up to fraction p of its length (animate p 0->1 to 'draw' lines, arrows, charts)."""
    if p <= 0 or alpha <= 0.004 or len(pts) < 2:
        return
    pts = [(float(x), float(y)) for x, y in pts]
    segl = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    target = sum(segl) * clamp(p)
    out, acc = [pts[0]], 0.0
    for (a, b), L in zip(zip(pts, pts[1:]), segl):
        if acc + L <= target + 1e-6:
            out.append(b)
            acc += L
        else:
            f = (target - acc) / L if L > 0 else 0
            out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
            break
    pad = int(width) + 4
    xs, ys = [q[0] for q in out], [q[1] for q in out]
    x0, y0, x1, y1 = int(min(xs) - pad), int(min(ys) - pad), int(max(xs) + pad), int(max(ys) + pad)
    s = 3
    im = Image.new("RGBA", ((x1 - x0) * s, (y1 - y0) * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    P = [((x - x0) * s, (y - y0) * s) for x, y in out]
    col = tuple(color) + (255,)
    if len(P) > 1:
        d.line(P, fill=col, width=int(width * s), joint="curve")
    if caps:
        r = width * s / 2
        for q in (P[0], P[-1]):
            d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)
    put(cv, im.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0 + x1) / 2, (y0 + y1) / 2, alpha)


def curve(fn, x0, x1, n=60):
    """sample y=fn(x) into a point list for poly()"""
    return [(x0 + (x1 - x0) * i / n, fn(x0 + (x1 - x0) * i / n)) for i in range(n + 1)]


def dashed_line(cv, p0, p1, color, width=6, dash=26, gap=16, p=1.0, alpha=1.0):
    L = math.dist(p0, p1)
    if L < 1:
        return
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
    pos, end = 0.0, L * clamp(p)
    while pos < end:
        e = min(end, pos + dash)
        poly(cv, [(p0[0] + ux * pos, p0[1] + uy * pos), (p0[0] + ux * e, p0[1] + uy * e)], color, width, 1.0, alpha, caps=False)
        pos += dash + gap


# ----------------------------------------------------------------------------- icons (cached RGBA layers)
def _canvas(w, h, s=4): return Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0)), s


@lru_cache(None)
def logo(size, bubble, ncol, dot):
    """Narx Tili bubble logo: speech bubble with an N and a small dot"""
    s4 = size * 4
    sc = s4 / 400.0
    im = Image.new("RGBA", (s4, s4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    P = lambda x, y: (x * sc, (y - 11) * sc)
    d.rounded_rectangle([P(40, 70), P(360, 280)], radius=56 * sc, fill=tuple(bubble) + (255,))
    d.polygon([P(190, 280), P(96, 352), P(112, 280)], fill=tuple(bubble) + (255,))
    pts = [(130, 235), (130, 115), (172, 115), (236, 191), (236, 115), (270, 115), (270, 235), (228, 235), (164, 159), (164, 235)]
    d.polygon([P(*p) for p in pts], fill=tuple(ncol) + (255,))
    cx, cy = P(88, 112)
    r = 14 * sc
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(dot) + (255,))
    return im.resize((size, size), Image.LANCZOS)


@lru_cache(None)
def coin(d=160, col=AMBER, rim=(214, 138, 0), mark="", mark_col=(140, 84, 0)):
    im, s = _canvas(d, d)
    dr = ImageDraw.Draw(im)
    D = d * s
    dr.ellipse([0, 0, D - 1, D - 1], fill=tuple(rim) + (255,))
    dr.ellipse([D * 0.07, D * 0.07, D * 0.93, D * 0.93], fill=tuple(col) + (255,))
    dr.ellipse([D * 0.17, D * 0.17, D * 0.83, D * 0.83], outline=tuple(rim) + (255,), width=int(D * 0.025))
    im = im.resize((d, d), Image.LANCZOS)
    if mark:
        t = txt(mark, int(d * 0.30), mark_col, "xb", maxw=int(d * 0.62))
        im.alpha_composite(t, ((d - t.width) // 2, (d - t.height) // 2))
    return im


@lru_cache(None)
def balloon(d=300, col=AMBER, string=(170, 180, 200)):
    """party balloon (body d wide) with knot and wavy string; total height ~1.75 d"""
    h = int(d * 1.75)
    im, s = _canvas(d, h)
    dr = ImageDraw.Draw(im)
    bh = d * 1.18
    dr.ellipse([0, 0, d * s - 1, bh * s], fill=tuple(col) + (255,))
    kx, ky = d / 2, bh
    dr.polygon([((kx - d * 0.07) * s, (ky + d * 0.07) * s), ((kx + d * 0.07) * s, (ky + d * 0.07) * s), (kx * s, (ky - d * 0.02) * s)],
               fill=tuple(col) + (255,))
    pts = [(kx + math.sin(i / 3.2) * d * 0.05, ky + d * 0.07 + i * (h - ky - d * 0.08) / 24) for i in range(25)]
    dr.line([(x * s, y * s) for x, y in pts], fill=tuple(string) + (255,), width=int(d * 0.012 * s) + 1)
    hl = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([d * 0.18 * s, d * 0.14 * s, d * 0.38 * s, d * 0.42 * s], fill=(255, 255, 255, 80))
    im.alpha_composite(hl)
    return im.resize((d, h), Image.LANCZOS)


@lru_cache(None)
def basket(w=520, h=320, col=(196, 132, 60), dark=(142, 90, 36)):
    """shopping/food basket with handle"""
    hh = int(h * 1.3)
    im, s = _canvas(w, hh)
    dr = ImageDraw.Draw(im)
    top = hh - h
    dr.arc([w * 0.16 * s, 4 * s, w * 0.84 * s, (top + h * 0.5) * s], 180, 360, fill=tuple(dark) + (255,), width=int(w * 0.035 * s))
    dr.polygon([(0, top * s), (w * s, top * s), (w * 0.88 * s, hh * s), (w * 0.12 * s, hh * s)], fill=tuple(col) + (255,))
    dr.rounded_rectangle([(-w * 0.02) * s, top * s, (w * 1.02) * s, (top + h * 0.12) * s], radius=int(h * 0.05 * s), fill=tuple(dark) + (255,))
    for i in range(1, 6):
        x = w * i / 6
        xb = w * 0.12 + w * 0.76 * i / 6
        dr.line([(x * s, (top + h * 0.12) * s), (xb * s, (hh - 2) * s)], fill=tuple(dark) + (255,), width=int(w * 0.012 * s))
    for j in (0.45, 0.75):
        y = top + h * j
        dr.line([((w * 0.04 + (w * 0.08) * (j - 0.12)) * s, y * s), ((w * 0.96 - (w * 0.08) * (j - 0.12)) * s, y * s)],
                fill=tuple(dark) + (255,), width=int(w * 0.012 * s))
    return im.resize((w, hh), Image.LANCZOS)


@lru_cache(None)
def face(d=240, mood="happy", col=AMBER, ink=NAVY):
    """round character face. moods: happy, sad, worried, shock, neutral, wink"""
    im, s = _canvas(d, d)
    dr = ImageDraw.Draw(im)
    D = d * s
    dr.ellipse([0, 0, D - 1, D - 1], fill=tuple(col) + (255,))
    ink4 = tuple(ink) + (255,)
    lw = max(2, int(D * 0.035))
    ey, ex0, ex1, er = D * 0.40, D * 0.33, D * 0.67, D * 0.055
    if mood == "wink":
        dr.arc([ex0 - er * 1.6, ey - er, ex0 + er * 1.6, ey + er * 2], 200, 340, fill=ink4, width=lw)
    else:
        dr.ellipse([ex0 - er, ey - er, ex0 + er, ey + er], fill=ink4)
    r2 = er * (1.5 if mood == "shock" else 1)
    if mood == "shock":
        dr.ellipse([ex0 - r2, ey - r2, ex0 + r2, ey + r2], fill=ink4)
    dr.ellipse([ex1 - r2, ey - r2, ex1 + r2, ey + r2], fill=ink4)
    if mood in ("happy", "wink"):
        dr.arc([D * 0.27, D * 0.40, D * 0.73, D * 0.80], 20, 160, fill=ink4, width=lw)
    elif mood == "sad":
        dr.arc([D * 0.30, D * 0.60, D * 0.70, D * 0.98], 200, 340, fill=ink4, width=lw)
    elif mood == "worried":
        dr.line([(ex0 - D * .07, ey - D * .09), (ex0 + D * .06, ey - D * .14)], fill=ink4, width=lw)
        dr.line([(ex1 + D * .07, ey - D * .09), (ex1 - D * .06, ey - D * .14)], fill=ink4, width=lw)
        dr.arc([D * 0.34, D * 0.64, D * 0.66, D * 0.88], 200, 340, fill=ink4, width=lw)
    elif mood == "shock":
        dr.ellipse([D * 0.43, D * 0.62, D * 0.57, D * 0.82], fill=ink4)
    else:
        dr.line([(D * 0.36, D * 0.70), (D * 0.64, D * 0.70)], fill=ink4, width=lw)
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def person(h=300, col=CREAM, ink=None):
    """simple bust pictogram (head + shoulders), h = total height"""
    w = int(h * 0.82)
    im, s = _canvas(w, h)
    dr = ImageDraw.Draw(im)
    r = h * 0.20
    dr.ellipse([(w / 2 - r) * s, 0, (w / 2 + r) * s, 2 * r * s], fill=tuple(col) + (255,))
    dr.rounded_rectangle([w * 0.06 * s, (2 * r + h * 0.05) * s, w * 0.94 * s, (h + h * 0.4) * s], radius=int(w * 0.32 * s), fill=tuple(col) + (255,))
    return im.resize((w, h), Image.LANCZOS).crop((0, 0, w, h))


@lru_cache(None)
def arrow(L=300, th=22, col=AMBER):
    """horizontal arrow pointing right; use put(rot=...) to aim it"""
    hh = th * 3
    im, s = _canvas(L, hh)
    dr = ImageDraw.Draw(im)
    head = th * 2.4
    dr.rounded_rectangle([0, (hh - th) / 2 * s, (L - head + 4) * s, (hh + th) / 2 * s], radius=int(th / 2 * s), fill=tuple(col) + (255,))
    dr.polygon([((L - head) * s, 0), (L * s, hh / 2 * s), ((L - head) * s, hh * s)], fill=tuple(col) + (255,))
    return im.resize((L, hh), Image.LANCZOS)


@lru_cache(None)
def check(d=120, col=GREEN, th=18):
    im, s = _canvas(d, d)
    dr = ImageDraw.Draw(im)
    pts = [(d * .16 * s, d * .54 * s), (d * .40 * s, d * .78 * s), (d * .86 * s, d * .24 * s)]
    dr.line(pts, fill=tuple(col) + (255,), width=th * s, joint="curve")
    for q in (pts[0], pts[-1]):
        dr.ellipse([q[0] - th * s / 2, q[1] - th * s / 2, q[0] + th * s / 2, q[1] + th * s / 2], fill=tuple(col) + (255,))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def cross(d=120, col=RED, th=18):
    im, s = _canvas(d, d)
    dr = ImageDraw.Draw(im)
    for a, b in (((.22, .22), (.78, .78)), ((.78, .22), (.22, .78))):
        dr.line([(d * a[0] * s, d * a[1] * s), (d * b[0] * s, d * b[1] * s)], fill=tuple(col) + (255,), width=th * s)
        for q in (a, b):
            dr.ellipse([d * q[0] * s - th * s / 2, d * q[1] * s - th * s / 2, d * q[0] * s + th * s / 2, d * q[1] * s + th * s / 2], fill=tuple(col) + (255,))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def pricetag(w=360, h=170, col=CREAM, hole=NAVY, text="", tcol=NAVY, tsize=90):
    """price tag with a punched hole; text drawn in the middle"""
    im, s = _canvas(w, h)
    dr = ImageDraw.Draw(im)
    n = h * 0.42
    dr.polygon([(n * s, 0), (w * s, 0), (w * s, h * s), (n * s, h * s), (0, h / 2 * s)], fill=tuple(col) + (255,))
    dr.ellipse([(n * 0.62) * s, (h / 2 - h * 0.07) * s, (n * 0.62 + h * 0.14) * s, (h / 2 + h * 0.07) * s], fill=tuple(hole) + (255,))
    im = im.resize((w, h), Image.LANCZOS)
    if text:
        t = txt(text, tsize, tcol, "xb", maxw=int(w - n - 30))
        im.alpha_composite(t, (int(n + (w - n - t.width) / 2), (h - t.height) // 2))
    return im


@lru_cache(None)
def bag(w=240, h=280, col=AMBER, dark=(214, 138, 0)):
    im, s = _canvas(w, h)
    dr = ImageDraw.Draw(im)
    top = h * 0.24
    dr.arc([w * .28 * s, 2 * s, w * .72 * s, (top * 2.2) * s], 180, 360, fill=tuple(dark) + (255,), width=int(w * .05 * s))
    dr.rounded_rectangle([0, top * s, w * s - 1, h * s - 1], radius=int(w * .1 * s), fill=tuple(col) + (255,))
    return im.resize((w, h), Image.LANCZOS)


# ----------------------------------------------------------------------------- backgrounds / overlays
@lru_cache(None)
def build_bg(theme, style):
    t = THEMES[theme]
    yy, xx = np.mgrid[0:H, 0:W]
    if style == "radial":
        k = np.clip(np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.45) / H) ** 2) * 1.6, 0, 1)
    elif style == "diag":
        k = np.clip(((xx / W) * 0.55 + (yy / H) * 0.9) / 1.2, 0, 1)
    elif style == "top":
        k = np.clip(yy / H * 1.15, 0, 1)
    elif style == "spot":      # off-centre spotlight, upper right
        k = np.clip(np.sqrt(((xx - W * 0.78) / W) ** 2 + ((yy - H * 0.30) / H) ** 2) * 1.5, 0, 1)
    else:                       # flat
        k = np.zeros((H, W))
    k = k[..., None]
    base = np.array(t["bg0"], float) * (1 - k) + np.array(t["bg1"], float) * k
    base = base + np.random.default_rng(5).normal(0, 1.3, (H, W, 1))     # dither: avoids banding after Instagram re-encode
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")


@lru_cache(None)
def _sheet(theme, kind):
    t = THEMES[theme]
    im = Image.new("RGBA", (W + 120, H + 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = tuple(t["dot"]) + (t["dota"],)
    if kind == "dots":
        for y in range(0, H + 120, 60):
            for x in range(0, W + 120, 60):
                d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=c)
    elif kind == "grid":
        for x in range(0, W + 120, 120):
            d.line([(x, 0), (x, H + 120)], fill=c, width=2)
        for y in range(0, H + 120, 120):
            d.line([(0, y), (W + 120, y)], fill=c, width=2)
    elif kind == "diag":
        for k in range(-H - 120, W + 120, 90):
            d.line([(k, 0), (k + H + 120, H + 120)], fill=c, width=3)
    return im


def overlay(cv, t, kind):
    """slow moving texture on top of the background: dots | grid | diag | rings | none"""
    if kind in ("dots", "grid", "diag"):
        ox, oy = int((t * 9) % 60), int((t * 6) % 60)
        if kind != "dots":
            ox, oy = int((t * 9) % 120), int((t * 6) % 120)
        cv.alpha_composite(_sheet(TH.name, kind).crop((ox, oy, ox + W, oy + H)))
    elif kind == "rings":
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        c = tuple(TH.dot)
        for k in range(9):
            r = ((t * 70 + k * 130) % 1170)
            a = int(TH.dota * 1.6 * (1 - r / 1170))
            d.ellipse([W / 2 - r, H * 0.45 - r, W / 2 + r, H * 0.45 + r], outline=c + (a,), width=3)
        cv.alpha_composite(im)


# ----------------------------------------------------------------------------- the reel (brand frame + scenes)
class Reel:
    """scenes: list of fn(cv, t). The brand frame (header, progress bar, end card) is added here."""

    def __init__(self, tim, scenes, theme="navy", bg="radial", overlay_kind="dots", header=True,
                 tagline="Iqtisod va marketing, oddiy tilda", handle="@narxtili", sub="Har 2 kunda bitta Reels",
                 disclaimer=""):
        set_theme(theme)
        self.tim, self.scenes, self.theme, self.bg, self.ov, self.header = tim, scenes, theme, bg, overlay_kind, header
        self.tagline, self.handle, self.sub, self.disclaimer = tagline, handle, sub, disclaimer

    def end_card(self, cv, t):
        tim = self.tim
        if t < tim.end0:
            return
        lt = t - tim.end0
        fo = clamp((tim.total - t) / 0.25)
        item(cv, logo(300, TH.lb, TH.ln, TH.ln), 540, 650, lt, 0.0, fo, 0, dur=0.45)
        item(cv, txt("Narx Tili", 132), 540, 905, lt, 0.12, fo, 0)
        item(cv, txt(self.tagline, 52, TH.fg, "sb", maxw=880), 540, 1030, lt, 0.24, fo, 0, base=0.8)
        item(cv, txt(self.handle, 74, TH.acc), 540, 1150, lt, 0.36, fo, 0)
        item(cv, txt(self.sub, 46, TH.fg, "sb"), 540, 1260, lt, 0.48, fo, 0, base=0.6)
        if self.disclaimer:
            item(cv, txt(self.disclaimer, 34, TH.fg, "sb", maxw=900), 540, 1380, lt, 0.6, fo, 0, base=0.55)

    def draw(self, t):
        tim = self.tim
        cv = build_bg(self.theme, self.bg).copy()
        overlay(cv, t, self.ov)
        if self.header:
            hdr = clamp((tim.end0 - 0.2 - t) / 0.25) if t > tim.end0 - 0.45 else 1.0
            if hdr > 0:
                tl = txt("Narx Tili", 38, TH.fg, "b")
                x0 = 540 - (58 + 14 + tl.width) / 2
                put(cv, logo(58, TH.lb, TH.ln, TH.ln), x0 + 29, 300, hdr * 0.9)
                put(cv, tl, x0 + 72 + tl.width / 2, 300, hdr * 0.9)
                put(cv, rrect(900, 6, 3, TH.mut), 540, 1488, hdr * 0.5)
                pw = int(900 * clamp(t / tim.end0))
                if pw >= 6:
                    put(cv, rrect(pw, 6, 3, TH.acc), 90 + pw / 2, 1488, hdr * 0.9)
        for fn in self.scenes:
            fn(cv, t)
        self.end_card(cv, t)
        return cv


_R = None


def _frame(i): return _R.draw(i / FPS).convert("RGB").tobytes()


def stills(reel, times, outdir):
    os.makedirs(outdir, exist_ok=True)
    for tv in times:
        reel.draw(float(tv)).convert("RGB").save(f"{outdir}/t{float(tv):05.2f}.png")


def render(reel, out_mp4, mix_wav, cover_t=2.9, crf=11, procs=2):
    """Render all frames -> H.264 (High, yuv420p, bt709, CRF 11, faststart) + AAC 192k from mix_wav. Also writes <out>.jpg cover."""
    global _R
    _R = reel
    tim = reel.tim
    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", mix_wav, "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-profile:v", "high", "-level", "4.2",
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", f"{tim.total:.3f}", "-movflags", "+faststart", out_mp4]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(procs) as pool:
        for fr in pool.imap(_frame, range(tim.nf), chunksize=6):
            pr.stdin.write(fr)
    pr.stdin.close()
    pr.wait()
    reel.draw(cover_t).convert("RGB").save(os.path.splitext(out_mp4)[0] + ".jpg", quality=95, subsampling=0)
    print("rendered", tim.nf, "frames ->", out_mp4)
