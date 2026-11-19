"""THE LAST LIGHT · audit Stage D: the recorded CC0 sounds, cut and mastered for the game (host Python: tools/py).

The sources are Freesound CC0 recordings Daniel approved on 2026-11-19 (DECISIONS Q16), downloaded as Freesound's
high-quality preview MP3s into assets/audio_cc0/<item>_<id>/ (each with SOURCE.txt; logged in
assets/ASSET_LICENSES.md). This script decodes them (ffmpeg), finds the events in each (an onset and level
detector, no listening needed), cuts the takes named in CUTS with short fades, masters them through synth.py's
save() (DC removed, peak-normalised, 16-bit mono 44.1 kHz WAV in godot/assets/audio/) and writes
audio/RECORDED.json: every output with its source page, licence, the source file's sha256 and its own sha256.
tests/test_last_light_audio.py reads that manifest: recorded files are exempt from synth byte-identity but must
match their recorded hash and pass analyze.py's gates.

  tools/py audio/recorded.py            cut and write everything
  tools/py audio/recorded.py --sheet P  also draw each source's envelope with the cuts marked (for review)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SRC = ROOT / "assets" / "audio_cc0"
sys.path.insert(0, str(HERE))
import synth  # noqa: E402  (save(), SR, OUT)

SR = synth.SR
MANIFEST = HERE / "RECORDED.json"

# item folder -> page, title, author (as logged in assets/ASSET_LICENSES.md)
SOURCES = {
    "cough_369295": ("https://freesound.org/people/georgisound/sounds/369295/", "Coughing.wav", "georgisound"),
    "cough_157296": ("https://freesound.org/people/husky70/sounds/157296/", "Coughing Cough.wav", "husky70"),
    "breaths_711359": ("https://freesound.org/people/sickfin/sounds/711359/",
                       "Old Man or Middle-aged Man's Struggled Breathing", "sickfin"),
    "boots_concrete_465299": ("https://freesound.org/people/SoftDistortionFX/sounds/465299/", "Concrete Footsteps",
                              "SoftDistortionFX"),
    "boots_steel_562195": ("https://freesound.org/people/gristi/sounds/562195/", "snd_footsteps_metal_floor_inside.wav",
                           "gristi"),
    "stair_iron_749713": ("https://freesound.org/people/RFCaldas/sounds/749713/", "Steps on metal stair Up and Down 2",
                          "RFCaldas"),
    "door_hinge_637583": ("https://freesound.org/people/kyles/sounds/637583/",
                          "gate big rusty metal door garage open heavy creak rattle.flac", "kyles"),
    "phone_lift_616840": ("https://freesound.org/people/TRP/sounds/616840/",
                          "Phone, old wired handset, pick up hang up, cu then medium (2012).wav", "TRP"),
    "hand_pump_580670": ("https://freesound.org/people/Garuda1982/sounds/580670/",
                         "old manual pump pumping water sound effect", "Garuda1982"),
    "kettle_507937": ("https://freesound.org/people/wlabarron/sounds/507937/", "Whistling gas kettle coming to the boil",
                      "wlabarron"),
    "teletype_483336": ("https://freesound.org/people/craigsmith/sounds/483336/", "R20-17-Teletype Machine.wav",
                        "craigsmith"),
}

# What is cut from each source. "events": the strongest N detected events (in time order), each padded and
# faded; "span": one fixed stretch [t0, t1] in seconds. peak = synth.save()'s peak target (dBFS).
CUTS = [
    # Ross's cough: one older, sick voice (georgisound), topped up from husky70's fit; never the same twice (game)
    {"src": "cough_369295", "names": "ross_cough_%d", "events": 6, "gap": 0.15, "min": 0.12, "max": 3.0,
     "rel_db": -26.0, "pre": 0.03, "post": 0.18, "peak": -4.0},
    {"src": "cough_157296", "names": "ross_cough_%d", "first_index": 6, "events": 2, "gap": 0.2, "min": 0.4, "max": 2.6,
     "rel_db": -20.0, "pre": 0.03, "post": 0.18, "peak": -4.0},
    # tired breaths between his lines, kept quiet
    {"src": "breaths_711359", "names": "ross_breath_%d", "events": 4, "gap": 0.15, "min": 0.4, "max": 1.6,
     "rel_db": -40.0, "pre": 0.05, "post": 0.2, "peak": -14.0, "pick": "median"},
    # the keeper's boots: concrete (the room) and steel (the stair takes, also on the chequer-plate landing)
    {"src": "boots_concrete_465299", "names": "step_concrete_%d", "steps": 6, "win": 0.32, "peak": -6.0},
    # (boots_steel_562195, approved and logged, is not used: one reverberant hit, then rumble, no distinct
    # footfalls; the chequer-plate landing uses the iron-stair takes, the same steel underfoot)
    {"src": "stair_iron_749713", "names": "step_stair_%d", "steps": 8, "win": 0.38, "after": 0.3, "peak": -5.0},
    # one take each
    {"src": "door_hinge_637583", "names": "door_hinge", "span": [0.25, 6.1], "peak": -6.0},
    {"src": "phone_lift_616840", "names": "phone_lift", "span": [0.1, 1.2], "peak": -6.0},
    {"src": "hand_pump_580670", "names": "hand_pump", "span": [2.0, 9.0], "peak": -6.0},
    {"src": "kettle_507937", "names": "kettle_boil", "span": [17.0, 35.0], "peak": -8.0},
    {"src": "teletype_483336", "names": "teleprinter", "span": [0.5, 10.5], "peak": -8.0},
]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def source_file(item: str) -> Path:
    fs = sorted((SRC / item).glob("*.mp3"))
    if not fs:
        raise SystemExit(f"missing source {SRC / item} (see assets/ASSET_LICENSES.md)")
    return fs[0]


def decode(p: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def frames_db(x: np.ndarray, hop: float = 0.01) -> np.ndarray:
    n = int(hop * SR)
    k = len(x) // n
    return 20.0 * np.log10(np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(axis=1)) + 1e-9)


def events(x: np.ndarray, rel_db: float, gap: float, dmin: float, dmax: float) -> list[tuple[float, float, float]]:
    """Stretches louder than (the loudest 10 ms frame + rel_db), with gaps under `gap` s merged: (t0, t1, level)."""
    db = frames_db(x)
    on = db > db.max() + rel_db
    out, i = [], 0
    while i < len(on):
        if not on[i]:
            i += 1
            continue
        j = i
        while j < len(on) and (on[j] or (np.any(on[j:j + int(gap / 0.01)]) and j < len(on))):
            j += 1
        t0, t1 = i * 0.01, j * 0.01
        if dmin <= t1 - t0 <= dmax:
            out.append((t0, t1, float(db[i:j].max())))
        i = j
    return out


def onsets(x: np.ndarray, min_gap: float = 0.25) -> list[tuple[float, float]]:
    """Footfalls: frames where the level jumps (spectral-flux-like, on 5 ms frames), at least min_gap apart:
    (time, jump in dB). Works on a steady background, where a level threshold would not."""
    n = int(0.005 * SR)
    k = len(x) // n
    db = 20.0 * np.log10(np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(axis=1)) + 1e-9)
    jump = np.diff(db, prepend=db[0])
    smooth = np.convolve(jump, np.ones(3) / 3, mode="same")
    order = np.argsort(-smooth)
    picked: list[tuple[float, float]] = []
    for i in order:
        t = i * 0.005
        if smooth[i] < 3.0:
            break
        if all(abs(t - p[0]) >= min_gap for p in picked):
            picked.append((t, float(smooth[i])))
    return sorted(picked)


def sharpness(x: np.ndarray, t: float) -> float:
    """A footfall is an impact: its peak in the first 30 ms over the RMS of the 100 ms before it (dB). A scrape,
    a swell or the stair's ringing background scores low."""
    i = int(t * SR)
    pre = x[max(0, i - int(0.1 * SR)):i]
    hit = x[i:i + int(0.03 * SR)]
    if len(pre) < 10 or len(hit) < 10:
        return -99.0
    return float(20.0 * np.log10(np.abs(hit).max() / (np.sqrt((pre ** 2).mean()) + 1e-9) + 1e-9))


