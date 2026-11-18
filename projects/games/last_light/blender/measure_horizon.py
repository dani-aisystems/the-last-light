"""THE LAST LIGHT · audit Stage M: horizon and fog metrics on game captures (host Python: tools/py).

The acceptance tests of docs/last_light/audit-2026-11/14_stageM_ocean_boundary_fog.md section H, measured on
the 8-bit PNGs that scripts/capture_fp.gd writes. Each capture run also writes <capture>_cams.json (the
camera of every shot: vertical fov, pitch, yaw, roll, eye), which is how the horizon row is found:
for a camera with no roll the true horizon (elevation 0) is the row  y_h = H/2 + f·tan(pitch),
f = (H/2) / tan(fov/2), and elevation e at the centre column is the row  y(e) = H/2 - f·tan(e - pitch).

A row's value is the mean of the middle half (25th to 75th percentile) of its luma across the strip, so a
mullion, a mast or rain covering a minority of the columns does not move it. Luma: Rec. 709 on the 8-bit
values (the same as the Stage 0 measurements in section A.2).

  band PNG... [--strip x0:x1] [--deg 3]      H1: largest adjacent-row step from +deg to -deg about the horizon
  contrast PNG [--strip x0:x1]               H3: luma std-dev in 1-degree strips below the horizon, with range (m)
  compare A B [--deg 3]                      H6: two cameras on one bearing (e.g. binoculars and the naked eye),
                                             row values resampled by elevation over their common bearings
  series GLOB --box x0:y0:x1:y1 [--ref ...]  H5: a region's luma per frame (minus a reference patch's: the
             [--dark-pct P]                  contrast; or its P-th percentile minus its median, for a dark
                                             hull in a swaying view); steps as a share of the total change
Camera overrides for files without a sidecar: --fov --pitch [--eye-y]. Output is JSON on stdout.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image


# ------------------------------------------------------------------ geometry and image helpers

def luma(path_or_img) -> np.ndarray:
    img = path_or_img if isinstance(path_or_img, Image.Image) else Image.open(path_or_img)
    a = np.asarray(img.convert("RGB")).astype(np.float64)
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def focal_px(h: int, fov_deg: float) -> float:
    return (h / 2.0) / math.tan(math.radians(fov_deg) / 2.0)


def row_of(elev_deg: float, h: int, fov_deg: float, pitch_deg: float) -> float:
    """Image row (0 = top, may be fractional or off the image) of elevation elev_deg at the centre column."""
    return h / 2.0 - focal_px(h, fov_deg) * math.tan(math.radians(elev_deg - pitch_deg))


def elev_of(row: float, h: int, fov_deg: float, pitch_deg: float) -> float:
    return pitch_deg + math.degrees(math.atan((h / 2.0 - row) / focal_px(h, fov_deg)))


def row_values(lum: np.ndarray, x0: int, x1: int) -> np.ndarray:
    """Per row: the mean of the middle half (25th-75th percentile) of the strip's luma."""
    s = np.sort(lum[:, x0:x1], axis=1)
    n = s.shape[1]
    lo, hi = n // 4, max(n // 4 + 1, (3 * n) // 4)
    return s[:, lo:hi].mean(axis=1)


def parse_strip(s: str | None, w: int) -> tuple[int, int]:
    if not s:
        m = int(round(w * 0.05))
        return m, w - m
    a, b = s.split(":")
    return max(0, int(a)), min(w, int(b))


# ------------------------------------------------------------------ camera sidecar

_PREFIX = re.compile(r"^(.*?)_(?:t\d{3}_|menu$|end$|tmenu)")


