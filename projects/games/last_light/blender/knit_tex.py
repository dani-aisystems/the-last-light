"""THE LAST LIGHT · audit Stage P (4.1): the keeper's cloth textures, tileable, for body.py and hands.py.

One navy (Daniel, 2026-11-17, DECISIONS Q19): the guernsey matches the chair's gansey, whose knit is drawn by
documents.knit() into the props atlas. That function is not edited; its output is sampled here and its mean
colour becomes the target, so the body and the sleeves follow the chair if it ever changes.

Sets (OpenGL normal maps; roughness as a greyscale map):
  T_LL_Knit_{albedo,normal,rough}   1024 px, stockinette: 32 stitch columns x 32 rows a tile (KNIT_TILE m)
  T_LL_Rib_{albedo,normal,rough}    512 px, 2x2 rib for welts, cuffs and the neckband (RIB_TILE m)
  T_LL_Darn_albedo                  1024 px, the knit in a bluer, newer wool (canon: cuffs repaired)
  T_LL_Twill_{albedo,normal}        512 px, the trousers' wool twill

  tools/py projects/games/last_light/blender/knit_tex.py      -> blender/textures/cloth/*.png
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "textures" / "cloth"
sys.path.insert(0, str(HERE))
import documents  # noqa: E402  (PIL only; its main() is guarded)

KNIT_TILE = 32 * 10 / 12 / 100       # m: 32 stitches at 12 stitches per 10 cm (a guernsey's close gauge)
RIB_TILE = 0.08                       # m: 16 rib columns (8 ribs) across 512 px
TWILL_TILE = 0.06
TROUSERS = (75, 71, 63)               # body.py TROUSERS #4B473F


def chair_mean():
    """The chair gansey's mean colour (sRGB 0-255), from documents.knit as the atlas draws it."""
    a = np.asarray(documents.knit(400, 320), dtype=np.float64)
    return a.reshape(-1, 3).mean(0)


def _blur_wrap(a, r):
    """Box blur with wrap-around (keeps a tile seamless)."""
    out = a.copy()
    for ax in (0, 1):
        acc = np.zeros_like(out)
        for k in range(-r, r + 1):
            acc += np.roll(out, k, axis=ax)
        out = acc / (2 * r + 1)
    return out


def _noise(n, r, seed):
    rnd = np.random.default_rng(seed)
    a = _blur_wrap(rnd.standard_normal((n, n)), r)
    return (a - a.mean()) / (a.std() + 1e-9)


def _leg(u, v, cx, ang, a, b):
    """A slanted elliptical strand centred at (cx, 0.5) of a stitch cell: height 0..1."""
    du, dv = u - cx, v - 0.5
    c, s = np.cos(ang), np.sin(ang)
    x, y = c * du + s * dv, -s * du + c * dv
    r2 = (x / a) ** 2 + (y / b) ** 2
    return np.sqrt(np.clip(1.0 - r2, 0.0, 1.0))


def stockinette(n, cols, rows, seed):
    """Height field of V stitches (two slanted legs per cell), seamless, with per-stitch jitter."""
    y, x = np.mgrid[0:n, 0:n].astype(np.float64)
    cw, rh = n / cols, n / rows
    ci, ri = np.floor(x / cw), np.floor(y / rh)
    u, v = x / cw - ci, y / rh - ri
    rnd = np.random.default_rng(seed)
    jit = rnd.uniform(-0.04, 0.04, (rows, cols))
    lift = rnd.uniform(0.85, 1.0, (rows, cols))
    j = jit[ri.astype(int) % rows, ci.astype(int) % cols]
    k = lift[ri.astype(int) % rows, ci.astype(int) % cols]
    # v runs down the image: the left leg leans in toward the bottom (a V, legs meeting below), fat enough
    # that neighbouring stitches nearly touch, as relaxed stockinette does
    h = np.maximum(_leg(u, v, 0.28 + j, -0.50, 0.25, 0.62), _leg(u, v, 0.72 + j, 0.50, 0.25, 0.62)) * k
    return h


