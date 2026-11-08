"""Archive a finished video in the public repo (so Metricool can fetch it by URL) and print the raw URLs.

  python3 publish.py --repo /home/claude/narxtili-videos --day 3 --mp4 DAYDIR/out/day03.mp4 --cover DAYDIR/out/day03.jpg \
        --daydir DAYDIR --msg "Day 3: Inflyatsiya" --trailer "Co-Authored-By: ...\nClaude-Session: ..."
Copies videos/dayNN.mp4/.jpg and days/dayNN/{scenes.py,design.md,timing.json}, commits, pushes (rebasing if needed),
then waits until the raw URL answers 200 with the right size.  --trailer: the attribution lines from your session reminder.
"""
import argparse
import os
import shutil
import subprocess
import time

ap = argparse.ArgumentParser()
ap.add_argument("--repo", required=True)
ap.add_argument("--day", type=int, required=True)
ap.add_argument("--mp4", required=True)
ap.add_argument("--cover", required=True)
ap.add_argument("--daydir", required=True)
ap.add_argument("--msg", required=True)
ap.add_argument("--trailer", default="")
a = ap.parse_args()
R = a.repo
nn = f"{a.day:02d}"


def git(*args, check=True):
    return subprocess.run(["git", "-C", R, *args], check=check, capture_output=True, text=True)


os.makedirs(f"{R}/videos", exist_ok=True)
os.makedirs(f"{R}/days/day{nn}", exist_ok=True)
shutil.copy(a.mp4, f"{R}/videos/day{nn}.mp4")
shutil.copy(a.cover, f"{R}/videos/day{nn}.jpg")
for f in ("scenes.py", "design.md"):
    if os.path.exists(f"{a.daydir}/{f}"):
        shutil.copy(f"{a.daydir}/{f}", f"{R}/days/day{nn}/{f}")
if os.path.exists(f"{a.daydir}/work/timing.json"):
    shutil.copy(f"{a.daydir}/work/timing.json", f"{R}/days/day{nn}/timing.json")
if git("config", "user.email", check=False).returncode != 0:
    git("config", "user.email", "narxtili@users.noreply.github.com")
    git("config", "user.name", "Narx Tili video bot")
git("add", "-A")
msg = a.msg + ("\n\n" + a.trailer.replace("\\n", "\n") if a.trailer else "")
git("commit", "-m", msg)
git("fetch", "origin", "main")
git("rebase", "origin/main")
p = git("push", "origin", "HEAD:main", check=False)
print(p.stdout, p.stderr)
if p.returncode != 0:
    raise SystemExit("PUSH FAILED (see above). Is the Claude GitHub App installed on the repo?")
base = subprocess.run(["git", "-C", R, "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip().removesuffix(".git")
owner_repo = base.split("github.com/")[-1]
raw = f"https://raw.githubusercontent.com/{owner_repo}/main/videos/day{nn}"
size = os.path.getsize(a.mp4)
for _ in range(20):
    out = subprocess.run(["curl", "-sSIL", "--max-time", "30", raw + ".mp4"], capture_output=True, text=True).stdout.lower()
    if "http/2 200" in out or "http/1.1 200" in out.replace("connection established", ""):
        if f"content-length: {size}" in out:
            break
    time.sleep(3)
else:
    raise SystemExit("raw URL not serving the full file yet")
print("VIDEO_URL", raw + ".mp4")
print("COVER_URL", raw + ".jpg")
