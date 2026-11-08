"""Original synthesised background bed (no samples, no third-party audio -> no licence issues).

Usage: python3 music.py DAYDIR --style pluck|arp|keys --bpm 96 --prog "C G Am F" --seed 11 [--drums 1]
Reads DAYDIR/work/timing.json + voice_clean.wav; writes DAYDIR/work/music.wav and voice_st.wav (stereo voice padded to length).
Vary style / bpm / progression / seed from video to video so every Reel sounds different.
  pluck : soft pad + 8th-note plucks + kick/hats (the Day-1 sound)          bpm 90-110
  arp   : brighter 16th-note arpeggio, light kick on 1 and 3, no hats        bpm 100-120
  keys  : calm piano-like chords + bass, no drums, lots of reverb            bpm 70-90
Chords: names like C G Am F Dm Em Bb F#m (major / minor triads).
"""
import argparse
import json

import numpy as np
from scipy import signal
from scipy.io import wavfile

ap = argparse.ArgumentParser()
ap.add_argument("daydir")
ap.add_argument("--style", default="pluck")
ap.add_argument("--bpm", type=float, default=96)
ap.add_argument("--prog", default="C G Am F")
ap.add_argument("--seed", type=int, default=11)
ap.add_argument("--drums", type=int, default=1)
A = ap.parse_args()
D, SR = A.daydir.rstrip("/"), 48000
TIM = json.load(open(f"{D}/work/timing.json"))
T = TIM["last_word_end"] + 0.55 + 2.3
N = int(T * SR)
rng = np.random.default_rng(A.seed)
beat = 60 / A.bpm
bar = 4 * beat
eighth, sixteenth = beat / 2, beat / 4
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def mf(m): return 440.0 * 2 ** ((m - 69) / 12)


def chords(names):
    out, prev = [], None
    for nm in names:
        minor = nm.endswith("m")
        r = NOTE[nm[:-1] if minor else nm]
        pcs = [r, r + (3 if minor else 4), r + 7]
        best = None
        for inv in range(3):
            base = pcs[inv:] + [p + 12 for p in pcs[:inv]]
            for octv in (48, 60):
                notes = [octv + (p - r) + r for p in base]
                notes = [n if n >= octv else n + 12 for n in notes]
                notes = sorted(notes)
                mean = np.mean(notes)
                cost = abs(mean - 63) if prev is None else sum(abs(a - b) for a, b in zip(notes, prev)) + 0.2 * abs(mean - 63)
                if 57 <= min(notes) and max(notes) <= 74 and (best is None or cost < best[0]):
                    best = (cost, notes)
        notes = best[1] if best else [60 + r, 64 + r, 67 + r]
        prev = notes
        bm = 36 + r
        bm = bm - 12 if bm > 42 else bm
        out.append((mf(bm), [mf(n) for n in notes]))
    return out


PROG = chords(A.prog.split())
pad, pl = np.zeros((2, N)), np.zeros((2, N))
bass, kick, hats = np.zeros(N), np.zeros(N), np.zeros(N)


