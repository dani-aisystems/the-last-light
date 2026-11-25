"""Character portraits for THE LAST LIGHT (Stage 3C): colour busts, 1971 studio-print look.

  tools/bl -P projects/games/last_light/blender/portraits.py -- [--only morag,rory] [--expr neutral]
        [--samples 96] [--res 512x640] [--out DIR]

No AI imagery (CLAUDE.md): every face is Blender Studio's CC0 Human Base Meshes (assets/models/
human_base_meshes, licence in assets/ASSET_LICENSES.md), shaped procedurally per character from the
character references (character-refs/<id>/PROFILE.md §G): face proportions, age, skin, hair, beard or stubble,
clothing and headwear. Expressions are restrained offsets of the same face (brows, lids, mouth corners,
cheeks), so a character's identity holds across them. One studio rig, one 85 mm camera height and framing
for everyone. Writes the raw renders to blender/tex/src/portraits_raw/<id>_<expr>.png; portraits_grade.py
(host Python) gives them the faded 1971 colour-print look in godot/assets/portraits/. Headless only (it
clears the scene).
"""

import argparse
import bisect
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[3]
sys.path.insert(0, str(WS / "scripts"))

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

BUNDLE = WS / "assets/models/human_base_meshes/bundle/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend"
OUT = HERE / "tex" / "src" / "portraits_raw"          # portraits_grade.py turns these into the game's prints

# Landmark heights (metres above the crown, negative = below) measured on the realistic bodies' midline.
LAND = {
    "male": {"chin": -0.222, "mouth": -0.186, "nose": -0.146, "eyes": -0.115, "brow": -0.095, "front": -0.16},
    "female": {"chin": -0.213, "mouth": -0.175, "nose": -0.141, "eyes": -0.106, "brow": -0.09, "front": -0.162},
}

# The characters. Looks follow projects/games/last_light/character-refs/<id>/PROFILE.md §G (the dossiers are
# the visual reference, Daniel 2026-11-06; summary table in character-refs/CANON_INDEX.md §9). Distances in
# metres, factors around 1.0. Kept deliberately restrained: real people in a 1971 photograph, not caricatures.
CHARS = {
    "callum": {   # longish oval towards rectangular, defined cheekbones, firm slightly narrow jaw, grey-blue eyes
        "body": "male", "age": 41, "yaw": -11, "skin": "#B98E76", "rough_skin": 0.5, "iris": "#68767F",
        "face": {"head_w": 0.96, "jaw_w": 0.98, "chin": 0.003, "nose_len": 0.002, "nose_w": 0.95, "cheek": -0.003,
                 "brow": 0.002, "face_len": 1.04, "age_sag": 0.3, "flush": 0.25},
        "hair": {"color": "#4A3628", "grey": 0.3, "style": "short", "volume": 0.004},
        "stubble": 0.18, "beard": None,
        "cloth": [("guernsey", "#1D2330", 0.02), ("shirt_collar", "#D9D2C2", 0.0)], "hat": None, "glasses": False,
        "expr": ["neutral", "guarded", "grief"],
    },
    "morag": {    # oval, slightly narrow, defined chin and cheekbones; dark brown greying hair; grey-green eyes
        "body": "female", "age": 44, "yaw": 12, "skin": "#CAA28C", "rough_skin": 0.46, "iris": "#6A7462",
        "face": {"head_w": 0.97, "jaw_w": 0.96, "chin": 0.002, "nose_len": 0.001, "nose_w": 0.98, "cheek": -0.001,
                 "brow": 0.0, "face_len": 1.01, "age_sag": 0.3, "flush": 0.15},
        "hair": {"color": "#33241B", "grey": 0.22, "style": "set", "volume": 0.006},
        "stubble": 0.0, "beard": None,
        "cloth": [("cardigan", "#1F2A40", 0.014), ("blouse_collar", "#E4DFD3", 0.0)], "hat": None, "glasses": False,
        "expr": ["neutral", "worried", "hurt"],
    },
    "rory": {     # youthful angular oval, strong brows, freckles, curly brown hair under a wool cap, blue-grey eyes
        "body": "male", "age": 22, "yaw": -8, "skin": "#DDB29C", "rough_skin": 0.44, "iris": "#66767F",
        "face": {"head_w": 0.99, "jaw_w": 0.98, "chin": -0.001, "nose_len": -0.001, "nose_w": 1.0, "cheek": 0.001,
                 "brow": 0.002, "face_len": 0.99, "age_sag": 0.0, "flush": 0.5, "freckles": 0.6},
        "hair": {"color": "#4E3322", "grey": 0.0, "style": "curly", "volume": 0.006},
        "stubble": 0.06, "beard": None,
        "cloth": [("gansey", "#283044", 0.02), ("oilskin_jacket", "#B48C34", 0.034)], "hat": "woolcap", "glasses": False,
        "expr": ["neutral", "grin", "scared"],
    },
    "hector": {   # canon only (no reference yet): full white beard, reefer jacket, peaked cap, pipe
        "body": "male", "age": 68, "yaw": 10, "skin": "#CDA08A", "rough_skin": 0.55, "iris": "#66717C",
        "face": {"head_w": 1.03, "jaw_w": 1.04, "chin": 0.0, "nose_len": 0.004, "nose_w": 1.08, "cheek": 0.004,
                 "brow": 0.003, "face_len": 1.0, "age_sag": 0.85, "flush": 0.45},
        "hair": {"color": "#DCD8D0", "grey": 1.0, "style": "short", "volume": 0.003},
        "stubble": 0.0, "beard": {"color": "#E2DED6", "depth": 0.012, "moustache": True},
        "cloth": [("reefer", "#1A2030", 0.022)], "hat": "peaked", "glasses": False, "pipe": True,
        "expr": ["neutral", "warm", "sorry"],
    },
    "elspeth": {  # lean, defined features, dark wavy hair pinned back, grey eyes (her father's)
        "body": "female", "age": 29, "yaw": -12, "skin": "#DAB5A2", "rough_skin": 0.42, "iris": "#858E94",
        "face": {"head_w": 0.96, "jaw_w": 0.95, "chin": 0.002, "nose_len": 0.001, "nose_w": 0.95, "cheek": -0.003,
                 "brow": 0.001, "face_len": 1.03, "age_sag": 0.0, "flush": 0.2},
        "hair": {"color": "#2B1E16", "grey": 0.0, "style": "pinned", "volume": 0.006},
        "stubble": 0.0, "beard": None,
        "cloth": [("reefer", "#151B28", 0.022), ("rollneck", "#202228", 0.0)], "hat": None, "glasses": False,
        "expr": ["neutral", "cold", "moved"],
    },
    "ross": {     # SILHOUETTE ONLY (character-refs F12): tall, stooped, black oilskin, sou'wester, face in shadow
        "body": "male", "age": 64, "yaw": 9, "skin": "#C8A08E", "rough_skin": 0.55, "iris": "#80888C",
        "face": {"head_w": 0.98, "jaw_w": 0.99, "chin": 0.004, "nose_len": 0.003, "nose_w": 0.98, "cheek": -0.006,
                 "brow": 0.004, "face_len": 1.05, "age_sag": 0.7, "pallor": 0.35},
        "hair": {"color": "#CFCBC4", "grey": 1.0, "style": "none", "volume": 0.0},
        "stubble": 0.75, "stubble_color": "#D8D4CC", "beard": None,
        "cloth": [("oilskin", "#0D0E10", 0.024)], "hat": "souwester", "glasses": False, "silhouette": True,
        "expr": ["neutral", "grave", "grief"],
    },
}

# Silhouette variants (Ross): posture and light only, never the face. pitch = head bowed (deg), yaw extra.
SIL_POSE = {"neutral": (0.0, 0.0), "grave": (8.0, -6.0), "grief": (16.0, 4.0)}

