"""Synthesise every sound in THE LAST LIGHT (host Python + numpy; no downloads, fully owned).

  tools/py projects/games/last_light/audio/synth.py [--out DIR]

Writes 16-bit mono WAV (44.1 kHz) to godot/assets/audio/. Loops are crossfaded end-into-start so
they repeat seamlessly; every file is peak-normalised to <= -1 dBFS. Prints SYNTH_RESULT {json}.

Each sound draws its noise from its own generator, seeded from the sound's name (crc32 ^ 1953), so
adding or lengthening one sound never changes another.

G5 / finding 30 (2026-11-06):
- every constant loop is at least 20 s long;
- the rain is 48 s, and a separate window-glass patter layer (`amb_rain_glass`, 37 s) is placed at
  the windows;
- the wind is split into a steady bed and a gust layer (`amb_gust`), whose envelope is driven at
  runtime by the storm value;
- 6 seeded thunder variants: 0–2 are near (a crack, 5–6 s), 3–5 are far (no crack, darker,
  8–10 s rolling rumble);
- `carrier_click` (radio carrier key-up) was referenced by chapters.json but never made.

Phase-exact loops: a pure tone crossfades cleanly only if it completes whole cycles over
(length - crossfade). The hum, generator, clockwork and motor lengths are chosen for that.
"""

import argparse
import json
import wave
import zlib
from pathlib import Path

import numpy as np

SR = 44100
OUT = Path(__file__).resolve().parents[1] / "godot" / "assets" / "audio"
rng = np.random.default_rng(1953)
MIN_LOOP_S = 20.0          # finding 30: no constant layer may repeat faster than this


def seed_for(name: str) -> None:
    """Point the module generator at this sound's own stream."""
    global rng
    rng = np.random.default_rng(zlib.crc32(name.encode()) ^ 1953)


def t(sec):
    return np.arange(int(round(sec * SR))) / SR


def noise(sec):
    return rng.standard_normal(int(round(sec * SR)))