def env_ar(n, a, r):
    e = np.ones(n)
    na, nr = min(n // 2, int(a * SR)), min(n // 2, int(r * SR))
    e[:na] = np.linspace(0, 1, na) ** 2
    e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def tone(f, dur, decay, nh=6, rolloff=1.25):
    m = int(dur * SR)
    tq = np.arange(m) / SR
    s = np.zeros(m)
    for h in range(1, nh + 1):
        s += (1 / h ** rolloff) * np.sin(2 * np.pi * f * h * tq + h) * np.exp(-tq / (decay / h ** 0.5))
    s *= np.minimum(1, tq / 0.003)
    return s / np.max(np.abs(s))


def add_st(arr, tp, sig, g, pan):
    ip = int(tp * SR)
    if ip < 0 or ip >= N:
        return
    m = min(len(sig), N - ip)
    arr[0, ip:ip + m] += sig[:m] * g * (1 - pan)
    arr[1, ip:ip + m] += sig[:m] * g * pan


def add_kick(tk, g):
    ik = int(tk * SR)
    m = min(int(0.22 * SR), N - ik)
    if m > 0:
        tq = np.arange(m) / SR
        ph = 2 * np.pi * np.cumsum(48 + 110 * np.exp(-tq / 0.028)) / SR
        kick[ik:ik + m] += np.sin(ph) * np.exp(-tq / 0.085) * g


for k in range(int(np.ceil(T / bar)) + 1):
    root, tones = PROG[k % len(PROG)]
    t0 = k * bar
    # pad (swells across each bar)
    i0, i1 = max(0, int((t0 - 0.35) * SR)), min(N, int((t0 + bar + 0.7) * SR))
    if i1 > i0:
        tt = np.arange(i1 - i0) / SR
        e = env_ar(i1 - i0, 0.5, 0.7)
        for ch, det in enumerate((0.0012, -0.0016)):
            s = np.zeros(i1 - i0)
            for f in tones:
                for h, amp in ((1, 1.0), (2, 0.35), (3, 0.12)):
                    s += amp * np.sin(2 * np.pi * f * h * (1 + det) * tt + rng.uniform(0, 6.28))
            pad[ch, i0:i1] += s * e
    # bass on beats 1 and 3
    for j in (0, 2):
        ib = int((t0 + j * beat) * SR)
        m = min(int(1.4 * SR), N - ib)
        if m > 0:
            tq = np.arange(m) / SR
            bass[ib:ib + m] += np.sin(2 * np.pi * root * tq) * np.exp(-tq / 0.9) * (1.0 if j == 0 else 0.7)
    if A.style == "pluck":
        for j, idx in enumerate([0, 1, 2, 1, 0, 1, 2, 1]):
            tp = t0 + j * eighth + rng.uniform(-0.006, 0.006)
            if 0.6 <= tp <= T - 1.0:
                add_st(pl, tp, tone(tones[idx] * 2, 0.9, 0.30), (0.8 if j % 4 == 0 else 0.55) * rng.uniform(0.9, 1.05), 0.35 + 0.3 * (j % 2))
        if A.drums:
            for j in range(4):
                if not (k < 2 and j % 2) and 0.5 <= t0 + j * beat <= T - 1.6:
                    add_kick(t0 + j * beat, 0.85 if j % 2 == 0 else 0.5)
            for j in (1, 3, 5, 7):
                th = t0 + j * eighth
                if 1.0 <= th <= T - 1.6:
                    ih = int(th * SR)
                    m = min(int(0.05 * SR), N - ih)
                    if m > 0:
                        hats[ih:ih + m] += rng.standard_normal(m) * np.exp(-np.arange(m) / SR / 0.012)
    elif A.style == "arp":
        order = [0, 1, 2, 3, 2, 1, 0, 1]
        notes = tones + [tones[0] * 2]
        for j in range(16):
            tp = t0 + j * sixteenth + rng.uniform(-0.004, 0.004)
            if 0.6 <= tp <= T - 1.0:
                add_st(pl, tp, tone(notes[order[j % 8]] * 2, 0.55, 0.16, nh=5, rolloff=1.6), (0.85 if j % 4 == 0 else 0.5) * rng.uniform(0.9, 1.05), 0.3 + 0.4 * ((j % 4) / 3))
        if A.drums:
            for j in (0, 2):
                if 0.5 <= t0 + j * beat <= T - 1.6:
                    add_kick(t0 + j * beat, 0.7)
    elif A.style == "keys":
        for j in (0, 2):
            for q, f in enumerate(tones):
                tp = t0 + j * beat + q * 0.022
                if 0.4 <= tp <= T - 1.2:
                    add_st(pl, tp, tone(f, 2.4, 0.9, nh=7, rolloff=1.5), 0.6 if j == 0 else 0.42, 0.3 + 0.2 * q)
        for j, idx in ((1.5, 2), (3.0, 1)):
            tp = t0 + j * beat + rng.uniform(-0.01, 0.01)
            if 0.8 <= tp <= T - 1.2:
                add_st(pl, tp, tone(tones[idx] * 2, 1.2, 0.5), 0.35, 0.6)

lp = signal.butter(2, 2000 / (SR / 2))
pad = np.stack([signal.lfilter(*lp, p) for p in pad])
for arr in (pad, pl):
    arr /= max(1e-9, np.max(np.abs(arr)))
for arr in (bass, kick):
    arr /= max(1e-9, np.max(np.abs(arr)))
hats = signal.lfilter(*signal.butter(2, 6500 / (SR / 2), "high"), hats)
hats /= max(1e-9, np.max(np.abs(hats)))

irn = int(1.7 * SR)
ti = np.arange(irn) / SR
irs = []
for c in range(2):
    ir = np.random.default_rng(70 + c).standard_normal(irn) * np.exp(-ti / (0.8 if A.style == "keys" else 0.45))
    ir = signal.lfilter(*signal.butter(2, 5000 / (SR / 2)), ir)
    irs.append(ir / np.sqrt(np.sum(ir ** 2)))
padg, plg = {"pluck": (0.30, 0.34), "arp": (0.22, 0.36), "keys": (0.26, 0.40)}[A.style]
dry = [padg * pad[c] + plg * pl[c] for c in range(2)]
wet = [signal.fftconvolve(dry[c], irs[c], mode="full")[:N] for c in range(2)]
out = np.zeros((2, N))
for c in range(2):
    out[c] = dry[c] + (0.40 if A.style == "keys" else 0.28) * wet[c] + 0.26 * bass + 0.24 * kick + 0.05 * hats
out /= np.max(np.abs(out))
out *= 0.85
fi, fo = int(0.5 * SR), int(1.8 * SR)
out[:, :fi] *= np.linspace(0, 1, fi)
out[:, -fo:] *= np.linspace(1, 0, fo) ** 1.5
wavfile.write(f"{D}/work/music.wav", SR, out.T.astype(np.float32))

voice = wavfile.read(f"{D}/work/voice_clean.wav")[1].astype(np.float32)
st = np.zeros((N, 2), dtype=np.float32)
n = min(len(voice), N)
st[:n, 0] = st[:n, 1] = voice[:n]
wavfile.write(f"{D}/work/voice_st.wav", SR, st)
print(f"music ready: style={A.style} bpm={A.bpm} prog={A.prog} seed={A.seed} T={T:.2f}s")