# Under a hat the hair stops at HAT_LINE (metres below the crown) so nothing pokes through.
HAT_LINE = -0.052

# Restrained expression offsets (metres). smile: mouth corners up/out, cheeks up; sad: corners down, inner
# brows up; knit: inner brows down and in; squint: lower lids up; open: jaw a little open.
EXPR = {
    "neutral": {},
    "guarded": {"knit": 0.5, "squint": 0.6, "smile": -0.2},
    "grief": {"sad": 1.0, "squint": 0.3, "open": 0.3},
    "worried": {"sad": 0.6, "knit": 0.3, "open": 0.2},
    "hurt": {"sad": 0.9, "smile": -0.3},
    "grin": {"smile": 1.0, "squint": 0.5, "open": 0.4},
    "scared": {"sad": 0.6, "open": 0.7, "brow_up": 0.8},
    "warm": {"smile": 0.7, "squint": 0.6},
    "sorry": {"sad": 0.5, "smile": 0.3},
    "cold": {"knit": 0.3, "squint": 0.4, "smile": -0.4},
    "moved": {"sad": 0.6, "smile": 0.3, "open": 0.2},
    "grave": {"knit": 0.6, "smile": -0.4},
}

MATS = {}


def srgb(hexc):
    return tuple((int(hexc[i:i + 2], 16) / 255) ** 2.2 for i in (1, 3, 5))


def clear():
    if not bpy.app.background:
        raise SystemExit("portraits.py clears the scene: headless only")
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)


def smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def g(p, c, r):
    d = p - c
    return math.exp(-(d.x * d.x + d.y * d.y + d.z * d.z) / (r * r))


# ------------------------------------------------------------------ the base mesh

def load_body(kind):
    """The CC0 realistic body (multires level 2) cut to a bust, centred on x, crown at z = 0, facing -Y.
    Returns (mesh, eye meshes)."""
    name = "GEO-body_%s_realistic" % kind
    want = [name, name + ".eye.L", name + ".eye.R"]
    with bpy.data.libraries.load(str(BUNDLE), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in want]
    objs = {o.name: o for o in dst.objects}
    body = objs[name]
    bpy.context.scene.collection.objects.link(body)
    for m in body.modifiers:
        if m.type == "MULTIRES":
            m.levels = 2
            m.render_levels = 2
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(body.evaluated_get(dg))       # body-local: centred on x, facing -Y
    to_local = body.matrix_world.inverted()
    eye_raw = []
    for side in (".eye.L", ".eye.R"):                                   # read while the parent still exists
        o = objs[name + side]
        e = o.data.copy()
        # appended objects are not in the scene, so matrix_world is not evaluated: the eyes are children
        # of the body, so their body-local transform is parent-inverse @ basis
        e.transform(o.matrix_parent_inverse @ o.matrix_basis if o.parent else to_local @ o.matrix_world)
        eye_raw.append(e)
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.objects.remove(body, do_unlink=True)
    top = max(v.co.z for v in me.vertices)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < top - 0.62], context="VERTS")
    bm.to_mesh(me)
    bm.free()
    me.transform(Matrix.Translation((0, 0, -top)))
    for e in eye_raw:
        e.transform(Matrix.Translation((0, 0, -top)))
    return me, eye_raw


# ------------------------------------------------------------------ identity and expression fields

def face_field(kind, f, ex):
    """Displacement field p -> offset for one character's face and expression."""
    L = LAND[kind]
    fr = L["front"]
    chin, mouth, nose, eyes, brow = L["chin"], L["mouth"], L["nose"], L["eyes"], L["brow"]

    def field(p):
        d = Vector()
        head = smooth(chin - 0.05, chin - 0.01, p.z)            # 0 on the neck/body, 1 on the head
        if head <= 0.0:
            # neck: thicker with age and weight
            nk = smooth(chin - 0.14, chin - 0.06, p.z) * (1 - head)
            d.x += p.x * 0.04 * f.get("age_sag", 0) * nk
            return d
        # whole head width and face length (about the eye line)
        d.x += p.x * (f.get("head_w", 1.0) - 1.0) * head
        face = smooth(fr + 0.13, fr + 0.06, p.y) * head          # front of the head only
        d.z += (p.z - eyes) * (f.get("face_len", 1.0) - 1.0) * face * smooth(eyes + 0.02, eyes - 0.02, p.z)
        # jaw width (at the angles of the jaw) and chin length
        for s in (-1, 1):
            w = g(p, Vector((s * 0.055, fr + 0.07, chin + 0.03)), 0.04)
            d.x += s * 0.06 * (f.get("jaw_w", 1.0) - 1.0) * w
        d += Vector((0, -0.3, -1)).normalized() * f.get("chin", 0) * g(p, Vector((0, fr + 0.012, chin + 0.006)), 0.022)
        # nose: length (forward and a little down) and width
        nt = Vector((0, fr - 0.002, nose))
        d += Vector((0, -1, -0.35)).normalized() * f.get("nose_len", 0) * g(p, nt, 0.022)
        d.x += p.x * (f.get("nose_w", 1.0) - 1.0) * g(p, nt + Vector((0, 0.01, -0.004)), 0.02)
        # cheeks (fullness +, hollow -) and brow ridge
        for s in (-1, 1):
            d += Vector((s * 0.4, -1, 0)).normalized() * f.get("cheek", 0) * g(p, Vector((s * 0.042, fr + 0.035, nose - 0.008)), 0.024)
            d.y -= f.get("brow", 0) * g(p, Vector((s * 0.03, fr + 0.014, brow)), 0.02)
        # age: jowls and jaw line sag, nasolabial fold, eye bags
        a = f.get("age_sag", 0)
        if a:
            for s in (-1, 1):
                d.z -= 0.007 * a * g(p, Vector((s * 0.048, fr + 0.04, chin + 0.018)), 0.026)
                d += Vector((s, -0.6, 0)).normalized() * 0.003 * a * g(p, Vector((s * 0.05, fr + 0.045, chin + 0.012)), 0.02)
                d.y += 0.0025 * a * g(p, Vector((s * 0.024, fr + 0.016, mouth + 0.014)), 0.009)
                d += Vector((0, -0.6, -1)).normalized() * 0.0022 * a * g(p, Vector((s * 0.031, fr + 0.025, eyes - 0.014)), 0.011)
        # expression
        for s in (-1, 1):
            corner = Vector((s * 0.023, fr + 0.02, mouth))
            sm = ex.get("smile", 0)
            d += Vector((s * 0.5, 0.4, 1)).normalized() * 0.0035 * sm * g(p, corner, 0.012)
            d.z += 0.002 * max(sm, 0) * g(p, Vector((s * 0.04, fr + 0.03, nose - 0.01)), 0.02)
            sd = ex.get("sad", 0)
            d.z -= 0.0025 * sd * g(p, corner, 0.011)
            inner = Vector((s * 0.013, fr + 0.012, brow + 0.002))
            d.z += 0.0035 * sd * g(p, inner, 0.011)
            kn = ex.get("knit", 0)
            d += Vector((-s * 0.6, -0.2, -1)).normalized() * 0.003 * kn * g(p, inner, 0.012)
            bu = ex.get("brow_up", 0)
            d.z += 0.004 * bu * g(p, Vector((s * 0.028, fr + 0.014, brow + 0.004)), 0.02)
            sq = ex.get("squint", 0)
            d.z += 0.0018 * sq * g(p, Vector((s * 0.031, fr + 0.02, eyes - 0.007)), 0.008)
        d.z -= 0.005 * ex.get("open", 0) * g(p, Vector((0, fr + 0.02, chin + 0.008)), 0.03) * smooth(mouth, mouth - 0.008, p.z)
        return d
    return field


# ------------------------------------------------------------------ materials

