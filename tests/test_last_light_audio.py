"""THE LAST LIGHT: objective checks on the synthesised audio (G5 / finding 30). No Godot needed.

- synth.py is deterministic and the committed WAVs are exactly what it produces (so nobody hand-edits
  a generated file, and a regenerate never silently changes a sound);
- every file passes analyze.py's gates: CLIP, DC, SEAM, QUIET, LOUD, and SHORT (constant loops >= 20 s);
- the files the game references exist (6 thunder variants, carrier_click, the gust and glass layers).
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


def test_committed_audio_matches_synth(fresh):
    made = sorted(p.name for p in fresh.glob("*.wav"))
    committed = sorted(p.name for p in ASSETS.glob("*.wav"))
    assert made == committed, f"missing in assets: {set(made) - set(committed)}; stale in assets: {set(committed) - set(made)}"
    differ = [n for n in made if (fresh / n).read_bytes() != (ASSETS / n).read_bytes()]
    assert not differ, f"regenerate with audio/synth.py: {differ}"


def test_audio_gates_pass():
    an = _load("analyze")
    rows = [an.analyse(p) for p in sorted(ASSETS.glob("*.wav"))]
    flagged = {r["file"]: r["flags"] for r in rows if r["flags"]}
    assert not flagged, flagged


def test_referenced_sounds_exist():
    need = [f"thunder_{k}" for k in range(6)] + ["carrier_click", "amb_gust", "amb_rain_glass", "amb_wind", "amb_rain", "amb_sea"]
    missing = [n for n in need if not (ASSETS / f"{n}.wav").exists()]
    assert not missing, missing
