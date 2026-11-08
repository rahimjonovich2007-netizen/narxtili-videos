"""Quality gate for a finished Reel.  python3 qa.py VIDEO.mp4 OUTDIR [n_frames]
Checks container/codec/size/loudness/faststart and writes OUTDIR/qa_sheet.png (look at it with Read!). Exit code 1 if a check fails."""
import json
import os
import re
import struct
import subprocess
import sys

from PIL import Image

V, OUT = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 14
os.makedirs(OUT, exist_ok=True)
fails = []


def check(name, ok, info=""):
    print(("PASS " if ok else "FAIL ") + name, info)
    if not ok:
        fails.append(name)


pr = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", V]))
v = next(s for s in pr["streams"] if s["codec_type"] == "video")
a = next(s for s in pr["streams"] if s["codec_type"] == "audio")
dur = float(pr["format"]["duration"])
num, den = v["r_frame_rate"].split("/")
check("video H.264 High yuv420p 1080x1920 30fps", v["codec_name"] == "h264" and v["pix_fmt"] == "yuv420p" and v["width"] == 1080
      and v["height"] == 1920 and abs(int(num) / int(den) - 30) < 0.01, f'{v["codec_name"]} {v["profile"]} {v["pix_fmt"]} {v["width"]}x{v["height"]} {num}/{den}')
check("audio AAC 48 kHz stereo", a["codec_name"] == "aac" and int(a["sample_rate"]) == 48000 and a["channels"] == 2, f'{a["codec_name"]} {a["sample_rate"]} ch{a["channels"]}')
check("duration 15-45 s", 15 <= dur <= 45, f"{dur:.2f}s")
size = os.path.getsize(V)
check("size < 90 MB", size < 90e6, f"{size / 1e6:.1f} MB")

# moov before mdat (faststart)
with open(V, "rb") as f:
    pos, order = 0, []
    total = os.path.getsize(V)
    while pos < total and len(order) < 8:
        f.seek(pos)
        hdr = f.read(16)
        sz, typ = struct.unpack(">I4s", hdr[:8])
        if sz == 1:
            sz = struct.unpack(">Q", hdr[8:16])[0]
        order.append(typ.decode("latin1"))
        if sz == 0:
            break
        pos += sz
check("moov before mdat (faststart)", "moov" in order and "mdat" in order and order.index("moov") < order.index("mdat"), order)

# loudness
r = subprocess.run(["ffmpeg", "-nostats", "-i", V, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
summ = r[r.rfind("Summary:"):]
lufs = float(re.search(r"I:\s+(-?\d+\.\d+) LUFS", summ).group(1))
tp = float(re.search(r"Peak:\s+(-?\d+\.\d+) dBFS", summ).group(1))
check("loudness -15.5..-12.5 LUFS", -15.5 <= lufs <= -12.5, f"{lufs} LUFS")
check("true peak <= -1.0 dBFS", tp <= -1.0, f"{tp} dBTP")

# contact sheet
cols, tw, th = 7, 270, 480
rows = -(-N // cols)
sheet = Image.new("RGB", (cols * tw, rows * th), (30, 30, 30))
for i in range(N):
    t = (dur - 0.05) * i / (N - 1)
    fp = f"{OUT}/_f{i}.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", V, "-frames:v", "1", fp], check=True)
    sheet.paste(Image.open(fp).convert("RGB").resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
    os.remove(fp)
sheet.save(f"{OUT}/qa_sheet.png")
print("contact sheet ->", f"{OUT}/qa_sheet.png", "(open it and check: text spelling, safe zone, overlaps, no blank frames)")
print("RESULT:", "ALL PASS" if not fails else "FAILED: " + ", ".join(fails))
sys.exit(1 if fails else 0)
