"""Render the reference comparison views (REFERENCE_SPEC.md) of the watch room and lighthouse.

  tools/bl projects/games/last_light/blender/last_light_vNNN.blend -P projects/games/last_light/blender/review_views.py \
      -- --out renders/last_light/blender_vNNN --res 960 [--views plan,iso,fp_desk,fp_power,fp_console,fp_gen,ext]

plan = R1 (top-down, ceiling hidden), iso = R2 (cutaway from the south-west), fp_* = R3-style eye-level views.
Lighting is a review rig: warm interior points at the real lamp positions + a cold blue world.
Geometry/proportion/material check only; the game's lighting is judged in Godot captures.
"""

import argparse
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "scripts"))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from lib.bl_args import parse  # noqa: E402
from lib.safe_paths import ensure_allowed  # noqa: E402

F = 20.0


def dirv(bearing):
    b = math.radians(bearing)
    return Vector((math.sin(b), math.cos(b), 0))


def look(cam, frm, to):
    cam.location = frm
    cam.rotation_euler = (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()


def eye(bearing_from, dist_from, toward_bearing, toward_dist, z_from=1.65, z_to=1.0):
    return (dirv(bearing_from) * dist_from + Vector((0, 0, F + z_from)),
            dirv(toward_bearing) * toward_dist + Vector((0, 0, F + z_to)))


def lens_for_vfov(vfov_deg, aspect=16 / 9, sensor=36.0):
    """Blender focal length (horizontal sensor fit) matching a Godot vertical FOV at 16:9."""
    hfov = 2 * math.atan(math.tan(math.radians(vfov_deg) / 2) * aspect)
    return sensor / 2 / math.tan(hfov / 2)


VIEWS = {
    # name: (from, to, lens, cutaway). The fp_ceiling/cu_* views mirror godot/scripts/capture_fp.gd exactly.
    "plan": ((0, 0, F + 13.0), (0, 0.001, F), 22, True),
    "iso": ((-6.5, -7.0, F + 8.5), (0.2, 0.4, F + 0.6), 24, True),
    "fp_desk": (*eye(180, 0.2, 20, 3.0, 1.62, 1.05), 18, False),      # R3: from the desk chair area, looking N/NE
    "fp_power": (*eye(80, 0.6, -75, 3.0, 1.65, 1.2), 20, False),
    "fp_console": (*eye(-110, 0.5, 78, 3.0, 1.65, 0.95), 20, False),
    "fp_gen": (*eye(30, 0.8, -140, 3.0, 1.65, 0.9), 20, False),
    "fp_stair": (*eye(-10, 1.0, 170, 3.0, 1.65, 1.0), 20, False),
    "fp_ceiling": (*eye(200, 0.7, 30, 1.9, 1.6, 3.05), lens_for_vfov(80), False),
    "cu_lamp": (*eye(62, 2.0, 62, 3.25, 1.85, 2.05), lens_for_vfov(55), False),
    "cu_optic": (*eye(20, 1.3, 45, 2.78, 1.5, 1.25), lens_for_vfov(55), False),
    "cu_console": (*eye(78, 1.75, 78, 2.9, 1.6, 0.95), lens_for_vfov(50), False),
    "cu_power": (*eye(-80, 1.4, -80, 3.0, 1.6, 1.2), lens_for_vfov(62), False),
    "cu_window": (*eye(0, 1.4, 0, 3.42, 1.65, 1.75), lens_for_vfov(55), False),
    "cu_door": (*eye(170, 0.2, 170, 2.0, 1.65, 1.1), lens_for_vfov(55), False),
    "cu_shelf": (*eye(128, 1.55, 128, 3.0, 1.6, 1.15), lens_for_vfov(55), False),
    "cu_desk_l": (*eye(-20, 1.85, -11, 2.5, 1.25, 0.82), lens_for_vfov(45), False),
    "cu_desk_r": (*eye(28, 2.1, 16, 2.71, 1.4, 0.85), lens_for_vfov(45), False),
    "cu_chart": (*eye(3, 1.95, 2.3, 2.48, 1.6, 0.78), lens_for_vfov(50), False),
    "cu_chair": (*eye(34, 1.08, 1.7, 1.73, 1.5, 0.6), lens_for_vfov(55), False),
    "cu_radio": (*eye(-4, 1.75, -6, 2.75, 1.38, 0.95), lens_for_vfov(50), False),
    "cu_logbook": (*eye(-12, 1.75, -13, 2.5, 1.5, 0.79), lens_for_vfov(42), False),
    # audit Stage B (2026-11-16): matched to capture_fp.gd, for the cabin before/after sheets
    "cu_battery": (*eye(-61.5, 2.05, -61.5, 2.92, 1.62, 1.52), lens_for_vfov(42), False),
    "cu_west": (*eye(-62, 1.2, -62, 3.0, 1.6, 1.75), lens_for_vfov(62), False),      # lamp 0, diagram, charger, jamb
    "cu_coat": (*eye(149, 1.0, 150, 2.75, 1.55, 1.05), lens_for_vfov(55), False),
    "cu_door_top": (*eye(170, 1.75, 170, 2.6, 1.85, 2.0), lens_for_vfov(32), False),
    "cu_wheel": (*eye(176, 1.1, 177, 2.6, 1.15, 1.05), lens_for_vfov(50), False),     # handwheel and both dogs
    "cu_bowl": (*eye(-140, 0.7, -157, 1.56, 0.95, 0.52), lens_for_vfov(40), False),      # audit A5: fuel filter and sediment bowl
    "cu_phone": (*eye(20, 2.2, 15, 2.95, 1.3, 0.8), lens_for_vfov(40), False),       # mug, ashtray, phone, binoculars
    "ext": ((24, -38, 12), (0, 0, 17), 40, False),
    # audit Stage S (2026-11-16): the stairwell. Use with --door_open (and --dogs_up for the latch shots).
    "pp_door": (*eye(170, 1.114, 170, 2.846, 1.65, 0.65), lens_for_vfov(60), False),  # capture pp_door!pitch_m30
    "cu_landing": (*eye(163, 1.5, 172, 3.05, 1.6, 0.55), lens_for_vfov(60), False),   # into the housing from the room
    "in_hatch": (*eye(160.05, 2.894, 175.97, 2.886, 1.65, -1.5), lens_for_vfov(70), False),   # on the landing, looking down
    "plan_hatch": (*eye(174.0, 2.875, 174.05, 2.875, 2.05, -3.0), lens_for_vfov(80), False),   # straight down the hatch
    "low_ladder": (*eye(203, 2.3, 176, 2.75, -1.45, -2.3), lens_for_vfov(70), False),  # service landing: ladder foot
    "low_engine": (*eye(150, 2.6, 196, 1.6, -1.5, -2.2), lens_for_vfov(70), False),    # drums, engine-room door
}


DOG_LIFT_DEG = -78.0     # station.gd DOOR_DOG_LIFT: the levers swing up off their wedges, toward the leaf centre
DOOR_OPEN_DEG = -105.0   # station.gd: the leaf's open angle about its hinge (local Z here, Y in Godot)


def pose_stair_door(open_, dogs_up):
    """Stage S: pose the stair door as Godot does: the dogs about their pivots, then the leaf (with its
    handwheel, dogs and collider) about the hinge."""
    from mathutils import Matrix
    door = bpy.data.objects.get("PT_stair_door")
    if door is None:
        return
    if dogs_up:
        for i in range(2):
            d = bpy.data.objects.get(f"PT_stair_dog_{i}")
            if d:
                d.matrix_world = d.matrix_world @ Matrix.Rotation(math.radians(DOG_LIFT_DEG), 4, "Z")
    if open_:
        T = door.matrix_world @ Matrix.Rotation(math.radians(DOOR_OPEN_DEG), 4, "Z") @ door.matrix_world.inverted()
        for o in bpy.data.objects:
            if o.name.startswith(("PT_stair_handwheel", "PT_stair_dog_", "COL_stair_leaf")):
                o.matrix_world = T @ o.matrix_world
        door.matrix_world = T @ door.matrix_world


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--res", type=int, default=960)
    ap.add_argument("--views", default=",".join(VIEWS))
    ap.add_argument("--door_open", action="store_true", help="swing the stair door to its open pose (-105 deg)")
    ap.add_argument("--dogs_up", action="store_true", help="lift the stair door's lever dogs")
    a = parse(ap)
    out = ensure_allowed(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    sc.render.resolution_x = a.res
    sc.render.resolution_y = int(a.res * 9 / 16)
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = 0.3
    world = bpy.data.worlds.get("Review") or bpy.data.worlds.new("Review")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.05, 0.07, 0.11, 1)
    bg.inputs[1].default_value = 0.8
    sc.world = world
    for o in bpy.data.objects:
        if o.name.startswith("COL_"):
            o.hide_render = True
    pose_stair_door(a.door_open, a.dogs_up)
    cam_data = bpy.data.cameras.new("ReviewCam")
    cam = bpy.data.objects.new("ReviewCam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    # warm lights at the real lamp empties, cold moon
    for o in list(bpy.data.objects):
        if o.name.startswith("LIGHT_") and o.name != "LIGHT_lamp":
            ld = bpy.data.lights.new("Rev_" + o.name, "POINT")
            ld.energy = 90.0 if "desk" in o.name else 45.0
            ld.color = (1.0, 0.72, 0.45)
            ld.shadow_soft_size = 0.08
            lo = bpy.data.objects.new("Rev_" + o.name, ld)
            lo.location = o.matrix_world.translation
            sc.collection.objects.link(lo)
    fill = bpy.data.lights.new("RevFill", "POINT")
    fill.energy = 120.0
    fill.color = (0.9, 0.8, 0.7)
    fo = bpy.data.objects.new("RevFill", fill)
    fo.location = (0, 0, F + 2.6)
    sc.collection.objects.link(fo)
    sun = bpy.data.lights.new("RevMoon", "SUN")
    sun.energy = 1.2
    sun.color = (0.6, 0.7, 0.9)
    so = bpy.data.objects.new("RevMoon", sun)
    so.rotation_euler = (math.radians(55), 0, math.radians(160))
    sc.collection.objects.link(so)
    cutaway_hide = [o for o in bpy.data.objects if o.name.startswith(("SM_RoomCeiling", "SM_Lantern", "SM_Room_SteelRust", "SM_RoomPipes", "PT_optic_gear"))
                    or (o.users_collection and o.users_collection[0].name == "ASSET_lighthouse")]
    for name in a.views.split(","):
        frm, to, lens, cut = VIEWS[name]
        cam_data.lens = lens
        cam_data.clip_start = 0.05
        for o in cutaway_hide:
            o.hide_render = cut
        look(cam, frm, to)
        sc.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)
    print("REVIEW_RESULT", out)


if __name__ == "__main__":
    main()
