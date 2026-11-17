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
the WALK speed), sit (held), sitdown (Stage P: standing to seated in 11 keys, sought by the camera blend).
Origin at the feet, between them.

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

GUERNSEY = "#363F58"            # Stage P (Q19): the chair gansey's navy (knit_tex.py measures documents.knit)
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
SITDOWN_KEYS = 11               # Stage P: the sit-down blend, s = 0, 0.1 ... 1

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

# Audit Stage P (4.1): the clothes are garments, not the skin pushed out. Heights (scaled, metres):
NECK_Z, WRIST_Z, WAIST_Z, HEM_Z, BOOT_Z = 1.42 * S, 0.90 * S, 0.95 * S, 0.885 * S, 0.17 * S
WELT = 0.06                     # the guernsey's ribbed welt above the hem: snug over the trousers' waistband
TEX = HERE / "textures" / "cloth"   # knit_tex.py (run it first)
KNIT_TILE = 32 * 10 / 12 / 100  # knit_tex.py: metres per tile
TWILL_TILE = 0.06


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = {"new": "--new" in a, "save": "--save" in a, "preview": "", "check": ""}
    for k in ("preview", "check"):
        if "--" + k in a:
            out[k] = a[a.index("--" + k) + 1]
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


def tex_material(name, albedo, normal, rough, rough_val, sheen=0.0):
    """Principled BSDF with albedo / OpenGL normal / roughness maps from knit_tex.py (glTF exports them)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough_val
    if "Sheen Weight" in b.inputs:
        b.inputs["Sheen Weight"].default_value = sheen

    def img(fn, colour):
        path = TEX / fn
        if not path.exists():
            raise SystemExit(f"missing {path}: run tools/py projects/games/last_light/blender/knit_tex.py first")
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(str(path), check_existing=True)
        n.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        return n
    nt.links.new(img(albedo, True).outputs["Color"], b.inputs["Base Color"])
    if normal:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(img(normal, False).outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if rough:
        nt.links.new(img(rough, False).outputs["Color"], b.inputs["Roughness"])
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


def part_of(co, mat_name, m=0.03):
    """Which garment(s) a body face belongs to, with a margin m: the edges are then cut exactly by planes
    (garment_cuts). The welt band (HEM_Z .. WAIST_Z) is in both: the guernsey over the trousers' waistband."""
    if mat_name == "M_LL_Boots":
        return {"boots"}
    out = set()
    if _is_arm(co):
        if co.z >= WRIST_Z - m:
            out.add("guernsey")
        if co.z < WRIST_Z + m:
            out.add("skin")
        return out
    if co.z > NECK_Z - m:
        out.add("skin")
    if HEM_Z - m <= co.z <= NECK_Z + m:
        out.add("guernsey")
    if BOOT_Z - m <= co.z <= WAIST_Z + m:
        out.add("trousers")
    return out


def garment_cuts(kind):
    """Planes (point, normal, which verts) whose positive side is cut away: clean, level hems instead of the
    face staircase. The neckline dips 2.5 cm at the front (a crew neck); each cuff is square to its forearm."""
    if kind == "trousers":
        return [(Vector((0, 0, WAIST_Z)), Vector((0, 0, 1)), None),
                (Vector((0, 0, BOOT_Z)), Vector((0, 0, -1)), None)]
    cuts = [(Vector((0, 0, HEM_Z)), Vector((0, 0, -1)), lambda co: abs(co.x) < 0.20 * S),
            (Vector((0, 0, NECK_Z)), Vector((0, -0.25, 1)).normalized(), None)]
    for side, sgn in (("L", 1.0), ("R", -1.0)):
        h, t = joint(f"forearm.{side}")
        cuts.append((t, (t - h).normalized(), lambda co, sgn=sgn: co.x * sgn > 0.15 * S))
    return cuts


