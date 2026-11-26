"""Sirli Hikoyalar · 1-hikoya "Soat 03:07" · 1-qism "To'xtagan soat".  Scenes: A tower hook, B room, D exterior, E door, F question."""
import math
import os
import sys

_EP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_EP, "..", "..", "kit"))
from sh import *  # noqa: F401,F403,E402
import nt_char as C  # noqa: E402
from functools import lru_cache  # noqa: E402

WORK = os.path.join(_EP, "work")
EP_TAG = "SOAT 03:07 · 1/4"
SPK_COL = {"hik": (244, 240, 232), "jasur": (255, 164, 92), "malika": (110, 226, 214), "notanish": (255, 214, 120)}


# ----------------------------------------------------------------------------- cosy room (cached)
@lru_cache(None)
def room_bg():
    im = vgrad(W, H, (40, 36, 84), (22, 20, 54), 1.0)
    d = ImageDraw.Draw(im, "RGBA")
    for x in range(0, W, 90):                                       # wallpaper stripes
        d.rectangle([x, 0, x + 38, H], fill=(255, 255, 255, 9))
    # window with the tower in it
    wx0, wy0, wx1, wy1 = 640, 330, 960, 770
    win = vgrad(wx1 - wx0, wy1 - wy0, (14, 12, 44), (70, 48, 112), 0.9)
    wd = ImageDraw.Draw(win, "RGBA")
    for x, y, r in ((40, 40, 2), (120, 80, 2), (250, 50, 2), (200, 120, 1), (80, 150, 2), (280, 160, 1)):
        wd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 220))
    win.alpha_composite(radial(160, (190, 200, 255), 150, 2.0), (200, 20))
    wd.ellipse([240, 40, 280, 80], fill=(240, 236, 214, 255))
    tw = tower_src().resize((int(TW * 0.30), int(TH_ * 0.30)), Image.LANCZOS)
    win.alpha_composite(tw, (60, (wy1 - wy0) - tw.height + 30))
    town_ = town(3, wx1 - wx0, 120, (18, 14, 40), 0.35, hmin=50, hmax=100)
    win.alpha_composite(town_, (0, (wy1 - wy0) - 120))
    im.alpha_composite(win, (wx0, wy0))
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([wx0 - 14, wy0 - 14, wx1 + 14, wy0], fill=(120, 80, 62, 255))
    d.rectangle([wx0 - 14, wy1, wx1 + 14, wy1 + 20], fill=(150, 104, 80, 255))
    d.rectangle([wx0 - 14, wy0, wx0, wy1], fill=(110, 74, 58, 255))
    d.rectangle([wx1, wy0, wx1 + 14, wy1], fill=(110, 74, 58, 255))
    d.rectangle([(wx0 + wx1) // 2 - 5, wy0, (wx0 + wx1) // 2 + 5, wy1], fill=(120, 80, 62, 255))
    d.rectangle([wx0, (wy0 + wy1) // 2 - 5, wx1, (wy0 + wy1) // 2 + 5], fill=(120, 80, 62, 255))
    for sx, x0 in ((-1, wx0 - 20), (1, wx1 + 20)):                   # curtains
        pts = [(x0, wy0 - 40), (x0 + sx * 110, wy0 - 40), (x0 + sx * 90, wy1 + 120), (x0, wy1 + 120)]
        d.polygon(pts, fill=(24, 96, 104, 255))
        for k in range(1, 4):
            d.line([(x0 + sx * 26 * k, wy0 - 40), (x0 + sx * (22 * k), wy1 + 120)], fill=(14, 60, 70, 200), width=5)
    # shelf with books + frames
    d.rectangle([40, 640, 420, 662], fill=(120, 80, 62, 255))
    xs, rng = 52, np.random.default_rng(4)
    cols = [(200, 74, 74), (230, 180, 70), (70, 130, 200), (96, 170, 120), (180, 110, 190), (226, 120, 60)]
    while xs < 380:
        bw, bh = int(rng.integers(26, 44)), int(rng.integers(90, 150))
        d.rectangle([xs, 640 - bh, xs + bw, 640], fill=cols[int(rng.integers(0, 6))] + (255,))
        xs += bw + 4
    for (fx, fy, fw, fh) in ((80, 400, 130, 170), (240, 430, 150, 130)):
        d.rectangle([fx, fy, fx + fw, fy + fh], fill=(120, 80, 62, 255))
        d.rectangle([fx + 10, fy + 10, fx + fw - 10, fy + fh - 10], fill=(66, 74, 130, 255))
        d.ellipse([fx + fw * 0.3, fy + fh * 0.25, fx + fw * 0.7, fy + fh * 0.7], fill=(255, 214, 150, 200))
    # desk
    desk = vgrad(W, H - 1390, (108, 70, 58), (44, 28, 30), 1.0)
    im.alpha_composite(desk, (0, 1390))
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, 1386, W, 1396], fill=(190, 140, 110, 255))
    # lamp (left), cup with pencils (right)
    d.polygon([(70, 1390), (96, 1390), (96, 1300), (200, 1160), (186, 1148), (70, 1288)], fill=(40, 40, 56, 255))
    d.polygon([(130, 1110), (280, 1110), (310, 1210), (100, 1210)], fill=(255, 206, 110, 255))
    d.rectangle([60, 1384, 130, 1396], fill=(40, 40, 56, 255))
    d.rounded_rectangle([880, 1320, 960, 1392], radius=10, fill=(200, 70, 80, 255))
    for k, c in enumerate(((255, 214, 90), (110, 200, 240), (240, 240, 240))):
        d.line([(900 + k * 20, 1322), (890 + k * 26, 1250)], fill=c + (255,), width=9)
    return im


def lamp_glow(cv, t):
    k = 0.93 + 0.07 * math.sin(t * 7.3) * math.sin(t * 2.1)
    put(cv, radial(1100, (255, 196, 110), int(165 * k), 2.0), 210, 1220, 1.0, 1.0)


@lru_cache(None)
def dim_img(a, h=1020):
    ramp = np.clip((h - np.arange(h, dtype=np.float32)) / (h * 0.45), 0, 1) ** 1.3 * a
    arr = np.zeros((h, W, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = 6, 4, 22
    arr[..., 3] = ramp[:, None].astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


# ----------------------------------------------------------------------------- notebook inset (31 nights)
@lru_cache(None)
def notebook(n):
    w, h = 760, 480
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=26, fill=(246, 238, 214, 255))
    d.rounded_rectangle([0, 0, 34, h - 1], radius=16, fill=(60, 80, 150, 255))
    for y in range(86, h - 20, 52):
        d.line([(60, y), (w - 30, y)], fill=(160, 180, 220, 255), width=2)
    d.text((70, 30), "SOAT 03:07", font=F("xb", 38), fill=(60, 44, 90, 255))
    ink = (40, 34, 70, 255)
    for i in range(n):
        g, k = divmod(i, 5)
        row, col = divmod(g, 4)
        x0, y0 = 80 + col * 168, 112 + row * 150
        if k < 4:
            d.line([(x0 + k * 26, y0), (x0 + k * 26, y0 + 96)], fill=ink, width=7)
        else:
            d.line([(x0 - 10, y0 + 80), (x0 + 106, y0 + 12)], fill=(200, 60, 70, 255), width=7)
    return im


# ----------------------------------------------------------------------------- build
def build(tim):
    S_ = lambda n: tim.S("L%02d" % n)
    E_ = lambda n: tim.E("L%02d" % n)
    tB0 = S_(3) - 0.65
    tD0 = E_(8) + 0.30
    tE0 = E_(10) + 0.05
    tF0 = S_(12)
    t_stop = tim.ws(7) + 0.30                      # clock stops on the word "to'xtaydi"
    t_cat = E_(6) + 0.10
    t_keyfall = S_(7) - 0.62
    t_key = S_(7)
    t_close0, t_close1 = S_(8) - 0.10, E_(8) + 0.25
    t_light = S_(9) + 1.7                          # "chiroq yondi"
    t_tick6 = S_(10) - 0.10                        # 3:06
    t_stop2 = S_(10) + 1.35                        # 3:07 again, hands stop
    end0 = tim.end0 - 1.0

    # ------------------------------------------------------------ hosts
    envJ = C.speech_env(f"{WORK}/spk_jasur.wav")
    envM = C.speech_env(f"{WORK}/spk_malika.wav")
    BY = 1500
    jb = dict(cx=300, by=BY, sc=0.80, al=1.0, rise=0.0)
    mb = dict(cx=790, by=BY, sc=0.80, al=1.0, rise=0.0)

    def track(base, hid, evs):
        ks = [(0.0, "neutral", dict(base, al=0.0, rise=320), 0.01)]
        for e in sorted(evs, key=lambda e: e[0]):
            ks.append(e)
        return ks

    up = dict(ly=-1.0, lx=0.0, brow=0.55, eo=1.12)
    jas = [
        (tB0, "neutral", dict(jb), 0.55, "out"),
        (S_(3), "think", dict(jb, sc=0.90, ly=0.8), 0.25),
        (E_(3) + 0.15, "neutral", dict(jb), 0.35),
        (S_(5), "grin", dict(jb, sc=0.90), 0.25),
        (E_(5) + 0.15, "smile", dict(jb), 0.35),
        (S_(7) - 0.1, "shock", dict(jb, sc=0.92), 0.2),
        (E_(7) + 0.15, "shock", dict(jb), 0.35),
        (E_(8), "neutral", dict(jb), 0.4),
        (tD0, "neutral", dict(jb, cx=240, sc=0.62, **up), 0.5),
        (S_(10), "awe", dict(jb, cx=240, sc=0.68, **up), 0.25),
        (E_(10), "panic", dict(jb, cx=240, sc=0.62, **up), 0.4),
        (tE0 - 0.05, "panic", dict(jb, cx=240, sc=0.62, al=0.0, **up), 0.35),
    ]
    mal = [
        (tB0, "neutral", dict(mb), 0.55, "out"),
        (S_(4), "smile", dict(mb, sc=0.90), 0.25),
        (S_(4) + 2.0, "wink", dict(mb, sc=0.90), 0.2),
        (E_(4) + 0.15, "smile", dict(mb), 0.35),
        (S_(6), "no", dict(mb, sc=0.90), 0.25),
        (E_(6) + 0.15, "neutral", dict(mb), 0.35),
        (t_cat + 0.1, "shock", dict(mb), 0.25),
        (S_(8), "think", dict(mb, sc=0.90), 0.25),
        (E_(8) + 0.15, "neutral", dict(mb), 0.35),
        (tD0, "neutral", dict(mb, cx=850, sc=0.62, **up), 0.5),
        (S_(9), "shock", dict(mb, cx=850, sc=0.68, **up), 0.25),
        (E_(9) + 0.1, "awe", dict(mb, cx=850, sc=0.62, **up), 0.4),
        (tE0 - 0.05, "panic", dict(mb, cx=850, sc=0.62, al=0.0, **up), 0.35),
    ]
    hostJ = C.Host(track(jb, 0, jas), env=envJ, palette="jasur", halo=False, mouth_gain=1.0,
                   blinks=(1.3, 3.9, 6.2, 9.0, 12.1, 15.4, 19.2, 23.0, 27.0, 31.5, 36.0, 41.0))
    hostM = C.Host(track(mb, 0, mal), env=envM, palette="malika", halo=False, mouth_gain=1.0,
                   blinks=(0.9, 3.2, 5.8, 8.4, 11.3, 14.8, 18.4, 22.0, 26.4, 30.8, 35.1, 40.2))

    # ------------------------------------------------------------ scene A: the tower hook
    def minutes_A(t):
        if t >= t_stop:
            return 187.0 + 0.0
        return lerp(160.0, 187.0, ease_out_cubic(t / t_stop) ** 1.0)

    def sc_tower(cv, t):
        if t >= tB0:
            return
        cv.alpha_composite(sky_base())
        stars(cv, t, 1100)
        k = clamp(t / 5.5)
        sc = lerp(1.0, 1.78, ease_in_out(k)) + (0.12 * clamp((t - 5.5) / 4.4) if t > 5.5 else 0)
        fx, fy = lerp(600, 540, ease_in_out(k)), lerp(700, 770, ease_in_out(k))
        base_y = fy + (TH_ - FACE[1]) * sc
        put(cv, town(11, 1500, 430, (28, 22, 64), 0.28), 540 - 40 * k, base_y - 30 - 215, 1.0)
        put(cv, town(12, 1500, 420, (16, 13, 40), 0.22, hmin=150, hmax=380), 540 + 30 * k, base_y + 60 - 210, 1.0)
        M = minutes_A(t)
        draw_tower(cv, fx, fy, sc, M % 60, M // 60 + (M % 60) / 60.0, win_light=0.0)
        # ground fog
        fog = vgrad(W, 420, (60, 44, 110), (60, 44, 110), 1.0)
        fog.putalpha(Image.fromarray((np.linspace(0, 80, 420)[:, None] * np.ones((1, W))).astype(np.uint8), "L"))
        if base_y < H + 400:
            put(cv, fog, 540, min(H, base_y) - 120, 1.0)
        # big digital time after the stop
        if t >= t_stop:
            p = ease_out_back((t - t_stop) / 0.5, 2.0)
            big = glow(gtext("03:07", 230, (255, 238, 170), (255, 164, 40)), (255, 170, 60), 34, 1.3)
            shk = 10 * math.sin((t - t_stop) * 60) * max(0, 1 - (t - t_stop) / 0.4)
            put(cv, big, 540 + shk, 1070, clamp((t - t_stop) / 0.2), 0.5 + 0.5 * p)
        if t >= S_(2) + 2.2:
            put(cv, glow(stext("NEGA?", 150, (110, 220, 255), (6, 4, 22), 8), (110, 220, 255), 26, 1.2), 540, 1245, 1.0,
                0.6 + 0.4 * ease_out_back((t - (S_(2) + 2.2)) / 0.4, 2.0))

    # ------------------------------------------------------------ scene B: the room
    def sc_room(cv, t):
        if not (tB0 <= t < tD0 + 0.01):
            return
        cv.alpha_composite(room_bg())
        lamp_glow(cv, t)
        # cat on the sill
        if t >= t_cat:
            p = ease_out_back((t - t_cat) / 0.45, 1.8)
            put(cv, cat_src(), lerp(1100, 805, ease_out_cubic((t - t_cat) / 0.4)), 770 - 100 * 0.62 - 6, clamp((t - t_cat) / 0.15), 0.62 * (0.7 + 0.3 * p))
        # key falls from the cat to the desk
        if t_keyfall <= t:
            q = clamp((t - t_keyfall) / (t_key - t_keyfall))
            x = lerp(790, 430, q)
            y = lerp(700, 1425, q * q)
            rot = -40 + 300 * q
            if q >= 1.0:
                x, y, rot = 430, 1425, 14
                bounce = max(0.0, 1 - (t - t_key) / 0.35)
                y -= 36 * math.sin((t - t_key) * 14) * bounce
            put(cv, key_src(), x, y, 1.0, 0.20, rot)
            if q >= 1.0:
                sparks(cv, t, t_key, 430, 1415, n=12, col=(255, 226, 140), seed=4, life=0.5, speed=300, size=4, grav=500)

    def sc_inset(cv, t):
        """evidence insets (above the characters): notebook (DALIL 1) and the VII key (DALIL 2)"""
        a0, a1 = S_(3) + 0.1, E_(4) + 0.6
        if a0 <= t < a1:
            fo = clamp((a1 - t) / 0.3)
            put(cv, dim_img(int(175 * fo)), W / 2, 510, 1.0)
            n = int(31 * ease_out_cubic((t - (S_(3) + 0.4)) / 1.9))
            pop(cv, notebook(max(0, n)), 540, 560, t, a0, 0.4, fo)
            if t > S_(3) + 2.4:
                pop(cv, evidence_card(1, "", "Soat 31 tun ketma-ket 03:07 da to'xtagan"), 540, 860, t, S_(3) + 2.4, 0.4, fo)
        if t_close0 <= t < t_close1:
            fo = clamp((t_close1 - t) / 0.3)
            put(cv, dim_img(int(195 * fo)), W / 2, 510, 1.0)
            k = clamp((t - t_close0) / 0.45)
            rot = 8 + 6 * math.sin(t * 2.2)
            kk = glow(key_src(), (255, 200, 90), 30, 1.1)
            put(cv, kk, 540, 560, fo, 0.95 * (0.6 + 0.4 * ease_out_back(k, 1.8)), rot)
            put(cv, radial(500, (255, 244, 200), int(160 * (0.5 + 0.5 * math.sin(t * 5))), 1.8), 410, 520, fo, 1.0)
            if t > t_close0 + 0.7:
                pop(cv, evidence_card(2, "", "Mis kalit. Raqami: VII (yetti)"), 540, 860, t, t_close0 + 0.7, 0.4, fo)

    # ------------------------------------------------------------ scene D: outside, under the tower
    def sc_outside(cv, t):
        if not (tD0 <= t < tE0 + 0.01):
            return
        cv.alpha_composite(sky_base())
        stars(cv, t, 1000)
        fx, fy, sc = 540, 470, 1.0
        base_y = fy + (TH_ - FACE[1]) * sc
        put(cv, town(21, 1500, 420, (28, 22, 64), 0.3), 540, base_y - 70, 1.0)
        put(cv, town(22, 1500, 380, (16, 13, 40), 0.22, hmin=130, hmax=300), 540, base_y + 60, 1.0)
        wl = ease_out_cubic((t - t_light) / 0.5) if t >= t_light else 0.0
        flick = 1.0 - (0.35 * (math.sin(t * 40) > 0.6) if wl > 0.9 else 0)
        # clock: 3:05 -> 3:06 -> 3:07 (stops)
        if t < t_tick6:
            m = 5.0
        elif t < t_stop2:
            m = 6.0
        else:
            m = 7.0
        m_vis = m + (0.35 * max(0, 1 - (t - (t_tick6 if m == 6.0 else t_stop2)) / 0.18) if m > 5.5 else 0.0)
        draw_tower(cv, fx, fy, sc, m_vis, 3.0 + m_vis / 60.0, win_light=wl * flick)
        # street
        ground = vgrad(W, H - int(base_y), (30, 24, 62), (12, 10, 30), 1.0)
        cv.alpha_composite(ground, (0, int(base_y)))
        if t >= t_stop2:
            put(cv, glow(stext("03:07", 120, (255, 230, 150), (6, 4, 22), 6), (255, 170, 60), 24, 1.2), 540, 770, clamp((t - t_stop2) / 0.2), 1.0)

    # ------------------------------------------------------------ scene E/F: the door
    def sc_door(cv, t):
        if t < tE0:
            return
        cv.alpha_composite(vgrad(W, H, (12, 10, 34), (30, 22, 56), 1.0))
        stars(cv, t, 500, 0.5)
        d0 = tE0 + 0.2
        door_scene(cv, t, d0, 540, 1060, figure=1.0, glint=0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 4.0)) if t > S_(11) else 0.0)
        # dust in the light
        rng = np.random.default_rng(9)
        d = ImageDraw.Draw(cv, "RGBA")
        for i in range(22):
            x = 540 + (rng.uniform(-1, 1)) * 300 + 20 * math.sin(t * 0.8 + i)
            y = 1060 + rng.uniform(-1, 1) * 420 - ((t * 20 + i * 37) % 120)
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 200, 120, int(60 * clamp((t - d0) / 1.5))))
        if t >= tF0:
            k = ease_out_back((t - tF0) / 0.5, 1.8)
            put(cv, glow(stext("BU KIM?", 150, (255, 214, 120), (6, 4, 22), 9), (255, 170, 60), 28, 1.3), 540, 520, clamp((t - tF0) / 0.2), 0.5 + 0.5 * k)

    def sc_hosts(cv, t):
        if tB0 <= t < tE0:
            hostM.draw(cv, t)
            hostJ.draw(cv, t)

    # ------------------------------------------------------------ overlay + captions + camera
    def lay_cards(cv, t):
        sc_inset(cv, t)

    def top_caps(cv, t):
        if t >= tim.end0 - 0.05:
            return
        col = SPK_COL["hik"]
        for L in tim.segs:
            if L["s2"] - 0.05 <= t <= L["e2"] + 0.35:
                col = SPK_COL.get(L["spk"], col)
        captions(cv, tim, t, y=1392, size=70, maxw=940, n=3, col=(244, 240, 232), hi=col)
        if t < tim.end0 - 1.2:
            brand_chip(cv, t, EP_TAG, 0.85)

    cam = Cam(1.02)
    cam.key(0.0, 1.02).key(t_stop, 1.07).key(tB0 - 0.01, 1.12).key(tB0, 1.03).key(tD0 - 0.01, 1.07).key(tD0, 1.0)
    cam.key(S_(10) - 0.35, 1.0).key(S_(10) + 0.5, 1.42, 0, 270).key(t_stop2 + 0.3, 1.5, 0, 300).key(tE0 - 0.02, 1.2, 0, 120)
    cam.key(tE0, 1.0).key(tF0, 1.10).key(end0, 1.16)
    cam.punch(t_stop, 0.05, 0.4).shake(t_stop, 14, 0.5)
    cam.punch(t_key, 0.03, 0.3).shake(t_key, 8, 0.3)
    cam.punch(t_stop2, 0.04, 0.4).shake(t_stop2, 12, 0.5)
    cam.shake(tE0 + 0.6, 7, 0.8).punch(tF0, 0.05, 0.5).shake(tF0, 12, 0.6)

    whips = [(tB0, 0.30, 140, 0), (tD0, 0.30, 140, 0), (tE0, 0.30, 150, 90)]
    flashes = [(t_stop, 0.18), (t_stop2, 0.15), (tF0, 0.2)]
    chroma = [(t_stop, 8, 0.4), (t_stop2, 8, 0.4), (tF0, 10, 0.5)]
    reel = StoryReel(tim, [sc_tower, sc_room, sc_outside, sc_door, sc_hosts, lay_cards], cam=cam, vignette=0.55, grain=0.30,
                     bloom=0.30, whips=whips, flashes=flashes, chroma_at=chroma, top=[top_caps],
                     end_fn=end_card("2-QISM · ertaga 18:00", end0, tim.total))
    return reel


