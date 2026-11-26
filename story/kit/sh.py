"""Sirli Hikoyalar: story-reel framework + reusable art (all drawn with PIL/numpy, 1080x1920 @30).

from sh import *   (adds ../../kit to sys.path, re-exports nt_kit / nt_fx helpers)
StoryReel(tim, layers, cam=..., ...)  : layers = [fn(cv, t)], then camera -> whip/sweep/chroma/flash -> post -> top layers -> end card.
Art: sky/moon/stars, skyline, clock tower (+ hands, window light), cosy room, cat, brass key, evidence cards, door + silhouette.
"""
import math
import os
import sys
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "kit"))

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

import nt_kit as K  # noqa: E402
from nt_kit import *  # noqa: F401,F403,E402
from nt_kit import THEMES, TH, set_theme  # noqa: F401,E402
from nt_fx import (Cam, apply_camera, motion_blur, light_sweep, post, stext, fit_stext, glow, shadowed, glass, captions,  # noqa: F401,E402
                   pop, sparks, gtext, spot, rays)

THEMES["story"] = dict(bg0=(36, 28, 84), bg1=(8, 7, 26), fg=(244, 240, 232), acc=(255, 196, 92), mut=(110, 100, 160), card=(30, 24, 70),
                       ink=(8, 7, 26), dot=(244, 240, 232), dota=14, lb=(255, 196, 92), ln=(8, 7, 26), acc2=(110, 220, 255), glow=(255, 184, 72))
AMB, CYAN, CREAM_ = (255, 196, 92), (110, 220, 255), (244, 240, 232)
HANDLE = "@sirli.xikoyalar_ai"
BRAND = "SIRLI HIKOYALAR"


# ----------------------------------------------------------------------------- basics
def vgrad(w, h, c0, c1, gamma=1.0):
    k = (np.linspace(0, 1, h, dtype=np.float32) ** gamma)[:, None, None]
    a = np.array(c0, np.float32) * (1 - k) + np.array(c1, np.float32) * k
    return Image.fromarray(np.broadcast_to(a, (h, w, 3)).astype(np.uint8)).convert("RGBA")


@lru_cache(None)
def radial(d, col, a=255, p=2.0):
    yy, xx = np.mgrid[0:d, 0:d].astype(np.float32)
    r = np.sqrt((xx - d / 2) ** 2 + (yy - d / 2) ** 2) / (d / 2)
    al = np.clip(1 - r, 0, 1) ** p * a
    arr = np.dstack([np.broadcast_to(np.array(col, np.float32), (d, d, 3)), al])
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def ell(d, box, fill, S):
    d.ellipse([box[0] * S, box[1] * S, box[2] * S, box[3] * S], fill=fill)


def poly(d, pts, fill, S):
    d.polygon([(x * S, y * S) for x, y in pts], fill=fill)


def grad_h(size, mask_draw, c_left, c_right, x0, x1, S):
    """fill a shape (drawn on an L mask by mask_draw(draw)) with a horizontal gradient between x0..x1 (unscaled coords)"""
    w, h = size
    m = Image.new("L", size, 0)
    mask_draw(ImageDraw.Draw(m))
    xs = np.clip((np.arange(w, dtype=np.float32) - x0 * S) / max(1.0, (x1 - x0) * S), 0, 1)[None, :, None]
    col = np.array(c_left, np.float32) * (1 - xs) + np.array(c_right, np.float32) * xs
    arr = np.concatenate([np.broadcast_to(col, (h, w, 3)), np.asarray(m, np.float32)[..., None]], axis=2)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


# ----------------------------------------------------------------------------- sky, moon, stars, skyline
@lru_cache(None)
def sky_base():
    im = vgrad(W, H, (9, 8, 32), (66, 44, 110), 0.85)
    im.alpha_composite(radial(900, (170, 180, 255), 120, 2.0), (820 - 450, 470 - 450))
    d = ImageDraw.Draw(im)
    S = 3
    m = Image.new("RGBA", (200 * S, 200 * S), (0, 0, 0, 0))
    md = ImageDraw.Draw(m)
    md.ellipse([10 * S, 10 * S, 190 * S, 190 * S], fill=(240, 236, 214, 255))
    for (x, y, r) in ((70, 80, 22), (120, 60, 14), (110, 124, 26), (60, 130, 12), (140, 100, 10)):
        md.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(214, 210, 190, 255))
    im.alpha_composite(m.resize((200, 200), Image.LANCZOS), (820 - 100, 470 - 100))
    return im