def principled(name, hexc, rough, sss=0.0, metal=0.0, sheen=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*srgb(hexc), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
        b.inputs["Subsurface Scale"].default_value = 0.012
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    return m


def bump(m, scale, strength, detail=8.0, stretch=None):
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = detail
    src = tex
    if stretch:
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = stretch
        co = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(co.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = strength
    nt.links.new(src.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def skin_mat(c):
    """Skin with subsurface, pores, an age-dependent blotch, and a stubble mask (vertex attribute 'stubble')."""
    m = principled("M_skin_" + c["id"], c["skin"], c["rough_skin"], sss=0.3)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.22)
    b.inputs["Subsurface Scale"].default_value = 0.006
    b.inputs["Specular IOR Level"].default_value = 0.38          # less plastic sheen
    base = Vector(srgb(c["skin"]))
    f = c["face"]
    flush = f.get("flush", 0.0)
    pallor = f.get("pallor", 0.0)
    # blotches: subtle colour variation (more with age)
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 45.0
    n.inputs["Detail"].default_value = 5.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    lo = base * (0.88 - 0.04 * pallor - 0.0015 * c["age"])
    hi = Vector((min(1, base.x * 1.04), base.y * 1.0, base.z * 0.98))
    ramp.color_ramp.elements[0].color = (*lo, 1)
    ramp.color_ramp.elements[1].color = (*hi, 1)
    nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
    # wind flush on cheeks and nose (vertex attribute 'flush'), then freckles in the same region
    fa = nt.nodes.new("ShaderNodeAttribute")
    fa.attribute_name = "flush"
    fm = nt.nodes.new("ShaderNodeMath")
    fm.operation = "MULTIPLY"
    fm.inputs[1].default_value = 0.25 + 0.6 * flush
    nt.links.new(fa.outputs["Fac"], fm.inputs[0])
    fmix = nt.nodes.new("ShaderNodeMix")
    fmix.data_type = "RGBA"
    nt.links.new(fm.outputs[0], fmix.inputs["Factor"])
    nt.links.new(ramp.outputs["Color"], fmix.inputs["A"])
    fmix.inputs["B"].default_value = (base.x * 1.02, base.y * 0.62, base.z * 0.58, 1)
    col_out = fmix.outputs["Result"]
    if f.get("freckles"):
        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = 520.0
        vor.inputs["Randomness"].default_value = 1.0
        thr = nt.nodes.new("ShaderNodeMath")
        thr.operation = "LESS_THAN"
        thr.inputs[1].default_value = 0.22
        nt.links.new(vor.outputs["Distance"], thr.inputs[0])
        fr2 = nt.nodes.new("ShaderNodeMath")
        fr2.operation = "MULTIPLY"
        nt.links.new(thr.outputs[0], fr2.inputs[0])
        fr3 = nt.nodes.new("ShaderNodeMath")
        fr3.operation = "MULTIPLY"
        fr3.inputs[1].default_value = 0.55 * f["freckles"]
        nt.links.new(fa.outputs["Fac"], fr3.inputs[0])
        nt.links.new(fr3.outputs[0], fr2.inputs[1])
        frk = nt.nodes.new("ShaderNodeMix")
        frk.data_type = "RGBA"
        nt.links.new(fr2.outputs[0], frk.inputs["Factor"])
        nt.links.new(col_out, frk.inputs["A"])
        frk.inputs["B"].default_value = (base.x * 0.62, base.y * 0.42, base.z * 0.3, 1)
        col_out = frk.outputs["Result"]
    # roughness varies a little (oilier T-zone reads as less plastic than a flat value)
    rn = nt.nodes.new("ShaderNodeTexNoise")
    rn.inputs["Scale"].default_value = 30.0
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = c["rough_skin"] - 0.08
    rr.inputs["To Max"].default_value = c["rough_skin"] + 0.08
    nt.links.new(rn.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    stub_col = Vector(srgb(c.get("stubble_color", "#2A2420")))
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "stubble"
    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 900.0
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    nt.links.new(attr.outputs["Fac"], mul.inputs[0])
    nt.links.new(grain.outputs["Fac"], mul.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(mul.outputs[0], mix.inputs["Factor"])
    nt.links.new(col_out, mix.inputs["A"])
    mix.inputs["B"].default_value = (*stub_col, 1)
    lipa = nt.nodes.new("ShaderNodeAttribute")
    lipa.attribute_name = "lips"
    lmix = nt.nodes.new("ShaderNodeMix")
    lmix.data_type = "RGBA"
    nt.links.new(lipa.outputs["Fac"], lmix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], lmix.inputs["A"])
    lip_col = Vector((base.x * 0.82, base.y * 0.55, base.z * 0.55)) if c["body"] == "female" else Vector((base.x * 0.86, base.y * 0.66, base.z * 0.64))
    lmix.inputs["B"].default_value = (*lip_col, 1)
    la = nt.nodes.new("ShaderNodeAttribute")               # lash line: the dark upper-lid margin
    la.attribute_name = "lash"
    lam = nt.nodes.new("ShaderNodeMix")
    lam.data_type = "RGBA"
    nt.links.new(la.outputs["Fac"], lam.inputs["Factor"])
    nt.links.new(lmix.outputs["Result"], lam.inputs["A"])
    lam.inputs["B"].default_value = (0.02, 0.014, 0.01, 1)
    nt.links.new(lam.outputs["Result"], b.inputs["Base Color"])
    bump(m, 400.0, 0.12 + 0.002 * c["age"], detail=6.0)
    return m


def eye_material(cid, iris_hex):
    """Sclera with an iris and pupil on the -Y (front) pole, from the generated coordinates."""
    m = principled("M_eye_" + cid, "#D9D0C4", 0.05)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    co = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(co.outputs["Generated"], sep.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")         # generated Y: 0 at the front pole
    els = ramp.color_ramp.elements
    els[0].position = 0.0
    els[0].color = (0.01, 0.01, 0.01, 1)
    els[1].position = 0.16
    els[1].color = (*srgb("#D9D0C4"), 1)
    e = els.new(0.05)
    e.color = (*srgb(iris_hex), 1)
    e2 = els.new(0.13)
    e2.color = (*[x * 0.7 for x in srgb(iris_hex)], 1)
    ramp.color_ramp.interpolation = "CONSTANT"
    nt.links.new(sep.outputs["Y"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


def hair_mat(c, hexc=None, rough=0.42):
    h = c["hair"]
    col = Vector(srgb(hexc or h["color"]))
    grey = Vector(srgb("#B8B4AE"))
    col = col.lerp(grey, h.get("grey", 0) * 0.6)
    m = principled("M_hair_" + c["id"], "#000000", max(rough, 0.6))
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Specular IOR Level"].default_value = 0.25     # fine bumped strands threw grey highlights
    return bump(m, 140.0, 0.22, detail=6.0, stretch=(1.0, 1.0, 9.0))


# ------------------------------------------------------------------ hair, beard, clothing shells

def shell(src, name, sel, offset, mat, noise=0.0, seed=1, snap=None):
    """A copy of the faces whose vertices all satisfy sel(p), pushed out along the normal and solidified.
    snap(co) may move boundary vertices (a clean straight neckline instead of a stair-stepped one)."""
    bm = bmesh.new()
    bm.from_mesh(src)
    keep = {v for v in bm.verts if sel(v.co)}
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not all(v in keep for v in f.verts)], context="FACES_ONLY")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    if snap:
        for v in bm.verts:
            if v.is_boundary:
                snap(v.co)
    bm.normal_update()
    rnd = random.Random(seed)
    for v in bm.verts:
        o = offset(v.co) if callable(offset) else offset
        v.co += v.normal * (o + (rnd.uniform(-1, 1) * noise if noise else 0.0))
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    so = ob.modifiers.new("solid", "SOLIDIFY")
    so.thickness = 0.003
    so.offset = -1
    ob.modifiers.new("sub", "SUBSURF").render_levels = 1
    return ob


def strand_mat(c, melanin, redness, grey=0.0, name="scalp"):
    """Principled Hair BSDF (melanin model: physically plausible natural hair), with a per-strand share of
    grey hairs (low melanin)."""
    m = bpy.data.materials.new("M_%s_%s" % (name, c["id"]))
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")

    def hbsdf(mel, red):
        n = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
        n.parametrization = "MELANIN"
        for k, v in (("Melanin", mel), ("Melanin Redness", red), ("Roughness", 0.3), ("Radial Roughness", 0.35),
                     ("Coat", 0.05), ("Random Color", 0.15), ("Random Roughness", 0.12)):
            if k in n.inputs:                      # some inputs exist only for some parametrisations
                n.inputs[k].default_value = v
        return n
    dark = hbsdf(melanin, redness)
    if grey <= 0.0:
        nt.links.new(dark.outputs[0], out.inputs["Surface"])
        return m
    light = hbsdf(0.12, 0.15)
    info = nt.nodes.new("ShaderNodeHairInfo")
    lt = nt.nodes.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    lt.inputs[1].default_value = grey
    nt.links.new(info.outputs["Random"], lt.inputs[0])
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lt.outputs[0], mix.inputs["Fac"])
    nt.links.new(dark.outputs[0], mix.inputs[1])
    nt.links.new(light.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def grow_curves(name, me, bvh, weight, n, length, comb, mat, seed, seg=8, lift=0.0, gravity=0.0, kink=None,
                r_root=0.00006, r_tip=0.00002, jitter=0.25, min_off=0.0011, per_guide=1, spread=0.004, clump=0.6, hug=0.003,
                lift_at=lambda p: 1.0):
    """Hair curves grown from the mesh where weight(p) > 0. Each strand starts on the surface, heads along
    comb(p) projected onto the surface, bends with gravity, and is kept min_off..lift above the surface (so it
    lies along the scalp's curvature instead of sticking out). kink = ('curl'|'wave', amplitude, turns)."""
    verts = [v.co.copy() for v in me.vertices]
    cand, cum, tot = [], [], 0.0
    for p in me.polygons:
        w = sum(weight(verts[i]) for i in p.vertices) / len(p.vertices)
        if w > 0.02:
            tot += p.area * w
            cand.append(p)
            cum.append(tot)
    if not cand:
        return None
    rnd = random.Random(seed)
    pts_all = []
    for _ in range(max(1, n // per_guide)):
        f = cand[min(len(cand) - 1, bisect.bisect(cum, rnd.random() * tot))]
        vs = [verts[i] for i in f.vertices]
        t = rnd.randrange(len(vs) - 2)
        a, b, c3 = vs[0], vs[t + 1], vs[t + 2]
        u, v = rnd.random(), rnd.random()
        if u + v > 1:
            u, v = 1 - u, 1 - v
        root = a + (b - a) * u + (c3 - a) * v
        nrm = f.normal.copy()
        d = Vector(comb(root)) + Vector((rnd.gauss(0, jitter), rnd.gauss(0, jitter), rnd.gauss(0, jitter)))
        dirv = (d - nrm * d.dot(nrm))
        dirv = dirv.normalized() if dirv.length > 1e-6 else nrm.orthogonal().normalized()
        L = length * (0.7 + 0.6 * rnd.random())
        step = L / seg
        p = root - nrm * 0.0006
        pts = [p.copy()]
        n2 = nrm
        for s in range(seg):
            dirv = (dirv + Vector((0, 0, -gravity))).normalized()
            p = p + dirv * step
            hit = bvh.find_nearest(p)
            if hit[0] is not None:
                loc, n2 = hit[0], hit[1]
                want = min_off + lift * (s + 1) / seg * lift_at(root)
                h = (p - loc).dot(n2)
                if h < want:                       # never into the head ...
                    p = p + n2 * (want - h)
                elif h > want + hug:               # ... and never flying off it: hug the curvature
                    p = p - n2 * (h - want - hug)
                dirv = dirv - n2 * min(0.0, dirv.dot(n2))     # never steer back into the head
                dirv.normalize()
            pts.append(p.copy())
        if kink:
            kind, amp, turns = kink
            ph = rnd.random() * 6.283
            side = dirv.cross(n2).normalized()
            for s in range(1, len(pts)):
                k = s / seg
                a1 = ph + turns * 6.283 * k
                w = amp * min(1.0, 3 * k)
                if kind == "curl":
                    pts[s] = pts[s] + side * (math.cos(a1) * w) + n2 * (abs(math.sin(a1)) * w)
                else:
                    pts[s] = pts[s] + side * (math.sin(a1) * w)
        pts_all.append(pts)
    if per_guide > 1:                              # clumped children around each grown guide strand
        guides, pts_all = pts_all, []
        for gp in guides:
            pts_all.append(gp)
            t0 = (gp[1] - gp[0]).normalized()
            for _ in range(per_guide - 1):
                off = Vector((rnd.gauss(0, spread), rnd.gauss(0, spread), rnd.gauss(0, spread)))
                off -= t0 * off.dot(t0)
                hit = bvh.find_nearest(gp[0] + off)
                if hit[0] is None:
                    continue
                d0 = hit[0] - hit[1] * 0.0006 - gp[0]
                lmul = 0.8 + 0.35 * rnd.random()
                ch = []
                for k, q in enumerate(gp):
                    f = k / seg
                    w = (1 - clump * f ** 0.7)
                    base = gp[0] + (q - gp[0]) * lmul
                    ch.append(base + d0 * w + Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))) * 0.00025 * f)
                pts_all.append(ch)
    cv = bpy.data.hair_curves.new(name)
    npts = seg + 1
    cv.add_curves([npts] * len(pts_all))
    cv.position_data.foreach_set("vector", [x for pts in pts_all for p in pts for x in p])
    rad = cv.attributes.new("radius", "FLOAT", "POINT")
    rad.data.foreach_set("value", [r_root + (r_tip - r_root) * (k / seg) for _ in pts_all for k in range(npts)])
    cv.materials.append(mat)
    ob = bpy.data.objects.new(name, cv)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# style: strands, length, comb(p, side), lift (volume), gravity, kink
HAIR_LOOK = {
    "callum": dict(melanin=0.86, redness=0.3),
    "morag": dict(melanin=0.86, redness=0.28),
    "rory": dict(melanin=0.66, redness=0.42),
    "hector": dict(melanin=0.1, redness=0.1),
    "elspeth": dict(melanin=0.9, redness=0.25),
}


def hair(c, head, me, L, bvh):
    h = c["hair"]
    style = h["style"]
    if style == "none":
        return []
    fr = L["front"]
    brow = L["brow"]
    hatted = bool(c.get("hat"))
    hairline = brow + (0.032 if style not in ("set", "pinned") else 0.028)
    inset = 0.0

    def sel(p):
        if p.z < L["chin"] + 0.01:
            return False
        if p.y < fr + 0.09:                        # face and forehead: above a curved hairline only
            return p.z > hl(p) - inset
        side = abs(p.x) > 0.062 and p.y < fr + 0.13
        if side:                                   # temples and above the ears
            return p.z > L["eyes"] + (-0.004 if style in ("short", "curly") else -0.01) - inset
        nape = {"short": L["mouth"] + 0.01, "curly": L["mouth"] - 0.004, "set": L["mouth"] - 0.012,
                "pinned": L["mouth"] + 0.0}[style]
        return p.z > nape - inset

    def hl(p):                                     # hairline height: higher at the temples, a soft widow's arc
        return hairline + 0.016 * (abs(p.x) / 0.06) ** 2 + (0.006 if c["age"] > 35 and c["body"] == "male" else 0.0) * smooth(0.02, 0.05, abs(p.x))

    def edge(p):                                   # thin out at the hairline and the nape
        front = smooth(hl(p) - 0.003, hl(p) + 0.012, p.z) if p.y < fr + 0.09 else 1.0
        return front * smooth(L["mouth"] - 0.02, L["eyes"] + 0.01, p.z)

    bun_c = Vector((0.0, 0.075, -0.08))

    def bun(p):                                    # pinned: a low bun at the back
        return 0.024 * math.exp(-((p.y - bun_c.y) ** 2 + (p.z - bun_c.z) ** 2 + p.x ** 2) / 0.0009) if style == "pinned" else 0.0
    look = HAIR_LOOK[c["id"]]
    # base layer: a thin, dark, matte hair-coloured shell so the scalp never shows between the strands
    dark = "#%02X%02X%02X" % tuple(int(int(h["color"][i:i + 2], 16) * 0.55) for i in (1, 3, 5))
    inset = -0.004                                 # the base layer stops 4 mm inside the strands' edge
    base = shell(me, "hairbase_" + c["id"], sel, lambda p: 0.0008 + bun(p), principled("M_hairbase_" + c["id"], dark, 0.95),
                 noise=0.0002, seed=7)
    base.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.1

    inset_strands = 0.0

    def weight(p):
        nonlocal inset
        inset = inset_strands
        if not sel(p):
            return 0.0
        if hatted and p.z > HAT_LINE + 0.012:      # under a hat: only the hair that shows below the brim
            return 0.0
        return max(0.05, edge(p))

    sgn = lambda p: 1.0 if p.x >= 0 else -1.0      # noqa: E731
    if style == "short":                           # short back and sides, combed back with a side parting
        comb = lambda p: (0.45 * sgn(p), 1.0, 0.1 if p.z > -0.05 else -0.9)   # noqa: E731
        cfg = dict(n=42000, length=0.03, lift=0.005, gravity=0.0, kink=("wave", 0.0008, 1.0), per_guide=8, clump=0.45)
    elif style == "curly":
        comb = lambda p: (0.4 * sgn(p), 0.3, -1.0)  # noqa: E731
        cfg = dict(n=24000, length=0.036, lift=0.007, gravity=0.05, kink=("curl", 0.004, 2.5), per_guide=10, clump=0.7)
    elif style == "set":                           # a 1971 set: soft waves back from the face, full at the sides
        comb = lambda p: (0.7 * sgn(p), 0.9, -0.35)  # noqa: E731
        cfg = dict(n=56000, length=0.07, lift=0.012, gravity=0.03, kink=("wave", 0.003, 1.6), per_guide=14, clump=0.65)
    else:                                          # pinned: everything drawn back towards the bun
        comb = lambda p: tuple((bun_c - p).normalized())  # noqa: E731
        cfg = dict(n=50000, length=0.095, lift=0.003, gravity=0.0, kink=("wave", 0.0012, 2.5), per_guide=12, clump=0.6)
    if hatted:
        comb = lambda p: (0.5 * sgn(p), 0.25, -1.0)  # noqa: E731
    mat = strand_mat(c, look["melanin"], look["redness"], h.get("grey", 0.0))
    lift_at = lambda p: smooth(hl(p), hl(p) + 0.03, p.z) if p.y < fr + 0.09 else 1.0  # noqa: E731
    ob = grow_curves("hair_" + c["id"], me, bvh, weight, cfg["n"], cfg["length"] * (0.7 if hatted else 1.0), comb, mat,
                     lift_at=lift_at,
                     seed=11, lift=cfg["lift"], gravity=cfg["gravity"], kink=cfg["kink"], per_guide=cfg["per_guide"],
                     clump=cfg["clump"])
    return [base] + ([ob] if ob else [])


def brows(c, me, L, bvh):
    """Eyebrows: short strands over each brow ridge, combed outwards and a little up (heavier with age)."""
    fr = L["front"]
    heavy = 1.0 + 0.5 * (c["age"] > 60)

    def sel(p):
        ax = abs(p.x)
        if not (0.008 < ax < 0.05) or p.y > fr + 0.035:
            return False
        arch = L["brow"] + 0.003 - 18.0 * (ax - 0.03) ** 2
        return abs(p.z - arch) < 0.0042 * heavy * (1 - 0.45 * smooth(0.03, 0.05, ax))
    look = HAIR_LOOK.get(c["id"], dict(melanin=0.5, redness=0.2))
    mel = 0.2 if c["age"] > 60 else look["melanin"] * 0.95
    mat = strand_mat(c, mel, look["redness"], 0.0, name="brows")
    comb = lambda p: ((1.0 if p.x >= 0 else -1.0), 0.0, 0.35 if abs(p.x) < 0.025 else 0.0)  # noqa: E731
    return grow_curves("brows_" + c["id"], me, bvh, lambda p: 1.0 if sel(p) else 0.0, int(1400 * heavy), 0.009, comb,
                       mat, seed=5, seg=4, lift=0.0006, jitter=0.15, r_root=0.00005, min_off=0.0004)


def beard(c, head, me, L, bvh):
    """A thin beard base plus strands combed down (moustache down and out)."""
    b = c["beard"]
    fr = L["front"]

    def sel2(p):
        if p.y > fr + 0.11 or p.z > L["nose"] - 0.006:
            return False
        if abs(p.x) < 0.02 and L["mouth"] - 0.006 < p.z < L["mouth"] + 0.004 and p.y < fr + 0.03:
            return False
        if b.get("moustache") and L["mouth"] + 0.004 <= p.z and abs(p.x) < 0.03:
            return True
        return L["chin"] - 0.035 < p.z < L["mouth"] + 0.004
    mat = strand_mat(c, 0.08, 0.1, 0.0, name="beard")
    comb = lambda p: (0.5 * (1.0 if p.x >= 0 else -1.0) if p.z > L["mouth"] else 0.0, -0.2, -1.0)  # noqa: E731
    ob = grow_curves("beardhair_" + c["id"], me, bvh, lambda p: 1.0 if sel2(p) else 0.0, 16000, 0.02, comb, mat,
                     seed=13, lift=0.006, gravity=0.1, kink=("wave", 0.0015, 1.5))
    return [beard_shell(c, me, L)] + ([ob] if ob else [])


def beard_shell(c, me, L):
    b = c["beard"]
    fr = L["front"]

    def sel(p):
        if p.y > fr + 0.11 or p.z > L["nose"] - 0.006:
            return False
        lip = abs(p.x) < 0.02 and L["mouth"] - 0.006 < p.z < L["mouth"] + 0.004 and p.y < fr + 0.03
        if lip:
            return False                           # keep the lips clear
        if b.get("moustache") and L["mouth"] + 0.004 <= p.z and abs(p.x) < 0.03:
            return True
        return p.z < L["mouth"] + 0.004 and p.z > L["chin"] - 0.035
    return shell(me, "beard_" + c["id"], sel, lambda p: b["depth"] * (0.6 + 0.4 * smooth(L["mouth"], L["chin"], p.z)),
                 hair_mat(c, b["color"], 0.6), noise=0.002, seed=3)


KNITS = ("gansey", "guernsey", "cardigan", "rollneck", "woolcap")


def cloth_mat(name, hexc, kind):
    rough = {"oilskin": 0.22, "oilskin_jacket": 0.32, "tunic": 0.6, "reefer": 0.7, "mate_jacket": 0.55}.get(
        kind, 0.88 if kind in KNITS else 0.6)
    m = principled("M_" + name, hexc, rough, sheen=0.35 if kind in KNITS else 0.0)
    if kind in KNITS:                                  # knit rib: fine vertical stretch
        bump(m, 300.0, 0.4, detail=2.0, stretch=(1.0, 1.0, 3.5))
    elif kind in ("oilskin", "oilskin_jacket"):        # creased waxed cotton
        bump(m, 22.0, 0.3, detail=4.0)
    elif kind in ("reefer", "tunic", "mate_jacket"):   # woollen cloth
        bump(m, 500.0, 0.12, detail=3.0)
    return m


def neck_ellipse(me, z, half_w=0.085):
    """Centre and radii of the body's cross-section at height z (the neck only, |x| < half_w)."""
    pts = [v.co for v in me.vertices if abs(v.co.z - z) < 0.006 and abs(v.co.x) < half_w]
    if not pts:
        return Vector((0, 0)), 0.06, 0.06
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    return Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)), (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2


def ellipse_ring(name, me, z, mat, grow, depth, tilt=-10.0):
    """A collar or neck band fitted to the neck's real cross-section at height z (hides the shell's edge)."""
    c2, rx, ry = neck_ellipse(me, z)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=1.0, radius2=0.9, depth=depth,
                          matrix=Matrix.Translation((c2.x, c2.y, z + depth * 0.35)) @ Matrix.Rotation(math.radians(tilt), 4, "X")
                          @ Matrix.Diagonal((rx + grow, ry + grow, 1.0, 1.0)))
    ob = mesh_obj(name, bm, mat)
    so = ob.modifiers.new("solid", "SOLIDIFY")
    so.thickness = 0.004
    ob.modifiers.new("sub", "SUBSURF").render_levels = 1
    return ob


def collar_flaps(name, me, zn, mat):
    """Two shirt-collar points lying over the front of the neckline, angled down and out."""
    c2, rx, ry = neck_ellipse(me, zn)
    front = c2.y - ry - 0.004
    bm = bmesh.new()
    for s in (-1, 1):
        a = Vector((s * 0.008, front - 0.002, zn + 0.012))        # inner top, by the throat
        b = Vector((s * (rx + 0.004), c2.y - ry * 0.3, zn + 0.016))   # back along the neck
        tip = Vector((s * 0.03, front - 0.012, zn - 0.03))         # the collar point
        mid = Vector((s * (rx * 0.75), front + 0.004, zn - 0.006))
        vs = [bm.verts.new(v) for v in (a, b, mid, tip)]
        bm.faces.new((vs[0], vs[2], vs[1]) if s > 0 else (vs[0], vs[1], vs[2]))
        bm.faces.new((vs[0], vs[3], vs[2]) if s > 0 else (vs[0], vs[2], vs[3]))
    ob = mesh_obj(name, bm, mat)
    ob.modifiers.new("solid", "SOLIDIFY").thickness = 0.0025
    sub = ob.modifiers.new("sub", "SUBSURF")
    sub.levels = sub.render_levels = 2
    return ob


def buttons(c, name, me, mat, xs, zs, r=0.0065):
    """Buttons on the front of a garment: ray-cast onto the body, lifted off the cloth."""
    bm = bmesh.new()
    pts = [v.co for v in me.vertices]
    for z in zs:
        for x in xs:
            near = [p for p in pts if abs(p.z - z) < 0.006 and abs(p.x - x) < 0.006]
            if not near:
                continue
            front = min(near, key=lambda p: p.y)
            bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=r,
                                      matrix=Matrix.Translation(front + Vector((0, -0.024, 0))) @ Matrix.Diagonal((1, 0.45, 1, 1)))
    return mesh_obj(name, bm, mat)