def rib(n, ribs, rows, seed):
    """2x2 rib: two knit columns standing proud, two purl columns sunk and bumpy across."""
    cols = ribs * 4
    h = stockinette(n, cols, rows, seed)
    y, x = np.mgrid[0:n, 0:n].astype(np.float64)
    col = np.floor(x / (n / cols)).astype(int) % 4
    purl = (col >= 2)
    v = (y / (n / rows)) % 1.0
    bump = 0.35 + 0.25 * np.cos(2 * np.pi * v)           # purl loops read as horizontal bars
    return np.where(purl, bump * 0.55, 0.25 + 0.75 * h)


def twill(n, seed):
    y, x = np.mgrid[0:n, 0:n].astype(np.float64)
    period = n / 64
    h = 0.5 + 0.5 * np.sin(2 * np.pi * (x + y) / period)   # the diagonal wale
    return np.clip(h + 0.15 * _noise(n, 2, seed), 0, 1)


def normal_gl(h, strength):
    """OpenGL tangent-space normal (green up) from a seamless height field."""
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    nx, ny, nz = -dx * strength, dy * strength, np.ones_like(h)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5


def albedo(h, base, seed, fuzz=0.06, shade=(0.62, 0.5)):
    """Base colour shaded by the height (deep = dark), plus a wool fuzz; normalised so the MEAN is base."""
    n = h.shape[0]
    f = shade[0] + shade[1] * h + fuzz * _noise(n, 1, seed)
    col = np.asarray(base, dtype=np.float64)[None, None, :] * f[..., None]
    col *= np.asarray(base, dtype=np.float64) / col.reshape(-1, 3).mean(0)
    return np.clip(col, 0, 255)


def save_rgb(a, name):
    Image.fromarray(np.clip(a * (255.0 if a.max() <= 1.0001 else 1.0), 0, 255).astype(np.uint8), "RGB").save(OUT / name)


def save_grey(a, name):
    Image.fromarray(np.clip(a * 255.0, 0, 255).astype(np.uint8), "L").save(OUT / name)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    navy = chair_mean()
    darn = navy * np.array([1.10, 1.14, 1.22])            # bluer, newer wool (documents.knit's darn: (62, 76, 116))
    k = stockinette(1024, 32, 32, 7)
    save_rgb(albedo(k, navy, 1), "T_LL_Knit_albedo.png")
    save_rgb(normal_gl(k, 6.0), "T_LL_Knit_normal.png")
    save_grey(0.80 + 0.12 * (1.0 - k), "T_LL_Knit_rough.png")
    save_rgb(albedo(k, darn, 2, fuzz=0.04), "T_LL_Darn_albedo.png")
    r = rib(512, 8, 12, 11)
    save_rgb(albedo(r, navy, 3), "T_LL_Rib_albedo.png")
    save_rgb(normal_gl(r, 7.0), "T_LL_Rib_normal.png")
    save_grey(0.80 + 0.12 * (1.0 - r), "T_LL_Rib_rough.png")
    t = twill(512, 5)
    save_rgb(albedo(t, TROUSERS, 4, fuzz=0.05, shade=(0.85, 0.3)), "T_LL_Twill_albedo.png")
    save_rgb(normal_gl(t, 1.5), "T_LL_Twill_normal.png")
    res = {"navy_mean": [round(c, 1) for c in navy], "hex": "#%02X%02X%02X" % tuple(int(round(c)) for c in navy),
           "files": sorted(p.name for p in OUT.glob("*.png")),
           "tiles_m": {"knit": round(KNIT_TILE, 4), "rib": RIB_TILE, "twill": TWILL_TILE}}
    print("KNIT_RESULT", json.dumps(res))


if __name__ == "__main__":
    main()
