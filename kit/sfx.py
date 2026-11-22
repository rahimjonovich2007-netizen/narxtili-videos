"""Sound design: synthesised sound effects (no samples -> no licence issues), aligned to the picture.

Usage: python3 sfx.py DAYDIR
DAYDIR/scenes.py must define   sfx(tim) -> [(t_seconds, "kind", gain), ...]   (gain 0..1, default levels are already mixed to sit under the voice)
Kinds:  whoosh  whoosh_dn  impact  thump  tick  riser:<seconds>  ding  coin  stamp  pop  clank  sparkle  glitch
A `riser:2.0` at time t ENDS at t+2.0 (put the impact/ding exactly there; leave a beat of silence before it for drama).
Writes DAYDIR/work/sfx.wav (stereo, 48 kHz); mix.py adds it after the voice/music ducking (SFX are not ducked).
"""
import importlib.util
import json
import os
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
RNG = np.random.default_rng(7)


def env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))
    return e


def sweep_noise(dur, f0, f1, q=4.0, curve=1.0):
    n = int(dur * SR)
    x = RNG.normal(0, 1, n)
    out = np.zeros(n)
    blk, zi = 512, None
    for i in range(0, n, blk):
        p = (i / n) ** curve
        f = f0 * (f1 / f0) ** p
        b, a = signal.iirpeak(min(0.95, f / (SR / 2)), q)
        if zi is None:
            zi = signal.lfilter_zi(b, a) * 0
        y, zi = signal.lfilter(b, a, x[i:i + blk], zi=zi)
        out[i:i + blk] = y
    return out / (np.abs(out).max() + 1e-9)


def sine_glide(dur, f0, f1, curve=2.0):
    n = int(dur * SR)
    p = (np.arange(n) / n) ** curve
    f = f0 + (f1 - f0) * p
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def lp(x, fc):
    b, a = signal.butter(2, fc / (SR / 2))
    return signal.lfilter(b, a, x)


def hp(x, fc):
    b, a = signal.butter(2, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def make(kind):
    k, _, arg = kind.partition(":")
    if k == "whoosh":
        d = 0.55
        x = sweep_noise(d, 400, 4200, 2.2, 1.4)
        n = len(x)
        t = np.arange(n) / n
        return x * np.sin(np.pi * t) ** 1.6 * 0.9
    if k == "whoosh_dn":
        d = 0.6
        x = sweep_noise(d, 4200, 300, 2.2, 1.2)
        n = len(x)
        t = np.arange(n) / n
        return x * np.sin(np.pi * t) ** 1.4 * 0.9
    if k == "impact":
        n = int(1.1 * SR)
        s = sine_glide(1.1, 140, 38, 0.35) * env(n, 0.002, 0.28)
        nz = lp(RNG.normal(0, 1, n), 900) * env(n, 0.001, 0.07)
        return 1.0 * s + 0.7 * nz
    if k == "thump":
        n = int(0.5 * SR)
        s = sine_glide(0.5, 90, 45, 0.3) * env(n, 0.003, 0.12)
        s2 = np.concatenate([np.zeros(int(0.17 * SR)), s[:n - int(0.17 * SR)] * 0.7])
        return s + s2
    if k == "tick":
        n = int(0.06 * SR)
        t = np.arange(n) / SR
        return (np.sin(2 * np.pi * 2300 * t) + 0.5 * np.sin(2 * np.pi * 4600 * t)) * env(n, 0.0005, 0.012) * 0.7
    if k == "riser":
        d = float(arg or 1.6)
        x = sweep_noise(d, 250, 6500, 2.5, 1.7)
        n = len(x)
        t = np.arange(n) / n
        g = sine_glide(d, 180, 1400, 2.2) * 0.35
        return (x * 0.8 + g) * (t ** 2.2)
    if k == "ding":
        n = int(1.6 * SR)
        t = np.arange(n) / SR
        f = 1318.5
        x = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t / dd) for m, a, dd in ((1, 1.0, 0.7), (2.76, 0.4, 0.35), (5.4, 0.2, 0.18), (8.9, 0.1, 0.1)))
        return x * np.minimum(1, t / 0.002) * 0.7
    if k == "coin":
        n = int(0.45 * SR)
        t = np.arange(n) / SR
        x = np.sin(2 * np.pi * 2930 * t) * np.exp(-t / 0.09) + 0.8 * np.sin(2 * np.pi * 3950 * (t - 0.06).clip(0)) * np.exp(-(t - 0.06).clip(0) / 0.14) * (t > 0.06)
        return x * 0.55
    if k == "stamp":
        n = int(0.5 * SR)
        s = sine_glide(0.5, 200, 60, 0.4) * env(n, 0.001, 0.09)
        nz = hp(lp(RNG.normal(0, 1, n), 5000), 400) * env(n, 0.0005, 0.03)
        return s + 0.8 * nz
    if k == "pop":
        n = int(0.14 * SR)
        return sine_glide(0.14, 380, 980, 0.6) * env(n, 0.002, 0.05) * 0.8
    if k == "clank":
        n = int(0.9 * SR)
        t = np.arange(n) / SR
        x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, a, d in ((182, 1, 0.35), (343, .7, 0.25), (521, .5, 0.2), (887, .3, 0.12)))
        nz = hp(RNG.normal(0, 1, n), 1500) * env(n, 0.0005, 0.02)
        return x * 0.6 + nz * 0.5
    if k == "sparkle":
        n = int(0.9 * SR)
        x = np.zeros(n)
        for i in range(9):
            f = RNG.uniform(2800, 7200)
            st = int(i * 0.06 * SR)
            m = int(0.18 * SR)
            t = np.arange(m) / SR
            x[st:st + m] += np.sin(2 * np.pi * f * t) * np.exp(-t / 0.05)[:n - st]
        return x * 0.22
    if k == "glitch":
        n = int(0.22 * SR)
        x = np.sign(RNG.normal(0, 1, n)) * (RNG.random(n) > 0.6)
        return hp(x, 800) * env(n, 0.001, 0.09) * 0.5
    raise ValueError(kind)


def render(events, total):
    N = int((total + 1.0) * SR)
    L, R = np.zeros(N), np.zeros(N)
    for t, kind, gain in events:
        x = make(kind) * gain
        x = np.tanh(x * 1.4) / 1.4
        pan = RNG.uniform(-0.25, 0.25)
        k, _, arg = kind.partition(":")
        t0 = t - (float(arg or 1.6) if k == "riser" else 0.0)       # riser ends at t (timestamp = its target moment)
        i = int(max(0, t0) * SR)
        m = min(len(x), N - i)
        if m <= 0:
            continue
        L[i:i + m] += x[:m] * (1 - pan) * 0.5 * 2
        R[i:i + m] += x[:m] * (1 + pan) * 0.5 * 2
    out = np.stack([L, R], 1)
    pk = np.abs(out).max()
    if pk > 0.95:
        out = out * (0.95 / pk)
    return out[:int(total * SR)]


if __name__ == "__main__":
    D = sys.argv[1].rstrip("/")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, D)
    import nt_kit as K
    spec = importlib.util.spec_from_file_location("scenes", f"{D}/scenes.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    tim = K.Timing(f"{D}/work/timing.json")
    ev = sorted(mod.sfx(tim), key=lambda e: e[0])
    out = render(ev, tim.total)
    wavfile.write(f"{D}/work/sfx.wav", SR, (out * 32767).astype(np.int16))
    print("sfx ->", f"{D}/work/sfx.wav", len(ev), "events")
