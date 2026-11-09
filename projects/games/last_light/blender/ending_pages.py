"""THE LAST LIGHT · G6a (item 34): the P3 ending panels, the station log page in Callum's hand.

The log_strips.py page (header, ruling) carrying tonight's five canon rows (chapters.json "station_log")
and the 06.30 entry Callum writes at dawn, word for word from ch6.dlg (ch6_final_log):
  godot/assets/ending/p3_correction_ross.png   told the truth, having confessed to Ross
  godot/assets/ending/p3_correction.png        told the truth, "on the instruction of the principal keeper"
  godot/assets/ending/p3_exhibited.png         kept the lie: "Light exhibited throughout"
The entries are read from ch6.dlg, so the panel can never drift from the line the player saw. Seeded:
two runs give identical files.

  tools/py projects/games/last_light/blender/ending_pages.py
"""
import json
import re
import sys
from pathlib import Path

CROP_H = 660        # the panel shows the written part of the page (header to just under the 06.30 entry)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from log_strips import GODOT, ROW, Y0, page_log, row_strip  # noqa: E402

OUT = GODOT / "assets" / "ending"
DLG = GODOT / "data" / "story" / "ch6.dlg"
VARIANTS = {   # panel id -> the ch6_final_log condition its entry is written under
    "p3_correction_ross": 'has_flag("told_truth") and has_flag("confessed_to_ross")',
    "p3_correction": 'has_flag("told_truth") and not has_flag("confessed_to_ross")',
    "p3_exhibited": 'has_flag("kept_lie")',
}
ENTRY = re.compile(r'"15\.11\.71\. 06\.30\. (.+?)"')


def dawn_entries():
    """{panel id: the 06.30 remark} from the quoted log entries in ch6_final_log."""
    text = DLG.read_text()
    block = text.split("== ch6_final_log", 1)[1].split("\n== ", 1)[0]
    out = {}
    for line in block.splitlines():
        m = re.match(r"\[if (.+?)\]\s*~\s*(.*)", line.strip())
        if not m:
            continue
        for pid, cond in VARIANTS.items():
            if m.group(1) == cond:
                e = ENTRY.search(m.group(2))
                if e:
                    out[pid] = e.group(1)
    missing = set(VARIANTS) - set(out)
    if missing:
        raise SystemExit(f"ENDING_PAGES_RESULT FAIL: no ch6_final_log entry for {sorted(missing)}")
    return out


def page(rows, seed):
    img = page_log().convert("RGBA")
    y = Y0 + 52 - 6
    for i, e in enumerate(rows):
        strip, n = row_strip(e, seed + i * 10)
        img.alpha_composite(strip, (0, y))
        y += ROW * max(1, n)
    return img.convert("RGB").crop((0, 0, img.width, CROP_H))


def main():
    data = json.loads((GODOT / "data" / "story" / "chapters.json").read_text())
    tonight = data["station_log"]["1971-11-14"]
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for pid, remark in dawn_entries().items():
        dawn = {"id": "log_0630", "date": "15.11", "time": "06.30", "wind": "", "weather": "", "text": remark}
        page(tonight + [dawn], 71).save(OUT / f"{pid}.png", optimize=True)    # 71: log_strips' row seeds
        made.append(pid)
    print("ENDING_PAGES_RESULT", json.dumps({"pages": made, "out": str(OUT)}))


if __name__ == "__main__":
    main()
