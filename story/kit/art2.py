"""art2.py - flat/outlined set pieces for the new Sirli Hikoyalar look (street, door, tower interior, cat, props).
All coordinates are canvas px (1080x1920); sprites are cached and drawn with PIL at 2x then reduced."""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from sh import *  # noqa: F401,F403  (put, clamp, lerp, ease_*, W, H, vgrad, radial, glow, stext, sky_base, stars, town, draw_tower, key_src ...)

OLC = (20, 15, 38)
GROUND_Y = 1330


def _spr(w, h, S=2):
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im), S


def _fin(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


# ----------------------------------------------------------------------------- street pieces
def ground(cv, y0=GROUND_Y, c0=(30, 40, 78), c1=(10, 12, 32)):
    g = vgrad(W, H - y0, c0, c1, 0.9)
    cv.alpha_composite(g, (0, y0))
    d = ImageDraw.Draw(cv, "RGBA")
    d.rectangle([0, y0 - 3, W, y0 + 4], fill=(120, 130, 200, 40))


def path_marks(cv, scroll, y0=GROUND_Y):
    """cobbles / paving stripes moving with the scroll (parallax: nearer = faster)"""
    d = ImageDraw.Draw(cv, "RGBA")
    for row, (yy, sp, hh, a) in enumerate(((y0 + 40, 1.0, 14, 40), (y0 + 130, 1.3, 20, 36), (y0 + 270, 1.7, 30, 30), (y0 + 460, 2.2, 44, 26))):
        step = 220 * sp
        off = (-scroll * sp) % step
        x = off - step
        while x < W + step:
            d.rounded_rectangle([x, yy, x + step * 0.62, yy + hh], radius=int(hh / 2), fill=(150, 160, 230, a))
            x += step


@lru_cache(None)
def fence_src(w=1500, h=210):
    im, d, S = _spr(w, h)
    col = (18, 16, 40, 255)
    d.rectangle([0, 70 * S, w * S, 86 * S], fill=col)
    d.rectangle([0, 138 * S, w * S, 154 * S], fill=col)
    for x in range(10, w, 120):
        d.polygon([(x * S, 0), ((x + 22) * S, 0), ((x + 11) * S, -14 * S)], fill=col) if False else None
        d.rounded_rectangle([x * S, 12 * S, (x + 26) * S, h * S], radius=8 * S, fill=col)
        d.polygon([(x * S, 14 * S), ((x + 26) * S, 14 * S), ((x + 13) * S, -8 * S)], fill=col)
    return _fin(im, w, h)


def fence(cv, scroll, par=1.0, y=GROUND_Y + 8, alpha=1.0):
    src = fence_src()
    off = (-scroll * par) % 1500
    for k in (-1, 0, 1):
        put(cv, src, off + k * 1500 + 750, y - 100, alpha)


@lru_cache(None)
def lamp_src(h=620):
    im, d, S = _spr(220, h)
    col = (24, 22, 50, 255)
    d.rounded_rectangle([104 * S, 110 * S, 116 * S, h * S], radius=5 * S, fill=col)
    d.rectangle([92 * S, (h - 30) * S, 128 * S, h * S], fill=col)
    d.polygon([(70 * S, 118 * S), (150 * S, 118 * S), (136 * S, 70 * S), (84 * S, 70 * S)], fill=col)
    d.polygon([(80 * S, 64 * S), (140 * S, 64 * S), (110 * S, 34 * S)], fill=col)
    d.rectangle([88 * S, 76 * S, 132 * S, 112 * S], fill=(255, 214, 120, 255))
    return _fin(im, 220, h)


def lamp(cv, x, base_y, on=1.0, t=0.0, par_scale=1.0):
    src = lamp_src()
    h = src.height * par_scale
    cy = base_y - h / 2
    if on > 0.01:
        fl = 0.85 + 0.15 * math.sin(t * 9 + x * 0.01)
        put(cv, radial(560, (255, 196, 100), int(120 * on * fl), 2.0), x, base_y - h + 94 * par_scale, 1.0, par_scale)
    put(cv, src, x, cy, 1.0, par_scale)
    if on < 0.99:
        # dark lamp head
        pass


def bushes(cv, scroll, par, y, seed=3, col=(14, 18, 40), alpha=1.0, size=1.0):
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(cv, "RGBA")
    span = 1700
    off = (-scroll * par) % span
    xs = np.cumsum(rng.uniform(160, 380, 16))
    for base in (-span, 0, span):
        for x in xs:
            X = x + off + base - span / 2
            if -200 < X < W + 200:
                r = rng.uniform(55, 95) * size
                d.ellipse([X - r, y - r * 1.3, X + r, y + 6], fill=col + (int(255 * alpha),))
                d.ellipse([X - r * 1.7, y - r * 0.8, X - r * 0.2, y + 6], fill=col + (int(255 * alpha),))


# ----------------------------------------------------------------------------- tower wall + door
@lru_cache(None)
def brick_src(w, h, base=(44, 38, 70), seed=1):
    S = 2
    im = Image.new("RGBA", (w * S, h * S), base + (255,))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    bh, bw = 38, 96
    for r, y in enumerate(range(0, h, bh)):
        off = (bw // 2) if r % 2 else 0
        for x in range(-bw, w + bw, bw):
            tone = rng.uniform(-8, 8)
            c = tuple(int(max(0, min(255, v + tone))) for v in base)
            d.rectangle([(x + off) * S + 2, y * S + 2, (x + off + bw) * S - 2, (y + bh) * S - 2], fill=c + (255,))
    im = im.resize((w, h), Image.LANCZOS)
    return im


@lru_cache(None)
def door_leaf(w, h, side, S=2):
    """one wooden door leaf (arched outer edge handled by the mask elsewhere): planks + iron bands"""
    im = Image.new("RGBA", (w * S, h * S), (92, 56, 40, 255))
    d = ImageDraw.Draw(im)
    pw = w / 3.0
    for i in range(1, 3):
        d.line([(i * pw * S, 0), (i * pw * S, h * S)], fill=OLC + (255,), width=3 * S)
    for yy in (0.18, 0.55, 0.86):
        y = int(h * yy)
        d.rectangle([0, (y - 14) * S, w * S, (y + 14) * S], fill=(46, 44, 62, 255))
        for x in range(14, w, 34):
            d.ellipse([(x - 4) * S, (y - 4) * S, (x + 4) * S, (y + 4) * S], fill=(120, 120, 150, 255))
    # grain
    rng = np.random.default_rng(side + 7)
    for _ in range(14):
        x = rng.uniform(4, w - 4)
        d.line([(x * S, rng.uniform(0, h * 0.4) * S), ((x + rng.uniform(-6, 6)) * S, rng.uniform(h * 0.5, h) * S)], fill=(70, 40, 30, 120), width=2 * S)
    return im.resize((w, h), Image.LANCZOS)


def tower_door(cv, cx, base_y, dw, dh, openness=0.0, glow_k=0.0, locked=True, t=0.0, shake=0.0):
    """arched double door. openness 0..1: leaves swing inward (shrink toward the hinges), revealing a warm interior."""
    top = base_y - dh
    arch_r = dw / 2
    # frame (stone)
    S = 2
    fr = Image.new("RGBA", (int((dw + 90) * S), int((dh + 60) * S)), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fr)
    fd.rounded_rectangle([0, 0, (dw + 90) * S, (dh + 60) * S + 200], radius=int((arch_r + 45) * S), fill=OLC + (255,))
    fd.rounded_rectangle([4 * S, 4 * S, (dw + 86) * S, (dh + 60) * S + 200], radius=int((arch_r + 41) * S), fill=(128, 114, 150, 255))
    fr = fr.resize((dw + 90, dh + 60), Image.LANCZOS)
    cv.alpha_composite(fr, (int(cx - (dw + 90) / 2), int(top - 40)))
    # interior (dark / warm light)
    inner = Image.new("RGBA", (dw, dh + 40), (0, 0, 0, 0))
    idr = ImageDraw.Draw(inner)
    idr.rounded_rectangle([0, 0, dw, dh + 200], radius=int(arch_r), fill=(10, 8, 22, 255))
    mask = inner.getchannel("A")
    if glow_k > 0.01:
        lg = vgrad(dw, dh + 40, (255, 214, 130), (255, 150, 60), 1.0)
        lg.putalpha(mask.point(lambda v: int(v * clamp(glow_k))))
        inner.alpha_composite(lg)
    cv.alpha_composite(inner, (int(cx - dw / 2), int(top)))
    # leaves
    k = 1.0 - clamp(openness)
    lw = max(4, int(dw / 2 * k))
    if lw > 6:
        for side in (-1, 1):
            leaf = door_leaf(int(dw / 2), int(dh + 40), side)
            leaf = leaf.resize((lw, leaf.height), Image.BILINEAR)
            # arch clip
            clip = Image.new("L", (lw, leaf.height), 0)
            cd = ImageDraw.Draw(clip)
            cd.rounded_rectangle([0 if side < 0 else -lw, 0, lw * (1 if side < 0 else 1) * 2 + 0, leaf.height + 200], radius=int(arch_r), fill=255) if False else None
            leaf2 = leaf.copy()
            x0 = int(cx - dw / 2) if side < 0 else int(cx + dw / 2 - lw)
            full = Image.new("RGBA", (dw, dh + 40), (0, 0, 0, 0))
            xx = 0 if side < 0 else dw - lw
            full.alpha_composite(leaf2, (xx, 0))
            full.putalpha(Image.fromarray((np.array(full.getchannel("A"), np.float32) * np.array(mask, np.float32) / 255).astype(np.uint8)))
            cv.alpha_composite(full, (int(cx - dw / 2), int(top)))
    # centre seam + lock plate
    d = ImageDraw.Draw(cv, "RGBA")
    if openness < 0.05:
        d.line([(cx, top + arch_r * 0.6), (cx, base_y)], fill=OLC + (255,), width=5)
        px, py = cx + 34, base_y - dh * 0.46
        d.rounded_rectangle([px - 26, py - 44, px + 26, py + 44], radius=14, fill=OLC + (255,))
        d.rounded_rectangle([px - 22, py - 40, px + 22, py + 40], radius=11, fill=(176, 150, 70, 255))
        d.ellipse([px - 9, py - 22, px + 9, py - 4], fill=OLC + (255,))
        d.polygon([(px - 5, py - 10), (px + 5, py - 10), (px + 8, py + 22), (px - 8, py + 22)], fill=OLC + (255,))
    return top


# ----------------------------------------------------------------------------- gears, board, key
@lru_cache(None)
def gear_src(r, teeth, col, hole=0.28, spokes=6):
    S = 2
    n = int(r * 2 + 40)
    im = Image.new("RGBA", (n * S, n * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = n * S / 2

    def ring(rad_out, rad_in, fill):
        pts = []
        for i in range(teeth * 4):
            a = 2 * math.pi * i / (teeth * 4)
            rad = rad_out if (i % 4) in (0, 1) else rad_in
            pts.append((c + math.cos(a) * rad * S, c + math.sin(a) * rad * S))
        d.polygon(pts, fill=fill)

    ring(r + 14, r - 6, OLC + (255,))
    ring(r + 8, r - 12, col + (255,))
    d.ellipse([c - (r - 18) * S, c - (r - 18) * S, c + (r - 18) * S, c + (r - 18) * S], fill=shade_(col, 0.82) + (255,))
    # spokes cut-outs
    hr = r * hole
    for i in range(spokes):
        a0 = 2 * math.pi * i / spokes
        a1 = a0 + 2 * math.pi / spokes * 0.62
        pts = [(c + math.cos(a0) * hr * 1.5 * S, c + math.sin(a0) * hr * 1.5 * S)]
        for k in range(8):
            a = a0 + (a1 - a0) * k / 7
            pts.append((c + math.cos(a) * (r - 34) * S, c + math.sin(a) * (r - 34) * S))
        pts.append((c + math.cos(a1) * hr * 1.5 * S, c + math.sin(a1) * hr * 1.5 * S))
        d.polygon(pts, fill=(14, 10, 28, 255))
    d.ellipse([c - hr * S, c - hr * S, c + hr * S, c + hr * S], fill=OLC + (255,))
    d.ellipse([c - (hr - 6) * S, c - (hr - 6) * S, c + (hr - 6) * S, c + (hr - 6) * S], fill=light_(col, 0.2) + (255,))
    return im.resize((n, n), Image.LANCZOS)


def shade_(c, k): return tuple(int(v * k) for v in c)


def light_(c, k): return tuple(int(v + (255 - v) * k) for v in c)


def draw_gear(cv, cx, cy, r, teeth, ang, col=(176, 120, 60), alpha=1.0, scale=1.0):
    put(cv, gear_src(int(r), teeth, col), cx, cy, alpha, scale, ang)


@lru_cache(None)
def board_src(w=860, h=190):
    im, d, S = _spr(w, h)
    d.rounded_rectangle([0, 0, w * S, h * S], radius=22 * S, fill=OLC + (255,))
    d.rounded_rectangle([6 * S, 6 * S, (w - 6) * S, (h - 6) * S], radius=18 * S, fill=(104, 66, 44, 255))
    for i in range(1, 3):
        d.line([(10 * S, i * h / 3 * S), ((w - 10) * S, i * h / 3 * S)], fill=(80, 46, 32, 255), width=2 * S)
    return _fin(im, w, h)


def key_hook_positions(cx, cy, w=860, n=7):
    step = (w - 140) / (n - 1)
    return [(cx - (w - 140) / 2 + i * step, cy) for i in range(n)]


@lru_cache(None)
def small_key(label, S=2):
    """a small brass key hanging DOWN from the hook point (pivot top-centre)"""
    W_, H_ = 90, 190
    im = Image.new("RGBA", (W_ * S, H_ * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    brass, dark = (226, 176, 64), (150, 100, 30)
    cx = W_ // 2
    d.ellipse([(cx - 22) * S, 0, (cx + 22) * S, 44 * S], fill=OLC + (255,))
    d.ellipse([(cx - 18) * S, 4 * S, (cx + 18) * S, 40 * S], fill=brass + (255,))
    d.ellipse([(cx - 8) * S, 14 * S, (cx + 8) * S, 30 * S], fill=(26, 18, 40, 255))
    d.rounded_rectangle([(cx - 8) * S, 40 * S, (cx + 8) * S, 160 * S], radius=6 * S, fill=OLC + (255,))
    d.rounded_rectangle([(cx - 5) * S, 40 * S, (cx + 5) * S, 158 * S], radius=4 * S, fill=brass + (255,))
    for yy, ww in ((124, 24), (142, 18), (158, 28)):
        d.rounded_rectangle([cx * S, (yy - 7) * S, (cx + ww) * S, (yy + 7) * S], radius=3 * S, fill=OLC + (255,))
        d.rounded_rectangle([cx * S, (yy - 4) * S, (cx + ww - 2) * S, (yy + 4) * S], radius=2 * S, fill=brass + (255,))
    f = F("xb", 15 * S)
    d.text((cx * S, 22 * S), label, font=f, fill=(60, 36, 18, 255), anchor="mm")
    return im.resize((W_, H_), Image.LANCZOS)


# ----------------------------------------------------------------------------- the cat (Tuman)
@lru_cache(None)
def cat_src(pose="sit", S=2):
    """cat facing RIGHT. pose: sit | leap | land"""
    Wc, Hc = 360, 300
    im = Image.new("RGBA", (Wc * S, Hc * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fur, fur2, belly = (92, 94, 122), (66, 68, 94), (200, 204, 226)

    def blob(box, col, ow=5):
        x0, y0, x1, y1 = box
        d.ellipse([(x0 - ow) * S, (y0 - ow) * S, (x1 + ow) * S, (y1 + ow) * S], fill=OLC + (255,))
        d.ellipse([x0 * S, y0 * S, x1 * S, y1 * S], fill=col + (255,))

    def tail(pts, w=22):
        d.line([(x * S, y * S) for x, y in pts], fill=OLC + (255,), width=(w + 10) * S, joint="curve")
        d.line([(x * S, y * S) for x, y in pts], fill=fur2 + (255,), width=w * S, joint="curve")
        for x, y in (pts[0], pts[-1]):
            d.ellipse([(x - w / 2 - 5) * S, (y - w / 2 - 5) * S, (x + w / 2 + 5) * S, (y + w / 2 + 5) * S], fill=OLC + (255,))
            d.ellipse([(x - w / 2) * S, (y - w / 2) * S, (x + w / 2) * S, (y + w / 2) * S], fill=fur2 + (255,))

    def head(cx, cy, r=62):
        # ears
        for sx in (-1, 1):
            e = [(cx + sx * r * 0.95, cy - r * 0.2), (cx + sx * r * 0.7, cy - r * 1.35), (cx + sx * r * 0.18, cy - r * 0.8)]
            d.polygon([(x * S, y * S) for x, y in e], fill=OLC + (255,))
            e2 = [(cx + sx * r * 0.86, cy - r * 0.25), (cx + sx * r * 0.68, cy - r * 1.18), (cx + sx * r * 0.28, cy - r * 0.78)]
            d.polygon([(x * S, y * S) for x, y in e2], fill=fur + (255,))
            e3 = [(cx + sx * r * 0.76, cy - r * 0.35), (cx + sx * r * 0.66, cy - r * 0.98), (cx + sx * r * 0.4, cy - r * 0.72)]
            d.polygon([(x * S, y * S) for x, y in e3], fill=(236, 150, 170, 255))
        blob((cx - r, cy - r * 0.9, cx + r, cy + r * 0.85), fur)
        for sx in (-1, 1):
            ex = cx + sx * r * 0.42
            d.ellipse([(ex - 16) * S, (cy - 18) * S, (ex + 16) * S, (cy + 14) * S], fill=OLC + (255,))
            d.ellipse([(ex - 13) * S, (cy - 15) * S, (ex + 13) * S, (cy + 11) * S], fill=(255, 222, 70, 255))
            d.ellipse([(ex - 4) * S, (cy - 15) * S, (ex + 4) * S, (cy + 11) * S], fill=OLC + (255,))
        d.polygon([((cx - 8) * S, (cy + 24) * S), ((cx + 8) * S, (cy + 24) * S), (cx * S, (cy + 34) * S)], fill=(236, 150, 170, 255))
        for sx in (-1, 1):
            for k in (-6, 6):
                d.line([((cx + sx * 22) * S, (cy + 30 + k * 0.5) * S), ((cx + sx * 74) * S, (cy + 30 + k * 2.4) * S)], fill=(235, 235, 245, 255), width=2 * S)

    if pose == "sit":
        tail([(86, 262), (36, 262), (22, 212), (44, 176)])
        blob((70, 120, 230, 280), fur)
        blob((100, 170, 200, 280), belly, 0)
        blob((190, 236, 250, 284), fur2)
        blob((78, 236, 138, 284), fur2)
        head(222, 100)
    elif pose == "leap":   # stretched out in the air, legs spread
        tail([(40, 150), (10, 120), (6, 80), (28, 52)])
        blob((50, 110, 250, 190), fur)
        blob((26, 120, 80, 150), fur2)
        # legs front/back
        d.polygon([(220 * S, 150 * S), (300 * S, 168 * S), (306 * S, 190 * S), (214 * S, 176 * S)], fill=OLC + (255,))
        d.polygon([(224 * S, 154 * S), (294 * S, 170 * S), (298 * S, 184 * S), (220 * S, 172 * S)], fill=fur2 + (255,))
        d.polygon([(70 * S, 170 * S), (20 * S, 210 * S), (36 * S, 226 * S), (94 * S, 188 * S)], fill=OLC + (255,))
        d.polygon([(72 * S, 172 * S), (26 * S, 208 * S), (38 * S, 218 * S), (90 * S, 186 * S)], fill=fur2 + (255,))
        head(264, 116, 56)
    else:  # land: crouched
        tail([(70, 262), (20, 250), (12, 206), (40, 184)])
        blob((60, 150, 240, 284), fur)
        blob((120, 196, 220, 284), belly, 0)
        blob((190, 246, 262, 288), fur2)
        blob((70, 246, 140, 288), fur2)
        head(246, 160, 58)
    return im.resize((Wc, Hc), Image.LANCZOS)


# ----------------------------------------------------------------------------- lights
def flash_cone(cv, x, y, ang_deg, length=900, spread=18, a=150, col=(255, 240, 190)):
    """flashlight beam: translucent triangle with soft falloff, pointing at ang_deg (0 = right, 90 = down)"""
    S = 1
    L = int(length)
    layer = Image.new("RGBA", (L, int(2 * L * math.tan(math.radians(spread)) + 4)), (0, 0, 0, 0))
    hh = layer.height
    arr = np.zeros((hh, L, 4), np.uint8)
    xs = np.arange(L, dtype=np.float32)[None, :]
    ys = np.arange(hh, dtype=np.float32)[:, None] - hh / 2
    half = xs * math.tan(math.radians(spread)) + 6
    edge = np.clip(1 - np.abs(ys) / np.maximum(half, 1), 0, 1) ** 0.8
    fall = np.clip(1 - xs / L, 0, 1) ** 1.3
    al = (edge * fall * a).astype(np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3] = col[0], col[1], col[2], al
    layer = Image.fromarray(arr, "RGBA")
    rot = layer.rotate(-ang_deg, resample=Image.BICUBIC, expand=True)
    # pivot: left-middle of the layer; after rotate/expand it moves -> compute
    ca, sa = math.cos(math.radians(ang_deg)), math.sin(math.radians(ang_deg))
    px_, py_ = 0 - L / 2.0, hh / 2.0 - hh / 2.0   # pivot relative to layer centre
    rx = px_ * math.cos(math.radians(-ang_deg)) - py_ * math.sin(math.radians(-ang_deg))
    ry = px_ * math.sin(math.radians(-ang_deg)) + py_ * math.cos(math.radians(-ang_deg))
    # PIL rotates counter-clockwise by `angle`; we passed -ang so rotation is clockwise by ang (y-down math)
    cx_img, cy_img = rot.width / 2 - rx * -1 * 0, rot.height / 2
    # centre of rotated layer in canvas = pivot + (centre - pivot) rotated
    vx, vy = L / 2.0, 0.0
    cxs, cys = x + vx * ca - vy * sa, y + vx * sa + vy * ca
    put(cv, rot, cxs, cys, 1.0)
