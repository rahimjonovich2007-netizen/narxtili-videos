# Avatar: keyhole + warm light + clock hands at 3:07 (original artwork)
import numpy as np, math
from PIL import Image, ImageDraw, ImageFilter
S = 2
N = 1080 * S
rng = np.random.default_rng(7)

def grad_bg():
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / N
    d = np.sqrt((xx - 0.5) ** 2 + (yy - 0.45) ** 2)
    t = np.clip(d / 0.75, 0, 1)
    c0 = np.array((46, 38, 110), np.float32)   # indigo centre
    c1 = np.array((10, 9, 32), np.float32)     # deep night edge
    img = c0[None, None] * (1 - t[..., None]) + c1[None, None] * t[..., None]
    return img

bg = grad_bg()
im = Image.fromarray(bg.astype(np.uint8), "RGB").convert("RGBA")

# soft bokeh dots
bok = Image.new("RGBA", (N, N), (0, 0, 0, 0))
bd = ImageDraw.Draw(bok)
for _ in range(34):
    x, y = rng.uniform(0.05, 0.95) * N, rng.uniform(0.05, 0.95) * N
    r = rng.uniform(10, 38) * S
    col = (255, 190, 90, int(rng.uniform(18, 60))) if rng.random() < 0.7 else (110, 220, 255, int(rng.uniform(14, 40)))
    bd.ellipse((x - r, y - r, x + r, y + r), fill=col)
bok = bok.filter(ImageFilter.GaussianBlur(6 * S))
im = Image.alpha_composite(im, bok)

cx, cy = 540 * S, 440 * S
R = 150 * S

# light fan below keyhole (volumetric rays)
fan = Image.new("RGBA", (N, N), (0, 0, 0, 0))
fd = ImageDraw.Draw(fan)
for k in range(-6, 7):
    ang = math.radians(90 + k * 6.2)
    L = 900 * S
    w = math.radians(2.1)
    p0 = (cx, cy + 40 * S)
    p1 = (cx + math.cos(ang - w) * L, cy + math.sin(ang - w) * L)
    p2 = (cx + math.cos(ang + w) * L, cy + math.sin(ang + w) * L)
    fd.polygon([p0, p1, p2], fill=(255, 196, 110, int(46 - abs(k) * 4)))
fan = fan.filter(ImageFilter.GaussianBlur(10 * S))
im = Image.alpha_composite(im, fan)

# keyhole mask
def keyhole_mask(scale=1.0, dy=0):
    m = Image.new("L", (N, N), 0)
    md = ImageDraw.Draw(m)
    r = R * scale
    md.ellipse((cx - r, cy + dy - r, cx + r, cy + dy + r), fill=255)
    top_w, bot_w = 70 * S * scale, 150 * S * scale
    y0, y1 = cy + dy + r * 0.55, cy + dy + 400 * S * scale
    md.polygon([(cx - top_w, y0), (cx + top_w, y0), (cx + bot_w, y1), (cx - bot_w, y1)], fill=255)
    md.rounded_rectangle((cx - bot_w, y1 - 22 * S, cx + bot_w, y1 + 22 * S), radius=22 * S, fill=255)
    return m

mask = keyhole_mask()

# outer glow
glow = Image.new("RGBA", (N, N), (255, 170, 70, 0))
ga = mask.filter(ImageFilter.GaussianBlur(46 * S)).point(lambda v: int(v * 0.85))
glow.putalpha(ga)
im = Image.alpha_composite(im, glow)
glow2 = Image.new("RGBA", (N, N), (255, 214, 140, 0))
glow2.putalpha(mask.filter(ImageFilter.GaussianBlur(16 * S)).point(lambda v: int(v * 0.8)))
im = Image.alpha_composite(im, glow2)

# keyhole fill: warm gradient (bright centre -> amber)
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
dd = np.sqrt((xx - cx) ** 2 + (yy - (cy + 30 * S)) ** 2) / (R * 1.5)
t = np.clip(dd, 0, 1)[..., None]
cA = np.array((255, 247, 214), np.float32)
cB = np.array((255, 168, 64), np.float32)
fill = cA * (1 - t) + cB * t
fillim = Image.fromarray(fill.astype(np.uint8), "RGB").convert("RGBA")
fillim.putalpha(mask)
im = Image.alpha_composite(im, fillim)

# thin cyan rim
edge = mask.filter(ImageFilter.MaxFilter(9 * S // 2 * 2 + 1))
rim = Image.new("RGBA", (N, N), (120, 225, 255, 0))
rim_a = np.clip(np.array(edge, np.float32) - np.array(mask, np.float32), 0, 255) * 0.9
rim.putalpha(Image.fromarray(rim_a.astype(np.uint8), "L"))
im = Image.alpha_composite(im, rim)

# clock face in the round part: ticks + hands at 3:07 (hour -> III, minute -> VII)
cl = Image.new("RGBA", (N, N), (0, 0, 0, 0))
cd = ImageDraw.Draw(cl)
ink = (36, 26, 86, 255)
rc = R * 0.78
for i in range(12):
    a = math.radians(i * 30 - 90)
    r0 = rc * (0.84 if i % 3 else 0.72)
    cd.line((cx + math.cos(a) * r0, cy + math.sin(a) * r0, cx + math.cos(a) * rc, cy + math.sin(a) * rc),
            fill=ink, width=int((7 if i % 3 else 11) * S))
def hand(deg, L, w):
    a = math.radians(deg - 90)
    cd.line((cx, cy, cx + math.cos(a) * L, cy + math.sin(a) * L), fill=ink, width=int(w * S))
hand(90 + 3.5, rc * 0.50, 15)   # hour hand: just past III
hand(210, rc * 0.78, 10)         # minute hand: 35 min -> VII
cd.ellipse((cx - 13 * S, cy - 13 * S, cx + 13 * S, cy + 13 * S), fill=ink)
im = Image.alpha_composite(im, cl)

# sparkle
sp = Image.new("RGBA", (N, N), (0, 0, 0, 0))
sd = ImageDraw.Draw(sp)
sx, sy = 780 * S, 270 * S
for L, w in ((70, 7), (46, 5)):
    sd.polygon([(sx, sy - L * S), (sx + w * S, sy), (sx, sy + L * S), (sx - w * S, sy)], fill=(255, 255, 255, 235))
    sd.polygon([(sx - L * S, sy), (sx, sy - w * S), (sx + L * S, sy), (sx, sy + w * S)], fill=(255, 255, 255, 235))
sp2 = sp.filter(ImageFilter.GaussianBlur(14 * S))
im = Image.alpha_composite(im, sp2)
im = Image.alpha_composite(im, sp)

# vignette
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / N
v = 1 - 0.45 * np.clip((np.sqrt((xx - 0.5) ** 2 + (yy - 0.5) ** 2) - 0.35) / 0.4, 0, 1) ** 1.5
arr = np.array(im, np.float32)
arr[..., :3] *= v[..., None]
im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA").convert("RGB")
im = im.resize((1080, 1080), Image.LANCZOS)
im.save("avatar.png")
# preview as Instagram circle crop
m = Image.new("L", (1080, 1080), 0)
ImageDraw.Draw(m).ellipse((0, 0, 1079, 1079), fill=255)
prev = Image.new("RGB", (1080, 1080), (255, 255, 255))
prev.paste(im, (0, 0), m)
prev.resize((320, 320), Image.LANCZOS).save("avatar_circle_preview.png")
print("ok")
