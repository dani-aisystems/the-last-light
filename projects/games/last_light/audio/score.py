"""THE LAST LIGHT · the score: Daniel's own tracks (DECISIONS Q16, Q27) cut, looped, mastered and encoded for the
game (host Python: tools/py; needs ffmpeg with libmp3lame).

Daniel generates the tracks (Suno; the prompts are audio/SOUNDTRACK_PROMPTS.md) and drops them into
audio/Music Tracks/ (not committed: like other supplied assets, the folder stays local). PICKS names the take used
for each cue and the stretch kept. This script:
  - decodes the take (48 kHz stereo), keeps [t0, t1] (trimming the lead-in and the tail Suno adds);
  - a loop cue: crossfades its last LOOP_XF seconds into its head, so the end runs seamlessly into the start;
  - a once-through cue: a short fade-in, and a fade-out over its last FADE_OUT seconds;
  - masters it to the cue's level in godot/data/music_cues.json (integrated LUFS, analyze.lufs), with a soft
    knee on the peaks only (1 dB of headroom);
  - encodes 192 kbps stereo MP3 into godot/assets/audio/score/<cue>.mp3 (LAME writes its gapless tag, which
    Godot's minimp3 reads, so a loop has no encoder gap; music_test checks the decoded length);
  - writes audio/SCORE.json: per cue, the take, its sha256, the cut, the measured level and the output's sha256.

  tools/py audio/score.py            build every cue in PICKS
  tools/py audio/score.py --scan     only print each take's level, key and shape (no output)
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
sys.path.insert(0, str(HERE))
import analyze  # noqa: E402

SRC = HERE / "Music Tracks"
GODOT = HERE.parent / "godot"
OUT = GODOT / "assets" / "audio" / "score"
CUES = GODOT / "data" / "music_cues.json"
MANIFEST = HERE / "SCORE.json"
SR = 48000
LOOP_XF = 4.0
FADE_OUT = 3.0

# cue -> (take file in audio/Music Tracks/, keep from t0 to t1 seconds; None = to the end). Chosen 2026-11-20 by
# measurement (Claude cannot listen): the key against D minor, no late climax, the flattest loudness curve, the
# sparsest texture. Record: docs/last_light/audit-2026-11/19_music.md section 6. M10's takes were filed as
# "M09 Decision" (17 to 20; they resolve to D major), identified 2026-11-20 at Daniel's word.
PICKS = {
    "M01": ("41 - M01 Title.wav", 0.0, None),
    "M02": ("37 - M02 Arrival.wav", 0.0, None),
    "M03": ("29 - M03 The watch.wav", 0.0, None),
    "M04": ("21 - M04 Weather (calm).wav", 0.0, None),
    "M04b": ("09 - M04b Weather (restless).wav", 0.0, None),
    "M05": ("05 - M05 Mechanism.wav", 0.0, None),
    "M06": ("10 - M06 The stair.wav", 0.0, None),
    "M07": ("02 - M07 Ross.wav", 0.0, None),
    "M08": ("28 - M08 The letter.wav", 0.0, None),
    "M09": ("22 - M09 Decision.wav", 0.0, None),
    "M10": ("18 - M09 Decision.wav", 0.0, None),    # filed by Suno as "M09": 17-20 end in D major (M10's brief)
    "M11": ("13 - M11 Ending Heard Together.wav", 0.0, None),
    "M12": ("09 - M12 Ending Nothing to Report.wav", 0.0, None),
    "M13": ("07 - M13 Ending Light Exhibited.wav", 0.0, None),
    "M14": ("03 - M14 Credits.wav", 0.0, None),
}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def decode(p: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64).reshape(-1, 2)


def trim(x: np.ndarray, floor_db: float = -60.0) -> tuple[np.ndarray, float, float]:
    """Drop near-silence at both ends (10 ms frames under floor_db): (x, seconds cut at the head, at the tail)."""
    n = int(0.01 * SR)
    k = len(x) // n
    db = 20.0 * np.log10(np.sqrt((x[:k * n] ** 2).mean(axis=1).reshape(k, n).mean(axis=1)) + 1e-12)
    on = np.flatnonzero(db > floor_db)
    if len(on) == 0:
        return x, 0.0, 0.0
    a, b = on[0] * n, min(len(x), (on[-1] + 1) * n)
    return x[a:b], a / SR, (len(x) - b) / SR


def tail_fade_start(x: np.ndarray) -> float:
    """Where a take's own ending fade begins: the last time its 1 s level was within 6 dB of its median."""
    n = SR
    k = len(x) // n
    db = 20.0 * np.log10(np.sqrt((x[:k * n] ** 2).mean(axis=1).reshape(k, n).mean(axis=1)) + 1e-12)
    med = np.median(db)
    ok = np.flatnonzero(db > med - 6.0)
    return float((ok[-1] + 1) * n / SR) if len(ok) else len(x) / SR