def sfx(tim):
    S_ = lambda n: tim.S("L%02d" % n)
    E_ = lambda n: tim.E("L%02d" % n)
    tB0, tD0, tE0, tF0 = S_(3) - 0.65, E_(8) + 0.30, E_(10) + 0.05, S_(12)
    t_stop = tim.ws(7) + 0.30
    ev = []
    t = 0.2
    while t < t_stop - 0.1:                                        # fast ticking time-lapse
        ev.append((round(t, 3), "tick", 0.22))
        t += 0.17
    ev += [(t_stop, "impact", 0.85), (t_stop, "thump", 0.7), (t_stop + 0.05, "glitch", 0.3)]
    ev += [(S_(2) + 2.2, "pop", 0.5)]
    ev += [(tB0 - 0.12, "whoosh", 0.55), (tD0 - 0.1, "whoosh", 0.55), (tE0 - 0.05, "whoosh", 0.6)]
    ev += [(S_(3) + 2.4, "ding", 0.5), (S_(3) + 0.4, "tick", 0.3), (S_(3) + 0.9, "tick", 0.3), (S_(3) + 1.4, "tick", 0.3), (S_(3) + 1.9, "tick", 0.3)]
    t_cat = E_(6) + 0.10
    ev += [(t_cat, "pop", 0.7), (t_cat + 0.1, "thump", 0.4)]
    ev += [(S_(7), "clank", 0.8), (S_(7) - 0.62, "whoosh_dn", 0.3)]
    ev += [(S_(8) - 0.1, "sparkle", 0.6), (S_(8) + 0.6, "ding", 0.5)]
    ev += [(S_(9) + 0.7, "riser:1.0", 0.45), (S_(9) + 1.7, "sparkle", 0.7), (S_(9) + 1.7, "thump", 0.5)]
    ev += [(S_(10) - 0.1, "tick", 0.6), (S_(10) + 1.35, "tick", 0.7), (S_(10) + 1.38, "impact", 0.9)]
    ev += [(tE0 + 0.3, "riser:2.2", 0.4), (tE0 + 2.5, "thump", 0.6), (S_(11) + 4.3, "sparkle", 0.5)]
    ev += [(tF0, "impact", 0.95), (tF0, "thump", 0.8), (tF0 + 0.1, "glitch", 0.4)]
    ev += [(tim.end0 - 1.0, "whoosh_dn", 0.4)]
    return ev