def fade(y: np.ndarray, fin: float = 0.005, fout: float = 0.04) -> np.ndarray:
    y = y.copy()
    a, b = max(1, int(fin * SR)), max(1, int(fout * SR))
    y[:a] *= np.linspace(0.0, 1.0, a)
    y[-b:] *= np.linspace(1.0, 0.0, b)
    return y


def highpass(y: np.ndarray, hz: float = 60.0) -> np.ndarray:
    """One-pole high-pass: rumble and MP3 DC drift out before the DC-free master."""
    a = np.exp(-2.0 * np.pi * hz / SR)
    out = np.zeros_like(y)
    prev_x = prev_y = 0.0
    for i, v in enumerate(y):
        prev_y = a * (prev_y + v - prev_x)
        prev_x = v
        out[i] = prev_y
    return out


def cut_all() -> tuple[list[dict], dict]:
    results, marks = [], {}
    for c in CUTS:
        src = source_file(c["src"])
        x = decode(src)
        x = highpass(x)
        cuts: list[tuple[str, float, float]] = []
        if "span" in c:
            cuts.append((c["names"], c["span"][0], min(c["span"][1], len(x) / SR)))
        elif "steps" in c:
            ons = [o for o in onsets(x) if c.get("after", 0.0) <= o[0] <= len(x) / SR - c["win"] - 0.01]
            best = sorted(ons, key=lambda o: -sharpness(x, o[0]))[:c["steps"]]
            for k, (t, _) in enumerate(sorted(best)):
                cuts.append((c["names"] % k, max(0.0, t - 0.01), t + c["win"]))
        else:
            ev = events(x, c["rel_db"], c["gap"], c["min"], c["max"])
            if c.get("pick") == "median":       # mid-strength events: tired, not gasping
                ev = sorted(ev, key=lambda e: e[2])
                mid = len(ev) // 2
                ev = ev[max(0, mid - c["events"] // 2):max(0, mid - c["events"] // 2) + c["events"]]
            else:
                ev = sorted(ev, key=lambda e: -e[2])[:c["events"]]
            for k, (t0, t1, _) in enumerate(sorted(ev)):
                cuts.append((c["names"] % (c.get("first_index", 0) + k), max(0.0, t0 - c["pre"]), t1 + c["post"]))
        marks.setdefault(c["src"], []).extend([(a, b) for _, a, b in cuts])
        for name, t0, t1 in cuts:
            y = fade(x[int(t0 * SR):int(t1 * SR)], 0.005, 0.06 if t1 - t0 > 0.5 else 0.03)
            synth.save(name, y, c["peak"])
            out = Path(synth.OUT) / f"{name}.wav"
            page, title, author = SOURCES[c["src"]]
            results.append({"name": name, "file": f"godot/assets/audio/{name}.wav", "sha256": sha256(out),
                            "seconds": round(t1 - t0, 3), "cut": [round(t0, 3), round(t1, 3)],
                            "source": {"page": page, "title": title, "author": author, "licence": "CC0 1.0",
                                       "file": str(src.relative_to(ROOT)), "sha256": sha256(src)}})
    return results, marks


def sheet(marks: dict, path: str) -> None:
    from PIL import Image, ImageDraw
    W, H = 1600, 110
    items = list(marks)
    img = Image.new("RGB", (W, H * len(items)), "white")
    d = ImageDraw.Draw(img)
    for i, item in enumerate(items):
        x = highpass(decode(source_file(item)))
        db = frames_db(x)
        dur = len(x) / SR
        y0 = i * H
        for a, b in marks[item]:
            d.rectangle([int(a / dur * W), y0 + 14, int(b / dur * W), y0 + H - 4], fill=(255, 225, 160))
        for k, v in enumerate(db):
            px = int(k / len(db) * W)
            h = int(np.clip((v + 70.0) / 70.0, 0.0, 1.0) * (H - 25))
            d.line([(px, y0 + H - 5), (px, y0 + H - 5 - h)], fill=(40, 80, 160))
        d.text((4, y0 + 2), f"{item}  {dur:.1f} s  ({len(marks[item])} cuts)", fill=(0, 0, 0))
    img.save(path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheet")
    a = ap.parse_args(argv)
    results, marks = cut_all()
    MANIFEST.write_text(json.dumps({"note": "audit Stage D: recorded CC0 sounds (audio/recorded.py); Daniel's OK "
                                            "2026-11-19, DECISIONS Q16; licences in assets/ASSET_LICENSES.md",
                                    "files": results}, indent=1) + "\n")
    if a.sheet:
        sheet(marks, a.sheet)
    print("RECORDED_RESULT", json.dumps({"files": len(results), "names": [r["name"] for r in results]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
