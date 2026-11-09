"""THE LAST LIGHT · G2b layer C (Daniel 2026-11-06): tonight's station log, written as the night goes.

Renders, in Callum's hand (Bradley Hand, as documents.py: "small square letters ... like a clerk"):
  godot/assets/docs/log/page_log.png         the 14 November log page, ruled, header only (no rows)
  godot/assets/docs/log/row_<id>.png         one transparent strip per canon row, placed by the manifest
  godot/assets/docs/log/card_<id>.png        a small paper slip for that row (the completion moment), and
  godot/assets/docs/log/card_ink_<id>.png    its ink alone, which the game reveals left to right as written
  godot/assets/docs/log/page_duties.png      the pencil "Tonight" page at the back of the log
  godot/assets/docs/log/duty_<id>.png, sub_<duty>_<sub>.png   pencil strips for every duty line
  godot/assets/docs/log/manifest.json        row positions on the page, strip sizes
The rows and duties come from godot/data/story/chapters.json ("station_log", "duties"), so the game and
these images share one source. Everything is seeded: running it twice gives identical files (unlike the
paper grain in documents.py, which uses Pillow's unseeded noise).

  tools/py projects/games/last_light/blender/log_strips.py
"""
import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from documents import CALLUM, PRINT, PRINTB, INK, PENCIL, PAPER, jitter_text, wrap  # noqa: E402

GODOT = HERE.parent / "godot"
OUT = GODOT / "assets" / "docs" / "log"
W, H = 1500, 1050               # log_page() geometry (documents.py)
Y0, ROW, X_REMARK = 130, 47, 620
COLS = [60, 170, 270, 430, X_REMARK]