def skin_cuts():
    """The skin left under nothing: the neck and head above the neckline, the hands below the cuffs (cut 1 cm
    inside the garment so no gap opens between them)."""
    cuts = [(Vector((0, 0, NECK_Z - 0.01)), -Vector((0, -0.25, 1)).normalized(),
             lambda co: co.z > 1.2 * S and not _is_arm(co))]          # the neck only (never the boots)
    for side, sgn in (("L", 1.0), ("R", -1.0)):
        h, t = joint(f"forearm.{side}")
        d = (t - h).normalized()
        cuts.append((t - d * 0.01, -d, lambda co, sgn=sgn: co.x * sgn > 0.15 * S and _is_arm(co)))
    return cuts


def cut(me, cuts):
    bm = bmesh.new()
    bm.from_mesh(me)
    for co, no, which in cuts:
        verts = [v for v in bm.verts if which is None or which(v.co)]
        vs = set(verts)
        edges = [e for e in bm.edges if e.verts[0] in vs and e.verts[1] in vs]
        faces = [f for f in bm.faces if all(v in vs for v in f.verts)]
        bmesh.ops.bisect_plane(bm, geom=verts + edges + faces, dist=1e-5, plane_co=co, plane_no=no,
                               clear_outer=True)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(me)
    bm.free()


def _smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def guernsey_offset(co):
    """Off the skin along its normal: snug at the welt and the sleeves, easy over the belly and back (a
    working jumper, not a skin), back to fitted across the chest and shoulders."""
    if _is_arm(co):
        return 0.008
    if co.z < HEM_Z + WELT:
        return 0.016                      # the welt: 10 mm clear of the waistband (walk and sit moved it 2.9 mm)
    above = co.z - (HEM_Z + WELT)
    loose = _smooth01(above / 0.04) * (1.0 - _smooth01((co.z - 1.12 * S) / 0.12))
    # the knit blouses over the tighter welt: soft horizontal ripples, wandering round the body, fading upward
    th = math.atan2(co.x, -co.y)
    ripple = 0.5 + 0.5 * math.sin(2 * math.pi * above / 0.035 + 1.6 * math.sin(3 * th))
    blouse = (1.0 - _smooth01(above / 0.11)) * _smooth01(above / 0.01)
    return 0.013 + 0.008 * loose + 0.0028 * ripple * blouse


def trousers_offset(co, n):
    """Wool trousers with volume: 12 mm off the leg, cinched to 6 mm at the waistband (under the welt), a
    little fuller over the knee and the seat."""
    top = _smooth01((co.z - (HEM_Z - 0.05)) / 0.05)
    off = 0.012 * (1.0 - top) + 0.006 * top
    off += 0.004 * math.exp(-((co.z - 0.48 * S) / 0.07) ** 2) * max(0.0, -n.y)        # knee, at the front
    off += 0.004 * math.exp(-((co.z - 0.80 * S) / 0.06) ** 2) * max(0.0, n.y) * (1.0 - top)   # seat
    return off


def foot_frame(side):
    """As boot() builds it: (ankle, along the foot toward the toe, across the foot outward)."""
    sgn = 1.0 if side == "L" else -1.0
    ankle = Vector((0.172 * sgn, 0.045, 0.0)) * S
    ball = Vector((0.21 * sgn, -0.08, 0.0)) * S
    d = (ball - ankle).normalized()
    ax = Vector((-d.y, d.x, 0.0))
    if ax.x * sgn < 0:
        ax = -ax
    return ankle, d, ax


def trouser_hem(me):
    """The hem clears the boot shaft (its ellipse + 7 mm) and breaks: lower at the front, over the instep."""
    for v in me.vertices:
        if v.co.z > 0.27 * S:
            continue
        side = "L" if v.co.x > 0 else "R"
        ankle, d, ax = foot_frame(side)
        c = ankle + d * (-0.01 * S)
        rel = Vector((v.co.x - c.x, v.co.y - c.y, 0.0))
        a, b = rel.dot(ax), rel.dot(d)
        ln = max(rel.length, 1e-6)
        ca, sb = a / ln, b / ln
        r_e = 1.0 / math.sqrt((ca / (0.052 * S)) ** 2 + (sb / (0.060 * S)) ** 2)
        ramp = 1.0 - _smooth01((v.co.z - 0.20 * S) / (0.07 * S))
        want = r_e + 0.007
        if ln < want and ramp > 0:
            k = (want - ln) * ramp
            v.co.x += rel.x / ln * k
            v.co.y += rel.y / ln * k
        if v.co.z < 0.20 * S and sb > 0:
            v.co.z -= 0.012 * sb * (1.0 - _smooth01((v.co.z - BOOT_Z) / 0.04))


