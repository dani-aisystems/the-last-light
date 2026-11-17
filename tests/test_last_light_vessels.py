"""THE LAST LIGHT · audit Stage E1: the vessel models (projects/games/last_light/blender/vessels.py).

Two layers:
- the generator itself (always runs; no Blender): every vessel is closed, wound outward, inside its triangle
  budget and ship_view2.gd's DIMS, with one non-overlapping UV atlas and the light empties the game will read;
- the exported GLBs as Godot will read them (exports/ is gitignored, so these skip when the files are absent):
  they load, normals agree with the winding, no shell is inside out, 4 to 6k triangles, one material, one UV set,
  1024 textures, bow -Z and port -X, clean node names.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "projects" / "games" / "last_light" / "blender"))
import vessels  # noqa: E402

IDS = list(vessels.VESSELS)


@pytest.fixture(scope="module", params=IDS)
def built(request):
    vid = request.param
    return vid, vessels.checks(vessels.make(vid), vid)


def test_generator_closed_and_outward(built):
    vid, r = built
    assert r["nonmanifold"] == 0, vid
    assert r["inconsistent"] == 0, vid
    assert r["inward_shells"] == 0, vid


def test_generator_budget_and_dims(built):
    vid, r = built
    assert vessels.TRI_MIN <= r["tris"] <= vessels.TRI_MAX, (vid, r["tris"])
    kind = vessels.VESSELS[vid]["kind"]
    if kind:
        dx, dy, dz = vessels.DIMS[kind]
        assert r["beam"] <= dx + 1e-6 and r["loa"] <= dz + 1e-6 and r["rail_max"] <= dy + 1e-6, (vid, r)


def test_generator_uvs_and_names(built):
    vid, r = built
    assert r["uv_in_unit"] and r["island_overlaps"] == 0, vid
    assert not r["empties_missing"] and not r["hint_suffix_names"], vid
    assert r["result"] == "PASS", (vid, r["fails"])


def test_mapping_covers_every_kind():
    """Every kind ship_view2.gd knows today gets a file of its own name."""
    served = {v["kind"] for v in vessels.VESSELS.values() if v["export"] == "ship_" + str(v["kind"])}
    assert served == set(vessels.DIMS)


@pytest.mark.parametrize("vid", IDS)
def test_exported_glb(vid):
    path = vessels.latest_glb(vessels.VESSELS[vid]["export"])
    if path is None:
        pytest.skip("no export yet for %s (exports/ is gitignored; run the Stage E1 chain)" % vid)
    r = vessels.glb_checks(path, vid)
    assert r["result"] == "PASS", (vid, r["file"], r["fails"])
    assert r["normals_agree_winding"] >= 0.995 and r["inward_shells"] == 0
    assert r["materials"] == 1 and r["material_names"] == ["M_Vessel_" + vessels.VESSELS[vid]["Id"]]
