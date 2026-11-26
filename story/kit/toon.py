"""toon.py - flat-colour, thick-outline 2D cartoon characters with a real skeleton (Sirli Hikoyalar).

    from toon import Toon, JASUR, MALIKA, Cat
    c = Toon(JASUR, env=speech_env(wav))             # lip-sync from the voice envelope
    c.draw(cv, t, x, ground_y, scale=1.0, facing=+1, pose=<dict>, expr="smile")

Local space: origin = ground point under the character, +x = facing direction, y down, units ~ px at scale 1.0.
Body: legs (thigh+shin+shoe) x2, torso, neck, head (face drawn every frame: eyes, brows, mouth visemes, blink), arms (upper+fore+hand) x2.
Angles (deg): arm = (shoulder, elbow): shoulder measured from straight DOWN, positive swings FORWARD/UP; elbow adds to it (positive bends the
forearm forward/up).  leg = (hip, knee): knee negative bends the shin backwards.
pose keys: lean (torso deg), head (tilt deg), ya (head yaw -1..1 look back/forward), bob (px), dx, arm_n / arm_f / leg_n / leg_f (tuples), crouch (px)
Named arm poses + walk cycle helpers at the bottom.
"""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

D = 1.6            # sprite density (px per local unit); final scale = scale / D
OL = (22, 16, 40)  # outline colour
OW = 5.0           # outline width (local units)


def lerp(a, b, p): return a + (b - a) * p
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(p): p = clamp(p); return p * p * (3 - 2 * p)


def mix(c0, c1, k): return tuple(int(lerp(a, b, k)) for a, b in zip(c0, c1))


def shade(c, k=0.78): return tuple(int(v * k) for v in c)


def light(c, k=0.18): return tuple(int(v + (255 - v) * k) for v in c)


# ----------------------------------------------------------------------------- sprite helpers
def _canvas(w, h): return Image.new("RGBA", (int(w * D), int(h * D)), (0, 0, 0, 0))


def _px(v): return v * D


def _shape_outlined(size, draw_fn, fill, shadow=None, shadow_fn=None, ow=OW):
    """draw_fn(draw, grow) draws the shape expanded by `grow` units. Returns RGBA with outline (+ optional cel shadow)."""
    w, h = size
    im = _canvas(w, h)
    d = ImageDraw.Draw(im)
    draw_fn(d, ow)
    # recolour everything drawn so far as outline
    a = im.getchannel("A")
    im = Image.new("RGBA", im.size, OL + (0,))
    im.putalpha(a)
    d = ImageDraw.Draw(im)
    fill_im = _canvas(w, h)
    fd = ImageDraw.Draw(fill_im)
    draw_fn(fd, 0.0)
    m = fill_im.getchannel("A")
    base = Image.new("RGBA", im.size, tuple(fill) + (255,))
    im.paste(base, (0, 0), m)
    if shadow is not None and shadow_fn is not None:
        sh = _canvas(w, h)
        sd = ImageDraw.Draw(sh)
        shadow_fn(sd)
        sm = Image.fromarray((np.array(sh.getchannel("A"), np.float32) * np.array(m, np.float32) / 255).astype(np.uint8))
        im.paste(Image.new("RGBA", im.size, tuple(shadow) + (255,)), (0, 0), sm)
    return im


def rr(d, box, r, fill, grow=0.0):
    x0, y0, x1, y1 = box
    d.rounded_rectangle([_px(x0 - grow), _px(y0 - grow), _px(x1 + grow), _px(y1 + grow)], radius=_px(r + grow), fill=fill)


def el(d, box, fill, grow=0.0):
    x0, y0, x1, y1 = box
    d.ellipse([_px(x0 - grow), _px(y0 - grow), _px(x1 + grow), _px(y1 + grow)], fill=fill)


def pg(d, pts, fill):
    d.polygon([(_px(x), _px(y)) for x, y in pts], fill=fill)


def ln(d, pts, fill, w):
    d.line([(_px(x), _px(y)) for x, y in pts], fill=fill, width=max(1, int(_px(w))), joint="curve")


def rot_about_center(sprite, deg):
    return sprite.rotate(deg, resample=Image.BICUBIC, expand=False) if abs(deg) > 0.05 else sprite


