"""THE LAST LIGHT · G4b (item 6): the keeper's oilskin as a baked Blender cloth drape.

The coat starts as a closed garment shell (collar, sloped shoulders, body to the hem) around an empty
hanging axis, pinned only at the collar loop on the back of the neck, and falls under gravity for SETTLE
frames with Blender's built-in cloth (fixed settings, so every build gives the same drape). It collides
with the coat stand's post behind it. The settled shell is smoothed, applied and given THICK of thickness.

simulate_coat() returns a world-space Mesh datablock; the caller appends it to its bucket and frees it.
Called from build.py build_coat_rack(); usable alone for previews (tools/bl -P a harness).
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

SEGS = 48                     # around the body
SETTLE = 120                  # frames at 24 fps
NOISE = 0.004                 # seeded radial jitter (m) so the shell buckles into folds, not a smooth tube
# cloth settings (overridable for previews): soft in bending and compression so the empty shoulders give way
CLOTH = {"mass": 0.45, "tension": 30.0, "compression": 40.0, "shear": 5.0, "bending": 0.35, "air": 2.0}   # compression 4 let the shell shrink to 22 cm
# audit C5 (2026-11-16): 2 mm read as paper: the rim showed as a razor edge and the thin shell's folds as
# sawtooth ridges. 4.5 mm (waxed cotton over a lining) and SMOOTH passes of the settled shell before the
# thickness is added, which take out the one-face crumples without moving the big folds
THICK = 0.0045
SMOOTH = (4, 0.5)             # (iterations, factor)
# the shell as cut, before it falls (z down from the collar loop, half-width, depth ratio): wider and
# rounder than it will hang, so the empty shoulders collapse into folds that run down from the loop
PROFILE = [(0.0, 0.045, 1.0), (-0.025, 0.09, 0.75), (-0.06, 0.17, 0.6), (-0.11, 0.215, 0.55),
           (-0.2, 0.225, 0.55), (-0.35, 0.215, 0.55), (-0.5, 0.215, 0.55), (-0.65, 0.225, 0.56),
           (-0.8, 0.24, 0.58), (-0.98, 0.255, 0.6)]
ROWS_PER_SPAN = 3


def _shell(top, b3):
    """Closed shell: rows from the collar to the hem, a cap at the collar. Returns (bmesh, pin vert ids)."""
    bm = bmesh.new()
    rnd = random.Random(6)            # item 6
    rows = []
    prof = []
    for (z0, r0, d0), (z1, r1, d1) in zip(PROFILE, PROFILE[1:]):
        for k in range(ROWS_PER_SPAN):
            f = k / ROWS_PER_SPAN
            prof.append((z0 + (z1 - z0) * f, r0 + (r1 - r0) * f, d0 + (d1 - d0) * f))
    prof.append(PROFILE[-1])
    for z, r, d in prof:
        row = []
        for i in range(SEGS):
            th = 2 * math.pi * i / SEGS
            rr = r + (rnd.uniform(-NOISE, NOISE) if z < -0.03 else 0.0)
            row.append(bm.verts.new(top + b3 @ Vector((rr * math.cos(th), rr * math.sin(th) * d, z))))
        rows.append(row)
    for a, b in zip(rows, rows[1:]):
        for i in range(SEGS):
            bm.faces.new((a[i], a[(i + 1) % SEGS], b[(i + 1) % SEGS], b[i]))
    cap = bm.verts.new(top + b3 @ Vector((0.0, 0.0, 0.006)))
    for i in range(SEGS):
        bm.faces.new((cap, rows[0][(i + 1) % SEGS], rows[0][i]))
    bm.verts.index_update()
    # the collar loop: the cap and the back of the collar ring (y < 0 is the coat's back, toward the post)
    pins = [cap.index] + [rows[0][i].index for i in range(SEGS) if math.sin(2 * math.pi * i / SEGS) < -0.35]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm, pins


def simulate_coat(top, b3, post_a, post_b, post_r, coll):
    """top: the collar loop (world), b3: the coat frame (x across, y toward the room, z up),
    post_a / post_b: the stand's post axis ends, post_r: its radius. Returns a world-space Mesh."""
    scene = bpy.context.scene
    bm, pins = _shell(top, b3)
    me = bpy.data.meshes.new("TMP_coat_cloth")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("TMP_coat_cloth", me)
    coll.objects.link(ob)
    vg = ob.vertex_groups.new(name="pin")
    vg.add(pins, 1.0, "REPLACE")
    # the post as a collision proxy (a capped cylinder along the axis)
    axis = post_b - post_a
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=post_r + 0.004, depth=axis.length,
                                        location=(post_a + post_b) / 2)
    post = bpy.context.active_object
    post.name = "TMP_coat_post"
    post.rotation_mode = "QUATERNION"
    post.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(axis.normalized())
    for c in post.users_collection:
        c.objects.unlink(post)
    coll.objects.link(post)
    post.modifiers.new("collision", "COLLISION")
    post.collision.thickness_outer = 0.004
    cl = ob.modifiers.new("cloth", "CLOTH")
    s = cl.settings
    s.quality = 10
    s.mass = CLOTH["mass"]               # waxed cotton: heavier than shirting
    s.air_damping = CLOTH["air"]
    s.tension_stiffness = CLOTH["tension"]
    s.compression_stiffness = CLOTH["compression"]
    s.shear_stiffness = CLOTH["shear"]
    s.bending_stiffness = CLOTH["bending"]
    s.tension_damping = s.compression_damping = s.shear_damping = 5.0
    s.bending_damping = 0.8
    s.vertex_group_mass = "pin"
    cs = cl.collision_settings
    cs.collision_quality = 4
    cs.distance_min = 0.004
    cs.use_self_collision = True
    cs.self_distance_min = 0.003
    cl.point_cache.frame_start = 1
    cl.point_cache.frame_end = SETTLE
    f0 = scene.frame_current
    for f in range(1, SETTLE + 1):
        scene.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    settled = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    settled.transform(ob.matrix_world)
    scene.frame_set(f0)
    for o in (ob, post):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.meshes.remove(me)
    sbm = bmesh.new()
    sbm.from_mesh(settled)
    for _ in range(SMOOTH[0]):
        bmesh.ops.smooth_vert(sbm, verts=sbm.verts, factor=SMOOTH[1], use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bmesh.ops.recalc_face_normals(sbm, faces=sbm.faces)
    sbm.to_mesh(settled)
    sbm.free()
    # THICK, outward, through a throwaway object (solidify is a modifier)
    tmp = bpy.data.objects.new("TMP_coat_solid", settled)
    coll.objects.link(tmp)
    sol = tmp.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = THICK
    sol.offset = 1.0
    dg = bpy.context.evaluated_depsgraph_get()
    out = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    shell = settled                                # the outer surface, for raycasts (kept for the caller)
    return out, shell
