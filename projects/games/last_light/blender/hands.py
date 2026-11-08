"""THE LAST LIGHT · G3b (Daniel 2026-11-07): the keeper's first-person hands.

Callum's hands (character-refs/callum/PROFILE.md §G): skin fair to lightly ruddy, no scars or invented
marks, kept clean; the cuff of a dark navy / charcoal wool guernsey, "cuffs repaired, not replaced".

Source: "Hand  - Realistic" from Blender Studio's Human Base Meshes v1.4.1 (CC0, assets/ASSET_LICENSES.md),
multires applied at level 1 (3,300 verts). It is a LEFT hand hanging fingers-down (-Z), palm to +Y; the right
hand is its mirror. The bundle has no armature, so this script builds one: a hand bone plus three bones per
finger and thumb (16 per hand), joints placed from a slice trace of the mesh (FINGERS below), automatic
weights. Four poses become actions: relaxed, torch (a cylinder grip), compass (a cupped palm), binoculars.

Output collection ASSET_hands: ARM_hand_L / ARM_hand_R with SK_hand_L / SK_hand_R and SM_cuff_L / SM_cuff_R
(parented to the hand bone). Materials M_LL_Skin, M_LL_Guernsey.

  tools/bl -P projects/games/last_light/blender/hands.py -- --new --save [--preview DIR]
"""
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
WS = HERE.parents[3]
sys.path.insert(0, str(WS / "scripts"))
from lib.scene_utils import clear_scene, get_collection, save_versioned, hex_to_linear  # noqa: E402

BUNDLE = WS / "assets/models/human_base_meshes/bundle/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"
SRC_NAME = "Hand  - Realistic"
SKIN = "#C99079"          # fair to lightly ruddy (PROFILE §G), weathered at the knuckles by the roughness only
GUERNSEY = "#272B33"      # dark navy / charcoal wool
DARN = "#353A44"          # the repaired patch: same wool, a little lighter and flatter

# Joint positions traced from the source mesh (world coords of the appended object, metres):
# MCP (knuckle) -> tip, plus the thumb CMC -> MCP -> IP -> tip. Splits: proximal 46 %, middle 30 %, distal 24 %.
FINGERS = {
    "index":  {"mcp": (1.447, 0.012, 0.245), "tip": (1.458, 0.023, 0.158)},
    "middle": {"mcp": (1.424, 0.011, 0.247), "tip": (1.423, 0.025, 0.146)},
    "ring":   {"mcp": (1.401, 0.012, 0.245), "tip": (1.393, 0.031, 0.153)},
    "little": {"mcp": (1.370, 0.018, 0.240), "tip": (1.354, 0.032, 0.182)},
}
THUMB = [(1.435, 0.018, 0.315), (1.462, 0.028, 0.285), (1.482, 0.034, 0.258), (1.494, 0.037, 0.234)]
WRIST = (1.407, 0.013, 0.405)
PALM = (1.415, 0.013, 0.262)
SPLIT = (0.46, 0.30, 0.24)

# Poses: degrees of curl toward the palm per joint (MCP, PIP, DIP); thumb (CMC, MCP, IP) plus abduction.
POSES = {   # Round 2 (renders v2): spread signs flipped (the source hand is modelled splayed: negative brings
            # the index in, positive the little finger); thumb opposition negative (toward the fingers), stronger curl
    "relaxed":    {"fingers": (14, 18, 8),  "spread": (-6, -1, 5, 10), "thumb": (10, 12, 6),  "thumb_in": -12},
    "torch":      {"fingers": (72, 88, 38), "spread": (-6, -1, 4, 9),  "thumb": (38, 42, 30), "thumb_in": -40},
    "compass":    {"fingers": (38, 46, 22), "spread": (-1, 0, 1, 3),   "thumb": (14, 18, 10), "thumb_in": -14},   # Round 4: cupped, fingers together (the open hand read as a wave)
    "binoculars": {"fingers": (52, 62, 30), "spread": (-5, -1, 3, 8),  "thumb": (28, 34, 24), "thumb_in": -30},
}


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = {"new": "--new" in a, "save": "--save" in a, "preview": ""}
    if "--preview" in a:
        out["preview"] = a[a.index("--preview") + 1]
    return out


