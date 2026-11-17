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
  tools/bl -P projects/games/last_light/blender/hands.py -- --grip_check renders/last_light/stageP/grips OUT.json
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
sys.path.insert(0, str(HERE))
from body import tex_material, KNIT_TILE  # noqa: E402  (Stage P: one knit for body and sleeves)

BUNDLE = WS / "assets/models/human_base_meshes/bundle/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"
SRC_NAME = "Hand  - Realistic"
SKIN = "#C99079"          # fair to lightly ruddy (PROFILE §G), weathered at the knuckles by the roughness only
GUERNSEY = "#363F58"      # Stage P (Q19): one navy with the body and the chair (textures: knit_tex.py)
SHIRT = "#D6CFBF"         # pale worn cotton
RIB_TILE = 0.08           # knit_tex.py: 8 ribs a tile
# Stage P (4.1 item 5): the sleeve bends. Heights in the source's frame (the hand hangs fingers down, -Z):
CUFF_Z = 0.350            # the guernsey cuff's edge, at the real wrist
SHIRT_Z = 0.338           # the shirt cuff shows 1.2 cm below it
SKIN_TOP = 0.385          # the hand's skin is trimmed here, inside the rigid part of the cuff
BEND = (0.39, 0.45)       # the sleeve goes from the hand bone to the forearm bone across this span
PIVOT_Z = 0.400           # where the forearm and wrist bones turn

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
    "torch":      {"fingers": (57.6, 72.2, 31.2), "curl_k": (1.0, 1.0, 0.9, 0.75), "spread": (-6, -1, 4, 9),
                   "thumb": (38, 42, 30), "thumb_in": -40},
    "compass":    {"fingers": (38, 46, 22), "spread": (-1, 0, 1, 3),   "thumb": (7, 9, 5), "thumb_in": 5},   # Round 4: cupped, fingers together (the open hand read as a wave)
    "binoculars": {"fingers": (39, 46.5, 22.5), "curl_k": (1.0, 1.0, 1.0, 0.8), "spread": (-5, -1, 3, 8),
                   "thumb": (28, 34, 24), "thumb_in": 0},
}
# Stage P (4.1): fitted against the held items (regress R27 dumps the grips; --grip_check measures them). G3b's
# fingers went into the items: the binoculars 16.7 mm (the palm too), the torch 6.9, the compass 5.0, and the
# two thumbs into each other over the bridge 4.7. Now the torch fist opens at the knuckles (72 -> 58 deg) and
# keeps its middle joints (middle finger PIP 72, R16 wants a closed fist over 70), the ring and little fingers
# curl less; the compass thumb lies open beside the case; the binocular fingers lie over the barrels and the
# thumbs stop short of the bridge. equipment.gd GRIP_FIT moves each hand off its item to match.


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = {"new": "--new" in a, "save": "--save" in a, "preview": "", "grip_check": None}
    if "--preview" in a:
        out["preview"] = a[a.index("--preview") + 1]
    if "--grip_check" in a:                     # Stage P: --grip_check DIR OUT.json
        i = a.index("--grip_check")
        out["grip_check"] = (a[i + 1], a[i + 2])
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