def paste_c(dst, sprite, cx, cy):
    """paste sprite centred at (cx, cy) in dst pixel coordinates"""
    x, y = int(round(cx - sprite.width / 2)), int(round(cy - sprite.height / 2))
    dst.alpha_composite(sprite, (x, y)) if x >= 0 and y >= 0 and x + sprite.width <= dst.width and y + sprite.height <= dst.height else _safe_paste(dst, sprite, x, y)


def _safe_paste(dst, sp, x, y):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.width, x + sp.width), min(dst.height, y + sp.height)
    if x1 <= x0 or y1 <= y0:
        return
    dst.alpha_composite(sp.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


# ----------------------------------------------------------------------------- limb sprites (pivot = sprite centre)
@lru_cache(None)
def limb_sprite(w, length, col, shade_col, hand=None, shoe=None, R=None, kind="arm"):
    """A limb segment hanging DOWN from the pivot (sprite centre). R = half canvas size (units).
    hand: skin colour -> draws a hand circle at the end. shoe: colour -> not used here (feet are separate)."""
    R = R or (length + 30)
    im = _canvas(2 * R, 2 * R)
    cx = R

    def dfn(d, grow):
        rr(d, (cx - w / 2, R - 6, cx + w / 2, R + length), w / 2, (0, 0, 0, 255), grow)
        if hand:
            el(d, (cx - w * 0.62, R + length - w * 0.55, cx + w * 0.62, R + length + w * 0.75), (0, 0, 0, 255), grow)

    base = _shape_outlined((2 * R, 2 * R), dfn, col, shade_col, lambda sd: rr(sd, (cx + w * 0.08, R - 6, cx + w / 2 + 2, R + length), w / 2, (0, 0, 0, 255)))
    if hand:
        # re-paint the hand skin over the sleeve end
        hm = _canvas(2 * R, 2 * R)
        hd = ImageDraw.Draw(hm)
        el(hd, (cx - w * 0.62, R + length - w * 0.55, cx + w * 0.62, R + length + w * 0.75), (0, 0, 0, 255), 0.0)
        base.paste(Image.new("RGBA", base.size, tuple(hand) + (255,)), (0, 0), hm.getchannel("A"))
        sm = _canvas(2 * R, 2 * R)
        sd = ImageDraw.Draw(sm)
        el(sd, (cx + w * 0.12, R + length - w * 0.5, cx + w * 0.7, R + length + w * 0.75), (0, 0, 0, 255), 0.0)
        sa = Image.fromarray((np.array(sm.getchannel("A"), np.float32) * np.array(hm.getchannel("A"), np.float32) / 255).astype(np.uint8))
        base.paste(Image.new("RGBA", base.size, shade(hand, 0.86) + (255,)), (0, 0), sa)
    return base


@lru_cache(None)
def foot_sprite(col, sole=(245, 245, 250), L=64, H=30, R=60):
    im = _canvas(2 * R, 2 * R)

    def dfn(d, grow):
        # shoe pointing +x, pivot (ankle) at the centre
        rr(d, (-14 + R, R - 10, R + L - 14, R + H - 10), 14, (0, 0, 0, 255), grow)
    base = _shape_outlined((2 * R, 2 * R), dfn, col, shade(col, 0.8),
                           lambda sd: rr(sd, (-14 + R, R + H * 0.45 - 10, R + L - 14, R + H - 10), 10, (0, 0, 0, 255)))
    sd = ImageDraw.Draw(base)
    rr(sd, (-12 + R, R + H - 17, R + L - 16, R + H - 10), 4, sole + (255,))
    return base


# ----------------------------------------------------------------------------- characters
class Spec:
    def __init__(self, **kw):
        self.__dict__.update(kw)


JASUR = Spec(name="jasur", skin=(232, 174, 130), hair=(36, 28, 40), top=(238, 120, 44), top2=(250, 190, 90), pants=(48, 62, 120), shoe=(236, 236, 240),
             girl=False, arm_w=34, torso_w=124, torso_h=150, head_w=196, head_h=202, leg_w=44, sh_x=(-8, 20), kind="hoodie", scale=1.0)
MALIKA = Spec(name="malika", skin=(244, 196, 158), hair=(62, 34, 42), top=(36, 150, 150), top2=(240, 240, 246), pants=(40, 46, 70), shoe=(240, 80, 110),
              girl=True, arm_w=31, torso_w=112, torso_h=146, head_w=192, head_h=200, leg_w=40, sh_x=(-8, 18), kind="blazer", scale=1.0)
KARIM = Spec(name="karim", skin=(214, 160, 120), hair=(190, 190, 196), top=(84, 62, 120), top2=(220, 180, 70), pants=(70, 60, 56), shoe=(80, 56, 40),
             girl=False, arm_w=36, torso_w=132, torso_h=156, head_w=194, head_h=206, leg_w=44, sh_x=(-8, 20), kind="chapan", scale=1.0, old=True)

EXPR = {
    #            brow y, brow ang (inner up +), eye open, pupil dy, mouth curve (smile+), mouth w, blush, brow gap
    "neutral":   dict(by=0, ba=0, eo=1.0, pr=1.0, sm=0.15, mw=1.0, bl=0.0),
    "smile":     dict(by=-2, ba=-4, eo=0.95, pr=1.0, sm=0.7, mw=1.1, bl=0.5),
    "grin":      dict(by=-6, ba=-8, eo=0.9, pr=1.0, sm=1.0, mw=1.25, bl=0.7),
    "worried":   dict(by=-6, ba=16, eo=1.05, pr=0.95, sm=-0.35, mw=0.9, bl=0.0),
    "scared":    dict(by=-16, ba=18, eo=1.35, pr=0.72, sm=-0.5, mw=0.95, bl=0.0),
    "surprised": dict(by=-18, ba=4, eo=1.4, pr=0.8, sm=0.0, mw=0.7, bl=0.0),
    "angry":     dict(by=6, ba=-22, eo=0.85, pr=1.0, sm=-0.4, mw=1.0, bl=0.0),
    "determined": dict(by=3, ba=-14, eo=0.92, pr=1.0, sm=0.05, mw=0.9, bl=0.0),
    "sly":       dict(by=-3, ba=-10, eo=0.62, pr=1.0, sm=0.55, mw=1.0, bl=0.3),
    "sad":       dict(by=-4, ba=20, eo=0.85, pr=1.0, sm=-0.6, mw=0.8, bl=0.0),
    "shout":     dict(by=-8, ba=10, eo=1.25, pr=0.85, sm=0.0, mw=1.1, bl=0.0),
}


def expr_at(keys, t):
    """keys = [(t0, name, fade)] sorted; returns blended param dict"""
    if not keys:
        return dict(EXPR["neutral"])
    cur = dict(EXPR[keys[0][1]])
    for i in range(1, len(keys)):
        t0, name, fd = keys[i]
        p = smooth((t - t0) / max(fd, 1e-3))
        if t < t0 - 1e-6:
            break
        tgt = EXPR[name]
        if p < 1.0:
            return {k: lerp(cur[k], tgt[k], p) for k in cur}
        cur = dict(tgt)
    return cur


class Toon:
    def __init__(self, spec, env=None, blinks=(), expr_keys=None):
        self.s = spec
        self.env = env
        self.blinks = tuple(blinks)
        self.expr_keys = expr_keys or [(0.0, "neutral", 0.1)]
        self._parts()

    # ---------------------------------------------------------- static parts
    def _parts(self):
        s = self.s
        aw = s.arm_w
        sleeve = s.top if s.kind != "chapan" else s.top
        self.upper = limb_sprite(aw, 78, sleeve, shade(sleeve), None, None, R=110)
        self.fore = limb_sprite(aw - 3, 72, sleeve if s.kind in ("hoodie", "chapan") else s.top, shade(sleeve), s.skin, None, R=110)
        if s.kind == "blazer":
            self.fore = limb_sprite(aw - 4, 72, s.top2, shade(s.top2, 0.82), s.skin, None, R=110)
        self.thigh = limb_sprite(s.leg_w, 100, s.pants, shade(s.pants), None, None, R=125)
        self.shin = limb_sprite(s.leg_w - 4, 92, s.pants, shade(s.pants), None, None, R=125)
        self.foot = foot_sprite(s.shoe)
        self.torso = self._torso()
        self.head_back, self.head_front = self._head()

    def _torso(self):
        s = self.s
        w, h = s.torso_w, s.torso_h
        R = 140
        im_w, im_h = 2 * R, 2 * R  # pivot (waist centre) at the sprite centre
        cx = R
        top = R - h   # shoulder line
        bot = R + 14

        def dfn(d, grow):
            # rounded trapezoid body
            pts = [(cx - w * 0.5, top + 10), (cx - w * 0.40, top), (cx + w * 0.40, top), (cx + w * 0.5, top + 10), (cx + w * 0.46, bot - 8), (cx + w * 0.38, bot),
                   (cx - w * 0.38, bot), (cx - w * 0.46, bot - 8)]
            g = grow
            d.polygon([(_px(x + (g if x > cx else -g)), _px(y + (g if y > (top + bot) / 2 else -g))) for x, y in pts], fill=(0, 0, 0, 255))
            rr(d, (cx - w * 0.5, top - 2, cx + w * 0.5, top + 40), 18, (0, 0, 0, 255), g)

        im = _shape_outlined((im_w, im_h), dfn, s.top, shade(s.top),
                             lambda sd: pg(sd, [(cx + w * 0.12, top - 4), (cx + w * 0.55, top - 4), (cx + w * 0.55, bot + 2), (cx + w * 0.16, bot + 2)], (0, 0, 0, 255)))
        d = ImageDraw.Draw(im)
        if s.kind == "hoodie":
            # hood collar + drawstrings + kangaroo pocket
            ln(d, [(cx - w * 0.30, top + 6), (cx, top + 34), (cx + w * 0.30, top + 6)], OL + (255,), 5)
            ln(d, [(cx - 14, top + 32), (cx - 17, top + 72)], light(s.top2, 0.5) + (255,), 5)
            ln(d, [(cx + 14, top + 32), (cx + 17, top + 70)], light(s.top2, 0.5) + (255,), 5)
            ln(d, [(cx - w * 0.30, bot - 50), (cx - w * 0.22, bot - 22), (cx + w * 0.22, bot - 22), (cx + w * 0.30, bot - 50)], OL + (255,), 4)
        elif s.kind == "blazer":
            pg(d, [(cx - 22, top + 2), (cx + 22, top + 2), (cx, top + 64)], s.top2 + (255,))
            ln(d, [(cx - 22, top + 2), (cx, top + 64), (cx + 22, top + 2)], OL + (255,), 4)
            ln(d, [(cx - 34, top + 2), (cx - 8, top + 56)], OL + (255,), 4)
            ln(d, [(cx + 34, top + 2), (cx + 8, top + 56)], OL + (255,), 4)
            el(d, (cx - 7, top + 44, cx + 7, top + 58), (240, 80, 110, 255))
            for k in range(2):
                el(d, (cx + 18, top + 78 + k * 28, cx + 27, top + 87 + k * 28), (250, 210, 100, 255))
        else:  # chapan - striped robe
            for k in range(-3, 4):
                ln(d, [(cx + k * 17, top + 6), (cx + k * 17, bot - 4)], s.top2 + (255,), 5)
            ln(d, [(cx - w * 0.5, bot - 40), (cx + w * 0.5, bot - 40)], OL + (255,), 4)
        # belt
        return im

    def _head(self):
        s = self.s
        w, h = s.head_w, s.head_h
        R = 190
        cx, cy = R, R
        skin, hair = s.skin, s.hair

        def head_dfn(d, grow):
            el(d, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), (0, 0, 0, 255), grow)
            # jaw softening
            rr(d, (cx - w * 0.40, cy + h * 0.05, cx + w * 0.40, cy + h * 0.5), 40, (0, 0, 0, 255), grow)

        back = _canvas(2 * R, 2 * R)
        if s.girl:
            def hb(d, grow):
                rr(d, (cx - w * 0.60, cy - h * 0.55, cx + w * 0.60, cy + h * 0.95), 60, (0, 0, 0, 255), grow)
            back = _shape_outlined((2 * R, 2 * R), hb, hair, shade(hair, 0.78), lambda sd: rr(sd, (cx + w * 0.1, cy - h * 0.5, cx + w * 0.65, cy + h), 40, (0, 0, 0, 255)))
        elif getattr(s, "old", False):
            pass
        face = _shape_outlined((2 * R, 2 * R), head_dfn, skin, shade(skin, 0.9),
                               lambda sd: el(sd, (cx + w * 0.25, cy - h * 0.5, cx + w * 0.75, cy + h * 0.6), (0, 0, 0, 255)))
        back.alpha_composite(face)
        # ears
        for ex in (-1, 1):
            eim = _canvas(2 * R, 2 * R)
            ed = ImageDraw.Draw(eim)
            el(ed, (cx + ex * w * 0.5 - 15, cy - 10, cx + ex * w * 0.5 + 15, cy + 42), OL + (255,), 0)
            el(ed, (cx + ex * w * 0.5 - 11, cy - 6, cx + ex * w * 0.5 + 11, cy + 38), skin + (255,), 0)
            back.alpha_composite(eim)
        # front hair
        fr = _canvas(2 * R, 2 * R)
        fd = ImageDraw.Draw(fr)

        def fdfn(d, grow):
            top = cy - h / 2
            if s.name == "jasur":
                # cap of hair + quiff
                pts = [(cx - w * 0.52, cy - 6), (cx - w * 0.5, cy - h * 0.30), (cx - w * 0.36, top + 6), (cx - w * 0.1, top - 8), (cx + w * 0.14, top - 24),
                       (cx + w * 0.4, top - 8), (cx + w * 0.52, cy - h * 0.28), (cx + w * 0.54, cy - 4), (cx + w * 0.40, cy - h * 0.26), (cx + w * 0.18, cy - h * 0.34),
                       (cx - w * 0.06, cy - h * 0.30), (cx - w * 0.28, cy - h * 0.34), (cx - w * 0.44, cy - h * 0.22)]
                d.polygon([(_px(x + (grow if x > cx else -grow)), _px(y + (grow if y > cy - h * 0.3 else -grow))) for x, y in pts], fill=(0, 0, 0, 255))
            elif s.name == "malika":
                pts = [(cx - w * 0.56, cy + 14), (cx - w * 0.54, cy - h * 0.30), (cx - w * 0.38, top + 2), (cx, top - 12), (cx + w * 0.38, top + 2), (cx + w * 0.56, cy - h * 0.28),
                       (cx + w * 0.55, cy + 30), (cx + w * 0.44, cy - h * 0.20), (cx + w * 0.2, cy - h * 0.30), (cx - w * 0.05, cy - h * 0.18), (cx - w * 0.3, cy - h * 0.30),
                       (cx - w * 0.44, cy - h * 0.12)]
                d.polygon([(_px(x + (grow if x > cx else -grow)), _px(y + (grow if y > cy - h * 0.3 else -grow))) for x, y in pts], fill=(0, 0, 0, 255))
            else:  # old man: bald top with side hair + brows done in face
                el(d, (cx - w * 0.5, cy - 8, cx - w * 0.36, cy + 40), (0, 0, 0, 255), grow)
                el(d, (cx + w * 0.36, cy - 8, cx + w * 0.5, cy + 40), (0, 0, 0, 255), grow)

        fim = _shape_outlined((2 * R, 2 * R), fdfn, hair, shade(hair, 0.75))
        if s.name == "malika":
            # goggles pushed up on the forehead + clip
            gd = ImageDraw.Draw(fim)
            strap = (170, 120, 60, 255)
            ln(gd, [(cx - w * 0.52, cy - h * 0.30), (cx, cy - h * 0.42), (cx + w * 0.52, cy - h * 0.30)], OL + (255,), 12)
            ln(gd, [(cx - w * 0.52, cy - h * 0.30), (cx, cy - h * 0.42), (cx + w * 0.52, cy - h * 0.30)], strap, 7)
            for gx in (-26, 26):
                el(gd, (cx + gx - 25, cy - h * 0.50 - 5, cx + gx + 25, cy - h * 0.50 + 40), OL + (255,))
                el(gd, (cx + gx - 20, cy - h * 0.50, cx + gx + 20, cy - h * 0.50 + 34), (150, 210, 235, 255))
                el(gd, (cx + gx - 13, cy - h * 0.50 + 5, cx + gx - 3, cy - h * 0.50 + 15), (255, 255, 255, 200))
            rr(gd, (cx + w * 0.30, cy - h * 0.14, cx + w * 0.30 + 26, cy - h * 0.14 + 12), 5, (240, 80, 110, 255))
        if getattr(s, "old", False):
            # doppi (black skull cap with white embroidery)
            gd = ImageDraw.Draw(fim)
            dp = [(cx - w * 0.42, cy - h * 0.20), (cx - w * 0.36, cy - h * 0.55), (cx + w * 0.36, cy - h * 0.55), (cx + w * 0.42, cy - h * 0.20)]
            pg(gd, dp, (30, 30, 46, 255))
            ln(gd, dp + [dp[0]], OL + (255,), 5)
            for k in range(-2, 3):
                ln(gd, [(cx + k * 22, cy - h * 0.24), (cx + k * 22, cy - h * 0.48)], (240, 240, 240, 255), 4)
        fr = fim
        return back, fr

    # ---------------------------------------------------------- face (dynamic)
    def _face(self, t, yaw, ex, mouth_open, say_seed, look=(0.0, 0.0)):
        s = self.s
        w, h = s.head_w, s.head_h
        R = 190
        im = _canvas(2 * R, 2 * R)
        d = ImageDraw.Draw(im)
        cx, cy = R + yaw * 26, R + 12
        # blink
        blink = 1.0
        for b0 in self.blinks:
            if 0 <= t - b0 < 0.16:
                blink = abs((t - b0) / 0.08 - 1.0)
        eo = ex["eo"] * lerp(0.08, 1.0, blink) if blink < 1 else ex["eo"]
        eye_w, eye_h = 46, 56
        gap = 54
        for side in (-1, 1):
            sx = cx + side * gap + side * yaw * 6
            wsc = 1.0 - 0.18 * abs(yaw) if side != yaw_side(yaw) else 1.0
            ew, eh = eye_w * wsc, eye_h * min(eo, 1.35)
            ey = cy - 6
            # white
            el(d, (sx - ew / 2 - 3.5, ey - eh / 2 - 3.5, sx + ew / 2 + 3.5, ey + eh / 2 + 3.5), OL + (255,))
            el(d, (sx - ew / 2, ey - eh / 2, sx + ew / 2, ey + eh / 2), (255, 255, 255, 255))
            # pupil
            pr = 14.0 * ex["pr"] * (1.0 if eo > 0.3 else 0.5)
            px = sx + (yaw * 9 + look[0] * 9)
            py = ey + look[1] * 10 + 3
            el(d, (px - pr, py - pr * 1.18, px + pr, py + pr * 1.18), (30, 22, 40, 255))
            el(d, (px - pr * 0.42 - 2, py - pr * 0.62, px + pr * 0.1, py - pr * 0.1), (255, 255, 255, 255))
            if eo < 0.5:  # lids drawn as a line
                ln(d, [(sx - ew / 2, ey), (sx + ew / 2, ey)], OL + (255,), 5)
            # eyelashes for the girl
            if s.girl:
                ln(d, [(sx + side * ew * 0.45, ey - eh * 0.35), (sx + side * (ew * 0.45 + 9), ey - eh * 0.5)], OL + (255,), 4)
            # brows
            ang = math.radians(ex["ba"])
            by = ey - eh / 2 - 20 + ex["by"]
            thick = 13 if getattr(s, "old", False) else (7 if s.girl else 9)
            outer = (sx + side * 24, by + math.sin(ang) * 24)
            inner = (sx - side * 24, by - math.sin(ang) * 24)
            ln(d, [outer, inner], hair_col(s) + (255,), thick)
        # nose (tiny) + cheeks
        nx = cx + yaw * 10
        ln(d, [(nx - 4, cy + 28), (nx + 3, cy + 33), (nx + 10, cy + 28)], shade(s.skin, 0.62) + (255,), 4)
        if ex["bl"] > 0.02:
            for side in (-1, 1):
                el(d, (cx + side * 80 - 18 + yaw * 8, cy + 36, cx + side * 80 + 18 + yaw * 8, cy + 56), (255, 120, 120, int(110 * ex["bl"])))
        # mouth
        my = cy + 64
        mw = 30 * ex["mw"]
        mx = cx + yaw * 12
        op = mouth_open
        sm = ex["sm"]
        if op < 0.12:
            pts = []
            for k in range(11):
                u = k / 10.0
                curve = 1 - (2 * u - 1) ** 2
                pts.append((mx + lerp(-mw, mw, u), my + curve * 9 * sm))
            ln(d, pts, OL + (255,), 5)
        else:
            vis = (int(say_seed * 7.0) % 3)
            hh = 8 + 40 * op ** 0.9
            ww = mw * (0.8 + 0.5 * (1 if vis == 0 else 0) - 0.25 * (1 if vis == 2 else 0)) * (1.0 + 0.35 * op)
            box = (mx - ww, my - hh * 0.25, mx + ww, my + hh * 0.85)
            el(d, tuple(b + (-3.5 if i < 2 else 3.5) for i, b in enumerate(box)), OL + (255,))
            el(d, box, (92, 30, 44, 255))
            # tongue
            el(d, (mx - ww * 0.55, my + hh * 0.45, mx + ww * 0.55, my + hh * 0.85), (240, 110, 130, 255))
            # upper teeth
            if hh > 18:
                rr(d, (mx - ww * 0.78, my - hh * 0.22, mx + ww * 0.78, my - hh * 0.22 + 10), 4, (255, 255, 255, 255))
        if getattr(s, "old", False):
            # moustache + beard tuft (drawn over the mouth line)
            ln(d, [(mx - 52, my - 14), (mx - 20, my - 22), (mx, my - 12), (mx + 20, my - 22), (mx + 52, my - 14)], (200, 200, 206, 255), 12)
        return im

    # ---------------------------------------------------------- drawing
    def draw(self, cv, t, x, gy, scale=1.0, facing=1, pose=None, expr_params=None, alpha=1.0, flash_tint=None, say=None, look=(0.0, 0.0)):
        s = self.s
        pose = pose or {}
        env = self.env(t) if self.env else 0.0
        if say is not None:
            env = say
        ex = expr_params or expr_at(self.expr_keys, t)
        yaw = pose.get("ya", 0.0)
        CW_, CH_ = 640, 760
        loc = Image.new("RGBA", (int(CW_ * D), int(CH_ * D)), (0, 0, 0, 0))
        gx, gyy = CW_ / 2, CH_ - 40   # local ground point in the canvas (units)
        bob = pose.get("bob", 0.0) + pose.get("crouch", 0.0)
        ox = gx + pose.get("dx", 0.0)

        def P(px_, py_):  # local units -> canvas pixels
            return ((ox + px_) * D, (gyy + py_ + bob) * D)

        hip = (0.0, -204.0)
        lean = pose.get("lean", 0.0)
        la = math.radians(lean)
        tl = s.torso_h
        sh_c = (hip[0] + math.sin(la) * tl * 0.98, hip[1] - math.cos(la) * tl * 0.98)  # shoulder centre
        # leg poses
        lf = pose.get("leg_f", (4, -2))
        ln_ = pose.get("leg_n", (-4, -2))

        def leg(hx, ang, depth):
            h1, k1 = ang
            thigh_dir = math.radians(h1)
            knee = (hx + math.sin(thigh_dir) * 96, hip[1] + 6 + math.cos(thigh_dir) * 96)
            sh_dir = math.radians(h1 + k1)
            ankle = (knee[0] + math.sin(sh_dir) * 88, knee[1] + math.cos(sh_dir) * 88)
            return knee, ankle, h1, h1 + k1

        legs = []
        for hx, ang in ((-10, ln_), (14, lf)):
            legs.append(leg(hx, ang, 0))
        # arms
        def arm(sx, ang):
            a1, a2 = ang
            sp = (sh_c[0] + sx, sh_c[1] + 12)
            e = (sp[0] + math.sin(math.radians(a1)) * 74, sp[1] + math.cos(math.radians(a1)) * 74)
            wr = (e[0] + math.sin(math.radians(a1 + a2)) * 68, e[1] + math.cos(math.radians(a1 + a2)) * 68)
            return sp, e, wr, a1, a1 + a2

        arm_f = pose.get("arm_f", (-8, 10))     # far arm
        arm_n = pose.get("arm_n", (6, 10))      # near arm
        af = arm(s.sh_x[1], arm_f)
        an = arm(s.sh_x[0], arm_n)

        def put_limb(sprite, jx, jy, ang):
            sp = rot_about_center(sprite, ang)
            ccx, ccy = P(jx, jy)
            # sprite's pivot = sprite centre, drawn hanging down from (R - 6)... so pivot is at its centre; draw directly
            paste_c(loc, sp, ccx, ccy)

        # ---- draw order
        if s.girl:
            hb = self.head_back
        # far arm
        put_limb(self.upper, af[0][0], af[0][1], af[3])
        put_limb(self.fore, af[1][0], af[1][1], af[4])
        # far leg then near leg (far = index 1 -> x=+14)
        for idx in (1, 0):
            knee, ankle, a1, a2 = legs[idx]
            put_limb(self.thigh, (-10, 14)[idx], hip[1] + 6, a1)
            put_limb(self.shin, knee[0], knee[1], a2)
            fa = clamp(-(a2) * 0.55, -35, 35)
            paste_c(loc, rot_about_center(self.foot, fa), *P(ankle[0] + 2, ankle[1] - 6))
        # torso
        tors = rot_about_center(self.torso, -lean)
        paste_c(loc, tors, *P(hip[0], hip[1]))
        # head
        head_c = (sh_c[0] + math.sin(la) * 16 + pose.get("hx", 0.0), sh_c[1] - 98 + pose.get("hy", 0.0))
        say_seed = t * 1.0 + 0.37
        face = self._face(t, yaw, ex, clamp(env * 1.15), say_seed, look)
        hd = self.head_back.copy()
        hd.alpha_composite(face)
        hd.alpha_composite(self.head_front)
        hd = rot_about_center(hd, -pose.get("head", 0.0) - lean * 0.4)
        paste_c(loc, hd, *P(head_c[0], head_c[1]))
        # near arm
        put_limb(self.upper, an[0][0], an[0][1], an[3])
        put_limb(self.fore, an[1][0], an[1][1], an[4])
        self.last = dict(wrist_n=an[2], wrist_f=af[2], head=head_c, hip=hip, ankle_n=legs[0][1], ankle_f=legs[1][1], gx=gx, gy=gyy, bob=bob)
        if flash_tint:
            tint = Image.new("RGBA", loc.size, flash_tint + (0,))
            tint.putalpha(loc.getchannel("A").point(lambda v: int(v * 0.0)))
        if facing < 0:
            loc = loc.transpose(Image.FLIP_LEFT_RIGHT)
        k = scale / D
        sc = loc.resize((max(1, int(loc.width * k)), max(1, int(loc.height * k))), Image.LANCZOS if k < 0.7 else Image.BILINEAR)
        if alpha < 0.999:
            a = sc.getchannel("A").point(lambda v: int(v * alpha))
            sc.putalpha(a)
        # position so local ground point lands on (x, gy)
        px = x - (gx * k * D) if facing > 0 else x - ((CW_ - gx) * k * D)
        py = gy - gyy * k * D
        _safe_paste(cv, sc, int(round(px)), int(round(py)))

    def wrist_pos(self, which, x, gy, scale=1.0, facing=1):
        """screen position of a wrist after the last draw() (for props: flashlight, key)"""
        wx, wy = self.last["wrist_n" if which == "n" else "wrist_f"]
        return x + facing * wx * scale, gy + (wy + self.last["bob"]) * scale

    def head_pos(self, x, gy, scale=1.0, facing=1):
        hx, hy = self.last["head"]
        return x + facing * hx * scale, gy + (hy + self.last["bob"]) * scale