def find_cam(png: str | Path) -> dict | None:
    p = Path(png)
    m = _PREFIX.match(p.stem)
    cands = [p.parent / f"{m.group(1)}_cams.json"] if m else []
    cands += sorted(p.parent.glob("*_cams.json"))
    for c in cands:
        if c.exists():
            try:
                d = json.loads(c.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if p.name in d:
                return d[p.name]
    return None


def camera(png, args) -> dict:
    cam = find_cam(png) or {}
    if getattr(args, "fov", None) is not None:
        cam["fov"] = args.fov
    if getattr(args, "pitch", None) is not None:
        cam["pitch_deg"] = args.pitch
    if getattr(args, "eye_y", None) is not None:
        cam["eye"] = [0.0, args.eye_y, 0.0]
    if "fov" not in cam or "pitch_deg" not in cam:
        raise SystemExit(f"{png}: no camera in a *_cams.json sidecar; pass --fov and --pitch")
    return cam


# ------------------------------------------------------------------ metrics

def band_metric(lum: np.ndarray, fov: float, pitch: float, strip: tuple[int, int], deg: float = 3.0) -> dict:
    """H1: the largest step between adjacent row values from +deg to -deg about the horizon."""
    h = lum.shape[0]
    rv = row_values(lum, *strip)
    y_top = int(math.floor(row_of(deg, h, fov, pitch)))
    y_bot = int(math.ceil(row_of(-deg, h, fov, pitch)))
    y0, y1 = max(0, y_top), min(h - 1, y_bot)
    out = {"horizon_row": round(row_of(0.0, h, fov, pitch), 1), "rows": [y0, y1], "clipped": y_top < 0 or y_bot > h - 1}
    if y1 - y0 < 2:
        out.update({"max_step": None, "note": "band off the image"})
        return out
    seg = rv[y0:y1 + 1]
    d = np.abs(np.diff(seg))
    order = np.argsort(d)[::-1]
    k = int(order[0])
    out.update({
        "max_step": round(float(d[k]), 2),
        "at_row": y0 + k, "at_elev_deg": round(elev_of(y0 + k + 0.5, h, fov, pitch), 3),
        "across": [round(float(seg[k]), 1), round(float(seg[k + 1]), 1)],
        "second_step": round(float(d[int(order[1])]), 2) if len(order) > 1 else None,
        "second_at_row": y0 + int(order[1]) if len(order) > 1 else None,
        "band_range": [round(float(seg.min()), 1), round(float(seg.max()), 1)],
    })
    return out


def contrast_metric(lum: np.ndarray, fov: float, pitch: float, eye_y: float | None, strip: tuple[int, int],
                    start_deg: float = 0.5, step_deg: float = 1.0, stop_deg: float = 30.0) -> list[dict]:
    """H3: luma standard deviation in elevation strips below the horizon, with the sea range they cover."""
    h = lum.shape[0]
    out = []
    e = -start_deg
    while e > -stop_deg:
        ya, yb = row_of(e, h, fov, pitch), row_of(e - step_deg, h, fov, pitch)
        r0, r1 = int(math.ceil(ya)), int(math.floor(yb))
        if r0 >= h:
            break
        r0, r1 = max(0, r0), min(h, r1)
        if r1 - r0 >= 1:
            block = lum[r0:r1, strip[0]:strip[1]]
            mid = e - step_deg / 2.0
            rng = (eye_y / math.tan(math.radians(-mid))) if eye_y and mid < 0 else None
            out.append({"elev_deg": round(mid, 2), "range_m": round(rng, 1) if rng else None,
                        "std": round(float(block.std()), 2), "mean": round(float(block.mean()), 1), "rows": [r0, r1]})
        e -= step_deg
    return out


def compare_metric(lum_a: np.ndarray, cam_a: dict, lum_b: np.ndarray, cam_b: dict, deg: float = 3.0,
                   step: float = 0.1) -> dict:
    """H6: row values of two cameras on one bearing, resampled by elevation over their common bearings."""
    def half_h(lum, cam):
        h, w = lum.shape
        return math.degrees(math.atan(math.tan(math.radians(cam["fov"]) / 2.0) * w / h))
    common = min(half_h(lum_a, cam_a), half_h(lum_b, cam_b))

    def sample(lum, cam):
        h, w = lum.shape
        f = focal_px(h, cam["fov"])
        dx = f * math.tan(math.radians(common))
        rv = row_values(lum, max(0, int(w / 2 - dx)), min(w, int(w / 2 + dx)))
        es = np.arange(-deg, deg + 1e-9, step)
        ys = np.array([row_of(e, h, cam["fov"], cam["pitch_deg"]) for e in es])
        ok = (ys >= 0) & (ys <= h - 1)
        return es, np.where(ok, np.interp(ys, np.arange(h), rv), np.nan)
    es, va = sample(lum_a, cam_a)
    _, vb = sample(lum_b, cam_b)
    diff = np.abs(va - vb)
    good = ~np.isnan(diff)
    yaw_gap = abs(((cam_a.get("yaw_deg", 0.0) - cam_b.get("yaw_deg", 0.0)) + 180.0) % 360.0 - 180.0)
    if not good.any():
        return {"max_diff": None, "note": "no common elevations on both images", "yaw_gap_deg": round(yaw_gap, 2)}
    k = int(np.nanargmax(diff))
    return {"max_diff": round(float(diff[k]), 2), "at_elev_deg": round(float(es[k]), 2),
            "mean_diff": round(float(np.nanmean(diff)), 2), "samples": int(good.sum()),
            "common_half_bearing_deg": round(common, 2), "yaw_gap_deg": round(yaw_gap, 2)}


def series_metric(values: list[float]) -> dict:
    """H5: per-frame change of a region's luma as a share of its total change (first to last frame)."""
    v = np.asarray(values, dtype=np.float64)
    total = float(v[-1] - v[0])
    steps = np.abs(np.diff(v))
    share = steps / abs(total) if abs(total) > 1e-6 else np.zeros_like(steps)
    k = int(np.argmax(share)) if len(share) else 0
    return {"frames": len(v), "first": round(float(v[0]), 2), "last": round(float(v[-1]), 2),
            "total_change": round(total, 2), "max_step": round(float(steps.max()), 2) if len(steps) else 0.0,
            "max_step_share": round(float(share.max()), 3) if len(share) else 0.0, "at_frame": k + 1,
            "values": [round(float(x), 2) for x in v]}


# ------------------------------------------------------------------ CLI

def _cmd_band(args) -> list:
    res = []
    for p in args.png:
        lum = luma(p)
        cam = camera(p, args)
        r = band_metric(lum, cam["fov"], cam["pitch_deg"], parse_strip(args.strip, lum.shape[1]), args.deg)
        r = {"file": Path(p).name, "fov": cam["fov"], "pitch_deg": round(cam["pitch_deg"], 3), **r}
        if abs(cam.get("roll_deg", 0.0)) > 0.3:
            r["warn"] = f"roll {cam['roll_deg']:.2f} deg: the horizon is tilted"
        res.append(r)
    return res


def _cmd_contrast(args) -> dict:
    lum = luma(args.png)
    cam = camera(args.png, args)
    eye_y = cam["eye"][1] if "eye" in cam else None
    return {"file": Path(args.png).name, "eye_y": eye_y,
            "strips": contrast_metric(lum, cam["fov"], cam["pitch_deg"], eye_y, parse_strip(args.strip, lum.shape[1]))}


def _cmd_compare(args) -> dict:
    a, b = luma(args.a), luma(args.b)
    ca, cb = camera(args.a, argparse.Namespace()), camera(args.b, argparse.Namespace())
    return {"a": Path(args.a).name, "b": Path(args.b).name, **compare_metric(a, ca, b, cb, args.deg)}


def _cmd_series(args) -> dict:
    files = sorted(glob.glob(args.glob))
    if not files:
        raise SystemExit(f"no files match {args.glob}")
    x0, y0, x1, y1 = (int(v) for v in args.box.split(":"))
    ref = [int(v) for v in args.ref.split(":")] if args.ref else None
    vals = []
    for f in files:
        lum = luma(f)
        box = lum[y0:y1, x0:x1]
        if args.dark_pct is not None:    # a swaying view (the binoculars breathe): the darkest few percent of a
            vals.append(float(np.percentile(box, args.dark_pct) - np.median(box)))   # wide window against its
            continue                                                                  # median (a dark hull's contrast)
        v = float(box.mean())
        if ref:          # contrast against a reference patch (e.g. the sea beside the hull): the beam's sweep
            v -= float(lum[ref[1]:ref[3], ref[0]:ref[2]].mean())   # and the swell move both alike
        vals.append(v)
    return {"files": [Path(f).name for f in files], "ref": args.ref, **series_metric(vals)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("band", "contrast"):
        s = sub.add_parser(name)
        s.add_argument("png", nargs="+" if name == "band" else None)
        s.add_argument("--strip")
        s.add_argument("--fov", type=float)
        s.add_argument("--pitch", type=float)
        s.add_argument("--eye-y", type=float, dest="eye_y")
        if name == "band":
            s.add_argument("--deg", type=float, default=3.0)
    s = sub.add_parser("compare")
    s.add_argument("a")
    s.add_argument("b")
    s.add_argument("--deg", type=float, default=3.0)
    s = sub.add_parser("series")
    s.add_argument("glob")
    s.add_argument("--box", required=True)
    s.add_argument("--ref", help="x0:y0:x1:y1 patch subtracted from the box mean (contrast)")
    s.add_argument("--dark-pct", type=float, dest="dark_pct",
                   help="value = this percentile of the box minus its median (a dark object in a swaying view)")
    args = ap.parse_args(argv)
    out = {"band": _cmd_band, "contrast": _cmd_contrast, "compare": _cmd_compare, "series": _cmd_series}[args.cmd](args)
    json.dump(out, sys.stdout, indent=1)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
