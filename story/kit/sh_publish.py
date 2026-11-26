"""Archive a finished Sirli Hikoyalar episode in the public repo (so Metricool can fetch it by URL) and print the raw URLs.

  python3 sh_publish.py --repo /home/claude/narxtili-videos --ep s1e1 --epdir story/s1/ep1 --msg "S1E1: To'xtagan soat" --trailer "Co-Authored-By: ...\nClaude-Session: ..."
Copies story/videos/<ep>.mp4/.jpg and story/<epdir>/{scenes.py,timing.json,in/lines.json,in/plan.json}, commits, pushes (rebasing if needed),
then waits until the raw URL answers 200 with the right size.
"""
import argparse
import os
import shutil
import subprocess
import time

ap = argparse.ArgumentParser()
ap.add_argument("--repo", required=True)
ap.add_argument("--ep", required=True, help="short id, e.g. s1e1")
ap.add_argument("--epdir", required=True, help="episode dir (relative to repo or absolute)")
ap.add_argument("--msg", required=True)
ap.add_argument("--trailer", default="")
a = ap.parse_args()
R = a.repo
E = a.epdir if os.path.isabs(a.epdir) else f"{R}/{a.epdir}"


def git(*args, check=True):
    return subprocess.run(["git", "-C", R, *args], check=check, capture_output=True, text=True)


os.makedirs(f"{R}/story/videos", exist_ok=True)
shutil.copy(f"{E}/out/{os.path.basename(E.rstrip('/'))}.mp4" if os.path.exists(f"{E}/out/{os.path.basename(E.rstrip('/'))}.mp4") else f"{E}/out/ep1.mp4",
            f"{R}/story/videos/{a.ep}.mp4")
shutil.copy(f"{E}/out/{os.path.basename(E.rstrip('/'))}.jpg" if os.path.exists(f"{E}/out/{os.path.basename(E.rstrip('/'))}.jpg") else f"{E}/out/ep1.jpg",
            f"{R}/story/videos/{a.ep}.jpg")
git("add", "-A")
if git("config", "user.email", check=False).returncode != 0:
    git("config", "user.email", "sirli@users.noreply.github.com")
    git("config", "user.name", "Sirli Hikoyalar bot")
msg = a.msg + ("\n\n" + a.trailer.replace("\\n", "\n") if a.trailer else "")
git("commit", "-m", msg)
git("fetch", "origin", "main")
git("rebase", "origin/main")
p = git("push", "origin", "HEAD:main", check=False)
print(p.stdout, p.stderr)
if p.returncode != 0:
    raise SystemExit("PUSH FAILED (see above)")
base = subprocess.run(["git", "-C", R, "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip().removesuffix(".git")
owner_repo = base.split("github.com/")[-1].split("@")[-1]
raw = f"https://raw.githubusercontent.com/{owner_repo}/main/story/videos/{a.ep}"
size = os.path.getsize(f"{R}/story/videos/{a.ep}.mp4")
for _ in range(20):
    out = subprocess.run(["curl", "-sSIL", "--max-time", "30", raw + ".mp4"], capture_output=True, text=True).stdout.lower()
    if " 200" in out and f"content-length: {size}" in out:
        break
    time.sleep(3)
else:
    raise SystemExit("raw URL not serving the full file yet")
print("VIDEO_URL", raw + ".mp4")
print("COVER_URL", raw + ".jpg")
