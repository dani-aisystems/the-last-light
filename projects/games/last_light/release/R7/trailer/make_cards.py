#!/usr/bin/env python3
"""THE LAST LIGHT release R7: the trailer's text cards, drawn with the game's own type and colours.

  make_cards.py OUT_DIR

Fonts are the game's OFL faces (godot/assets/fonts). Colours are the ending sequence's: warm black
(ending_sequence.gd WARM_BLACK 0.035, 0.026, 0.02), the card title cream and the amber of its subtitle
(sampled from the in-game "HEARD TOGETHER" card: title ~(232,226,214), subtitle ~(214,160,74)).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

GAME = Path(__file__).resolve().parents[3] / "godot"
FONTS = GAME / "assets/fonts"
W, H = 1920, 1080
WARM_BLACK = (9, 7, 5)
CREAM = (232, 226, 214)
AMBER = (214, 160, 74)
GREY = (120, 112, 100)


def font(name: str, size: int, wght: int | None = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTS / name), size)
    if wght:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    return f


def centred(d: ImageDraw.ImageDraw, y: int, text: str, f, fill, tracking: int = 0) -> None:
    if tracking:
        widths = [d.textlength(ch, font=f) for ch in text]
        total = sum(widths) + tracking * (len(text) - 1)
        x = (W - total) / 2
        for ch, w in zip(text, widths):
            d.text((x, y), ch, font=f, fill=fill)
            x += w + tracking
    else:
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2, y), text, font=f, fill=fill)


def title_card(out: Path, with_credit: bool) -> None:
    im = Image.new("RGB", (W, H), WARM_BLACK)
    logo = Image.open(GAME / "assets/branding/logo_title.png").convert("RGBA")
    lw = 860
    logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    y0 = 360
    im.paste(logo, ((W - lw) // 2, y0), logo)
    d = ImageDraw.Draw(im)
    it = font("libre_baskerville/LibreBaskerville-Italic[wght].ttf", 30)
    centred(d, y0 + logo.height + 54, "A story of a light that went out, and a man who wrote it down.", it, AMBER)
    if with_credit:
        sm = font("source_sans_3/SourceSans3[wght].ttf", 19, 400)
        centred(d, H - 64, "A game by Daniel Yanchev   ·   Godot Engine   ·   Narration voice: elevenlabs.io", sm, GREY,
                tracking=1)
    im.save(out)


def place_card(out: Path) -> None:
    im = Image.new("RGB", (W, H), WARM_BLACK)
    d = ImageDraw.Draw(im)
    caps = font("libre_baskerville/LibreBaskerville[wght].ttf", 40)
    it = font("libre_baskerville/LibreBaskerville-Italic[wght].ttf", 28)
    centred(d, 488, "NORTH POINT LIGHT", caps, CREAM, tracking=12)
    centred(d, 552, "Outer Hebrides.  The night of the fourteenth of November, 1971.", it, AMBER)
    im.save(out)


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    title_card(out / "card_title.png", with_credit=True)
    title_card(out / "card_title_clean.png", with_credit=False)
    place_card(out / "card_place.png")
    print("CARDS_RESULT ok", out)


if __name__ == "__main__":
    main()
