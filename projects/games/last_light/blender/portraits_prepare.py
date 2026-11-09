"""Prepare Daniel's radio portraits for the game (Stage 3C, item 22).

  tools/py projects/games/last_light/blender/portraits_prepare.py

Daniel generates the portraits in ChatGPT from one shared template (2:3, 1024x1536, same framing, lighting,
backdrop and grade) and drops them into character-refs/<id>/. Decision 2026-11-09: AI portraits are allowed
for the radio card ONLY (and the item 34 ending panels, DECISIONS Q11); the no-AI rule stands for everything
else. The Mary Ellen's card is a print of the boat (character-refs/ellen.png), not a face.

This crops each source to the centred 4:5 area (1024x1280: 128 px off the top and the bottom, as the template
was composed for), resizes it to 512x640 and writes godot/assets/portraits/<id>_<expr>.png. No extra grade:
the template already carries the 1971 print look (portraits_grade.py is the old Blender-bust path).

To add an expression: put the file in character-refs/<id>/, add one line to SOURCES, run this. The game
picks it up by file name (Speakers.portrait), so no code change is needed.
"""

from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REFS = HERE.parent / "character-refs"
OUT = HERE.parent / "godot" / "assets" / "portraits"
SIZE = (512, 640)

# (character id, expression) -> source file in character-refs/. Keys match the .dlg tags: MORAG(worried).
SOURCES = {
    ("callum", "neutral"): "callum/image.png",
    ("callum", "guarded"): "callum/image copy.png",
    ("morag", "neutral"): "morag/image.png",
    ("morag", "worried"): "morag/image copy.png",
    ("rory", "neutral"): "rory/image.png",
    ("rory", "scared"): "rory/image copy.png",
    ("elspeth", "neutral"): "elspeth/image.png",
    ("elspeth", "cold"): "elspeth/Cold Resolve_ A Watery-Eyed Portrait.png",
    ("hector", "neutral"): "hector/image.png",
    ("hector", "sorry"): "hector/Warmly Apologetic Captain Macleod.png",
    ("ross", "neutral"): "ross/Weathered Fisherman in Rain-Slick Shadow.png",   # silhouette only (F12)
    # the ch2 caller (speaker MARY ELLEN): not a face but the boat, SY 214 at the pier (Daniel 2026-11-09)
    ("mary_ellen", "neutral"): "ellen.png",
}


def prepare(src: Path, dst: Path) -> None:
    im = Image.open(src).convert("RGB")
    w, h = im.size
    ch = round(w * 5 / 4)                       # the centred 4:5 crop of the 2:3 template
    if ch > h:
        raise SystemExit(f"{src}: {w}x{h} is wider than 4:5; expected the 2:3 template")
    top = (h - ch) // 2
    im = im.crop((0, top, w, top + ch)).resize(SIZE, Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, optimize=True)


def main() -> None:
    done, missing = [], []
    for (cid, expr), rel in SOURCES.items():
        src = REFS / rel
        if not src.exists():
            missing.append(rel)
            continue
        prepare(src, OUT / f"{cid}_{expr}.png")
        done.append(f"{cid}_{expr}")
    print("PORTRAITS_RESULT", "PASS" if not missing else "PARTIAL", done, "missing:", missing)


if __name__ == "__main__":
    main()