def yaw_side(yaw): return 1 if yaw >= 0 else -1


def hair_col(s): return shade(s.hair, 1.0) if not getattr(s, "old", False) else (170, 170, 178)


# ----------------------------------------------------------------------------- poses
ARMS = {
    # name: (far arm (shoulder, elbow-bend), near arm (shoulder, elbow-bend))
    "down":      ((-4, 12), (4, 12)),
    "relaxed":   ((-8, 14), (6, 18)),
    "light":     ((-6, 12), (58, 34)),       # near arm holds a flashlight horizontally ahead
    "point":     ((-6, 12), (72, 14)),
    "cheeks":    ((98, 72), (110, 62)),      # both hands to the cheeks (scared)
    "up":        ((140, 36), (148, 30)),
    "hips":      ((-28, 80), (-22, 84)),
    "reach":     ((-6, 12), (82, 8)),
    "think":     ((-6, 12), (66, 92)),
    "cross":     ((44, 100), (52, 98)),
    "shock":     ((120, 50), (125, 44)),
    "hold_key":  ((-6, 12), (64, 40)),
    "shush":     ((-6, 12), (92, 96)),
    "pull":      ((54, 10), (62, 8)),
    "wave":      ((-6, 12), (150, 26)),
}


def arms(name, mirror=False):
    f, n = ARMS[name]
    return dict(arm_f=f, arm_n=n)


def walk(ph, amp=1.0, arms_mode="swing"):
    """walk cycle at phase ph (cycles); returns pose dict (legs, arm swing, bob, lean)"""
    s = math.sin(2 * math.pi * ph)
    c = math.cos(2 * math.pi * ph)
    leg_n = (30 * amp * s, -34 * amp * max(0.0, -c) - 4)
    leg_f = (-30 * amp * s, -34 * amp * max(0.0, c) - 4)
    pose = dict(leg_n=leg_n, leg_f=leg_f, bob=-5 * amp * abs(math.sin(2 * math.pi * ph)) * -1 + 0.0, lean=3.0 * amp)
    pose["bob"] = 7 * amp * abs(c) - 3.5 * amp
    if arms_mode == "swing":
        pose["arm_n"] = (-28 * amp * s + 2, 14)
        pose["arm_f"] = (28 * amp * s - 4, 14)
    return pose


def merge(*ps):
    out = {}
    for p in ps:
        out.update(p)
    return out