def clothing(c, me, L):
    obs = []
    male = c["body"] == "male"
    zn = L["chin"] - (0.05 if male else 0.046)               # the garment's neckline (on the neck itself)
    def snap_neck(co):                                       # straight neckline, not a stair-step
        if co.z > zn - 0.03:
            co.z = zn - 0.001
    for kind, hexc, thick in c["cloth"]:
        m = cloth_mat(kind + "_" + c["id"], hexc, kind)
        if kind.endswith("collar"):                          # shirt / blouse collar: two points over the neckline
            obs.append(ellipse_ring("collar_" + c["id"], me, zn + 0.01, m, 0.006, 0.018, tilt=-6))
            continue
        if kind == "rollneck":                               # a dark roll-neck jersey under the jacket
            obs.append(ellipse_ring("rollneck_" + c["id"], me, zn + 0.004, m, 0.012, 0.06, tilt=-10))
            continue
        if kind == "oilskin_jacket":                         # worn open over the gansey: shoulders and sides only
            def sel_j(p):
                return p.z < zn - 0.022 and abs(p.x) > 0.058 + 0.12 * max(0.0, (zn - 0.022) - p.z)

            def snap_j(co):
                if co.z > zn - 0.05:
                    co.z = min(co.z, zn - 0.023)
            obs.append(shell(me, kind + "_" + c["id"], sel_j, lambda p, t=thick: t, m, snap=snap_j))
            continue
        obs.append(shell(me, kind + "_" + c["id"], lambda p: p.z < zn or (abs(p.x) > 0.066 and p.z < zn + 0.05),
                         lambda p, t=thick: t * (0.6 + 0.4 * smooth(-0.3, -0.45, p.z)), m, snap=snap_neck))
        high = kind in ("gansey", "guernsey", "oilskin", "reefer")
        if kind in ("gansey", "guernsey", "cardigan"):      # a knitted neck band hugging the neck
            obs.append(ellipse_ring("band_" + c["id"], me, zn - 0.006, m, 0.014, 0.024, tilt=-6))
        else:
            obs.append(ellipse_ring("band_" + c["id"], me, zn - 0.004, m, 0.02 if high else 0.017,
                                    0.05 if kind == "oilskin" else 0.042, tilt=-12))
        if kind in ("tunic", "reefer", "mate_jacket"):
            brass = principled("M_brass_" + c["id"], "#B38B45", 0.32, metal=1.0)
            xs = (-0.055, 0.055) if kind == "reefer" else (0.0,)
            obs.append(buttons(c, "buttons_" + c["id"], me, brass, xs, [zn - 0.07 - 0.065 * k for k in range(4)]))
        if kind == "cardigan":
            horn = principled("M_horn_" + c["id"], "#2A2622", 0.4)
            obs.append(buttons(c, "buttons_" + c["id"], me, horn, (0.0,), [zn - 0.05 - 0.05 * k for k in range(5)], r=0.005))
    return obs