def material(name, hex_, rough, sheen=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex_to_linear(hex_)
    b.inputs["Roughness"].default_value = rough
    if "Sheen Weight" in b.inputs:
        b.inputs["Sheen Weight"].default_value = sheen
    return m


def source_hand():
    with bpy.data.libraries.load(str(BUNDLE)) as (src, dst):
        dst.objects = [n for n in src.objects if n == SRC_NAME]
    ob = dst.objects[0]
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        if m.type == "MULTIRES":
            m.levels = 1
            bpy.ops.object.modifier_apply(modifier=m.name)
    ob.data = ob.data.copy()          # local, editable
    ob.data.transform(ob.matrix_world)  # bake the bundle's placement: local == world (the traced coords)
    ob.data.transform(Matrix.Translation(-Vector(WRIST)))   # then the wrist centre becomes the origin
    ob.matrix_world = Matrix.Identity(4)
    return ob


def lerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)


def build_armature(name, coll, mirror=False):
    W = Vector(WRIST)
    M = (lambda p: Vector((-(p[0] - W.x), p[1] - W.y, p[2] - W.z))) if mirror else (lambda p: Vector(p) - W)
    roll_thumb = Vector((0.4 if mirror else -0.4, -1, 0)).normalized()
    arm = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, arm)
    coll.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones
    hand = eb.new("hand")
    hand.head, hand.tail = M(WRIST), M(PALM)
    hand.align_roll(Vector((0, -1, 0)))
    for f, d in FINGERS.items():
        mcp, tip = M(d["mcp"]), M(d["tip"])
        pts = [mcp]
        acc = 0.0
        for s in SPLIT:
            acc += s
            pts.append(mcp.lerp(tip, acc))
        parent = hand
        for i in range(3):
            b = eb.new(f"{f}_{i + 1}")
            b.head, b.tail = pts[i], pts[i + 1]
            b.align_roll(Vector((0, -1, 0)))       # local Z to the back of the hand: a curl is -X rotation
            b.parent = parent
            b.use_connect = i > 0
            parent = b
    parent = hand
    for i in range(3):
        b = eb.new(f"thumb_{i + 1}")
        b.head, b.tail = M(THUMB[i]), M(THUMB[i + 1])
        b.align_roll(roll_thumb)
        b.parent = parent
        b.use_connect = i > 0
        parent = b
    bpy.ops.object.mode_set(mode="OBJECT")
    return ob


