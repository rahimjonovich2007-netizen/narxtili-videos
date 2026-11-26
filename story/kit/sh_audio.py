"""Multi-voice dialogue assembler for Sirli Hikoyalar.

Usage: python3 sh_audio.py EPDIR
Needs EPDIR/in/lines.json   [{"n","spk","text","file"}, ...]  (one TTS wav per line, any rate)
      EPDIR/in/plan.json    {"speakers": {"jasur": {"pitch": 2.0}}, "lines": {"01": {"tempo": 1.15, "pre": 0.0, "gain": 1.0, "pitch": 0, "af": "aecho=..."}, ...}, "default": {"tempo": 1.08, "pre": 0.28}}
Writes EPDIR/work/voice_clean.wav       mono 48 kHz, all voices mixed (feeds music.py / mix.py)
       EPDIR/work/spk_<speaker>.wav     per-speaker track (drives lip-sync)
       EPDIR/work/timing.json           nt_kit.Timing compatible: words (s2/e2), segs (one per line, name "L01"...), last_word_end,
                                        plus "lines": [{n, spk, text, s2, e2}]
Each line: leading/trailing silence trimmed, long internal pauses squeezed, tempo changed with ffmpeg atempo (pitch kept).
Word times inside a line are proportional to letter counts over the voiced span (good enough for karaoke captions).
"""
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
LINES = json.load(open(f"{D}/in/lines.json"))
PLAN = json.load(open(f"{D}/in/plan.json"))
DEF = PLAN.get("default", {"tempo": 1.08, "pre": 0.28})


def load(path):
    tmp = f"{D}/work/_tmp.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", path, "-ar", str(SR), "-ac", "1", "-c:a", "pcm_f32le", tmp], check=True)
    return wavfile.read(tmp)[1].astype(np.float32)


def tidy(x, keep_head=0.03, keep_tail=0.10, max_pause=0.30):
    hop = int(0.01 * SR)
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1))
    db = 20 * np.log10(rms + 1e-9)
    act = db > db.max() - 36
    idx = np.where(act)[0]
    a, b = max(0, idx[0] - int(keep_head / 0.01)), min(n, idx[-1] + 1 + int(keep_tail / 0.01))
    # squeeze internal silences longer than 0.45 s down to max_pause
    out, i = [], a
    while i < b:
        if not act[i]:
            j = i
            while j < b and not act[j]:
                j += 1
            run = j - i
            if run * 0.01 > 0.45:
                run = int(max_pause / 0.01)
            out.append(np.zeros(run * hop, np.float32))
            i = j
        else:
            j = i
            while j < b and act[j]:
                j += 1
            out.append(x[i * hop: j * hop])
            i = j
    return np.concatenate(out)


def tempo(x, f, semis=0.0, extra=""):
    """tempo f and pitch (semitones, formants follow the pitch) with rubberband; `extra` = further ffmpeg filters (echo etc.)"""
    if abs(f - 1.0) < 0.01 and abs(semis) < 0.05 and not extra:
        return x
    src, dst = f"{D}/work/_t_in.wav", f"{D}/work/_t_out.wav"
    wavfile.write(src, SR, x)
    chain = []
    if abs(f - 1.0) >= 0.01 or abs(semis) >= 0.05:
        chain.append(f"rubberband=tempo={f}:pitch={2 ** (semis / 12):.5f}:pitchq=quality")
    if extra:
        chain.append(extra)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", ",".join(chain), "-c:a", "pcm_f32le", dst], check=True)
    return wavfile.read(dst)[1].astype(np.float32)


tracks, lines_out, words_out, segs_out = {}, [], [], []
t = 0.0
fade = int(0.008 * SR)
for L in LINES:
    cfg = dict(DEF)
    cfg.update(PLAN.get("speakers", {}).get(L["spk"], {}))
    cfg.update(PLAN.get("lines", {}).get(L["n"], {}))
    t += cfg.get("pre", 0.0)
    x = tidy(load(f"{D}/{L['file']}" if not L["file"].startswith("/") else L["file"]))
    x = tempo(x, cfg.get("tempo", 1.0), cfg.get("pitch", 0.0), cfg.get("af", "")) * cfg.get("gain", 1.0)
    x[:fade] *= np.linspace(0, 1, fade)
    x[-fade:] *= np.linspace(1, 0, fade)
    s0 = t
    e0 = t + len(x) / SR
    tr = tracks.setdefault(L["spk"], [])
    tr.append((int(s0 * SR), x))
    toks = L["text"].replace("...", "…").split()
    wts = [max(2, len(re.sub(r"\W", "", w))) + (4 if re.search(r"[.?!…,:]$", w) else 0) for w in toks]
    tot = sum(wts)
    a = len(words_out)
    cur = s0
    span = e0 - s0
    for w, wt in zip(toks, wts):
        dur = span * wt / tot
        words_out.append({"t": w, "s": round(cur, 3), "e": round(cur + dur * 0.94, 3), "s2": round(cur, 3), "e2": round(cur + dur * 0.94, 3),
                          "spk": L["spk"], "line": L["n"]})
        cur += dur
    segs_out.append({"name": "L" + L["n"], "a": a, "b": len(words_out) - 1, "s": round(s0, 3), "e": round(e0, 3), "s2": round(s0, 3), "e2": round(e0, 3),
                     "spk": L["spk"]})
    lines_out.append({"n": L["n"], "spk": L["spk"], "text": L["text"], "s2": round(s0, 3), "e2": round(e0, 3)})
    t = e0 + cfg.get("post", 0.0)
    t += 0.0

total = max(l["e2"] for l in lines_out) + 0.5
N = int(total * SR)
mix = np.zeros(N, np.float32)
for spk, parts in tracks.items():
    tr = np.zeros(N, np.float32)
    for off, x in parts:
        tr[off: off + len(x)] += x[: N - off]
    wavfile.write(f"{D}/work/spk_{spk}.wav", SR, tr)
    mix += tr
# gentle EQ + compression on the mixed voice
wavfile.write(f"{D}/work/voice_raw.wav", SR, mix)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{D}/work/voice_raw.wav", "-af",
                "highpass=f=75,equalizer=f=250:t=q:w=1.2:g=-1.0,equalizer=f=3200:t=q:w=1.0:g=1.5,"
                "acompressor=threshold=0.08:ratio=2.5:attack=8:release=160:makeup=1.3,alimiter=limit=0.9",
                "-c:a", "pcm_f32le", f"{D}/work/voice_clean.wav"], check=True)
json.dump({"words": words_out, "segs": segs_out, "lines": lines_out, "voice_dur": round(total, 3), "last_word_end": lines_out[-1]["e2"]},
          open(f"{D}/work/timing.json", "w"), indent=1, ensure_ascii=False)
print(f"dialogue {lines_out[-1]['e2']:.2f}s")
for l in lines_out:
    print(f"L{l['n']} {l['spk']:9s} {l['s2']:6.2f} - {l['e2']:6.2f}  {l['text']}")
