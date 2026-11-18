"""THE LAST LIGHT, audit Stage R (Addendum B 6.5, 6.6, 20.4): Alasdair Ross, the man at the door.

Canon (character-refs/ross/PROFILE.md §G, CANON_INDEX §9, DECISIONS Q15): 64, tall, broad-shouldered but
thinned by illness, slightly stooped; an old black oilskin, wet, water beading on the shoulders; a sou'wester
with rain running off the brim; the face is never shown clearly (at most the edge of a cheek and short
grey-white stubble). One hand on the stair rail. Read through posture and light.

Modes (each run headless; heavy ones under `taskpolicy -b`):

  marks   verify the staging positions A..E (B 20.4) in the built room with the door open: a body-sized
          proxy at each mark, floor / clearance / reach checks, plan and eye-level renders.
            tools/bl projects/games/last_light/blender/last_light_vNNN.blend -P .../ross.py -- --marks OUT_DIR

  build   the figure, ASSET_ross: SK_ross (one skinned mesh, two materials, one 2k texture set) on ARM_ross
          (body.py's rig, plus 15 finger bones a hand). Saves last_light_ross_vNNN.blend.
            tools/bl -P .../ross.py -- --new --save [--preview DIR]

  stills  the checkpoint: the figure posed at A, B and C in the built room, lit by the game's lights only.
            tools/bl projects/games/last_light/blender/last_light_vNNN.blend -P .../ross.py -- \
                --stills OUT_DIR --figure .../last_light_ross_vNNN.blend [--only A,B,C] [--variant game|key]

  actions the game's actions on the opened figure (idle, walk, and the held poses door / chair / wheel solved at
          marks B / C / D), saved as a new version for the glTF export (ross.glb).
            tools/bl .../last_light_ross_vNNN.blend -P .../ross.py -- --actions --save

Room frame (build.py): a point is (bearing, along, z, dist): `dist` from the room centre on the bearing,
`along` to the right as seen from inside facing the wall, `z` above the room floor (20.0 m).
"""
import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[3]
sys.path.insert(0, str(WS / "scripts"))
sys.path.insert(0, str(HERE))

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Quaternion, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

from lib.bl_args import parse  # noqa: E402
from lib.safe_paths import ensure_allowed  # noqa: E402

F = 20.0                      # room floor (spec room.floor_z)
STAIR_B = 170.0               # spec room.stair
DOOR_FRONT = 2.5642           # build.py build_stair: back_dist(1.3, 0) - STAIR_DEPTH (the door plane)