def cuff(name, hand_ob, coll, mat_wool, mat_darn):
    """A 2x2 ribbed guernsey cuff over the cut wrist, open both ends, with a darned patch on the back."""
    vs = [p for p in (hand_ob.matrix_world @ v.co for v in hand_ob.data.vertices) if p.z > 0.355 - WRIST[2]]
    cx = sum(v.x for v in vs) / len(vs)
    cy = sum(v.y for v in vs) / len(vs)
    rx = (max(v.x for v in vs) - min(v.x for v in vs)) / 2 + 0.006
    ry = (max(v.y for v in vs) - min(v.y for v in vs)) / 2 + 0.006
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    # Round 3 (G3b): a sleeve, not a short cuff. Held palm-up (the compass) the wrist points at the camera, so
    # the guernsey runs 35 cm up the forearm, out of view: a 2x2 rib for the cuff (7 cm), plain knit beyond,
    # widening toward the elbow.
    segs = 64
    # Round 4 (G3b captures): the cuff edge at the real wrist (the mesh is narrowest at z 0.35-0.36 and flares
    # into the palm below 0.34); from 0.372 it left 2 cm of bare forearm and the hand read long.
    zs = [0.350 + 0.0098 * k for k in range(11)] + [0.47 + 0.035 * k for k in range(1, 9)]
    zs = [z - WRIST[2] for z in zs]              # wrist-relative
    rings = len(zs) - 1
    grid = []
    for k, z in enumerate(zs):
        cuff_part = k <= 10
        flare = 1.0 + 0.10 * min(k, 10) / 10 + (0.035 * (k - 10) if k > 10 else 0.0)
        row = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            rib = (1.0 + (0.035 if (i // 2) % 2 == 0 else -0.015)) if cuff_part else 1.0
            lip = 1.0 + (0.04 if k == 0 else 0.0)                # the turned-back edge reads thicker
            row.append(bm.verts.new((cx + rx * math.cos(a) * rib * flare * lip, cy + ry * math.sin(a) * rib * flare * lip, z)))
        grid.append(row)
    for k in range(rings):
        for i in range(segs):
            f = bm.faces.new((grid[k][i], grid[k][(i + 1) % segs], grid[k + 1][(i + 1) % segs], grid[k + 1][i]))
            for lp, (ii, kk) in zip(f.loops, ((i, k), (i + 1, k), (i + 1, k + 1), (i, k + 1))):
                lp[uvl].uv = (ii / segs, kk / rings)            # cylindrical: u around, v along the arm
            # the darn: a patch on the back of the wrist (-Y), two rings tall
            back = math.sin(2 * math.pi * (i + 0.5) / segs) < -0.82
            f.material_index = 1 if back and 2 <= k <= 4 else 0
    # thickness: a second, inner wall so it never reads as paper from inside
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    me.materials.append(mat_wool)
    me.materials.append(mat_darn)
    sol = ob.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.004
    sol.offset = 1.0
    coll.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def apply_pose(arm_ob, pose, side):
    p = POSES[pose]
    sgn = 1.0 if side == "L" else -1.0
    for i, f in enumerate(["index", "middle", "ring", "little"]):
        for j in range(3):
            pb = arm_ob.pose.bones[f"{f}_{j + 1}"]
            pb.rotation_mode = "XYZ"
            spread = math.radians(p["spread"][i]) * sgn if j == 0 else 0.0
            pb.rotation_euler = (-math.radians(p["fingers"][j]), 0.0, spread)
    for j in range(3):
        pb = arm_ob.pose.bones[f"thumb_{j + 1}"]
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (-math.radians(p["thumb"][j]), 0.0, math.radians(p["thumb_in"]) * sgn if j == 0 else 0.0)


def bake_actions(arm_ob, side):
    arm_ob.animation_data_create()
    for name in POSES:
        apply_pose(arm_ob, name, side)
        act = bpy.data.actions.new(f"{side}_{name}")      # unique per side: Godot gets L_torch, R_torch...
        arm_ob.animation_data.action = act
        for pb in arm_ob.pose.bones:
            pb.keyframe_insert("rotation_euler", frame=1)
            pb.keyframe_insert("location", frame=1)
        act.use_fake_user = True
        track = arm_ob.animation_data.nla_tracks.new()
        track.name = f"{side}_{name}"
        track.strips.new(f"{side}_{name}", 1, act)
        arm_ob.animation_data.action = None
    for pb in arm_ob.pose.bones:              # saved and exported at rest: the game applies the poses
        pb.rotation_euler = (0.0, 0.0, 0.0)
    for tr in arm_ob.animation_data.nla_tracks:   # strips muted: the file and the validator see the rest pose;
        tr.mute = True                             # the glTF export still writes every action (checked: 8)


def mirror_object(ob):
    """Mirror across the hand's own centre plane (x = WRIST.x), keep transforms applied, fix normals."""
    me = ob.data
    for v in me.vertices:
        v.co.x = -v.co.x                      # the wrist centre is the origin
    me.flip_normals()
    me.update()


def main():
    a = args()
    if a["new"]:
        clear_scene()
    coll = get_collection("ASSET_hands")
    skin = material("M_LL_Skin", SKIN, 0.52, 0.15)
    wool = material("M_LL_Guernsey", GUERNSEY, 0.92, 0.6)
    darn = material("M_LL_GuernseyDarn", DARN, 0.95, 0.3)
    src = source_hand()
    rig = {}
    for side in ("L", "R"):
        hand = src.copy()
        hand.data = src.data.copy()
        hand.name = f"SK_hand_{side}"
        coll.objects.link(hand)
        hand.data.materials.clear()
        hand.data.materials.append(skin)
        for p in hand.data.polygons:
            p.use_smooth = True
        if side == "R":
            mirror_object(hand)
        arm = build_armature(f"ARM_hand_{side}", coll, mirror=side == "R")   # mirrored points, not moved bones
        # automatic weights
        bpy.ops.object.select_all(action="DESELECT")
        hand.select_set(True)
        arm.select_set(True)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        c = cuff(f"SK_cuff_{side}", hand, coll, wool, darn)
        # skinned to the hand bone (transforms stay applied; the glTF skin carries it with the hand)
        vg = c.vertex_groups.new(name="hand")
        vg.add(list(range(len(c.data.vertices))), 1.0, "REPLACE")
        c.parent = arm
        mod = c.modifiers.new("Armature", "ARMATURE")
        mod.object = arm
        bake_actions(arm, side)
        rig[side] = (arm, hand, c)
    bpy.data.objects.remove(src)
    res = {"objects": len(coll.all_objects), "tris": 0, "bones": {s: len(rig[s][0].data.bones) for s in rig}}
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in coll.all_objects:
        if ob.type == "MESH":
            m = ob.evaluated_get(dg).to_mesh()
            m.calc_loop_triangles()
            res["tris"] += len(m.loop_triangles)
    if a["preview"]:
        preview(rig, a["preview"])
    if a["save"]:
        res["saved"] = save_versioned(HERE, "last_light_hands")
    import json
    print("HANDS_RESULT", json.dumps(res))


def preview(rig, outdir):
    """One render per pose: both hands, seen as the keeper sees them (from the wrist side, palms in)."""
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT" if any(e.identifier == "BLENDER_EEVEE_NEXT" for e in
                                                   bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items) else "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 800, 800
    world = bpy.data.worlds.new("w")
    world.color = (0.05, 0.05, 0.06)
    sc.world = world
    cam = bpy.data.objects.new("pcam", bpy.data.cameras.new("pcam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    key = bpy.data.objects.new("key", bpy.data.lights.new("key", "AREA"))
    key.data.energy, key.data.size = 60, 0.6
    sc.collection.objects.link(key)
    key.location = (0.01, -0.5, 0.2)
    key.rotation_euler = (math.radians(55), 0, 0)
    fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "AREA"))
    fill.data.energy, fill.data.size = 15, 1.0
    sc.collection.objects.link(fill)
    fill.location = (0.5, 0.5, -0.1)
    fill.rotation_euler = (math.radians(70), 0, math.radians(130))
    # put the right hand beside the left for the review
    rig["R"][0].location.x += 0.20
    centre = Vector((0.10, 0.007, -0.135))
    for side in rig:
        rig[side][0].animation_data.action = None
        for tr in rig[side][0].animation_data.nla_tracks:     # the export strips would override the poses
            tr.mute = True
    for name in POSES:
        for side in rig:
            apply_pose(rig[side][0], name, side)
        for view, off in (("back", Vector((0, -0.62, 0.05))), ("palm", Vector((0, 0.62, 0.05)))):
            cam.location = centre + off
            cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
            sc.render.filepath = f"{outdir}/pose_{name}_{view}.png"
            bpy.ops.render.render(write_still=True)
    rig["R"][0].location.x -= 0.20
    for side in rig:
        for pb in rig[side][0].pose.bones:
            pb.rotation_euler = (0.0, 0.0, 0.0)
        for tr in rig[side][0].animation_data.nla_tracks:
            tr.mute = True


if __name__ == "__main__":
    main()