def band(x, lo=None, hi=None, slope=1.0):
    """FFT band filter with soft edges (lo/hi in Hz)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if lo:
        g *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** (2 * slope))
    if hi:
        g *= 1 / (1 + (f / hi) ** (2 * slope))
    return np.fft.irfft(X * g, n=len(x))


def env(n, a=0.01, d=0.3, curve=3.0):
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    tail = np.arange(n - na) / SR
    e[na:] = np.exp(-tail / max(d, 1e-4) * curve / 3.0)
    return e


def lfo(sec, rate, depth, phase=0.0):
    return 1 + depth * np.sin(2 * np.pi * rate * t(sec) + phase)


def smooth_rand(sec, rate, seed):
    r = np.random.default_rng(seed)
    k = max(2, int(sec * rate) + 2)
    pts = r.uniform(0, 1, k)
    x = np.linspace(0, k - 1, int(round(sec * SR)))
    return np.interp(x, np.arange(k), pts)


def loopify(x, xf=1.5):
    n = int(xf * SR)
    head, tail = x[:n], x[-n:]
    w = np.linspace(0, 1, n)
    x = x[:-n].copy()
    x[:n] = tail * (1 - w) + head * w
    return x


def norm(x, peak_db=-1.0):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * (10 ** (peak_db / 20))


def dc_free(x):
    """Remove DC without moving the endpoints: subtract the mean shaped by a Hann window."""
    if len(x) < 64:
        return x
    w = np.hanning(len(x))
    return x - (x.mean() / w.mean()) * w


def save(name, x, peak_db=-1.0, loop=False):
    OUT.mkdir(parents=True, exist_ok=True)
    x = np.nan_to_num(x)
    if not loop:
        x = dc_free(x)
    x = norm(x, peak_db)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    RESULT[name] = round(len(x) / SR, 2)


RESULT = {}


def drops(sec, count, f_lo, f_hi, a_lo, a_hi, d_lo=0.002, d_hi=0.006):
    """Short decaying sine pings: raindrops on glass or metal."""
    x = np.zeros(int(sec * SR))
    for i in rng.integers(0, len(x) - 3000, count):
        L = int(rng.integers(200, 1400))
        f = rng.uniform(f_lo, f_hi)
        x[i:i + L] += rng.uniform(a_lo, a_hi) * np.sin(2 * np.pi * f * t(L / SR)) * env(L, 0.0004, rng.uniform(d_lo, d_hi))
    return x


# ------------------------------------------------------------------ ambience loops

def wind():
    """The steady bed. Gusts are a separate layer (amb_gust) shaped at runtime by the storm."""
    sec = 42.5
    base = band(noise(sec), 70, 850)
    swell = smooth_rand(sec, 0.09, 2)
    moan = band(noise(sec), 220, 380, 2.5) * smooth_rand(sec, 0.15, 3) ** 2
    x = base * (0.55 + 0.35 * swell) + moan * 0.5
    save("amb_wind", loopify(x), -4, loop=True)


def gust():
    """Gust layer: brighter, with two drifting whistles round the gallery rails. Kept fairly steady
    on purpose, because audio_director gives it its gust envelope (two envelopes would double up)."""
    sec = 34.5
    air = band(noise(sec), 250, 1600)
    w1 = band(noise(sec), 560, 640, 3.0) * smooth_rand(sec, 0.3, 21)
    w2 = band(noise(sec), 880, 960, 3.0) * smooth_rand(sec, 0.25, 22) ** 2
    x = air * (0.7 + 0.3 * smooth_rand(sec, 0.6, 23)) + w1 * 0.9 + w2 * 0.6
    save("amb_gust", loopify(x), -4, loop=True)


def rain():
    """Rain on the lantern roof and the gallery: hiss, light drops and a dull drumming on metal."""
    sec = 49.5
    hiss = band(noise(sec), 1500, 9000) * 0.35 * (0.85 + 0.15 * smooth_rand(sec, 0.2, 31))
    light = band(drops(sec, 8000, 2500, 6000, 0.2, 1.0), 1200, 12000) * 0.8
    roof = band(drops(sec, 2600, 300, 900, 0.2, 0.7, 0.008, 0.02), 200, 2500) * 0.35
    save("amb_rain", loopify(hiss + light + roof), -6, loop=True)


def rain_glass():
    """Close patter on the window glass, plus the odd running trickle. 37 s, so it never lines up
    with the 48 s roof rain."""
    sec = 38.5
    patter = band(drops(sec, 5200, 3000, 8000, 0.3, 1.0, 0.0015, 0.004), 2000, 14000)
    trickle = np.zeros(int(sec * SR))
    for i in rng.integers(0, len(trickle) - 3 * SR, 14):
        L = int(rng.uniform(0.8, 2.4) * SR)
        tt = t(L / SR)
        f = 1800 + 900 * np.sin(2 * np.pi * rng.uniform(3, 7) * tt) * np.exp(-tt)
        tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * band(noise(L / SR), 1500, 4000) * 0.15
        trickle[i:i + L] += tone * np.sin(np.pi * tt / tt[-1]) ** 2
    hiss = band(noise(sec), 4000, 11000) * 0.12
    save("amb_rain_glass", loopify(patter + trickle + hiss), -8, loop=True)


def sea():
    sec = 30
    swell = smooth_rand(sec, 0.12, 5)
    surf = band(noise(sec), 60, 1200) * (0.2 + swell ** 1.5)
    boom = band(noise(sec), 30, 140) * (smooth_rand(sec, 0.08, 6) ** 3)
    save("amb_sea", loopify(surf + boom * 1.5), -5, loop=True)


def generator():
    """Single-cylinder diesel at 25 Hz firing. 20.5 s - 0.5 s crossfade = 20 s = 500 whole cycles."""
    sec, xf = 20.5, 0.5
    tt = t(sec)
    f0 = 25.0
    x = sum((1 / k) * np.sin(2 * np.pi * f0 * k * tt + k) for k in range(1, 9))
    load = 0.85 + 0.15 * smooth_rand(sec, 0.4, 41)            # governor hunting: level, not speed
    knock = np.zeros_like(tt)
    for i in range(int(sec * f0 / 2)):
        p = int(i * SR / (f0 / 2))
        L = 700
        if p + L < len(knock):
            knock[p:p + L] += env(L, 0.001, 0.01) * band(noise(L / SR), 200, 2000) * rng.uniform(0.75, 1.0)
    save("gen_idle", loopify(x * 0.6 * load + knock * 0.5 + band(noise(sec), 100, 400) * 0.15, xf), -6, loop=True)


def hum():
    """50 Hz mains hum. 23 s - 0.5 s = 22.5 s = 1125 cycles, so the crossfade is in phase."""
    sec, xf = 23.0, 0.5
    tt = t(sec)
    w1 = 0.9 + 0.1 * smooth_rand(sec, 0.15, 51)
    w3 = 0.6 + 0.4 * smooth_rand(sec, 0.1, 52)
    x = np.sin(2 * np.pi * 50 * tt) * w1 + 0.5 * np.sin(2 * np.pi * 100 * tt) + 0.25 * np.sin(2 * np.pi * 150 * tt) * w3
    x += band(noise(sec), 2000, 5000) * 0.03 * (0.7 + 0.6 * smooth_rand(sec, 0.3, 53))
    save("hum", loopify(x, xf), -12, loop=True)


def clockwork():
    """Optic drive escapement, 4 ticks/s. 20.3 s - 0.3 s = 20 s = 80 ticks."""
    sec, xf = 20.3, 0.3
    x = np.zeros(int(sec * SR))
    for i in range(int(sec * 4)):
        p = int(i * SR / 4) + int(rng.integers(0, 200))
        L = 1500
        if p + L < len(x):
            x[p:p + L] += env(L, 0.0005, 0.006) * band(noise(L / SR), 1800, 7000) * (1.0 if i % 2 else 0.6) * rng.uniform(0.8, 1.0)
    x += band(noise(sec), 60, 200) * 0.08
    save("clockwork", loopify(x, xf), -8, loop=True)


def static_loop():
    """Radio static with crackle and the occasional heterodyne whistle drifting across."""
    sec, xf = 21.3, 0.3
    x = band(noise(sec), 400, 6000) * (0.6 + 0.4 * smooth_rand(sec, 6, 9))
    crackle = np.zeros(int(sec * SR))
    for i in rng.integers(0, len(crackle) - 300, 900):
        crackle[i:i + 120] += rng.uniform(-1, 1) * env(120, 0.0001, 0.001)
    whistle = np.zeros(int(sec * SR))
    for i in rng.integers(int(0.5 * SR), len(whistle) - 4 * SR, 4):
        L = int(rng.uniform(1.5, 3.5) * SR)
        tt = t(L / SR)
        f = np.linspace(rng.uniform(600, 1400), rng.uniform(1600, 3000), L)
        whistle[i:i + L] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / tt[-1]) ** 2 * 0.05
    save("static", loopify(x + crackle * 2.0 + whistle, xf), -9, loop=True)


def motor_grind():
    """Jammed optic motor. 20.2 s - 0.2 s = 20 s: 7 Hz -> 140 cycles, 61 Hz -> 1220."""
    sec, xf = 20.2, 0.2
    tt = t(sec)
    x = band(noise(sec), 200, 1800) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 7 * tt)))
    x += 0.4 * np.sign(np.sin(2 * np.pi * 61 * tt)) * band(noise(sec), 50, 300)
    x *= 0.85 + 0.15 * smooth_rand(sec, 0.5, 61)
    save("motor_grind", loopify(x, xf), -4, loop=True)


# ------------------------------------------------------------------ one-shots

THUNDER_VARIANTS = 6       # 0-2 near, 3-5 far (audio_director picks by strike distance)


def thunder(k):
    rr = np.random.default_rng(100 + k)
    far = k >= 3
    sec = rr.uniform(8.0, 10.0) if far else rr.uniform(5.0, 6.0)
    n = len(t(sec))
    hi = rr.uniform(140, 190) if far else rr.uniform(320, 420)
    body = band(rr.standard_normal(n), 18, hi)
    # rolling: a few overlapping bursts, the sound arriving from different parts of the channel
    roll = np.zeros(n)
    bursts = rr.integers(3, 6) if far else rr.integers(2, 4)
    for b in range(bursts):
        start = rr.uniform(0.0, sec * (0.45 if far else 0.3)) if b else 0.0
        i = int(start * SR)
        L = n - i
        roll[i:] += rr.uniform(0.5, 1.0) * env(L, rr.uniform(0.15, 0.5) if far else rr.uniform(0.02, 0.08),
                                               rr.uniform(2.0, 3.5) if far else rr.uniform(1.2, 2.2))
    y = body * roll * (0.6 + 0.4 * smooth_rand(sec, 3, 200 + k))
    if not far:
        cl = int(0.25 * SR)
        crack = band(rr.standard_normal(cl), 300, 4000) * env(cl, 0.001, 0.08)
        y[:cl] += crack * (0.8 if k == 0 else 0.45) * np.abs(y).max()
    save(f"thunder_{k}", y, -2)


def click(name, f=2500, d=0.012, body=None):
    L = int(0.08 * SR)
    x = band(noise(L / SR), f * 0.5, f * 2) * env(L, 0.0003, d)
    if body:
        x += np.sin(2 * np.pi * body * t(L / SR)) * env(L, 0.0005, 0.03) * 0.6
    save(name, x, -3)


def carrier_click():
    """Radio carrier key-up: the relay clack, the carrier thump, and a short hiss that cuts dead."""
    L = int(0.7 * SR)
    tt = t(L / SR)
    clack = band(noise(L / SR), 1500, 6000) * env(L, 0.0003, 0.006)
    thump = np.sin(2 * np.pi * 140 * tt) * env(L, 0.001, 0.04) * 0.5
    hiss = band(noise(L / SR), 600, 5000) * 0.25 * (tt > 0.03) * (tt < 0.45) * np.clip((0.45 - tt) / 0.02, 0, 1)
    tail = band(noise(L / SR), 1500, 6000) * env(L, 0.0003, 0.004) * 0.6
    tail = np.roll(tail, int(0.45 * SR))                  # the release click as the carrier drops
    tail[:int(0.45 * SR)] = 0
    save("carrier_click", clack + thump + hiss + tail, -6)


def breaker():
    L = int(0.6 * SR)
    x = band(noise(L / SR), 80, 3000) * env(L, 0.0005, 0.05)
    x += np.sin(2 * np.pi * 70 * t(L / SR)) * env(L, 0.001, 0.15)
    save("breaker_trip", x, -1)


def crank():
    sec = 1.6
    tt = t(sec)
    rate = 7 + 6 * tt
    ph = np.cumsum(rate) / SR
    x = (np.sin(2 * np.pi * ph) > 0.6).astype(float) * band(noise(sec), 100, 900)
    save("gen_crank", x + band(noise(sec), 100, 400) * 0.1, -3)


def footsteps(name, metal=True, n=4):
    for k in range(n):
        L = int(0.35 * SR)
        rr = np.random.default_rng(300 + k + (0 if metal else 50))
        x = band(rr.standard_normal(L), 150, 1500) * env(L, 0.001, 0.04)
        if metal:
            for fr in (420 + 60 * k, 1170 + 80 * k, 2650):
                x += np.sin(2 * np.pi * fr * t(L / SR)) * env(L, 0.001, 0.12) * 0.25
        save(f"{name}_{k}", x, -3)


def knock():
    L = int(0.5 * SR)
    x = band(noise(L / SR), 60, 900) * env(L, 0.0005, 0.03)
    x += np.sin(2 * np.pi * 95 * t(L / SR)) * env(L, 0.001, 0.09) * 0.9
    x += np.sin(2 * np.pi * 380 * t(L / SR)) * env(L, 0.001, 0.05) * 0.3    # steel door ring
    save("knock", x, -1)


def door_heavy():
    sec = 2.4
    tt = t(sec)
    bolt = band(noise(0.3), 500, 5000) * env(int(0.3 * SR), 0.001, 0.05)
    creak_f = 180 + 60 * np.sin(2 * np.pi * 0.7 * tt) + 40 * smooth_rand(sec, 8, 11)
    creak = np.sin(2 * np.pi * np.cumsum(creak_f) / SR) * (np.sin(2 * np.pi * 23 * tt) > 0.2) * 0.4
    x = np.zeros(len(tt))
    x[:len(bolt)] += bolt
    x += band(creak, 100, 2000) * np.clip(tt - 0.4, 0, 1) * np.clip(2.2 - tt, 0, 1)
    save("door_heavy", x + band(noise(sec), 30, 200) * 0.3 * env(len(tt), 0.5, 1.0), -2)


def base_door():
    L = int(1.8 * SR)
    x = band(noise(L / SR), 40, 400) * env(L, 0.002, 0.25)
    x = band(x, None, 600)       # far away, through stone
    save("door_base", x, -6)


def paper_slide():
    sec = 1.2
    x = band(noise(sec), 2000, 9000) * (np.sin(np.pi * t(sec) / sec) ** 2)
    save("paper_slide", x, -6)


def horn(name, f, sec=2.6, peak=-3.0):
    tt = t(sec)
    x = sum((1 / k) * np.sin(2 * np.pi * f * k * tt) for k in range(1, 7))
    e = np.clip(tt / 0.15, 0, 1) * np.clip((sec - tt) / 0.5, 0, 1)
    save(name, band(x * e, 80, 2500), peak)


def squelch():
    L = int(0.12 * SR)
    save("squelch", band(noise(L / SR), 800, 5000) * env(L, 0.0005, 0.04), -8)


def blip():
    L = int(0.02 * SR)
    save("blip", np.sin(2 * np.pi * 1800 * t(L / SR)) * env(L, 0.0002, 0.006), -18)


def ui_click():
    click("ui_click", 3200, 0.008, 900)
    L = int(0.05 * SR)
    save("ui_hover", np.sin(2 * np.pi * 1300 * t(L / SR)) * env(L, 0.001, 0.01), -20)


def pad(name, notes, sec, seed, brightness=1.0, tension=False):
    tt = t(sec)
    x = np.zeros(len(tt))
    for i, n in enumerate(notes):
        f = 440 * 2 ** ((n - 69) / 12)
        det = 1 + 0.002 * np.sin(2 * np.pi * (0.07 + 0.03 * i) * tt)
        voice = sum((0.5 ** k) * np.sin(2 * np.pi * f * (k + 1) * det * tt + i) for k in range(4))
        x += voice * (0.6 + 0.4 * smooth_rand(sec, 0.1, seed + i))
    if tension:
        x += 0.3 * np.sin(2 * np.pi * 41.2 * tt) * (0.5 + 0.5 * smooth_rand(sec, 0.2, seed + 9))
    air = band(noise(sec), 300, 3000) * 0.04
    x = band(x, 40, 1800 * brightness) + air
    save(name, loopify(x, 4.0), -10, loop=True)


def main(argv=None):
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="", help="write here instead of godot/assets/audio (tests)")
    a = ap.parse_args(argv)
    if a.out:
        OUT = Path(a.out)
    RESULT.clear()
    jobs = [
        ("amb_wind", wind), ("amb_gust", gust), ("amb_rain", rain), ("amb_rain_glass", rain_glass),
        ("amb_sea", sea), ("gen_idle", generator), ("hum", hum), ("clockwork", clockwork),
        ("static", static_loop), ("motor_grind", motor_grind),
    ]
    jobs += [(f"thunder_{k}", lambda k=k: thunder(k)) for k in range(THUNDER_VARIANTS)]
    jobs += [
        ("click_switch", lambda: click("click_switch", 2200, 0.012, 160)),
        ("click_knob", lambda: click("click_knob", 1600, 0.02, 220)),
        ("click_button", lambda: click("click_button", 1200, 0.03, 120)),
        ("carrier_click", carrier_click),
        ("ui_click", ui_click), ("breaker_trip", breaker), ("gen_crank", crank),
        ("gen_stop", lambda: save("gen_stop", band(noise(2.0), 30, 300) * env(int(2.0 * SR), 0.01, 0.8), -4)),
        ("step_metal", lambda: footsteps("step_metal", True)),
        ("step_stone", lambda: footsteps("step_stone", False)),
        ("knock", knock), ("door_heavy", door_heavy), ("door_base", base_door), ("paper_slide", paper_slide),
        ("horn_fishing", lambda: horn("horn_fishing", 233, peak=-4.0)),     # was -3: RMS sat on the LOUD gate
        ("horn_ship", lambda: horn("horn_ship", 98, 3.6)),
        ("squelch", squelch), ("blip", blip),
        ("music_menu", lambda: pad("music_menu", [50, 57, 62, 64, 69], 48, 1, 0.8)),      # D modal, open and cold
        ("music_tension", lambda: pad("music_tension", [38, 45, 51, 56], 40, 7, 0.6, tension=True)),
    ]
    for name, fn in jobs:
        seed_for(name)
        fn()
    print("SYNTH_RESULT", json.dumps({"files": len(RESULT), "seconds": RESULT}))


if __name__ == "__main__":
    main()
