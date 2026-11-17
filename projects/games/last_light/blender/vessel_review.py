"""THE LAST LIGHT · audit Stage E1: review renders of the exported vessel GLBs (not the build scene).

Each GLB is imported into an empty scene, set on a flat sea with its waterline at sea level (the model origin
0.4 m below it, as ship_view2.gd places it), and rendered with EEVEE:

  3q_dusk, side_dusk, 3q_night, side_night      close views; at night the lamps are point lights at the empties
  bino_120, bino_230, bino_400                  7x binocular framing (10 deg vertical FOV, as equipment.gd
                                                BINO_FOV) from the watch room's eye (21.65 m above the sea), dusk,
                                                depth fog for about 1 km visibility (Stage M's recommended range)
  bino_230_night                                the same at night: lights first, hull second
  bino_230_beam   (unlit vessels only)          night, with the light's beam on her: can SY 214 be read?

  tools/bl -P projects/games/last_light/blender/vessel_review.py -- --only kittiwake --out renders/last_light/stageE
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
WS = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(WS / "scripts"))
import vessels as VS  # noqa: E402

EYE = 20.0 + 1.65            # spec.py watch room floor_z + eye_height, above the sea
BINO_FOV = 10.0              # equipment.gd BINO_FOV (vertical, degrees)
VIS_M = 1000.0               # visibility for the fog variants (Koschmieder: sigma = 3.912 / V)
RES = (1280, 720)
LIGHTS = {"NAV_masthead": ((1.0, 0.95, 0.85), 60.0), "NAV_port": ((1.0, 0.12, 0.08), 40.0),
          "NAV_starboard": ((0.2, 1.0, 0.35), 40.0), "NAV_stern": ((1.0, 0.95, 0.85), 30.0),
          "DECK_work": ((1.0, 0.7, 0.4), 220.0), "DECK_aft": ((1.0, 0.7, 0.4), 160.0)}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)        # headless only; never in a live session
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.film_transparent = False
    sc.eevee.taa_render_samples = 48
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "None"
    return sc


def import_ship(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    objs = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new("ShipRoot", None)
    bpy.context.scene.collection.objects.link(root)
    for o in objs:
        if o.parent is None:
            o.parent = root
    root.location.z = -VS.WL
    return root, objs


def world_gradient(sc, horizon, zenith, strength, sun_dir=None):
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    bg = nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.5, (*horizon, 1)
    el[1].position, el[1].color = 0.72, (*zenith, 1)
    bg.inputs["Strength"].default_value = strength


def sea(sc, color):
    bpy.ops.mesh.primitive_plane_add(size=12000, location=(0, 0, 0))
    p = bpy.context.active_object
    p.name = "Sea"
    m = bpy.data.materials.new("Sea")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.24
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.35
    nz.inputs["Detail"].default_value = 6.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    p.data.materials.append(m)
    return p


def sun(name, az, el, strength, color, angle=0.6):
    d = bpy.data.lights.new(name, "SUN")
    d.energy = strength
    d.color = color
    d.angle = math.radians(angle)
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = (math.radians(90 - el), 0, math.radians(az + 90))
    return o


def lamps(objs, root):
    for o in objs:
        if o.type != "EMPTY" or o.name.split(".")[0] not in LIGHTS:
            continue
        col, w = LIGHTS[o.name.split(".")[0]]
        ld = bpy.data.lights.new("L_" + o.name, "POINT")
        ld.energy, ld.color, ld.shadow_soft_size = w, col, 0.05
        lo = bpy.data.objects.new("L_" + o.name, ld)
        bpy.context.scene.collection.objects.link(lo)
        lo.matrix_world = o.matrix_world.copy()


def camera(sc, loc, target, lens=50.0, fov_v=None):
    cd = bpy.data.cameras.new("Cam")
    if fov_v is not None:
        cd.sensor_fit = "VERTICAL"
        cd.angle_y = math.radians(fov_v)
    else:
        cd.lens = lens
    cd.clip_end = 20000
    c = bpy.data.objects.new("Cam", cd)
    sc.collection.objects.link(c)
    c.location = loc
    d = Vector(target) - Vector(loc)
    c.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = c
    return c


def bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def render(sc, path):
    sc.render.filepath = str(path)
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)


def horizon_rgb(sc):
    """The sky just above the horizon as this scene renders it (a small probe render, ship and lights hidden)."""
    cam = sc.camera
    keep = (cam.matrix_world.copy(), sc.render.resolution_x, sc.render.resolution_y, cam.data.sensor_fit,
            cam.data.angle_y)
    hide = [o for o in sc.objects if o.type in ("MESH", "LIGHT") and o.name not in ("Sea",) and not o.hide_render
            and not (o.type == "LIGHT" and o.data.type == "SUN")]
    for o in hide:
        o.hide_render = True
    cam.location = (0, 0, EYE)
    cam.rotation_euler = (math.radians(90), 0, math.radians(-90))       # level, looking along +X
    cam.data.sensor_fit, cam.data.angle_y = "VERTICAL", math.radians(BINO_FOV)
    sc.render.resolution_x, sc.render.resolution_y = 128, 72
    probe = str(WS / "renders" / "last_light" / "stageE" / "_horizon_probe.png")
    render(sc, probe)
    img = bpy.data.images.load(probe)
    a = np.empty(128 * 72 * 4, np.float32)
    img.pixels.foreach_get(a)
    a = a.reshape(72, 128, 4)
    rgb = a[37:41, :, :3].reshape(-1, 3).mean(0)                          # rows just above the horizon
    bpy.data.images.remove(img)
    for o in hide:
        o.hide_render = False
    cam.matrix_world, sc.render.resolution_x, sc.render.resolution_y, cam.data.sensor_fit, cam.data.angle_y = keep
    return rgb


def fogged(sc, path, sigma, fog_rgb=None):
    """Beauty (kept clear), then camera distance (material override, EXR), and a fogged copy *_fog.png mixed
    toward the horizon colour."""
    if fog_rgb is None:
        fog_rgb = horizon_rgb(sc)
    render(sc, path)
    vl = sc.view_layers[0]
    m = bpy.data.materials.new("Depth")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    cdat = nt.nodes.new("ShaderNodeCameraData")
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(cdat.outputs["View Distance"], em.inputs["Strength"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    wstr = sc.world.node_tree.nodes["Background"].inputs["Strength"]
    keep = (wstr.default_value, sc.view_settings.view_transform, sc.eevee.taa_render_samples)
    wstr.default_value = 0.0
    hidden = [o for o in sc.objects if o.type == "LIGHT" and not o.hide_render]
    for o in hidden:
        o.hide_render = True
    vl.material_override = m
    sc.view_settings.view_transform = "Standard"
    sc.eevee.taa_render_samples = 1
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_mode = "BW"
    sc.render.image_settings.color_depth = "32"
    sc.render.image_settings.exr_codec = "ZIP"
    (Path(path).parent / "depth").mkdir(exist_ok=True)
    dpath = str(Path(path).parent / "depth" / Path(path).name.replace(".png", ".exr"))
    sc.render.filepath = dpath
    bpy.ops.render.render(write_still=True)
    sc.render.image_settings.color_mode = "RGB"
    vl.material_override = None
    wstr.default_value, sc.view_settings.view_transform, sc.eevee.taa_render_samples = keep
    for o in hidden:
        o.hide_render = False
    W, H = RES
    di = bpy.data.images.load(dpath)
    d = np.empty(W * H * 4, np.float32)
    di.pixels.foreach_get(d)
    d = d.reshape(H, W, 4)[..., 0]
    bi = bpy.data.images.load(str(path))
    b = np.empty(W * H * 4, np.float32)
    bi.pixels.foreach_get(b)
    b = b.reshape(H, W, 4)
    sky = d <= 0.0
    T = np.where(sky, 1.0, np.exp(-sigma * d))[..., None]
    b[..., :3] = b[..., :3] * T + np.asarray(fog_rgb)[None, None, :] * (1 - T)
    bi.pixels.foreach_set(b.ravel())
    bi.filepath_raw = str(path).replace(".png", "_fog.png")
    bi.file_format = "PNG"
    bi.save()
    return [round(float(x), 3) for x in fog_rgb]


def dusk(sc):
    world_gradient(sc, (0.16, 0.13, 0.13), (0.025, 0.035, 0.07), 1.0)
    sea(sc, (0.006, 0.016, 0.024))
    sun("Sun", 115, 4.0, 2.6, (1.0, 0.62, 0.4))


def night(sc, moon=0.06):
    world_gradient(sc, (0.012, 0.016, 0.026), (0.002, 0.003, 0.007), 1.0)
    sea(sc, (0.006, 0.012, 0.018))
    sun("Moon", 140, 28, moon, (0.7, 0.78, 1.0), angle=0.5)
    sc.view_settings.exposure = 1.2


def view_close(sc, lo, hi, az, el, lens=50.0):
    c = (lo + hi) / 2
    size = max((hi - lo).y, (hi - lo).z * 1.6, (hi - lo).x)
    dist = size / (2 * math.tan(math.radians(39.6) / 2)) * 1.12
    a, e = math.radians(az), math.radians(el)
    loc = c + Vector((math.cos(e) * math.sin(a), math.cos(e) * math.cos(a), math.sin(e))) * dist
    loc.z = max(loc.z, 1.2)
    camera(sc, loc, c, lens)


def view_bino(sc, rng, root, heading_deg=35.0):
    """Ship at horizontal range rng on the +X axis, her bow turned heading_deg from the line of sight."""
    root.location = Vector((rng, 0.0, -VS.WL))
    root.rotation_euler = (0, 0, math.radians(90 + heading_deg))
    camera(sc, (0, 0, EYE), (rng, 0, 3.0), fov_v=BINO_FOV)


def run(vid, out):
    V = VS.VESSELS[vid]
    glb = VS.latest_glb(V["export"])
    od = Path(out) / vid
    od.mkdir(parents=True, exist_ok=True)
    files, info = [], {"vid": vid, "glb": str(glb.relative_to(WS))}
    shots = [("3q_dusk", "dusk", 42, 12), ("side_dusk", "dusk", -90, 3), ("3q_night", "night", 42, 12),
             ("side_night", "night", -90, 3)]
    for name, light, az, el in shots:
        sc = reset()
        root, objs = import_ship(glb)
        (dusk if light == "dusk" else night)(sc)
        if light == "night" and V["lit"]:
            lamps(objs, root)
        lo, hi = bounds(objs)
        view_close(sc, lo, hi, az, el)
        p = od / (name + ".png")
        render(sc, p)
        files.append(p)
    sigma = 3.912 / VIS_M
    bino = [("bino_120", "dusk", 120), ("bino_230", "dusk", 230), ("bino_400", "dusk", 400),
            ("bino_230_night", "night", 230)]
    if not V["lit"]:
        bino.append(("bino_230_beam", "beam", 230))
    for name, light, rng in bino:
        sc = reset()
        root, objs = import_ship(glb)
        if light == "dusk":
            dusk(sc)
        else:
            night(sc)
            if V["lit"]:
                lamps(objs, root)
        view_bino(sc, rng, root)
        bpy.context.view_layer.update()
        if V["lit"] and light != "dusk":
            for o in [o for o in sc.objects if o.name.startswith("L_")]:
                src = bpy.data.objects.get(o.name[2:])
                if src:
                    o.matrix_world = src.matrix_world.copy()
        if light == "beam":                          # the lighthouse beam swung onto her
            sd = bpy.data.lights.new("Beam", "SPOT")
            sd.energy, sd.spot_size, sd.spot_blend, sd.color = 4.0e6, math.radians(3.0), 0.3, (1.0, 0.97, 0.9)
            so = bpy.data.objects.new("Beam", sd)
            sc.collection.objects.link(so)
            so.location = (0, 2.0, EYE + 6.0)
            so.rotation_euler = (Vector((rng, 0, 1.5)) - so.location).to_track_quat("-Z", "Y").to_euler()
        p = od / (name + ".png")
        info[name + "_fog_rgb"] = [round(float(x), 4) for x in fogged(sc, p, sigma)]
        files.append(p)
        if rng >= 230 and light == "dusk":
            files.append(Path(str(p).replace(".png", "_fog.png")))
    return files, info


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    only, out = "", "renders/last_light/stageE"
    for i, a in enumerate(argv):
        if a == "--only":
            only = argv[i + 1]
        if a == "--out":
            out = argv[i + 1]
    vids = [v for v in only.split(",") if v] or VS.ORDER
    res = {}
    for vid in vids:
        files, info = run(vid, WS / out)
        info["files"] = [str(Path(f).relative_to(WS)) for f in files]
        res[vid] = info
    print("REVIEW_RESULT", json.dumps(res))


if __name__ == "__main__":
    main()
