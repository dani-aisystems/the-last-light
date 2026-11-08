"""THE LAST LIGHT · G3c (Daniel 2026-11-08): the keeper's body, seen when he looks down, and his shadow.

Daniel's decisions: the G3b camera hands stay; the body shows legs, boots and torso; its arms and head only
cast shadows (SK_body_shadow, set to shadows-only in Godot); our own light rig with region-limited distance weights (bone heat failed on this mesh);
walk / idle / sit hand-keyed here; the body casts shadows.

Callum (character-refs/callum/PROFILE.md §G): lean, upright; a dark navy / charcoal guernsey, a worn shirt,
practical wool trousers, stout boots. No insignia.

Source: "GEO-body_male_realistic" from Blender Studio's Human Base Meshes v1.4.1 (CC0,
assets/ASSET_LICENSES.md), base level (21k tris), an A-pose facing -Y, 1.69 m. Scaled so the eyes sit at
the game's 1.65 m (player.gd EYE): 1.77 m.

Output collection ASSET_body: ARM_body with SK_body (visible: legs, boots, torso) and SK_body_shadow (arms,
hands, neck, head). Actions: idle (loop), walk (loop; one stride of two 0.72 m steps in 0.9 s = 1.6 m/s,
the WALK speed), sit (held). Origin at the feet, between them.

  tools/bl -P projects/games/last_light/blender/body.py -- --new --save [--preview DIR]
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = Path(__file__).resolve().parent
WS = HERE.parents[3]
sys.path.insert(0, str(WS / "scripts"))
from lib.scene_utils import clear_scene, get_collection, save_versioned, hex_to_linear  # noqa: E402

BUNDLE = WS / "assets/models/human_base_meshes/bundle/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"
SRC_NAME = "GEO-body_male_realistic"
EYE_SRC = 1.575                 # traced: the eyes of the source mesh
EYE_GAME = 1.65                 # player.gd EYE
S = EYE_GAME / EYE_SRC

GUERNSEY = "#343A46"            # G3c captures: #272B33 read flat black on the body; still dark navy-charcoal
TROUSERS = "#4B473F"            # dark grey-brown wool (#34332F read black)
BOOTS = "#3E2F25"               # dark oiled leather (#2B211A read black)
SKIN = "#C99079"                # as the G3b hands (shadow-only here)

# Joints traced from slices of the source mesh (metres, source scale; front is -Y, the keeper's left is +X).
J = {
    "hips": ((0, 0.0, 0.92), (0, 0.0, 1.02)),
    "spine": ((0, 0.0, 1.02), (0, -0.005, 1.15)),
    "chest": ((0, -0.005, 1.15), (0, -0.01, 1.38)),
    "neck": ((0, -0.02, 1.40), (0, -0.04, 1.50)),
    "head": ((0, -0.04, 1.50), (0, -0.04, 1.68)),
    "thigh.L": ((0.09, 0.0, 0.90), (0.135, 0.005, 0.48)),
    "shin.L": ((0.135, 0.005, 0.48), (0.172, 0.045, 0.09)),
    "foot.L": ((0.172, 0.045, 0.09), (0.21, -0.08, 0.02)),
    "toe.L": ((0.21, -0.08, 0.02), (0.225, -0.13, 0.015)),
    "upper_arm.L": ((0.175, 0.0, 1.37), (0.30, 0.0, 1.08)),
    "forearm.L": ((0.30, 0.0, 1.08), (0.36, -0.045, 0.90)),
    "hand.L": ((0.36, -0.045, 0.90), (0.40, -0.12, 0.78)),
}
PARENT = {"spine": "hips", "chest": "spine", "neck": "chest", "head": "neck",
          "thigh": "hips", "shin": "thigh", "foot": "shin", "toe": "foot",
          "upper_arm": "chest", "forearm": "upper_arm", "hand": "forearm"}
SHADOW_BONES = ("upper_arm", "forearm", "hand", "neck", "head")
FPS = 30
WALK_FRAMES = 27                # 0.9 s per stride (two steps)
STEP = 0.72                     # metres per step at the WALK speed

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = {"new": "--new" in a, "save": "--save" in a, "preview": ""}
    if "--preview" in a:
        out["preview"] = a[a.index("--preview") + 1]
    return out


def material(name, hex_, rough, sheen=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex_to_linear(hex_)
    b.inputs["Roughness"].default_value = rough
    if "Sheen Weight" in b.inputs:
        b.inputs["Sheen Weight"].default_value = sheen
    return m


def joint(name):
    """Head and tail (scaled) for a bone name; .R mirrors the .L trace."""
    base = name.replace(".R", ".L")
    h, t = J[base]
    m = -1.0 if name.endswith(".R") else 1.0
    return Vector((h[0] * m, h[1], h[2])) * S, Vector((t[0] * m, t[1], t[2])) * S


def source_body(coll):
    with bpy.data.libraries.load(str(BUNDLE)) as (src, dst):
        dst.objects = [SRC_NAME]
    ob = dst.objects[0]
    coll.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        if m.type == "MULTIRES":
            m.levels = 0
            bpy.ops.object.modifier_apply(modifier=m.name)
    ob.data = ob.data.copy()
    # Local coordinates, not world: the bundle places this object at x -2.264 for its layout, and the
    # joints above were traced in the mesh's own space (feet at the origin, facing -Y).
    ob.data.transform(Matrix.Scale(S, 4))
    ob.matrix_world = Matrix.Identity(4)
    ob.name = "SK_body"
    ob.data.name = "SK_body"
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def build_armature(coll):
    arm = bpy.data.armatures.new("ARM_body")
    ob = bpy.data.objects.new("ARM_body", arm)
    coll.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones
    names = ["hips", "spine", "chest", "neck", "head"]
    for side in ("L", "R"):
        names += [f"{b}.{side}" for b in ("thigh", "shin", "foot", "toe", "upper_arm", "forearm", "hand")]
    for n in names:
        b = eb.new(n)
        b.head, b.tail = joint(n)
        b.align_roll(Vector((0, -1, 0)) if abs((b.tail - b.head).normalized().y) < 0.9 else Vector((0, 0, 1)))
    for n in names:
        base = n.split(".")[0]
        if base in PARENT:
            par = PARENT[base] + ("." + n.split(".")[1] if "." in n and PARENT[base] not in ("hips", "chest") else "")
            eb[n].parent = eb[par]
            eb[n].use_connect = (eb[n].head - eb[par].tail).length < 1e-4
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in ob.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return ob


def clothe(body, mats):
    """Materials by region, and each layer pushed out along the normals (the guernsey hem over the trousers)."""
    me = body.data
    for m in mats:
        me.materials.append(m)
    boot_z, waist_z, neck_z, wrist_z = 0.17 * S, 0.95 * S, 1.42 * S, 0.90 * S

    def region(co):
        if co.z > neck_z:
            return 3                              # skin: neck and head
        if _is_arm(co):
            return 3 if co.z < wrist_z else 0      # hands skin, sleeves guernsey
        if co.z < boot_z:
            return 2
        if co.z < waist_z:
            return 1
        return 0
    push = {0: 0.010, 1: 0.007, 2: 0.012, 3: 0.0}
    for p in me.polygons:
        p.material_index = region(p.center)
    vreg = [region(v.co) for v in me.vertices]
    for v, r in zip(me.vertices, vreg):
        v.co += v.normal * push[r]
        if r == 2 and v.co.z < 0.012:
            v.co.z = 0.0                          # a flat sole on the floor
    me.update()


def _seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length


def _is_arm(co):
    lim = 0.20 * S if co.z < 1.15 * S else 0.15 * S
    return abs(co.x) > lim and 0.70 * S < co.z < 1.42 * S


def weights(body, arm_ob):
    """Region-limited distance weights. Blender's bone heat failed on this mesh (every vertex went to one
    bone), so: each vertex picks bones from its own limb's chain (plus the bone it hangs from) and blends
    the two nearest by inverse distance^4."""
    bones = {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in arm_ob.data.bones}
    for n in bones:
        body.vertex_groups.new(name=n)
    vg = {g.name: g for g in body.vertex_groups}
    crotch = 0.86 * S
    for v in body.data.vertices:
        co = v.co
        side = "L" if co.x > 0 else "R"
        if _is_arm(co):
            cand = [f"upper_arm.{side}", f"forearm.{side}", f"hand.{side}", "chest"]
        elif co.z < crotch:
            cand = [f"thigh.{side}", f"shin.{side}", f"foot.{side}", f"toe.{side}", "hips"]
        else:
            cand = ["hips", "spine", "chest", "neck", "head"] + ([f"thigh.{side}"] if co.z < 1.0 * S else [])
        ds = sorted((_seg_dist(co, *bones[n]), n) for n in cand)[:2]
        w = [1.0 / max(d, 0.01) ** 4 for d, _ in ds]
        tot = sum(w)
        for (d, n), wi in zip(ds, w):
            if wi / tot > 0.02:
                vg[n].add([v.index], wi / tot, "REPLACE")
    body.parent = arm_ob
    mod = body.modifiers.new("Armature", "ARMATURE")
    mod.object = arm_ob


def boot(name, side, coll, mat):
    """A stout leather boot, lofted along the foot (heel to toe) plus a shaft round the ankle; replaces the
    bare foot (whose toes showed through a shaded 'boot'). Built in the foot's frame, splayed as traced."""
    sgn = 1.0 if side == "L" else -1.0
    ankle = Vector((0.172 * sgn, 0.045, 0.0)) * S
    ball = Vector((0.21 * sgn, -0.08, 0.0)) * S
    d = (ball - ankle).normalized()                       # along the foot, toward the toe (mostly -Y)
    ax = Vector((-d.y, d.x, 0.0)) * (-1.0 if side == "L" else 1.0)   # across the foot, outward
    if ax.x * sgn < 0:
        ax = -ax
    bm = bmesh.new()
    seg = 20

    def ring(c, hw, hd, z0, z1, n=seg):
        # a superellipse section in the plane across the foot: hw across, from the sole z0 to the top z1
        out = []
        for i in range(n):
            a = 2 * math.pi * i / n
            ca, sa = math.cos(a), math.sin(a)
            x = hw * math.copysign(abs(ca) ** 0.6, ca)
            z = (z0 + z1) / 2 + (z1 - z0) / 2 * math.copysign(abs(sa) ** 0.5, sa)
            out.append(bm.verts.new(c + ax * x + Vector((0, 0, z))))
        return out
    # along the foot: (distance from the ankle toward the toe, half width, top height)
    prof = [(-0.085, 0.028, 0.090), (-0.075, 0.038, 0.114), (-0.04, 0.042, 0.120), (0.0, 0.044, 0.118),
            (0.05, 0.047, 0.106), (0.10, 0.049, 0.092), (0.14, 0.047, 0.082), (0.17, 0.042, 0.072),
            (0.19, 0.032, 0.060), (0.20, 0.018, 0.046)]       # v3 (G3c captures): 30 cm long (was 35), narrower toe
    rings = [ring(ankle + d * (t * S), w * S, 0, 0.0, h * S) for t, w, h in prof]
    # the shaft: rings up round the ankle
    for z in (0.10, 0.15, 0.19):
        c = ankle + d * (-0.01 * S)
        rings.append([bm.verts.new(c + ax * (0.052 * S * math.cos(2 * math.pi * i / seg)) +
                                   d * (0.060 * S * math.sin(2 * math.pi * i / seg)) + Vector((0, 0, z * S)))
                      for i in range(seg)])
    for k in range(len(prof) - 1):
        for i in range(seg):
            bm.faces.new((rings[k][i], rings[k][(i + 1) % seg], rings[k + 1][(i + 1) % seg], rings[k + 1][i]))
    for k in range(len(prof), len(rings) - 1):
        for i in range(seg):
            bm.faces.new((rings[k][i], rings[k][(i + 1) % seg], rings[k + 1][(i + 1) % seg], rings[k + 1][i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[len(prof) - 1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    coll.objects.link(ob)
    return ob


def merge_into(body, parts):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()


def drop_feet(body):
    """The bare feet go: the boots replace them (anything below the trouser hem inside the boot shaft)."""
    bm = bmesh.new()
    bm.from_mesh(body.data)
    kill = [f for f in bm.faces if f.calc_center_median().z < 0.15 * S]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(body.data)
    bm.free()


def split_shadow(body, coll):
    """Faces whose vertices belong mostly to arm / neck / head bones go to SK_body_shadow."""
    gi = {g.index: g.name for g in body.vertex_groups}
    shadow_v = set()
    for v in body.data.vertices:
        best, w = None, 0.0
        for g in v.groups:
            if g.weight > w:
                best, w = gi[g.group], g.weight
        if best and best.split(".")[0] in SHADOW_BONES:
            shadow_v.add(v.index)
    sh = body.copy()
    sh.data = body.data.copy()
    sh.name = sh.data.name = "SK_body_shadow"
    coll.objects.link(sh)
    for ob, keep_shadow in ((body, False), (sh, True)):
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        kill = [f for f in bm.faces if (sum(v.index in shadow_v for v in f.verts) * 2 > len(f.verts)) != keep_shadow]
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(ob.data)
        bm.free()
    return sh


# ---------------------------------------------------------------- poses (world-space, converted per bone)

def set_rot(arm_ob, name, axis, deg):
    """Rotate a bone by deg about an armature-space axis, relative to its parent (rest-frame conjugation)."""
    pb = arm_ob.pose.bones[name]
    r = arm_ob.data.bones[name].matrix_local.to_quaternion()
    pb.rotation_quaternion = r.inverted() @ Quaternion(axis, math.radians(deg)) @ r


def set_loc(arm_ob, name, world):
    pb = arm_ob.pose.bones[name]
    r = arm_ob.data.bones[name].matrix_local.to_3x3()
    pb.location = r.inverted() @ Vector(world)


def rest(arm_ob):
    for pb in arm_ob.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)


def arms_down(arm_ob, swing_l=0.0, swing_r=0.0):
    # A-pose to hanging: the upper arm in toward the body; a little elbow bend; forward swing (deg) per side
    for side, sgn, sw in (("L", 1.0, swing_l), ("R", -1.0, swing_r)):
        q_in = Quaternion(Y, math.radians(17.0 * sgn))
        q_sw = Quaternion(X, math.radians(-sw))
        pb = arm_ob.pose.bones[f"upper_arm.{side}"]
        r = arm_ob.data.bones[f"upper_arm.{side}"].matrix_local.to_quaternion()
        pb.rotation_quaternion = r.inverted() @ (q_sw @ q_in) @ r
        set_rot(arm_ob, f"forearm.{side}", X, -(10.0 + max(0.0, sw) * 0.6))


def leg(arm_ob, side, thigh, knee, foot):
    """thigh: forward swing (deg); knee: bend (deg, the shin back); foot: toes up (deg)."""
    set_rot(arm_ob, f"thigh.{side}", X, -thigh)
    set_rot(arm_ob, f"shin.{side}", X, knee)
    set_rot(arm_ob, f"foot.{side}", X, -foot)


def key_all(arm_ob, frame):
    for pb in arm_ob.pose.bones:
        pb.keyframe_insert("rotation_quaternion", frame=frame)
        pb.keyframe_insert("location", frame=frame)


# One leg over a stride (phase 0 = heel strike): (phase, thigh, knee, foot)
# v2 (R17: the planted foot drifted 0.13 m a step): +30 / -24, so the stance sweep matches 1.6 m/s
LEG_CYCLE = [(0.00, 30, 4, 8), (0.12, 21, 14, 0), (0.30, 3, 6, 0), (0.48, -24, 8, -6),
             (0.60, -18, 40, -10), (0.75, 8, 58, 0), (0.90, 28, 18, 6), (1.00, 30, 4, 8)]


def leg_at(ph):
    ph %= 1.0
    for a, b in zip(LEG_CYCLE, LEG_CYCLE[1:]):
        if a[0] <= ph <= b[0]:
            t = (ph - a[0]) / (b[0] - a[0])
            t = t * t * (3 - 2 * t)
            return tuple(a[i] + (b[i] - a[i]) * t for i in (1, 2, 3))
    return LEG_CYCLE[0][1:]


def make_action(arm_ob, name, frames, pose_at):
    rest(arm_ob)
    act = bpy.data.actions.new(name)
    arm_ob.animation_data.action = act
    for f in frames:
        rest(arm_ob)
        pose_at(f)
        key_all(arm_ob, f)
    act.use_fake_user = True
    tr = arm_ob.animation_data.nla_tracks.new()
    tr.name = name
    tr.strips.new(name, frames[0], act)
    arm_ob.animation_data.action = None
    return act


def bake_actions(arm_ob):
    arm_ob.animation_data_create()

    def idle(f):
        arms_down(arm_ob)
        set_rot(arm_ob, "chest", X, 1.2 * math.sin(2 * math.pi * (f - 1) / 90.0))   # a slow breath, 3 s

    def walk(f):
        ph = (f - 1) / WALK_FRAMES
        for side, off in (("L", 0.0), ("R", 0.5)):
            leg(arm_ob, side, *leg_at(ph + off))
        sw = 12.0 * math.cos(2 * math.pi * ph)            # arms opposite the legs
        arms_down(arm_ob, swing_l=-sw, swing_r=sw)
        bob = -0.022 * math.cos(4 * math.pi * ph)          # down at each heel strike
        set_loc(arm_ob, "hips", (0, 0, bob))
        set_rot(arm_ob, "hips", Z, 4.0 * math.cos(2 * math.pi * ph))
        set_rot(arm_ob, "chest", Z, -5.0 * math.cos(2 * math.pi * ph))

    def sit(f):
        # the chair seat is 0.46 m high (build.py); the hip joint over its centre at about 0.55 m
        drop = 0.92 * S - 0.55
        set_loc(arm_ob, "hips", (0, 0.0, -drop))
        for side in ("L", "R"):
            leg(arm_ob, side, 88.0, 92.0, 0.0)
        set_rot(arm_ob, "spine", X, -6.0)                  # leaning to the set
        arms_down(arm_ob, 30.0, 30.0)

    make_action(arm_ob, "idle", list(range(1, 92, 6)), idle)
    make_action(arm_ob, "walk", list(range(1, WALK_FRAMES + 2)), walk)
    make_action(arm_ob, "sit", [1, 2], sit)
    rest(arm_ob)
    for tr in arm_ob.animation_data.nla_tracks:
        tr.mute = True                                     # saved and validated at rest; the export writes each action


def main():
    a = args()
    if a["new"]:
        clear_scene()
    bpy.context.scene.render.fps = FPS
    coll = get_collection("ASSET_body")
    mats = [material("M_LL_Guernsey", GUERNSEY, 0.92, 0.6), material("M_LL_Trousers", TROUSERS, 0.88, 0.3),
            material("M_LL_Boots", BOOTS, 0.55), material("M_LL_Skin", SKIN, 0.52, 0.15)]
    body = source_body(coll)
    arm_ob = build_armature(coll)
    clothe(body, mats)
    drop_feet(body)
    merge_into(body, [boot(f"boot_{s}", s, coll, mats[2]) for s in ("L", "R")])
    weights(body, arm_ob)
    shadow = split_shadow(body, coll)
    bake_actions(arm_ob)
    res = {"objects": len(coll.all_objects), "bones": len(arm_ob.data.bones), "tris": {}, "scale": round(S, 4)}
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in (body, shadow):
        m = ob.evaluated_get(dg).to_mesh()
        m.calc_loop_triangles()
        res["tris"][ob.name] = len(m.loop_triangles)
    if a["preview"]:
        preview(arm_ob, a["preview"])
    if a["save"]:
        res["saved"] = save_versioned(HERE, "last_light_body")
    print("BODY_RESULT", json.dumps(res))


def preview(arm_ob, outdir):
    """Front and side of idle, two walk frames and the sit pose, orthographic, for the review."""
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT" if any(e.identifier == "BLENDER_EEVEE_NEXT" for e in
                                                   bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items) else "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 600, 900
    world = bpy.data.worlds.new("w")
    world.color = (0.32, 0.33, 0.35)
    sc.world = world
    cam = bpy.data.objects.new("pcam", bpy.data.cameras.new("pcam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 2.0
    sc.collection.objects.link(cam)
    sc.camera = cam
    for nm, loc, rot, e in (("key", (1.5, -2.5, 2.5), (55, 0, 30), 600), ("fill", (-2.0, -1.0, 1.5), (65, 0, -60), 250)):
        L = bpy.data.objects.new(nm, bpy.data.lights.new(nm, "AREA"))
        L.data.energy, L.data.size = e, 2.0
        sc.collection.objects.link(L)
        L.location = loc
        L.rotation_euler = tuple(math.radians(v) for v in rot)
    shots = [("idle", 1, "front"), ("idle", 1, "side"), ("walk", 1, "side"), ("walk", 8, "side"), ("sit", 1, "side")]
    for act, frame, view in shots:
        arm_ob.animation_data.action = bpy.data.actions[act]
        sc.frame_set(frame)
        cam.location = (0, -4, 0.95) if view == "front" else (4, 0, 0.95)
        cam.rotation_euler = (math.radians(90), 0, 0) if view == "front" else (math.radians(90), 0, math.radians(90))
        sc.render.filepath = f"{outdir}/body_{act}{frame}_{view}.png"
        bpy.ops.render.render(write_still=True)
    arm_ob.animation_data.action = None
    rest(arm_ob)


if __name__ == "__main__":
    main()
