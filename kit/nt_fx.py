"""Premium layer on top of nt_kit: cinematic camera, light, depth, kinetic captions, particles, new colour worlds.

A day's scenes.py does:   from nt_kit import *;  from nt_fx import *
and returns a PremiumReel (instead of Reel) from build(tim).  Everything here is pure PIL + numpy.

Why this exists (owner feedback, 23-Nov): the first 15 Reels were flat infographics that all looked alike and
used one third of the frame.  The premium standard is:
  * the picture FILLS the safe zone (big type >= 100 px, hero object >= 600 px), no empty thirds;
  * a question/puzzle hook on frame 0 (never a blank frame), an open loop that is answered near the end;
  * a camera that is always slowly moving (push-in / drift) plus shake/punch on impacts;
  * light and depth: aurora background, glow, soft shadows, glass cards, bloom, vignette, grain;
  * karaoke captions (active word highlighted) so muted viewers still follow;
  * sound design (kit/sfx.py): whoosh, tick, impact, riser, ding, coin... aligned to the picture;
  * every video lives in a DIFFERENT world (palette + background + hero object + camera language + music).
"""
import math

import numpy as np
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFilter

import nt_kit as K
from nt_kit import *  # noqa: F401,F403  (W, H, FPS, put, txt, F, rrect, disc, ease_*, clamp, lerp, mixc, prog, item, vis, Timing, Reel, ...)
from nt_kit import THEMES, TH, set_theme  # noqa: F401

# ----------------------------------------------------------------------------- new colour worlds
THEMES.update({
    "noir":   dict(bg0=(38, 28, 24), bg1=(8, 7, 9), fg=(246, 240, 230), acc=(255, 184, 48), mut=(104, 92, 84), card=(40, 33, 31), ink=(8, 7, 9),
                   dot=(246, 240, 230), dota=14, lb=(255, 184, 48), ln=(8, 7, 9), acc2=(226, 72, 56), glow=(255, 170, 40)),
    "neon":   dict(bg0=(44, 18, 98), bg1=(7, 5, 26), fg=(240, 244, 255), acc=(0, 229, 255), mut=(96, 84, 160), card=(32, 22, 74), ink=(7, 5, 26),
                   dot=(240, 244, 255), dota=14, lb=(0, 229, 255), ln=(7, 5, 26), acc2=(255, 64, 160), glow=(0, 229, 255)),
    "gold":   dict(bg0=(30, 30, 40), bg1=(5, 5, 9), fg=(250, 246, 236), acc=(244, 196, 92), mut=(104, 100, 94), card=(36, 36, 48), ink=(5, 5, 9),
                   dot=(250, 246, 236), dota=12, lb=(244, 196, 92), ln=(5, 5, 9), acc2=(120, 200, 255), glow=(255, 200, 90)),
    "paper":  dict(bg0=(248, 240, 224), bg1=(222, 207, 180), fg=(34, 28, 24), acc=(200, 52, 40), mut=(172, 158, 130), card=(255, 252, 244), ink=(34, 28, 24),
                   dot=(34, 28, 24), dota=10, lb=(34, 28, 24), ln=(248, 240, 224), acc2=(30, 90, 160), glow=(255, 255, 255)),
    "teal":   dict(bg0=(12, 100, 112), bg1=(3, 28, 42), fg=(240, 250, 248), acc=(255, 214, 102), mut=(70, 132, 140), card=(8, 62, 76), ink=(3, 28, 42),
                   dot=(240, 250, 248), dota=14, lb=(255, 214, 102), ln=(3, 28, 42), acc2=(255, 120, 100), glow=(120, 255, 230)),
    "sunset": dict(bg0=(255, 132, 94), bg1=(98, 30, 96), fg=(255, 248, 240), acc=(255, 226, 120), mut=(196, 112, 122), card=(124, 44, 106), ink=(58, 16, 66),
                   dot=(255, 248, 240), dota=14, lb=(255, 226, 120), ln=(58, 16, 66), acc2=(120, 240, 255), glow=(255, 200, 140)),
})


