"""THE LAST LIGHT · audit Stage M: blender/measure_horizon.py, the horizon and fog metrics (H1, H3, H5, H6).

Synthetic images with a known horizon: the row mapping, step detection, the strip's robustness to objects,
the two-camera comparison, the frame-series metric and the camera sidecar lookup.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "projects" / "games" / "last_light" / "blender"))
import measure_horizon as mh  # noqa: E402

W, H = 1920, 1080


def render(fov, pitch, fn, w=W, h=H):
    """An image whose every pixel is fn(elevation of its row at the centre column)."""
    rows = np.array([fn(mh.elev_of(y + 0.5, h, fov, pitch)) for y in range(h)], dtype=np.float64)
    a = np.repeat(rows[:, None], w, axis=1)
    return np.clip(a, 0, 255)


def test_row_mapping_roundtrip_and_horizon():
    for fov, pitch in [(72.0, 0.0), (60.0, -10.0), (10.0, -3.0), (40.0, 7.5)]:
        f = mh.focal_px(H, fov)
        assert mh.row_of(0.0, H, fov, pitch) == pytest.approx(H / 2 + f * math.tan(math.radians(pitch)))
        for e in (-4.0, -0.5, 0.0, 1.0, 3.0):
            assert mh.elev_of(mh.row_of(e, H, fov, pitch), H, fov, pitch) == pytest.approx(e)
    # a level camera: the horizon is the middle row; looking down puts it higher in the frame
    assert mh.row_of(0.0, H, 72.0, 0.0) == pytest.approx(H / 2)
    assert mh.row_of(0.0, H, 72.0, -5.0) < H / 2


def test_band_finds_the_horizon_line():
    fov, pitch = 10.0, -3.0
    lum = render(fov, pitch, lambda e: 110.0 if e > 0 else 70.0)        # a hard line at the true horizon
    r = mh.band_metric(lum, fov, pitch, mh.parse_strip(None, W))
    assert r["max_step"] == pytest.approx(40.0)
    assert abs(r["at_row"] + 0.5 - r["horizon_row"]) <= 1.0
    assert abs(r["at_elev_deg"]) < 0.02
    assert r["second_step"] == pytest.approx(0.0)


def test_band_soft_horizon_passes_h1():
    fov, pitch = 10.0, -3.0
    # 70 -> 110 spread over 2 degrees: about 0.18/255 per row at 10 degrees across 1080 rows
    lum = render(fov, pitch, lambda e: 90.0 + 20.0 * math.tanh(e / 0.5))
    r = mh.band_metric(lum, fov, pitch, mh.parse_strip(None, W))
    assert r["max_step"] < 4.0


def test_strip_ignores_a_minority_object():
    fov, pitch = 40.0, -2.0
    lum = render(fov, pitch, lambda e: 90.0 + 10.0 * math.tanh(e / 1.0))
    lum[:, 300:600] = 5.0                       # a dark mullion over 16 % of the columns
    clean = render(fov, pitch, lambda e: 90.0 + 10.0 * math.tanh(e / 1.0))
    a = mh.row_values(lum, *mh.parse_strip(None, W))
    b = mh.row_values(clean, *mh.parse_strip(None, W))
    assert np.max(np.abs(a - b)) < 1e-9


def test_band_off_image_is_reported_not_crashed():
    lum = render(40.0, 30.0, lambda e: 50.0)    # looking 30 degrees up: the horizon is below the frame
    r = mh.band_metric(lum, 40.0, 30.0, mh.parse_strip(None, W))
    assert r["max_step"] is None and r["clipped"]


def test_contrast_strips_have_ranges_and_fall_with_distance():
    fov, pitch, eye = 60.0, -10.0, 21.65
    rng = np.random.default_rng(1)
    lum = render(fov, pitch, lambda e: 60.0)
    for y in range(H):
        e = mh.elev_of(y + 0.5, H, fov, pitch)
        if e < 0:
            d = eye / math.tan(math.radians(-e))
            lum[y] += rng.normal(0.0, 20.0 * math.exp(-d / 300.0), W)    # texture that fades with range
    s = mh.contrast_metric(lum, fov, pitch, eye, mh.parse_strip(None, W))
    assert len(s) >= 15
    assert all(x["range_m"] > 0 for x in s)
    assert s[0]["range_m"] > s[-1]["range_m"]                 # the first strip is the farthest
    assert s[0]["std"] < s[-1]["std"]                          # far sea has less contrast than near


def test_compare_two_fovs_on_one_scene():
    # a soft 2-degree horizon (the target look). The 72-degree view has about 13 rows per degree, so a much
    # sharper edge would cost it about 1/255 to row sampling; that is the tool's floor, well under H6's 3/255.
    fn = lambda e: 90.0 + 25.0 * math.tanh(e / 2.0)            # noqa: E731
    a = render(72.0, -1.0, fn)
    b = render(10.0, -3.0, fn)
    r = mh.compare_metric(a, {"fov": 72.0, "pitch_deg": -1.0}, b, {"fov": 10.0, "pitch_deg": -3.0}, deg=3.0)
    assert r["samples"] > 30
    assert r["max_diff"] < 0.5                                 # agree to well within H6's 3/255
    b2 = b + 8.0                                               # a binocular view 8/255 brighter fails H6
    r2 = mh.compare_metric(a, {"fov": 72.0, "pitch_deg": -1.0}, b2, {"fov": 10.0, "pitch_deg": -3.0}, deg=3.0)
    assert r2["max_diff"] > 3.0


def test_series_fade_and_pop():
    fade = mh.series_metric([20.0 + 4.0 * i for i in range(21)])     # 20 frames, 5 % each
    assert fade["max_step_share"] == pytest.approx(0.05)
    pop = mh.series_metric([20.0] * 10 + [100.0] * 10)
    assert pop["max_step_share"] == pytest.approx(1.0) and pop["at_frame"] == 10


def test_series_cli_contrast_and_dark_percentile(tmp_path):
    # a dark 40x20 "hull" on a sea of 60 that brightens with a passing beam (+30) in frame 2
    for i, (hull, beam) in enumerate([(None, 0), (20, 0), (20, 30), (20, 0)]):
        a = np.full((200, 300), 60.0) + beam
        if hull is not None:
            a[100:120, 100 + i * 5:140 + i * 5] = hull + beam      # she drifts 5 px a frame
        Image.fromarray(np.repeat(a[..., None], 3, axis=2).astype(np.uint8)).save(tmp_path / f"s_f{i:02d}.png")
    ns = lambda **k: type("A", (), {"glob": str(tmp_path / "s_f*.png"), "ref": None, "dark_pct": None, **k})()   # noqa: E731
    raw = mh._cmd_series(ns(box="90:95:170:125"))
    assert raw["values"][2] - raw["values"][1] > 20                  # the beam swamps the raw mean
    con = mh._cmd_series(ns(box="115:100:140:120", ref="200:100:240:120"))   # inside the hull in frames 1 to 3
    assert con["values"][1] == pytest.approx(con["values"][2])       # contrast against the sea cancels it
    dark = mh._cmd_series(ns(box="50:50:250:150", dark_pct=2.0))
    assert dark["values"][0] == pytest.approx(0.0) and dark["values"][1] == pytest.approx(-40.0)
    assert dark["values"][3] == pytest.approx(-40.0)                 # the drift does not matter


def test_camera_sidecar_lookup(tmp_path):
    img = tmp_path / "m0_t096_ext_far-dawn.png"
    Image.fromarray(np.full((H, W, 3), 80, np.uint8)).save(img)
    (tmp_path / "m0_cams.json").write_text(json.dumps({img.name: {"fov": 40.0, "pitch_deg": -5.0, "eye": [0, 30, 0]}}))
    (tmp_path / "other_cams.json").write_text(json.dumps({"x.png": {"fov": 1.0, "pitch_deg": 0.0}}))
    cam = mh.find_cam(img)
    assert cam["fov"] == 40.0 and cam["pitch_deg"] == -5.0
    assert mh.find_cam(tmp_path / "nothing_t001_x.png") is None
    out = mh._cmd_band(type("A", (), {"png": [str(img)], "strip": None, "deg": 3.0, "fov": None, "pitch": None,
                                      "eye_y": None})())
    assert out[0]["max_step"] == pytest.approx(0.0) and out[0]["fov"] == 40.0


def test_flat_finds_a_pale_flat_patch_and_ignores_texture():
    """Audit E3: a smooth pale blob on a textured sea counts; the textured sea alone does not."""
    rng = np.random.default_rng(3)
    h, w, fov, pitch = 1205, 1920, 10.0, -3.0
    lum = 120.0 + rng.normal(0.0, 3.0, (h, w))           # textured sea everywhere
    r0 = int(mh.row_of(-1.0, h, fov, pitch)); r1 = int(mh.row_of(-2.4, h, fov, pitch))
    base = mh.flat_metric(lum, fov, pitch, (300, 1150))
    assert base["patch_pct"] < 0.1 and base["longest_run_px"] < 5
    mid = (r0 + r1) // 2
    lum[mid - 10:mid + 10, 500:800] = 132.0                # a flat patch 12/255 brighter, 300 px long
    got = mh.flat_metric(lum, fov, pitch, (300, 1150))
    assert got["rows"] == [r0, r1] or abs(got["rows"][0] - r0) <= 1
    assert got["patch_pct"] > 1.0 and got["longest_run_px"] >= 280


def test_flat_cli(tmp_path):
    h, w = 1205, 1920
    img = Image.fromarray(np.full((h, w, 3), 100, np.uint8))
    p = tmp_path / "x_t001_a.png"
    img.save(p)
    (tmp_path / "x_cams.json").write_text(json.dumps({"x_t001_a.png": {"fov": 10.0, "pitch_deg": -3.0, "size": [w, h]}}))
    out = mh.main(["flat", str(p), "--strip", "300:1150"])
    assert out == 0

