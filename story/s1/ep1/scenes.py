"""Sirli Hikoyalar · 1-hikoya "Soat 03:07" · 1-qism v2 (yangi 2D uslub: qalin kontur, to'liq bo'yli personajlar).
Shots: A hook tower | B blackout | C street walk | D stop + look up | E door | F cat + key | G key close-up | H door opens |
       I interior (7 hooks) | J clock hits 03:07 | K key on hook | L silhouette on the stairs | M "BU KIM?" + fade out."""
import math
import os
import sys

_EP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_EP, "..", "..", "kit"))

from art2 import *  # noqa: F401,F403,E402
from toon import Toon, JASUR, MALIKA, arms, walk, merge  # noqa: E402
import nt_char as C  # noqa: E402

WORK = os.path.join(_EP, "work")
EP_TAG = "SOAT 03:07 · 1/4"
SPK_COL = {"hik": (244, 240, 232), "jasur": (255, 164, 92), "malika": (110, 226, 214), "notanish": (255, 214, 120)}
GY = 1250          # horizon / ground line
FY = 1345          # feet of the characters in street shots
CSC = 0.80         # standard character scale
STAND = dict(leg_n=(4, -2), leg_f=(-4, -2))


def seq(t, keys, ease=True):
    """piecewise value over time: keys = [(t, v), ...]"""
    if t <= keys[0][0]:
        return keys[0][1]
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if t < b:
            p = (t - a) / max(1e-6, b - a)
            return lerp(va, vb, ease_in_out(p) if ease else p)
    return keys[-1][1]