def hat(c, L):
    kind = c["hat"]
    if not kind:
        return []
    top = 0.0
    if kind == "woolcap":        # Rory: knitted wool cap with a turned-up brim, worn back on the head
        m = cloth_mat("woolcap_" + c["id"], "#2E3440", "woolcap")
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=0.106,
                                  matrix=Matrix.Translation((0, 0.012, top - 0.052)) @ Matrix.Rotation(math.radians(12), 4, "X")
                                  @ Matrix.Diagonal((1.02, 1.08, 0.88, 1.0)))
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < top - 0.05 - 0.035 * max(0.0, v.co.y) / 0.1],
                         context="VERTS")
        crown = mesh_obj("woolcap_" + c["id"], bm, m)
        crown.modifiers.new("solid", "SOLIDIFY").thickness = 0.004
        crown.modifiers.new("sub", "SUBSURF").render_levels = 1
        bm = bmesh.new()                                     # the rolled brim: a thick band round the crown's edge
        bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=1.0, radius2=0.97, depth=0.026,
                              matrix=Matrix.Translation((0, 0.016, top - 0.054)) @ Matrix.Rotation(math.radians(12), 4, "X")
                              @ Matrix.Diagonal((0.112, 0.122, 1.0, 1.0)))
        brim = mesh_obj("woolcap_brim_" + c["id"], bm, m)
        so = brim.modifiers.new("solid", "SOLIDIFY")
        so.thickness = 0.009
        so.offset = 1.0
        brim.modifiers.new("sub", "SUBSURF").render_levels = 2
        return [crown, brim]
    if kind == "peaked":         # Hector's master's cap: navy crown, black peak, gold badge
        navy = cloth_mat("peaked_" + c["id"], "#1C2232", "reefer")
        blk = principled("M_peak_" + c["id"], "#0C0C0E", 0.25)
        gold = principled("M_badge_" + c["id"], "#B08A3A", 0.3, metal=1.0)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=36, radius1=0.1, radius2=0.118, depth=0.065,
                              matrix=Matrix.Translation((0, 0.006, top - 0.018)) @ Matrix.Rotation(math.radians(5), 4, "X"))
        crown = mesh_obj("peaked_" + c["id"], bm, navy)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.085, radius2=0.08, depth=0.007,
                              matrix=Matrix.Translation((0, -0.098, top - 0.05)) @ Matrix.Rotation(math.radians(-18), 4, "X")
                              @ Matrix.Diagonal((1.0, 0.62, 1.0, 1.0)))
        peak = mesh_obj("peak_" + c["id"], bm, blk)
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.014,
                                  matrix=Matrix.Translation((0, -0.112, top - 0.02)) @ Matrix.Diagonal((1.3, 0.4, 1.0, 1.0)))
        return [crown, peak, mesh_obj("badge_" + c["id"], bm, gold)]
    if kind == "souwester":      # Ross: black oilskin sou'wester, longer brim at the back
        oil = cloth_mat("souwester_" + c["id"], "#141618", "oilskin")
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.108,
                                  matrix=Matrix.Translation((0, 0.006, top - 0.045)) @ Matrix.Diagonal((1.0, 1.06, 0.8, 1.0)))
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < top - 0.06], context="VERTS")
        crown = mesh_obj("souwester_" + c["id"], bm, oil)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=0.17, radius2=0.11, depth=0.03,
                              matrix=Matrix.Translation((0, 0.03, top - 0.07)) @ Matrix.Rotation(math.radians(-10), 4, "X")
                              @ Matrix.Diagonal((1.0, 1.15, 1.0, 1.0)))
        return [crown, mesh_obj("brim_" + c["id"], bm, oil)]
    return []