def garment(body, faces, name, offset, cuts=()):
    """A copy of the body (its weights, parent and armature come with it) keeping only `faces`, each vertex
    moved out along the skin's own normal by offset(co, normal), then trimmed by the cut planes."""
    ob = body.copy()
    ob.data = body.data.copy()
    ob.name = ob.data.name = name
    for c in body.users_collection:
        c.objects.link(ob)
    me = ob.data
    for v, v0 in zip(me.vertices, body.data.vertices):
        v.co = v0.co + v0.normal * offset(v0.co, v0.normal)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    keep = set(faces)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(me)
    bm.free()
    cut(me, cuts)
    return ob


def turn_in(ob, depth):
    """Every open edge of the garment gets a turned-in rim `depth` deep (toward the body), so a hem, cuff or
    neck reads as cloth with thickness, never a paper edge; it also closes the gap to the skin."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.normal_update()
    bnd = [e for e in bm.edges if e.is_boundary]
    inward = {tuple(round(c, 6) for c in v.co): -v.normal.copy() for e in bnd for v in e.verts}
    geom = bmesh.ops.extrude_edge_only(bm, edges=bnd)["geom"]
    for v in [g for g in geom if isinstance(g, bmesh.types.BMVert)]:
        n = inward.get(tuple(round(c, 6) for c in v.co))
        if n is not None:
            v.co += n * depth
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()


def _chain_uv(p, segs, tile, radius, ref):
    """Cylindrical UV round a bone chain: u = arc round the axis, v = distance along it."""
    best, along_best, acc = None, 0.0, 0.0
    for a, b in segs:
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
        d = (p - (a + ab * t)).length
        if best is None or d < best[0]:
            best = (d, a + ab * t, ab.normalized())
            along_best = acc + ab.length * t
        acc += ab.length
    _d, q, axis = best
    r = p - q
    r -= axis * r.dot(axis)
    x0 = (ref - axis * ref.dot(axis)).normalized()
    y0 = axis.cross(x0)
    th = math.atan2(r.dot(y0), r.dot(x0))
    return th * radius / tile, along_best / tile, 2 * math.pi * radius / tile


def uv_garment(ob, kind):
    """Knit / twill UVs in metres over the tile size: the torso round the body's vertical axis, the arms
    and legs round their bones. Faces across the wrap seam are unwrapped (no smeared seam face)."""
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uvl = me.uv_layers[0].data
    tile = KNIT_TILE if kind == "guernsey" else TWILL_TILE
    chains = {}
    for side in ("L", "R"):
        ua, ut = joint(f"upper_arm.{side}")
        fa, ft = joint(f"forearm.{side}")
        th, tt = joint(f"thigh.{side}")
        sh, st = joint(f"shin.{side}")
        chains["arm" + side] = [(ua, ut), (fa, ft)]
        chains["leg" + side] = [(th, tt), (sh, st)]
    crotch = 0.86 * S
    for p in me.polygons:
        c = p.center
        side = "L" if c.x > 0 else "R"
        if kind == "guernsey" and _is_arm(c):
            how = ("arm" + side, 0.05)
        elif kind == "trousers" and c.z < crotch:
            how = ("leg" + side, 0.065)
        else:
            how = None
        uvs = []
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if how:
                u, v, per = _chain_uv(co, chains[how[0]], tile, how[1], Vector((0, -1, 0)))
            else:
                th = math.atan2(co.x, -co.y)
                u, v, per = th * 0.16 / tile, co.z / tile, 2 * math.pi * 0.16 / tile
            uvs.append([u, v])
        us = [u for u, _ in uvs]
        if max(us) - min(us) > per / 2:
            for q in uvs:
                if q[0] < (max(us) + min(us)) / 2:
                    q[0] += per
        for li, q in zip(p.loop_indices, uvs):
            uvl[li].uv = q


def build_garments(body, mats):
    """Guernsey and trousers as their own meshes; the body keeps skin (neck, head, hands) and the boots."""
    me = body.data
    names = [m.name for m in me.materials]
    parts = {"guernsey": [], "trousers": [], "skin": [], "boots": []}
    for p in me.polygons:
        for k in part_of(p.center, names[p.material_index] if names else ""):
            parts[k].append(p.index)
    g = garment(body, parts["guernsey"], "SK_guernsey", lambda co, n: guernsey_offset(co), garment_cuts("guernsey"))
    t = garment(body, parts["trousers"], "SK_trousers", trousers_offset, garment_cuts("trousers"))
    trouser_hem(t.data)
    for ob, kind, mat in ((g, "guernsey", mats[0]), (t, "trousers", mats[1])):
        turn_in(ob, 0.009 if kind == "guernsey" else 0.010)
        uv_garment(ob, kind)
        ob.data.materials.clear()
        ob.data.materials.append(mat)
        for p in ob.data.polygons:
            p.material_index = 0
            p.use_smooth = True
    # the body itself: skin and boots only (what the garments cover goes)
    keep = set(parts["skin"]) | set(parts["boots"])
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(me)
    bm.free()
    cut(me, skin_cuts())
    return g, t


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
    uvl = bm.loops.layers.uv.new("UVMap")
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
    def quad(k, i, v0, v1):
        # Stage P: real UVs, u round the boot (0.3 m of leather a unit), v along the loft
        f = bm.faces.new((rings[k][i], rings[k][(i + 1) % seg], rings[k + 1][(i + 1) % seg], rings[k + 1][i]))
        for lp, (uu, vv) in zip(f.loops, ((i, v0), (i + 1, v0), (i + 1, v1), (i, v1))):
            lp[uvl].uv = (uu / seg, vv)
    for k in range(len(prof) - 1):
        for i in range(seg):
            quad(k, i, prof[k][0] / 0.3, prof[k + 1][0] / 0.3)
    for k in range(len(prof), len(rings) - 1):
        for i in range(seg):
            quad(k, i, 1.0 + k * 0.15, 1.15 + k * 0.15)
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

    def sit_at(s):
        """Standing (s 0) to seated (s 1). The chair seat is 0.46 m high (build.py); the hip joint ends over its
        centre at about 0.55 m. Audit Stage P (C11): the game drives this by the camera's blend, so the body
        lowers under the eye instead of waiting on the chair; the trunk leans forward as it goes down (a real
        sit), most at the middle, and ends at the held G3c sit pose exactly."""
        e = s * s * (3 - 2 * s)
        drop = 0.92 * S - 0.55
        set_loc(arm_ob, "hips", (0, 0.0, -drop * e))
        for side in ("L", "R"):
            leg(arm_ob, side, 88.0 * e, 92.0 * e, 0.0)
        # +X tips the upright spine forward (-Y); the held sit keeps the G3c -6 (a slight settle back)
        set_rot(arm_ob, "spine", X, -6.0 * e + 16.0 * math.sin(math.pi * s))
        arms_down(arm_ob, 30.0 * e, 30.0 * e)

    make_action(arm_ob, "idle", list(range(1, 92, 6)), idle)
    make_action(arm_ob, "walk", list(range(1, WALK_FRAMES + 2)), walk)
    make_action(arm_ob, "sit", [1, 2], lambda f: sit_at(1.0))
    # SITDOWN_KEYS keys, one per tenth of the blend: the game seeks s * length (player_body.gd)
    make_action(arm_ob, "sitdown", list(range(1, SITDOWN_KEYS + 1)), lambda f: sit_at((f - 1) / (SITDOWN_KEYS - 1)))
    rest(arm_ob)
    for tr in arm_ob.animation_data.nla_tracks:
        tr.mute = True                                     # saved and validated at rest; the export writes each action


CHECK_POSES = [("idle", 1), ("walk", 1), ("walk", 8), ("walk", 15), ("walk", 22),
               ("sitdown", 1), ("sitdown", 6), ("sitdown", 11), ("sit", 1)]


def check(arm_ob, body, gu, tr, out_path):
    """Poke-through, posed (audit Stage P): in each pose, how far (m) the trousers' waistband comes out through
    the guernsey's welt, and the boot shafts out through the trouser hems: a ray from each inner point into the
    body along its own normal; the outer garment met within 3 cm means the inner layer is through it by that
    much. (A nearest-point sign test gave false 17 mm hits on the turned-in hem rim.) Also: the share of
    garment faces whose normal points away from the body (the rims must not flip a shell inside out)."""
    from mathutils.bvhtree import BVHTree
    sc = bpy.context.scene
    boots_i = [i for i, m in enumerate(body.data.materials) if m.name == "M_LL_Boots"]
    boot_v = sorted({v for p in body.data.polygons if p.material_index in boots_i for v in p.vertices
                     if body.data.vertices[v].co.z > 0.185 * S})
    # the waistband under the welt, not its own turned-in top edge (rim normals face sideways: a ray "into the
    # body" from them runs out through the welt, a false hit; that edge is inside the guernsey anyway)
    band_v = [v.index for v in tr.data.vertices if HEM_Z + 0.01 <= v.co.z <= WAIST_Z - 0.005]

    legs = {sd: [joint(f"thigh.{sd}"), joint(f"shin.{sd}")] for sd in ("L", "R")}

    def outward(ob):
        """Faces facing away from the axis they wrap (the leg bones below the crotch, else the body's
        vertical axis); arms are judged by the renders."""
        me = ob.data
        good = 0
        for p in me.polygons:
            c = p.center
            if _is_arm(c):
                good += 1
                continue
            if c.z < 0.86 * S:
                a, b = min(legs["L" if c.x > 0 else "R"], key=lambda ab: _seg_dist(c, *ab))
                ab = b - a
                t = max(0.0, min(1.0, (c - a).dot(ab) / ab.length_squared))
                radial = c - (a + ab * t)
            else:
                radial = Vector((c.x, c.y, 0.0))
            if radial.length < 1e-4 or p.normal.dot(radial.normalized()) > -0.2:
                good += 1
        return round(good / max(1, len(me.polygons)), 4)

    rep = {"outward_share": {"guernsey": outward(gu), "trousers": outward(tr)}, "poses": {}}
    for act, frame in CHECK_POSES:
        arm_ob.animation_data.action = bpy.data.actions[act]
        sc.frame_set(frame)
        dg = bpy.context.evaluated_depsgraph_get()

        def posed(ob):
            m = ob.evaluated_get(dg).to_mesh()
            r3 = ob.matrix_world.to_3x3()
            vs = [ob.matrix_world @ v.co for v in m.vertices]
            ns = [(r3 @ v.normal).normalized() for v in m.vertices]
            ps = [list(p.vertices) for p in m.polygons]
            ob.evaluated_get(dg).to_mesh_clear()
            return vs, ns, ps
        gv, _gn, gp = posed(gu)
        tv, tn, tp = posed(tr)
        bv, bn, _bp = posed(body)
        res = {}
        for label, idx, (pv, pn), (ov, op) in (("waistband_through_welt", band_v, (tv, tn), (gv, gp)),
                                               ("boot_through_hem", boot_v, (bv, bn), (tv, tp))):
            # inner layer point -> along its own normal INTO the body: meeting the outer garment there means
            # the inner layer is through it by that distance (an open garment has no inside to test against)
            bvh = BVHTree.FromPolygons(ov, op)
            worst, n_over, at = 0.0, 0, None
            for i in idx:
                hit = bvh.ray_cast(pv[i] - pn[i] * 0.0002, -pn[i], 0.03)
                if hit[0] is not None:
                    d = hit[3] + 0.0002
                    if d > worst:
                        worst, at = d, i
                    n_over += d > 0.002
            res[label] = {"max_mm": round(worst * 1000, 2), "over_2mm": n_over, "points": len(idx)}
            if at is not None and worst > 0.002:
                src = tr if label.startswith("waist") else body
                gi = {g.index: g.name for g in src.vertex_groups}
                ws = sorted(((g.weight, gi[g.group]) for g in src.data.vertices[at].groups), reverse=True)[:3]
                res[label]["worst_at_rest"] = [round(c, 3) for c in src.data.vertices[at].co]
                res[label]["worst_weights"] = [[n, round(w, 2)] for w, n in ws]
        rep["poses"][f"{act}{frame}"] = res
    arm_ob.animation_data.action = None
    rest(arm_ob)
    worst = max(r[k]["max_mm"] for r in rep["poses"].values() for k in r)
    rep["worst_mm"] = worst
    rep["pass"] = worst < 2.0 and min(rep["outward_share"].values()) > 0.97
    with open(out_path, "w") as f:
        json.dump(rep, f, indent=1)
    print("BODY_CHECK", json.dumps({"worst_mm": worst, "outward": rep["outward_share"], "pass": rep["pass"]}))


def main():
    a = args()
    if a["new"]:
        clear_scene()
    bpy.context.scene.render.fps = FPS
    coll = get_collection("ASSET_body")
    mats = [tex_material("M_LL_Guernsey", "T_LL_Knit_albedo.png", "T_LL_Knit_normal.png", "T_LL_Knit_rough.png", 0.9, 0.6),
            tex_material("M_LL_Trousers", "T_LL_Twill_albedo.png", "T_LL_Twill_normal.png", None, 0.88, 0.3),
            material("M_LL_Boots", BOOTS, 0.55), material("M_LL_Skin", SKIN, 0.52, 0.15)]
    body = source_body(coll)
    arm_ob = build_armature(coll)
    for m in mats:
        body.data.materials.append(m)
    for p in body.data.polygons:
        p.material_index = 3                               # skin until the garments take their faces
    drop_feet(body)
    merge_into(body, [boot(f"boot_{s}", s, coll, mats[2]) for s in ("L", "R")])
    weights(body, arm_ob)
    garments = build_garments(body, mats)
    bake_actions(arm_ob)
    if a["check"]:
        check(arm_ob, body, *garments, a["check"])
    merge_into(body, list(garments))
    shadow = split_shadow(body, coll)
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
    shots = [("idle", 1, "front"), ("idle", 1, "side"), ("walk", 1, "side"), ("walk", 8, "side"), ("sit", 1, "side"),
             ("sitdown", 4, "side"), ("sitdown", 6, "side"), ("sitdown", 8, "side"), ("idle", 1, "back"),
             ("idle", 1, "q34"), ("idle", 1, "down"), ("walk", 8, "down")]
    for act, frame, view in shots:
        arm_ob.animation_data.action = bpy.data.actions[act]
        sc.frame_set(frame)
        cam.data.type = "ORTHO"
        if view == "down":
            # Stage P: as the keeper sees himself (player_body.gd: pitch -1.2, the body 0.28 m behind the eye)
            cam.data.type = "PERSP"
            cam.data.sensor_fit = "VERTICAL"
            cam.data.angle = math.radians(70.0)
            cam.location = (0, -0.28 - 0.04 * S, 1.65)
            cam.rotation_euler = (math.radians(90 - 69), 0, math.radians(180))
        elif view == "q34":
            cam.data.type = "PERSP"
            cam.data.lens = 50
            cam.location = (-1.6, -2.2, 1.35)
            cam.rotation_euler = (math.radians(84), 0, math.radians(-36))
        elif view in ("front", "back"):
            cam.location = (0, -4 if view == "front" else 4, 0.95)
            cam.rotation_euler = (math.radians(90), 0, 0 if view == "front" else math.radians(180))
        else:
            cam.location = (4, 0, 0.95)
            cam.rotation_euler = (math.radians(90), 0, math.radians(90))
        sc.render.filepath = f"{outdir}/body_{act}{frame}_{view}.png"
        bpy.ops.render.render(write_still=True)
    arm_ob.animation_data.action = None
    rest(arm_ob)


if __name__ == "__main__":
    main()
