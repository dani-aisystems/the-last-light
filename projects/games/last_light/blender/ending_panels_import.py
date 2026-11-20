"""Import Daniel's ending panels into the game (R3, item 34).

  tools/py projects/games/last_light/blender/ending_panels_import.py

Daniel generates the nine photographic panels in ChatGPT (DECISIONS Q11, item 34 exception) from the prompts and
references in docs/last_light/audit-2026-11/E_ending_image_pack.md. He drops them into `Ending Card/`, named
as ChatGPT named them. This maps each file to its panel id and centre-crops it to exact 16:9. An optional vertical
anchor (0 = top, 1 = bottom) applies when the source isn't landscape. The result is written to
godot/assets/ending/<id>.png at the source's native width. The three P3 log pages come from ending_pages.py and are
not touched.

Native width, not 3840: the panels are shown at about 1536 px (P1-P3) and 1056 px (P4) on a 1080p screen, and
ending_sequence imports them without mipmaps. A 4K upscale adds no detail, and without mipmaps it shimmers
when drawn at a third of its size. ChatGPT's 1672 px output already covers the 1080p slot.
"""

from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "Ending Card"
OUT = HERE.parent / "godot" / "assets" / "ending"

# panel id -> (source file in Ending Card/, vertical anchor of the 16:9 crop)
PANELS = {
    "p1_wheel": ("Stormbound Lighthouse Control Wheel.png", 0.5),
    "p1_alone": ("Stormbound Ship Control Room.png", 0.5),
    "p2_gut": ("Stormbound Lighthouse Passage.png", 0.5),
    "p2_ledge": ("Stranded Freighter at Dawn.png", 0.5),
    "p4_correction": ("Vintage Hearing Room Testimony.png", 0.5),
    "p4_heard_together": ("A Tender Gesture in Court.png", 440 / (1312 - 674)),   # portrait source: the hands band
    "p4_nothing_tide": ("Misty Horizon Fishing Boat.png", 0.5),
    "p4_nothing_pier": ("Rainy Harbor Conversation.png", 0.5),
    "p4_light_exhibited": ("Lighthouse Station Log Inquiry.png", 0.5),
}


def crop_16x9(im: Image.Image, anchor: float) -> Image.Image:
    w, h = im.size
    if w * 9 > h * 16:                       # too wide: trim the sides, centred
        nw = h * 16 // 9
        x0 = (w - nw) // 2
        return im.crop((x0, 0, x0 + nw, h))
    nh = w * 9 // 16                         # too tall: keep the anchored band
    y0 = round((h - nh) * anchor)
    return im.crop((0, y0, w, y0 + nh))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for pid, (name, anchor) in PANELS.items():
        im = crop_16x9(Image.open(SRC / name).convert("RGB"), anchor)
        im.save(OUT / f"{pid}.png", optimize=True)
        print(f"{pid:20s} {im.size[0]}x{im.size[1]}  <- {name}")


if __name__ == "__main__":
    main()