def build(tim):
    S_ = lambda n: tim.S("L%02d" % n)
    E_ = lambda n: tim.E("L%02d" % n)
    # ------------------------------------------------------------------ timeline
    tA_stop = E_(1) - 0.30           # hands slam to 03:07
    tB0 = S_(2) - 0.05               # the mahalla goes dark
    tC0 = S_(3) - 0.55               # street, walking
    tD0 = S_(5) - 0.10               # they stop ("Jim!")
    tD2 = S_(5) + 1.55               # look-up insert on the clock (03:06)
    tE0 = S_(6) - 0.85               # at the door
    tF0 = S_(7) - 0.45               # cat leaps down with the key
    tG0 = S_(8) - 0.40               # key close-up
    tH0 = S_(9) - 0.40               # door opens, they go in
    tI0 = S_(10) - 0.60              # interior, the 7 hooks
    tJ0 = S_(11) - 0.45              # clock mechanism, 03:07
    tK0 = S_(12) - 0.35              # key goes on the hook
    tL0 = S_(13) - 0.60              # silhouette on the stairs
    tM0 = S_(14) - 0.40              # "BU KIM?"
    tEnd = tim.total

    envJ = C.speech_env(f"{WORK}/spk_jasur.wav")
    envM = C.speech_env(f"{WORK}/spk_malika.wav")
    jx = [(0.0, "neutral", 0.1), (S_(3) - 0.2, "worried", 0.25), (E_(3) + 0.1, "neutral", 0.3), (S_(4) + 1.2, "worried", 0.3),
          (S_(5) + 0.2, "scared", 0.25), (tE0, "worried", 0.2), (S_(6) - 0.1, "shout", 0.15), (tF0 + 0.5, "scared", 0.12),
          (S_(7) + 1.2, "surprised", 0.25), (tG0 + 0.2, "worried", 0.3), (tH0 + 0.2, "scared", 0.2), (tI0, "worried", 0.3),
          (S_(11) - 0.2, "scared", 0.15), (E_(11), "scared", 0.2), (tK0 + 0.6, "scared", 0.2), (tL0 + 0.2, "scared", 0.2)]
    mx = [(0.0, "determined", 0.1), (S_(4) - 0.1, "sly", 0.2), (E_(4) + 0.1, "determined", 0.25), (S_(5) - 0.1, "determined", 0.15),
          (tE0 + 0.6, "worried", 0.25), (S_(7) + 0.9, "surprised", 0.2), (tG0, "determined", 0.2), (S_(8) + 0.2, "surprised", 0.25),
          (tH0, "determined", 0.15), (tI0 + 0.2, "worried", 0.3), (S_(11), "scared", 0.2), (tK0, "determined", 0.15), (tK0 + 0.9, "scared", 0.2),
          (tL0 + 0.1, "scared", 0.2)]
    J = Toon(JASUR, env=envJ, blinks=(1.3, 3.9, 6.2, 8.0, 9.5, 11.4, 14.1, 16.8, 19.0, 21.5, 24.3, 27.1, 29.5, 31.9, 34.2, 37.0, 39.4, 41.8), expr_keys=jx)
    M = Toon(MALIKA, env=envM, blinks=(0.9, 3.2, 5.8, 7.6, 10.4, 12.8, 15.6, 18.4, 21.0, 23.5, 26.0, 28.7, 31.0, 33.6, 36.1, 38.5, 41.2), expr_keys=mx)

    def ph(t, off=0.0, rate=1.12): return (t * rate + off) % 1.0

    # ================================================================== A / B  tower hook + blackout
    def lit_dark(cv, seed, w, h, col, lit_p, ybase, x, r, hmin=120, hmax=330):
        dark = town(seed, w, h, col, 0.0, hmin=hmin, hmax=hmax)
        lit = town(seed, w, h, col, lit_p, hmin=hmin, hmax=hmax)
        put(cv, dark, x, ybase - h / 2)
        if r <= 0.5:
            put(cv, lit, x, ybase - h / 2)
            return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        put(lay, lit, x, ybase - h / 2)
        m = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(m)
        if 540 - r > 0:
            md.rectangle([0, 0, 540 - r, H], fill=255)
        if 540 + r < W:
            md.rectangle([540 + r, 0, W, H], fill=255)
        lay.putalpha(Image.fromarray((np.array(lay.getchannel("A"), np.float32) * np.array(m, np.float32) / 255).astype(np.uint8)))
        cv.alpha_composite(lay)

    def bats(cv, t, t0):
        d = ImageDraw.Draw(cv, "RGBA")
        for i in range(6):
            p = (t - t0 - i * 0.22)
            if p < 0:
                continue
            x = lerp(-80, 1180, clamp(p / 3.0)) if i % 2 == 0 else lerp(1180, -80, clamp(p / 3.0))
            y = 520 + i * 70 + 40 * math.sin(p * 3 + i)
            fl = math.sin(p * 18 + i) * 0.7
            s = 26 + (i % 3) * 8
            d.polygon([(x, y), (x - s * 1.8, y - s * (0.7 + fl)), (x - s * 0.8, y + s * 0.1)], fill=OLC + (255,))
            d.polygon([(x, y), (x + s * 1.8, y - s * (0.7 + fl)), (x + s * 0.8, y + s * 0.1)], fill=OLC + (255,))
            d.ellipse([x - s * 0.34, y - s * 0.4, x + s * 0.34, y + s * 0.5], fill=OLC + (255,))

    def shot_tower(cv, t):
        cv.alpha_composite(sky_base())
        stars(cv, t, 1000)
        k = clamp(t / max(1.0, tC0))
        sc = lerp(0.80, 0.98, ease_in_out(k))
        base_y = 1580
        fx, fy = 540, base_y - 1010 * sc
        r = clamp((t - tB0) / 1.0) * 760 if t >= tB0 else 0.0
        lit_dark(cv, 11, 2200, 420, (30, 24, 70), 0.34, base_y - 150, 540 - 30 * k, r)
        lit_dark(cv, 12, 2200, 360, (18, 15, 46), 0.30, base_y - 20, 540 + 40 * k, r, hmin=140, hmax=320)
        if t < tA_stop:
            m = lerp(30.0, 187.0, ease_out_cubic(t / tA_stop))
        else:
            m = 187.0
        draw_tower(cv, fx, fy, sc, m % 60, m // 60 + (m % 60) / 60.0, win_light=0.0, glow_face=0.7 if t >= tA_stop else 0.45)
        fog = vgrad(W, 500, (60, 44, 110), (60, 44, 110), 1.0)
        fog.putalpha(Image.fromarray((np.linspace(0, 120, 500)[:, None] * np.ones((1, W))).astype(np.uint8), "L"))
        cv.alpha_composite(fog, (0, H - 500))
        if t >= tB0:
            bats(cv, t, tB0 + 0.4)
        if t >= tA_stop:
            p = ease_out_back((t - tA_stop) / 0.45, 2.0)
            big = glow(stext("03:07", 230, (255, 238, 170), (22, 14, 40), 12), (255, 170, 60), 34, 1.3)
            shk = 12 * math.sin((t - tA_stop) * 60) * max(0, 1 - (t - tA_stop) / 0.4)
            fo = 1.0 - clamp((t - (tB0 + 1.0)) / 0.5)
            put(cv, big, 540 + shk, 1085, clamp((t - tA_stop) / 0.15) * fo, 0.5 + 0.5 * p)

    # ================================================================== street
    def street(cv, t, scroll, tw_sc, lamp_on=1.0, tower_x=820):
        cv.alpha_composite(sky_base())
        stars(cv, t, 900)
        fy_t = GY - 1010 * tw_sc
        put(cv, town(11, 2200, 400, (30, 24, 70), 0.16, hmin=120, hmax=300), 540 - scroll * 0.05, GY - 200 + 14)
        draw_tower(cv, tower_x, fy_t, tw_sc, 5.0, 3.0 + 5 / 60.0, win_light=0.0, glow_face=0.5)
        put(cv, town(12, 2200, 330, (18, 15, 46), 0.12, hmin=130, hmax=280), 540 - scroll * 0.14, GY - 165 + 22)
        ground(cv, GY)
        bushes(cv, scroll, 0.55, GY + 18, 3, (14, 18, 42))
        path_marks(cv, scroll, GY)
        for k in range(-1, 4):
            lx = 300 + 800 * k - scroll
            if -150 < lx < W + 150:
                lamp(cv, lx, GY + 70, lamp_on, t, 0.95)

    def beam(cv, who, x, y, sc, facing, t, ang=10.0, a=120):
        wx, wy = who.wrist_pos("n", x, y, sc, facing)
        d = ImageDraw.Draw(cv, "RGBA")
        d.rounded_rectangle([wx - 6, wy - 12, wx + 40, wy + 12], radius=8, fill=(40, 46, 70, 255))
        hx = wx + 42
        d.rounded_rectangle([hx - 5, wy - 16, hx + 12, wy + 16], radius=6, fill=(250, 230, 150, 255))
        flash_cone(cv, hx, wy, ang, 950, 17, a)
        put(cv, radial(200, (255, 240, 190), 150, 2.0), hx + 12, wy, 1.0, 1.0)

    def shot_walk(cv, t):
        scroll = (t - tC0) * 330.0
        sc_t = seq(t, [(tC0, 0.50), (tD0, 0.60)])
        street(cv, t, scroll, sc_t)
        mx_ = seq(t, [(tC0, 560), (S_(4), 690)])
        jx_ = seq(t, [(tC0, 250), (S_(4), 330)])
        wm = walk(ph(t, 0.0), 1.0)
        wj = walk(ph(t, 0.45), 0.9)
        pm = merge(wm, dict(ya=0.25 if t < S_(4) else -0.5 * clamp((t - S_(4)) / 0.3)))
        pj = merge(wj, arms("light"), dict(lean=2.0, ya=0.5))
        pj["arm_n"] = (58 + 6 * math.sin(t * 5), 34)
        J.draw(cv, t, jx_, FY, CSC, 1, pj)
        beam(cv, J, jx_, FY, CSC, 1, t, 12)
        M.draw(cv, t, mx_, FY - 4, CSC, 1, pm)

    def shot_stop(cv, t):
        trun = E_(5) - 0.55
        run = t > trun
        scroll = (tD0 - tC0) * 330.0 + seq(t, [(tD0, 0.0), (tD0 + 0.45, 90.0)]) + (max(0.0, t - trun) ** 2) * 600
        street(cv, t, scroll, seq(t, [(tD0, 0.60), (tD2, 0.86)]))
        k = clamp((t - tD0) / 0.35)
        mx_, jx_ = 690, 330
        if not run:
            pm = merge(STAND, arms("shush"), dict(ya=0.4, head=-6 * k, lean=-3 * k))
            pj = merge(STAND, arms("cheeks"), dict(ya=0.3, head=-8 * k, lean=-4 * k))
        else:
            pm = merge(walk(ph(t, 0.0, 2.0), 1.6), dict(lean=10))
            pj = merge(walk(ph(t, 0.4, 2.0), 1.6), dict(lean=10), arms("pull"))
            dxr = (t - trun) ** 2 * 900
            mx_ += dxr
            jx_ += dxr
        lk = (0.4, -1.0) if not run else (0, 0)
        J.draw(cv, t, jx_, FY, CSC, 1, pj, look=lk)
        M.draw(cv, t, mx_, FY - 4, CSC, 1, pm, look=lk)

    def shot_clock_up(cv, t):
        """low-angle insert: the clock reads 03:06 and ticks"""
        cv.alpha_composite(sky_base())
        stars(cv, t, 1000)
        p = clamp((t - tD2) / max(0.1, (tE0 - tD2)))
        sc = lerp(1.10, 1.28, ease_in_out(p))
        fy = lerp(640, 760, ease_in_out(p))
        put(cv, town(11, 2200, 400, (30, 24, 70), 0.0), 540, 1700)
        m = 6.0 if t > tD2 + 0.55 else 5.0
        kick = max(0.0, 1 - (t - (tD2 + 0.55)) / 0.2) * 0.4 if t > tD2 + 0.55 else 0.0
        draw_tower(cv, 540, fy, sc, m + kick, 3.0 + m / 60.0, win_light=0.0, glow_face=0.8)
        fogd = vgrad(W, 360, (8, 7, 26), (8, 7, 26), 1.0)
        fogd.putalpha(Image.fromarray((np.linspace(0, 200, 360)[:, None] * np.ones((1, W))).astype(np.uint8), "L"))
        cv.alpha_composite(fogd, (0, H - 360))

    # ================================================================== door shots
    def door_bg(cv, t, open_k=0.0, glow_k=0.0):
        cv.alpha_composite(vgrad(W, H, (34, 30, 60), (14, 12, 34), 1.0))
        wall = brick_src(1080, 1350, (52, 46, 84), 2)
        shade_ = vgrad(1080, 1350, (0, 0, 0), (0, 0, 0), 1.0)
        shade_.putalpha(Image.fromarray((np.linspace(185, 20, 1350)[:, None] * np.ones((1, 1080))).astype(np.uint8), "L"))
        cv.alpha_composite(wall, (0, 0))
        cv.alpha_composite(shade_, (0, 0))
        g = vgrad(W, H - 1300, (46, 42, 78), (14, 12, 34), 0.9)
        cv.alpha_composite(g, (0, 1300))
        d = ImageDraw.Draw(cv, "RGBA")
        d.rectangle([0, 1296, W, 1312], fill=(120, 110, 160, 255))
        d.rectangle([0, 1312, W, 1322], fill=OLC + (255,))
        fl = 0.8 + 0.2 * math.sin(t * 11) * math.sin(t * 3.1)
        put(cv, radial(620, (255, 190, 96), int(110 * fl), 2.0), 160, 780, 1.0)
        d.rounded_rectangle([146, 735, 174, 790], radius=8, fill=OLC + (255,))
        d.rounded_rectangle([150, 742, 170, 784], radius=6, fill=(255, 214, 120, int(255 * fl)))
        d.line([(160, 700), (160, 735)], fill=OLC + (255,), width=5)
        tower_door(cv, 540, 1300, 400, 660, open_k, glow_k, t=t)
        if glow_k > 0.05:
            put(cv, radial(900, (255, 196, 110), int(150 * glow_k), 1.8), 540, 1050, 1.0, 1.3)

    def shot_door(cv, t):
        door_bg(cv, t)
        ta = tE0 + 0.9
        jx_ = seq(t, [(tE0, -260), (ta, 330)])
        mx_ = seq(t, [(tE0, -520), (ta + 0.2, 740)])
        runJ = t < ta
        runM = t < ta + 0.2
        pj = merge(walk(ph(t, 0.4, 2.0), 1.5), dict(lean=9)) if runJ else merge(STAND, arms("pull"), dict(ya=0.3))
        pm = merge(walk(ph(t, 0.0, 2.0), 1.5), dict(lean=9)) if runM else merge(STAND, arms("think"), dict(ya=0.3))
        if not runJ and t > S_(6) - 0.15:
            pj = merge(dict(leg_n=(10, -2), leg_f=(-8, -2)), arms("pull"), dict(lean=-8 + 6 * math.sin(t * 22), ya=0.3))
        J.draw(cv, t, jx_, 1405, 0.84, 1, pj)
        M.draw(cv, t, mx_, 1405, 0.84, 1 if runM else -1, pm)

    def shot_cat(cv, t):
        door_bg(cv, t)
        p = clamp((t - tF0) / 0.85)
        land = tF0 + 0.85
        if t < land:
            cx_ = lerp(-120, 620, p)
            cy_ = lerp(-80, 1240, p * p)
            ang = lerp(-35, 8, p)
            put(cv, cat_src("leap"), cx_, cy_, 1.0, 0.95, ang)
            put(cv, small_key("VII"), cx_ + 128, cy_ + 22, 1.0, 0.5, -80)
        else:
            q = t - land
            squash = 1.0 + 0.12 * max(0, 1 - q / 0.25) * math.sin(q * 30)
            put(cv, cat_src("land" if q < 0.35 else "sit"), 620, 1225, 1.0, 0.95 * squash)
            put(cv, small_key("VII"), 620 + 108, 1225 - 30 + (0 if q < 0.35 else 18), 1.0, 0.46, -80 if q < 0.35 else -95)
            if q < 0.35:
                d = ImageDraw.Draw(cv, "RGBA")
                for i in range(7):
                    a = math.radians(200 + i * 22)
                    r0 = 40 + q * 380
                    d.ellipse([620 + math.cos(a) * r0 - 8, 1300 + math.sin(a) * r0 * 0.25 - 8, 620 + math.cos(a) * r0 + 8, 1300 + math.sin(a) * r0 * 0.25 + 8],
                              fill=(200, 200, 230, int(160 * (1 - q / 0.35))))
        jy = -60 * math.sin(math.pi * clamp((t - (land - 0.05)) / 0.5)) if t >= land - 0.05 else 0.0
        jxx = 330 - 90 * clamp((t - (land - 0.05)) / 0.25) + (30 * clamp((t - land - 0.8) / 0.6))
        pj = merge(dict(leg_n=(-18, -10), leg_f=(10, -4)), arms("up"), dict(lean=-12, ya=0.6))
        if t >= land + 0.9:
            pj = merge(STAND, arms("shock"), dict(lean=-4, ya=0.5))
        pm = merge(STAND, arms("think"), dict(ya=0.3))
        J.draw(cv, t, jxx, 1405 + jy, 0.84, 1, pj, look=(0.8, 0.2))
        M.draw(cv, t, 760, 1405, 0.84, -1, pm, look=(-0.6, 0.3))

    def shot_key(cv, t):
        cv.alpha_composite(vgrad(W, H, (16, 14, 40), (6, 5, 20), 1.0))
        p = clamp((t - tG0) / 0.5)
        put(cv, radial(1100, (255, 200, 100), int(120 * p), 2.0), 540, 760, 1.0)
        rot = 10 + 7 * math.sin(t * 2.4)
        kk = glow(key_src("VII"), (255, 200, 90), 34, 1.2)
        put(cv, kk, 540, 740, clamp(p * 2), 1.5 * (0.6 + 0.4 * ease_out_back(p, 1.8)), rot)
        sparks(cv, t, tG0 + 0.1, 540, 740, n=16, col=(255, 226, 140), seed=6, life=0.9, speed=380, size=5, grav=100)
        M.draw(cv, t, 540, 2330, 1.55, 1, merge(STAND, arms("down"), dict(ya=0.0, head=-3)), look=(0, -0.6))

    def shot_open(cv, t):
        p = clamp((t - (tH0 + 0.55)) / 1.5)
        open_k = ease_in_out(p)
        door_bg(cv, t, open_k, open_k)
        wk = clamp((t - (tH0 + 1.6)) / 1.2)
        jx_ = lerp(330, 470, wk)
        mx_ = lerp(740, 610, wk)
        sc = lerp(0.84, 0.56, ease_in_out(wk))
        fy = lerp(1405, 1330, ease_in_out(wk))
        al = 1.0 - clamp((wk - 0.7) / 0.3)
        wlk = wk > 0.01
        pj = merge(walk(ph(t, 0.4, 1.4), 1.0), dict(lean=6)) if wlk else merge(STAND, arms("think"), dict(ya=0.3))
        pm = merge(walk(ph(t, 0.0, 1.4), 1.0), dict(lean=6)) if wlk else merge(STAND, arms("reach"), dict(ya=-0.4))
        J.draw(cv, t, jx_, fy, sc, 1, pj, alpha=al)
        M.draw(cv, t, mx_, fy - 2, sc, 1 if wlk else -1, pm, alpha=al)
        put(cv, cat_src("sit"), 930, 1285, al, 0.72)

    # ================================================================== interior
    def interior_bg(cv, t, speed=1.0):
        cv.alpha_composite(vgrad(W, H, (30, 24, 56), (10, 8, 26), 1.0))
        tex = brick_src(1080, 1920, (42, 36, 68), 5).copy()
        tex.putalpha(60)
        cv.alpha_composite(tex)
        tt = t * speed
        draw_gear(cv, 540, 560, 330, 26, tt * 9, (120, 82, 54), 0.55)
        draw_gear(cv, 150, 250, 150, 14, -tt * 9 * 330 / 150 * 0.8, (136, 96, 60), 0.6)
        draw_gear(cv, 930, 940, 200, 16, -tt * 9 * 330 / 200 * 0.8, (110, 76, 50), 0.6)
        draw_gear(cv, 880, 230, 110, 12, tt * 22, (150, 108, 62), 0.6)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        for sx in (-120, 40, 200):
            ld.polygon([(120 + sx, 0), (230 + sx, 0), (760 + sx, 1400), (420 + sx, 1400)], fill=(150, 190, 255, 22))
        cv.alpha_composite(lay)
        g = vgrad(W, H - 1330, (52, 40, 62), (14, 11, 28), 0.9)
        cv.alpha_composite(g, (0, 1330))
        d = ImageDraw.Draw(cv, "RGBA")
        d.rectangle([0, 1326, W, 1338], fill=OLC + (255,))
        for x in range(0, W, 140):
            d.line([(x + 70 * ((x // 140) % 2), 1338), (x - 60 + 70 * ((x // 140) % 2), H)], fill=(10, 8, 22, 120), width=4)
        ang = math.radians(15 * math.sin(t * math.pi))
        px, py = 1000, -30
        L = 1180
        bx, by = px + math.sin(ang) * L, py + math.cos(ang) * L
        d.line([(px, py), (bx, by)], fill=OLC + (255,), width=16)
        d.line([(px, py), (bx, by)], fill=(176, 136, 70, 255), width=9)
        d.ellipse([bx - 72, by - 72, bx + 72, by + 72], fill=OLC + (255,))
        d.ellipse([bx - 64, by - 64, bx + 64, by + 64], fill=(206, 160, 76, 255))
        d.ellipse([bx - 40, by - 44, bx + 18, by + 2], fill=(238, 204, 120, 255))
        rng = np.random.default_rng(11)
        for i in range(30):
            x = (rng.uniform(0, W) + 16 * math.sin(t * 0.6 + i)) % W
            y = (rng.uniform(0, H) - t * (12 + i % 7 * 3)) % H
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(230, 220, 255, 70))

    def key_board(cv, t, cy=560, hook7=0.0, filled=0.0, sparkle_t=None, scale=1.0, shake=0.0):
        put(cv, board_src(), 540, cy, 1.0, scale)
        d = ImageDraw.Draw(cv, "RGBA")
        labels = ["I", "II", "III", "IV", "V", "VI", "VII"]
        pos = key_hook_positions(540, cy - 30, 860, 7)
        fnt = F("xb", int(30 * scale))
        out = []
        for i, (hx, hy) in enumerate(pos):
            hx = 540 + (hx - 540) * scale
            hy = cy + (hy - cy) * scale
            out.append((hx, hy))
            d.ellipse([hx - 11, hy - 11, hx + 11, hy + 11], fill=OLC + (255,))
            d.ellipse([hx - 7, hy - 7, hx + 7, hy + 7], fill=(210, 170, 80, 255))
            d.text((hx, cy + 66 * scale), labels[i], font=fnt, fill=(60, 34, 24, 255), anchor="mm")
            if i < 6 or filled > 0.5:
                sw = 4 * math.sin(t * 2.3 + i) + shake * math.sin(t * 40 + i * 2) * 6
                put(cv, small_key(labels[i]), hx, hy + 92 * scale, 1.0, scale, sw)
        hx, hy = out[6]
        if filled < 0.5:
            pulse = 0.6 + 0.4 * math.sin(t * 5.0)
            put(cv, radial(260, (110, 226, 255), int(170 * pulse * hook7), 1.8), hx, hy + 30, 1.0, scale)
            d.ellipse([hx - 16, hy - 16, hx + 16, hy + 16], outline=(110, 226, 255, int(255 * hook7 * pulse)), width=4)
        if sparkle_t is not None:
            for i in range(6):
                q = (t - (sparkle_t + i * 0.28))
                if 0 <= q < 0.4:
                    put(cv, radial(220, (255, 240, 180), int(210 * math.sin(math.pi * q / 0.4)), 2.0), out[i][0], cy + 80 * scale, 1.0, scale)
        return out

    def shot_interior(cv, t):
        interior_bg(cv, t)
        key_board(cv, t, 600, hook7=clamp((t - (S_(10) + 1.6)) / 0.6), sparkle_t=S_(10) + 0.2)
        pj = merge(STAND, arms("down"), dict(ya=0.35, head=-12, lean=-2))
        pm = merge(STAND, arms("point"), dict(ya=0.3, head=-12, lean=-2))
        J.draw(cv, t, 330, 1450, 0.82, 1, pj, look=(0.3, -1.0))
        M.draw(cv, t, 760, 1450, 0.82, -1, pm, look=(-0.3, -1.0))

    def shot_mech(cv, t):
        """the clock from inside: the minute hand ticks 03:06 -> 03:07"""
        interior_bg(cv, t, speed=1.0)
        tk = S_(11) + 1.15
        cx_, cy_, R_ = 540, 700, 400
        put(cv, radial(1300, (110, 226, 255), 80, 2.0), cx_, cy_, 1.0)
        d = ImageDraw.Draw(cv, "RGBA")
        d.ellipse([cx_ - R_ - 14, cy_ - R_ - 14, cx_ + R_ + 14, cy_ + R_ + 14], fill=OLC + (255,))
        d.ellipse([cx_ - R_, cy_ - R_, cx_ + R_, cy_ + R_], fill=(34, 66, 90, 255))
        d.ellipse([cx_ - R_ + 24, cy_ - R_ + 24, cx_ + R_ - 24, cy_ + R_ - 24], fill=(60, 116, 140, 255))
        for i in range(60):
            a = math.radians(i * 6 - 90)
            r0 = R_ - (70 if i % 5 == 0 else 46)
            d.line([(cx_ + math.cos(a) * r0, cy_ + math.sin(a) * r0), (cx_ + math.cos(a) * (R_ - 30), cy_ + math.sin(a) * (R_ - 30))],
                   fill=(220, 240, 250, 255 if i % 5 == 0 else 150), width=8 if i % 5 == 0 else 3)
        m = 6.0 + clamp((t - tk) / 0.12)
        if t > tk:
            m += 0.25 * max(0.0, 1 - (t - tk) / 0.2)
        ma = math.radians(m * 6 - 90)
        ha = math.radians(3 * 30 + m * 0.5 - 90)
        for ang, L, wd in ((ha, 210, 26), (ma, 330, 18)):
            x1, y1 = cx_ + math.cos(ang) * L, cy_ + math.sin(ang) * L
            d.line([(cx_, cy_), (x1, y1)], fill=OLC + (255,), width=wd + 10)
            d.line([(cx_, cy_), (x1, y1)], fill=(236, 190, 90, 255), width=wd)
        d.ellipse([cx_ - 30, cy_ - 30, cx_ + 30, cy_ + 30], fill=OLC + (255,))
        d.ellipse([cx_ - 22, cy_ - 22, cx_ + 22, cy_ + 22], fill=(236, 190, 90, 255))
        if t > tk:
            p = ease_out_back((t - tk) / 0.4, 2.0)
            put(cv, glow(stext("03:07", 170, (255, 238, 170), (22, 14, 40), 10), (255, 170, 60), 30, 1.3), 720, 1215, clamp((t - tk) / 0.12), 0.5 + 0.5 * p)
        pj = merge(STAND, arms("cheeks"), dict(ya=0.2, head=-8, lean=-4))
        J.draw(cv, t, 300, 1460, 0.80, 1, pj, look=(0.2, -1.0))
        if t > tk:
            q = (t - tk)
            fl = 1.0 if (int(q * 18) % 3 == 0 and q < 1.1) else 0.0
            cv.alpha_composite(Image.new("RGBA", (W, H), (4, 3, 14, int(150 * fl))))

    def shot_hang(cv, t):
        interior_bg(cv, t, speed=1.0 + 3.0 * clamp((t - (tK0 + 1.3)) / 0.5))
        p = clamp((t - tK0 - 0.35) / 0.9)
        cy_ = 700
        filled = 1.0 if p >= 1.0 else 0.0
        pos = key_board(cv, t, cy_, hook7=1.0, filled=filled, shake=clamp(1 - (t - (tK0 + 1.3)) / 1.5) if t > tK0 + 1.3 else 0.0)
        hx, hy = pos[6]
        if p < 1.0:
            e = ease_in_out(p)
            kx = lerp(980, hx, e)
            ky = lerp(1150, hy + 92, e) - 140 * math.sin(math.pi * e)
            put(cv, glow(small_key("VII"), (255, 220, 120), 26, 1.0), kx, ky, 1.0, 1.0, lerp(-50, 0, e))
        else:
            q = t - (tK0 + 0.35 + 0.9)
            put(cv, small_key("VII"), hx, hy + 92, 1.0, 1.0, 2 * math.sin(q * 9) * max(0, 1 - q / 1.0))
            ring = clamp(q / 0.7)
            d = ImageDraw.Draw(cv, "RGBA")
            for k in range(3):
                rr_ = 40 + ring * (520 + k * 140)
                d.ellipse([hx - rr_, hy + 92 - rr_, hx + rr_, hy + 92 + rr_], outline=(255, 226, 150, int(230 * (1 - ring) ** 1.3)), width=10 - k * 3)
            sparks(cv, t, tK0 + 0.35 + 0.9, hx, hy + 92, n=34, col=(255, 226, 140), seed=8, life=1.0, speed=620, size=7, grav=300)
        pm = merge(STAND, arms("reach"), dict(ya=0.3, head=-10))
        M.draw(cv, t, 760, 1520, 0.9, -1, pm, look=(0, -1.0))

    # ================================================================== the staircase and the figure
    def stairs(cv, t):
        cv.alpha_composite(vgrad(W, H, (20, 16, 40), (7, 6, 20), 1.0))
        tex = brick_src(1080, 1920, (36, 30, 58), 9).copy()
        tex.putalpha(70)
        cv.alpha_composite(tex)
        draw_gear(cv, 150, 330, 190, 16, t * 8, (110, 76, 50), 0.35)
        draw_gear(cv, 930, 1100, 230, 18, -t * 7, (110, 76, 50), 0.35)
        d = ImageDraw.Draw(cv, "RGBA")
        dx_, dy_ = 650, 760
        put(cv, radial(1500, (255, 176, 84), 150, 1.8), dx_, dy_ + 100, 1.0)
        d.rounded_rectangle([dx_ - 270, dy_ - 420, dx_ + 270, dy_ + 700], radius=270, fill=OLC + (255,))
        lg = vgrad(520, 1100, (255, 230, 150), (255, 140, 56), 1.0)
        m = Image.new("L", (520, 1100), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, 520, 1400], radius=260, fill=255)
        lg.putalpha(m)
        cv.alpha_composite(lg, (dx_ - 260, dy_ - 410))
        # landing + steps (drawn BEFORE the figure so he stands on the top step)
        top_y = 1160
        d.rectangle([dx_ - 330, top_y, W, top_y + 60], fill=(40, 32, 70, 255))
        d.line([(dx_ - 330, top_y), (W, top_y)], fill=(255, 190, 110, 90), width=5)
        for i in range(5):
            y0 = top_y + 60 + i * 70
            x0 = dx_ - 330 - (i + 1) * 70
            d.polygon([(x0, y0), (W, y0), (W, y0 + 70), (x0, y0 + 70)], fill=(30 - i * 2, 24 - i * 2, 54 - i * 3, 255))
            d.line([(x0, y0), (W, y0)], fill=(255, 190, 110, 70 - i * 8), width=4)
        d.rectangle([0, 1560, W, H], fill=(8, 6, 22, 255))
        sil = silhouette_src()
        sc = 0.95
        sway = 3 * math.sin(t * 1.6)
        put(cv, sil, dx_ + sway, top_y - sil.height * sc / 2 + 4, 1.0, sc)
        # the lantern in the raised hand
        hx, hy = dx_ + 131 * sc / 0.95 + sway, top_y - sil.height * sc / 2 + 4 - 57
        la = math.radians(14 * math.sin(t * 2.6))
        lxx, lyy = hx + math.sin(la) * 46, hy + 70
        d.line([(hx, hy + 6), (lxx, lyy - 10)], fill=OLC + (255,), width=5)
        put(cv, radial(560, (255, 210, 110), 190, 1.6), lxx, lyy + 20, 1.0)
        d.rounded_rectangle([lxx - 26, lyy - 8, lxx + 26, lyy + 56], radius=10, fill=OLC + (255,))
        d.rounded_rectangle([lxx - 19, lyy - 1, lxx + 19, lyy + 49], radius=8, fill=(255, 226, 140, 255))

    def shot_stairs(cv, t):
        stairs(cv, t)
        sh_ = 6.0 * math.sin(t * 50) * clamp(1 - (t - tL0) / 0.6)
        pj = merge(STAND, arms("cheeks"), dict(ya=0.5, head=-8, lean=-6, dx=sh_))
        pm = merge(STAND, arms("shock"), dict(ya=0.5, head=-8, lean=-6, dx=sh_))
        J.draw(cv, t, 190, 1590, 0.74, 1, pj, look=(0.8, -1.0))
        M.draw(cv, t, 410, 1590, 0.74, 1, pm, look=(0.8, -1.0))

    # ================================================================== dispatcher
    def scene(cv, t):
        if t < tC0:
            shot_tower(cv, t)
        elif t < tD0:
            shot_walk(cv, t)
        elif t < tD2:
            shot_stop(cv, t)
        elif t < tE0:
            shot_clock_up(cv, t)
        elif t < tF0:
            shot_door(cv, t)
        elif t < tG0:
            shot_cat(cv, t)
        elif t < tH0:
            shot_key(cv, t)
        elif t < tI0:
            shot_open(cv, t)
        elif t < tJ0:
            shot_interior(cv, t)
        elif t < tK0:
            shot_mech(cv, t)
        elif t < tL0:
            shot_hang(cv, t)
        else:
            shot_stairs(cv, t)

    def finale(cv, t):
        """BU KIM? text + fade to black (no end card)"""
        if t >= tM0:
            k = ease_out_back((t - tM0) / 0.5, 1.8)
            put(cv, glow(stext("BU KIM?", 168, (255, 214, 120), (6, 4, 22), 10), (255, 170, 60), 30, 1.3), 540, 470, clamp((t - tM0) / 0.2), 0.5 + 0.5 * k)
        fo = clamp((t - (tEnd - 0.8)) / 0.7)
        if fo > 0:
            cv.alpha_composite(Image.new("RGBA", (W, H), (4, 3, 14, int(255 * fo))))

    def top_caps(cv, t):
        col = SPK_COL["hik"]
        for L in tim.segs:
            if L["s2"] - 0.05 <= t <= L["e2"] + 0.35:
                col = SPK_COL.get(L["spk"], col)
        captions(cv, tim, t, y=1392, size=70, maxw=940, n=3, col=(244, 240, 232), hi=col)
        if t < tM0 - 0.2:
            brand_chip(cv, t, EP_TAG, 0.85)

    # ================================================================== camera + FX
    cam = Cam(1.02)
    cam.key(0.0, 1.0).key(tA_stop, 1.10).key(tC0 - 0.01, 1.14)
    cam.key(tC0, 1.04).key(tD0 - 0.01, 1.08).key(tD0, 1.12).key(tD2 - 0.01, 1.16)
    cam.key(tD2, 1.0).key(tE0 - 0.01, 1.08).key(tE0, 1.0).key(tF0 - 0.01, 1.03)
    cam.key(tF0, 1.0).key(tG0 - 0.01, 1.04).key(tG0, 1.0).key(tH0 - 0.01, 1.1).key(tH0, 1.0).key(tI0 - 0.01, 1.22)
    cam.key(tI0, 1.0).key(tJ0 - 0.01, 1.1).key(tJ0, 1.0).key(tK0 - 0.01, 1.08).key(tK0, 1.04).key(tL0 - 0.01, 1.14)
    cam.key(tL0, 1.0).key(tM0 - 0.01, 1.14, -40, 70).key(tM0, 1.2, -60, 110).key(tEnd, 1.34, -90, 170)
    cam.punch(tA_stop, 0.06, 0.4).shake(tA_stop, 16, 0.55)
    cam.shake(tD2 + 0.55, 8, 0.4)
    cam.punch(S_(6), 0.02, 0.2).shake(S_(6) + 0.2, 8, 0.25)
    cam.punch(tF0 + 0.85, 0.03, 0.3).shake(tF0 + 0.85, 10, 0.3)
    cam.shake(tH0 + 0.55, 6, 1.4)
    cam.shake(S_(11) + 1.15, 12, 0.5).punch(S_(11) + 1.15, 0.05, 0.4)
    cam.punch(tK0 + 1.25, 0.06, 0.45).shake(tK0 + 1.25, 14, 0.9)
    cam.shake(tL0 + 0.2, 6, 0.8).punch(tM0, 0.05, 0.5).shake(tM0, 12, 0.6)
    whips = [(tC0, 0.26, 120, 0), (tD0, 0.2, 80, 0), (tD2, 0.22, 100, 90), (tE0, 0.26, 130, 0), (tF0, 0.18, 90, 90), (tG0, 0.22, 100, 0),
             (tH0, 0.22, 100, 0), (tI0, 0.28, 130, 90), (tJ0, 0.2, 90, 0), (tK0, 0.2, 90, 0), (tL0, 0.3, 120, 90)]
    flashes = [(tA_stop, 0.2), (S_(11) + 1.15, 0.16), (tK0 + 1.25, 0.28), (tM0, 0.16)]
    chroma = [(tA_stop, 6, 0.4), (S_(11) + 1.15, 7, 0.35), (tK0 + 1.25, 8, 0.45)]
    reel = StoryReel(tim, [scene, finale], cam=cam, vignette=0.5, grain=0.14, bloom=0.16, whips=whips, flashes=flashes, chroma_at=chroma,
                     top=[top_caps], end_fn=None)
    return reel


def sfx(tim):
    S_ = lambda n: tim.S("L%02d" % n)
    E_ = lambda n: tim.E("L%02d" % n)
    tA_stop = E_(1) - 0.30
    tB0 = S_(2) - 0.05
    tC0 = S_(3) - 0.55
    tD0 = S_(5) - 0.10
    tD2 = S_(5) + 1.55
    tE0 = S_(6) - 0.85
    tF0 = S_(7) - 0.45
    tG0 = S_(8) - 0.40
    tH0 = S_(9) - 0.40
    tI0 = S_(10) - 0.60
    tK0 = S_(12) - 0.35
    tL0 = S_(13) - 0.60
    tM0 = S_(14) - 0.40
    ev = []
    ev.append((max(0.0, tA_stop - 3.0), "riser:3.0", 0.6))
    t = 0.5
    while t < tA_stop - 0.2:
        ev.append((t, "tick", 0.35))
        t += 0.22
    ev += [(tA_stop, "impact", 1.0), (tA_stop + 0.02, "whoosh_dn", 0.5)]
    for i in range(6):
        ev.append((tB0 + 0.12 + i * 0.14, "thump", 0.5))
    ev.append((tB0, "whoosh_dn", 0.6))
    ev.append((tC0 - 0.1, "whoosh", 0.5))
    t = tC0 + 0.3
    while t < tD0:
        ev.append((t, "thump", 0.16))
        t += 0.45
    ev += [(tD0 - 0.1, "whoosh", 0.3), (tD2 - 0.1, "whoosh", 0.5)]
    for i in range(3):
        ev.append((tD2 + 0.2 + i * 0.55, "tick", 0.5))
    ev.append((tD2 + 0.55, "impact", 0.7))
    t = E_(5) - 0.5
    while t < tE0:
        ev.append((t, "thump", 0.22))
        t += 0.22
    ev += [(tE0 - 0.1, "whoosh", 0.5)]
    for dt in (0.0, 0.28, 0.58):
        ev.append((S_(6) - 0.12 + dt, "clank", 0.7))
    ev += [(tF0 - 0.05, "whoosh_dn", 0.6), (tF0 + 0.85, "thump", 0.9), (tF0 + 0.85, "pop", 0.7), (tF0 + 0.9, "sparkle", 0.5)]
    ev += [(tG0 - 0.05, "whoosh", 0.5), (tG0 + 0.1, "sparkle", 0.8), (tG0 + 0.1, "ding", 0.5)]
    ev += [(tH0 + 0.4, "clank", 0.9), (tH0 + 0.7, "clank", 0.6), (tH0 + 0.9, "whoosh_dn", 0.7), (tH0 + 1.4, "riser:1.2", 0.35)]
    ev += [(tI0 - 0.05, "whoosh", 0.5)]
    for i in range(6):
        ev.append((S_(10) + 0.2 + i * 0.28, "sparkle", 0.35))
    for i in range(14):
        ev.append((tI0 + i * 0.5, "tick", 0.3))
    ev += [(S_(11) - 0.2, "riser:1.35", 0.7), (S_(11) + 1.15, "impact", 1.0), (S_(11) + 1.2, "glitch", 0.6), (S_(11) + 1.55, "glitch", 0.5)]
    ev += [(tK0 + 0.3, "whoosh", 0.4), (tK0 + 1.25, "clank", 1.0), (tK0 + 1.27, "impact", 1.0), (tK0 + 1.3, "sparkle", 0.8), (tK0 + 0.4, "riser:0.85", 0.5)]
    ev += [(tL0 - 0.05, "whoosh_dn", 0.8)]
    for i in range(5):
        ev.append((tL0 + 0.6 + i * 0.85, "thump", 0.5))
    ev += [(tM0 - 0.8, "riser:0.8", 0.6), (tM0, "impact", 1.0), (tM0 + 0.05, "whoosh_dn", 0.5)]
    return sorted(ev, key=lambda e: e[0])
