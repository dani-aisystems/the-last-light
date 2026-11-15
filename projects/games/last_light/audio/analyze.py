"""Objective audio QA for THE LAST LIGHT's synthesised sounds (godot/assets/audio/*.wav).

    tools/py projects/games/last_light/audio/analyze.py [--json renders/last_light/audio_report.json]

It measures what can be checked without ears. Whether a sound *sounds* right is still Daniel's call.

Per file it reports:
- peak and RMS (dBFS)
- crest factor
- DC offset
- clipped samples
- duration
- for looping ambiences (amb_*, gen_*, hum*, clockwork*, static*, motor*): the loop-seam jump, which
  is heard as a click every loop

Flags:
- CLIP: peak >= -0.3 dBFS, or any sample at full scale
- DC: |mean| > 0.005
- SEAM: loop jump > 0.05 full scale AND larger than the file's own 99.9th-percentile sample step
  (bright noise steps more than 0.05 between neighbouring samples anyway; that is not a click)
- QUIET: RMS < -45 dBFS, on a file that isn't meant to be silent
- LOUD: RMS > -10 dBFS (a ceiling check on overall level)
- SHORT: a constant looping layer shorter than 20 s, whose repeat is easy to hear (finding 30)
- CLICKY (R3, 2026-11-15): a rain layer with more than 2 sudden onsets a second (5 ms frames whose level
  jumps by > 6 dB); the old rain had about 5 a second on the roof and 40 on the glass ("clicking")
- TAIL (R3): a thunder file that is still audible at its end (last 50 ms above -45 dB of its peak)
- DULL (R3): a thunder file with less than -18 dB of its energy above 200 Hz (a "pop" on small speakers)

`--strict` exits 1 when any file is flagged (used by tests/test_last_light_audio.py).
"""

import argparse
import json
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
AUDIO = HERE.parent / "godot" / "assets" / "audio"
LOOP_PREFIXES = ("amb_", "gen_idle", "gen_run", "hum", "clockwork", "static", "motor", "music_")
MIN_LOOP_S = 20.0


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        n, ch, sw, sr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = w.readframes(n)
    if sw == 2:
        x = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        v = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16))
        v = np.where(v & 0x800000, v - 0x1000000, v)
        x = v.astype(np.float64) / 8388608.0
    elif sw == 4:
        x = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    else:
        raise ValueError(f"{path.name}: unsupported sample width {sw}")
    return x.reshape(-1, ch), sr


def db(v: float) -> float:
    return float(20 * np.log10(max(v, 1e-9)))


def analyse(path: Path) -> dict:
    x, sr = read_wav(path)
    mono = x.mean(axis=1)
    peak = float(np.abs(x).max())
    rms = float(np.sqrt(np.mean(mono ** 2)))
    is_loop = path.stem.startswith(LOOP_PREFIXES)
    seam = float(np.abs(x[0] - x[-1]).max()) if is_loop and len(x) > 1 else None
    step999 = float(np.percentile(np.abs(np.diff(mono)), 99.9)) if is_loop and len(x) > 1 else None
    r = {
        "file": path.name, "seconds": round(len(x) / sr, 2), "rate": sr, "channels": x.shape[1],
        "peak_dbfs": round(db(peak), 1), "rms_dbfs": round(db(rms), 1),
        "crest_db": round(db(peak) - db(rms), 1), "dc": round(float(mono.mean()), 4),
        "clipped": int(np.sum(np.abs(x) >= 0.9999)), "loop": is_loop,
        "seam_jump": round(seam, 3) if seam is not None else None,
        "step_p999": round(step999, 3) if step999 is not None else None,
    }
    flags = []
    if r["peak_dbfs"] >= -0.3 or r["clipped"]:
        flags.append("CLIP")
    if abs(r["dc"]) > 0.005:
        flags.append("DC")
    if seam is not None and seam > 0.05 and seam > step999:
        flags.append("SEAM")
    if r["rms_dbfs"] < -45:
        flags.append("QUIET")
    if r["rms_dbfs"] > -10:
        flags.append("LOUD")
    if is_loop and r["seconds"] < MIN_LOOP_S:
        flags.append("SHORT")
    if path.stem.startswith("amb_rain"):
        fr = mono[: len(mono) // 220 * 220].reshape(-1, 220)
        lv = np.sqrt((fr ** 2).mean(axis=1)) + 1e-9
        r["onsets_per_s"] = round(float(np.mean(20 * np.log10(lv[1:] / lv[:-1]) > 6.0)) * sr / 220, 2)
        if r["onsets_per_s"] > 2.0:
            flags.append("CLICKY")
    if path.stem.startswith("thunder_"):
        end = mono[-int(0.05 * sr):]
        r["end_db"] = round(db(float(np.sqrt(np.mean(end ** 2)))) - db(peak), 1)
        X = np.abs(np.fft.rfft(mono)) ** 2
        f = np.fft.rfftfreq(len(mono), 1 / sr)
        r["above_200_db"] = round(float(10 * np.log10(X[f >= 200].sum() / X.sum() + 1e-12)), 1)
        if r["end_db"] > -45:
            flags.append("TAIL")
        if r["above_200_db"] < -18:
            flags.append("DULL")
    r["flags"] = flags
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(AUDIO))
    ap.add_argument("--json", default="")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any file is flagged")
    a = ap.parse_args()
    files = sorted(Path(a.dir).glob("*.wav"))
    if not files:
        print(f"no wav files in {a.dir}")
        return 1
    rows = [analyse(f) for f in files]
    print(f"{'file':28s} {'sec':>6s} {'peak':>6s} {'rms':>6s} {'crest':>6s} {'dc':>7s} {'seam':>6s}  flags")
    for r in rows:
        seam = "" if r["seam_jump"] is None else f"{r['seam_jump']:.3f}"
        print(f"{r['file']:28s} {r['seconds']:6.2f} {r['peak_dbfs']:6.1f} {r['rms_dbfs']:6.1f} {r['crest_db']:6.1f} "
              f"{r['dc']:7.4f} {seam:>6s}  {' '.join(r['flags'])}")
    flagged = [r for r in rows if r["flags"]]
    print(f"AUDIO_RESULT files={len(rows)} flagged={len(flagged)} "
          + " ".join(f"{r['file']}:{'+'.join(r['flags'])}" for r in flagged))
    if a.json:
        Path(a.json).write_text(json.dumps(rows, indent=1))
    return 1 if (a.strict and flagged) else 0


if __name__ == "__main__":
    sys.exit(main())