_STARS = np.random.default_rng(5).uniform(0, 1, (120, 5))


def stars(cv, t, ymax=1100, alpha=1.0):
    d = ImageDraw.Draw(cv, "RGBA")
    for x, y, r, f, ph in _STARS:
        tw = 0.55 + 0.45 * math.sin(t * (1.2 + 2.6 * f) + ph * 6.28)
        X_, Y_ = x * W, y * ymax * 0.95
        rr = 1.2 + 2.6 * r
        d.ellipse([X_ - rr * 2.4, Y_ - rr * 2.4, X_ + rr * 2.4, Y_ + rr * 2.4], fill=(200, 210, 255, int(30 * tw * alpha)))
        d.ellipse([X_ - rr, Y_ - rr, X_ + rr, Y_ + rr], fill=(255, 255, 255, int(235 * tw * alpha)))


@lru_cache(None)
def town(seed, w, h, col, lit_p, lit_col=(255, 190, 96), hmin=120, hmax=330):
    S = 2
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = -40
    while x < w:
        bw = int(rng.uniform(90, 190))
        bh = int(rng.uniform(hmin, hmax))
        top = h - bh
        d.rectangle([x * S, top * S, (x + bw) * S, h * S], fill=col + (255,))
        kind = rng.integers(0, 3)
        if kind == 0:
            poly(d, [(x - 6, top), (x + bw + 6, top), (x + bw / 2, top - bw * 0.32)], col + (255,), S)
        elif kind == 1:
            d.rectangle([(x - 4) * S, (top - 12) * S, (x + bw + 4) * S, top * S], fill=col + (255,))
        for wx in range(x + 18, x + bw - 22, 38):
            for wy in range(top + 26, h - 30, 52):
                if rng.random() < lit_p:
                    d.rectangle([wx * S, wy * S, (wx + 14) * S, (wy + 22) * S], fill=lit_col + (210,))
                else:
                    d.rectangle([wx * S, wy * S, (wx + 14) * S, (wy + 22) * S], fill=tuple(int(c * 1.25) for c in col) + (255,))
        if rng.random() < 0.35:                          # a round tree between houses
            tx = x + bw + 12
            ell(d, (tx - 36, h - 150, tx + 36, h - 80), tuple(int(c * 0.9) for c in col) + (255,), S)
            d.rectangle([(tx - 5) * S, (h - 90) * S, (tx + 5) * S, h * S], fill=col + (255,))
        x += bw + int(rng.uniform(-8, 26))
    return im.resize((w, h), Image.LANCZOS)


# ----------------------------------------------------------------------------- the clock tower
TW, TH_ = 520, 1500           # sprite size (local units)
FACE = (260, 490)             # clock-face centre in sprite coordinates
WIN = (260, 800)              # arched window centre
DOOR = (260, 1500)            # door base centre


