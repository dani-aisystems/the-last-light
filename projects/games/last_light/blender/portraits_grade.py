"""Grade the raw portrait renders into the game's portrait prints (Stage 3C).

  tools/py projects/games/last_light/blender/portraits_grade.py

Reads blender/tex/src/portraits_raw/<id>_<expr>.png (portraits.py, Blender) and writes
godot/assets/portraits/<id>_<expr>.png: a 1971 colour print (warm cast, lifted blacks, slightly lower
saturation, fine grain, soft vignette). Deterministic: the grain is seeded per file.
"""

import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
RAW = HERE / "tex" / "src" / "portraits_raw"
OUT = HERE.parent / "godot" / "assets" / "portraits"


def grade(src: Path, dst: Path) -> None:
    im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    h, w, _ = im.shape
    lum = im @ np.array([0.3, 0.59, 0.11], dtype=np.float32)
    im = lum[..., None] + (im - lum[..., None]) * 0.82                  # a little less saturated
    im = im * np.array([0.94, 0.92, 0.84]) + np.array([14, 10, 8])      # warm cast, lifted blacks
    yy, xx = np.mgrid[0:h, 0:w]
    dx, dy = (xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)
    im *= (1 - 0.22 * (dx * dx + dy * dy))[..., None]                   # soft vignette
    rng = np.random.default_rng(random.Random(src.stem).randint(0, 2 ** 31))
    im += rng.normal(0, 4.5, (h, w, 1))                                 # fine print grain
    out = Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.35))
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, optimize=True)


def main() -> None:
    done = []
    for src in sorted(RAW.glob("*.png")):
        grade(src, OUT / src.name)
        done.append(src.name)
    print("GRADE_RESULT", done)


if __name__ == "__main__":
    main()
