"""THE LAST LIGHT: objective checks on the synthesised audio (G5 / finding 30). No Godot needed.

- synth.py is deterministic and the committed WAVs are exactly what it produces (so nobody hand-edits
  a generated file, and a regenerate never silently changes a sound);
- every file passes analyze.py's gates: CLIP, DC, SEAM, QUIET, LOUD, and SHORT (constant loops >= 20 s);
- the files the game references exist (6 thunder variants, carrier_click, the gust and glass layers);
- audit Stage D: the recorded CC0 files listed in audio/RECORDED.json match it and are licence-logged.
Whether anything SOUNDS right is Daniel's call at a listening session.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

WS = Path(__file__).resolve().parents[1]
AUDIO_DIR = WS / "projects/games/last_light/audio"
ASSETS = WS / "projects/games/last_light/godot/assets/audio"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"ll_{name}", AUDIO_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def fresh(tmp_path_factory):
    out = tmp_path_factory.mktemp("ll_audio")
    _load("synth").main(["--out", str(out)])
    return out


def _recorded():
    """audit Stage D: the recorded CC0 files (audio/recorded.py), name -> manifest entry."""
    import json
    m = AUDIO_DIR / "RECORDED.json"
    return {f["name"] + ".wav": f for f in json.loads(m.read_text())["files"]} if m.exists() else {}


def test_committed_audio_matches_synth(fresh):
    made = sorted(p.name for p in fresh.glob("*.wav"))
    rec = _recorded()
    committed = sorted(p.name for p in ASSETS.glob("*.wav") if p.name not in rec)
    assert made == committed, f"missing in assets: {set(made) - set(committed)}; stale in assets: {set(committed) - set(made)}"
    differ = [n for n in made if (fresh / n).read_bytes() != (ASSETS / n).read_bytes()]
    assert not differ, f"regenerate with audio/synth.py: {differ}"


def test_audio_gates_pass():
    an = _load("analyze")
    rows = [an.analyse(p) for p in sorted(ASSETS.glob("*.wav"))]
    flagged = {r["file"]: r["flags"] for r in rows if r["flags"]}
    assert not flagged, flagged


def test_referenced_sounds_exist():
    need = [f"thunder_{k}" for k in range(8)] + ["carrier_click", "amb_gust", "amb_rain_glass", "amb_wind", "amb_rain", "amb_sea"]
    missing = [n for n in need if not (ASSETS / f"{n}.wav").exists()]
    assert not missing, missing


def test_recorded_audio_matches_its_manifest():
    """audit Stage D: each recorded file is exactly what audio/recorded.py wrote (sha256 in RECORDED.json), has a
    CC0 source page, and is logged in assets/ASSET_LICENSES.md; no recorded name collides with a synth one."""
    import hashlib
    rec = _recorded()
    assert rec, "audio/RECORDED.json is missing or empty"
    lic = (WS / "assets/ASSET_LICENSES.md").read_text()
    bad = []
    for name, f in rec.items():
        p = ASSETS / name
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != f["sha256"]:
            bad.append(f"{name}: missing or changed (re-run audio/recorded.py)")
        src = f["source"]
        if src["licence"] != "CC0 1.0" or src["page"] not in lic:
            bad.append(f"{name}: source not CC0 or not in ASSET_LICENSES.md")
    assert not bad, bad
    synth_names = {p.name for p in ASSETS.glob("*.wav")} - set(rec)
    assert not (set(rec) & synth_names)



def test_lufs_meter_matches_bs1770_reference():
    """audit music stage: analyze.lufs reads a 997 Hz sine at -20 dBFS as -23.0 LUFS (BS.1770), at 44.1 and 48 kHz."""
    import numpy as np
    an = _load("analyze")
    for sr in (44100, 48000):
        x = 0.1 * np.sin(2 * np.pi * 997 * np.arange(5 * sr) / sr)
        assert abs(an.lufs(x, sr) + 23.0) < 0.1
    assert an.lufs(np.zeros(44100), 44100) == -70.0


def test_music_cues_are_mastered_to_the_cue_sheet():
    """audit music stage: every cue in godot/data/music_cues.json has its file, within 1 LU of its 23.2 level."""
    import json
    an = _load("analyze")
    table = json.loads((WS / "projects/games/last_light/godot/data/music_cues.json").read_text())
    import subprocess
    import numpy as np
    off = {}
    for cid, c in table["cues"].items():
        f = c["file"]
        p = ASSETS / (f if "." in f else f"{f}.wav")
        assert p.exists(), cid
        if p.suffix == ".wav":
            got = an.analyse(p)["lufs"]
        else:                                    # Daniel's tracks (MP3): decoded by ffmpeg, then the same meter
            raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "2", "-ar", "48000", "-f", "f32le", "-"],
                                 capture_output=True, check=True).stdout
            got = an.lufs(np.frombuffer(raw, np.float32).astype(np.float64).reshape(-1, 2), 48000)
        if abs(got - c["lufs"]) > 1.0:
            off[cid] = (round(got, 2), c["lufs"])
        if c.get("placeholder"):
            assert (ASSETS / f"{c['placeholder']}.wav").exists(), cid
    assert not off, off


def test_score_tracks_match_their_manifest():
    """Daniel's own tracks (DECISIONS Q27): each MP3 is what audio/score.py wrote (SCORE.json sha256), and the cue
    table points at it."""
    import hashlib
    import json
    m = json.loads((AUDIO_DIR / "SCORE.json").read_text())
    table = json.loads((WS / "projects/games/last_light/godot/data/music_cues.json").read_text())["cues"]
    bad = []
    for r in m["cues"]:
        p = WS / "projects/games/last_light" / r["file"]
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != r["sha256"]:
            bad.append(f"{r['cue']}: missing or changed (re-run audio/score.py)")
        if table[r["cue"]]["file"] != f"score/{p.name}":
            bad.append(f"{r['cue']}: music_cues.json does not point at {p.name}")
    assert not bad, bad