def pipe(c, L):
    """Hector's pipe: a briar bowl at the left corner of the mouth, the stem in his teeth."""
    wood = principled("M_briar_" + c["id"], "#3A2418", 0.35)
    vul = principled("M_stem_" + c["id"], "#0E0D0C", 0.2)
    fr, mz = L["front"], L["mouth"]
    a = Vector((0.016, fr + 0.004, mz - 0.001))
    b = Vector((0.03, fr - 0.06, mz - 0.016))
    bm = bmesh.new()
    tube(bm, a, b, 0.0032, 10)
    stem = mesh_obj("pipe_stem_" + c["id"], bm, vul)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.0095, radius2=0.012, depth=0.03,
                          matrix=Matrix.Translation(b + Vector((0.002, -0.004, 0.012))))
    bowl = mesh_obj("pipe_bowl_" + c["id"], bm, wood)
    bowl.modifiers.new("sub", "SUBSURF").render_levels = 1
    return [stem, bowl]


def glasses(c, L):
    """Morag's reading glasses: thin gold frames, worn low on the nose, on a chain."""
    gold = principled("M_frames_" + c["id"], "#9A7A40", 0.3, metal=1.0)
    glass = principled("M_lens_" + c["id"], "#FFFFFF", 0.02)
    glass.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0
    fr = L["front"]
    bm = bmesh.new()
    lens = bmesh.new()
    for s in (-1, 1):
        cen = Vector((s * 0.03, fr - 0.006, L["eyes"] - 0.012))
        m = Matrix.Translation(cen) @ Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Diagonal((1.15, 0.85, 1.0, 1.0))
        tube_ring(bm, m, 0.018, 0.0011)
        bmesh.ops.create_circle(lens, cap_ends=True, segments=24, radius=0.0175, matrix=m)
        a0 = cen + Vector((s * 0.021, 0.0, 0.002))                       # temple arm back towards the ear
        tube(bm, a0, a0 + Vector((s * 0.006, 0.1, 0.006)), 0.0011)
    tube(bm, Vector((-0.012, fr - 0.008, L["eyes"] - 0.008)), Vector((0.012, fr - 0.008, L["eyes"] - 0.008)), 0.0011)
    for s in (-1, 1):            # the chain, from each temple down round the neck
        prev = None
        for k in range(21):
            t = k / 20
            p = Vector((s * (0.052 + 0.03 * t), fr + 0.06 + 0.03 * t, L["eyes"] - 0.01 - 0.16 * t * t - 0.02 * t))
            if prev is not None:
                tube(bm, prev, p, 0.0007, 5)
            prev = p
    frames = mesh_obj("glasses_" + c["id"], bm, gold)
    return [frames, mesh_obj("lenses_" + c["id"], lens, glass)]


