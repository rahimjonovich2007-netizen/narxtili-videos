"""Render a day's video.

  python3 render.py DAYDIR stills 1.0 3.5 8        -> DAYDIR/work/stills/tXX.XX.png  (look at them with Read before the full render)
  python3 render.py DAYDIR sheet 0 26 14           -> DAYDIR/work/sheet.png contact sheet of 14 evenly spaced frames (t from..to)
  python3 render.py DAYDIR full NAME [cover_t]     -> DAYDIR/out/NAME.mp4 + NAME.jpg   (takes ~5-10 min on 2 CPUs)

DAYDIR/scenes.py must define build(tim) -> nt_kit.Reel   (see days/day03/scenes.py for a full example).
"""
import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nt_kit as K  # noqa: E402
from PIL import Image  # noqa: E402

D, mode = sys.argv[1].rstrip("/"), sys.argv[2]
sys.path.insert(0, D)
spec = importlib.util.spec_from_file_location("scenes", f"{D}/scenes.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
tim = K.Timing(f"{D}/work/timing.json")
reel = mod.build(tim)

if mode == "stills":
    K.stills(reel, [float(a) for a in sys.argv[3:]], f"{D}/work/stills")
    print("stills in", f"{D}/work/stills", "| total", round(tim.total, 2), "s,", tim.nf, "frames")
elif mode == "sheet":
    t0, t1, n = float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
    ts = [t0 + (t1 - t0) * i / (n - 1) for i in range(n)]
    cols = 7 if n > 8 else 4
    rows = -(-n // cols)
    tw, th = 270, 480
    sheet = Image.new("RGB", (cols * tw, rows * th), (30, 30, 30))
    for i, tv in enumerate(ts):
        sheet.paste(reel.draw(tv).convert("RGB").resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
    sheet.save(f"{D}/work/sheet.png")
    print("sheet ->", f"{D}/work/sheet.png", "times", [round(x, 1) for x in ts])
else:
    name = sys.argv[3]
    cover_t = float(sys.argv[4]) if len(sys.argv) > 4 else 2.9
    K.render(reel, f"{D}/out/{name}.mp4", f"{D}/work/mix.wav", cover_t=cover_t)
