"""Contact check (audit Stages B and S): which loose mesh parts intersect the part found at each probe point.

    tools/bl FILE.blend -P projects/games/last_light/blender/contact_check.py -- OUT.json \
        name=bearing,along,z,dist [name=...] [--collection ASSET_watch_room,ASSET_stairwell]

A probe is given in build.py dp() terms: bearing (deg), along (m, right of the wall frame), z above the room
floor and dist from the room centre. The smallest loose part whose box contains the probe is "the part"; the
report lists every other loose part whose triangles overlap it (BVH), with its size and centre, so each
touch can be checked against the intended mates. Colliders, UCX_ and glass are skipped.
"""
import json
import math
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

F = 20.0


def dp(b, along, z, dist):
    br = math.radians(b)
    r = Vector((math.cos(br), -math.sin(br), 0))
    o = Vector((math.sin(br), math.cos(br), 0))
    return o * dist + r * along + Vector((0, 0, F + z))


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:]
    out, probes, colls = argv[0], {}, None
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--collection":
            colls = set(argv[i + 1].split(","))
            i += 2
            continue
        name, vals = a.split("=", 1)
        b, al, z, d = (float(x) for x in vals.split(","))
        probes[name] = dp(b, al, z, d)
        i += 1
    return out, probes, colls


def loose_parts(colls):
    parts = []   # (obj name, verts, polys, aabb lo, aabb hi)
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name.startswith(("COL_", "UCX_")) or "Glass" in ob.name:
            continue
        if colls and not any(c.name in colls for c in ob.users_collection):
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.transform(ob.matrix_world)
        bm.verts.ensure_lookup_table()
        seen = set()
        for v0 in bm.verts:
            if v0.index in seen:
                continue
            stack, comp = [v0], []
            seen.add(v0.index)
            while stack:
                v = stack.pop()
                comp.append(v)
                for e in v.link_edges:
                    w = e.other_vert(v)
                    if w.index not in seen:
                        seen.add(w.index)
                        stack.append(w)
            idx = sorted({v.index for v in comp})
            faces = {f for v in comp for f in v.link_faces}
            if not faces:
                continue
            loc = {i: k for k, i in enumerate(idx)}
            verts = [bm.verts[i].co.copy() for i in idx]
            polys = [[loc[v.index] for v in f.verts] for f in faces]
            lo = Vector((min(p.x for p in verts), min(p.y for p in verts), min(p.z for p in verts)))
            hi = Vector((max(p.x for p in verts), max(p.y for p in verts), max(p.z for p in verts)))
            parts.append((ob.name, verts, polys, lo, hi))
        bm.free()
    return parts


def main():
    out_path, probes, colls = parse_args()
    parts = loose_parts(colls)

    def near(p, lo, hi, r):
        return all(lo[i] - r <= p[i] <= hi[i] + r for i in range(3))

    report = {}
    for name, p in probes.items():
        hits = [k for k, (_n, _v, _p, lo, hi) in enumerate(parts) if near(p, lo, hi, 0.005)]
        hits.sort(key=lambda k: (parts[k][4] - parts[k][3]).length)
        entries = []
        for k in hits[:1]:
            n, v, pl, lo, hi = parts[k]
            bvh = BVHTree.FromPolygons(v, pl)
            touching = []
            for j, (n2, v2, p2, lo2, hi2) in enumerate(parts):
                if j == k or any(hi2[i] < lo[i] - 0.002 or lo2[i] > hi[i] + 0.002 for i in range(3)):
                    continue
                ov = bvh.overlap(BVHTree.FromPolygons(v2, p2))
                if ov:
                    touching.append({"obj": n2, "tris": len(ov), "size": [round(x, 3) for x in (hi2 - lo2)],
                                     "centre": [round(x, 3) for x in (lo2 + hi2) / 2]})
            entries.append({"obj": n, "size": [round(x, 3) for x in (hi - lo)],
                            "centre": [round(x, 3) for x in (lo + hi) / 2], "touching": touching})
        report[name] = entries or "no part at probe"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=1)
    print("CONTACT_RESULT", out_path)


main()