@lru_cache(None)
def tower_src():
    S = 2
    sz = (TW * S, TH_ * S)
    im = Image.new("RGBA", sz, (0, 0, 0, 0))
    stone, stone_l = (58, 48, 78), (104, 88, 124)
    # shaft, tapered, shaded left->right (moonlit from the right)
    shaft = lambda dd: dd.polygon([(112 * S, 1500 * S), (150 * S, 640 * S), (370 * S, 640 * S), (408 * S, 1500 * S)], fill=255)
    im.alpha_composite(grad_h(sz, shaft, (34, 28, 52), stone_l, 112, 408, S))
    d = ImageDraw.Draw(im)
    for y in range(650, 1500, 36):                      # brick courses
        xl = 150 - (y - 640) * 38 / 860
        xr = 370 + (y - 640) * 38 / 860
        d.line([(xl * S, y * S), (xr * S, y * S)], fill=(20, 16, 34, 70), width=2 * S // 2)
    # balcony under the clock
    d.rectangle([96 * S, 640 * S, 424 * S, 662 * S], fill=(120, 100, 138, 255))
    for x in range(104, 424, 22):
        d.rectangle([x * S, 662 * S, (x + 8) * S, 690 * S], fill=(82, 68, 100, 255))
    # clock box
    box = lambda dd: dd.rectangle([118 * S, 330 * S, 402 * S, 640 * S], fill=255)
    im.alpha_composite(grad_h(sz, box, (50, 42, 70), (112, 96, 134), 118, 402, S))
    d = ImageDraw.Draw(im)
    d.rectangle([104 * S, 318 * S, 416 * S, 338 * S], fill=(130, 112, 150, 255))
    # roof (two shaded halves) + spire
    poly(d, [(100, 322), (260, 112), (260, 322)], (36, 56, 84, 255), S)
    poly(d, [(260, 112), (420, 322), (260, 322)], (62, 90, 124, 255), S)
    d.line([(260 * S, 112 * S), (260 * S, 40 * S)], fill=(196, 150, 64, 255), width=6 * S)
    ell(d, (250, 24, 270, 44), (230, 186, 90, 255), S)
    # clock face
    ell(d, (FACE[0] - 124, FACE[1] - 124, FACE[0] + 124, FACE[1] + 124), (120, 84, 30, 255), S)
    ell(d, (FACE[0] - 118, FACE[1] - 118, FACE[0] + 118, FACE[1] + 118), (214, 168, 76, 255), S)
    ell(d, (FACE[0] - 106, FACE[1] - 106, FACE[0] + 106, FACE[1] + 106), (246, 238, 214, 255), S)
    ell(d, (FACE[0] - 100, FACE[1] - 100, FACE[0] + 100, FACE[1] + 100), (236, 226, 198, 255), S)
    for i in range(60):
        a = math.radians(i * 6 - 90)
        r0 = 90 if i % 5 else 82
        d.line([((FACE[0] + math.cos(a) * r0) * S, (FACE[1] + math.sin(a) * r0) * S),
                ((FACE[0] + math.cos(a) * 98) * S, (FACE[1] + math.sin(a) * 98) * S)], fill=(80, 60, 48, 255), width=(3 if i % 5 == 0 else 1) * S)
    rom = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
    f = F("xb", 22 * S)
    for i, s in enumerate(rom):
        a = math.radians(i * 30 - 90)
        cx, cy = FACE[0] + math.cos(a) * 68, FACE[1] + math.sin(a) * 68
        col = (214, 112, 8, 255) if s in ("III", "VII") else (74, 54, 46, 255)      # the two polished numerals (a fair-play clue)
        d.text((cx * S, cy * S), s, font=f, fill=col, anchor="mm")
    # arched window and door
    d.rounded_rectangle([(WIN[0] - 46) * S, (WIN[1] - 70) * S, (WIN[0] + 46) * S, (WIN[1] + 74) * S], radius=46 * S, fill=(150, 130, 166, 255))
    d.rounded_rectangle([(WIN[0] - 36) * S, (WIN[1] - 62) * S, (WIN[0] + 36) * S, (WIN[1] + 66) * S], radius=36 * S, fill=(14, 10, 26, 255))
    d.rectangle([90 * S, 1486 * S, 430 * S, 1500 * S], fill=(90, 76, 108, 255))
    d.rounded_rectangle([(DOOR[0] - 70) * S, 1350 * S, (DOOR[0] + 70) * S, 1500 * S], radius=70 * S, fill=(140, 120, 156, 255))
    d.rounded_rectangle([(DOOR[0] - 58) * S, 1362 * S, (DOOR[0] + 58) * S, 1500 * S], radius=58 * S, fill=(66, 38, 30, 255))
    for x in (-30, 0, 30):
        d.line([((DOOR[0] + x) * S, 1368 * S), ((DOOR[0] + x) * S, 1500 * S)], fill=(40, 22, 20, 255), width=3 * S)
    return im


def tower_xf(fx, fy, sc):
    """anchor so that the clock-face centre lands on (fx, fy) at scale sc -> function local->canvas"""
    return lambda x, y: (fx + (x - FACE[0]) * sc, fy + (y - FACE[1]) * sc)


def draw_tower(cv, fx, fy, sc, minute, hour_h=3.0, win_light=0.0, door_open=0.0, glow_face=0.55):
    """clock tower with face centre at (fx, fy). minute: float minutes (0..60), hour_h: hour (0..12)"""
    src = tower_src()
    w, h = int(TW * sc), int(TH_ * sc)
    spr = src.resize((max(2, w), max(2, h)), Image.LANCZOS)
    X = tower_xf(fx, fy, sc)
    ox, oy = X(0, 0)
    # warm halo behind the face
    cx, cy = X(*FACE)
    put(cv, radial(900, (255, 190, 96), int(150 * glow_face), 2.2), cx, cy, 1.0, 1.0 * sc * 0.9)
    _paste_clip(cv, spr, ox, oy)
    d = ImageDraw.Draw(cv, "RGBA")
    # window light
    wx, wy = X(*WIN)
    if win_light > 0.01:
        put(cv, radial(520, (255, 190, 96), int(230 * win_light), 1.6), wx, wy, 1.0, sc * 0.95)
        rr = 36 * sc
        d.rounded_rectangle([wx - rr, wy - 62 * sc, wx + rr, wy + 66 * sc], radius=int(rr), fill=(255, 200, 110, int(255 * win_light)))
        d.line([(wx, wy - 62 * sc), (wx, wy + 66 * sc)], fill=(120, 70, 20, int(200 * win_light)), width=max(2, int(4 * sc)))
        d.line([(wx - rr, wy + 4 * sc), (wx + rr, wy + 4 * sc)], fill=(120, 70, 20, int(200 * win_light)), width=max(2, int(4 * sc)))
    # door light spilling out
    if door_open > 0.01:
        dx, dy = X(DOOR[0], 1440)
        put(cv, radial(500, (255, 190, 96), int(220 * door_open), 1.5), dx, dy, 1.0, sc * 0.9)
    # hands
    ma = math.radians(minute * 6 - 90)
    ha = math.radians((hour_h % 12) * 30 + minute * 0.5 - 90)
    for ang, L, wd, col in ((ha, 62, 9, (44, 30, 24, 255)), (ma, 92, 6, (44, 30, 24, 255))):
        x1, y1 = cx + math.cos(ang) * L * sc, cy + math.sin(ang) * L * sc
        tx, ty = cx - math.cos(ang) * 18 * sc, cy - math.sin(ang) * 18 * sc
        d.line([(tx, ty), (x1, y1)], fill=col, width=max(2, int(wd * sc)))
        ell_r = wd * sc * 0.6
        d.ellipse([x1 - ell_r, y1 - ell_r, x1 + ell_r, y1 + ell_r], fill=col)
    r_ = 8 * sc
    d.ellipse([cx - r_, cy - r_, cx + r_, cy + r_], fill=(196, 150, 64, 255))
    return X


def _paste_clip(cv, im, ox, oy):
    ox, oy = int(round(ox)), int(round(oy))
    w, h = im.size
    x0, y0, x1, y1 = max(0, ox), max(0, oy), min(W, ox + w), min(H, oy + h)
    if x1 <= x0 or y1 <= y0:
        return
    cv.alpha_composite(im.crop((x0 - ox, y0 - oy, x1 - ox, y1 - oy)), (x0, y0))


# ----------------------------------------------------------------------------- props
@lru_cache(None)
def key_src(label="VII", S=2):
    w, h = 560, 240
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    br, br_l, br_d = (214, 160, 62, 255), (255, 226, 140, 255), (120, 78, 20, 255)
    d.rounded_rectangle([150 * S, 108 * S, 520 * S, 134 * S], radius=12 * S, fill=br_d)                         # shaft shadow
    d.rounded_rectangle([150 * S, 100 * S, 520 * S, 126 * S], radius=12 * S, fill=br)
    d.rectangle([150 * S, 102 * S, 520 * S, 108 * S], fill=br_l)
    for x in (430, 470, 506):                                                                                    # bit
        d.rectangle([x * S, 126 * S, (x + 20) * S, (150 + (x % 30)) * S], fill=br)
    ell(d, (14, 20, 160, 200), br_d, S)
    ell(d, (20, 14, 160, 194), br, S)
    ell(d, (48, 42, 134, 164), (40, 28, 70, 255), S)                                                            # hole in the bow
    ell(d, (52, 40, 130, 100), (60, 44, 96, 255), S)
    d.arc([22 * S, 18 * S, 156 * S, 190 * S], 200, 300, fill=br_l, width=7 * S)
    d.text((91 * S, 104 * S), label, font=F("xb", 40 * S), fill=(255, 238, 190, 255), anchor="mm")
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def cat_src(S=2):
    w, h = 300, 340
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fur, fur_d, fur_l = (126, 130, 150, 255), (84, 86, 108, 255), (170, 174, 192, 255)
    d.line([(220 * S, 300 * S), (290 * S, 270 * S), (286 * S, 200 * S)], fill=fur_d, width=30 * S, joint="curve")      # tail
    ell(d, (60, 160, 250, 336), fur, S)                                                                           # body
    ell(d, (96, 220, 214, 334), fur_l, S)                                                                         # chest
    for sx in (92, 176):                                                                                          # paws
        ell(d, (sx - 6, 300, sx + 46, 340), fur_l, S)
    poly(d, [(62, 92), (74, 6), (140, 60)], fur, S)                                                               # ears
    poly(d, [(238, 92), (226, 6), (160, 60)], fur, S)
    poly(d, [(80, 80), (82, 30), (116, 62)], (230, 150, 170, 255), S)
    poly(d, [(220, 80), (218, 30), (184, 62)], (230, 150, 170, 255), S)
    ell(d, (46, 40, 254, 224), fur, S)                                                                            # head
    ell(d, (110, 150, 190, 214), fur_l, S)                                                                        # muzzle
    for sx in (-1, 1):
        ex = 150 + sx * 52
        ell(d, (ex - 30, 98, ex + 30, 160), (255, 226, 96, 255), S)
        ell(d, (ex - 8, 100, ex + 8, 158), (24, 16, 20, 255), S)
        ell(d, (ex - 20, 106, ex - 8, 120), (255, 255, 255, 235), S)
        for k in (-1, 0, 1):                                                                                      # whiskers
            d.line([((150 + sx * 40) * S, (186 + k * 6) * S), ((150 + sx * 120) * S, (180 + k * 20) * S)], fill=(230, 232, 244, 200), width=2 * S)
    poly(d, [(138, 176), (162, 176), (150, 190)], (236, 140, 160, 255), S)
    for x_, y_ in ((100, 70), (150, 54), (200, 70)):                                                              # forehead stripes
        d.line([(x_ * S, y_ * S), (x_ * S, (y_ + 22) * S)], fill=fur_d, width=6 * S)
    return im.resize((w, h), Image.LANCZOS)


@lru_cache(None)
def evidence_card(n, title, body, w=860, h=170):
    s = 2
    base = glass(w, h, 34, tint=(20, 16, 56), a=215, border=(110, 220, 255), ba=190)
    im = base.copy()
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 12, h], radius=6, fill=(110, 220, 255, 255))
    lab = stext(f"DALIL {n}", 36, (110, 220, 255), (6, 4, 22), 3, "xb")
    im.alpha_composite(lab, (34, 12))
    b = fit_stext(body, 54, (244, 240, 232), maxw=w - 80, stroke=(6, 4, 22), sw=4)
    im.alpha_composite(b, (30, 66))
    return im