def make_loop(x: np.ndarray) -> np.ndarray:
    """A seamless loop: keep the take up to its own fade, then crossfade the last LOOP_XF s into the head (equal
    power), so sample N-1 runs into sample 0 with no seam."""
    end = int(tail_fade_start(x) * SR)
    x = x[:end]
    xf = int(LOOP_XF * SR)
    head, body, tail = x[:xf], x[xf:-xf], x[-xf:]
    t = np.linspace(0.0, np.pi / 2.0, xf)[:, None]
    blend = tail * np.cos(t) + head * np.sin(t)
    return np.vstack([blend, body])


def master(x: np.ndarray, target: float) -> np.ndarray:
    y = x - x.mean(axis=0)
    for _ in range(3):
        z = y * 10.0 ** ((target - analyze.lufs(y, SR)) / 20.0)
        a = np.abs(z)
        z = np.where(a < 0.7, z, np.sign(z) * (0.7 + 0.19 * np.tanh((a - 0.7) / 0.19)))
        if abs(analyze.lufs(z, SR) - target) < 0.2:
            return z
        y = z
    return z


def encode(x: np.ndarray, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(x, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "libmp3lame", "-b:a", "192k", "-write_xing", "1", str(out)], input=pcm, check=True)


def build(cue: str, table: dict) -> dict:
    take, t0, t1 = PICKS[cue]
    src = SRC / take
    c = table["cues"][cue]
    x = decode(src)
    x = x[int(t0 * SR):(int(t1 * SR) if t1 else len(x))]
    x, cut_a, cut_b = trim(x)
    if c.get("loop", False):
        x = make_loop(x)
    else:
        n = len(x)
        fin = np.clip(np.arange(n) / (0.05 * SR), 0.0, 1.0)
        fout = np.clip((n - np.arange(n)) / (FADE_OUT * SR), 0.0, 1.0)
        x = x * (fin * fout)[:, None]
    y = master(x, float(c["lufs"]))
    out = OUT / f"{cue.lower()}.mp3"
    encode(y, out)
    got = analyze.lufs(decode(out), SR)
    return {"cue": cue, "take": take, "take_sha256": sha256(src), "kept": [round(t0 + cut_a, 2), round(t0 + cut_a + len(x) / SR, 2)],
            "loop": bool(c.get("loop", False)), "seconds": round(len(y) / SR, 2), "lufs_target": c["lufs"],
            "lufs_mp3": round(got, 2), "peak_dbfs": round(20 * np.log10(np.abs(y).max() + 1e-12), 2),
            "file": f"godot/assets/audio/score/{out.name}", "sha256": sha256(out)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args(argv)
    table = json.loads(CUES.read_text())
    rows = [build(c, table) for c in PICKS if not a.only or c in a.only]
    old = json.loads(MANIFEST.read_text())["cues"] if MANIFEST.exists() and a.only else []
    keep = {r["cue"]: r for r in old}
    keep.update({r["cue"]: r for r in rows})
    MANIFEST.write_text(json.dumps({"note": "Daniel's own tracks (DECISIONS Q16, Q27), built by audio/score.py from "
                                            "audio/Music Tracks/ (local, not committed)",
                                    "cues": [keep[c] for c in PICKS if c in keep]}, indent=1) + "\n")
    for r in rows:
        print(f"{r['cue']:5s} {r['take'][:38]:38s} {r['seconds']:7.1f} s  {r['lufs_mp3']:6.1f} LUFS "
              f"(target {r['lufs_target']})  peak {r['peak_dbfs']:5.1f}  {'loop' if r['loop'] else 'once'}")
    print("SCORE_RESULT", json.dumps({"cues": len(rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