def _slice(hand_ob, z, h=0.003):
    """The hand's cross-section near height z (source frame): (cx, cy, rx, ry), or None."""
    vs = [p for p in (hand_ob.matrix_world @ v.co for v in hand_ob.data.vertices) if abs(p.z - (z - WRIST[2])) < h]
    if not vs:
        return None
    xs, ys = [v.x for v in vs], [v.y for v in vs]
    return ((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2)


def cuff(name, hand_ob, coll, mats):
    """The guernsey sleeve: a 2x2 ribbed cuff over the wrist (with a darned patch on the back), plain knit up
    the forearm, widening toward the elbow; and the shirt's cotton cuff showing 1.2 cm below it.
    mats: rib, knit, darn, shirt. Returns (sleeve, shirt cuff)."""
    vs = [p for p in (hand_ob.matrix_world @ v.co for v in hand_ob.data.vertices) if p.z > 0.355 - WRIST[2]]
    cx = sum(v.x for v in vs) / len(vs)
    cy = sum(v.y for v in vs) / len(vs)
    rx = (max(v.x for v in vs) - min(v.x for v in vs)) / 2 + 0.006
    ry = (max(v.y for v in vs) - min(v.y for v in vs)) / 2 + 0.006
    # the shirt cuff: a plain tube clearing the skin by 2.5 mm (plus its 1.5 mm wall) over everything it and
    # the guernsey cover, SHIRT_Z .. SKIN_TOP (the palm flares below the wrist). Sized by the largest
    # elliptical radius of any skin vertex there: an ellipse through a slice's box half-widths misses the
    # box's corners (the first build had skin 2.7 mm outside)
    w0 = _slice(hand_ob, CUFF_Z + 0.006)
    a0, b0 = w0[2], w0[3]
    span = [p for p in (hand_ob.matrix_world @ v.co for v in hand_ob.data.vertices)
            if SHIRT_Z - WRIST[2] <= p.z <= SKIN_TOP - WRIST[2]]
    e = max(math.hypot((p.x - cx) / a0, (p.y - cy) / b0) for p in span)
    srx = e * a0 + 0.0025 + 0.0015
    sry = e * b0 + 0.0025 + 0.0015
    # the guernsey cuff must ride over it (its purl valleys sit 1.5 % in, the lip 4 % out)
    rx, ry = max(rx, (srx + 0.002) / 0.985), max(ry, (sry + 0.002) / 0.985)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    dvl = bm.verts.layers.deform.verify()
    # Round 3 (G3b): a sleeve, not a short cuff. Held palm-up (the compass) the wrist points at the camera, so
    # the guernsey runs 35 cm up the forearm, out of view: a 2x2 rib for the cuff, plain knit beyond,
    # widening toward the elbow.
    segs = 64
    # Round 4 (G3b captures): the cuff edge at the real wrist (the mesh is narrowest at z 0.35-0.36 and flares
    # into the palm below 0.34); from 0.372 it left 2 cm of bare forearm and the hand read long.
    zs_abs = [CUFF_Z + 0.0098 * k for k in range(11)] + [0.47 + 0.035 * k for k in range(1, 9)]
    zs = [z - WRIST[2] for z in zs_abs]          # wrist-relative
    rings = len(zs) - 1
    circ = 2 * math.pi * (rx + ry) / 2
    grid = []
    for k, (z, za) in enumerate(zip(zs, zs_abs)):
        cuff_part = k <= 10
        flare = 1.0 + 0.10 * min(k, 10) / 10 + (0.035 * (k - 10) if k > 10 else 0.0)
        row = []
        # Stage P: hand -> wrist -> forearm across BEND (the cuff's first 4 cm move with the hand)
        t = max(0.0, min(1.0, (za - BEND[0]) / (BEND[1] - BEND[0])))
        t = t * t * (3 - 2 * t)
        w = {"hand": 1.0 - t, "forearm": t, "wrist": 0.5 * math.sin(math.pi * t)}
        tot = sum(w.values())
        for i in range(segs):
            a = 2 * math.pi * i / segs
            rib = (1.0 + (0.035 if (i // 2) % 2 == 0 else -0.015)) if cuff_part else 1.0
            lip = 1.0 + (0.04 if k == 0 else 0.0)                # the turned-back edge reads thicker
            v = bm.verts.new((cx + rx * math.cos(a) * rib * flare * lip, cy + ry * math.sin(a) * rib * flare * lip, z))
            for gi, gname in enumerate(("hand", "wrist", "forearm")):
                if w[gname] > 1e-4:
                    v[dvl][gi] = w[gname] / tot
            row.append(v)
        grid.append(row)
    for k in range(rings):
        rib_k = k < 10
        for i in range(segs):
            f = bm.faces.new((grid[k][i], grid[k][(i + 1) % segs], grid[k + 1][(i + 1) % segs], grid[k + 1][i]))
            for lp, (ii, kk) in zip(f.loops, ((i, k), (i + 1, k), (i + 1, k + 1), (i, k + 1))):
                along = zs_abs[kk] - CUFF_Z
                # Stage P: UVs in tiles: the rib's 16 ribs round the wrist = 2 rib tiles; knit at its gauge
                lp[uvl].uv = (ii / segs * 2.0, along / RIB_TILE) if rib_k else (ii / segs * circ / KNIT_TILE, along / KNIT_TILE)
            # the darn: a patch on the back of the wrist (-Y), two rings tall
            back = math.sin(2 * math.pi * (i + 0.5) / segs) < -0.82
            f.material_index = 2 if back and 2 <= k <= 4 else (0 if rib_k else 1)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    for m in mats[:3]:
        me.materials.append(m)
    for gname in ("hand", "wrist", "forearm"):
        ob.vertex_groups.new(name=gname)
    sol = ob.modifiers.new("thick", "SOLIDIFY")   # a second, inner wall so it never reads as paper from inside
    sol.thickness = 0.004
    sol.offset = 1.0
    coll.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    # the shirt cuff: SHIRT_Z up under the guernsey's edge, rigid with the hand
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    rows = []
    for z in (SHIRT_Z, SHIRT_Z + 0.004, CUFF_Z + 0.008):
        rows.append([bm.verts.new((cx + srx * math.cos(2 * math.pi * i / segs), cy + sry * math.sin(2 * math.pi * i / segs),
                                   z - WRIST[2])) for i in range(segs)])
    circ_s = 2 * math.pi * (srx + sry) / 2
    for k in range(len(rows) - 1):
        for i in range(segs):
            f = bm.faces.new((rows[k][i], rows[k][(i + 1) % segs], rows[k + 1][(i + 1) % segs], rows[k + 1][i]))
            for lp, (ii, kk) in zip(f.loops, ((i, k), (i + 1, k), (i + 1, k + 1), (i, k + 1))):
                lp[uvl].uv = (ii / segs * circ_s / 0.02, kk * 0.4)
    sme = bpy.data.meshes.new(name.replace("cuff", "shirt"))
    bm.to_mesh(sme)
    bm.free()
    sh = bpy.data.objects.new(sme.name, sme)
    sme.materials.append(mats[3])
    sol = sh.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.0015
    sol.offset = -1.0                              # inward: its outside stays where it was measured
    coll.objects.link(sh)
    for p in sme.polygons:
        p.use_smooth = True
    sh.vertex_groups.new(name="hand").add(list(range(len(sme.vertices))), 1.0, "REPLACE")
    ob["fit"] = {"cuff_r": [rx, ry], "shirt_r": [srx, sry], "centre": [cx, cy]}
    return ob, sh


def trim_skin(hand_ob):
    """The hand's own stub of forearm goes above SKIN_TOP: it sits in the cuff's rigid part, so the bent sleeve
    can never pass through it."""
    bm = bmesh.new()
    bm.from_mesh(hand_ob.data)
    kill = [v for v in bm.verts if v.co.z > SKIN_TOP - WRIST[2]]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(hand_ob.data)
    bm.free()


def add_arm_bones(arm_ob):
    """Stage P: the forearm (aimed at the elbow by equipment.gd), the wrist (half the forearm's turn, so the
    bend keeps its volume) and an elbow marker at the forearm's tip. Children of the hand, added after the
    automatic weights, so the skin never takes weight from them."""
    bpy.context.view_layer.objects.active = arm_ob
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_ob.data.edit_bones
    hand = eb["hand"]
    piv = Vector((0.0, 0.0, PIVOT_Z - WRIST[2]))
    for nm, length in (("wrist", 0.06), ("forearm", 0.27)):
        b = eb.new(nm)
        b.head, b.tail = piv, piv + Vector((0, 0, length))
        b.align_roll(Vector((0, -1, 0)))
        b.parent = hand
        b.use_connect = False
    el = eb.new("elbow")
    el.head, el.tail = eb["forearm"].tail, eb["forearm"].tail + Vector((0, 0, 0.03))
    el.align_roll(Vector((0, -1, 0)))
    el.parent = eb["forearm"]
    el.use_connect = True
    el.use_deform = False
    bpy.ops.object.mode_set(mode="OBJECT")


def check_fit(rig):
    """Static fit (the cuff is rigid with the hand, the skin under it too): every skin vertex in the cuffs'
    span inside the shirt cuff's inner wall, and the shirt cuff inside the guernsey's (both ellipses, mm)."""
    out = {}
    for side, (arm, hand, c, sh) in rig.items():
        f = c["fit"]
        cx, cy = f["centre"]
        srx, sry = f["shirt_r"]
        rx, ry = f["cuff_r"]
        worst = 0.0
        for v in hand.data.vertices:
            p = hand.matrix_world @ v.co
            za = p.z + WRIST[2]
            if SHIRT_Z <= za <= SKIN_TOP:
                inner = (srx - 0.0015, sry - 0.0015) if za < CUFF_Z + 0.008 else (rx * 0.985, ry * 0.985)
                e = math.hypot((p.x - cx) / inner[0], (p.y - cy) / inner[1])
                worst = max(worst, (e - 1.0) * min(inner) * 1000)
        out[side] = {"skin_out_of_cuff_mm": round(max(0.0, worst), 2),
                     "shirt_under_guernsey_mm": round(min(rx * 0.985 - srx, ry * 0.985 - sry) * 1000, 2)}
    return out


def apply_pose(arm_ob, pose, side):
    p = POSES[pose]
    sgn = 1.0 if side == "L" else -1.0
    ks = p.get("curl_k", (1.0, 1.0, 1.0, 1.0))     # Stage P: per finger (index .. little), fitted to the items
    for i, f in enumerate(["index", "middle", "ring", "little"]):
        for j in range(3):
            pb = arm_ob.pose.bones[f"{f}_{j + 1}"]
            pb.rotation_mode = "XYZ"
            spread = math.radians(p["spread"][i]) * sgn if j == 0 else 0.0
            pb.rotation_euler = (-math.radians(p["fingers"][j] * ks[i]), 0.0, spread)
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


def grip_check(src_dir, out_path):
    """Stage P (4.1): no hand or cuff through a held item, nor through the other hand, in any grip. Reads the
    posed meshes regress R27 writes (renders/last_light/stageP/grips/grips_<pose>.glb: hands posed on the CPU,
    items as held, all in the camera's frame). A point is inside a part when at least 4 of 6 axis rays from it
    first meet a back face (the parts are not all watertight); its depth is the distance to that part's
    surface. Plain touching is not a penetration."""
    import glob
    import json
    from mathutils.bvhtree import BVHTree
    dirs = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
    report = {}
    for path in sorted(glob.glob(str(Path(src_dir) / "grips_*.glb"))):
        clear_scene()
        bpy.ops.import_scene.gltf(filepath=path)
        dg = bpy.context.evaluated_depsgraph_get()
        parts = {}
        for ob in bpy.context.scene.objects:
            if ob.type != "MESH":
                continue
            m = ob.evaluated_get(dg).to_mesh()
            vs = [ob.matrix_world @ v.co for v in m.vertices]
            ps = [list(p.vertices) for p in m.polygons]
            ob.evaluated_get(dg).to_mesh_clear()
            nm = ob.name
            key = nm.rsplit("_", 1)[0] if nm.startswith("item_") else nm.split(".")[0]
            v0, p0 = parts.get(key, ([], []))
            parts[key] = (v0 + vs, p0 + [[i + len(v0) for i in q] for q in ps])
        bvh = {k: BVHTree.FromPolygons(v, p) for k, (v, p) in parts.items()}
        hands_ = [k for k in parts if k.startswith("hand")]
        solids = [k for k in parts if k.startswith("item_")] + [k for k in hands_ if "SK_hand_" in k]
        pairs = {}
        for a_k in hands_:
            for b_k in solids:
                if b_k == a_k or (b_k.startswith("hand") and b_k[:5] == a_k[:5]):
                    continue                              # never a hand against its own side
                worst, n_over = 0.0, 0
                for q in parts[a_k][0][::2]:
                    back, hits = 0, 0
                    for d in dirs:
                        h = bvh[b_k].ray_cast(q, d, 0.5)
                        if h[0] is not None:
                            hits += 1
                            back += h[1].dot(d) > 0
                    if hits >= 4 and back >= 4:
                        dep = bvh[b_k].find_nearest(q)[3]
                        worst = max(worst, dep)
                        n_over += dep > 0.002
                pairs[f"{a_k} in {b_k}"] = {"max_mm": round(worst * 1000, 2), "over_2mm": n_over}
        report[Path(path).stem] = pairs
    worst = max((v["max_mm"] for r in report.values() for v in r.values()), default=0.0)
    with open(out_path, "w") as f:
        json.dump({"worst_mm": worst, "pass": worst < 2.0, "grips": report}, f, indent=1)
    print("GRIP_CHECK", json.dumps({"worst_mm": worst, "pass": worst < 2.0, "files": len(report)}))


def main():
    a = args()
    if a["grip_check"]:
        grip_check(*a["grip_check"])
        return
    if a["new"]:
        clear_scene()
    coll = get_collection("ASSET_hands")
    skin = material("M_LL_Skin", SKIN, 0.52, 0.15)
    rib = tex_material("M_LL_GuernseyRib", "T_LL_Rib_albedo.png", "T_LL_Rib_normal.png", "T_LL_Rib_rough.png", 0.9, 0.6)
    wool = tex_material("M_LL_Guernsey", "T_LL_Knit_albedo.png", "T_LL_Knit_normal.png", "T_LL_Knit_rough.png", 0.9, 0.6)
    darn = tex_material("M_LL_GuernseyDarn", "T_LL_Darn_albedo.png", "T_LL_Rib_normal.png", "T_LL_Rib_rough.png", 0.93, 0.3)
    shirt = material("M_LL_Shirt", SHIRT, 0.8, 0.2)
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
        trim_skin(hand)
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        add_arm_bones(arm)
        c, sh = cuff(f"SK_cuff_{side}", hand, coll, (rib, wool, darn, shirt))
        # skinned (transforms stay applied; the glTF skin carries them with the hand): the shirt cuff and the
        # first 4 cm of the guernsey cuff to the hand bone, the rest across to the wrist and forearm bones
        for ob in (c, sh):
            ob.parent = arm
            mod = ob.modifiers.new("Armature", "ARMATURE")
            mod.object = arm
        bake_actions(arm, side)
        rig[side] = (arm, hand, c, sh)
    bpy.data.objects.remove(src)
    res = {"objects": len(coll.all_objects), "tris": 0, "bones": {s: len(rig[s][0].data.bones) for s in rig},
           "fit": check_fit(rig)}
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