def load_spec():
    import importlib.util
    s = importlib.util.spec_from_file_location("ll_spec", HERE / "spec.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m.SPEC


def wall_frame(bearing):
    b = math.radians(bearing)
    return Vector((math.cos(b), -math.sin(b), 0.0)), Vector((math.sin(b), math.cos(b), 0.0)), Vector((0, 0, 1))


def dp(bearing, along, z, dist):
    r, o, u = wall_frame(bearing)
    return o * dist + r * along + u * (F + z)


def polar(p):
    """World point -> (bearing deg, dist from the centre, z above the floor), as spec.py records them."""
    return (round(math.degrees(math.atan2(p.x, p.y)) % 360.0, 2), round(math.hypot(p.x, p.y), 3), round(p.z - F, 3))


def from_polar(bearing, dist, z=0.0):
    b = math.radians(bearing)
    return Vector((math.sin(b) * dist, math.cos(b) * dist, F + z))


def dir_of(bearing):
    b = math.radians(bearing)
    return Vector((math.sin(b), math.cos(b), 0.0))


# ------------------------------------------------------------------------------------------------ marks

def marks():
    """The staging marks, from spec.py (Stage R records them there once verified)."""
    return load_spec()["ross_marks"]


def mark_frame(m):
    """(feet centre, facing direction, right direction) of a mark."""
    p = from_polar(*m["pos"])
    f = dir_of(m["face"])
    return p, f, f.cross(Vector((0, 0, 1)))


# A body-sized proxy (Ross: 1.88 m upright, stooped): (z0, z1, half-width across, half-depth, forward offset).
# Widths are the oilskin's over a lean old frame (measured on the figure once it exists).
PROXY = [(0.00, 0.12, 0.16, 0.15, 0.03),    # boots (both feet, 0.2 m stance)
         (0.12, 0.45, 0.14, 0.10, 0.00),    # sea-boot shafts
         (0.45, 0.95, 0.18, 0.15, 0.00),    # oilskin skirt (a thinned man's hips)
         (0.95, 1.30, 0.22, 0.15, 0.01),    # chest
         (1.30, 1.52, 0.245, 0.14, 0.03),   # shoulders (deltoids and the coat)
         (1.52, 1.66, 0.08, 0.08, 0.07),    # neck and scarf
         (1.66, 1.80, 0.11, 0.12, 0.09),    # head
         (1.80, 1.84, 0.17, 0.19, 0.06),    # sou'wester brim (longer at the back)
         (1.84, 1.93, 0.11, 0.12, 0.08)]    # crown
INSET = 0.02                                 # a designed contact passes if the proxy inset by this clears it
PROXY_NAMES = ["boots", "shafts", "skirt", "chest", "shoulders", "neck", "head", "brim", "crown"]
SHOULDER = (0.215, 1.47)                     # (across, height): the shoulder joint, for reach
HIP_Z = 0.95                                 # the lean's pivot (a mark's "lean": spine flexion in degrees)
ARM_REACH = 0.70                             # shoulder joint to palm centre, arm straight


def proxy_mesh(name, m, coll, inset=0.0):
    """The proxy at a mark. A mark's "sway" (m, + to his left) shifts the upper body over the hips."""
    p, f, rt = mark_frame(m)
    sway = m.get("sway", 0.0)
    bm = bmesh.new()
    seg = 20
    for z0, z1, hw, hd, fwd in PROXY:
        k = 0.0 if z0 < 0.95 else (0.5 if z0 < 1.3 else 1.0)
        c = p + f * fwd - rt * (sway * k)
        hw, hd = hw - inset, hd - inset
        rings = []
        for z in (z0 + inset * 0.5, z1 - inset * 0.5):
            rings.append([bm.verts.new(c + rt * (hw * math.cos(2 * math.pi * i / seg)) +
                                       f * (hd * math.sin(2 * math.pi * i / seg)) + Vector((0, 0, z)))
                          for i in range(seg)])
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[1])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def room_bvhs(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.transform(o.matrix_world)
        out.append((o.name, BVHTree.FromBMesh(bm), bm))
        ev.to_mesh_clear()
    return out


def room_objects():
    keep = []
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name.startswith(("COL_", "ROSS_", "PRX_")):
            continue
        cn = o.users_collection[0].name if o.users_collection else ""
        if cn in ("ASSET_watch_room", "ASSET_stairwell"):
            keep.append(o)
    return keep


def check_mark(key, m, prx, bvhs):
    """Floor under the feet, clearance to the room (sampled from the proxy's surface), reach to the hand target."""
    p, f, rt = mark_frame(m)
    res = {"pos": m["pos"], "face": m["face"]}
    # floor: a ray down at each foot
    floor = []
    for side in (-1, 1):
        o_ = p + rt * (0.1 * side) + Vector((0, 0, 0.5))
        best = None
        for nm, t, _ in bvhs:
            hit = t.ray_cast(o_, Vector((0, 0, -1)), 2.0)
            if hit[0] is not None and (best is None or hit[3] < best[1]):
                best = (nm, hit[3], hit[0].z)
        floor.append({"hit": best[0] if best else None, "z": round(best[2] - F, 4) if best else None})
    res["floor"] = floor
    res["floor_ok"] = all(fl["z"] is not None and abs(fl["z"]) <= 0.02 for fl in floor)
    # clearance: nearest room surface to each proxy vertex (the floor itself excluded below 2 cm)
    pv = [prx.matrix_world @ v.co for v in prx.data.vertices]
    worst = (9.0, None, None)
    hand = from_polar(*m["hand"]) if m.get("hand") else None
    for v in pv:
        for nm, t, _ in bvhs:
            hit = t.find_nearest(v, 0.3)
            if hit[0] is None:
                continue
            if v.z - F < 0.02 and abs(hit[0].z - F) < 0.03:
                continue                     # the boots stand on the floor
            if hand is not None and (hit[0] - hand).length < 0.12:
                continue                     # the hand's own target
            if hit[3] < worst[0]:
                worst = (hit[3], nm, tuple(round(c, 3) for c in polar(v)))
    # interpenetration: a proxy point inside a closed room part shows as a near-zero distance; also test overlap
    pbm = bmesh.new()
    pbm.from_mesh(prx.data)
    pbm.transform(prx.matrix_world)
    ptree = BVHTree.FromBMesh(pbm)
    bands = [b[:2] for b in PROXY]
    per = len(pbm.faces) // len(PROXY)
    overlaps = {}
    for nm, t, rbm in bvhs:
        if nm in ("SM_Room_Floor", "SM_Room_Rug", "SM_Well_Chequer"):
            continue
        pairs = ptree.overlap(t)
        if not pairs:
            continue
        rbm.faces.ensure_lookup_table()
        hit_bands = sorted({PROXY_NAMES[min(i // per, len(PROXY) - 1)] for i, _ in pairs})
        zs = [rbm.faces[j].calc_center_median().z - F for _, j in pairs]
        overlaps[nm] = {"bands": hit_bands, "z": [round(min(zs), 2), round(max(zs), 2)], "pairs": len(pairs)}
    pbm.free()
    contacts = m.get("contacts", [])
    if overlaps:
        ins = proxy_mesh(prx.name + "_inset", m, prx.users_collection[0], inset=INSET)
        ibm = bmesh.new()
        ibm.from_mesh(ins.data)
        itree = BVHTree.FromBMesh(ibm)
        for nm, t, _ in bvhs:
            if nm in overlaps:
                overlaps[nm]["designed"] = any(nm.startswith(c) for c in contacts)
                overlaps[nm]["clear_when_inset_2cm"] = not itree.overlap(t)
        ibm.free()
        bpy.data.objects.remove(ins, do_unlink=True)
    res["overlaps_ok"] = all(v.get("designed") and v.get("clear_when_inset_2cm") for v in overlaps.values())
    res["min_clear_m"] = round(worst[0], 4)
    res["min_clear_at"] = {"object": worst[1], "polar": worst[2]}
    res["overlaps"] = overlaps
    if hand is not None:
        ln = math.radians(m.get("lean", 0.0))
        up = SHOULDER[1] - HIP_Z
        sh = (p - rt * m.get("sway", 0.0) + rt * (SHOULDER[0] * (1 if m["hand_side"] == "R" else -1)) + f * (up * math.sin(ln)) +
              Vector((0, 0, HIP_Z + up * math.cos(ln))))
        res["lean_deg"] = m.get("lean", 0.0)
        res["hand"] = m["hand"]
        res["reach_m"] = round((hand - sh).length, 3)
        res["reach_ok"] = 0.30 <= res["reach_m"] <= ARM_REACH
    return res


def pose_room_door():
    import review_views
    review_views.pose_stair_door(True, True)


def run_marks(out):
    out = ensure_allowed(out)
    out.mkdir(parents=True, exist_ok=True)
    pose_room_door()
    coll = bpy.data.collections.new("PRX_marks")
    bpy.context.scene.collection.children.link(coll)
    objs = room_objects()
    bvhs = room_bvhs(objs)
    report = {}
    prox = {}
    for k, m in marks().items():
        if k.startswith("_"):
            continue
        prx = proxy_mesh(f"PRX_{k}", m, coll)
        prox[k] = prx
        report[k] = check_mark(k, m, prx, bvhs)
    # door head over the A -> B walk: the crown's top against the trim's underside
    report["_door_head"] = {"crown_top_m": PROXY[-1][1], "trim_underside_m": round(_trim_underside(bvhs) - F, 3)}
    for _, _, bm in bvhs:
        bm.free()
    path = out / "marks.json"
    path.write_text(json.dumps(report, indent=1))
    print("MARKS_RESULT", json.dumps(report))
    if not _ARGS.norender:
        render_marks(out, prox)


def _trim_underside(bvhs):
    """Lowest surface over the doorway centre (a ray up from 1.5 m on the door line)."""
    p = dp(STAIR_B, 0.0, 1.5, DOOR_FRONT - 0.01)
    best = None
    for nm, t, _ in bvhs:
        hit = t.ray_cast(p, Vector((0, 0, 1)), 2.0)
        if hit[0] is not None and (best is None or hit[0].z < best):
            best = hit[0].z
    return best


def _review_scene(res):
    sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = 0.3
    for o in bpy.data.objects:
        if o.name.startswith("COL_"):
            o.hide_render = True
    world = bpy.data.worlds.new("RossReview")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.07, 0.11, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    sc.world = world
    cam = bpy.data.objects.new("RossCam", bpy.data.cameras.new("RossCam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.clip_start = 0.03
    return sc, cam


def _flat_mat(name, rgb, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = 0.6
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def render_marks(out, prox):
    """Plan (top-down, ceiling hidden) and an eye-level view of each mark, review lighting."""
    import review_views as RV
    sc, cam = _review_scene((1400, 1400))
    mat = _flat_mat("PRX_mat", (1.0, 0.35, 0.05), 0.6)
    hm = _flat_mat("PRX_hand", (0.1, 0.9, 0.2), 2.0)
    for k, prx in prox.items():
        prx.data.materials.append(mat)
        m = marks()[k]
        if m.get("hand"):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=from_polar(*m["hand"]))
            s = bpy.context.active_object
            s.name = f"PRX_hand_{k}"
            s.data.materials.append(hm)
        t = bpy.data.objects.new(f"PRX_label_{k}", bpy.data.curves.new(f"lbl{k}", "FONT"))
        t.data.body = k
        t.data.size = 0.25
        t.data.materials.append(hm)
        p, f, _ = mark_frame(m)
        t.location = p + Vector((0.18, 0.18, 2.2))
        sc.collection.objects.link(t)
    for o in list(bpy.data.objects):
        if o.name.startswith("LIGHT_") and o.name != "LIGHT_lamp":
            ld = bpy.data.lights.new("Rev_" + o.name, "POINT")
            ld.energy = 90.0 if "desk" in o.name else 45.0
            ld.color = (1.0, 0.72, 0.45)
            lo = bpy.data.objects.new("Rev_" + o.name, ld)
            lo.location = o.matrix_world.translation
            sc.collection.objects.link(lo)
    fill = bpy.data.objects.new("RevFill", bpy.data.lights.new("RevFill", "POINT"))
    fill.data.energy = 120.0
    fill.location = (0, 0, F + 2.6)
    sc.collection.objects.link(fill)
    hide = [o for o in bpy.data.objects if o.name.startswith(("SM_RoomCeiling", "SM_Lantern", "SM_Room_SteelRust", "SM_RoomPipes", "PT_optic_gear"))
            or (o.users_collection and o.users_collection[0].name == "ASSET_lighthouse")]
    # top-down, orthographic, from just under the housing's top plate (2.3 m): the clip hides everything above
    cam.data.type = "ORTHO"
    cam.data.clip_start, cam.data.clip_end = 0.01, 4.0
    for name, c, scale in (("plan_room", (0.0, 0.0), 6.9), ("plan_door", tuple(dp(STAIR_B, 0.0, 0, 2.55).xy), 2.0)):
        cam.data.ortho_scale = scale
        cam.location = (c[0], c[1], F + 2.28)
        cam.rotation_euler = (0.0, 0.0, 0.0)
        sc.render.filepath = str(out / f"{name}.png")
        bpy.ops.render.render(write_still=True)
    cam.data.type = "PERSP"
    cam.data.clip_end = 100.0
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    cam.data.lens = RV.lens_for_vfov(72)
    for k, m in marks().items():
        if k.startswith("_") or "view" not in m:
            continue
        v = m["view"]
        for kk, prx in prox.items():
            prx.hide_render = kk != k
            for extra in (f"PRX_hand_{kk}", f"PRX_label_{kk}"):
                if extra in bpy.data.objects:
                    bpy.data.objects[extra].hide_render = kk != k or extra.startswith("PRX_label")
        RV.look(cam, from_polar(v[0], v[1], 1.65), from_polar(*m["pos"][:2], 1.2))
        sc.render.filepath = str(out / f"eye_{k}.png")
        bpy.ops.render.render(write_still=True)


# ------------------------------------------------------------------------------------------------ the figure

BUNDLE = WS / "assets/models/human_base_meshes/bundle/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"
SRC = "GEO-body_male_realistic"       # Blender Studio Human Base Meshes v1.4.1, CC0 (assets/ASSET_LICENSES.md)
SRC_TOP = 1.684                       # the source's crown (traced)
HEIGHT = 1.88                         # Ross upright (PROFILE §G: tall); stooped he stands about 1.84 at the crown
S_R = HEIGHT / SRC_TOP
HAND_K = 1.12                         # large hands (hands.py's hand is Callum's)
TEX_DIR = HERE / "textures" / "ross"
TEX_PX = 2048
# the stoop, applied as the rest pose (degrees; + bends forward): kyphosis at the chest, the head brought back up
STOOP = {"spine": 4.0, "chest": 12.0, "neck": 10.0, "head": -12.0}
ARM_SWING = 5.0                       # rounded shoulders: the hanging arms a little forward
HIP_CUT = 1.06                        # the coat's body becomes its skirt here (m), above the ragged crotch edge
HEM_Z = 0.40                          # oilskin hem, over the sea boots' tops (0.47)
BOOT_TOP = 0.47
COLLAR_H = 0.050
EASE = {"torso": 0.030, "arm": 0.025}
# cloth (fixed settings, so every build drapes the same): waxed cotton, stiffer in bending than a shirt
CLOTH_R = {"mass": 0.6, "tension": 40.0, "compression": 40.0, "shear": 10.0, "bending": 1.6, "air": 1.0}
SETTLE_R = 36
PART = {"coat": 0, "hat": 1, "boots": 2, "scarf": 3, "skin": 4, "hands": 5, "eyes": 6, "stubble": 7, "hair": 8}
SKIN_PARTS = (4, 5, 6, 7, 8)
BUDGET_TRIS = 25000
_LANDMARKS = {}


def _bd():
    import body as BD
    BD.S = S_R                        # body.py's rig functions read the module's scale at call time
    return BD


def _deselect():
    for o in list(bpy.data.objects):
        try:
            o.select_set(False)
        except RuntimeError:
            pass


def _active(ob):
    _deselect()
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def _apply_mod(ob, name):
    _active(ob)
    with bpy.context.temp_override(object=ob, active_object=ob):
        bpy.ops.object.modifier_apply(modifier=name)


def load_source(coll, level):
    """The CC0 male body and its eyes at a multires level, scaled to Ross, feet at the origin facing -Y."""
    with bpy.data.libraries.load(str(BUNDLE)) as (src, dst):
        dst.objects = [SRC, SRC + ".eye.L", SRC + ".eye.R"]
    body, eyes = dst.objects[0], dst.objects[1:]
    for o in dst.objects:
        coll.objects.link(o)
    bpy.context.view_layer.update()                   # parented eyes: their world matrices exist only after this
    Mb = body.matrix_world.copy()
    _active(body)
    for m in list(body.modifiers):
        if m.type == "MULTIRES":
            m.levels = level
            _apply_mod(body, m.name)
    body.data = body.data.copy()
    body.data.transform(Matrix.Scale(S_R, 4))
    body.matrix_world = Matrix.Identity(4)
    out_eyes = []
    for e in eyes:
        local = Mb.inverted() @ e.matrix_world
        e.parent = None
        e.data = e.data.copy()
        for m in list(e.modifiers):
            if m.type == "MULTIRES":
                _active(e)
                m.levels = 0
                _apply_mod(e, m.name)
        e.data.transform(Matrix.Scale(S_R, 4) @ local)
        e.matrix_world = Matrix.Identity(4)
        out_eyes.append(e)
    for p in body.data.polygons:
        p.use_smooth = True
    return body, out_eyes


def _sphere_push(me, c, r, depth, facing=None):
    """Move vertices within r of c along their normal by depth (smooth falloff); facing filters by normal."""
    for v in me.vertices:
        d = (v.co - c).length
        if d >= r:
            continue
        if facing is not None and v.normal.dot(facing) < 0.2:
            continue
        k = 1.0 - d / r
        v.co += v.normal * (depth * k * k * (3 - 2 * k))


def age_shape(me, eye_l, eye_r):
    """64 and ill: hollow cheeks and temples, a brow that throws shadow, a thinner neck, a thinner chest."""
    fwd = Vector((0, -1, 0))
    for e, sgn in ((eye_l, 1.0), (eye_r, -1.0)):
        _sphere_push(me, e + Vector((0.014 * sgn, 0.004, -0.050)), 0.032, -0.0045, fwd)        # cheek hollow
        _sphere_push(me, e + Vector((0.048 * sgn, 0.030, 0.014)), 0.026, -0.0022)             # temple
        _sphere_push(me, e + Vector((0.004 * sgn, -0.004, 0.024)), 0.022, 0.0022, fwd)        # brow ridge
        corner = e + Vector((-0.004 * sgn, -0.006, -0.083))                                     # the mouth's corner
        for v in me.vertices:                                                                   # turned down, not a smile
            d = (v.co - corner).length
            if d < 0.016 and v.normal.dot(fwd) > 0.1:
                k = (1 - d / 0.016) ** 2
                v.co.z -= 0.0048 * k
                v.co.y += 0.0016 * k
    mid = (eye_l + eye_r) / 2
    for v in me.vertices:                                                                       # thinner lips
        rel = v.co - (mid + Vector((0, -0.01, -0.078)))
        if abs(rel.x) < 0.026 and abs(rel.z) < 0.009 and v.normal.dot(fwd) > 0.3:
            v.co.y += 0.0022 * (1 - abs(rel.x) / 0.026)
    # a closed, set mouth: the lower lip back and up against the upper (a lit lower lip under a dark parting
    # read as a grin under the brim in the B still, s10)
    lc = mid + Vector((0, -0.01, -0.078))
    for v in me.vertices:
        rel = v.co - lc
        if abs(rel.x) < 0.028 and -0.016 < rel.z < -0.001 and v.normal.dot(fwd) > 0.2:
            k = (1 - abs(rel.x) / 0.028) * min(1.0, (rel.z + 0.016) / 0.006)
            v.co.y += 0.0030 * k
            v.co.z += 0.0016 * k
    for v in me.vertices:
        z = v.co.z / S_R
        if 1.40 < z < 1.52 and abs(v.co.x) < 0.09 * S_R:                                      # neck
            k = min(1.0, (z - 1.40) / 0.03, (1.52 - z) / 0.03)
            v.co.x *= 1.0 - 0.07 * k
            v.co.y = (v.co.y + 0.03 * S_R) * (1.0 - 0.07 * k) - 0.03 * S_R
        elif 0.95 < z < 1.38 and abs(v.co.x) < 0.17 * S_R:                                    # chest, belly
            k = min(1.0, (z - 0.95) / 0.08, (1.38 - z) / 0.08)
            v.co.y *= 1.0 - 0.07 * k
            v.co.x *= 1.0 - 0.03 * k
    for v in me.vertices:                                     # broad shoulders (a seaman's frame, thinned)
        z = v.co.z / S_R
        if 1.15 < z < 1.48:
            k = min(1.0, (z - 1.15) / 0.15) * min(1.0, (1.48 - z) / 0.05)
            if abs(v.co.x) > 0.15 * S_R:                       # the arms move out with the shoulder
                v.co.x += math.copysign(0.022 * min(1.0, (z - 1.15) / 0.15), v.co.x) if z < 1.42 else 0.0
            else:
                v.co.x *= 1.0 + 0.07 * k
        elif 0.70 < z <= 1.15 and abs(v.co.x) > 0.17 * S_R:
            v.co.x += math.copysign(0.022, v.co.x)
    me.update()


def stoop_rest(arm, meshes):
    """Pose the stoop and apply it as the rest pose, so the coat drapes on it and every clip starts from it."""
    BD = _bd()
    BD.rest(arm)
    for b, deg in STOOP.items():
        BD.set_rot(arm, b, Vector((1, 0, 0)), deg)
    BD.arms_down(arm, ARM_SWING, ARM_SWING)
    bpy.context.view_layer.update()
    for ob in meshes:
        _apply_mod(ob, "Armature")
    _active(arm)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    for ob in meshes:
        m = ob.modifiers.new("Armature", "ARMATURE")
        m.object = arm


def dominant(ob):
    gi = {g.index: g.name for g in ob.vertex_groups}
    out = []
    for v in ob.data.vertices:
        best, w = "", 0.0
        for g in v.groups:
            if g.weight > w:
                best, w = gi[g.group], g.weight
        out.append(best)
    return out


def keep_faces(ob, pred):
    """Delete the faces whose vertices do not all satisfy pred(vertex index, co)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    kill = [f for f in bm.faces if not all(pred(v.index, v.co) for v in f.verts)]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()


def decimate(ob, tris):
    ob.data.calc_loop_triangles()
    n = len(ob.data.loop_triangles)
    if n <= tris:
        return
    m = ob.modifiers.new("dec", "DECIMATE")
    m.ratio = tris / n
    m.use_collapse_triangulate = True
    bpy.ops.object.mode_set(mode="OBJECT")
    ob.modifiers.move(len(ob.modifiers) - 1, 0)
    _apply_mod(ob, "dec")


def bone_frame(arm, name):
    b = arm.data.bones[name]
    M = b.matrix_local
    return b.head_local.copy(), b.tail_local.copy(), M.col[0].xyz.normalized(), M.col[1].xyz.normalized(), M.col[2].xyz.normalized()


def _rename_groups(ob, mapping):
    for g in ob.vertex_groups:
        if g.name in mapping:
            g.name = mapping[g.name]


def graft_hands(arm, coll):
    """hands.py's CC0 realistic hand and its 16-bone rig (traced joints, grips fitted in Stage P), scaled for a
    big man's hand and set on body.py's hand bone with the thumb forward; the oilskin cuff hides the wrist."""
    import hands as HD
    src = HD.source_hand()
    out = []
    W = Vector(HD.WRIST)
    for side in ("L", "R"):
        h = src.copy()
        h.data = src.data.copy()
        coll.objects.link(h)
        h.name = f"TMP_hand_{side}"
        for p in h.data.polygons:
            p.use_smooth = True
        if side == "R":
            HD.mirror_object(h)
        wrist_z = HD.CUFF_Z - W.z                         # the real wrist, in the source frame (wrist centre = 0)
        keep_faces(h, lambda i, co: co.z < wrist_z + 0.07)
        decimate(h, 1900)
        hr = HD.build_armature(f"TMP_hrig_{side}", coll, mirror=side == "R")
        _deselect()
        h.select_set(True)
        hr.select_set(True)
        bpy.context.view_layer.objects.active = hr
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        sgn = 1.0 if side == "L" else -1.0
        d_s = (Vector(HD.PALM) - W).normalized()
        pal = Vector((0, 1, 0))                                   # the source's palm faces +Y (hands.py)
        t_s = (pal - d_s * pal.dot(d_s)).normalized()
        hh, ht, _, _, _ = bone_frame(arm, f"hand.{side}")
        d_r = (ht - hh).normalized()
        med = Vector((-sgn, 0.3, 0))                              # hanging: the palm to the thigh, a little back
        t_r = (med - d_r * med.dot(d_r)).normalized()
        Bs = Matrix((d_s, t_s, d_s.cross(t_s))).transposed()
        Br = Matrix((d_r, t_r, d_r.cross(t_r))).transposed()
        T = (Matrix.Translation(hh) @ (Br @ Bs.transposed()).to_4x4() @ Matrix.Scale(HAND_K, 4) @
             Matrix.Translation(-Vector((0, 0, wrist_z))))
        h.parent = None
        h.data.transform(T)
        h.matrix_world = Matrix.Identity(4)
        hr.data.transform(T)
        names = [b.name for b in hr.data.bones]
        for b in hr.data.bones:
            b.name = f"graft.{side}" if b.name == "hand" else f"{b.name}.{side}"
        _rename_groups(h, {n: (f"hand.{side}" if n == "hand" else f"{n}.{side}") for n in names})
        # the stub above the wrist is forearm skin: it turns with the forearm, not the hand, so a bent wrist
        # does not swing it out through the sleeve (the A still, s10)
        gF = h.vertex_groups.new(name=f"forearm.{side}")
        for v in h.data.vertices:
            s = (v.co - hh).dot(d_r)
            if s >= 0.0:
                continue
            wf = min(1.0, -s / 0.025)
            old = [(g.group, g.weight) for g in v.groups if g.group != gF.index]
            for gi_, w in old:
                h.vertex_groups[gi_].add([v.index], w * (1.0 - wf), "REPLACE")
            gF.add([v.index], wf, "REPLACE")
        for m in list(h.modifiers):
            h.modifiers.remove(m)
        _deselect()
        hr.select_set(True)
        arm.select_set(True)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode="EDIT")
        eb = arm.data.edit_bones
        for b in eb:
            if b.parent and b.parent.name == f"graft.{side}":
                b.parent = eb[f"hand.{side}"]
                b.use_connect = False
        eb.remove(eb[f"graft.{side}"])
        bpy.ops.object.mode_set(mode="OBJECT")
        h.parent = arm
        m = h.modifiers.new("Armature", "ARMATURE")
        m.object = arm
        out.append(h)
    bpy.data.objects.remove(src, do_unlink=True)
    return out


def _ring_order(bm, edges):
    """Order the vertices of a closed loop of boundary edges."""
    adj = {}
    for e in edges:
        a, b = e.verts
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    start = next(iter(adj))
    ring, prev, cur = [start], None, start
    while True:
        nxt = [v for v in adj[cur] if v is not prev]
        if not nxt or nxt[0] is start:
            break
        prev, cur = cur, nxt[0]
        ring.append(cur)
        if len(ring) > len(adj):
            break
    return ring


def _ring_angle(verts, axis):
    """Boundary vertices of a star-shaped cut, ordered by angle round their centre (about axis)."""
    c = sum((v.co for v in verts), Vector()) / max(1, len(verts))
    a = Vector((1, 0, 0))
    a = (a - axis * a.dot(axis)).normalized()
    b = axis.cross(a)
    return sorted(verts, key=lambda v: math.atan2((v.co - c).dot(b), (v.co - c).dot(a)))


def _hull2d(pts):
    """Convex hull (monotone chain) of 2D points, counter-clockwise."""
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def _ray_hull(c, d, hull):
    """Distance from c (inside) along the unit 2D direction d to the hull's boundary."""
    best = None
    for i in range(len(hull)):
        a, b = hull[i], hull[(i + 1) % len(hull)]
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-12:
            continue
        wx, wy = a[0] - c[0], a[1] - c[1]
        t = (wx * ey - wy * ex) / den
        s = (wx * d[1] - wy * d[0]) / den
        if t > 0 and -1e-9 <= s <= 1 + 1e-9:
            best = t if best is None else min(best, t)
    return best


HANG = 0.20                  # the coat front may fall back at most 20 cm per metre below any point above it
# checkpoint review (2026-11-18): the shell followed the body's pecs and sternum through the drape, so the
# chest read as a bust in the B still and the neutral front view


def fill_torso(verts, z0, z1, step=0.02, front_x=0.17, z_full=None):
    """Oilskin bridges the body's hollows: every horizontal slice of the torso is pushed out to its convex
    hull (no sternum valley, no spine groove), then the front hangs from the chest: it never falls back more
    than HANG below any point above it (no shadow under the pecs). Only ever moves vertices outward.
    Below z_full the push fades out to nothing at z0 (no ledge where the filled torso meets the skirt)."""

    def fade(z):
        return 1.0 if z_full is None or z >= z_full else max(0.0, (z - z0) / (z_full - z0))
    bins = {}
    for v in verts:
        if z0 <= v.co.z <= z1:
            bins.setdefault(int(math.floor(v.co.z / step)), []).append(v)
    cen = {}
    for k, vs in bins.items():
        vs = [v for v in vs if abs(v.co.x) < 0.22]     # elbows beside the waist are not torso (s11: a pannier)
        bins[k] = vs
        hull = _hull2d([(round(v.co.x, 5), round(v.co.y, 5)) for v in vs])
        if len(hull) < 3:
            continue
        cx = sum(p[0] for p in hull) / len(hull)
        cy = sum(p[1] for p in hull) / len(hull)
        cen[k] = cy
        for v in vs:
            dx, dy = v.co.x - cx, v.co.y - cy
            r = math.hypot(dx, dy)
            if r < 1e-6:
                continue
            t = _ray_hull((cx, cy), (dx / r, dy / r), hull)
            if t and t > r:
                f = fade(v.co.z)
                v.co.x, v.co.y = cx + dx / r * (r + (t - r) * f), cy + dy / r * (r + (t - r) * f)
    cols = {}
    for k, vs in bins.items():
        if k not in cen:
            continue
        for v in vs:
            if abs(v.co.x) < front_x and v.co.y < cen[k] - 0.03:          # the front (-Y) half only
                cols.setdefault(int(math.floor(v.co.x / 0.025)), []).append(v)
    moved = 0
    for vs in cols.values():
        vs.sort(key=lambda v: -v.co.z)
        run = None
        for v in vs:
            if run is not None and v.co.y + HANG * v.co.z > run:
                v.co.y += (run - HANG * v.co.z - v.co.y) * fade(v.co.z)
                moved += 1
            g = v.co.y + HANG * v.co.z
            run = g if run is None else min(run, g)
    return moved


def sleeve_tubes(bm, AW, arm):
    """A sleeve is a roomy tube, not the arm's muscles: round the bone axis, as wide at every point as the
    widest part below it (no bicep, no deltoid bulge), belling 12 mm over the last 7 cm to the cuff. The side
    toward the body grows at most 6 mm, so the sleeve does not swallow the coat's flank."""
    for side in ("L", "R"):
        sgn = 1 if side == "L" else -1
        segs = [bone_frame(arm, f"upper_arm.{side}")[:2], bone_frame(arm, f"forearm.{side}")[:2]]
        L0 = (segs[0][1] - segs[0][0]).length
        vs = [v for v in bm.verts if v[AW] > 0.5 and v.co.x * sgn > 0.05]
        info = []
        for v in vs:
            best = None
            for k, (a, b) in enumerate(segs):
                ab = b - a
                t = max(0.0, min(1.0, (v.co - a).dot(ab) / ab.length_squared))
                p = a + ab * t
                d = (v.co - p).length
                if best is None or d < best[0]:
                    best = (d, p, t * ab.length + (L0 if k else 0.0))
            info.append(best)
        if not info:
            continue
        B = 0.03
        mx = {}
        for d, p, u in info:
            if u < 0.12:                                   # the shoulder cap is not the sleeve's width
                continue
            k = int(u // B)
            mx[k] = max(mx.get(k, 0.0), d)
        ks = sorted(mx)
        sm = {k: max(mx.get(j, 0.0) for j in range(k - 1, k + 2)) for k in ks}
        R, run = {}, 0.0
        for k in reversed(ks):
            run = max(run, sm[k])
            R[k] = run
        Lt = max(u for _, _, u in info)
        for v, (d, p, u) in zip(vs, info):
            if d < 1e-5:
                continue
            target = R[max(int(u // B), ks[0])] + 0.012 * max(0.0, (u - (Lt - 0.07)) / 0.07)
            target = min(target, d + 0.030)                # never more than 30 mm of new room
            rd = (v.co - p) / d
            if rd.x * sgn < -0.6:
                target = min(target, d + 0.006)
            w = min(1.0, (v[AW] - 0.5) / 0.3) * min(1.0, u / 0.12)
            v.co = p + rd * (d + max(0.0, target - d) * w)


def arm_flags(ob, thr=0.15):
    gi = {g.index: g.name for g in ob.vertex_groups}
    return [sum(g.weight for g in v.groups if gi[g.group].split(".")[0] in ("upper_arm", "forearm", "hand")) > thr
            for v in ob.data.vertices]


def cuff_weights(ob, arm, share=0.35):
    """The last 8 cm of each sleeve follows the hand by up to `share`: a hard-bent wrist turns the cuff with it
    instead of tearing out through it (the A and B stills, s10)."""
    vg = {g.name: g for g in ob.vertex_groups}
    for side in ("L", "R"):
        fh, ft, _, _, _ = bone_frame(arm, f"forearm.{side}")
        d = (ft - fh).normalized()
        L = (ft - fh).length
        gf = vg[f"forearm.{side}"]
        gh = vg.get(f"hand.{side}") or ob.vertex_groups.new(name=f"hand.{side}")
        for v in ob.data.vertices:
            s = (v.co - fh).dot(d)
            if s < L - 0.08 or ((v.co - fh) - d * s).length > 0.12:
                continue
            wf = sum(g.weight for g in v.groups if g.group == gf.index)
            if wf < 0.5:
                continue
            k = share * min(1.0, (s - (L - 0.08)) / 0.10)
            gf.add([v.index], wf * (1 - k), "REPLACE")
            gh.add([v.index], wf * k, "REPLACE")


def coat_details(sh, coll):
    """What makes it a coat and not a gown: two hip pocket flaps and four horn buttons down the off-centre
    closure, each laid onto the draped shell by rays from the front. Returns (flaps, buttons)."""
    from mathutils.bvhtree import BVHTree
    from mathutils import Matrix
    bm0 = bmesh.new()
    bm0.from_mesh(sh.data)
    bvh = BVHTree.FromBMesh(bm0)
    bm0.free()

    def onto(x, z, off):
        h = bvh.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)))
        if h[0] is None:
            return None
        n = h[1] if h[1].y < 0 else -h[1]
        if abs(n.x) > 0.7:
            return None
        return h[0] + n * off, n
    bm = bmesh.new()
    placed = {"flaps": 0, "buttons": 0}
    for sgn in (1, -1):
        cx, top, W, H = 0.105 * sgn, 0.885, 0.13, 0.060      # inside the hanging hands (0.115 / 0.15 hit the R sleeve)
        grids = []
        for off0, off1 in ((0.0045, 0.0085), (0.0008, 0.0010)):        # the flap's face, then its underside
            g = []
            for j in range(3):
                row = []
                for i in range(5):
                    o = onto(cx + (i / 4 - 0.5) * W * (1 - 0.06 * j), top - j / 2 * H, off0 + (off1 - off0) * j / 2)
                    row.append(o[0] if o else None)
                g.append(row)
            grids.append(g)
        if any(p is None for g in grids for row in g for p in row):
            continue
        tv = [[bm.verts.new(p) for p in row] for row in grids[0]]
        uv_ = [[bm.verts.new(p) for p in row] for row in grids[1]]
        for G, flip in ((tv, False), (uv_, True)):
            for j in range(2):
                for i in range(4):
                    q = (G[j][i], G[j + 1][i], G[j + 1][i + 1], G[j][i + 1])
                    bm.faces.new(tuple(reversed(q)) if flip else q)
        loop = [(0, i) for i in range(5)] + [(j, 4) for j in (1, 2)] + [(2, i) for i in (3, 2, 1, 0)] + [(1, 0)]
        for (a0, a1), (b0, b1) in zip(loop, loop[1:] + loop[:1]):
            bm.faces.new((tv[a0][a1], uv_[a0][a1], uv_[b0][b1], tv[b0][b1]))
        placed["flaps"] += 1
    flaps = None
    if placed["flaps"]:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        flaps = _mesh_ob("TMP_flaps", bm, coll)
    else:
        bm.free()
    bm = bmesh.new()
    for z in (1.43, 1.29, 1.15, 1.01):
        o = onto(0.030, z, 0.0030)
        if o is None:
            continue
        p, n = o
        r = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.0115, radius2=0.0095, depth=0.0045)
        M = Matrix.Translation(p) @ Vector((0, 0, 1)).rotation_difference(n).to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=M, verts=r["verts"])
        placed["buttons"] += 1
    buttons = None
    if placed["buttons"]:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        buttons = _mesh_ob("TMP_buttons", bm, coll)
    else:
        bm.free()
    print("ROSS_DETAILS", json.dumps(placed))
    return flaps, buttons


def coat_shell(body0, arm, coll):
    """The oilskin before it falls: the body's torso and arms eased out, cut by planes at the hips, the neck and
    the wrists (each a clean loop), a lathed skirt bridged on at the hips and flaring to the hem, and a 5 cm
    collar turned up, open at the throat (the scarf's knot shows there)."""
    dom = dominant(body0)
    sh = body0.copy()
    sh.data = body0.data.copy()
    sh.name = "TMP_coat"
    coll.objects.link(sh)
    for m in list(sh.modifiers):
        sh.modifiers.remove(m)
    # which vertices are arm (from the rig's weights, carried as a layer the bisects interpolate): the forearms
    # hang beside the hips, so no distance test can tell a sleeve from a hip
    gi = {g.index: g.name for g in sh.vertex_groups}
    aw = sh.data.attributes.new("armw", "FLOAT", "POINT")
    for v in sh.data.vertices:
        aw.data[v.index].value = sum(g.weight for g in v.groups if gi[g.group].split(".")[0] in ("upper_arm", "forearm", "hand"))
    okb = ("hips", "spine", "chest", "neck", "upper_arm", "forearm", "thigh")
    keep_faces(sh, lambda i, co: dom[i].split(".")[0] in okb)
    nh, nt, _, _, _ = bone_frame(arm, "neck")
    nd = (nt - nh).normalized()
    neck_c = nh + nd * 0.015
    bm = bmesh.new()
    bm.from_mesh(sh.data)
    AW = bm.verts.layers.float.get("armw")

    def bisect(co, no, which):
        vs = [v for v in bm.verts if which(v)]
        S = set(vs)
        es = [e for e in bm.edges if e.verts[0] in S and e.verts[1] in S]
        fs = [f for f in bm.faces if all(v in S for v in f.verts)]
        bmesh.ops.bisect_plane(bm, geom=vs + es + fs, dist=1e-5, plane_co=co, plane_no=no, clear_outer=True)

    def is_arm(v):
        return v[AW] > 0.5
    bisect(Vector((0, 0, HIP_CUT)), Vector((0, 0, -1)), lambda v: not is_arm(v))
    bisect(neck_c, nd, lambda v: abs(v.co.x) < 0.2 and v.co.z > 1.2)
    for side in ("L", "R"):
        hh, ht, _, _, _ = bone_frame(arm, f"hand.{side}")
        fh, ft, _, _, _ = bone_frame(arm, f"forearm.{side}")
        d = (ft - fh).normalized()
        sgn = 1 if side == "L" else -1
        bisect(hh + d * 0.025, d, lambda v, sgn=sgn: v.co.x * sgn > 0.12 and is_arm(v))
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    _keep_biggest(bm)
    bm.normal_update()
    for v in bm.verts:
        e = EASE["arm"] if is_arm(v) else EASE["torso"]
        if not is_arm(v):                                       # a man's long oilskin: no waist
            k = max(0.0, 1.0 - abs(v.co.z - 1.08) / 0.18)
            e += 0.010 * k * k * (3 - 2 * k)                   # 0.030 before the hull fill made it a pear
        v.co += v.normal * e
    # the chest hangs flat from the shoulders (no pecs, no sternum valley under oilskin)
    front = [v for v in bm.verts if not is_arm(v) and 1.10 < v.co.z < 1.48 and v.co.y < -0.02]
    for _ in range(14):
        bmesh.ops.smooth_vert(bm, verts=front, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=False)
    sleeve = [v for v in bm.verts if is_arm(v) and not v.is_boundary]
    for _ in range(8):                                  # the arm's muscles out of the sleeve before it is made a tube
        bmesh.ops.smooth_vert(bm, verts=sleeve, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.normal_update()
    sleeve_tubes(bm, AW, arm)
    fill_torso([v for v in bm.verts if v[AW] < 0.15], HIP_CUT - 0.02, 1.50)
    # the skirt: the clean hip loop extruded down, in its own order (no bridge, no twist), folds widening to the hem
    hip_e = [e for e in bm.edges if e.is_boundary and all(abs(v.co.z - HIP_CUT) < 0.05 and not is_arm(v) for v in e.verts)]
    hv = list({v for e in hip_e for v in e.verts})
    ring = _ring_angle(hv, Vector((0, 0, 1)))
    print("ROSS_SKIRT", json.dumps({"hip_edges": len(hip_e), "ring": len(ring)}))
    c = sum((v.co for v in ring), Vector()) / len(ring)
    rows = 10
    prev = ring
    for k in range(1, rows + 1):
        t = k / rows
        z = HIP_CUT + (HEM_Z - HIP_CUT) * t
        cur = []
        for v in ring:
            d = Vector((v.co.x - c.x, v.co.y - c.y, 0.0))
            a_ = math.atan2(d.y, d.x)
            fold = 0.022 * t ** 1.5 * math.sin(7 * a_ + 0.9 * math.sin(3 * a_))
            back = 1.0 + 0.05 * t * max(0.0, math.sin(a_))
            r = d.length * (1.0 + 0.08 * t ** 1.2) * back + fold
            cur.append(bm.verts.new(Vector((c.x, c.y, z)) + d.normalized() * r))
        n = len(ring)
        for i_ in range(n):
            j_ = (i_ + 1) % n
            try:
                bm.faces.new((prev[i_], prev[j_], cur[j_], cur[i_]))
            except ValueError:
                pass
        prev = cur
    waist = [v for v in bm.verts if abs(v.co.z - HIP_CUT) < 0.11 and not is_arm(v)]
    for _ in range(4):
        bmesh.ops.smooth_vert(bm, verts=waist, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    # the collar: the neck loop stands up and a little out, open at the throat
    nk_e = [e for e in bm.edges if e.is_boundary and all(abs((v.co - neck_c).dot(nd)) < 0.06 and v.co.z > 1.2 and abs(v.co.x) < 0.25 for v in e.verts)]
    ring = _ring_order(bm, nk_e)
    cc = sum((v.co for v in ring), Vector()) / len(ring)
    prev = ring
    for k in (1, 2):
        t = k / 2
        cur = [bm.verts.new(cc + (v.co - cc) * (1.0 + 0.10 * t) + nd * (COLLAR_H * t)) for v in ring]
        n = len(ring)
        for i in range(n):
            j = (i + 1) % n
            mid = (prev[i].co + prev[j].co) / 2 - cc
            if mid.y < 0 and abs(math.degrees(math.atan2(mid.x, -mid.y))) < 22:
                continue
            try:
                bm.faces.new((prev[i], prev[j], cur[j], cur[i]))
            except ValueError:
                pass
        prev = cur
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(sh.data)
    bm.free()
    sh.vertex_groups.clear()
    if "armw" in sh.data.attributes:
        sh.data.attributes.remove(sh.data.attributes["armw"])
    return sh


def _keep_biggest(bm):
    seen, islands = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        st, isl = [v], []
        seen.add(v)
        while st:
            x = st.pop()
            isl.append(x)
            for e in x.link_edges:
                o = e.other_vert(x)
                if o not in seen:
                    seen.add(o)
                    st.append(o)
        islands.append(isl)
    islands.sort(key=len, reverse=True)
    for isl in islands[1:]:
        bmesh.ops.delete(bm, geom=isl, context="VERTS")


def drape(sh, body0, coll, settle=SETTLE_R):
    """Blender cloth, fixed settings: the shell hangs from its yoke and collar and falls onto the body."""
    sc = bpy.context.scene
    decimate(sh, 5200)
    yoke = 1.40 * S_R - 0.06
    pins = [v.index for v in sh.data.vertices if (v.co.z > yoke and abs(v.co.x) < 0.24)
            or (abs(v.co.z - HIP_CUT) < 0.06 and abs(v.co.x) < 0.30)]                  # the waist keeps its line
    vg = sh.vertex_groups.new(name="pin")
    vg.add(pins, 1.0, "REPLACE")
    col = body0.copy()
    col.data = body0.data.copy()
    col.name = "TMP_collider"
    coll.objects.link(col)
    for m in list(col.modifiers):
        col.modifiers.remove(m)
    col.modifiers.new("collision", "COLLISION")
    col.collision.thickness_outer = 0.006
    cl = sh.modifiers.new("cloth", "CLOTH")
    s = cl.settings
    s.quality = 8
    s.mass = CLOTH_R["mass"]
    s.air_damping = CLOTH_R["air"]
    s.tension_stiffness = CLOTH_R["tension"]
    s.compression_stiffness = CLOTH_R["compression"]
    s.shear_stiffness = CLOTH_R["shear"]
    s.bending_stiffness = CLOTH_R["bending"]
    s.tension_damping = s.compression_damping = s.shear_damping = 5.0
    s.vertex_group_mass = "pin"
    cs = cl.collision_settings
    cs.collision_quality = 3
    cs.distance_min = 0.005
    cs.use_self_collision = True
    cs.self_distance_min = 0.004
    cl.point_cache.frame_start = 1
    cl.point_cache.frame_end = settle
    for f in range(1, settle + 1):
        sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(sh.evaluated_get(dg))
    sc.frame_set(1)
    old = sh.data
    sh.modifiers.remove(cl)
    sh.data = me
    bpy.data.meshes.remove(old)
    bpy.data.objects.remove(col, do_unlink=True)
    sh.vertex_groups.clear()
    bm = bmesh.new()
    bm.from_mesh(sh.data)
    for _ in range(3):
        bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if not v.is_boundary], factor=0.5,
                              use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.to_mesh(sh.data)
    bm.free()
    _bd().turn_in(sh, 0.009)
    for p in sh.data.polygons:
        p.use_smooth = True
    return sh


def transfer_weights(dst, src):
    """Vertex groups from the full body (nearest face, interpolated): the clothes move with the rig."""
    for g in src.vertex_groups:
        if g.name not in dst.vertex_groups:
            dst.vertex_groups.new(name=g.name)
    _deselect()
    dst.select_set(True)
    src.select_set(True)
    bpy.context.view_layer.objects.active = src
    bpy.ops.object.data_transfer(use_reverse_transfer=False, data_type="VGROUP_WEIGHTS", vert_mapping="POLYINTERP_NEAREST",
                                 layers_select_src="ALL", layers_select_dst="NAME", mix_mode="REPLACE")


def smooth_weights(ob, repeat, factor):
    """Average each vertex's weights with its neighbours' (all groups), then normalise: no sleeve tears where the
    transfer picked neighbouring faces of different bones."""
    me = ob.data
    nb = [[] for _ in me.vertices]
    for e in me.edges:
        a, b = e.vertices
        nb[a].append(b)
        nb[b].append(a)
    G = len(ob.vertex_groups)
    W = [[0.0] * G for _ in me.vertices]
    for v in me.vertices:
        for g in v.groups:
            W[v.index][g.group] = g.weight
    for _ in range(repeat):
        N = []
        for i, ns in enumerate(nb):
            if not ns:
                N.append(W[i])
                continue
            avg = [sum(W[j][g] for j in ns) / len(ns) for g in range(G)]
            N.append([W[i][g] * (1 - factor) + avg[g] * factor for g in range(G)])
        W = N
    for i, ws in enumerate(W):
        t = sum(ws) or 1.0
        for g, w in enumerate(ws):
            w /= t
            if w > 0.01:
                ob.vertex_groups[g].add([i], w, "REPLACE")
            else:
                ob.vertex_groups[g].remove([i])


def skirt_weights(ob):
    """Below the hips the coat follows the pelvis, a little of each thigh on its own side, never the shins."""
    vg = {g.name: g for g in ob.vertex_groups}
    for v in ob.data.vertices:
        if v.co.z >= HIP_CUT + 0.04:
            continue
        t = max(0.0, min(1.0, (HIP_CUT + 0.04 - v.co.z) / 0.35))
        sx = max(-1.0, min(1.0, v.co.x / 0.12))
        for g in list(v.groups):
            ob.vertex_groups[g.group].remove([v.index])
        wl, wr = 0.45 * t * max(0.0, sx), 0.45 * t * max(0.0, -sx)
        vg["hips"].add([v.index], 1.0 - wl - wr, "REPLACE")
        if wl > 0.01:
            vg["thigh.L"].add([v.index], wl, "REPLACE")
        if wr > 0.01:
            vg["thigh.R"].add([v.index], wr, "REPLACE")


def rigid(ob, bone, arm):
    ob.vertex_groups.clear()
    g = ob.vertex_groups.new(name=bone)
    g.add([v.index for v in ob.data.vertices], 1.0, "REPLACE")
    ob.parent = arm
    m = ob.modifiers.new("Armature", "ARMATURE")
    m.object = arm


def _mesh_ob(name, bm, coll):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def head_frame(arm):
    """(origin at the head bone's head, up, forward, right) in the rest pose."""
    h, t, x, y, z = bone_frame(arm, "head")
    up = (t - h).normalized()
    fw = z - up * z.dot(up)
    if fw.y > 0:
        fw = -fw
    fw.normalize()
    return h, up, fw, fw.cross(up).normalized() * -1.0


def skull(head_ob, arm, eyes):
    """Head landmarks in the head frame: the eyes' height, the skull's ellipse at any height, the chin."""
    o, up, fw, rt = head_frame(arm)
    pts = [(v.co - o) for v in head_ob.data.vertices]
    loc = [(p.dot(rt), p.dot(fw), p.dot(up)) for p in pts]
    eye_u = sum(((e - o).dot(up) for e in eyes), 0.0) / len(eyes)
    top_u = max(l[2] for l in loc)

    def ellipse(u, h=0.008):
        sl = [l for l in loc if abs(l[2] - u) < h]
        if len(sl) < 6:
            return None
        s0, s1 = min(l[0] for l in sl), max(l[0] for l in sl)
        f0, f1 = min(l[1] for l in sl), max(l[1] for l in sl)
        return (s0 + s1) / 2, (f0 + f1) / 2, (s1 - s0) / 2, (f1 - f0) / 2
    face = [l for l in loc if abs(l[0]) < 0.015 and eye_u - 0.16 < l[2] < eye_u - 0.07]
    fmax = max((l[1] for l in face), default=0.08)
    front = [l for l in face if l[1] > fmax - 0.03]
    chin = min(front, key=lambda l: l[2]) if front else (0.0, 0.06, eye_u - 0.12)
    mid = [l for l in loc if abs(l[0]) < 0.012 and -0.07 < l[2] - eye_u < -0.005]
    nose = max(mid, key=lambda l: l[1]) if mid else (0.0, 0.11, eye_u - 0.035)
    cheeks = [o + rt * (sg * 0.046) + fw * (nose[1] - 0.045) + up * (eye_u - 0.028) for sg in (1, -1)]
    return {"o": o, "up": up, "fw": fw, "rt": rt, "eye_u": eye_u, "top_u": top_u, "ellipse": ellipse, "chin": chin,
            "nose": o + rt * nose[0] + fw * nose[1] + up * nose[2], "cheeks": cheeks,
            "mouth": o + rt * nose[0] + fw * (nose[1] - 0.014) + up * (nose[2] - 0.042)}


def to_world(K, s, f, u):
    return K["o"] + K["rt"] * s + K["fw"] * f + K["up"] * u


def souwester(K, coll):
    """A sou'wester with a real brim: a four-panel crown over the skull, the brim short in front and long at the
    back (it sheds water off the neck), turned down, 4 mm thick with a rolled edge; chin ties."""
    bm = bmesh.new()
    seg = 28
    u_b = K["eye_u"] + 0.022                          # the band sits low on the forehead, just above the brow
    base = K["ellipse"](u_b) or (0.0, -0.01, 0.085, 0.10)
    cs, cf = base[0], base[1]
    rows = []
    hs = [u_b - 0.012]
    top = K["top_u"]
    for k in range(1, 9):
        hs.append(u_b + (top - u_b) * k / 8)
    for i, u in enumerate(hs):
        e = K["ellipse"](min(u, top - 0.006)) or base
        grow = 0.010 + 0.001 * (i / len(hs))
        a, b = e[2] + grow, e[3] + grow
        if u >= top - 0.002:
            a, b = a * 0.62, b * 0.62
        rows.append([bm.verts.new(to_world(K, cs + a * math.cos(2 * math.pi * j / seg), cf + b * math.sin(2 * math.pi * j / seg), u + (0.012 if i == len(hs) - 1 else 0.0)))
                     for j in range(seg)])
    cap = bm.verts.new(to_world(K, cs, cf, top + 0.010))
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(seg):
            bm.faces.new((r0[j], r0[(j + 1) % seg], r1[(j + 1) % seg], r1[j]))
    for j in range(seg):
        bm.faces.new((rows[-1][j], rows[-1][(j + 1) % seg], cap))
    # the brim, from the band outward: width and droop by direction (0 = front)
    a0, b0 = base[2] + 0.013, base[3] + 0.013

    def brim_pt(j, t, under):
        th = 2 * math.pi * j / seg                      # sin > 0: front (fw)
        front = math.sin(th)
        # the sou'wester: a short, nearly flat front (6.5 cm), sides 9 cm at 20 deg, a long back (16 cm) at 34 deg
        w = 0.065 + 0.025 * (1 - abs(front)) + (0.070 * -front if front < 0 else 0.0)
        droop = math.radians((6 + 14 * (1 - front) if front >= 0 else 20 + 14 * -front))
        r = t * w
        ds = math.cos(th) * (a0 + r * math.cos(droop))
        df = math.sin(th) * (b0 + r * math.cos(droop))
        du = -math.sin(droop) * r - 0.005 * t * t * math.sin(5 * th + 0.7) - (0.004 if under else 0.0)
        return to_world(K, cs + ds, cf + df, u_b - 0.004 + du)
    ts = (0.0, 0.35, 0.7, 1.0)
    top_r = [[bm.verts.new(brim_pt(j, t, False)) for j in range(seg)] for t in ts]
    bot_r = [[bm.verts.new(brim_pt(j, t, True)) for j in range(seg)] for t in ts]
    for R, flip in ((top_r, False), (bot_r, True)):
        for r0, r1 in zip(R, R[1:]):
            for j in range(seg):
                q = (r0[j], r0[(j + 1) % seg], r1[(j + 1) % seg], r1[j])
                bm.faces.new(tuple(reversed(q)) if flip else q)
    for j in range(seg):                                # the rolled edge (top to underside)
        q = (top_r[-1][j], top_r[-1][(j + 1) % seg], bot_r[-1][(j + 1) % seg], bot_r[-1][j])
        bm.faces.new(q)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    hat = _mesh_ob("TMP_hat", bm, coll)
    # chin ties: from under the brim at the ears, down the cheeks, to a knot under the chin
    bm = bmesh.new()
    chin = K["chin"]
    for sgn in (1, -1):
        p0 = (cs + sgn * (a0 - 0.006), cf - 0.012, u_b - 0.012)
        p1 = (sgn * 0.058, 0.035, K["eye_u"] - 0.075)
        p2 = (sgn * 0.012, chin[1] - 0.025, chin[2] - 0.012)
        pts = [Vector(p0).lerp(Vector(p1), t) for t in (0.0, 0.33, 0.66)] + [Vector(p1).lerp(Vector(p2), t) for t in (0.0, 0.5, 1.0)]
        rings = []
        for k, p in enumerate(pts):
            c = to_world(K, *p)
            nxt = to_world(K, *(pts[min(k + 1, len(pts) - 1)])) - to_world(K, *(pts[max(k - 1, 0)]))
            d = nxt.normalized()
            a = d.cross(K["fw"]).normalized()
            b = d.cross(a).normalized()
            rings.append([bm.verts.new(c + a * 0.0035 * math.cos(2 * math.pi * i / 6) + b * 0.0015 * math.sin(2 * math.pi * i / 6)) for i in range(6)])
        for r0, r1 in zip(rings, rings[1:]):
            for i in range(6):
                bm.faces.new((r0[i], r0[(i + 1) % 6], r1[(i + 1) % 6], r1[i]))
    knot = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.008)
    for v in knot["verts"]:
        v.co = to_world(K, 0.0, chin[1] - 0.028, chin[2] - 0.018) + Vector((v.co.x, v.co.y * 0.8, v.co.z * 0.7))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ties = _mesh_ob("TMP_ties", bm, coll)
    return hat, ties


def scarf(arm, body0, coll):
    """A knotted grey wool scarf: a thick roll round the neck inside the collar, the knot at the throat."""
    nh, nt, _, _, z = bone_frame(arm, "neck")
    nd = (nt - nh).normalized()
    fw = z - nd * z.dot(nd)
    if fw.y > 0:
        fw = -fw
    fw.normalize()
    rt = fw.cross(nd).normalized() * -1.0
    # the neck's radius at the band, from the body
    rs = [((v.co - nh) - nd * (v.co - nh).dot(nd)) for v in body0.data.vertices
          if 0.045 < (v.co - nh).dot(nd) < 0.08 and ((v.co - nh) - nd * (v.co - nh).dot(nd)).length < 0.10]
    ra = max((abs(r.dot(rt)) for r in rs), default=0.055)
    rb = max((abs(r.dot(fw)) for r in rs), default=0.06)
    bm = bmesh.new()
    seg = 22
    prof = [(0.000, 0.006), (0.012, 0.016), (0.026, 0.020), (0.040, 0.017), (0.054, 0.019), (0.068, 0.013), (0.076, 0.004)]
    rows = []
    for h, bulge in prof:
        c = nh + nd * (h + 0.005)
        rows.append([bm.verts.new(c + rt * ((ra + bulge) * math.cos(2 * math.pi * j / seg)) +
                                  fw * ((rb + bulge) * math.sin(2 * math.pi * j / seg) + 0.004)) for j in range(seg)])
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(seg):
            bm.faces.new((r0[j], r0[(j + 1) % seg], r1[(j + 1) % seg], r1[j]))
    kc = nh + nd * 0.040 + fw * (rb + 0.026)
    for row in rows:                                   # the knot: the roll thickens at the throat
        for j, v in enumerate(row):
            a_ = 2 * math.pi * j / seg
            k = max(0.0, math.sin(a_)) ** 6
            v.co += fw * (0.014 * k)
    for sgn, tw in ((1, 0.18), (-1, 0.12)):                  # two short tails out of the knot, into the coat
        r0 = None
        rings = []
        for k in range(4):
            t = k / 3
            c = kc - nd * (0.018 + 0.05 * t) + rt * (sgn * (0.010 + 0.008 * t)) + fw * (0.002 - 0.012 * t)
            rings.append([bm.verts.new(c + rt * (0.016 * math.cos(2 * math.pi * i / 8)) + fw * (0.006 * math.sin(2 * math.pi * i / 8))) for i in range(8)])
        for a, b in zip(rings, rings[1:]):
            for i in range(8):
                bm.faces.new((a[i], a[(i + 1) % 8], b[(i + 1) % 8], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _mesh_ob("TMP_scarf", bm, coll)


def sea_boot(side, coll):
    """Knee-high rubber sea boots: body.py's foot loft (scaled to Ross) with a shaft to the knee, the top turned
    down."""
    BD = _bd()
    b = BD.boot(f"TMP_boot_{side}", side, coll, bpy.data.materials.new("tmp"))
    sh, st, _, _, _ = bone_frame(bpy.data.objects["ARM_ross"], f"shin.{side}")
    d = (sh - st).normalized()                       # up the shin
    bm = bmesh.new()
    bm.from_mesh(b.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z > 0.112], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    for v in bm.verts:                                # 7 % shorter than body.py's scaled foot
        v.co = Vector((st.x + (v.co.x - st.x) * 0.93, st.y + (v.co.y - st.y) * 0.93, v.co.z))
    seg = 20
    a_ = Vector((1, 0, 0))
    f_ = d.cross(a_).normalized()
    a_ = f_.cross(d).normalized()
    prof = [(0.085, 0.058, 0.070), (0.15, 0.062, 0.072), (0.24, 0.066, 0.072), (0.33, 0.071, 0.074), (0.41, 0.070, 0.072),
            (BOOT_TOP, 0.069, 0.071), (BOOT_TOP + 0.004, 0.077, 0.079), (BOOT_TOP - 0.035, 0.078, 0.080)]
    rows = []
    for z, ra, rb in prof:
        t = (z - st.z) / max(1e-4, d.z)
        c = st + d * t
        rows.append([bm.verts.new(c + a_ * (ra * math.cos(2 * math.pi * i / seg)) + f_ * (rb * math.sin(2 * math.pi * i / seg)))
                     for i in range(seg)])
    for r0, r1 in zip(rows, rows[1:]):
        for i in range(seg):
            bm.faces.new((r0[i], r0[(i + 1) % seg], r1[(i + 1) % seg], r1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(b.data)
    bm.free()
    b.data.materials.clear()
    for p in b.data.polygons:
        p.use_smooth = True
    return b


def shell_from(head, K, coll):
    """Short grey-white stubble and cropped hair as a shell over the head (alpha-tested in the skin material):
    the stubble catches light at the jaw's edge."""
    me = head.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.normal_update()
    eu = K["eye_u"]
    kinds = {}
    for f in bm.faces:
        c = f.calc_center_median() - K["o"]
        s, fw, u = c.dot(K["rt"]), c.dot(K["fw"]), c.dot(K["up"])
        rel = u - eu
        if rel < -0.040 and fw > -0.035 and rel > -0.16:
            kinds[f.index] = "stubble"                 # cheeks below the cheekbone, lip, chin, jaw, under the jaw
        elif -0.045 < rel < 0.030 and fw < -0.018:
            kinds[f.index] = "hair"                    # back and sides below the hat band, the nape
        elif -0.040 < rel < 0.012 and abs(s) > 0.060 and -0.035 < fw < 0.012:
            kinds[f.index] = "stubble"                 # sideburns in front of the ears
    out = {}
    for kind, off in (("stubble", 0.0016), ("hair", 0.0030)):
        nb = bmesh.new()
        vmap = {}
        for f in bm.faces:
            if kinds.get(f.index) != kind:
                continue
            vs = []
            for v in f.verts:
                if v.index not in vmap:
                    vmap[v.index] = nb.verts.new(v.co + v.normal * off)
                vs.append(vmap[v.index])
            nb.faces.new(vs)
        out[kind] = _mesh_ob(f"TMP_{kind}", nb, coll)
    bm.free()
    return out


def set_part(ob, part):
    a = ob.data.attributes.get("part") or ob.data.attributes.new("part", "INT", "FACE")
    for i in range(len(ob.data.polygons)):
        a.data[i].value = PART[part]


def join(objs, name):
    _deselect()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = objs[0]
    ob.name = ob.data.name = name
    return ob


def unwrap(ob):
    """One UV map in 0..1: smart islands, the skin (face, hands) at 1.7x the density, packed."""
    _active(ob)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(62), island_margin=0.002)
    bpy.ops.object.mode_set(mode="OBJECT")
    part = ob.data.attributes["part"]
    uv = ob.data.uv_layers.active
    for poly in ob.data.polygons:
        k = 1.7 if part.data[poly.index].value in SKIN_PARTS else 1.0
        if k != 1.0:
            for li in poly.loop_indices:
                uv.data[li].uv *= k
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")


def count_tris(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    m = ob.evaluated_get(dg).to_mesh()
    m.calc_loop_triangles()
    n = len(m.loop_triangles)
    ob.evaluated_get(dg).to_mesh_clear()
    return n


def build_figure(coll):
    """Everything up to SK_ross (one mesh) on ARM_ross; returns (arm, sk, landmarks)."""
    BD = _bd()
    body0, eyes0 = load_source(coll, 0)
    head1, eyes = load_source(coll, 1)
    for e in eyes0:
        bpy.data.objects.remove(e, do_unlink=True)
    eye_c = [sum((v.co for v in e.data.vertices), Vector()) / len(e.data.vertices) for e in eyes]
    eye_l = max(eye_c, key=lambda p: p.x)
    eye_r = min(eye_c, key=lambda p: p.x)
    age_shape(body0.data, eye_l, eye_r)
    age_shape(head1.data, eye_l, eye_r)
    body0.name, head1.name = "TMP_body0", "TMP_head"
    arm = BD.build_armature(coll)
    arm.name = arm.data.name = "ARM_ross"
    BD.weights(body0, arm)
    keep_faces(head1, lambda i, co: co.z > 1.36 * S_R and abs(co.x) < 0.14 * S_R)
    BD.weights(head1, arm)
    for e in eyes:
        rigid(e, "head", arm)
    stoop_rest(arm, [body0, head1] + eyes)
    hands = graft_hands(arm, coll)
    sh = drape(coat_shell(body0, arm, coll), body0, coll)
    transfer_weights(sh, body0)
    smooth_weights(sh, 6, 0.5)
    skirt_weights(sh)
    cuff_weights(sh, arm)
    af = arm_flags(sh)                                     # the drape pulls the chest back in: fill it again
    moved = fill_torso([v for v in sh.data.vertices if not af[v.index]], HIP_CUT - 0.25, 1.44, z_full=HIP_CUT + 0.06)
    print("ROSS_FILL", json.dumps({"hang_moved": moved}))
    sh.data.update()
    flaps, buttons = coat_details(sh, coll)
    details = [o for o in (flaps, buttons) if o]
    for o in details:
        transfer_weights(o, body0)
        o.parent = arm
        o.modifiers.new("Armature", "ARMATURE").object = arm
    sh.parent = arm
    sh.modifiers.new("Armature", "ARMATURE").object = arm
    # the head: only what shows above the collar and scarf
    nh, nt, _, _, _ = bone_frame(arm, "neck")
    nd = (nt - nh).normalized()
    keep_faces(head1, lambda i, co: (co - nh).dot(nd) > 0.035)
    decimate(head1, 4600)
    K = skull(head1, arm, [sum((v.co for v in e.data.vertices), Vector()) / len(e.data.vertices) for e in eyes])
    K["elbows"] = []
    for side in ("L", "R"):
        fh, ft, _, _, _ = bone_frame(arm, f"forearm.{side}")
        K["elbows"].append((tuple(fh), tuple((ft - fh).normalized())))
    global _LANDMARKS
    _LANDMARKS = K
    hat, ties = souwester(K, coll)
    rigid(hat, "head", arm)
    rigid(ties, "head", arm)
    sc_ = scarf(arm, body0, coll)
    transfer_weights(sc_, body0)
    sc_.parent = arm
    sc_.modifiers.new("Armature", "ARMATURE").object = arm
    boots = [sea_boot(s, coll) for s in ("L", "R")]
    for b, s in zip(boots, ("L", "R")):
        b.vertex_groups.clear()
        gf, gs = b.vertex_groups.new(name=f"foot.{s}"), b.vertex_groups.new(name=f"shin.{s}")
        for v in b.data.vertices:
            w = max(0.0, min(1.0, (v.co.z - 0.08) / 0.08))
            gs.add([v.index], w, "REPLACE")
            if w < 0.99:
                gf.add([v.index], 1.0 - w, "REPLACE")
        b.parent = arm
        b.modifiers.new("Armature", "ARMATURE").object = arm
    shells = shell_from(head1, K, coll)
    for o in shells.values():
        transfer_weights(o, head1)
        o.parent = arm
        o.modifiers.new("Armature", "ARMATURE").object = arm
    for ob, part in [(sh, "coat"), (hat, "hat"), (ties, "hat"), (sc_, "scarf"), (head1, "skin"),
                     (shells["stubble"], "stubble"), (shells["hair"], "hair")] + [(h, "hands") for h in hands] + \
                    [(e, "eyes") for e in eyes] + [(b, "boots") for b in boots] + \
                    ([(flaps, "coat")] if flaps else []) + ([(buttons, "boots")] if buttons else []):
        set_part(ob, part)
    bpy.data.objects.remove(body0, do_unlink=True)
    parts = [sh, hat, ties, sc_, head1, shells["stubble"], shells["hair"]] + hands + eyes + boots + details
    for o in parts:
        for m in list(o.modifiers):
            o.modifiers.remove(m)
    sk = join(parts, "SK_ross")
    clamp_weights(sk)
    sk.parent = arm
    sk.modifiers.new("Armature", "ARMATURE").object = arm
    for p in sk.data.polygons:
        p.use_smooth = True
    return arm, sk, K


# ------------------------------------------------------------------------------------------------ texture set

def _n(nt, typ, **kw):
    n = nt.nodes.new(typ)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def _vm(nt, op, a, b=None):
    n = _n(nt, "ShaderNodeVectorMath", operation=op)
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (Vector, tuple)):
            n.inputs[i].default_value = tuple(x)
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs["Value"] if op in ("DOT_PRODUCT", "DISTANCE", "LENGTH") else n.outputs["Vector"]


def _m(nt, op, a, b=0.0, clamp=False):
    n = _n(nt, "ShaderNodeMath", operation=op, use_clamp=clamp)
    for i, x in enumerate((a, b)):
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[0]


def _ramp(nt, x, a, b, lo=0.0, hi=1.0):
    """Smoothstep map of x from [a, b] to [lo, hi], clamped."""
    n = _n(nt, "ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", clamp=True)
    nt.links.new(x, n.inputs["Value"])
    n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = a, b
    n.inputs["To Min"].default_value, n.inputs["To Max"].default_value = lo, hi
    return n.outputs["Result"]


def _mix(nt, f, a, b):
    n = _n(nt, "ShaderNodeMix", data_type="RGBA")
    for sock, x in ((n.inputs[0], f), (n.inputs[6], a), (n.inputs[7], b)):
        if isinstance(x, (tuple, list)):
            sock.default_value = tuple(x) if len(x) == 4 else (*x, 1.0)
        elif isinstance(x, (int, float)):
            sock.default_value = x
        else:
            nt.links.new(x, sock)
    return n.outputs[2]


def _rgb(hex_):
    from lib.scene_utils import hex_to_linear
    return tuple(hex_to_linear(hex_))


def _noise(nt, P, scale, detail=3.0, stretch=(1, 1, 1)):
    v = _vm(nt, "MULTIPLY", P, Vector(stretch))
    n = _n(nt, "ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    nt.links.new(v, n.inputs["Vector"])
    return n.outputs["Fac"]


def _vor(nt, P, scale):
    n = _n(nt, "ShaderNodeTexVoronoi")
    n.inputs["Scale"].default_value = scale
    nt.links.new(P, n.inputs["Vector"])
    return n.outputs["Distance"]


def bake_material(part, K):
    """A procedural look for one part, baked to the atlas. Outputs: BSDF (colour, roughness, bump) and an
    emission carrying the masks (R: clearcoat, G: alpha) for the mask pass."""
    m = bpy.data.materials.new(f"TMP_bake_{part}")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    out = nt.nodes["Material Output"]
    tc = _n(nt, "ShaderNodeTexCoord")
    geo = _n(nt, "ShaderNodeNewGeometry")
    P = tc.outputs["Object"]
    point = geo.outputs["Pointiness"]
    nz = _vm(nt, "DOT_PRODUCT", geo.outputs["Normal"], Vector((0, 0, 1)))
    height = None
    coat = 0.0
    alpha = 1.0
    if part in ("coat", "hat", "boots"):
        up = _ramp(nt, nz, 0.30, 0.78)                                    # where rain sits: shoulders, crown, brim
        beads = _m(nt, "MULTIPLY", _ramp(nt, _vor(nt, P, 150.0 if part == "hat" else 110.0), 0.13, 0.03), up)
        streak = _noise(nt, P, 9.0, 4.0, (1.0, 1.0, 0.18))                 # runs: stretched down the coat
        worn = _ramp(nt, point, 0.515, 0.56)                              # wax rubbed off on the edges and seams
        base = "#141414" if part == "boots" else "#161513"
        col = _mix(nt, _m(nt, "MULTIPLY", worn, 0.55), _rgb(base), _rgb("#3A372F"))
        col = _mix(nt, _m(nt, "MULTIPLY", _ramp(nt, streak, 0.45, 0.65), 0.35), col, _rgb("#121210"))
        # checkpoint review (2026-11-18): roughness 0.36 with a clear coat everywhere read as latex. Waxed
        # cotton is satin (0.55); it is wet and glossy only where the rain sits (up-facing) and in the runs
        wet = _m(nt, "MAXIMUM", _m(nt, "MULTIPLY", up, 0.75), _m(nt, "MULTIPLY", _ramp(nt, streak, 0.58, 0.72), 0.45))
        rough = _m(nt, "ADD", 0.40 if part == "boots" else 0.55, _m(nt, "MULTIPLY", _m(nt, "SUBTRACT", streak, 0.5), 0.16))
        rough = _m(nt, "ADD", rough, _m(nt, "MULTIPLY", _ramp(nt, point, 0.5, 0.46), 0.10))   # dry, dull fold interiors
        # r3 (Godot close-up): wet at -0.30 left the shoulders at 0.3, glossy as plastic under the clear coat;
        # the film carries the wet look, the cloth under it stays satin
        rough = _m(nt, "SUBTRACT", rough, _m(nt, "MULTIPLY", wet, 0.18), clamp=True)
        rough = _m(nt, "ADD", _m(nt, "MULTIPLY", rough, _m(nt, "SUBTRACT", 1.0, beads)), _m(nt, "MULTIPLY", beads, 0.05))
        crease = _noise(nt, P, 14.0, 6.0, (1.0, 1.0, 0.35))              # the waxed cotton's crumple
        hang = _noise(nt, P, 5.0, 2.0, (1.0, 1.0, 0.10))                  # long folds hanging from the yoke
        wrinkle = _noise(nt, P, 32.0, 3.0, (1.0, 1.0, 0.45))             # small creases that break the highlights
        height = _m(nt, "ADD", _m(nt, "MULTIPLY", beads, 0.9), _m(nt, "MULTIPLY", crease, 2.4))
        height = _m(nt, "ADD", height, _m(nt, "MULTIPLY", wrinkle, 0.9))
        height = _m(nt, "ADD", height, _m(nt, "MULTIPLY", _noise(nt, P, 60.0, 4.0), 0.2))
        if part == "coat":
            height = _m(nt, "ADD", height, _m(nt, "MULTIPLY", _ramp(nt, hang, 0.3, 0.7), 2.6))
            for e, d in K.get("elbows", []):                              # compression creases round the elbows
                rel = _vm(nt, "SUBTRACT", P, Vector(e))
                s = _vm(nt, "DOT_PRODUCT", rel, Vector(d))
                ring = _m(nt, "SINE", _m(nt, "ADD", _m(nt, "MULTIPLY", s, 230.0), _m(nt, "MULTIPLY", _noise(nt, P, 25.0, 2.0), 5.0)))
                mask = _ramp(nt, _vm(nt, "LENGTH", rel), 0.11, 0.03)
                height = _m(nt, "ADD", height, _m(nt, "MULTIPLY", _m(nt, "MULTIPLY", ring, mask), 1.4))
        coat = _m(nt, "ADD", _m(nt, "MULTIPLY", wet, 0.45 if part != "boots" else 0.15), _m(nt, "MULTIPLY", beads, 0.5))
        if part == "hat":
            rough = _m(nt, "ADD", rough, 0.04)
        if part == "coat":
            seam = _m(nt, "MULTIPLY", _ramp(nt, _m(nt, "ABSOLUTE", _m(nt, "SUBTRACT", _vm(nt, "DOT_PRODUCT", P, Vector((1, 0, 0))), 0.05)), 0.006, 0.0),
                      _ramp(nt, _vm(nt, "DOT_PRODUCT", geo.outputs["Normal"], Vector((0, -1, 0))), 0.3, 0.7))
            height = _m(nt, "SUBTRACT", height, _m(nt, "MULTIPLY", seam, 0.35))         # the front closure, off-centre
        if part == "hat":
            ang = _n(nt, "ShaderNodeSeparateXYZ")
            nt.links.new(_vm(nt, "SUBTRACT", P, K["o"]), ang.inputs[0])
            panel = _ramp(nt, _m(nt, "ABSOLUTE", _m(nt, "SINE", _m(nt, "MULTIPLY", _m(nt, "ARCTAN2", ang.outputs[0], ang.outputs[1]), 2.0))), 0.04, 0.0)
            height = _m(nt, "SUBTRACT", height, _m(nt, "MULTIPLY", panel, 0.6))        # four crown panels
    elif part == "scarf":
        knit = _n(nt, "ShaderNodeTexWave", wave_type="BANDS", bands_direction="Z")
        knit.inputs["Scale"].default_value = 90.0
        knit.inputs["Distortion"].default_value = 2.0
        nt.links.new(P, knit.inputs["Vector"])
        col = _mix(nt, _m(nt, "MULTIPLY", _noise(nt, P, 30.0), 0.4), _rgb("#38352F"), _rgb("#45413A"))
        rough = 0.93
        height = _m(nt, "ADD", _m(nt, "MULTIPLY", knit.outputs["Fac"], 0.6), _m(nt, "MULTIPLY", _noise(nt, P, 200.0), 0.3))
    elif part in ("skin", "hands", "eyes", "stubble", "hair"):
        rel = _vm(nt, "SUBTRACT", P, K["o"])
        u = _m(nt, "SUBTRACT", _vm(nt, "DOT_PRODUCT", rel, K["up"]), K["eye_u"])
        f = _vm(nt, "DOT_PRODUCT", rel, K["fw"])
        if part == "eyes":
            col, rough = _rgb("#3E3A36"), 0.62
        elif part in ("stubble", "hair"):
            if part == "stubble":
                dens = _m(nt, "MULTIPLY", _ramp(nt, u, -0.030, -0.052), _ramp(nt, f, -0.040, -0.012))
                dens = _m(nt, "MULTIPLY", dens, _ramp(nt, u, -0.170, -0.140))
                col, scale, rad = _rgb("#8A857C"), 820.0, 0.36   # 0.30 vanished at game distance; 0.50 read as a pale mask
            else:
                dens = _m(nt, "MULTIPLY", _ramp(nt, u, -0.050, -0.030), _ramp(nt, f, -0.008, -0.030))
                dens = _m(nt, "MULTIPLY", dens, _ramp(nt, u, 0.034, 0.020))
                col, scale, rad = _rgb("#8F8A82"), 620.0, 0.45
            dots = _m(nt, "LESS_THAN", _vor(nt, P, scale), _m(nt, "MULTIPLY", dens, rad))
            alpha = dots
            rough = 0.7
            height = _m(nt, "MULTIPLY", dots, 0.4)
        else:
            col = _rgb("#A97C66")
            red = _ramp(nt, _vm(nt, "DISTANCE", P, K["nose"]), 0.045, 0.0) if "nose" in K else None
            if red is not None:
                for ch in K.get("cheeks", []):
                    red = _m(nt, "MAXIMUM", red, _m(nt, "MULTIPLY", _ramp(nt, _vm(nt, "DISTANCE", P, ch), 0.035, 0.0), 0.7))
                col = _mix(nt, _m(nt, "MULTIPLY", red, 0.6), col, _rgb("#A35A4A"))
            if "mouth" in K:                               # thin, darker lips: no highlight to read as a smile
                lips = _ramp(nt, _vm(nt, "DISTANCE", P, K["mouth"]), 0.026, 0.008)
                col = _mix(nt, _m(nt, "MULTIPLY", lips, 0.85), col, _rgb("#5A4038"))
            # jaw shadow under the stubble (the skin there is greyer)
            jaw = _m(nt, "MULTIPLY", _ramp(nt, u, -0.035, -0.055), _ramp(nt, f, -0.040, -0.012))
            col = _mix(nt, _m(nt, "MULTIPLY", jaw, 0.35), col, _rgb("#7E7268"))
            if part == "skin":
                # r4 (Godot): the alpha-scissor stubble shell vanished in the mipmaps and left a smooth young jaw.
                # The stubble is baked into the skin as well: a grey cast over the beard area and the dots
                # themselves, which survive every mip level as a greyer, rougher jaw.
                sd = _m(nt, "MULTIPLY", _ramp(nt, u, -0.030, -0.052), _ramp(nt, f, -0.040, -0.012))
                sd = _m(nt, "MULTIPLY", sd, _ramp(nt, u, -0.170, -0.140))
                col = _mix(nt, _m(nt, "MULTIPLY", sd, 0.45), col, _rgb("#6E6760"))
                sdots = _m(nt, "LESS_THAN", _vor(nt, P, 820.0), _m(nt, "MULTIPLY", sd, 0.42))
                col = _mix(nt, _m(nt, "MULTIPLY", sdots, 0.8), col, _rgb("#A8A399"))
            if part == "hands":
                knuck = _ramp(nt, point, 0.52, 0.58)
                col = _mix(nt, _m(nt, "MULTIPLY", knuck, 0.6), _rgb("#A57863"), _rgb("#9C5547"))
            rough = 0.55 if part == "skin" else 0.62
            height = _m(nt, "ADD", _m(nt, "MULTIPLY", _noise(nt, P, 700.0, 2.0), 0.25), _m(nt, "MULTIPLY", _noise(nt, P, 60.0, 4.0), 0.2))
    if isinstance(col, tuple):
        bsdf.inputs["Base Color"].default_value = col
    else:
        nt.links.new(col, bsdf.inputs["Base Color"])
    if isinstance(rough, (int, float)):
        bsdf.inputs["Roughness"].default_value = rough
    else:
        nt.links.new(rough, bsdf.inputs["Roughness"])
    if height is not None:
        bump = _n(nt, "ShaderNodeBump")
        bump.inputs["Strength"].default_value = 1.0 if part in ("coat", "hat") else 0.55
        bump.inputs["Distance"].default_value = 0.0015
        nt.links.new(height, bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    em = _n(nt, "ShaderNodeEmission")
    cmb = _n(nt, "ShaderNodeCombineColor")
    for i, x in ((0, coat), (1, alpha)):
        if isinstance(x, (int, float)):
            cmb.inputs[i].default_value = x
        else:
            nt.links.new(x, cmb.inputs[i])
    nt.links.new(cmb.outputs[0], em.inputs["Color"])
    m["mask_emit"] = em.name
    return m


def _bake(sk, img, typ, **kw):
    for m in sk.data.materials:
        nt = m.node_tree
        n = nt.nodes.get("BAKE_target") or _n(nt, "ShaderNodeTexImage", name="BAKE_target")
        n.image = img
        nt.nodes.active = n
    _active(sk)
    bpy.ops.object.bake(type=typ, margin=6, use_clear=True, **kw)


def texture(sk):
    """Bake the one 2k texture set and give SK_ross its two materials."""
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 4
    sc.cycles.device = "CPU"
    K = _LANDMARKS
    unwrap(sk)
    names = list(PART)
    sk.data.materials.clear()
    for nm in names:
        sk.data.materials.append(bake_material(nm, K))
    part = sk.data.attributes["part"]
    for p in sk.data.polygons:
        p.material_index = part.data[p.index].value
    TEX_DIR.mkdir(parents=True, exist_ok=True)

    def new(name, colour):
        im = bpy.data.images.new(name, TEX_PX, TEX_PX, alpha=True)
        im.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        return im
    alb, rgh, nrm, msk = new("T_LL_Ross_albedo", True), new("TMP_rough", False), new("T_LL_Ross_normal", False), new("TMP_mask", False)
    _bake(sk, alb, "DIFFUSE", pass_filter={"COLOR"})
    _bake(sk, rgh, "ROUGHNESS")
    _bake(sk, nrm, "NORMAL", normal_space="TANGENT")
    for m in sk.data.materials:                       # the mask pass: emission instead of the BSDF
        nt = m.node_tree
        nt.links.new(nt.nodes[m["mask_emit"]].outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    _bake(sk, msk, "EMIT")
    import numpy as np
    A = np.array(alb.pixels[:]).reshape(-1, 4)
    Mk = np.array(msk.pixels[:]).reshape(-1, 4)
    R = np.array(rgh.pixels[:]).reshape(-1, 4)
    A[:, 3] = (Mk[:, 1] > 0.5).astype(np.float32)
    alb.pixels[:] = A.ravel()
    orm = new("T_LL_Ross_orm", False)
    O = np.zeros_like(A)
    O[:, 0] = Mk[:, 0]
    O[:, 1] = R[:, 0]
    O[:, 3] = 1.0
    orm.pixels[:] = O.ravel()
    paths = {}
    for im in (alb, nrm, orm):
        im.filepath_raw = str(TEX_DIR / f"{im.name}.png")
        im.file_format = "PNG"
        im.save()
        paths[im.name] = str(Path(im.filepath_raw).relative_to(WS))
    for im in (rgh, msk):
        bpy.data.images.remove(im)
    final_materials(sk, alb, nrm, orm)
    for m in list(bpy.data.materials):
        if m.name.startswith("TMP_bake_") and m.users == 0:
            bpy.data.materials.remove(m)
    return {"textures": paths, "materials": [m.name for m in sk.data.materials], "alpha_cover": round(float(A[:, 3].mean()), 4)}


def final_materials(sk, alb, nrm, orm):
    mats = []
    for name, skin in (("M_LL_Ross_Oilskin", False), ("M_LL_Ross_Skin", True)):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        ta = _n(nt, "ShaderNodeTexImage")
        ta.image = alb
        tn = _n(nt, "ShaderNodeTexImage")
        tn.image = nrm
        to = _n(nt, "ShaderNodeTexImage")
        to.image = orm
        nm = _n(nt, "ShaderNodeNormalMap")
        sep = _n(nt, "ShaderNodeSeparateColor")
        nt.links.new(ta.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
        nt.links.new(to.outputs["Color"], sep.inputs[0])
        nt.links.new(sep.outputs[1], b.inputs["Roughness"])
        if skin:
            gt = _m(nt, "GREATER_THAN", ta.outputs["Alpha"], 0.5)
            nt.links.new(gt, b.inputs["Alpha"])
            if hasattr(m, "surface_render_method"):
                m.surface_render_method = "DITHERED"
            b.inputs["Subsurface Weight"].default_value = 0.08
            b.inputs["Subsurface Radius"].default_value = (0.012, 0.004, 0.002)
        else:
            nt.links.new(sep.outputs[0], b.inputs["Coat Weight"])
            b.inputs["Coat Roughness"].default_value = 0.07
            m.use_backface_culling = False
        mats.append(m)
    sk.data.materials.clear()
    for m in mats:
        sk.data.materials.append(m)
    part = sk.data.attributes["part"]
    for p in sk.data.polygons:
        p.material_index = 1 if part.data[p.index].value in SKIN_PARTS else 0



# ------------------------------------------------------------------------------------------------ stills

def _lin(c):
    """Godot treats light and ambient colours as sRGB; Blender's are linear."""
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


WARM = _lin((1.0, 0.72, 0.45))      # station.gd WARM (the lamps' tungsten), linearised
GODOT_BASE = {"desk": 2.6, "wall": 0.72, "inst": 0.8, "cage": 0.55, "stair": 0.26}
DOOR_FILL_ENERGY = 1.6              # station.gd
AMBIENT = _lin((0.15, 0.13, 0.11))  # station.gd probe ambient colour (energy 0.8 with the room lit), linearised
GAME_EXPOSURE = 1.35                # outside.gd tonemap_exposure (AgX)
# Blender watts per Godot energy unit (lamps, and the door fill on its own: Blender's lights fall off as 1/d^2,
# Godot's as d^-1.2, so one factor cannot fit both) and the world strength for the probe ambient. Fitted by
# --calibrate on cu_door against the game's s5r2_t060_cu_door.png: door 0.1233 (game 0.1208), left wall 0.3498
# (0.3390), frame 0.1663 (0.1603), Rec. 709 luma of the sRGB values (measure_luma.py's measure).
CAL = {"k": 40.0, "amb": 1.6, "kf": 30.0}


def g2b_dir(x, y, z):
    return Vector((x, -z, y))


def game_lights(coll, k, amb, kf=None, gen_running=False):
    """station.gd's interior rig in Blender: lamps at the LIGHT_ empties, the instrument spots, the cage bulb,
    the door's bounce fill (aimed at the SHUT leaf's centre, as Godot computes it at load), the window spill and
    the probe's warm ambient. Energies are Godot's times one calibrated factor."""
    sc = bpy.context.scene
    out = []

    def add(name, typ, loc, energy, colour=WARM, size=0.03, spot=None, aim=None, spec=1.0, shadow=True):
        ld = bpy.data.lights.new("GL_" + name, typ)
        ld.energy = energy * k
        ld.color = colour
        ld.shadow_soft_size = size
        ld.specular_factor = spec
        ld.use_shadow = shadow
        if spot:
            ld.spot_size = math.radians(spot[0] * 2.0)
            ld.spot_blend = spot[1]
        ob = bpy.data.objects.new("GL_" + name, ld)
        coll.objects.link(ob)
        ob.location = loc
        if aim is not None:
            ob.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        out.append(ob)
        return ob
    for o in bpy.data.objects:
        if not o.name.startswith("LIGHT_") or o.name in ("LIGHT_lamp", "LIGHT_stair_low"):
            continue
        id_ = o.name[6:]
        p = o.matrix_world.translation.copy()
        if id_ == "desk":
            inward = Vector((-p.x, -p.y, 0)).normalized()
            add(id_, "SPOT", p, GODOT_BASE["desk"], spot=(55.0, 0.3), aim=p + Vector((0, 0, -0.8)) + inward * 0.35 + Vector((0.2, 0, 0)))
        elif id_.startswith("wall"):
            add(id_, "POINT", p, GODOT_BASE["wall"], size=0.06)
        elif id_ == "stair":
            add(id_, "POINT", p, GODOT_BASE["stair"], colour=WARM)
    for idn, part in (("inst_console", "NDL_bearing"), ("inst_charger", "NDL_battery"), ("inst_gen", "NDL_temp"), ("inst_power", "PT_brk_lights")):
        o = bpy.data.objects.get(part)
        if o:
            p = o.matrix_world.translation.copy()
            inward = Vector((-p.x, -p.y, 0)).normalized()
            add(idn, "SPOT", p + inward * 0.45 + Vector((0, 0, 0.35)), GODOT_BASE["inst"], spot=(50.0, 0.3), aim=p, spec=0.0, shadow=False)
    cage = bpy.data.objects.get("LMP_cage")
    if cage:
        add("cage", "POINT", cage.matrix_world.translation + Vector((0, 0, -0.06)), GODOT_BASE["cage"], shadow=False)
    door = _DOOR_SHUT
    if door:
        hinge, across = door
        aim = hinge + across * 0.53 + Vector((0, 0, 1.05))
        flat = Vector((aim.x, aim.y, 0)).normalized()
        f_ = add("door_fill", "SPOT", flat * 0.7 + Vector((0, 0, F + 2.85)), DOOR_FILL_ENERGY, spot=(19.0, 0.55), aim=aim, spec=0.25, shadow=False)
        if kf is not None:
            f_.data.energy = DOOR_FILL_ENERGY * kf
    for g in bpy.data.objects:
        if g.name.startswith("GLS_window") and g.type == "MESH":
            ws = [g.matrix_world @ Vector(c) for c in g.bound_box]
            c = sum(ws, Vector()) / 8
            o_ = Vector((c.x, c.y, 0)).normalized()
            add(g.name, "SPOT", c + o_ * 1.4 + Vector((0, 0, 0.6)), 0.14, colour=_lin((0.68, 0.76, 0.92)), size=0.25,
                spot=(42.0, 0.4), aim=c - o_ * 1.6 + Vector((0, 0, -1.2)), spec=0.0)
    w = bpy.data.worlds.new("GameAmbient")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (*AMBIENT, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = amb
    sc.world = w
    return out


_DOOR_SHUT = None
_ARGS = None


def game_scene(res=(1920, 1080)):
    sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = math.log2(GAME_EXPOSURE)
    try:
        sc.eevee.taa_render_samples = 64
        sc.eevee.use_raytracing = True
        sc.eevee.use_shadows = True
    except AttributeError:
        pass
    for o in bpy.data.objects:
        if o.name.startswith("COL_") or o.name.startswith("LIGHT_"):
            o.hide_render = True
        if o.users_collection and o.users_collection[0].name in ("ASSET_lighthouse", "ASSET_island", "ASSET_boat"):
            o.hide_render = True
    game_palette()
    # the lamps' own glass, globes and guards never shadow their bulb (Godot's lamp meshes cast no shadows)
    for o in bpy.data.objects:
        mats = {m.name for m in getattr(o.data, "materials", []) if m} if o.type == "MESH" else set()
        if o.name.startswith(("LMP_", "GLS_")) or mats & {"M_LL_Glass", "M_LL_Lamp", "M_LL_LampGreen", "M_LL_LampRed"}:
            o.visible_shadow = False
    lamp = bpy.data.materials.get("M_LL_Lamp")
    if lamp and lamp.use_nodes:
        b = next((n for n in lamp.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b:
            b.inputs["Emission Color"].default_value = (1.0, 0.75, 0.42, 1)
            b.inputs["Emission Strength"].default_value = 6.0
    cam = bpy.data.objects.new("GameCam", bpy.data.cameras.new("GameCam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.clip_start = 0.05
    cam.data.sensor_fit = "VERTICAL"                   # Godot keeps the vertical field of view
    return sc, cam


# materials.gd PALETTE + ROOM: the colours Godot paints the room with (the scans only add detail). Applied in the
# stills scene only (the room .blend is not saved): (base hex, roughness, coat)
GAME_ROOM = {"M_LL_Concrete": ("#D6C9A6", 0.42, 0.2), "M_LL_Floor": ("#4A4743", 0.56, 0.16),
             "M_LL_SteelPaint": ("#66796B", 0.46, 0.15), "M_LL_SteelRust": ("#34493C", 0.45, 0.2),
             "M_LL_Iron": ("#2A2B28", 0.47, 0.0), "M_LL_EngineGreen": ("#55705A", 0.43, 0.25),
             "M_LL_Wood": ("#7A4E2A", 0.6, 0.1), "M_LL_WoodDark": ("#4A2E1A", 0.47, 0.3),
             "M_LL_Limewash": ("#B4AE9F", 0.86, 0.0), "M_LL_Chequer": ("#4F514B", 0.5, 0.0)}
DADO = ("#2E4537", 1.05)                         # the wall's painted dado below the rail


def game_palette():
    from lib.scene_utils import hex_to_linear
    for name, (hx, rough, coat) in GAME_ROOM.items():
        m = bpy.data.materials.get(name)
        if m is None:
            continue
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type not in ("BSDF_PRINCIPLED", "OUTPUT_MATERIAL"):
                nt.nodes.remove(n)
        b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Base Color"].default_value = hex_to_linear(hx)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = 0.0
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.4
        if name == "M_LL_Concrete":                     # cream above the dado rail, painted green below
            tc = _n(nt, "ShaderNodeTexCoord")
            sep = _n(nt, "ShaderNodeSeparateXYZ")
            nt.links.new(tc.outputs["Object"], sep.inputs[0])
            below = _m(nt, "LESS_THAN", sep.outputs[2], F + DADO[1])
            nt.links.new(_mix(nt, below, hex_to_linear(hx), hex_to_linear(DADO[0])), b.inputs["Base Color"])


def door_shut_frame():
    d = bpy.data.objects.get("PT_stair_door")
    if d is None:
        return None
    return d.matrix_world.translation.copy(), d.matrix_world.col[0].xyz.normalized()


def run_calibrate(out, k, amb):
    """Render cu_door (door shut) with the game rig and print the door crop's mean luminance (game: 0.121)."""
    import review_views as RV
    global _DOOR_SHUT
    out = ensure_allowed(out)
    out.mkdir(parents=True, exist_ok=True)
    _DOOR_SHUT = door_shut_frame()
    sc, cam = game_scene((960, 603))
    coll = bpy.data.collections.new("GL")
    sc.collection.children.link(coll)
    game_lights(coll, k, amb, kf=_ARGS.kf)
    frm, to, lens, _ = RV.VIEWS["cu_door"]
    cam.data.angle_y = math.radians(55.0)              # capture_fp.gd cu_door
    RV.look(cam, frm, to)
    path = out / f"cal_k{k:g}_a{amb:g}_f{_ARGS.kf if _ARGS.kf is not None else k:g}.png"
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print("CAL_RESULT", json.dumps({"k": k, "amb": amb, "kf": _ARGS.kf, **_lumas(path)}))


def _lumas(path):
    import numpy as np
    im = bpy.data.images.load(str(path))
    w, h = im.size
    px = np.array(im.pixels[:]).reshape(h, w, 4)[::-1, :, :3]
    bpy.data.images.remove(im)
    y = 0.2126 * px[..., 0] + 0.7152 * px[..., 1] + 0.0722 * px[..., 2]
    crops = {"door": (0.375, 0.04, 0.64, 0.76), "wall_l": (0.0, 0.0, 0.10, 0.30), "frame": (0.0, 0.0, 1.0, 0.75)}
    return {k: round(float(y[int(c[1] * h):int(c[3] * h), int(c[0] * w):int(c[2] * w)].mean()), 4) for k, c in crops.items()}



# where the checkpoint camera stands (room polar, eye 1.65 m): A from 1.9 m on the latch side, where the player
# stands aside (1.6 m); B from the room's south-west; C from the front-right three-quarter (east of the chair, by
# the desk's east end), so his right hand on the chair faces the camera and the desk lamp tests the brim (from
# the console side he was seen from behind, 118 degrees off his face)
STILL_VIEW = {"A": (184.0, 1.55), "B": (223.75, 0.93), "C": (32.66, 2.316)}

# the still poses: per mark, the hand's grip, finger pose, and posture (degrees; lean = spine flexion)
STILL_POSE = {
    "A": {"grip": "rail", "fingers": "torch", "head": 14.0, "neck": 8.0},     # head down, waiting
    "B": {"grip": "flat", "fingers": "relaxed", "head": 16.0, "neck": 10.0, "turn": 20.0},   # toward lamp 3 and the player
    "C": {"grip": "rail", "fingers": "torch", "head": 4.0, "neck": 6.0, "lean": 8.0},
}


def finger_pose(arm, side, pose):
    import hands as HD
    p = HD.POSES[pose]
    sgn = 1.0 if side == "L" else -1.0
    ks = p.get("curl_k", (1.0, 1.0, 1.0, 1.0))
    for i, f in enumerate(["index", "middle", "ring", "little"]):
        for j in range(3):
            pb = arm.pose.bones[f"{f}_{j + 1}.{side}"]
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (-math.radians(p["fingers"][j] * ks[i]), 0.0, math.radians(p["spread"][i]) * sgn if j == 0 else 0.0)
    for j in range(3):
        pb = arm.pose.bones[f"thumb_{j + 1}.{side}"]
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (-math.radians(p["thumb"][j]), 0.0, math.radians(p["thumb_in"]) * sgn if j == 0 else 0.0)


def _empty(name, loc, coll):
    e = bpy.data.objects.get(name) or bpy.data.objects.new(name, None)
    if not e.users_collection:
        coll.objects.link(e)
    e.location = loc
    return e


def place_and_pose(arm, key, coll):
    """Put the figure on a mark and pose it: the stoop is the rest; sway, head, the hand to its target by IK
    (wrist placed back from the contact by the hand's length, the hand bone tracking the contact)."""
    BD = _bd()
    m = marks()[key]
    sp = STILL_POSE[key]
    p, f, rt = mark_frame(m)
    arm.location = p
    arm.rotation_euler = (0.0, 0.0, math.atan2(f.x, -f.y))
    for pb in arm.pose.bones:
        for c in list(pb.constraints):
            pb.constraints.remove(c)
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    if m.get("sway"):
        k = math.degrees(math.atan2(m["sway"], 0.5)) / 2
        for b in ("spine", "chest"):
            BD.set_rot(arm, b, Vector((0, 1, 0)), k)
    if m.get("lean"):
        BD.set_rot(arm, "spine", Vector((1, 0, 0)), m["lean"] * 0.5)
        BD.set_rot(arm, "chest", Vector((1, 0, 0)), m["lean"] * 0.5)
    if sp.get("lean"):
        BD.set_rot(arm, "spine", Vector((1, 0, 0)), sp["lean"] * 0.5)
        BD.set_rot(arm, "chest", Vector((1, 0, 0)), sp["lean"] * 0.5)
    if sp.get("hinge"):                                    # bend at the hips: the thighs turn back, legs stay put
        BD.set_rot(arm, "hips", Vector((1, 0, 0)), sp["hinge"])
        for s_ in ("L", "R"):
            BD.set_rot(arm, f"thigh.{s_}", Vector((1, 0, 0)), -sp["hinge"])
    BD.set_rot(arm, "neck", Vector((1, 0, 0)), sp["neck"])
    BD.set_rot(arm, "head", Vector((1, 0, 0)), sp["head"])
    if sp.get("turn"):                                     # + turns his face to his left
        from mathutils import Quaternion
        for b, k in (("neck", 0.5), ("head", 0.5)):
            pb = arm.pose.bones[b]
            r = arm.data.bones[b].matrix_local.to_quaternion()
            pb.rotation_quaternion = pb.rotation_quaternion @ (r.inverted() @ Quaternion(Vector((0, 0, 1)), math.radians(sp["turn"] * k)) @ r)
    side = m["hand_side"]
    other = "R" if side == "L" else "L"
    hand = from_polar(*m["hand"])
    up = Vector((0, 0, 1))
    if sp["grip"] == "rail":
        wrist = hand + up * 0.045 - f * 0.075 + rt * (0.012 if side == "L" else -0.012)
        track = hand - up * 0.03 + f * 0.02
    else:                                                    # flat on the jamb: palm on its room face, fingers up
        n_ = Vector((hand.x, hand.y, 0)).normalized() * -1.0  # toward the room centre
        wrist = hand + up * 0.07 + n_ * 0.03          # resting, fingers down the trim: steadying himself
        track = hand - up * 0.06 + n_ * 0.012
    tw = _empty(f"STILL_wrist_{key}", wrist, coll)
    tt = _empty(f"STILL_track_{key}", track, coll)
    sgn = 1.0 if side == "R" else -1.0
    pole = _empty(f"STILL_pole_{key}", p + rt * (0.65 * sgn) - f * 0.08 + up * 0.95, coll)
    ik = arm.pose.bones[f"forearm.{side}"].constraints.new("IK")
    ik.target, ik.pole_target, ik.chain_count = tw, pole, 2
    ik.pole_angle = math.radians(-90)
    dt = arm.pose.bones[f"hand.{side}"].constraints.new("DAMPED_TRACK")
    dt.target, dt.track_axis = tt, "TRACK_Y"
    finger_pose(arm, side, sp["fingers"])
    finger_pose(arm, other, "relaxed")
    bpy.context.view_layer.update()
    got = (arm.matrix_world @ arm.pose.bones[f"hand.{side}"].head)
    return {"wrist_err_m": round((got - wrist).length, 4)}


def append_figure(path):
    with bpy.data.libraries.load(str(path), link=False) as (src, dst):
        dst.collections = ["ASSET_ross"]
    c = dst.collections[0]
    bpy.context.scene.collection.children.link(c)
    return bpy.data.objects["ARM_ross"], bpy.data.objects["SK_ross"]


def _posed_landmarks(arm, sk):
    """World positions of the landmarks (stored at rest on the rig) after posing: through the head bone."""
    L = arm.get("landmarks")
    if not L:
        return {}
    b = arm.data.bones["head"]
    pb = arm.pose.bones["head"]
    M = arm.matrix_world @ pb.matrix @ b.matrix_local.inverted()
    return {k: [M @ Vector(v) for v in vs] for k, vs in L.to_dict().items()}


def _project(sc, cam, pts):
    from bpy_extras.object_utils import world_to_camera_view
    W, H = sc.render.resolution_x, sc.render.resolution_y
    out = []
    for p in pts:
        c = world_to_camera_view(sc, cam, p)
        out.append((c.x * W, (1 - c.y) * H, c.z))
    return out


def _box(sc, cam, pts, pad=0):
    pr = _project(sc, cam, pts)
    xs, ys = [q[0] for q in pr], [q[1] for q in pr]
    return int(min(xs)) - pad, int(min(ys)) - pad, int(max(xs)) + pad + 1, int(max(ys)) + pad + 1


def _load_px(path):
    import numpy as np
    im = bpy.data.images.load(str(path))
    w, h = im.size
    px = np.array(im.pixels[:]).reshape(h, w, 4)[::-1]
    bpy.data.images.remove(im)
    return px


def _boxblur(a, r):
    import numpy as np
    k = 2 * r + 1
    p = np.pad(a, r, mode="edge")
    c = p.cumsum(0).cumsum(1)
    c = np.pad(c, ((1, 0), (1, 0)))
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def still_metrics(sc, cam, arm, sk, beauty, mask):
    import numpy as np
    px = _load_px(beauty)[..., :3]
    L = 0.2126 * px[..., 0] + 0.7152 * px[..., 1] + 0.0722 * px[..., 2]
    M = _load_px(mask)[..., 3] > 0.5
    H, W = M.shape
    lm = _posed_landmarks(arm, sk)
    res = {"figure_px": int(M.sum()), "figure_mean": round(float(L[M].mean()), 4) if M.any() else None}
    hb = arm.pose.bones["head"]
    Mh = arm.matrix_world @ hb.matrix
    head_up = (Mh.col[1].xyz).normalized()
    head_fw = (Mh.col[2].xyz).normalized()
    to_cam = (cam.matrix_world.translation - Mh.translation).normalized()
    res["face_toward_camera_deg"] = round(math.degrees(math.acos(max(-1.0, min(1.0, head_fw.dot(to_cam))))), 1)

    def region(box):
        x0, y0, x1, y1 = max(0, box[0]), max(0, box[1]), min(W, box[2]), min(H, box[3])
        if x1 <= x0 or y1 <= y0:
            return None
        sub, msk = L[y0:y1, x0:x1], M[y0:y1, x0:x1]
        return sub[msk] if msk.any() else None
    rt = (Mh.col[0].xyz).normalized()
    eyes = lm.get("eyes", [])
    vals = []
    boxes = []
    for e in eyes:
        bx = _box(sc, cam, [e + rt * dx + head_up * dy for dx in (-0.017, 0.017) for dy in (-0.011, 0.011)])
        boxes.append(bx)
        r = region(bx)
        if r is not None:
            vals.append(r)
    if vals:
        v = np.concatenate(vals)
        res["eye_box"] = {"mean": round(float(v.mean()), 4), "max": round(float(v.max()), 4), "px": int(v.size), "boxes": boxes}
    jaw_pts = lm.get("chin", []) + lm.get("cheeks", []) + [c - head_up * 0.035 for c in lm.get("cheeks", [])]
    if jaw_pts:
        jb = _box(sc, cam, jaw_pts)
        r = region(jb)
        if r is not None:
            res["jaw_box"] = {"mean": round(float(r.mean()), 4), "p95": round(float(np.percentile(r, 95)), 4), "px": int(r.size), "box": jb}
            if "eye_box" in res:
                res["brim_ratio"] = round(res["eye_box"]["mean"] / max(1e-4, res["jaw_box"]["mean"]), 3)
    # silhouette: a 3 px band inside the outline against the local background just outside it
    Mf = M.astype(np.float32)
    er = _boxblur(Mf, 3) > 0.999
    di = _boxblur(Mf, 3) > 0.001
    inner = M & ~er
    outer = di & ~M
    bg = _boxblur(L * outer, 6) / np.maximum(_boxblur(outer.astype(np.float32), 6), 1e-6)
    ys = np.nonzero(M.any(1))[0]
    if ys.size:
        top, bot = ys.min(), ys.max()
        upper = np.zeros_like(M)
        upper[top:top + int((bot - top) * 0.55)] = True
        d = (L - bg)[inner]
        res["edge_contrast"] = round(float(np.abs(d).mean()), 4)
        du = (L - bg)[inner & upper]
        res["rim_upper_frac"] = round(float((du > 0.10).mean()), 4) if du.size else None
        res["figure_bbox"] = [int(np.nonzero(M.any(0))[0].min()), int(top), int(np.nonzero(M.any(0))[0].max()), int(bot)]
    return res


def _eval_bvh(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.transform(ob.matrix_world)
    eyes = []
    a = me.attributes.get("part")
    if a is not None:
        bm.faces.ensure_lookup_table()
        lay = bm.faces.layers.int.get("part")
        for f in bm.faces:
            if f[lay] == PART["eyes"]:
                eyes.append((f.calc_center_median(), f.normal.copy()))
    t = BVHTree.FromBMesh(bm)
    ev.to_mesh_clear()
    return t, bm, eyes


def brim_sweep(key, arm, sk, lights, cam_sets):
    """Geometry, not pixels: from each viewpoint, the share of the eyes' surface the viewer can see (rays not
    stopped by the brim, the figure or the room), and of that how much any game light reaches (energy / d^2).
    'shown' = seen and lit by more than a quarter of the light reaching his cheeks and chin."""
    fig, fbm, eyes = _eval_bvh(sk)
    room = [t for _, t, _ in room_bvhs(room_objects())]
    trees = [fig] + room

    def blocked(a, b, skip=0.004):
        d = b - a
        L = d.length
        d.normalize()
        for t in trees:
            h = t.ray_cast(a + d * skip, d, L - 2 * skip)
            if h[0] is not None:
                return True
        return False
    def irr(c, n):
        w = 0.0
        for lo in lights:
            lp = lo.matrix_world.translation
            l = lp - c
            if l.dot(n) <= 0:
                continue
            if not blocked(c + n * 0.002, lp):
                w += lo.data.energy * max(0.0, n.dot(l.normalized())) / max(0.05, l.length_squared)
        return w
    lit_w = [irr(c, n) for c, n in eyes]
    hb = arm.pose.bones["head"]
    Mh = arm.matrix_world @ hb.matrix
    fwd = Mh.col[2].xyz.normalized()
    lm = _posed_landmarks(arm, sk)
    refs = [irr(q + fwd * 0.012, fwd) for q in lm.get("cheeks", []) + lm.get("chin", [])]
    face_ref = max(refs + [1e-6])
    out = []
    for label, cam in cam_sets:
        seen = [i for i, (c, n) in enumerate(eyes) if (cam - c).dot(n) > 0 and not blocked(c + n * 0.002, cam)]
        shown = [i for i in seen if lit_w[i] > 0.25 * face_ref]
        out.append({"view": label, "eye_seen_frac": round(len(seen) / max(1, len(eyes)), 3),
                    "eye_seen_and_lit_frac": round(len(shown) / max(1, len(eyes)), 3),
                    "elev_deg": round(math.degrees(math.atan2(Mh.translation.z - cam.z, (Mh.translation - cam).xy.length)), 1)})
    fbm.free()
    return {"eyes_lit_frac": round(sum(1 for w in lit_w if w > 0.25 * face_ref) / max(1, len(lit_w)), 3),
            "face_ref_irradiance": round(face_ref, 2), "views": out}


def sweep_views(key, m):
    p, f, rt = mark_frame(m)
    views = []
    for d in (1.3, 2.2):
        for ang in (0, 30, -30, 60, -60, 90, -90):
            a = math.radians(ang)
            dirv_ = f * math.cos(a) + rt * math.sin(a)
            c = p + dirv_ * d
            c.z = F + 1.65
            if math.hypot(c.x, c.y) < 3.0:
                views.append((f"stand_{ang:+d}deg_{d}m", c))
    if key == "C":
        chair = bpy.data.objects.get("SM_Chair_Wood")
        if chair:
            ws = [chair.matrix_world @ Vector(cb) for cb in chair.bound_box]
            cc = sum(ws, Vector()) / 8
            views.append(("seated_at_radio_eye_1.2m", Vector((cc.x, cc.y + 0.05, F + 1.20))))
    return views



def run_stills(a):
    global _DOOR_SHUT
    out = ensure_allowed(a.stills)
    out.mkdir(parents=True, exist_ok=True)
    _DOOR_SHUT = door_shut_frame()
    pose_room_door()
    sc, cam = game_scene()
    gl = bpy.data.collections.new("GL")
    sc.collection.children.link(gl)
    game_lights(gl, a.k, a.amb, kf=a.kf)
    arm, sk = append_figure(ensure_allowed(a.figure))
    import review_views as RV
    cam.data.angle_y = math.radians(72.0)          # settings.gd fov (Godot keeps the vertical angle)
    report = {"figure": str(Path(a.figure).name), "cal": {"k": a.k, "amb": a.amb, "kf": a.kf}}
    if a.sweep:
        lights = [o for o in gl.objects if o.type == "LIGHT"]
        res = {}
        for key in a.only.split(","):
            place_and_pose(arm, key, gl)
            bpy.context.view_layer.update()
            res[key] = brim_sweep(key, arm, sk, lights, sweep_views(key, marks()[key]))
        (out / f"sweep_{a.tag}.json").write_text(json.dumps(res, indent=1))
        print("SWEEP_RESULT", json.dumps(res))
        return
    for key in a.only.split(","):
        r = place_and_pose(arm, key, gl)
        m = marks()[key]
        v = STILL_VIEW.get(key, m["view"])
        frm = from_polar(v[0], v[1], 1.65)
        bpy.context.view_layer.update()
        aim = arm.matrix_world @ arm.pose.bones["chest"].tail       # his upper chest, as posed
        RV.look(cam, frm, aim)
        beauty = out / f"r{key}_{a.tag}.png"
        sc.render.film_transparent = False
        sc.render.filepath = str(beauty)
        bpy.ops.render.render(write_still=True)
        # the figure's mask: everything else a holdout, the figure flat white
        hold = [o for o in sc.objects if o.type == "MESH" and o is not sk]
        for o in hold:
            o.is_holdout = True
        wm = bpy.data.materials.get("TMP_white") or bpy.data.materials.new("TMP_white")
        wm.use_nodes = True
        wb = wm.node_tree.nodes["Principled BSDF"]
        wb.inputs["Emission Color"].default_value = (1, 1, 1, 1)
        wb.inputs["Emission Strength"].default_value = 1.0
        old = list(sk.data.materials)
        for i in range(len(sk.data.materials)):
            sk.data.materials[i] = wm
        sc.render.film_transparent = True
        mask = out / f"r{key}_{a.tag}_mask.png"
        sc.render.filepath = str(mask)
        bpy.ops.render.render(write_still=True)
        for i, mm in enumerate(old):
            sk.data.materials[i] = mm
        for o in hold:
            o.is_holdout = False
        sc.render.film_transparent = False
        r.update(still_metrics(sc, cam, arm, sk, beauty, mask))
        r["camera"] = {"from_polar": v, "eye_m": 1.65, "vfov_deg": 72.0}
        report[key] = r
    (out / f"metrics_{a.tag}.json").write_text(json.dumps(report, indent=1))
    print("STILLS_RESULT", json.dumps(report))



# ------------------------------------------------------------------------------------------------ game actions

# Stage R (2026-11-18): the actions ross.glb carries. Each held pose is solved at its mark exactly as the stills
# are (IK to the spec hand target), so the game must stand the root on that mark facing its bearing
# (visitor_figure.gd MARKS). A slow breath (3 s) runs through every one.
GAME_POSES = {"door": "B", "chair": "C", "wheel": "D"}
# D: the wheel's rim is 0.70 m up and 0.36 m in front of him; a 42 degree spine curl left the wrist 13.6 cm
# short (the shoulder stayed 1.40 m up), so he hinges at the hips as well (pelvis forward, legs kept upright)
STILL_POSE.setdefault("D", {"grip": "rail", "fingers": "torch", "head": 8.0, "neck": 6.0, "hinge": 24.0})
WALK_K = (0.72, 0.80, 0.70)        # an old, ill man's stride: thigh, knee and foot swing against body.py's walk
WALK_FRAMES_R = 36                 # 1.2 s a stride (body.py: 0.9 s)


def _breath(arm, f):
    BD = _bd()
    ph = 2 * math.pi * (f - 1) / 90.0
    return {"chest": Quaternion(Vector((1, 0, 0)), math.radians(1.3 * math.sin(ph))),
            "spine": Quaternion(Vector((1, 0, 0)), math.radians(0.5 * math.sin(ph)))}


def _new_action(arm, name):
    act = bpy.data.actions.new(name)
    arm.animation_data.action = act
    return act


def _close_action(arm, act, start):
    act.use_fake_user = True
    tr = arm.animation_data.nla_tracks.new()
    tr.name = act.name
    tr.strips.new(act.name, start, act)
    arm.animation_data.action = None


def held_pose_action(arm, name, key, coll, frames):
    """Solve the mark's pose (IK + damped track), breathe it, and bake the visual result to plain keys."""
    BD = _bd()
    # the actions already made sit on NLA tracks; left live, the depsgraph re-evaluates them over the pose
    # being solved (the first wheel bake lost its lean and hip hinge: the hand 27 cm off the rim)
    for tr in arm.animation_data.nla_tracks:
        tr.mute = True
    arm.animation_data.action = None
    place_and_pose(arm, key, coll)
    base = {b: arm.pose.bones[b].rotation_quaternion.copy() for b in ("chest", "spine")}
    order = sorted(arm.pose.bones, key=lambda pb: len(pb.parent_recursive))
    baked = {}
    for f in frames:
        for b, q in _breath(arm, f).items():
            r = arm.data.bones[b].matrix_local.to_quaternion()
            arm.pose.bones[b].rotation_quaternion = base[b] @ (r.inverted() @ q @ r)
        bpy.context.view_layer.update()
        baked[f] = {pb.name: arm.convert_space(pose_bone=pb, matrix=pb.matrix, from_space="POSE", to_space="LOCAL")
                    for pb in order}
    for pb in arm.pose.bones:
        for c in list(pb.constraints):
            pb.constraints.remove(c)
        pb.rotation_mode = "QUATERNION"            # finger_pose works in Euler; the keys are quaternions
        pb.rotation_euler = (0.0, 0.0, 0.0)
    act = _new_action(arm, name)
    for f in frames:
        for pb in order:
            pb.matrix_basis = baked[f][pb.name]
        BD.key_all(arm, f)
    _close_action(arm, act, frames[0])
    arm.location = (0, 0, 0)
    arm.rotation_euler = (0, 0, 0)
    BD.rest(arm)


def walk_pose(arm, f):
    BD = _bd()
    ph = (f - 1) / WALK_FRAMES_R
    for side, off in (("L", 0.0), ("R", 0.5)):
        th, kn, ft = BD.leg_at(ph + off)
        BD.leg(arm, side, th * WALK_K[0], kn * WALK_K[1], ft * WALK_K[2])
    sw = 7.0 * math.cos(2 * math.pi * ph)                   # the arms swing little: he is tired, the coat is heavy
    BD.set_rot(arm, "upper_arm.L", Vector((1, 0, 0)), sw)
    BD.set_rot(arm, "upper_arm.R", Vector((1, 0, 0)), -sw)
    BD.set_loc(arm, "hips", (0, 0, -0.014 * math.cos(4 * math.pi * ph)))
    BD.set_rot(arm, "hips", Vector((0, 0, 1)), 3.0 * math.cos(2 * math.pi * ph))
    BD.set_rot(arm, "chest", Vector((0, 0, 1)), -3.5 * math.cos(2 * math.pi * ph))
    BD.set_rot(arm, "head", Vector((1, 0, 0)), 6.0)           # watching his feet on a strange floor


def walk_speed(arm, frames):
    """Ground speed the walk implies: how fast the planted foot slides back under the still root (m/s, 30 fps).
    The game moves the root at this speed so the boots do not skate."""
    BD = _bd()
    pts = []
    for f in frames:
        BD.rest(arm)
        walk_pose(arm, f)
        bpy.context.view_layer.update()
        pts.append((f, arm.matrix_world @ arm.pose.bones["foot.L"].head))
    BD.rest(arm)
    # the left foot is planted from heel strike (phase 0) until it lifts (about 0.48): measure 0.05 to 0.40
    st = [(f, p) for f, p in pts if 0.05 <= (f - 1) / WALK_FRAMES_R <= 0.40]
    (f0, p0), (f1, p1) = st[0], st[-1]
    return abs(p1.y - p0.y) / ((f1 - f0) / 30.0)


def clamp_weights(ob):
    """Weights a hair over 1 (the data transfer's interpolation overshoots, up to 1.04) make the mesh invalid
    for the glTF exporter: clamp them. Returns how many were clamped."""
    n = 0
    for v in ob.data.vertices:
        for g in v.groups:
            if g.weight > 1.0:
                g.weight = 1.0
                n += 1
    return n


def run_export(a):
    """Bake the game actions onto ARM_ross and save a new version (the .blend opened is the figure)."""
    from lib.scene_utils import save_versioned
    BD = _bd()
    arm, sk = bpy.data.objects["ARM_ross"], bpy.data.objects["SK_ross"]
    clamped = clamp_weights(sk)
    arm.animation_data_create()
    for tr in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(tr)
    tmp = bpy.data.collections.new("TMP_targets")
    bpy.context.scene.collection.children.link(tmp)
    bpy.context.scene.render.fps = 30
    breath_frames = list(range(1, 92, 6))

    def idle(f):
        for b, q in _breath(arm, f).items():
            r = arm.data.bones[b].matrix_local.to_quaternion()
            arm.pose.bones[b].rotation_quaternion = r.inverted() @ q @ r
    BD.make_action(arm, "idle", breath_frames, idle)

    wf = list(range(1, WALK_FRAMES_R + 2))
    BD.make_action(arm, "walk", wf, lambda f: walk_pose(arm, f))
    for tr in arm.animation_data.nla_tracks:
        tr.mute = True
    speed = walk_speed(arm, wf)
    for name, key in GAME_POSES.items():
        held_pose_action(arm, name, key, tmp, breath_frames)
    for o in list(tmp.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(tmp)
    BD.rest(arm)
    for tr in arm.animation_data.nla_tracks:
        tr.mute = True                                       # saved at rest; the export writes each action
    res = {"actions": [t.name for t in arm.animation_data.nla_tracks], "walk_speed_mps": round(speed or 0.0, 3),
           "weights_clamped": clamped, "mesh_valid": not sk.data.copy().validate()}
    if a.save:
        res["saved"] = save_versioned(HERE, "last_light_ross")
    print("EXPORT_RESULT", json.dumps(res))


def flat_materials(sk):
    """Stand-ins before the bake: one slot per part, flat colours (geometry review only)."""
    cols = {0: "#1E1D1A", 1: "#1E1D1A", 2: "#151515", 3: "#5E5950", 4: "#B48770", 5: "#B48770", 6: "#4A4540",
            7: "#BDB8AE", 8: "#A9A49B"}
    from lib.scene_utils import hex_to_linear
    sk.data.materials.clear()
    for k in range(9):
        m = bpy.data.materials.new(f"TMP_flat_{k}")
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = hex_to_linear(cols[k])
        b.inputs["Roughness"].default_value = 0.3 if k in (0, 1, 2) else 0.6
        sk.data.materials.append(m)
    part = sk.data.attributes["part"]
    for p in sk.data.polygons:
        p.material_index = part.data[p.index].value


def preview(arm, sk, out, tag="p"):
    """Neutral-light review: ortho front, side, back, a 3/4 and the face close, and a 160 px glance thumbnail."""
    out = ensure_allowed(out)
    out.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("RossPrev")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.30, 0.31, 0.33, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    sc.world = w
    cam = bpy.data.objects.new("PrevCam", bpy.data.cameras.new("PrevCam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    for nm, loc, rot, e in (("key", (1.6, -2.4, 2.6), (55, 0, 32), 500), ("rim", (-1.2, 2.2, 2.4), (-55, 0, 200), 350),
                            ("fill", (-2.2, -1.4, 1.4), (70, 0, -60), 150)):
        L = bpy.data.objects.new("Prev_" + nm, bpy.data.lights.new(nm, "AREA"))
        L.data.energy, L.data.size = e, 1.5
        sc.collection.objects.link(L)
        L.location = loc
        L.rotation_euler = tuple(math.radians(v) for v in rot)
    shots = [("front", "ORTHO", (0, -4, 0.95), (90, 0, 0), 2.1, (700, 1000)),
             ("side", "ORTHO", (4, 0, 0.95), (90, 0, 90), 2.1, (700, 1000)),
             ("back", "ORTHO", (0, 4, 0.95), (90, 0, 180), 2.1, (700, 1000)),
             ("q34", "PERSP", (-1.9, -2.5, 1.55), (86, 0, -37), 50, (900, 1200)),
             ("face", "PERSP", (-0.45, -0.85, 1.60), (88, 0, -28), 85, (800, 800)),
             ("glance", "PERSP", (-1.9, -2.5, 1.55), (86, 0, -37), 50, (120, 160))]
    for name, typ, loc, rot, lens, res in shots:
        cam.data.type = typ
        if typ == "ORTHO":
            cam.data.ortho_scale = lens
        else:
            cam.data.lens = lens
        cam.location = loc
        cam.rotation_euler = tuple(math.radians(v) for v in rot)
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.filepath = str(out / f"{tag}_{name}.png")
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    for o in list(bpy.data.objects):
        if o.name.startswith("Prev_"):
            bpy.data.objects.remove(o, do_unlink=True)


def run_build(a):
    from lib.scene_utils import clear_scene, get_collection, save_versioned
    if a.new:
        clear_scene()
    bpy.context.scene.render.fps = 30
    coll = get_collection("ASSET_ross")
    arm, sk, K = build_figure(coll)
    for o in list(bpy.data.objects):
        if o.name.startswith("TMP_") and o.type in ("ARMATURE", "MESH"):
            bpy.data.objects.remove(o, do_unlink=True)
    res = {"tris": count_tris(sk), "bones": len(arm.data.bones), "verts": len(sk.data.vertices),
           "height_m": round(max((sk.matrix_world @ v.co).z for v in sk.data.vertices), 3),
           "eye_u": round(K["eye_u"], 3)}
    eyes_w = []
    part = sk.data.attributes["part"]
    ev = {}
    for poly in sk.data.polygons:
        if part.data[poly.index].value == PART["eyes"]:
            for vi in poly.vertices:
                ev[vi] = sk.data.vertices[vi].co.copy()
    for sgn in (1, -1):
        pts = [c for c in ev.values() if (c - K["o"]).dot(K["rt"]) * sgn > 0]
        if pts:
            eyes_w.append(sum(pts, Vector()) / len(pts))
    arm["landmarks"] = {"eyes": [list(e) for e in eyes_w], "nose": [list(K["nose"])],
                        "cheeks": [list(c) for c in K["cheeks"]], "chin": [list(to_world(K, *K["chin"]))]}
    if a.notex:
        flat_materials(sk)
    else:
        res.update(texture(sk))
    if a.preview:
        preview(arm, sk, a.preview, a.tag)
    if a.save:
        res["saved"] = save_versioned(HERE, "last_light_ross")
    print("ROSS_RESULT", json.dumps(res))



# ------------------------------------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marks", default="")
    ap.add_argument("--norender", action="store_true", help="marks: the checks only")
    ap.add_argument("--new", action="store_true")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--notex", action="store_true", help="flat stand-in colours, no bake (geometry review)")
    ap.add_argument("--preview", default="")
    ap.add_argument("--tag", default="p")
    ap.add_argument("--calibrate", default="")
    ap.add_argument("--k", type=float, default=CAL["k"])
    ap.add_argument("--amb", type=float, default=CAL["amb"])
    ap.add_argument("--kf", type=float, default=CAL.get("kf"))
    ap.add_argument("--stills", default="")
    ap.add_argument("--figure", default="")
    ap.add_argument("--only", default="A,B,C")
    ap.add_argument("--sweep", action="store_true", help="brim sweep (ray tests) instead of renders")
    ap.add_argument("--actions", action="store_true", help="bake the game actions onto the opened figure .blend")
    a = parse(ap)
    global _ARGS
    _ARGS = a
    if a.calibrate:
        run_calibrate(a.calibrate, a.k, a.amb)
        return
    if a.stills:
        run_stills(a)
        return
    if a.actions:
        run_export(a)
        return
    if a.marks:
        run_marks(a.marks)
    elif a.new or a.save or a.preview:
        run_build(a)


if __name__ == "__main__":
    main()