# ----------------------------------------------------------------------------- backgrounds
def aurora(theme, t, seed=1, blobs=3, speed=0.16, strength=0.62):
    """animated soft colour blobs over a vertical gradient (rendered at 1/6 size, smooth upscale) -> RGBA full frame"""
    th = THEMES[theme]
    w, h = 180, 320
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    xx, yy = xx / h, yy / h                      # both in units of frame height (xx runs 0..0.5625)
    k = np.clip(yy * 1.0, 0, 1)[..., None]
    base = np.array(th["bg0"], np.float32) * (1 - k) + np.array(th["bg1"], np.float32) * k
    rng = np.random.default_rng(seed)
    cols = [th["acc"], th.get("acc2", th["acc"]), th.get("glow", th["acc"])]
    for i in range(blobs):
        ph, sp = rng.uniform(0, 6.28, 4), rng.uniform(0.7, 1.3)
        cx = 0.28 + 0.30 * math.sin(t * speed * sp + ph[0])
        cy = 0.50 + 0.42 * math.cos(t * speed * 0.8 * sp + ph[1])
        r = rng.uniform(0.20, 0.34)
        g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))[..., None]
        a = strength * 0.55 * g
        base = base * (1 - a) + np.array(cols[i % 3], np.float32) * a
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    return im.convert("RGBA")


@lru_cache(None)
def _bokeh_layer(theme, seed, n):
    th = THEMES[theme]
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (W, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    for _ in range(n):
        x, y, r = rng.uniform(0, W), rng.uniform(0, H * 2), rng.uniform(5, 26)
        c = th["glow"] if rng.random() < 0.7 else th["fg"]
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(c) + (int(rng.uniform(14, 46)),))
    return im.filter(ImageFilter.GaussianBlur(2.2))


def bokeh(cv, t, theme=None, seed=4, n=46, speed=26):
    """slowly rising soft light particles (depth)"""
    theme = theme or TH.name
    lay = _bokeh_layer(theme, seed, n)
    off = int((t * speed) % H)
    cv.alpha_composite(lay.crop((0, off, W, off + H)))