def tube(bm, a, b, r, segs=6):
    d = b - a
    if d.length < 1e-6:
        return
    rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=d.length,
                          matrix=Matrix.Translation((a + b) / 2) @ rot)


def tube_ring(bm, m, R, r, segs=28):
    pts = [m @ Vector((R * math.cos(2 * math.pi * k / segs), R * math.sin(2 * math.pi * k / segs), 0)) for k in range(segs)]
    for k in range(segs):
        tube(bm, pts[k], pts[(k + 1) % segs], r)


def mesh_obj(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ------------------------------------------------------------------ studio

def studio(L):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "GPU"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "METAL"
    except TypeError:
        sc.cycles.device = "CPU"
    sc.cycles_curves.shape = "THICK"
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "Khronos PBR Neutral"     # keeps the base colours (AgX greyed hair and skin)
    world = bpy.data.worlds.new("w")
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.018, 0.016, 1)
    # mottled studio backdrop (warm grey-brown, darker at the edges)
    back = principled("M_backdrop", "#5C544C", 0.9)
    nt = back.node_tree
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 3.0
    n.inputs["Detail"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*srgb("#3A342F"), 1)
    ramp.color_ramp.elements[1].color = (*srgb("#7A6E62"), 1)
    nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.6, matrix=Matrix.Translation((0, 0.9, -0.3)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    mesh_obj("backdrop", bm, back)
    lights = [("key", (-0.9, -1.0, 0.4), 75.0, 0.9, (1.0, 0.94, 0.86)), ("fill", (1.0, -1.0, -0.05), 8.0, 1.4, (0.88, 0.93, 1.0)),
              ("rim", (0.7, 0.75, 0.45), 55.0, 0.45, (1.0, 0.9, 0.78)), ("back", (0.0, 0.6, -0.45), 12.0, 0.8, (1.0, 0.9, 0.8))]
    for name, loc, power, size, col in lights:
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = power
        ld["base_energy"] = power
        ld["base_color"] = col
        ld.size = size
        ld.color = col
        lo = bpy.data.objects.new(name, ld)
        lo.location = Vector(loc) + Vector((0, 0, L["eyes"]))
        target = Vector((0, 0.9, -0.3)) if name == "back" else Vector((0, 0, L["eyes"] - 0.05))
        lo.rotation_euler = (target - lo.location).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(lo)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 85
    cam.data.sensor_width = 36
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 4.0
    sc.collection.objects.link(cam)
    sc.camera = cam
    eye = Vector((0, -0.95, L["eyes"] + 0.01))
    look = Vector((0, 0, L["eyes"] - 0.075))
    cam.location = eye
    cam.rotation_euler = (look - eye).to_track_quat("-Z", "Y").to_euler()
    cam.data.dof.focus_distance = (Vector((0, L["front"], L["eyes"])) - eye).length


# ------------------------------------------------------------------ build and render one character

def build(cid, expr, base):
    c = dict(CHARS[cid])
    c["id"] = cid
    kind = c["body"]
    L = LAND[kind]
    src, eyes_src = base[kind]
    me = src.copy()
    me.name = "head_" + cid
    field = face_field(kind, c["face"], EXPR[expr])
    for v in me.vertices:
        v.co += field(v.co)
    # stubble mask: lower face below the nose, in front of the ears
    att = me.attributes.new("stubble", "FLOAT", "POINT")
    fr = L["front"]
    for i, v in enumerate(me.vertices):
        p = v.co
        w = smooth(L["nose"] - 0.004, L["nose"] - 0.016, p.z) * smooth(L["chin"] - 0.05, L["chin"] - 0.02, p.z)
        w *= 1 - smooth(fr + 0.1, fr + 0.12, p.y)
        lips = 1 - math.exp(-((p.x / 0.024) ** 2 + ((p.z - L["mouth"]) / 0.006) ** 2)) * (1 if p.y < fr + 0.03 else 0)
        att.data[i].value = w * lips * c.get("stubble", 0.0)
    lips = me.attributes.new("lips", "FLOAT", "POINT")
    for i, v in enumerate(me.vertices):
        p = v.co
        lips.data[i].value = math.exp(-((p.x / 0.021) ** 2 + ((p.z - L["mouth"]) / 0.0055) ** 2)) * (1 if p.y < fr + 0.025 else 0)
    lash = me.attributes.new("lash", "FLOAT", "POINT")       # upper-lid lash line, from the eyes' centres
    ctrs = []
    for e in eyes_src:
        ct = sum((v.co for v in e.vertices), Vector()) / len(e.vertices)
        ctrs.append(ct + field(ct))
    for i, v in enumerate(me.vertices):
        p = v.co
        w = 0.0
        for ct in ctrs:
            q = p - (ct + Vector((0, -0.0085, 0.0052)))
            w = max(w, math.exp(-((q.x / 0.0115) ** 2 + (q.z / 0.0015) ** 2 + (q.y / 0.005) ** 2)))
        lash.data[i].value = 0.85 * w
    flush = me.attributes.new("flush", "FLOAT", "POINT")     # cheeks and nose: wind flush, freckles
    for i, v in enumerate(me.vertices):
        p = v.co
        if p.y > fr + 0.06:
            continue
        w = max(g(p, Vector((s * 0.04, fr + 0.03, L["nose"] - 0.006)), 0.026) for s in (-1, 1))
        w = max(w, 0.8 * g(p, Vector((0, fr - 0.004, L["nose"] + 0.004)), 0.02))
        flush.data[i].value = w
    me.materials.append(skin_mat(c))
    for p in me.polygons:
        p.use_smooth = True
    head = bpy.data.objects.new("head_" + cid, me)
    bpy.context.scene.collection.objects.link(head)
    parts = [head]
    eye_mat = eye_material(cid, c.get("iris", "#4A5A66"))
    for k, e in enumerate(eyes_src):
        em = e.copy()
        ctr = sum((v.co for v in em.vertices), Vector()) / len(em.vertices)
        em.transform(Matrix.Translation(field(ctr)))
        em.materials.append(eye_mat)
        eo = bpy.data.objects.new("eye_%s_%d" % (cid, k), em)
        bpy.context.scene.collection.objects.link(eo)
        parts.append(eo)
    bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [p.vertices[:] for p in me.polygons])
    parts += hair(c, head, me, L, bvh)
    bw = brows(c, me, L, bvh)
    if bw:
        parts.append(bw)
    if c.get("beard"):
        parts += beard(c, head, me, L, bvh)
    parts += clothing(c, me, L)
    parts += hat(c, L)
    if c.get("glasses"):
        parts += glasses(c, L)
    if c.get("pipe"):
        parts += pipe(c, L)
    rig = bpy.data.objects.new("rig_" + cid, None)       # pivot at the base of the neck
    rig.location = (0, 0.02, -0.26)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.update()
    inv = rig.matrix_world.inverted()
    for p in parts:
        p.parent = rig
        p.matrix_parent_inverse = inv
    pitch, yaw2 = SIL_POSE.get(expr, (0.0, 0.0)) if c.get("silhouette") else (0.0, 0.0)
    rig.rotation_euler = (math.radians(-pitch), 0, math.radians(c["yaw"] + yaw2))
    return rig


