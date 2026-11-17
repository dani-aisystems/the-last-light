"""Mean luminance of a named crop in a capture (audit Stages B and S: the stair door's brightness).

    tools/py projects/games/last_light/blender/measure_luma.py IMAGE.png [IMAGE2.png ...] [--crop door]

Luminance is Rec. 709 weights on the sRGB-encoded values (0..1), averaged over the crop: the measure the
audit plan's 0.10 to 0.14 target for the door in `cu_door` was set in. Crops are fractions of the image
(x0, y0, x1, y1), so 1920x1080 and 1920x1205 captures of the same view share them.
"""
import argparse
import json

import numpy as np
from PIL import Image

CROPS = {
    # cu_door (stair door shut, camera 0.2 m off centre at 1.65 m): the leaf inside its trim, above the
    # dialogue panel's top edge. Set on b1_t060_cu_door.png (2026-11-16).
    "door": (0.375, 0.04, 0.64, 0.76),
}


def luma(path, crop):
    im = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
    h, w = im.shape[:2]
    x0, y0, x1, y1 = crop
    c = im[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
    y = 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]
    return float(y.mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--crop", default="door", choices=sorted(CROPS))
    a = ap.parse_args()
    for p in a.images:
        print("LUMA", json.dumps({"image": p, "crop": a.crop, "mean": round(luma(p, CROPS[a.crop]), 4)}))


if __name__ == "__main__":
    main()