# ----------------------------------------------------------------------------- camera
class Cam:
    """keyframed camera (zoom, dx, dy, rot) with eased interpolation + shake and punch events"""

    def __init__(self, zoom=1.06):
        self.keys = [(0.0, zoom, 0.0, 0.0, 0.0)]
        self.shakes, self.punches = [], []

    def key(self, t, zoom=1.06, dx=0.0, dy=0.0, rot=0.0):
        self.keys.append((float(t), zoom, dx, dy, rot))
        self.keys.sort()
        return self

    def shake(self, t0, mag=16.0, dur=0.55):
        self.shakes.append((t0, mag, dur))
        return self

    def punch(self, t0, amt=0.05, dur=0.40):
        self.punches.append((t0, amt, dur))
        return self

    def __call__(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            z, dx, dy, rot = ks[0][1:]
        elif t >= ks[-1][0]:
            z, dx, dy, rot = ks[-1][1:]
        else:
            for a, b in zip(ks, ks[1:]):
                if a[0] <= t < b[0]:
                    p = ease_in_out((t - a[0]) / max(1e-6, b[0] - a[0]))
                    z, dx, dy, rot = [lerp(u, v, p) for u, v in zip(a[1:], b[1:])]
                    break
        for t0, amt, dur in self.punches:
            p = (t - t0) / dur
            if 0 <= p < 1:
                z += amt * math.sin(math.pi * min(1, p * 1.6)) * (1 - p) ** 1.5
        for t0, mag, dur in self.shakes:
            p = (t - t0) / dur
            if 0 <= p < 1:
                k = (1 - p) ** 2 * mag
                dx += k * math.sin(t * 71 + 1.3)
                dy += k * math.cos(t * 59 + 0.4)
                rot += k * 0.018 * math.sin(t * 43)
        return z, dx, dy, rot


def apply_camera(img, z, dx, dy, rot):
    if abs(z - 1) < 1e-4 and abs(dx) + abs(dy) + abs(rot) < 1e-4:
        return img
    cx, cy = W / 2, H / 2
    s = 1.0 / z
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    a, b, c = s * ca, -s * sa, cx - s * (ca * cx - sa * cy) - dx
    d, e, f = s * sa, s * ca, cy - s * (sa * cx + ca * cy) - dy
    return img.transform((W, H), Image.AFFINE, (a, b, c, d, e, f), resample=Image.BICUBIC)


# ----------------------------------------------------------------------------- whip blur + light sweep (scene transitions)
def motion_blur(img, px, angle_deg=0.0, taps=9):
    """directional motion blur: running average of translated copies"""
    if px < 1.0:
        return img
    ang = math.radians(angle_deg)
    acc = None
    for i in range(taps):
        o = (i / (taps - 1) - 0.5) * px
        sh = img.transform(img.size, Image.AFFINE, (1, 0, -o * math.cos(ang), 0, 1, -o * math.sin(ang)), resample=Image.BILINEAR)
        acc = sh if acc is None else Image.blend(acc, sh, 1.0 / (i + 1))
    return acc


@lru_cache(None)
def _sweep_coord(angle_deg):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = math.radians(angle_deg)
    s_ = xx * math.cos(a) + yy * math.sin(a)
    return s_, float(s_.min()), float(s_.max())


def light_sweep(img, p, angle_deg=62.0, width=150.0, col=(255, 232, 178), amt=0.5):
    """a soft bright diagonal band travelling across the frame (p 0..1)"""
    s_, lo, hi = _sweep_coord(angle_deg)
    pos = lo - width * 2 + (hi - lo + width * 4) * p
    band = np.exp(-((s_ - pos) / width) ** 2) * amt
    a = np.asarray(img.convert("RGB"), np.float32)
    a = a + band[..., None] * np.array(col, np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


# ----------------------------------------------------------------------------- post FX (vignette, bloom, grain, chroma, flash)
@lru_cache(None)
def _vig(strength):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 1.414
    return (1 - strength * np.clip(r, 0, 1) ** 2.2)[..., None]


_GR = None


def _grain(i):
    global _GR
    if _GR is None:
        _GR = (np.random.default_rng(3).normal(0, 1, (6, H, W)) * 9).astype(np.int8)
    return _GR[i % 6]


def post(img, t, idx, vignette=0.5, grain=0.5, bloom=0.30, bloom_thr=0.60, tint=(1.0, 1.0, 1.0), chroma=0.0, flash=0.0, flash_col=(255, 255, 255)):
    rgb = img.convert("RGB")
    a = np.asarray(rgb, np.float32)
    if bloom > 0:
        sm = np.asarray(rgb.resize((W // 8, H // 8), Image.BILINEAR), np.float32) / 255
        m = np.clip((sm.max(axis=2, keepdims=True) - bloom_thr) / (1 - bloom_thr), 0, 1)
        bl = Image.fromarray((sm * m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BICUBIC)
        a = a + bloom * np.asarray(bl, np.float32)
    if chroma > 0.4:
        ch = int(round(chroma))
        a[..., 0] = np.roll(a[..., 0], ch, axis=1)
        a[..., 2] = np.roll(a[..., 2], -ch, axis=1)
    if vignette > 0:
        a = a * _vig(vignette)
    if tint != (1.0, 1.0, 1.0):
        a = a * np.array(tint, np.float32)
    if grain > 0:
        a = a + _grain(idx)[..., None].astype(np.float32) * grain
    if flash > 0.004:
        a = a * (1 - flash) + np.array(flash_col, np.float32) * flash
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


# ----------------------------------------------------------------------------- the premium reel
class PremiumReel(Reel):
    """scenes draw onto an animated background; then camera -> post FX -> brand mark -> end card.

    cam      : Cam()                      camera (always give it a slow push-in/drift)
    world    : theme name (navy ink slate cream amber noir neon gold paper teal sunset)
    seed     : aurora blob seed (different per video)
    flashes  : [(t, dur)] white flashes (cut accents);  chroma_at : [(t, px, dur)] RGB split pulses
    """

    def __init__(self, tim, scenes, world="noir", cam=None, seed=1, bokeh_n=40, vignette=0.5, grain=0.5, bloom=0.30,
                 tint=(1.0, 1.0, 1.0), flashes=(), chroma_at=(), aurora_strength=0.62, mark=True, top=(), whips=(), sweeps=(), **kw):
        super().__init__(tim, scenes, theme=world, header=False, **kw)
        self.world, self.cam, self.seed = world, cam or Cam(), seed
        self.bokeh_n, self.vig, self.grain, self.bloom, self.tint = bokeh_n, vignette, grain, bloom, tint
        self.flashes, self.chroma_at, self.astr, self.mark = list(flashes), list(chroma_at), aurora_strength, mark
        self.top = list(top)           # drawn AFTER camera + post (stable, crisp): captions, brand mark
        self.whips, self.sweeps = list(whips), list(sweeps)    # whips: [(t, dur, px, angle_deg)] motion blur at cuts; sweeps: [(t, dur)] light sweeps

    def draw(self, t):
        tim = self.tim
        set_theme(self.world)
        cv = aurora(self.world, t, self.seed, strength=self.astr)
        if self.bokeh_n:
            bokeh(cv, t, self.world, self.seed + 3, self.bokeh_n)
        for fn in self.scenes:
            fn(cv, t)
        cv = apply_camera(cv, *self.cam(t))
        for t0, dur, px, ang in self.whips:
            p = (t - t0) / dur
            if 0 <= p < 1:
                cv = motion_blur(cv, px * (1 - p) ** 1.6, ang)
        for t0, dur in self.sweeps:
            p = (t - t0) / dur
            if 0 <= p < 1:
                cv = light_sweep(cv, ease_in_out(p), amt=0.55 * math.sin(math.pi * min(1, p * 1.15)) ** 0.7)
        ch = 0.0
        for t0, px, dur in self.chroma_at:
            p = (t - t0) / dur
            if 0 <= p < 1:
                ch = max(ch, px * (1 - p))
        fl = 0.0
        for t0, dur in self.flashes:
            p = (t - t0) / dur
            if 0 <= p < 1:
                fl = max(fl, (1 - p) ** 2 * 0.85)
        tint = self.tint(t) if callable(self.tint) else self.tint
        cv = post(cv, t, int(round(t * FPS)), self.vig, self.grain, self.bloom, tint=tint, chroma=ch, flash=fl)
        for fn in self.top:
            fn(cv, t)
        # brand mark (small, calm) + cover-up before the end card
        if self.mark:
            hdr = clamp((tim.end0 - 0.15 - t) / 0.25)
            if hdr > 0:
                tl = txt("Narx Tili", 32, TH.fg, "b")
                x0 = 540 - (50 + 12 + tl.width) / 2
                put(cv, logo(50, TH.lb, TH.ln, TH.ln), x0 + 25, 292, hdr * 0.75)
                put(cv, tl, x0 + 62 + tl.width / 2, 292, hdr * 0.75)
        k = clamp((t - (tim.end0 - 0.28)) / 0.28)
        if k > 0:
            cover = aurora(self.world, t, self.seed, strength=self.astr * 0.6)
            ov = Image.new("RGBA", (W, H), tuple(TH.bg1) + (int(255 * k),))
            cv.alpha_composite(ov)
            self.end_card(cv, t)
        return cv


# ----------------------------------------------------------------------------- text
@lru_cache(None)
def stext(s, size, fill, stroke=(0, 0, 0), sw=6, weight="xb"):
    """text with outline (captions, hero words)"""
    font = F(weight, size)
    asc, desc = font.getmetrics()
    pad = sw + 10
    img = Image.new("RGBA", (int(font.getlength(s)) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((pad, pad), s, font=font, fill=tuple(fill) + (255,), stroke_width=sw, stroke_fill=tuple(stroke) + (255,))
    return img


def fit_stext(s, size, fill, maxw=900, stroke=(0, 0, 0), sw=6, weight="xb"):
    z = size
    while z > 30:
        im = stext(s, z, tuple(fill), tuple(stroke), max(2, int(sw * z / size)), weight)
        if im.width <= maxw + 2 * (sw + 10):
            return im
        z -= 4
    return stext(s, z, tuple(fill), tuple(stroke), sw, weight)


@lru_cache(None)
def gtext(s, size, c0, c1, weight="xb"):
    """vertical-gradient text (metal / gold)"""
    base = rich(((s, (255, 255, 255)),), size, weight)
    w, h = base.size
    g = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    col = np.array(c0, np.float32) * (1 - g) + np.array(c1, np.float32) * g
    arr = np.concatenate([np.broadcast_to(col, (h, w, 3)), np.asarray(base.getchannel("A"), np.float32)[..., None]], axis=2)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


@lru_cache(None)
def extrude(s, size, face, side, depth=14, weight="xb"):
    """faux-3D text: stacked offset copies"""
    f = rich(((s, tuple(face)),), size, weight)
    b = rich(((s, tuple(side)),), size, weight)
    out = Image.new("RGBA", (f.width + depth, f.height + depth), (0, 0, 0, 0))
    for i in range(depth, 0, -2):
        out.alpha_composite(b, (i, i))
    out.alpha_composite(f, (0, 0))
    return out


# ----------------------------------------------------------------------------- light, depth
def glow(layer, col, r=28, k=1.4):
    pad = int(r * 3)
    w, h = layer.size
    a = Image.new("L", (w + 2 * pad, h + 2 * pad), 0)
    a.paste(layer.getchannel("A"), (pad, pad))
    a = a.filter(ImageFilter.GaussianBlur(r)).point(lambda v: min(255, int(v * k)))
    g = Image.new("RGBA", a.size, tuple(col) + (0,))
    g.putalpha(a)
    g.alpha_composite(layer, (pad, pad))
    return g


def shadowed(layer, blur=26, off=(0, 20), alpha=0.5, col=(0, 0, 0)):
    pad = int(blur * 3)
    w, h = layer.size
    a = Image.new("L", (w + 2 * pad, h + 2 * pad), 0)
    a.paste(layer.getchannel("A"), (pad + off[0], pad + off[1]))
    a = a.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha))
    g = Image.new("RGBA", a.size, tuple(col) + (0,))
    g.putalpha(a)
    g.alpha_composite(layer, (pad, pad))
    return g


@lru_cache(None)
def glass(w, h, r=44, tint=(255, 255, 255), a=30, border=(255, 255, 255), ba=90):
    """translucent glass card with soft top sheen"""
    s = 2
    im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=r * s, fill=tuple(tint) + (a,),
                                         outline=tuple(border) + (ba,), width=2 * s)
    sheen = np.zeros((h * s, w * s, 4), np.uint8)
    sheen[..., :3] = 255
    gradient = np.clip(1 - np.linspace(0, 2.2, h * s), 0, 1)[:, None] * 44
    sheen[..., 3] = gradient.astype(np.uint8)
    sh = Image.fromarray(sheen, "RGBA")
    mask = Image.new("L", (w * s, h * s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w * s - 1, h * s - 1], radius=r * s, fill=255)
    sh.putalpha(Image.fromarray((np.asarray(sh.getchannel("A"), np.float32) * np.asarray(mask, np.float32) / 255).astype(np.uint8)))
    im.alpha_composite(sh)
    return im.resize((w, h), Image.LANCZOS)


def spot(cv, cx, cy, r, dark=0.82, col=(0, 0, 0), soft=0.7):
    """darken everything except a soft circle (spotlight / reveal)"""
    sw, sh = W // 4, H // 4
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    d = np.sqrt((xx - cx / 4) ** 2 + (yy - cy / 4) ** 2) / max(1.0, r / 4)
    a = np.clip((d - (1 - soft)) / soft, 0, 1) * dark
    ov = np.zeros((sh, sw, 4), np.uint8)
    ov[..., :3] = col
    ov[..., 3] = (a * 255).astype(np.uint8)
    cv.alpha_composite(Image.fromarray(ov, "RGBA").resize((W, H), Image.BICUBIC))


def rays(cv, cx, cy, t, col=(255, 220, 140), n=14, alpha=0.16, spin=6.0, length=2400):
    """rotating light rays from a point (reveal / vault light)"""
    sw, sh = W // 4, H // 4
    ov = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov, "RGBA")
    for i in range(n):
        a0 = math.radians(t * spin + i * 360 / n)
        wd = math.radians(360 / n * 0.34)
        pts = [(cx / 4, cy / 4)] + [((cx + math.cos(a0 + s * wd) * length) / 4, (cy + math.sin(a0 + s * wd) * length) / 4) for s in (-1, 1)]
        d.polygon(pts, fill=tuple(col) + (int(255 * alpha),))
    ov = ov.filter(ImageFilter.GaussianBlur(2)).resize((W, H), Image.BICUBIC)
    cv.alpha_composite(ov)


def sparks(cv, t, t0, cx, cy, n=30, col=(255, 210, 90), seed=1, life=0.9, speed=640, size=7, grav=760, r0=0.0):
    p = t - t0
    if p < 0 or p > life:
        return
    rng = np.random.default_rng(seed)
    ang, sp = rng.uniform(0, 2 * math.pi, n), rng.uniform(0.25, 1.0, n) * speed
    d = ImageDraw.Draw(cv, "RGBA")
    fade = 1 - p / life
    for a, s in zip(ang, sp):
        x, y = cx + math.cos(a) * (r0 + s * p), cy + math.sin(a) * (r0 + s * p) + 0.5 * grav * p * p
        r = size * (0.5 + 0.7 * fade)
        d.ellipse([x - r * 2.2, y - r * 2.2, x + r * 2.2, y + r * 2.2], fill=tuple(col) + (int(40 * fade),))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, int(255 * fade)))


@lru_cache(maxsize=512)
def ring_img(d, pq, col, track, th):
    s = 2
    im = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    box = [th * s / 2, th * s / 2, (d - th / 2) * s, (d - th / 2) * s]
    dr.arc(box, 0, 360, fill=tuple(track), width=th * s)
    if pq > 0:
        dr.arc(box, -90, -90 + 360 * pq, fill=tuple(col) + (255,), width=th * s)
        for ang in (-90, -90 + 360 * pq):
            x = d * s / 2 + math.cos(math.radians(ang)) * (d - th) * s / 2
            y = d * s / 2 + math.sin(math.radians(ang)) * (d - th) * s / 2
            dr.ellipse([x - th * s / 2, y - th * s / 2, x + th * s / 2, y + th * s / 2], fill=tuple(col) + (255,))
    return im.resize((d, d), Image.LANCZOS)


def ring(d, p, col, track=(255, 255, 255, 36), th=22):
    """progress ring layer (p 0..1), quantised to 1/90 for caching"""
    return ring_img(d, round(clamp(p) * 90) / 90, tuple(col), tuple(track), th)


def put_xs(cv, layer, cx, cy, sx=1.0, alpha=1.0, sy=1.0):
    """horizontally/vertically squashed composite (card flip: sx = |cos|)"""
    w, h = layer.size
    nw, nh = max(1, int(w * abs(sx))), max(1, int(h * sy))
    put(cv, layer.resize((nw, nh), Image.BILINEAR), cx, cy, alpha)


def _coeffs(dst, src):
    A, B = [], []
    for (x, y), (X, Y) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -X * x, -X * y], [0, 0, 0, x, y, 1, -Y * x, -Y * y]]
        B += [X, Y]
    return np.linalg.solve(np.array(A, float), np.array(B, float))


