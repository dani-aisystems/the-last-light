"""THE LAST LIGHT G6a (item 34): the P3 ending panels, the log page in Callum's hand. No Godot needed.

- the 06.30 entry on each page is the quoted log entry in ch6.dlg's ch6_final_log, word for word, so the
  panel can never drift from the line the player has just read;
- the committed PNGs are exactly what blender/ending_pages.py renders now (seeded; nobody hand-edits a
  generated panel).
Whether the page LOOKS right is checked in the captures.
"""

import importlib.util
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

WS = Path(__file__).resolve().parents[1]
BLENDER = WS / "projects/games/last_light/blender"
GODOT = WS / "projects/games/last_light/godot"


def _load():
    sys.path.insert(0, str(BLENDER))
    spec = importlib.util.spec_from_file_location("ll_ending_pages", BLENDER / "ending_pages.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_dawn_entries_are_the_dialogue_lines():
    mod = _load()
    entries = mod.dawn_entries()
    assert set(entries) == {"p3_correction_ross", "p3_correction", "p3_exhibited"}
    quoted = re.findall(r'"15\.11\.71\. 06\.30\. (.+?)"', (GODOT / "data/story/ch6.dlg").read_text())
    for pid, remark in entries.items():
        assert remark in quoted, f"{pid}: '{remark}' is not a ch6.dlg log entry"
    assert entries["p3_exhibited"] == "Storm abating. Light exhibited throughout. Nothing to report."
    assert "and in my hand" in entries["p3_correction_ross"]
    assert "on the instruction of the principal keeper" in entries["p3_correction"]


def test_committed_pages_match_the_renderer():
    import json
    mod = _load()
    tonight = json.loads((GODOT / "data/story/chapters.json").read_text())["station_log"]["1971-11-14"]
    for pid, remark in mod.dawn_entries().items():
        dawn = {"id": "log_0630", "date": "15.11", "time": "06.30", "wind": "", "weather": "", "text": remark}
        fresh = np.asarray(mod.page(tonight + [dawn], 71))
        committed = np.asarray(Image.open(GODOT / f"assets/ending/{pid}.png").convert("RGB"))
        assert fresh.shape == committed.shape, f"{pid}: {fresh.shape} vs {committed.shape}"
        assert np.array_equal(fresh, committed), f"{pid}: the committed panel differs from ending_pages.py"