def lowkey(L):
    """Character-bible lighting (Callum §12): one side warm amber interior light, the other cool and dim from
    the storm window, a dark room behind. Moody, and kinder to the faces than an even studio light."""
    rig = {"key": ((-1.15, -0.55, 0.25), 95.0, 0.6, (1.0, 0.76, 0.5)),
           "fill": ((1.1, -0.7, 0.05), 3.0, 1.2, (0.55, 0.66, 0.92)),
           "rim": ((0.85, 0.7, 0.35), 22.0, 0.4, (0.7, 0.8, 1.0)),
           "back": ((0.0, 0.6, -0.45), 2.5, 0.8, (1.0, 0.8, 0.6))}
    for name, (loc, e, size, col) in rig.items():
        o = bpy.data.objects[name]
        o.location = Vector(loc) + Vector((0, 0, L["eyes"]))
        target = Vector((0, 0.9, -0.3)) if name == "back" else Vector((0, 0, L["eyes"] - 0.05))
        o.rotation_euler = (target - o.location).to_track_quat("-Z", "Y").to_euler()
        o.data.size = size
        o.data["base_energy"] = e
        o.data["base_color"] = col


def set_lights(silhouette):
    """Normal studio light, or the silhouette rig: the face unlit, a warm stair-lamp glow behind and a hard rim."""
    for o in bpy.data.objects:
        if o.type != "LIGHT":
            continue
        d = o.data
        e, col = d["base_energy"], tuple(d["base_color"])
        if silhouette:
            e = {"key": 0.0, "fill": 0.0, "rim": 120.0, "back": 70.0}[o.name]
            col = (1.0, 0.78, 0.5) if o.name in ("rim", "back") else (0.6, 0.7, 0.9)
        d.energy = e
        d.color = col


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--expr", default="")
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--res", default="512x640")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--light", default="studio", choices=["studio", "lowkey"])
    a = ap.parse_args(argv)
    clear()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rx, ry = (int(v) for v in a.res.split("x"))
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.render.resolution_percentage = 100
    sc.cycles.samples = a.samples
    ids = [i for i in (a.only.split(",") if a.only else CHARS)]
    base = {}
    for kind in {CHARS[i]["body"] for i in ids}:
        base[kind] = load_body(kind)
    studio(LAND["male"])
    if a.light == "lowkey":
        lowkey(LAND["male"])
    done = []
    for cid in ids:
        exprs = a.expr.split(",") if a.expr else CHARS[cid]["expr"]
        for ex in exprs:
            keep = {o.name for o in bpy.data.objects}
            rig = build(cid, ex, base)
            set_lights(bool(CHARS[cid].get("silhouette")))
            L = LAND[CHARS[cid]["body"]]
            cam = sc.camera
            cam.location.z = L["eyes"] + 0.01
            look = Vector((0, 0, L["eyes"] - 0.075))
            cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
            path = out / ("%s_%s.png" % (cid, ex))
            sc.render.filepath = str(path)
            if a.debug:
                for o in bpy.data.objects:
                    if o.type == "MESH" and (o.name.startswith("eye_") or o.name.startswith("head_")):
                        vs = [o.matrix_world @ v.co for v in o.data.vertices]
                        print("DBG", o.name, len(vs), tuple(round(sum(v[i] for v in vs) / len(vs), 3) for i in range(3)),
                              "ymin", round(min(v.y for v in vs), 3), "hide", o.hide_render)
                continue
            bpy.ops.render.render(write_still=True)
            done.append(path.name)
            for o in list(bpy.data.objects):
                if o.name not in keep:
                    bpy.data.objects.remove(o, do_unlink=True)
    print("PORTRAITS_RESULT", done)


if __name__ == "__main__":
    main()