def seeded_paper(w, h, seed, tone=PAPER, stains=3):
    """documents.paper(), but with a seeded grain so the files are reproducible."""
    rnd = random.Random(seed)
    rng = np.random.default_rng(seed)
    img = Image.new("RGB", (w, h), tone)
    small = (rng.normal(128, 18, (h // 4, w // 4))).clip(0, 255).astype(np.uint8)
    noise = Image.fromarray(small, "L").resize((w, h), Image.BICUBIC).convert("RGB")
    img = Image.blend(img, noise, 0.06)
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(stains):
        x, y, r = rnd.randint(0, w), rnd.randint(0, h), rnd.randint(40, 160)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(150, 120, 80, 40), width=rnd.randint(2, 6))
    for _ in range(4):
        if rnd.random() < 0.5:
            y = rnd.randint(h // 4, 3 * h // 4)
            d.line([0, y, w, y + rnd.randint(-6, 6)], fill=(0, 0, 0, 18), width=3)
    return img


def page_log():
    img = seeded_paper(W, H, 71)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 46), "NORTHERN LIGHTHOUSE BOARD", font=PRINTB(30), fill=(60, 50, 40), anchor="mm")
    d.text((W // 2, 86), "NORTH POINT LIGHT  ·  STATION LOG  ·  NOVEMBER 1971", font=PRINT(24), fill=(60, 50, 40), anchor="mm")
    d.line([40, Y0, W - 40, Y0], fill=(120, 90, 70), width=2)
    for x, t in zip(COLS, ["Date", "Time", "Wind", "Weather", "Remarks"]):
        d.text((x, Y0 + 10), t, font=PRINTB(20), fill=(90, 70, 55))
        d.line([x - 10, Y0, x - 10, H - 50], fill=(170, 130, 110), width=1)
    for k in range(18):
        y = Y0 + 46 + k * ROW
        d.line([40, y, W - 40, y], fill=(170, 150, 140), width=1)
    return img.filter(ImageFilter.GaussianBlur(0.4))


def row_strip(e, seed):
    """One row as a transparent strip, full page width; returns (image, line count)."""
    f = CALLUM(26)                                   # F15: the 1971 hand (documents.py log_1971 at 26)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines = wrap(probe, e["text"], f, W - 680)
    h = ROW * max(1, len(lines)) + 16
    img = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for x, k, txt in [(60, 0, e["date"]), (170, 1, e["time"]), (270, 2, e["wind"]), (430, 3, e["weather"])]:
        if txt:
            jitter_text(d, (x, 6), txt, f, INK + (255,), seed + k)
    for i, line in enumerate(lines):
        jitter_text(d, (X_REMARK, 6 + i * ROW), line, f, INK + (255,), seed + 4 + i)
    return img.filter(ImageFilter.GaussianBlur(0.4)), len(lines)


def card(e, seed):
    """The row on a torn-edged paper slip: time, then the remark, in a larger hand."""
    f = CALLUM(38)
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    text = f"{e['time']}  {e['text']}"
    lines = wrap(probe, text, f, 1040)
    w = int(max(probe.textlength(l, font=f) for l in lines)) + 80
    h = 56 * len(lines) + 44
    img = seeded_paper(w, h, seed, (236, 228, 205), 1)
    ink = Image.new("RGBA", (w, h), (0, 0, 0, 0))          # the ink alone: the game reveals it as written
    d = ImageDraw.Draw(ink)
    for i, line in enumerate(lines):
        jitter_text(d, (40, 18 + i * 56), line, f, INK + (255,), seed + i)
    rnd = random.Random(seed)
    edge = Image.new("L", (w, h), 0)                       # a soft, slightly irregular deckle edge
    pts = [(0, 3)]
    for x in range(0, w + 10, 10):
        pts.append((min(x, w), rnd.uniform(1, 4)))
    for x in range(w, -10, -10):
        pts.append((max(x, 0), h - rnd.uniform(2, 6)))
    ImageDraw.Draw(edge).polygon(pts, fill=255)
    img.putalpha(edge.filter(ImageFilter.GaussianBlur(1.2)))
    return img.filter(ImageFilter.GaussianBlur(0.3)), ink.filter(ImageFilter.GaussianBlur(0.3))


def page_duties():
    """The back of the log: pencil rough notes. Ruled, a pencilled heading, nothing else."""
    img = seeded_paper(W, H, 1114, (230, 221, 195), 2)
    d = ImageDraw.Draw(img)
    for k in range(19):
        y = 120 + k * 48
        d.line([40, y, W - 40, y], fill=(176, 160, 150), width=1)
    d.line([96, 40, 96, H - 40], fill=(190, 120, 110), width=1)
    jitter_text(d, (118, 70), "Tonight", CALLUM(34), PENCIL, 7)
    return img.filter(ImageFilter.GaussianBlur(0.4))


def pencil_strip(text, size, seed):
    f = CALLUM(size)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    w = int(probe.textlength(text, font=f)) + 24
    img = Image.new("RGBA", (w, size + 22), (0, 0, 0, 0))
    jitter_text(ImageDraw.Draw(img), (8, 6), text, f, PENCIL + (235,), seed)
    return img.filter(ImageFilter.GaussianBlur(0.35))


def main():
    data = json.loads((GODOT / "data" / "story" / "chapters.json").read_text())
    rows = data["station_log"]["1971-11-14"]
    OUT.mkdir(parents=True, exist_ok=True)
    page_log().save(OUT / "page_log.png", optimize=True)
    page_duties().save(OUT / "page_duties.png", optimize=True)
    man = {"page": [W, H], "rows": {}, "duties": {}}
    y = Y0 + 52 - 6
    for i, e in enumerate(rows):
        img, n = row_strip(e, 71 + i * 10)
        img.save(OUT / f"row_{e['id']}.png", optimize=True)
        bg, ink = card(e, 300 + i)
        bg.save(OUT / f"card_{e['id']}.png", optimize=True)
        ink.save(OUT / f"card_ink_{e['id']}.png", optimize=True)
        man["rows"][e["id"]] = {"y": y, "h": img.height}
        y += ROW * max(1, n)
    for c in data["chapters"]:
        for k, dd in enumerate(c.get("duties", [])):
            s = pencil_strip(dd["line"], 30, 500 + k)
            s.save(OUT / f"duty_{dd['id']}.png", optimize=True)
            man["duties"][dd["id"]] = {"w": s.width, "h": s.height, "sub": {}}
            for j, sb in enumerate(dd.get("sub", [])):
                t = pencil_strip(sb["line"], 26, 600 + k * 10 + j)
                t.save(OUT / f"sub_{dd['id']}_{sb['id']}.png", optimize=True)
                man["duties"][dd["id"]]["sub"][sb["id"]] = {"w": t.width, "h": t.height}
    (OUT / "manifest.json").write_text(json.dumps(man, indent=1))
    print("LOG_STRIPS_RESULT", json.dumps({"rows": len(rows), "duties": len(man["duties"]), "out": str(OUT)}))


if __name__ == "__main__":
    main()