# ----------------------------------------------------------------------------- door + silhouette
def door_scene(cv, t, t0, cx=540, cy=1010, openness=None, figure=0.0, glint=0.0):
    """arched doorway (stone frame) whose two leaves swing open from t0; amber light + silhouette behind"""
    p = ease_in_out(clamp((t - t0) / 2.4)) if openness is None else openness
    aw, ah = 640, 940
    S = 1
    # interior light
    inner = Image.new("RGBA", (aw - 90, ah - 80), (0, 0, 0, 0))
    g = vgrad(inner.width, inner.height, (255, 214, 130), (120, 54, 24), 1.0)
    m = Image.new("L", inner.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, inner.width - 1, inner.height - 1], radius=inner.width // 2, fill=255, corners=(True, True, False, False))
    g.putalpha(m)
    interior = Image.new("RGBA", g.size, (0, 0, 0, 0))
    interior.alpha_composite(g)
    # figure
    if figure > 0.01:
        fg = silhouette_src()
        interior_cx = interior.width // 2
        sc = 1.0
        interior.alpha_composite(fg, (int(interior_cx - fg.width / 2), interior.height - fg.height))
    ib = Image.new("RGBA", g.size, (0, 0, 0, 0))
    ib.paste(interior, (0, 0), m)
    # dark closed-door leaves: widths shrink as they open (hinged at the outer edges)
    lw = int((aw - 90) / 2 * (1 - p * 0.92))
    leaf = Image.new("RGBA", (max(1, lw), ah - 80), (0, 0, 0, 0))
    lg = vgrad(max(1, lw), ah - 80, (84, 52, 38), (44, 26, 22), 1.0)
    leaf.alpha_composite(lg)
    ld = ImageDraw.Draw(leaf)
    for y in range(0, ah - 80, 62):
        ld.line([(0, y), (leaf.width, y)], fill=(30, 16, 14, 190), width=3)
    ld.rectangle([0, ah // 2 - 60, leaf.width, ah // 2 - 48], fill=(40, 40, 52, 255))
    cv_layer = Image.new("RGBA", (aw, ah), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv_layer)
    # stone frame arch
    d.rounded_rectangle([0, 0, aw - 1, ah - 1], radius=aw // 2, fill=(118, 100, 138, 255), corners=(True, True, False, False))
    d.rounded_rectangle([14, 14, aw - 15, ah - 1], radius=aw // 2 - 14, fill=(76, 62, 96, 255), corners=(True, True, False, False))
    cv_layer.paste(ib, (45, 40), ib)
    maskarch = Image.new("L", g.size, 0)
    ImageDraw.Draw(maskarch).rounded_rectangle([0, 0, g.width - 1, g.height - 1], radius=g.width // 2, fill=255, corners=(True, True, False, False))
    for side in (0, 1):
        x0 = 45 if side == 0 else 45 + g.width - lw
        lm = maskarch.crop((x0 - 45, 0, x0 - 45 + lw, g.height))
        cv_layer.paste(leaf, (x0, 40), lm)
    put(cv, radial(1100, (255, 190, 96), int(170 * p), 1.6), cx, cy - 40, 1.0, 1.0)
    put(cv, cv_layer, cx, cy)
    if glint > 0.01:
        put(cv, radial(300, (255, 244, 200), int(255 * glint), 1.8), cx + 120, cy + 150 + 40, 1.0, 1.0)
    return p


@lru_cache(None)
def silhouette_src():
    S = 2
    w, h = 340, 760
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dark = (12, 8, 20, 255)
    cx = 150
    ell(d, (cx - 62, 140, cx + 62, 272), dark, S)                           # head
    poly(d, [(cx - 66, 168), (cx + 66, 168), (cx + 52, 92), (cx - 52, 92)], dark, S)   # doppi (skullcap)
    d.rectangle([(cx - 24) * S, 250 * S, (cx + 24) * S, 310 * S], fill=dark)        # neck
    d.rounded_rectangle([(cx - 130) * S, 296 * S, (cx + 130) * S, 760 * S], radius=70 * S, fill=dark)   # shoulders + coat
    d.line([((cx + 100) * S, 360 * S), ((cx + 170) * S, 450 * S), ((cx + 150) * S, 330 * S)], fill=dark, width=44 * S, joint="curve")   # raised arm
    ell(d, (cx + 134, 296, cx + 182, 344), dark, S)                          # fist with key
    return im.resize((w, h), Image.LANCZOS)


# ----------------------------------------------------------------------------- brand marks
@lru_cache(None)
def logo_img(d_=300):
    p = os.path.join(HERE, "..", "brand", "avatar.png")
    im = Image.open(p).convert("RGBA").resize((d_, d_), Image.LANCZOS)
    m = Image.new("L", (d_ * 3, d_ * 3), 0)
    ImageDraw.Draw(m).ellipse([0, 0, d_ * 3 - 1, d_ * 3 - 1], fill=255)
    im.putalpha(m.resize((d_, d_), Image.LANCZOS))
    return im


def brand_chip(cv, t, ep_tag, alpha=0.9):
    tl = stext(f"{BRAND}  ·  {ep_tag}", 30, (244, 240, 232), (6, 4, 22), 3, "b")
    x0 = 540 - (54 + 14 + tl.width) / 2
    put(cv, logo_img(54), x0 + 27, 292, alpha)
    put(cv, tl, x0 + 68 + tl.width / 2, 292, alpha)


# ----------------------------------------------------------------------------- the reel
class StoryReel:
    def __init__(self, tim, layers, cam=None, vignette=0.55, grain=0.35, bloom=0.30, tint=(1.0, 1.0, 1.0), flashes=(), chroma_at=(),
                 whips=(), sweeps=(), top=(), end_fn=None):
        self.tim, self.layers, self.cam = tim, list(layers), cam or Cam()
        self.vig, self.grain, self.bloom, self.tint = vignette, grain, bloom, tint
        self.flashes, self.chroma_at, self.whips, self.sweeps = list(flashes), list(chroma_at), list(whips), list(sweeps)
        self.top, self.end_fn = list(top), end_fn

    def draw(self, t):
        set_theme("story")
        cv = Image.new("RGBA", (W, H), (8, 7, 26, 255))
        for fn in self.layers:
            fn(cv, t)
        cv = apply_camera(cv, *self.cam(t))
        for t0, dur, px, ang in self.whips:
            p = (t - t0) / dur
            if 0 <= p < 1:
                cv = motion_blur(cv, px * (1 - p) ** 1.6, ang)
        for t0, dur in self.sweeps:
            p = (t - t0) / dur
            if 0 <= p < 1:
                cv = light_sweep(cv, ease_in_out(p), amt=0.5 * math.sin(math.pi * min(1, p * 1.15)) ** 0.7)
        ch = 0.0
        for t0, px, dur in self.chroma_at:
            p = (t - t0) / dur
            if 0 <= p < 1:
                ch = max(ch, px * (1 - p))
        fl = 0.0
        for t0, dur in self.flashes:
            p = (t - t0) / dur
            if 0 <= p < 1:
                fl = max(fl, (1 - p) ** 2 * 0.8)
        tint = self.tint(t) if callable(self.tint) else self.tint
        cv = post(cv, t, int(round(t * FPS)), self.vig, self.grain, self.bloom, tint=tint, chroma=ch, flash=fl)
        for fn in self.top:
            fn(cv, t)
        if self.end_fn:
            self.end_fn(cv, t)
        return cv


def end_card(next_line, t0, total):
    """returns fn(cv, t): dark fade-in, logo, series name, 'next episode' line, handle"""
    def fn(cv, t):
        k = clamp((t - t0) / 0.5)
        if k <= 0:
            return
        fo = clamp((total - t) / 0.3)
        ov = Image.new("RGBA", (W, H), (7, 6, 22, int(235 * k)))
        cv.alpha_composite(ov)
        lt = t - t0
        item(cv, logo_img(330), 540, 640, lt, 0.1, fo, 0, dur=0.5)
        item(cv, stext(BRAND, 92, (244, 240, 232), (6, 4, 22), 4), 540, 930, lt, 0.28, fo, 0)
        item(cv, stext(next_line, 62, AMB, (6, 4, 22), 4), 540, 1070, lt, 0.46, fo, 0)
        item(cv, stext(HANDLE, 50, (244, 240, 232), (6, 4, 22), 3, "b"), 540, 1190, lt, 0.64, fo, 0, base=0.85)
    return fn