def warp4(layer, dst_quad):
    """perspective: where the 4 corners (TL,TR,BR,BL) of `layer` land -> returns a new RGBA of the quad's bounding box"""
    xs, ys = [p[0] for p in dst_quad], [p[1] for p in dst_quad]
    x0, y0 = min(xs), min(ys)
    w, h = int(max(xs) - x0) + 1, int(max(ys) - y0) + 1
    q = [(x - x0, y - y0) for x, y in dst_quad]
    lw, lh = layer.size
    c = _coeffs(q, [(0, 0), (lw, 0), (lw, lh), (0, lh)])
    return layer.transform((w, h), Image.PERSPECTIVE, tuple(c), resample=Image.BICUBIC), (x0 + w / 2, y0 + h / 2)


# ----------------------------------------------------------------------------- karaoke captions
def _chunks(tim, n=3):
    if getattr(tim, "_chunks", None) is None:
        out = []
        for sg in tim.segs:
            a, b = sg["a"], sg["b"]
            i = a
            while i <= b:
                j = min(b, i + n - 1)
                if b - j == 1:          # avoid a one-word orphan chunk
                    j = b
                out.append((i, j))
                i = j + 1
        tim._chunks = out
    return tim._chunks


def captions(cv, tim, t, y=1385, size=66, maxw=940, n=3, col=None, hi=None, alpha=1.0):
    """word-by-word captions: the chunk being spoken is shown, the active word pops in the accent colour"""
    col, hi = col or TH.fg, hi or TH.acc
    if t >= tim.end0 - 0.05:
        return
    cur = None
    chunks = _chunks(tim, n)
    for k, (i, j) in enumerate(chunks):
        end = tim.ws(chunks[k + 1][0]) if k + 1 < len(chunks) else tim.we(j) + 0.3
        if tim.ws(i) - 0.04 <= t < max(end, tim.we(j) + 0.12):
            cur = (i, j)
    if not cur:
        return
    i0, j0 = cur
    words = [tim.words[i]["t"] for i in range(i0, j0 + 1)]
    z = size
    while z > 36:
        widths = [F("xb", z).getlength(w) for w in words]
        if sum(widths) + 22 * (len(words) - 1) <= maxw:
            break
        z -= 4
    gap = 26
    act = i0
    for i in range(i0, j0 + 1):
        if tim.ws(i) <= t:
            act = i
    scs = []
    for idx in range(len(words)):
        i = i0 + idx
        scs.append(1.0 + (0.10 * math.sin(math.pi * clamp((t - tim.ws(i)) / 0.22)) ** 0.8 + 0.03 if i == act else 0.0))
    total = sum(w_ * s_ for w_, s_ in zip(widths, scs)) + gap * (len(words) - 1)
    x = 540 - total / 2
    for idx, w in enumerate(words):
        i = i0 + idx
        lay = stext(w, z, tuple(hi if i == act else col), (0, 0, 0), max(4, z // 10))
        a = alpha * (1.0 if i <= act else 0.55)
        wd = widths[idx] * scs[idx]
        put(cv, lay, x + wd / 2, y - (4 if i == act else 0), a, scs[idx])
        x += wd + gap


# ----------------------------------------------------------------------------- tiny helpers for scenes
def pop(cv, layer, cx, cy, t, t0, dur=0.34, al=1.0, rise=0.0, overshoot=1.5):
    """scale-pop entrance (premium default): 0.6 -> 1 with overshoot + fade"""
    p = (t - t0) / dur
    if p <= 0:
        return
    sc = 0.55 + 0.45 * ease_out_back(p, overshoot)
    put(cv, layer, cx, cy + (1 - ease_out_cubic(p)) * rise, al * clamp(p * 2.2), sc)


def rolling_digits(t, t_lock, final, digits=2, seed=3, rate=22):
    """slot-machine number: random digits until t_lock, then `final`"""
    if t >= t_lock:
        return str(final)
    rng = np.random.default_rng(seed + int(t * rate))
    return "".join(str(int(x)) for x in rng.integers(0, 10, digits))


def count_up(t, a, dur, v0, v1):
    return lerp(v0, v1, ease_out_cubic((t - a) / dur))
