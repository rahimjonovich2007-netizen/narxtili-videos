"""Tighten the single-take narration and write timing.json.

Usage: python3 audio.py DAYDIR
Needs:  DAYDIR/in/voice.<wav|mp3|m4a|...>   the TTS take
        DAYDIR/in/words.json                [[text, start_ms, end_ms], ...] from audio_transcribe(word_timestamps)
        DAYDIR/in/segments.json  (optional) [[name, first_word_idx, last_word_idx], ...]; default = one segment per
                                            sentence (words ending in . ? !), names "s0","s1",...
Writes: DAYDIR/work/voice_clean.wav (EQ + compressor, silences between sentences shortened) and DAYDIR/work/timing.json
        (every word with s2/e2 = time after trimming, every segment with s2/e2, last_word_end).
Prints the indexed words so you can wire scenes to word times.
"""
import glob
import json
import os
import re
import subprocess
import sys

import numpy as np
from scipy.io import wavfile

D = sys.argv[1].rstrip("/")
SR = 48000
os.makedirs(f"{D}/work", exist_ok=True)
src = [p for p in glob.glob(f"{D}/in/voice.*")][0]
W = json.load(open(f"{D}/in/words.json"))
words = [{"t": w[0], "s": w[1] / 1000, "e": w[2] / 1000} for w in W]

if os.path.exists(f"{D}/in/segments.json"):
    SEG = json.load(open(f"{D}/in/segments.json"))
else:
    SEG, a = [], 0
    for i, w in enumerate(words):
        if re.search(r"[.?!…]['\"’”)]*$", w["t"]) or i == len(words) - 1:
            SEG.append([f"s{len(SEG)}", a, i])
            a = i + 1
segs = [{"name": n, "a": a, "b": b, "s": words[a]["s"], "e": words[b]["e"]} for n, a, b in SEG]

subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-ar", str(SR), "-ac", "1", "-c:a", "pcm_f32le", f"{D}/work/voice_48k.wav"], check=True)
x = wavfile.read(f"{D}/work/voice_48k.wav")[1].astype(np.float32)

# voice activity: silent intervals >= 0.22 s (38 dB below the loudest 10 ms)
hop = int(0.01 * SR)
n = len(x) // hop
rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1))
db = 20 * np.log10(rms + 1e-9)
sil = db < (db.max() - 38)
ints, i = [], 0
while i < n:
    if sil[i]:
        j = i
        while j < n and sil[j]:
            j += 1
        if (j - i) * 0.01 >= 0.22:
            ints.append((i * 0.01, j * 0.01))
        i = j
    else:
        i += 1

# one cut per gap between segments: remove the middle of the silence, keep 0.20-0.42 s
cuts = []
for k in range(len(segs) - 1):
    g0, g1 = segs[k]["e"], segs[k + 1]["s"]
    best = None
    for a, b in ints:
        if b > g0 - 0.05 and a < g1 + 0.05:
            ov = min(b, g1 + 0.05) - max(a, g0 - 0.05)
            if best is None or ov > best[2]:
                best = (a, b, ov)
    if best is None:
        continue
    a, b, _ = best
    keep = float(np.clip((b - a) * 0.55, 0.20, 0.42))
    if b - a <= keep + 0.06:
        continue
    cuts.append((a + keep / 2, b - keep / 2))

fade = int(0.012 * SR)
pieces, pos = [], 0.0
for a, b in cuts:
    pieces.append((pos, a))
    pos = b
pieces.append((pos, len(x) / SR))
out = []
for idx, (s, e) in enumerate(pieces):
    p = x[int(s * SR): int(e * SR)].copy()
    if idx > 0:
        p[:fade] *= np.linspace(0, 1, fade)
    if idx < len(pieces) - 1:
        p[-fade:] *= np.linspace(1, 0, fade)
    out.append(p)
voice = np.concatenate(out)
wavfile.write(f"{D}/work/voice_cut.wav", SR, voice)


def remap(t):
    shift = 0.0
    for a, b in cuts:
        if t >= b:
            shift += b - a
        elif t > a:
            return a - shift
    return t - shift


for w in words:
    w["s2"], w["e2"] = round(remap(w["s"]), 3), round(remap(w["e"]), 3)
for s in segs:
    s["s2"], s["e2"] = round(remap(s["s"]), 3), round(remap(s["e"]), 3)

subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{D}/work/voice_cut.wav", "-af",
                "highpass=f=75,equalizer=f=250:t=q:w=1.2:g=-1.0,equalizer=f=3200:t=q:w=1.0:g=1.5,"
                "acompressor=threshold=0.08:ratio=2.5:attack=8:release=160:makeup=1.3,alimiter=limit=0.9",
                "-c:a", "pcm_f32le", f"{D}/work/voice_clean.wav"], check=True)

json.dump({"words": words, "segs": segs, "voice_dur": round(len(voice) / SR, 3), "last_word_end": segs[-1]["e2"]},
          open(f"{D}/work/timing.json", "w"), indent=1)
print(f"voice {len(x) / SR:.2f}s -> {len(voice) / SR:.2f}s, last word ends {segs[-1]['e2']}s, {len(cuts)} gaps shortened")
print("segments:", [(s["name"], s["a"], s["b"], s["s2"], s["e2"]) for s in segs])
print("words:", " ".join(f"{i}:{w['t']}@{w['s2']}" for i, w in enumerate(words)))
