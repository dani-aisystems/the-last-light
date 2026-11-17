"""THE LAST LIGHT · audit Stage E1 (plan 9.1): the vessels, built procedurally for ship_view2.gd.

Five designs, seven paint schemes, one GLB each:

  kittiwake       ring-netter MFV, 13 m      -> ship_fishing.glb   (Kittiwake SY 37; Corrie May until E2)
  corrie_may      same hull, other paint     -> ship_corrie_may.glb (BRD 9; wired in E2)
  mary_ellen      the black boat, 10 m       -> ship_launch.glb    (the Catriona rebuilt as SY 214; unlit)
  gannet          gaff schooner, 19 m        -> ship_schooner.glb  (SY 112; Lowestoft Star until E2)
  lowestoft_star  east-coast drifter, 25 m   -> ship_lowestoft_star.glb (LT 401; wired in E2)
  iona_star       coaster, 30 m              -> ship_steamer.glb   (Iona Star; Hendrika until E2)
  hendrika        same hull, timber deck cargo, grey -> ship_hendrika.glb (wired in E2)

Contract (godot/scripts/fp/ship_view2.gd, read-only here): the model is added at the ship node's origin, which sits
0.4 m below the wave height, so the design waterline is z = +0.40 in Blender; the bow is +Y (Godot -Z), starboard
+X. Sizes fit ship_view2's DIMS for the kind each file serves (Daniel, 2026-11-17). Materials are called
M_Vessel_<Id> so ship_view2._swap() (LLMaterials names only) never replaces them.

The geometry is generated in plain Python (numpy), so the painter, the checks and pytest see exactly the mesh and the
UV islands Blender gets. Every part is a closed shell; faces are oriented outward per shell (consistent winding,
then the sign of the shell's volume). UVs are object-space planar projections, one island per face group, packed
into one 1024 atlas without overlap (except the few uniform 'shared' kinds), so the AO bake is clean.

  tools/py projects/games/last_light/blender/vessels.py --report            # tri counts, checks, packing
  tools/py projects/games/last_light/blender/vessels.py --paint             # -> blender/textures/vessels/*_{base,rough,metal,normal,emit}.png
  tools/bl -P projects/games/last_light/blender/vessels.py -- --new --build --bake --check --save
  tools/bl <vessels_vNNN.blend> -P projects/games/last_light/blender/vessels.py -- --export all --out exports/last_light
  tools/py projects/games/last_light/blender/vessels.py --check-glb         # the latest exports/last_light/gltf/ship_*.glb
"""
import json
import math
import struct
import sys
from collections import defaultdict, deque
from pathlib import Path

import numpy as np

try:
    import bpy  # noqa: F401
except ImportError:          # host Python: geometry, painting and checks only
    bpy = None

HERE = Path(__file__).resolve().parent
WS = HERE.parents[3]
TEX = HERE / "textures" / "vessels"
EXPORTS = WS / "exports" / "last_light" / "gltf"

N = 1024                 # atlas size (one 1k set per vessel)
PAD = 4                  # px of padding round every island (mip bleed; the AO bake margin)
WL = 0.40                # design waterline above the model origin
TRI_MIN, TRI_MAX = 4000, 6000
DIMS = {"fishing": (4.2, 2.4, 13.0), "schooner": (5.0, 2.6, 19.0), "steamer": (7.5, 4.2, 30.0),
        "launch": (3.4, 1.9, 10.0)}     # ship_view2.gd DIMS: beam x, height above origin y, length z
HINT_SUFFIXES = ("-noimp", "-col", "_col", "-colonly", "_colonly", "-convcol", "_convcol", "-convcolonly",
                 "_convcolonly", "-rigid", "_rigid", "-vehicle", "_vehicle", "-wheel", "_wheel", "-navmesh",
                 "_navmesh", "-occ", "_occ", "-occonly", "_occonly", "-loop", "_loop", "-cycle", "_cycle")
EMPTY_NAMES = ("NAV_masthead", "NAV_port", "NAV_starboard", "NAV_stern", "DECK_work")
# kinds drawn as one uniform colour: all their faces share one small rect (overlap allowed, AO forced to 1)
SHARED = {"rope": 16, "hidden": 8, "lamp_r": 16, "lamp_g": 16, "lamp_w": 16, "lamp_dark": 16, "rubber": 16,
          "glass": 16, "soot": 16, "black": 16}
DENSITY = {"hull": 1.0, "transom": 1.0, "deck": 0.55, "bulwark": 0.6, "rail": 0.6, "break": 0.6, "paint": 0.9,
           "varnish": 0.9, "roof": 0.55, "canvas": 0.6, "net": 0.5, "metal": 0.6, "funnel": 0.9, "mast": 0.7,
           "timber": 0.6, "timber_end": 0.8, "tarp": 0.5}

# ------------------------------------------------------------------ the fleet
VESSELS = {
    "kittiwake": dict(Id="Kittiwake", export="ship_fishing", kind="fishing", design="ringnetter", lit=True,
                      reg="SY 37", name="KITTIWAKE", port="STORNOWAY", weather=0.4, seed=37, radar=True,
                      pal=dict(top="#1E2B3C", strake="#D6D0BF", boot="#1B1B1B", bottom="#6E2B22", rail="#CFC7B3",
                               bulwark="#CBC3AE", deck="#8B785E", house="#7A4A26", house_paint=None,
                               roof="#B4AEA2", mast="#8A5A33", sail="#8A5C3E", text="#ECE7DA", net="#3C3A2E")),
    "corrie_may": dict(Id="CorrieMay", export="ship_corrie_may", kind="fishing", design="ringnetter", lit=True,
                       reg="BRD 9", name="CORRIE MAY", port="BROADFORD", weather=0.55, seed=9, radar=False,
                       pal=dict(top="#2D4A37", strake="#DED5BC", boot="#1B1B1B", bottom="#6A2E24", rail="#2D4A37",
                                bulwark="#D8CFB6", deck="#867358", house=None, house_paint="#D9CCAC",
                                roof="#8F8B82", mast="#D6D0C2", sail="#7E6A52", text="#EDE6CF", net="#45402F")),
    "mary_ellen": dict(Id="MaryEllen", export="ship_launch", kind="launch", design="blackboat", lit=False,
                       reg="SY 214", name="MARY ELLEN", port="STORNOWAY", weather=0.9, seed=214,
                       pal=dict(top="#141414", strake=None, boot="#141414", bottom="#3B2A22", rail="#25221F",
                                bulwark="#37332E", deck="#5A5043", house=None, house_paint="#575349",
                                roof="#3B3833", mast="#4A4038", sail=None, text="#E2DED2", net=None)),
    "gannet": dict(Id="Gannet", export="ship_schooner", kind="schooner", design="schooner", lit=True,
                   reg="SY 112", name="GANNET", port="STORNOWAY", weather=0.35, seed=112,
                   pal=dict(top="#131313", strake="#D8D2C2", boot="#131313", bottom="#7A3324", rail="#8B5A30",
                            bulwark="#CEC8B8", deck="#A08A66", house="#7C4C28", house_paint=None, roof="#C9C4B8",
                            mast="#9A6A3C", sail="#8C5E3E", text="#E7E3D7", net=None)),
    "lowestoft_star": dict(Id="LowestoftStar", export="ship_lowestoft_star", kind=None, kind_today="schooner",
                           design="drifter", lit=True, reg="LT 401", name="LOWESTOFT STAR", port="LOWESTOFT",
                           weather=0.6, seed=401,
                           pal=dict(top="#151515", strake="#C8C2B4", boot="#151515", bottom="#6E3022",
                                    rail="#1C1C1C", bulwark="#ADA593", deck="#7E6E58", house="#7A4B28",
                                    house_paint="#3B3B37", roof="#8E8A80", mast="#C8B48A", sail="#7E5A40",
                                    text="#EAE6DA", net=None, funnel="#B99A63", band="#8E2A20")),
    "iona_star": dict(Id="IonaStar", export="ship_steamer", kind="steamer", design="coaster", lit=True,
                      name="IONA STAR", port="GLASGOW", weather=0.45, seed=1971, cargo="hatches",
                      pal=dict(top="#171717", strake=None, boot="#8A2B22", bottom="#6B2A22", rail="#171717",
                               bulwark="#C9C3B5", deck="#6A3A2E", house=None, house_paint="#D9D5CB",
                               roof="#8D8A83", mast="#C2AA7E", sail=None, text="#EDEAE0", net=None,
                               funnel="#171717", band="#9A2A22", star="#E9E5DA", tarp="#4A574B")),
    "hendrika": dict(Id="Hendrika", export="ship_hendrika", kind="steamer", design="coaster", lit=True,
                     name="HENDRIKA", port="GRONINGEN", weather=0.35, seed=1958, cargo="timber",
                     pal=dict(top="#5A626B", strake=None, boot="#8A2B22", bottom="#6B2A22", rail="#5A626B",
                              bulwark="#D0CBC0", deck="#5D5A52", house=None, house_paint="#DDD9CF",
                              roof="#8A8780", mast="#D4D0C6", sail=None, text="#F0EDE4", net=None,
                              funnel="#C4A246", band="#2F5A3E", star=None, tarp="#4A574B", timber="#B59B6E")),
}
ORDER = list(VESSELS)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


# ------------------------------------------------------------------ curves
def curve(pts):
    """Monotone cubic (Fritsch-Carlson) through (t, z) knots; a repeated t is a step (left, then right value)."""
    pts = [(float(t), float(z)) for t, z in pts]
    runs, cur = [], [pts[0]]
    for p in pts[1:]:
        if p[0] <= cur[-1][0] + 1e-12:
            runs.append(cur)
            cur = [p]
        else:
            cur.append(p)
    runs.append(cur)
    segs = []
    for run in runs:
        ts = [p[0] for p in run]
        zs = [p[1] for p in run]
        n = len(run)
        if n == 1:
            segs.append((ts, zs, [0.0]))
            continue
        d = [(zs[i + 1] - zs[i]) / (ts[i + 1] - ts[i]) for i in range(n - 1)]
        m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else 2.0 / (1.0 / d[i - 1] + 1.0 / d[i]) for i in range(1, n - 1)] \
            + [d[-1]]
        segs.append((ts, zs, m))

    def f(t):
        for k, (ts, zs, m) in enumerate(segs):
            last = k == len(segs) - 1
            if t <= ts[-1] or last:
                if t <= ts[0] or len(ts) == 1:
                    return zs[0]
                if t >= ts[-1]:
                    return zs[-1]
                i = max(j for j in range(len(ts) - 1) if ts[j] <= t)
                h = ts[i + 1] - ts[i]
                s = (t - ts[i]) / h
                h00, h10 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s
                h01, h11 = -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
                return h00 * zs[i] + h10 * h * m[i] + h01 * zs[i + 1] + h11 * h * m[i + 1]
        return segs[-1][1][-1]
    return f


# ------------------------------------------------------------------ mesh core
class Mesh:
    """Faces with per-corner (a, b) metric coordinates on their UV island."""

    def __init__(self):
        self.v, self.f, self.fi, self.fab, self.fs, self.fc = [], [], [], [], [], []
        self.isl, self.shared, self.ncomp = [], {}, 0
        self.empties, self.meta = {}, {}

    def vert(self, p):
        self.v.append((float(p[0]), float(p[1]), float(p[2])))
        return len(self.v) - 1

    def comp(self):
        self.ncomp += 1
        return self.ncomp - 1

    def island(self, kind, **kw):
        if kind in SHARED:
            if kind not in self.shared:
                self.isl.append(dict(kind=kind, shared=True))
                self.shared[kind] = len(self.isl) - 1
            return self.shared[kind]
        self.isl.append(dict(kind=kind, shared=False, **kw))
        return len(self.isl) - 1

    def face(self, vids, isl, ab, comp, smooth=False):
        self.f.append(list(vids))
        self.fi.append(isl)
        self.fab.append([(float(a), float(b)) for a, b in ab])
        self.fs.append(bool(smooth))
        self.fc.append(comp)

    def tris(self):
        return sum(len(f) - 2 for f in self.f)


def basis_z(axis, hint=(1.0, 0.0, 0.0)):
    """3x3 with columns x, y, z; z along axis, x as close to hint as possible."""
    z = np.asarray(axis, float)
    z = z / np.linalg.norm(z)
    h = np.asarray(hint, float)
    if abs(np.dot(h / np.linalg.norm(h), z)) > 0.95:
        h = np.array([0.0, 1.0, 0.0]) if abs(z[1]) < 0.9 else np.array([0.0, 0.0, 1.0])
    x = h - np.dot(h, z) * z
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.column_stack([x, y, z])


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1.0, 0, 0], [0, c, -s], [0, s, c]])


def ear_clip(p2):
    """Triangulate a simple polygon given as 2D points; returns index triples."""
    n = len(p2)
    if n < 3:
        return []
    area = sum(p2[i][0] * p2[(i + 1) % n][1] - p2[(i + 1) % n][0] * p2[i][1] for i in range(n))
    idx = list(range(n)) if area > 0 else list(range(n))[::-1]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def inside(p, a, b, c):
        return cross(a, b, p) >= -1e-12 and cross(b, c, p) >= -1e-12 and cross(c, a, p) >= -1e-12

    tris, guard = [], 0
    while len(idx) > 3 and guard < 20000:
        guard += 1
        best = None
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = p2[i0], p2[i1], p2[i2]
            cr = cross(a, b, c)
            if cr <= 1e-12:
                continue
            if any(inside(p2[j], a, b, c) for j in idx if j not in (i0, i1, i2)
                   and p2[j] not in (a, b, c)):
                continue
            best = k
            break
        if best is None:        # degenerate sliver: clip the flattest corner anyway
            best = min(range(len(idx)), key=lambda k: abs(cross(p2[idx[k - 1]], p2[idx[k]],
                                                                p2[idx[(k + 1) % len(idx)]])))
        k = best
        tris.append((idx[k - 1], idx[k], idx[(k + 1) % len(idx)]))
        idx.pop(k)
    tris.append(tuple(idx))
    return tris


def newell(pts):
    n = np.zeros(3)
    for i in range(len(pts)):
        a, b = np.asarray(pts[i]), np.asarray(pts[(i + 1) % len(pts)])
        n += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
    ln = np.linalg.norm(n)
    return n / ln if ln > 1e-12 else np.array([0, 0, 1.0])


def cap(m, vids, isl, comp, abf, smooth=False):
    """Triangulated polygon cap over existing vertices; abf(vertex position) -> (a, b)."""
    pts = [m.v[i] for i in vids]
    n = newell(pts)
    u = basis_z(n)
    p2 = [tuple(np.dot(u[:, :2].T, np.asarray(p))) for p in pts]
    for i0, i1, i2 in ear_clip(p2):
        tri = [vids[i0], vids[i1], vids[i2]]
        m.face(tri, isl, [abf(m.v[i]) for i in tri], comp, smooth)


# ------------------------------------------------------------------ primitives (each a closed shell)
def box(m, c, size, kind, top=None, bottom="hidden", R=None, taper=(0.0, 0.0), windows=None, part="",
        color=None, top_color=None, **kw):
    """Box standing on c (base centre), local x/y/z = size; taper shrinks the top per side. One island per face.
    windows: {face: [dict(a0, b0, a1, b1, round=False, lit=True, door=False)]} in that face's (a, b) metres,
    a to the right as seen from outside, b up from the base."""
    sx, sy, sz = size
    R = np.eye(3) if R is None else np.asarray(R)
    o = np.asarray(c, float)
    tx, ty = taper
    bot = [(-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2)]
    tp = [(-sx / 2 + tx, -sy / 2 + ty), (sx / 2 - tx, -sy / 2 + ty), (sx / 2 - tx, sy / 2 - ty),
          (-sx / 2 + tx, sy / 2 - ty)]
    loc = [(x, y, 0.0) for x, y in bot] + [(x, y, sz) for x, y in tp]
    vid = [m.vert(o + R @ np.array(p)) for p in loc]
    cp = m.comp()
    abf = {"+x": lambda p: (p[1] + sy / 2, p[2]), "-x": lambda p: (sy / 2 - p[1], p[2]),
           "+y": lambda p: (sx / 2 - p[0], p[2]), "-y": lambda p: (p[0] + sx / 2, p[2]),
           "+z": lambda p: (p[0] + sx / 2, p[1] + sy / 2), "-z": lambda p: (p[0], p[1])}
    quads = {"+x": [1, 2, 6, 5], "-x": [3, 0, 4, 7], "+y": [2, 3, 7, 6], "-y": [0, 1, 5, 4],
             "+z": [4, 5, 6, 7], "-z": [0, 3, 2, 1]}
    sizes = {"+x": (sy, sz), "-x": (sy, sz), "+y": (sx, sz), "-y": (sx, sz), "+z": (sx, sy), "-z": (sx, sy)}
    for key, q in quads.items():
        k = top if key == "+z" and top else (bottom if key == "-z" else kind)
        col = top_color if key == "+z" and top_color else color
        isl = m.island(k, part=part, face=key, size=sizes[key], color=col,
                       windows=(windows or {}).get(key, []), **kw)
        m.face([vid[i] for i in q], isl, [abf[key](loc[i]) for i in q], cp)
    return vid


def ring_pts(o, R, r, segs, ellipse=(1.0, 1.0), z=0.0, a0=0.0):
    return [o + R @ np.array([r * ellipse[0] * math.cos(a0 + 2 * math.pi * i / segs),
                              r * ellipse[1] * math.sin(a0 + 2 * math.pi * i / segs), z]) for i in range(segs)]


def cyl(m, p0, p1, r0, r1, segs, kind, cap0="hidden", cap1="hidden", part="", color=None, smooth=True,
        ellipse=(1.0, 1.0), R=None, a0=0.0, **kw):
    """Closed (possibly elliptic, tapered) cylinder p0 -> p1. Angle 0 is the frame's +x (world +x for a vertical
    one), increasing toward +y. The side is one strip island: a = arc length, b = distance from p0."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    L = float(np.linalg.norm(p1 - p0))
    R = basis_z(p1 - p0) if R is None else np.asarray(R)
    rb = [m.vert(p) for p in ring_pts(p0, R, r0, segs, ellipse, a0=a0)]
    rt = [m.vert(p) for p in ring_pts(p0, R, r1, segs, ellipse, z=L, a0=a0)]
    cp = m.comp()
    circ = 2 * math.pi * 0.5 * (r0 + r1) * 0.5 * (ellipse[0] + ellipse[1])
    isl = m.island(kind, part=part, face="side", size=(circ, L), color=color, **kw)
    for i in range(segs):
        j = (i + 1) % segs
        a_i, a_j = circ * i / segs, circ * (i + 1) / segs
        m.face([rb[i], rb[j], rt[j], rt[i]], isl, [(a_i, 0), (a_j, 0), (a_j, L), (a_i, L)], cp, smooth)
    for ring, k, sgn in ((rb, cap0, -1), (rt, cap1, 1)):
        ci = m.island(k, part=part, face="cap", size=(2 * r0, 2 * r0), color=color, **kw)
        for i in range(1, segs - 1):
            tri = [ring[0], ring[i], ring[i + 1]]
            m.face(tri, ci, [(sgn * float(np.dot(np.asarray(m.v[t]) - p0, R[:, 0])),
                              float(np.dot(np.asarray(m.v[t]) - p0, R[:, 1]))) for t in tri], cp)
    return rb, rt


def rod(m, p0, p1, r=0.015, kind="rope"):
    """Rigging: a closed triangular prism (8 triangles)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    R = basis_z(p1 - p0)
    a = [m.vert(p) for p in ring_pts(p0, R, r, 3)]
    b = [m.vert(p) for p in ring_pts(p1, R, r, 3)]
    cp = m.comp()
    isl = m.island(kind)
    for i in range(3):
        j = (i + 1) % 3
        m.face([a[i], a[j], b[j], b[i]], isl, [(0, 0), (1, 0), (1, 1), (0, 1)], cp)
    m.face([a[0], a[2], a[1]], isl, [(0, 0), (1, 0), (0, 1)], cp)
    m.face([b[0], b[1], b[2]], isl, [(0, 0), (1, 0), (0, 1)], cp)


def lump(m, c, radii, kind, R=None, nu=10, nv=6, seed=0, amp=0.1, flat=0.0, part="", color=None, **kw):
    """Closed, noisy ellipsoid (net pile, furled sail, coil). flat > 0 flattens the underside at -flat * rz."""
    rng = np.random.default_rng(seed)
    R = np.eye(3) if R is None else np.asarray(R)
    o = np.asarray(c, float)
    rx, ry, rz = radii
    rm = (rx + ry + rz) / 3
    rings = []
    for j in range(1, nv):
        lat = -math.pi / 2 + math.pi * j / nv
        ring = []
        for i in range(nu):
            lon = 2 * math.pi * i / nu
            k = 1.0 + amp * rng.uniform(-1, 1)
            p = np.array([math.cos(lat) * math.cos(lon) * rx * k, math.cos(lat) * math.sin(lon) * ry * k,
                          math.sin(lat) * rz * k])
            if flat > 0:
                p[2] = max(p[2], -flat * rz)
            ring.append(m.vert(o + R @ p))
        rings.append((lat, ring))
    zb = -flat * rz if flat > 0 else -rz
    pb, pt = m.vert(o + R @ np.array([0, 0, zb])), m.vert(o + R @ np.array([0, 0, rz]))
    cp = m.comp()
    isl = m.island(kind, part=part, face="all", size=(2 * math.pi * rm, math.pi * rm), color=color, **kw)
    for (la0, r0), (la1, r1) in zip(rings, rings[1:]):
        for i in range(nu):
            j = (i + 1) % nu
            ab = [(rm * 2 * math.pi * i / nu, rm * la0), (rm * 2 * math.pi * (i + 1) / nu, rm * la0),
                  (rm * 2 * math.pi * (i + 1) / nu, rm * la1), (rm * 2 * math.pi * i / nu, rm * la1)]
            m.face([r0[i], r0[j], r1[j], r1[i]], isl, ab, cp, True)
    la0, r0 = rings[0]
    la1, r1 = rings[-1]
    for i in range(nu):
        j = (i + 1) % nu
        a_i, a_j = rm * 2 * math.pi * i / nu, rm * 2 * math.pi * (i + 1) / nu
        m.face([pb, r0[j], r0[i]], isl, [((a_i + a_j) / 2, -rm * math.pi / 2), (a_j, rm * la0), (a_i, rm * la0)],
               cp, True)
        m.face([pt, r1[i], r1[j]], isl, [((a_i + a_j) / 2, rm * math.pi / 2), (a_i, rm * la1), (a_j, rm * la1)],
               cp, True)


def prism(m, poly, depth, o, R, kind, cap_kind=None, cap_kind2=None, part="", color=None, smooth=False,
          centered=True, **kw):
    """Polygon (local x, y) extruded along local z by depth (centred on z = 0 if centered). Side strip + caps."""
    o, R = np.asarray(o, float), np.asarray(R, float)
    z0, z1 = (-depth / 2, depth / 2) if centered else (0.0, depth)
    lo = [m.vert(o + R @ np.array([x, y, z0])) for x, y in poly]
    hi = [m.vert(o + R @ np.array([x, y, z1])) for x, y in poly]
    cp = m.comp()
    n = len(poly)
    per = [0.0]
    for i in range(n):
        per.append(per[-1] + math.dist(poly[i], poly[(i + 1) % n]))
    isl = m.island(kind, part=part, face="side", size=(per[-1], depth), color=color, **kw)
    for i in range(n):
        j = (i + 1) % n
        m.face([lo[i], lo[j], hi[j], hi[i]], isl, [(per[i], 0), (per[i + 1], 0), (per[i + 1], depth),
                                                   (per[i], depth)], cp, smooth)
    for ring, k, sgn in ((lo, cap_kind2 or cap_kind or kind, -1), (hi, cap_kind or kind, 1)):
        ci = m.island(k, part=part, face="cap%+d" % sgn, size=(1, 1), color=color, **kw)
        for i0, i1, i2 in ear_clip([tuple(p) for p in poly]):
            tri = [ring[i0], ring[i1], ring[i2]]
            m.face(tri, ci, [(sgn * poly[i][0], poly[i][1]) for i in (i0, i1, i2)], cp)


def strake(m, H, side, y0, y1, z_of_y, n=36, h=0.12, t=0.06, kind="paint", color=None, part="strake"):
    """Rubbing strake / belting: a closed 4-sided sweep along the hull side at z_of_y(y), y0 -> y1."""
    ys = [y0 + (y1 - y0) * i / (n - 1) for i in range(n)]
    prof = [(-0.02, -h / 2), (t, -h * 0.4), (t, h * 0.4), (-0.02, h / 2)]
    per = [0.0]
    for k in range(4):
        per.append(per[-1] + math.dist(prof[k], prof[(k + 1) % 4]))
    rings, arc = [], [0.0]
    for i, y in enumerate(ys):
        z = z_of_y(y)
        x = H.half_out(y, z)
        rings.append([m.vert((side * (x + dx), y, z + dz)) for dx, dz in prof])
        if i:
            arc.append(arc[-1] + math.dist((ys[i - 1], z_of_y(ys[i - 1])), (y, z)))
    cp = m.comp()
    isl = m.island(kind, part=part, face="side%+d" % side, size=(arc[-1], per[-1]), color=color, no_rotate=True)
    for i in range(n - 1):
        for k in range(4):
            k1 = (k + 1) % 4
            m.face([rings[i][k], rings[i][k1], rings[i + 1][k1], rings[i + 1][k]], isl,
                   [(arc[i], per[k]), (arc[i], per[k + 1]), (arc[i + 1], per[k + 1]), (arc[i + 1], per[k])], cp)
    ci = m.island(kind, part=part, face="ends", size=(0.2, 0.2), color=color)
    for ring in (rings[0], rings[-1]):
        m.face(ring, ci, [(p[0], p[1]) for p in prof], cp)


LENS_FACING = {"NAV_masthead": (0, 1, 0), "NAV_port": (-1, 1, 0), "NAV_starboard": (1, 1, 0),
               "NAV_stern": (0, -1, 0), "DECK_work": (0, -1, -0.6), "DECK_aft": (0, 1, -0.6)}


def lantern(m, name, p, kind, size=(0.16, 0.14, 0.24)):
    """A navigation or deck light: a black lantern body with its lens on the side that shows (the arc the
    light covers), and the empty the game reads."""
    sx, sy, sz = size
    box(m, (p[0], p[1], p[2] - sz / 2), size, "black", top="black", bottom="black")
    f = np.asarray(LENS_FACING.get(name, (0, 1, 0)), float)
    f[2] = 0.0
    f /= np.linalg.norm(f)
    R = rot_z(math.atan2(f[1], f[0]) - math.pi / 2)              # local +y along the facing
    c = np.asarray(p, float) + f * (max(sx, sy) / 2 - 0.02)
    box(m, (c[0], c[1], p[2] - sz * 0.36), (sx * 0.8, 0.06, sz * 0.72), kind, top=kind, bottom=kind, R=R)
    m.empties[name] = tuple(float(x) for x in p)


# ------------------------------------------------------------------ hull
class Hull:
    """Lofted hull: rows from keel (h = 0) to rail top (h = 1) per station t (0 stern .. 1 bow), plus the bulwark's
    inner face and a cambered deck, closed by a stern and a stem cap. All lengths in metres, Blender axes."""

    def __init__(self, y_aft, L, B, keel, rail, deck, plan, p, stern_over=0.8, stern_pow=1.6, stem_rake=1.0,
                 stem_pow=1.6, kw=0.09, bt=0.07, camber=0.06, z_ref=None, rows=None, stations=26, steps=(),
                 s=1.0):
        self.s = s
        sc = lambda f: (lambda t: WL + (f(t) - WL) * s)     # noqa: E731  scale about the waterline
        self.y_aft, self.L, self.B = y_aft * s, L * s, B * s
        self.keel, self.rail, self.deck = sc(curve(keel)), sc(curve(rail)), sc(curve(deck))
        self.plan, self.p = curve(plan), curve(p)
        self.stern_over, self.stern_pow = stern_over * s, stern_pow
        self.stem_rake, self.stem_pow = stem_rake * s, stem_pow
        self.kw, self.bt, self.camber = kw * s, bt * s, camber * s
        self.z_ref = None if z_ref is None else WL + (z_ref - WL) * s
        self.rows = rows or [0, .03, .08, .15, .25, .37, .5, .63, .76, .88, 1.0]
        self.nst, self.steps = stations, steps

    # parametrisation
    def hb(self, t):
        return self.B / 2 * self.plan(t)

    def y_row(self, t, h):
        ya = self.y_aft + self.stern_over * (1 - h) ** self.stern_pow
        yf = self.y_aft + self.L - self.stem_rake * (1 - h) ** self.stem_pow
        return ya + t * (yf - ya)

    def z_row(self, t, h):
        k = self.keel(t)
        return k + h * (self.rail(t) - k)

    def x_out(self, t, z):
        k, hb = self.keel(t), self.hb(t)
        zr = self.rail(t) if self.z_ref is None else min(self.z_ref, self.rail(t))
        kw = min(self.kw, hb * 0.9)
        q = min(max((z - k) / max(zr - k, 1e-6), 0.0), 1.0)
        return kw + (hb - kw) * (1 - (1 - q) ** self.p(t))

    def t_of_y(self, y):
        return min(max((y - self.y_aft) / self.L, 0.0), 1.0)

    # placement helpers (along the rail row)
    def deck_z(self, y):
        return self.deck(self.t_of_y(y))

    def rail_z(self, y):
        return self.rail(self.t_of_y(y))

    def half_out(self, y, z):
        return self.x_out(self.t_of_y(y), z)

    def half_in(self, y):
        t = self.t_of_y(y)
        return self.x_out(t, self.deck(t)) - self.bt

    def stations(self):
        n = self.nst
        ts = [0.55 * (i / (n - 1)) + 0.45 * (0.5 - 0.5 * math.cos(math.pi * i / (n - 1))) for i in range(n)]
        for st in self.steps:
            ts = [t for t in ts if abs(t - st) > 0.012] + [st - 0.002, st + 0.002]
        return sorted(ts)

    def build(self, m, kinds=None, colors=None, part="hull", texts=None, transom_texts=None):
        """kinds: override map for the hull's island kinds (a lifeboat paints everything 'paint')."""
        K = dict(hull="hull", rail="rail", bulwark="bulwark", deck="deck", brk="break", transom="transom")
        K.update(kinds or {})
        C = colors or {}
        rows, R = self.rows, len(self.rows)
        ts = self.stations()
        rings = []
        for t in ts:
            sp = []
            for h in rows:
                y, z = self.y_row(t, h), self.z_row(t, h)
                sp.append((self.x_out(t, z), y, z))
            y1, zr, zd = self.y_row(t, 1.0), self.rail(t), self.deck(t)
            xr, xd = sp[-1][0], self.x_out(t, zd)
            bt = min(self.bt, 0.45 * min(xr, xd))
            ring = sp + [(xr - bt, y1, zr), (xd - bt, y1, zd), (0.0, y1, zd + self.camber * xd / (self.B / 2))]
            ring += [(-ring[R + 1][0], y1, zd), (-ring[R][0], y1, zr)] + [(-x, y, z) for x, y, z in sp[::-1]]
            rings.append([m.vert(p) for p in ring])
        cp = m.comp()
        nr = len(rings[0])
        hk = dict(texts=texts or [], hull=self)
        isl = {"hull_s": m.island(K["hull"], part=part, face="s", no_rotate=True, color=C.get("hull"),
                                  **(dict(side="s", **hk) if K["hull"] == "hull" else {})),
               "hull_p": m.island(K["hull"], part=part, face="p", no_rotate=True, color=C.get("hull"),
                                  **(dict(side="p", **hk) if K["hull"] == "hull" else {})),
               "rail_s": m.island(K["rail"], part=part, face="rail_s", color=C.get("rail")),
               "rail_p": m.island(K["rail"], part=part, face="rail_p", color=C.get("rail")),
               "bulw_s": m.island(K["bulwark"], part=part, face="bulw_s", color=C.get("bulwark"), hull=self),
               "bulw_p": m.island(K["bulwark"], part=part, face="bulw_p", color=C.get("bulwark"), hull=self),
               "deck": m.island(K["deck"], part=part, face="deck", color=C.get("deck"), hull=self)}
        brk = {}
        for j in range(len(rings) - 1):
            ra, rb = rings[j], rings[j + 1]
            for k in range(nr):
                k1 = (k + 1) % nr
                q = [ra[k], ra[k1], rb[k1], rb[k]]
                P = [m.v[i] for i in q]
                if k < R - 1 or k == nr - 1:
                    key, ab = "hull_s", [(p[1], p[2]) for p in P]
                elif k > R + 4 and k < nr - 1:
                    key, ab = "hull_p", [(-p[1], p[2]) for p in P]
                elif k == R - 1:
                    key, ab = "rail_s", [(p[1], p[0]) for p in P]
                elif k == R + 4:
                    key, ab = "rail_p", [(p[1], -p[0]) for p in P]
                elif k == R:
                    key, ab = "bulw_s", [(-p[1], p[2]) for p in P]
                elif k == R + 3:
                    key, ab = "bulw_p", [(p[1], p[2]) for p in P]
                else:
                    nz = newell(P)
                    if abs(nz[2]) < 0.6:
                        # a deck step: higher aft -> the face looks forward (seen from ahead, right = -x)
                        sgn = -1.0 if self.deck(ts[j]) > self.deck(ts[j + 1]) else 1.0
                        if j not in brk:
                            brk[j] = m.island(K["brk"], part=part, face="break%d" % j, color=C.get("bulwark"))
                        isl_id = brk[j]
                        m.face(q, isl_id, [(sgn * p[0], p[2]) for p in P], cp, False)
                        continue
                    key, ab = "deck", [(p[0], p[1]) for p in P]
                m.face(q, isl[key], ab, cp, True)
        st = m.island(K["transom"], part=part, face="transom", texts=transom_texts or [], hull=self,
                      color=C.get("hull"), no_rotate=True)
        cap(m, rings[0], st, cp, lambda p: (p[0], p[2]))
        bw = m.island(K["transom"], part=part, face="stem", hull=self, color=C.get("hull"))
        cap(m, rings[-1], bw, cp, lambda p: (-p[0], p[2]))
        return self


# ------------------------------------------------------------------ windows
def win_row(w, n, ww, b0, b1, margin=None, lit=True, round_=False, gap=None):
    """n windows of width ww across a face of width w, from b0 to b1 (m)."""
    if n <= 0:
        return []
    if gap is None:
        margin = (w - n * ww) / (n + 1) if margin is None else margin
        gap = (w - 2 * margin - n * ww) / max(n - 1, 1) if n > 1 else 0.0
    else:
        margin = (w - n * ww - (n - 1) * gap) / 2
    return [dict(a0=margin + i * (ww + gap), b0=b0, a1=margin + i * (ww + gap) + ww, b1=b1, lit=lit,
                 round=round_) for i in range(n)]


def door(a0, w, h, b0=0.05):
    return dict(a0=a0, b0=b0, a1=a0 + w, b1=b0 + h, door=True, lit=False)


# ------------------------------------------------------------------ shared design helpers
def merge(m, sub, o=(0, 0, 0), R=None):
    """Append another Mesh (its own islands) transformed by R then o."""
    R = np.eye(3) if R is None else np.asarray(R)
    off = len(m.v)
    for p in sub.v:
        m.v.append(tuple(float(x) for x in (np.asarray(o, float) + R @ np.asarray(p))))
    remap = {}
    for i, isl in enumerate(sub.isl):
        if isl["shared"]:
            remap[i] = m.island(isl["kind"])
        else:
            m.isl.append(dict(isl))
            remap[i] = len(m.isl) - 1
    cbase = m.ncomp
    for f, fi, ab, fs, fc in zip(sub.f, sub.fi, sub.fab, sub.fs, sub.fc):
        m.f.append([v + off for v in f])
        m.fi.append(remap[fi])
        m.fab.append(list(ab))
        m.fs.append(fs)
        m.fc.append(fc + cbase)
    m.ncomp += sub.ncomp


def frame_yz():
    """Local x -> world y, local y -> world z, local z -> world x (a sail or board in the centre plane)."""
    return np.array([[0, 0, 1.0], [1.0, 0, 0], [0, 1.0, 0]])


def along(p0, p1):
    """Frame whose local y runs p0 -> p1 (for lumps lying along a spar)."""
    d = np.asarray(p1, float) - np.asarray(p0, float)
    d /= np.linalg.norm(d)
    x = np.array([1.0, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 0, 1.0])
    x = x - np.dot(x, d) * d
    x /= np.linalg.norm(x)
    return np.column_stack([x, d, np.cross(x, d)])


def mast(m, H, y, top, r0, r1, color, segs=8, x=0.0):
    zd = H.deck_z(y)
    cyl(m, (x, y, zd - 0.12), (x, y, top), r0, r1, segs, "mast", cap1="black", color=color, part="mast")
    return zd


def shrouds(m, H, y, z_top, n=2, spread=0.32, r=0.014):
    for side in (-1, 1):
        for k in range(n):
            yc = y - 0.25 - k * spread
            zr = H.rail_z(yc)
            xr = H.half_out(yc, zr) - 0.03
            rod(m, (side * 0.08, y, z_top), (side * xr, yc, zr), r)


def tyre(m, H, y, side, drop=0.55, r=0.26, th=0.14):
    z = H.rail_z(y) - drop
    x = side * (H.half_out(y, z) + th / 2 + 0.005)
    cyl(m, (x - side * th / 2, y, z), (x + side * th / 2, y, z), r, r, 10, "rubber", cap0="rubber", cap1="rubber",
        smooth=True)
    rod(m, (side * (H.half_out(y, H.rail_z(y)) - 0.02), y, H.rail_z(y)), (x, y, z + r * 0.9), 0.012)


def sidelights(m, H, xs, y, z, lit, screen=True):
    for name, side, k in (("NAV_port", -1, "lamp_r"), ("NAV_starboard", 1, "lamp_g")):
        lantern(m, name, (side * xs, y, z), k if lit else "lamp_dark")
        if screen:      # the inboard screen board behind the lamp
            box(m, (side * (xs - 0.11), y - 0.05, z - 0.2), (0.03, 0.5, 0.36), "black", top="black")


def wheelhouse(m, H, y0, y1, w, hgt, kind, color, roof_col, lit, n_front=3, n_side=2, win=(0.48, 0.55),
               part="wheelhouse", taper=(0.0, 0.0), z0=None, roof=True, back_door=True):
    zb = (H.deck_z((y0 + y1) / 2) - 0.08) if z0 is None else z0
    L = y1 - y0
    ww, wh = win
    b0 = hgt * 0.62
    b1 = min(b0 + wh, hgt - 0.12)
    front = win_row(w, n_front, ww * min(1.0, w / (n_front * ww + 0.2 * (n_front + 1))), b0, b1, lit=lit)
    sw = min(ww, (L * 0.6) / max(n_side, 1) - 0.08)
    s_fwd = [dict(a0=L - 0.12 - (i + 1) * sw - i * 0.1, b0=b0, a1=L - 0.12 - i * sw - i * 0.1, b1=b1, lit=lit)
             for i in range(n_side)]                      # +x face: forward is at high a
    s_port = [dict(a0=L - d["a1"], b0=b0, a1=L - d["a0"], b1=b1, lit=lit) for d in s_fwd]
    back = [door(w / 2 - 0.32, 0.64, min(1.75, hgt - 0.2))] if back_door else []
    wins = {"+y": front, "+x": s_fwd, "-x": s_port, "-y": back}
    box(m, (0, (y0 + y1) / 2, zb), (w, L, hgt), kind, top="roof", color=color, top_color=roof_col, windows=wins,
        part=part, taper=taper)
    zr = zb + hgt
    if roof:
        box(m, (0, (y0 + y1) / 2, zr), (w + 0.14, L + 0.14, 0.07), "roof", top="roof", color=roof_col,
            part=part + "_roof")
        zr += 0.07
    return zb, zr


# ------------------------------------------------------------------ the designs
def ringnetter_hull(s=1.0, stations=26, rows=None):
    return Hull(y_aft=-6.5, L=13.0, B=3.9,
                keel=[(0, -1.0), (0.35, -1.2), (0.75, -1.0), (0.92, -0.55), (1.0, -0.2)],
                rail=[(0, 1.95), (0.25, 1.8), (0.5, 1.75), (0.75, 1.9), (1.0, 2.33)],
                deck=[(0, 1.47), (0.25, 1.3), (0.5, 1.25), (0.75, 1.38), (1.0, 1.78)],
                plan=[(0, 0.10), (0.06, 0.55), (0.18, 0.86), (0.4, 1.0), (0.55, 1.0), (0.75, 0.86), (0.9, 0.52),
                      (1.0, 0.02)],
                p=[(0, 2.2), (0.4, 2.8), (0.8, 2.0), (1, 1.3)],
                stern_over=0.9, stern_pow=1.6, stem_rake=1.3, stem_pow=1.8, kw=0.09, bt=0.07, camber=0.06,
                stations=stations, rows=rows, s=s)


def d_ringnetter(m, V):
    """Ring-netter MFV, 13 m: varnished wheelhouse aft, foremast and derrick, mizzen with a steadying sail, the
    net piled on the stern, registration on both bows."""
    P, lit = V["pal"], V["lit"]
    H = ringnetter_hull(stations=40, rows=[0, .02, .05, .1, .16, .24, .33, .43, .53, .63, .73, .82, .9, .96, 1.0])
    H.build(m, texts=[dict(text=V["reg"], y=4.3, z=1.28, h=0.42, font="reg"),
                      dict(text=V["name"], y=-4.95, z=1.3, h=0.18, font="name")])
    m.meta["hull"] = H
    for side in (-1, 1):
        strake(m, H, side, -5.7, 5.9, lambda y: H.deck_z(y) + 0.02, color=P["strake"] or P["rail"])
    hk, hc = ("varnish", P["house"]) if P["house"] else ("paint", P["house_paint"])
    y0, y1, w = -4.4, -2.4, 1.9
    zb, zr = wheelhouse(m, H, y0, y1, w, 2.1, hk, hc, P["roof"], lit)
    cyl(m, (0.55, -3.95, zr - 0.03), (0.55, -3.95, zr + 1.0), 0.085, 0.08, 8, "black", cap1="soot")   # the lum
    if V.get("radar"):
        cyl(m, (0, -2.95, zr - 0.02), (0, -2.95, zr + 0.32), 0.07, 0.06, 6, "metal", color="#2F3234")
        box(m, (0, -2.95, zr + 0.32), (1.1, 0.12, 0.09), "metal", color="#D4D1C8", top_color="#D4D1C8")
    ym = 1.95
    zd = mast(m, H, ym, 7.3, 0.11, 0.07, P["mast"])
    rod(m, (0, ym - 0.1, 5.6), (0, ym + 0.1, 5.6), 0.04, "black")
    cyl(m, (-0.55, ym, 5.6), (0.55, ym, 5.6), 0.035, 0.03, 6, "mast", color=P["mast"])     # cross-tree
    boom_end = np.array([0, -1.55, 3.75])
    cyl(m, (0, ym - 0.13, zd + 0.8), boom_end, 0.065, 0.05, 8, "mast", color=P["mast"])    # derrick, topped
    rod(m, boom_end, (0, ym, 6.6))
    rod(m, (0, ym + 0.06, 7.0), (0, 6.42, H.rail_z(6.42)))                               # forestay
    shrouds(m, H, ym, 6.6, 2)
    yz = -4.62
    mast(m, H, yz, 5.0, 0.08, 0.05, P["mast"])
    sail = [(yz - 0.06, 2.45), (yz - 0.06, 4.85), (-6.2, 2.6)]
    prism(m, sail, 0.03, (0, 0, 0), frame_yz(), "canvas", color=P["sail"], part="sail")
    cyl(m, (0, yz - 0.05, 2.45), (0, -6.3, 2.5), 0.04, 0.035, 6, "mast", color=P["mast"])
    rod(m, (0, yz, 4.95), (0, y0 + 0.2, zr))
    yn = -5.55
    lump(m, (0, yn, H.deck_z(yn) + 0.1), (0.98, 0.7, 0.42), "net", nu=14, nv=7, seed=V["seed"], amp=0.13,
         flat=0.3, color=P["net"], part="net")
    box(m, (0, 0.35, H.deck_z(0.35) - 0.06), (1.3, 1.3, 0.38), "paint", top="varnish", color=P["bulwark"],
        top_color=P["deck"], part="hatch")
    yw = -1.95
    box(m, (0, yw, H.deck_z(yw) - 0.05), (0.55, 0.45, 0.5), "metal", color="#2E3133", top_color="#2E3133")
    for side in (-1, 1):
        cyl(m, (side * 0.28, yw, H.deck_z(yw) + 0.32), (side * 0.52, yw, H.deck_z(yw) + 0.32), 0.16, 0.16, 8,
            "metal", cap0="metal", cap1="metal", color="#3A3B39")
        cyl(m, (side * 0.3, 5.3, H.deck_z(5.3) - 0.05), (side * 0.3, 5.3, H.deck_z(5.3) + 0.42), 0.07, 0.07, 6,
            "black", cap1="black")
    for k, yb in enumerate((-1.0, -0.55)):
        box(m, (0.95, yb, H.deck_z(yb) - 0.02), (0.6, 0.4, 0.3), "paint", top="paint", color="#7E6A4E",
            part="fishbox")
    for y in (-2.7, 0.2, 2.9):
        for side in (-1, 1):
            tyre(m, H, y, side)
    sidelights(m, H, w / 2 + 0.08, y1 - 0.14, zb + 1.5, lit, screen=False)
    lantern(m, "NAV_masthead", (0, ym + 0.13, 6.95), "lamp_w" if lit else "lamp_dark")
    lantern(m, "NAV_stern", (0, -6.28, H.rail_z(-6.28) + 0.22), "lamp_w" if lit else "lamp_dark")
    rod(m, (0, -6.28, H.rail_z(-6.28) - 0.05), (0, -6.28, H.rail_z(-6.28) + 0.1), 0.02, "black")
    lantern(m, "DECK_work", (0, ym - 0.16, 4.4), "lamp_w" if lit else "lamp_dark", size=(0.2, 0.12, 0.16))


def d_blackboat(m, V):
    """The black boat: the Catriona, the Mary Ellen's sister off the same Fraserburgh yard, rebuilt by Ross as
    SY 214. The ring-netter's lines at 10 m, tarred black, an older and smaller wheelhouse, a bare mast, no
    lights burning."""
    P = V["pal"]
    s = 10.0 / 13.0
    H = ringnetter_hull(s=s, stations=40, rows=[0, .02, .05, .1, .16, .24, .33, .43, .53, .63, .73, .82, .9, .96, 1.0])
    H.build(m, texts=[dict(text=V["reg"], y=3.0, z=0.87, h=0.46, font="reg"),
                      dict(text=V["name"], y=-3.75, z=1.08, h=0.15, font="name")])
    m.meta["hull"] = H
    for side in (-1, 1):
        strake(m, H, side, -4.35, 4.5, lambda y: H.deck_z(y) + 0.02, h=0.1, t=0.05, color="#2A2622")
    y0, y1, w = -3.35, -2.0, 1.36
    zb, zr = wheelhouse(m, H, y0, y1, w, 1.86, "paint", P["house_paint"], P["roof"], False, n_front=2, n_side=1,
                        win=(0.34, 0.34), taper=(0.03, 0.03))
    box(m, (0, (y0 + y1) / 2, zr), (w + 0.04, y1 - y0 + 0.04, 0.09), "paint", top="roof", color=P["house_paint"],
        top_color=P["roof"], part="roof_rim")
    zr += 0.09
    cyl(m, (0.38, -3.0, zr - 0.05), (0.38, -3.0, zr + 0.8), 0.07, 0.065, 8, "metal", cap1="soot",
        color="#5A3A26")                                                               # rusted lum
    ym = 1.42
    zd = mast(m, H, ym, 5.6, 0.09, 0.06, P["mast"])
    rod(m, (0, ym + 0.05, 5.4), (0, 4.95, H.rail_z(4.95)))
    shrouds(m, H, ym, 5.1, 1)
    rod(m, (0, ym - 0.05, 5.3), (0, y1, zr))
    cyl(m, (0, ym - 0.1, zd + 0.7), (0, -0.9, zd + 1.05), 0.05, 0.045, 6, "mast", color=P["mast"])   # short boom
    box(m, (0, 0.3, H.deck_z(0.3) - 0.06), (1.0, 1.0, 0.3), "paint", top="tarp", color=P["bulwark"],
        top_color="#2D2F2A", part="hatch")
    for k, (x, yb) in enumerate(((0.55, -1.0), (0.55, -1.42), (-0.6, -1.2))):
        box(m, (x, yb, H.deck_z(yb) - 0.02), (0.5, 0.36, 0.26 + 0.04 * k), "paint", top="paint",
            color="#5F5242", part="fishbox")
    lump(m, (-0.5, -3.95, H.deck_z(-3.95) + 0.08), (0.36, 0.36, 0.12), "canvas", nu=10, nv=4, seed=5, amp=0.06,
         flat=0.4, color="#4E4436", part="coil")
    yw = -1.6
    box(m, (0, yw, H.deck_z(yw) - 0.05), (0.42, 0.34, 0.4), "metal", color="#3A2E26", top_color="#3A2E26")
    for side in (-1, 1):
        cyl(m, (side * 0.22, yw, H.deck_z(yw) + 0.26), (side * 0.4, yw, H.deck_z(yw) + 0.26), 0.12, 0.12, 8,
            "metal", cap0="metal", cap1="metal", color="#3C3029")
        cyl(m, (side * 0.24, 4.1, H.deck_z(4.1) - 0.05), (side * 0.24, 4.1, H.deck_z(4.1) + 0.34), 0.055, 0.055,
            6, "black", cap1="black")
        for y in (-1.9, 1.2):
            tyre(m, H, y, side, drop=0.42, r=0.21, th=0.12)
    lump(m, (0.45, 3.3, H.deck_z(3.3) + 0.07), (0.3, 0.3, 0.1), "canvas", nu=12, nv=5, seed=11, amp=0.06,
         flat=0.4, color="#4E4436", part="coil2")                                          # anchor warp
    cyl(m, (-0.55, 0.9, H.deck_z(0.9) - 0.05), (-0.55, 0.9, H.deck_z(0.9) + 0.7), 0.06, 0.05, 8, "metal",
        cap1="metal", color="#3C3029")                                                    # hand pump
    rod(m, (-0.55, 0.9, H.deck_z(0.9) + 0.66), (-0.55, 1.35, H.deck_z(0.9) + 0.8), 0.02, "black")
    sidelights(m, H, w / 2 + 0.07, y1 - 0.12, zb + 1.3, False, screen=False)
    lantern(m, "NAV_masthead", (0, ym + 0.11, 5.3), "lamp_dark")
    lantern(m, "NAV_stern", (0, -4.85, H.rail_z(-4.85) + 0.2), "lamp_dark")
    lantern(m, "DECK_work", (0, ym - 0.13, 3.4), "lamp_dark", size=(0.18, 0.1, 0.14))


def d_schooner(m, V):
    """Gaff schooner, 19 m over the bowsprit: two masts, sails furled on their booms, a deckhouse for passengers,
    a doghouse over the wheel, counter stern with the name on it."""
    P, lit = V["pal"], V["lit"]
    H = Hull(y_aft=-9.5, L=16.4, B=4.8,
             keel=[(0, -1.55), (0.25, -1.85), (0.6, -1.75), (0.85, -1.2), (1.0, -0.1)],
             rail=[(0, 2.05), (0.5, 1.78), (1, 2.55)], deck=[(0, 1.62), (0.5, 1.33), (1, 2.05)],
             plan=[(0, 0.48), (0.08, 0.7), (0.25, 0.92), (0.5, 1.0), (0.7, 0.9), (0.88, 0.56), (1.0, 0.02)],
             p=[(0, 1.8), (0.45, 2.4), (0.8, 1.8), (1, 1.25)], stern_over=2.4, stern_pow=1.25, stem_rake=2.2,
             stem_pow=1.5, kw=0.1, bt=0.08, camber=0.07, stations=40, rows=[0, .02, .05, .1, .16, .24, .33, .43, .53, .63, .73, .82, .9, .96, 1.0])
    H.build(m, texts=[dict(text=V["reg"], y=5.0, z=1.42, h=0.42, font="reg")],
            transom_texts=[dict(text=V["name"], x=0.0, z=1.68, h=0.22, font="name"),
                           dict(text=V["port"], x=0.0, z=1.4, h=0.12, font="name")])
    m.meta["hull"] = H
    for side in (-1, 1):
        strake(m, H, side, -8.4, 6.1, lambda y: H.deck_z(y) + 0.04, color=P["rail"])
    hk, hc = "varnish", P["house"]
    # passenger deckhouse and the doghouse over the wheel
    dz = H.deck_z(-2.8) - 0.08
    L, w, hh = 3.2, 2.5, 1.38
    wins = {"+x": win_row(L, 3, 0.42, 0.68, 1.06, lit=lit), "-x": win_row(L, 3, 0.42, 0.68, 1.06, lit=lit),
            "+y": win_row(w, 2, 0.42, 0.68, 1.06, lit=lit), "-y": [door(w / 2 - 0.3, 0.6, 1.25)]}
    box(m, (0, -2.8, dz), (w, L, hh), hk, top="roof", color=hc, top_color=P["roof"], windows=wins, part="deckhouse")
    box(m, (0, -2.8, dz + hh), (w + 0.12, L + 0.12, 0.06), "roof", top="roof", color=P["roof"])
    box(m, (0, -2.4, dz + hh + 0.06), (0.8, 0.7, 0.22), hk, top="glass", color=hc)          # skylight
    zb, zr = wheelhouse(m, H, -8.1, -7.0, 1.4, 1.25, hk, hc, P["roof"], lit, n_front=2, n_side=1, win=(0.36, 0.3),
                        back_door=False)
    # masts, topmasts, bowsprit
    yf, ym = 2.7, -0.75
    zf = mast(m, H, yf, 11.6, 0.15, 0.11, P["mast"], segs=10)
    cyl(m, (0, yf + 0.02, 11.2), (0, yf + 0.02, 13.6), 0.07, 0.045, 6, "mast", cap1="black", color=P["mast"])
    zm = mast(m, H, ym, 12.9, 0.16, 0.11, P["mast"], segs=10)
    cyl(m, (0, ym + 0.02, 12.5), (0, ym + 0.02, 15.0), 0.07, 0.045, 6, "mast", cap1="black", color=P["mast"])
    cyl(m, (0, 6.7, 2.43), (0, 9.49, 2.8), 0.11, 0.07, 8, "mast", cap1="black", color=P["mast"])
    # booms with the sails furled on them, gaffs lowered on top
    for (yg, y_end, z0, z1, top) in ((yf - 0.17, -0.25, zf + 1.35, zf + 1.5, 11.0), (ym - 0.18, -8.95, zm + 2.0,
                                                                                       zm + 2.3, 12.3)):
        p0, p1 = np.array([0, yg, z0]), np.array([0, y_end, z1])
        cyl(m, p0, p1, 0.09, 0.07, 8, "mast", cap1="black", color=P["mast"])
        mid = (p0 + p1) / 2 + np.array([0, 0, 0.27])
        lump(m, mid, (0.24, np.linalg.norm(p1 - p0) * 0.47, 0.3), "canvas", R=along(p0, p1), nu=10, nv=6,
             seed=int(abs(yg) * 10), amp=0.08, color=P["sail"], part="sail")
        g0, g1 = p0 + np.array([0, -0.05, 0.62]), p0 + (p1 - p0) * 0.62 + np.array([0, 0, 0.7])
        cyl(m, g0, g1, 0.065, 0.05, 6, "mast", cap1="black", color=P["mast"])
        rod(m, p1, (0, yg + 0.17, top))                                                   # topping lift
    lump(m, (0, 8.1, 2.95), (0.14, 1.15, 0.16), "canvas", R=along((0, 6.9, 2.5), (0, 9.4, 2.8)), nu=8, nv=4,
         seed=3, amp=0.06, color=P["sail"], part="jib")
    # rigging
    rod(m, (0, yf + 0.12, 11.4), (0, 9.46, 2.8))
    rod(m, (0, yf + 0.06, 13.4), (0, 9.4, 2.82))
    rod(m, (0, yf + 0.1, 10.2), (0, 6.75, H.rail_z(6.75)))
    rod(m, (0, yf - 0.1, 11.3), (0, ym + 0.12, 12.6))
    rod(m, (0, yf - 0.05, 13.4), (0, ym + 0.05, 14.8))
    shrouds(m, H, yf, 11.0, 3, spread=0.36)
    shrouds(m, H, ym, 12.3, 3, spread=0.36)
    for side in (-1, 1):
        zr2 = H.rail_z(-5.2)
        rod(m, (side * 0.1, ym, 12.0), (side * (H.half_out(-5.2, zr2) - 0.04), -5.2, zr2))
    # lights
    sidelights(m, H, 2.05, 2.3, 3.25, lit)
    lantern(m, "NAV_masthead", (0, yf + 0.18, 9.25), "lamp_w" if lit else "lamp_dark")
    lantern(m, "NAV_stern", (0, -9.33, H.rail_z(-9.33) + 0.22), "lamp_w" if lit else "lamp_dark")
    rod(m, (0, -9.33, H.rail_z(-9.33) - 0.05), (0, -9.33, H.rail_z(-9.33) + 0.1), 0.02, "black")
    lantern(m, "DECK_work", (0, ym + 0.2, zm + 2.7), "lamp_w" if lit else "lamp_dark", size=(0.2, 0.12, 0.16))
    # deck fittings: hatch, windlass, the dinghy upside down on the deckhouse
    box(m, (0, 0.95, H.deck_z(0.95) - 0.05), (1.2, 1.1, 0.35), "varnish", top="varnish", color=hc, part="hatch")
    box(m, (0, 5.6, H.deck_z(5.6) - 0.05), (0.9, 0.5, 0.4), "metal", color="#2E3133", top_color="#2E3133")
    dinghy = Mesh()
    Hull(y_aft=-1.3, L=2.6, B=1.2, keel=[(0, -0.05), (0.5, -0.12), (1, 0.05)], rail=[(0, 0.42), (0.5, 0.38),
                                                                                    (1, 0.5)],
         deck=[(0, 0.3), (0.5, 0.26), (1, 0.38)], plan=[(0, 0.6), (0.3, 1.0), (0.7, 0.9), (1, 0.03)],
         p=[(0, 1.8), (1, 1.4)], stern_over=0.1, stem_rake=0.4, kw=0.03, bt=0.03, camber=0.0, stations=10,
         rows=[0, .2, .5, .8, 1.0]).build(dinghy, kinds=dict(hull="paint", rail="paint", bulwark="paint",
                                                             deck="paint", brk="paint", transom="paint"),
                                          colors=dict(hull="#D9D3C4", rail="#8B5A30", bulwark="#B8B2A3",
                                                      deck="#B8B2A3"))
    merge(m, dinghy, (0, -2.8, dz + hh + 0.06 + 0.5), rot_x(math.pi) @ rot_z(0.0))


def d_drifter(m, V):
    """East-coast steam drifter, 25 m: tall thin funnel on the casing, wheelhouse forward of it, foremast,
    steadying mizzen set, LT number on both bows."""
    P, lit = V["pal"], V["lit"]
    H = Hull(y_aft=-12.5, L=25.0, B=6.0,
             keel=[(0, -2.2), (0.3, -2.45), (0.72, -2.25), (0.9, -1.6), (1.0, -0.5)],
             rail=[(0, 2.65), (0.5, 2.35), (1, 3.35)], deck=[(0, 1.85), (0.5, 1.5), (1, 2.5)],
             plan=[(0, 0.42), (0.07, 0.66), (0.22, 0.92), (0.5, 1.0), (0.7, 0.93), (0.88, 0.6), (1.0, 0.02)],
             p=[(0, 2.0), (0.45, 3.2), (0.8, 2.2), (1, 1.5)], stern_over=2.6, stern_pow=1.3, stem_rake=0.8,
             stem_pow=1.2, kw=0.12, bt=0.1, camber=0.09, stations=40,
             rows=[0, .02, .05, .1, .16, .24, .33, .43, .53, .63, .73, .82, .9, .96, 1.0])
    H.build(m, texts=[dict(text=V["reg"], y=9.4, z=2.0, h=0.62, font="reg"),
                      dict(text=V["name"], y=-9.2, z=1.95, h=0.26, font="name")],
            transom_texts=[dict(text=V["name"], x=0.0, z=2.2, h=0.22, font="name"),
                           dict(text="LT", x=0.0, z=1.9, h=0.18, font="name")])
    m.meta["hull"] = H
    for side in (-1, 1):
        strake(m, H, side, -10.9, 11.2, lambda y: H.deck_z(y) + 0.02, h=0.14, t=0.07, color=P["strake"])
    zc0 = H.deck_z(-5.0) - 0.1
    box(m, (0, -5.0, zc0), (3.4, 8.0, 1.0), "paint", top="metal", color=P["house_paint"], top_color="#3E3B36",
        windows={"+x": win_row(8.0, 4, 0.22, 0.45, 0.67, lit=lit, round_=True),
                 "-x": win_row(8.0, 4, 0.22, 0.45, 0.67, lit=lit, round_=True)}, part="casing")
    zc = zc0 + 1.0
    zb, zr = wheelhouse(m, H, -2.75, -1.05, 2.3, 2.1, "varnish", P["house"], P["roof"], lit, z0=zc - 0.02)
    cyl(m, (0, -4.45, zc - 0.05), (0, -4.75, 9.3), 0.5, 0.47, 12, "funnel", cap1="soot", color=P["funnel"],
        bands=[(-1, 9.5 - zc - 1.0, P["funnel"]), (9.3 - zc - 1.0, 99, "#141414"),
               (5.1 - zc, 5.6 - zc, P["band"])], part="funnel", a0=-math.pi / 2)
    for side in (-1, 1):
        cyl(m, (side * 1.0, -3.55, zc - 0.05), (side * 1.0, -3.55, zc + 1.25), 0.16, 0.16, 8, "paint",
            cap1="black", color=P["house_paint"])
        rod(m, (0, -4.7, 8.3), (side * (H.half_out(-4.7, H.rail_z(-4.7)) - 0.05), -4.7, H.rail_z(-4.7)))
    box(m, (0.9, -9.2, zc - 0.02), (0.8, 0.8, 0.34), "varnish", top="glass", color=P["house"])       # skylight
    boat = Mesh()
    Hull(y_aft=-1.5, L=3.0, B=1.3, keel=[(0, -0.05), (0.5, -0.12), (1, 0.05)], rail=[(0, 0.45), (0.5, 0.4),
                                                                                    (1, 0.52)],
         deck=[(0, 0.33), (0.5, 0.28), (1, 0.4)], plan=[(0, 0.55), (0.3, 1.0), (0.7, 0.9), (1, 0.03)],
         p=[(0, 1.8), (1, 1.4)], stern_over=0.1, stem_rake=0.45, kw=0.03, bt=0.03, camber=0.0, stations=12,
         rows=[0, .2, .5, .8, 1.0]).build(boat, kinds=dict(hull="paint", rail="paint", bulwark="paint",
                                                           deck="paint", brk="paint", transom="paint"),
                                          colors=dict(hull="#C9C1AD", rail="#6E4A2C", bulwark="#9C9584",
                                                      deck="#7E6E58"))
    merge(m, boat, (0, -6.6, zc + 0.12), np.eye(3))
    for yb in (-7.4, -5.8):
        box(m, (0, yb, zc - 0.02), (0.9, 0.14, 0.2), "black", top="black")                     # chocks
    yf = 6.6
    zf = mast(m, H, yf, 12.0, 0.17, 0.1, P["mast"], segs=10)
    cyl(m, (-0.8, yf, 9.4), (0.8, yf, 9.4), 0.04, 0.035, 6, "mast", color=P["mast"])
    cyl(m, (0, yf - 0.16, zf + 0.9), (0, 2.2, zf + 2.4), 0.08, 0.06, 8, "mast", color=P["mast"])      # derrick
    rod(m, (0, 2.2, zf + 2.4), (0, yf, 10.8))
    rod(m, (0, yf + 0.1, 11.6), (0, 12.42, H.rail_z(12.42)))
    shrouds(m, H, yf, 10.8, 2, spread=0.45)
    yz = -11.05
    mast(m, H, yz, 9.0, 0.1, 0.06, P["mast"])
    sail = [(yz - 0.07, 3.15), (yz - 0.07, 8.3), (-12.15, 8.65), (-12.35, 3.25)]
    prism(m, sail, 0.035, (0, 0, 0), frame_yz(), "canvas", color=P["sail"], part="sail")
    cyl(m, (0, yz - 0.06, 3.15), (0, -12.42, 3.25), 0.05, 0.045, 6, "mast", color=P["mast"])
    rod(m, (0, yz, 8.9), (0, -4.8, 8.6))
    shrouds(m, H, yz, 8.4, 1)
    cyl(m, (0, 9.0, H.deck_z(9.0) - 0.05), (0, 9.0, H.deck_z(9.0) + 0.7), 0.27, 0.23, 10, "metal", cap1="metal",
        color="#2E3133")                                                                           # capstan
    for yh in (2.6, 0.1):
        box(m, (0, yh, H.deck_z(yh) - 0.05), (1.9, 1.6, 0.45), "paint", top="varnish", color=P["bulwark"],
            top_color=P["deck"], part="hatch")
    for side in (-1, 1):
        cyl(m, (side * 0.35, 11.3, H.deck_z(11.3) - 0.05), (side * 0.35, 11.3, H.deck_z(11.3) + 0.5), 0.09,
            0.09, 6, "black", cap1="black")
    sidelights(m, H, 1.23, -1.2, zc + 1.45, lit, screen=False)
    lantern(m, "NAV_masthead", (0, yf + 0.2, 10.2), "lamp_w" if lit else "lamp_dark")
    lantern(m, "NAV_stern", (0, -12.3, H.rail_z(-12.3) + 0.22), "lamp_w" if lit else "lamp_dark")
    rod(m, (0, -12.3, H.rail_z(-12.3) - 0.05), (0, -12.3, H.rail_z(-12.3) + 0.1), 0.02, "black")
    lantern(m, "DECK_work", (0, yf - 0.2, 5.4), "lamp_w" if lit else "lamp_dark", size=(0.22, 0.12, 0.18))


def coaster_hull():
    return Hull(y_aft=-15.0, L=30.0, B=7.0,
                keel=[(0, -1.75), (0.12, -1.95), (0.8, -2.0), (0.93, -1.55), (1.0, -0.4)],
                rail=[(0, 3.85), (0.19, 3.85), (0.19, 3.0), (0.83, 3.0), (0.83, 3.95), (1.0, 4.15)],
                deck=[(0, 3.0), (0.19, 3.0), (0.19, 2.0), (0.5, 1.95), (0.83, 2.05), (0.83, 3.12), (1.0, 3.3)],
                plan=[(0, 0.30), (0.05, 0.62), (0.14, 0.9), (0.3, 1.0), (0.72, 1.0), (0.86, 0.85), (0.95, 0.5),
                      (1.0, 0.02)],
                p=[(0, 2.5), (0.3, 6.0), (0.7, 6.0), (0.9, 2.2), (1, 1.4)], z_ref=1.3, stern_over=2.4,
                stern_pow=1.5, stem_rake=3.0, stem_pow=1.0, kw=0.12, bt=0.1, camber=0.1, steps=(0.19, 0.83),
                stations=40, rows=[0, .02, .05, .1, .16, .24, .33, .43, .53, .63, .73, .82, .9, .96, 1.0])


def d_coaster(m, V):
    """Coaster, 30 m: raised forecastle and poop, two hatches and a mast with derricks between them, the bridge
    and accommodation aft with the funnel behind; Hendrika carries a timber deck cargo instead of open hatches."""
    P, lit = V["pal"], V["lit"]
    H = coaster_hull()
    H.build(m, texts=[dict(text=V["name"], y=11.9, z=2.95, h=0.5, font="name"),
                      dict(text=V["name"], y=-12.2, z=2.45, h=0.4, font="name"),
                      dict(text=V["port"], y=-12.2, z=1.95, h=0.28, font="name")])
    m.meta["hull"] = H
    for side in (-1, 1):
        strake(m, H, side, -13.3, 13.0, lambda y: 1.95, n=40, h=0.16, t=0.08, kind="metal", color=P["top"])
    timber = V.get("cargo") == "timber"
    # cargo
    for yc, ln in ((-4.9, 7.0), (5.0, 7.2)):
        dz = H.deck_z(yc) - 0.05
        if not timber:
            box(m, (0, yc, dz), (4.4, ln, 0.95), "paint", top="tarp", color="#3F4441", top_color=P["tarp"],
                part="hatch")
        else:
            box(m, (0, yc, dz), (6.1, ln + 0.6, 1.95), "timber", top="timber", color=P["timber"], part="timber",
                ends=True)
            box(m, (0, yc - 0.15, dz + 1.95), (5.6, ln, 0.75), "timber", top="timber", color=P["timber"],
                part="timber2", ends=True)
            top = dz + 2.7
            for k in range(4):
                yl = yc - ln / 2 + 0.8 + k * (ln - 1.6) / 3
                rod(m, (-3.1, yl, dz + 0.3), (-2.85, yl, top), 0.02, "black")
                rod(m, (-2.85, yl, top), (2.85, yl, top), 0.02, "black")
                rod(m, (2.85, yl, top), (3.1, yl, dz + 0.3), 0.02, "black")
    # mast, mast house, derricks
    dz = H.deck_z(0.0) - 0.05
    box(m, (0, 0, dz), (1.6, 1.2, 1.0), "paint", top="metal", color=P["house_paint"], top_color="#3E3B36",
        part="masthouse")
    cyl(m, (0, 0, dz + 0.95), (0, 0, 15.2), 0.22, 0.12, 10, "mast", cap1="black", color=P["mast"])
    box(m, (0, 0, 11.5), (1.9, 0.22, 0.12), "mast", top="mast", bottom="mast", color=P["mast"], top_color=P["mast"])
    ends = ((0, 3.6, 10.6), (0, -3.6, 10.6)) if timber else ((0, 6.6, 4.75), (0, -6.6, 4.75))
    for sgn, e in zip((1, -1), ends):
        cyl(m, (0, sgn * 0.4, dz + 1.45), e, 0.11, 0.085, 8, "mast", cap1="black", color=P["mast"])
        rod(m, e, (0, sgn * 0.14, 12.6))
    for side in (-1, 1):
        for yy in (-0.5, 0.6):
            zr = H.rail_z(yy)
            rod(m, (side * 0.12, 0, 11.4), (side * (H.half_out(yy, zr) - 0.04), yy, zr), 0.016)
    rod(m, (0, 0.14, 14.9), (0, 13.9, H.rail_z(13.9)))
    # forecastle: windlass, bitts, jackstaff
    box(m, (0, 12.0, H.deck_z(12.0) - 0.05), (1.6, 0.8, 0.55), "metal", color="#2E3133", top_color="#2E3133")
    for side in (-1, 1):
        cyl(m, (side * 0.8, 12.0, H.deck_z(12.0) + 0.3), (side * 1.15, 12.0, H.deck_z(12.0) + 0.3), 0.22, 0.22, 8,
            "metal", cap0="metal", cap1="metal", color="#383A39")
        cyl(m, (side * 1.2, 10.6, H.deck_z(10.6) - 0.05), (side * 1.2, 10.6, H.deck_z(10.6) + 0.55), 0.13, 0.13,
            8, "black", cap1="black")
    rod(m, (0, 14.65, H.rail_z(14.65) - 0.2), (0, 14.7, H.rail_z(14.7) + 1.6), 0.03, "black")
    # poop: accommodation, bridge, wings, funnel, lifeboats
    z0 = H.deck_z(-11.8) - 0.05
    hh = 2.35
    zt = z0 + hh
    wins = {"+x": win_row(4.4, 4, 0.3, 1.25, 1.55, lit=lit, round_=True),
            "-x": win_row(4.4, 4, 0.3, 1.25, 1.55, lit=lit, round_=True),
            "+y": [door(0.9, 0.75, 1.9)] + win_row(5.4, 2, 0.3, 1.25, 1.55, lit=lit, round_=True, gap=2.6),
            "-y": [door(2.3, 0.8, 1.9)]}
    box(m, (0, -11.8, z0), (5.4, 4.4, hh), "paint", top="roof", color=P["house_paint"], top_color=P["roof"],
        windows=wins, part="house")
    zb, zr = wheelhouse(m, H, -11.1, -9.6, 3.6, 2.15, "paint", P["house_paint"], P["roof"], lit, n_front=5,
                        n_side=1, win=(0.5, 0.6), z0=zt - 0.02, back_door=True)
    box(m, (0, -9.75, zt - 0.02), (6.9, 0.9, 0.09), "paint", top="paint", color=P["house_paint"],
        top_color="#8F8B83", part="wings")
    box(m, (0, -9.33, zt + 0.07), (6.9, 0.06, 1.0), "paint", top="paint", color=P["house_paint"], part="dodger")
    cyl(m, (0, -12.6, zt - 0.05), (0, -12.75, zt + 3.15), 1.2, 1.15, 14, "funnel", cap1="soot", ellipse=(0.75, 1.0),
        color=P["funnel"], bands=[(-1, 3.2 - 0.75, P["funnel"]), (3.2 - 0.75, 99, "#141414"),
                                  (1.25, 2.15, P["band"])], star=P.get("star"), part="funnel",
        a0=-math.pi / 2)
    for side in (-1, 1):
        cyl(m, (side * 1.45, -11.35, zt - 0.05), (side * 1.45, -11.35, zt + 1.3), 0.18, 0.18, 8, "paint",
            cap1="black", color=P["house_paint"])
        lb = Mesh()
        Hull(y_aft=-1.6, L=3.2, B=1.5, keel=[(0, -0.1), (0.5, -0.18), (1, -0.05)],
             rail=[(0, 0.5), (0.5, 0.45), (1, 0.55)], deck=[(0, 0.46), (0.5, 0.41), (1, 0.5)],
             plan=[(0, 0.08), (0.25, 0.95), (0.7, 0.95), (1, 0.03)], p=[(0, 1.6), (1, 1.4)], stern_over=0.35,
             stem_rake=0.35, kw=0.04, bt=0.03, camber=0.08, stations=12,
             rows=[0, .2, .5, .8, 1.0]).build(lb, kinds=dict(hull="paint", rail="paint", bulwark="paint",
                                                             deck="canvas", brk="paint", transom="paint"),
                                          colors=dict(hull="#DAD6CC", rail="#DAD6CC", bulwark="#DAD6CC",
                                                      deck="#8C8A7E"))
        merge(m, lb, (side * 1.9, -12.7, zt + 0.42), np.eye(3))
        for yd in (-13.9, -11.5):
            rod(m, (side * 2.55, yd, zt), (side * 2.55, yd, zt + 1.3), 0.035, "black")
            rod(m, (side * 2.55, yd, zt + 1.3), (side * 1.95, yd, zt + 1.35), 0.03, "black")
    for y in (-13.95, -12.6, -11.2):                                                          # boat-deck rail
        for side in (-1, 1):
            rod(m, (side * 2.68, y, zt), (side * 2.68, y, zt + 0.95), 0.02, "black")
    for side in (-1, 1):
        rod(m, (side * 2.68, -13.95, zt + 0.95), (side * 2.68, -11.2, zt + 0.95), 0.02, "black")
    rod(m, (-2.68, -13.95, zt + 0.95), (2.68, -13.95, zt + 0.95), 0.02, "black")
    cyl(m, (0, -13.7, zt + 0.0), (0, -13.7, zt + 4.2), 0.08, 0.05, 6, "mast", cap1="black", color=P["mast"])
    rod(m, (0, -13.65, zt + 4.1), (0, -0.1, 14.6))
    # lights
    sidelights(m, H, 3.37, -9.75, zt + 0.55, lit, screen=False)
    lantern(m, "NAV_masthead", (0, 0.25, 14.0), "lamp_w" if lit else "lamp_dark")
    lantern(m, "NAV_stern", (0, -14.82, H.rail_z(-14.82) + 0.22), "lamp_w" if lit else "lamp_dark")
    rod(m, (0, -14.82, H.rail_z(-14.82) - 0.05), (0, -14.82, H.rail_z(-14.82) + 0.1), 0.02, "black")
    lantern(m, "DECK_work", (0, 0.28, 8.5), "lamp_w" if lit else "lamp_dark", size=(0.24, 0.12, 0.18))
    lantern(m, "DECK_aft", (0, -9.5, zt + 1.98), "lamp_w" if lit else "lamp_dark", size=(0.24, 0.12, 0.18))


DESIGNS = {"ringnetter": d_ringnetter, "blackboat": d_blackboat, "schooner": d_schooner, "drifter": d_drifter,
           "coaster": d_coaster}


# ------------------------------------------------------------------ orientation, packing, UVs
def _directed(f, a, b):
    n = len(f)
    return any(f[k] == a and f[(k + 1) % n] == b for k in range(n))


def _flip(m, fi):
    m.f[fi] = m.f[fi][::-1]
    m.fab[fi] = m.fab[fi][::-1]


def _vol(m, faces):
    v = 0.0
    for fi in faces:
        f = m.f[fi]
        p0 = np.asarray(m.v[f[0]])
        for k in range(1, len(f) - 1):
            v += float(np.dot(p0, np.cross(np.asarray(m.v[f[k]]), np.asarray(m.v[f[k + 1]])))) / 6.0
    return v


def orient(m):
    """Consistent winding within each closed shell, then outward (positive volume)."""
    ef = defaultdict(list)
    for fi, f in enumerate(m.f):
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            ef[(min(a, b), max(a, b))].append(fi)
    seen = [False] * len(m.f)
    shells = []
    for s in range(len(m.f)):
        if seen[s]:
            continue
        seen[s] = True
        comp, dq = [s], deque([s])
        while dq:
            fi = dq.popleft()
            f = m.f[fi]
            for k in range(len(f)):
                a, b = f[k], f[(k + 1) % len(f)]
                for g in ef[(min(a, b), max(a, b))]:
                    if g == fi or seen[g]:
                        continue
                    if _directed(m.f[g], a, b):
                        _flip(m, g)
                    seen[g] = True
                    comp.append(g)
                    dq.append(g)
        if _vol(m, comp) < 0:
            for fi in comp:
                _flip(m, fi)
        shells.append(comp)
    m.meta["shells"] = shells


def _bounds(m):
    bd = {}
    for fi, ab in zip(m.fi, m.fab):
        for a, b in ab:
            if fi not in bd:
                bd[fi] = [a, a, b, b]
            else:
                d = bd[fi]
                d[0], d[1], d[2], d[3] = min(d[0], a), max(d[1], a), min(d[2], b), max(d[3], b)
    return bd


def _try_pack(m, ppm, commit=False):
    items = []
    for i, isl in enumerate(m.isl):
        if isl["shared"]:
            s = SHARED[isl["kind"]]
            items.append((i, s, s, False, ppm))
            continue
        q = ppm * DENSITY.get(isl["kind"], 0.8)
        w = max(2, int(math.ceil((isl["a1"] - isl["a0"]) * q)) + 1)
        h = max(2, int(math.ceil((isl["b1"] - isl["b0"]) * q)) + 1)
        rot = (not isl.get("no_rotate")) and h > 1.4 * w
        if rot:
            w, h = h, w
        items.append((i, w, h, rot, q))
    items.sort(key=lambda it: (-it[2], -it[1]))
    x, y, shelf = PAD, PAD, 0
    place = {}
    for i, w, h, rot, q in items:
        if w + 2 * PAD > N:
            return False
        if x + w + PAD > N:
            x, y = PAD, y + shelf + 2 * PAD
            shelf = 0
        if y + h + PAD > N:
            return False
        place[i] = (x, y, w, h, rot, q)
        x += w + 2 * PAD
        shelf = max(shelf, h)
    if commit:
        for i, (x, y, w, h, rot, q) in place.items():
            m.isl[i].update(rect=(x, y, w, h), rot=rot, ppm=q)
    return True


def pack(m):
    bd = _bounds(m)
    for i, isl in enumerate(m.isl):
        if not isl["shared"]:
            a0, a1, b0, b1 = bd.get(i, (0.0, 0.01, 0.0, 0.01))
            isl.update(a0=a0, a1=a1, b0=b0, b1=b1)
    lo, hi = 2.0, 600.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if _try_pack(m, mid):
            lo = mid
        else:
            hi = mid
    assert _try_pack(m, lo, commit=True)
    m.meta["ppm"] = lo


def to_px(isl, a, b):
    """Metric (a, b) on an island -> atlas pixel (col, row), row 0 at the top."""
    x0, y0, w, h = isl["rect"]
    q = isl["ppm"]
    if isl["rot"]:
        return x0 + (b - isl["b0"]) * q, y0 + (a - isl["a0"]) * q
    return x0 + (a - isl["a0"]) * q, y0 + h - (b - isl["b0"]) * q


def corner_uvs(m):
    """Per face, per corner UV (0..1, v up)."""
    out = []
    for fi, ab in zip(m.fi, m.fab):
        isl = m.isl[fi]
        if isl["shared"]:
            x0, y0, w, h = isl["rect"]
            aa, bb = [p[0] for p in ab], [p[1] for p in ab]
            sa, sb = max(max(aa) - min(aa), 1e-9), max(max(bb) - min(bb), 1e-9)
            uv = [((x0 + w * (0.2 + 0.6 * (a - min(aa)) / sa)) / N, 1 - (y0 + h * (0.8 - 0.6 * (b - min(bb)) / sb)) / N)
                  for a, b in ab]
        else:
            uv = []
            for a, b in ab:
                c, r = to_px(isl, a, b)
                uv.append((c / N, 1 - r / N))
        out.append(uv)
    return out


def make(vid):
    V = VESSELS[vid]
    m = Mesh()
    m.meta["vid"] = vid
    DESIGNS[V["design"]](m, V)
    orient(m)
    pack(m)
    return m


# ------------------------------------------------------------------ checks (host and Blender)
def dims_points(kind):
    """Where ship_view2 puts each light today (DIMS), in Blender axes (Godot (x, y, z) -> (x, -z, y))."""
    dx, dy, dz = DIMS[kind]
    g = {"NAV_masthead": (0, dy + dz * 0.35, -dz * 0.15), "NAV_port": (-dx * 0.5, dy * 1.15, -dz * 0.1),
         "NAV_starboard": (dx * 0.5, dy * 1.15, -dz * 0.1), "NAV_stern": (0, dy * 1.1, dz * 0.48),
         "DECK_work": (0, dy * 1.5, dz * 0.05)}
    return {k: (x, -z, y) for k, (x, y, z) in g.items()}


def checks(m, vid):
    V = VESSELS[vid]
    H = m.meta["hull"]
    r = {"vid": vid, "export": V["export"]}
    ec, dc = defaultdict(int), defaultdict(int)
    zero = 0
    for f in m.f:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            ec[(min(a, b), max(a, b))] += 1
            dc[(a, b)] += 1
        P = [np.asarray(m.v[i]) for i in f]
        ar = sum(np.linalg.norm(np.cross(P[k] - P[0], P[k + 1] - P[0])) for k in range(1, len(P) - 1)) / 2
        zero += ar < 1e-8
    vols = [_vol(m, s) for s in m.meta["shells"]]
    v = np.asarray(m.v)
    r.update(tris=m.tris(), verts=len(m.v), shells=len(vols), nonmanifold=sum(c != 2 for c in ec.values()),
             inconsistent=sum(c > 1 for c in dc.values()), inward_shells=sum(x <= 0 for x in vols),
             zero_area=int(zero), ppm=round(m.meta["ppm"], 1), islands=len(m.isl))
    r["beam"] = round(float(2 * np.abs(v[:, 0]).max()), 3)
    r["loa"] = round(float(v[:, 1].max() - v[:, 1].min()), 3)
    r["y_range"] = [round(float(v[:, 1].min()), 3), round(float(v[:, 1].max()), 3)]
    r["z_range"] = [round(float(v[:, 2].min()), 3), round(float(v[:, 2].max()), 3)]
    ts = np.linspace(0, 1, 401)
    r["rail_max"] = round(max(H.rail(t) for t in ts), 3)
    r["waterline"] = WL
    uv = corner_uvs(m)
    flat = [c for f in uv for c in f]
    r["uv_in_unit"] = all(0.0 <= u <= 1.0 and 0.0 <= w <= 1.0 for u, w in flat)
    rects = [isl["rect"] for isl in m.isl]
    ov = 0
    for i in range(len(rects)):
        x0, y0, w0, h0 = rects[i]
        for j in range(i + 1, len(rects)):
            x1, y1, w1, h1 = rects[j]
            if x0 < x1 + w1 and x1 < x0 + w0 and y0 < y1 + h1 and y1 < y0 + h0:
                ov += 1
    r["island_overlaps"] = ov
    need = EMPTY_NAMES + (("DECK_aft",) if V["design"] == "coaster" else ())
    r["empties_missing"] = [e for e in need if e not in m.empties]
    names = ["SM_Vessel_" + V["Id"], "M_Vessel_" + V["Id"]] + list(m.empties)
    r["hint_suffix_names"] = [n for n in names if n.lower().endswith(HINT_SUFFIXES)]
    kind = V["kind"]
    fails = []
    if not TRI_MIN <= r["tris"] <= TRI_MAX:
        fails.append("tris %d outside %d-%d" % (r["tris"], TRI_MIN, TRI_MAX))
    for key in ("nonmanifold", "inconsistent", "inward_shells", "island_overlaps"):
        if r[key]:
            fails.append("%s %d" % (key, r[key]))
    if not r["uv_in_unit"]:
        fails.append("uv outside 0-1")
    if r["empties_missing"] or r["hint_suffix_names"]:
        fails.append("names")
    if kind:
        dx, dy, dz = DIMS[kind]
        r["dims"] = dict(kind=kind, beam=dx, height=dy, length=dz)
        if r["beam"] > dx + 1e-6:
            fails.append("beam %.3f > DIMS %.2f" % (r["beam"], dx))
        if r["loa"] > dz + 1e-6:
            fails.append("length %.3f > DIMS %.2f" % (r["loa"], dz))
        if r["rail_max"] > dy + 1e-6:
            fails.append("rail %.3f > DIMS height %.2f" % (r["rail_max"], dy))
        dp = dims_points(kind)
        r["light_offsets_vs_dims"] = {k: [round(a - b, 2) for a, b in zip(m.empties[k], dp[k])]
                                      for k in dp if k in m.empties}
    r["empties"] = {k: [round(x, 3) for x in p] for k, p in m.empties.items()}
    if r["zero_area"]:
        r["warn"] = ["%d zero-area faces" % r["zero_area"]]
    r["result"] = "FAIL" if fails else "PASS"
    r["fails"] = fails
    return r


# ------------------------------------------------------------------ painting (host Python: numpy + Pillow)
FONTS = {"reg": "DIN Condensed Bold.ttf", "name": "Arial Narrow Bold.ttf"}
STEEL = ("drifter", "coaster")
SHARED_LOOK = {   # kind: (sRGB, roughness, emission when lit)
    "rope": ("#3A3630", 0.9, None), "hidden": ("#555555", 0.9, None), "lamp_r": ("#B81E14", 0.15, (1.0, .12, .08)),
    "lamp_g": ("#1E9A3A", 0.15, (.2, 1.0, .35)), "lamp_w": ("#E8E2D0", 0.15, (1.0, .95, .85)),
    "lamp_dark": ("#22262A", 0.2, None), "rubber": ("#161616", 0.92, None), "glass": ("#15191C", 0.1, None),
    "soot": ("#0E0D0C", 0.95, None), "black": ("#1A1A1A", 0.6, None)}


def _font(kind, px):
    from PIL import ImageFont
    for d in (Path("/System/Library/Fonts/Supplemental"), Path("/System/Library/Fonts")):
        f = d / FONTS[kind]
        if f.exists():
            return ImageFont.truetype(str(f), max(6, int(px)))
    raise FileNotFoundError(FONTS[kind])


def vnoise(x, y, seed=0):
    """Smooth value noise on a unit lattice, metric and resolution independent."""
    xi, yi = np.floor(x), np.floor(y)
    fx, fy = x - xi, y - yi

    def h(i, j):
        v = np.sin(i * 127.1 + j * 311.7 + seed * 74.7) * 43758.5453
        return v - np.floor(v)
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = h(xi, yi), h(xi + 1, yi)
    c, d = h(xi, yi + 1), h(xi + 1, yi + 1)
    return (a + (b - a) * sx) * (1 - sy) + (c + (d - c) * sx) * sy


def fbm(x, y, seed=0, octaves=3):
    out, amp, tot = 0.0, 1.0, 0.0
    for k in range(octaves):
        out = out + amp * vnoise(x * 2 ** k, y * 2 ** k, seed + 17 * k)
        tot += amp
        amp *= 0.5
    return out / tot - 0.5           # about -0.5 .. 0.5


def _rgb(c):
    return np.asarray(hexrgb(c) if isinstance(c, str) else c, float)


def _mix(col, c2, k):
    k = np.clip(k, 0, 1)[..., None]
    return col * (1 - k) + _rgb(c2)[None, None, :] * k


class Ctx:
    def __init__(self, vid):
        self.vid, self.V = vid, VESSELS[vid]
        self.P, self.w, self.seed, self.lit = self.V["pal"], self.V["weather"], self.V["seed"], self.V["lit"]
        self.steel = self.V["design"] in STEEL


def _lut(H):
    if not hasattr(H, "_lut"):
        t = np.linspace(0, 1, 2049)
        H._lut = (t, np.array([H.keel(x) for x in t]), np.array([H.rail(x) for x in t]),
                  np.array([H.deck(x) for x in t]))
    return H._lut


def _hull_fns(H, y):
    t = np.clip((y - H.y_aft) / H.L, 0, 1)
    T, K, Rl, D = _lut(H)
    return t, np.interp(t, T, K), np.interp(t, T, Rl), np.interp(t, T, D)


def _text(arr, isl, ox, oy, text, a_c, b_c, h_m, color, font, k=0.92, seed=0, mask_out=None):
    """Draw text centred at (a_c, b_c) metres on the island into arr (island-local, origin ox, oy in atlas px)."""
    from PIL import Image, ImageDraw
    q = isl["ppm"]
    cx, cy = to_px(isl, a_c, b_c)
    cx, cy = cx - ox, cy - oy
    ss = 4
    fnt = _font(font, h_m * q * ss / 0.72)
    hh, ww = arr.shape[:2]
    img = Image.new("L", (ww * ss, hh * ss), 0)
    d = ImageDraw.Draw(img)
    d.text((cx * ss, cy * ss), text, font=fnt, fill=255, anchor="mm")
    msk = np.asarray(img.resize((ww, hh), Image.LANCZOS), float) / 255.0
    if mask_out is not None:
        mask_out[:] = np.maximum(mask_out, msk)
    arr[:] = arr * (1 - msk[..., None] * k) + _rgb(color)[None, None, :] * (msk[..., None] * k)


def _windows(out, A, B, isl, ctx):
    col, rough, emit, hgt = out["col"], out["rough"], out["emit"], out["height"]
    for wd in isl.get("windows") or []:
        a0, b0, a1, b1 = wd["a0"], wd["b0"], wd["a1"], wd["b1"]
        if wd.get("round"):
            ca, cb, r = (a0 + a1) / 2, (b0 + b1) / 2, min(a1 - a0, b1 - b0) / 2
            d = np.sqrt((A - ca) ** 2 + (B - cb) ** 2)
            rim = (d < r + 0.03) & (d >= r)
            glass = d < r
            col[rim] = _rgb("#8A6A3A")
            hgt[rim] += 0.004
        else:
            fr = 0.035
            inner = (A > a0) & (A < a1) & (B > b0) & (B < b1)
            frame = (A > a0 - fr) & (A < a1 + fr) & (B > b0 - fr) & (B < b1 + fr) & ~inner
            col[frame] = col[frame] * 0.55
            hgt[frame] += 0.006
            glass = inner
            if wd.get("door"):
                col[inner] = col[inner] * 0.78
                hgt[inner] -= 0.004
                hx = a0 + (a1 - a0) * 0.82
                knob = (np.abs(A - hx) < 0.025) & (np.abs(B - (b0 + 0.95)) < 0.025)
                col[knob] = _rgb("#2A2520")
                continue
        col[glass] = _rgb("#15191C")
        rough[glass] = 0.08
        hgt[glass] -= 0.005
        if wd.get("lit") and ctx.lit:
            n = 0.8 + 0.25 * fbm(A[glass] * 3, B[glass] * 3, ctx.seed + 5)
            grad = 0.85 + 0.3 * np.clip((b1 - B[glass]) / max(b1 - b0, 1e-3), 0, 1)
            emit[glass] = np.array([1.0, 0.68, 0.38])[None, :] * (n * grad)[:, None]
            col[glass] = _rgb("#6A5236")
        elif ctx.lit is False:
            col[glass] = _rgb("#0D0F10")


def _dirt(out, A, B, ctx, amt=0.12, streak=True, sx=6.0):
    col = out["col"]
    n = fbm(A * 1.3, B * 1.3, ctx.seed + 3)
    col *= (1 + 0.08 * n)[..., None]
    if streak:
        s = fbm(A * sx, B * 0.35, ctx.seed + 9)
        col *= (1 - ctx.w * amt * np.clip(s + 0.15, 0, 1))[..., None]
    out["rough"] += 0.05 * n


def _new(A, color, rough=0.55):
    hh, ww = A.shape
    return dict(col=np.ones((hh, ww, 3)) * _rgb(color)[None, None, :], rough=np.full((hh, ww), rough),
                metal=np.zeros((hh, ww)), height=np.zeros((hh, ww)), emit=np.zeros((hh, ww, 3)))


def p_hull(A, B, isl, ctx, ox, oy):
    H, P = isl["hull"], ctx.P
    side = isl.get("side", "s")
    y = A if side == "s" else -A
    z = B
    t, keel, rail, deck = _hull_fns(H, y)
    out = _new(A, P["top"])
    col = out["col"]
    boot_hi = WL + (0.5 if ctx.V["design"] == "coaster" else 0.12)
    bot_hi = WL - (0.2 if ctx.V["design"] == "coaster" else 0.03)
    col[z < boot_hi] = _rgb(P["boot"])
    col[z < bot_hi] = _rgb(P["bottom"])
    out["rough"][z < bot_hi] = 0.78
    if ctx.V["design"] == "schooner" and P.get("strake"):
        cove = np.abs(z - (rail - 0.26)) < 0.03
        col[cove] = _rgb(P["strake"])
    col[z > rail - 0.05] = _rgb(P["rail"])
    hp = (z - keel) / np.maximum(rail - keel, 1e-3)
    if not ctx.steel:          # carvel planks follow the sheer
        npl = (np.interp(0.5, *_lut(H)[:3:2]) - np.interp(0.5, *_lut(H)[:2])) / (0.17 * H.s)
        f = (hp * npl) % 1.0
        seam = f < 0.06
        out["height"][seam] -= 0.0018
        col[seam] *= 0.86
        col *= (1 + 0.035 * np.sin(np.floor(hp * npl) * 12.9898)[..., None])
    else:                      # plates: lapped strakes and butts, faint rivet rows
        f = (hp * 6.0) % 1.0
        out["height"] += np.where(f < 0.5, 0.002, 0.0)
        butt = (np.abs(((y + 0.7 * np.floor(hp * 6.0)) % 3.6) - 1.8) < 0.012)
        out["height"][butt] -= 0.0012
        if isl["ppm"] > 32:
            riv = ((y % 0.09) < 0.025) & (np.abs(f - 0.5) < 0.03)
            out["height"][riv] += 0.002
    # waterline scum and grime
    wl = np.clip(1 - np.abs(z - WL - 0.08) / 0.22, 0, 1) * ctx.w
    col[:] = _mix(col, "#2E3A2A", 0.45 * wl)
    # scupper and rust streaks under the deck edge
    rng = np.random.default_rng(ctx.seed + (1 if side == "s" else 2))
    ys = np.arange(H.y_aft + 0.8, H.y_aft + H.L - 0.8, 1.3 * H.s) + rng.uniform(-0.3, 0.3, 1)[0]
    stk = np.zeros_like(A)
    for yk in ys:
        wk, lk = rng.uniform(0.04, 0.1) * H.s, rng.uniform(0.3, 1.4) * (0.5 + ctx.w)
        below = np.clip((deck - z) / lk, 0, 1)
        stk += np.exp(-((y - yk) / wk) ** 2) * np.where(z < deck, 1 - below, 0) * rng.uniform(0.4, 1.0)
    stk = np.clip(stk * ctx.w, 0, 1)
    col[:] = _mix(col, "#6B3A22" if ctx.steel else "#2A2520", 0.55 * stk)
    out["rough"] += 0.2 * stk
    # paint wear along the rail and fender rub
    wear = (fbm(y * 3, z * 9, ctx.seed + 4) > 0.32 - 0.12 * ctx.w) & (z > rail - 0.35)
    col[wear] = _mix(col[wear][None], "#6E5A44" if not ctx.steel else "#5A3A28", 0.6)[0]
    _dirt(out, y, z, ctx, 0.1)
    msk = np.zeros(A.shape)
    for tx in isl.get("texts") or []:
        a_c = tx["y"] if side == "s" else -tx["y"]
        _text(col, isl, ox, oy, tx["text"], a_c, tx["z"], tx["h"], P["text"], tx.get("font", "reg"),
              k=0.9 - 0.25 * ctx.w * (tx.get("font") == "name"), mask_out=msk)
    out["height"] += 0.0006 * msk
    out["rough"] = np.clip(out["rough"] - 0.1 * msk, 0.05, 1)
    return out


def p_transom(A, B, isl, ctx, ox, oy):
    H, P = isl["hull"], ctx.P
    if isl.get("color") and not isl.get("texts") and isl["face"] == "stem":
        out = _new(A, P["top"])
    else:
        out = _new(A, P["top"])
    z = B
    col = out["col"]
    col[z < WL + 0.12] = _rgb(P["boot"])
    col[z < WL - 0.03] = _rgb(P["bottom"])
    rail0 = H.rail(0.0)
    col[z > rail0 - 0.05] = _rgb(P["rail"])
    _dirt(out, A, B, ctx, 0.12)
    for tx in isl.get("texts") or []:
        _text(col, isl, ox, oy, tx["text"], tx["x"], tx["z"], tx["h"], P["text"], tx.get("font", "name"))
    return out


def p_deck(A, B, isl, ctx, ox, oy):
    H, P = isl["hull"], ctx.P
    x, y = A, B
    out = _new(A, P["deck"], 0.75)
    col = out["col"]
    if not ctx.steel:
        pw = 0.12 * H.s
        k = np.floor(x / pw)
        f = (x / pw) % 1.0
        col *= (1 + 0.08 * (vnoise(k * 3.1, k * 0.7, ctx.seed) - 0.5))[..., None]
        butt = np.abs(((y + k * 1.37) % (3.6 * H.s)) - 1.8 * H.s) < 0.006
        seam = (f < 0.07) | butt
        col[seam] = _rgb("#2A231C")
        out["height"][seam] -= 0.0015
        g = fbm(x * 0.8 + 3.0, y * 14.0, ctx.seed + 7)       # grain along the planks
        col *= (1 + 0.06 * g)[..., None]
    else:
        g = fbm(x * 2, y * 2, ctx.seed + 7)
        col *= (1 + 0.1 * g)[..., None]
        rust = fbm(x * 1.5, y * 1.5, ctx.seed + 8) > 0.28 - 0.1 * ctx.w
        col[rust] = _mix(col[rust][None], "#5C3220", 0.6)[0]
        seam = (np.abs((y % 2.4) - 1.2) < 0.01) | (np.abs((x % 1.8) - 0.9) < 0.01)
        out["height"][seam] += 0.0015
    t, keel, rail, deck = _hull_fns(H, y)
    edge = np.clip(1 - (H.B / 2 * 0.85 - np.abs(x)) / (0.5 * H.s), 0, 1)
    col *= (1 - 0.25 * ctx.w * edge)[..., None]
    _dirt(out, x, y, ctx, 0.0, streak=False)
    return out


def p_bulwark(A, B, isl, ctx, ox, oy):
    H = isl["hull"]
    face = isl["face"]
    y = -A if face == "bulw_s" else A
    t, keel, rail, deck = _hull_fns(H, y)
    out = _new(A, isl.get("color") or ctx.P["bulwark"])
    foot = np.clip(1 - (B - deck) / 0.12, 0, 1)
    out["col"] *= (1 - 0.35 * foot * (0.5 + ctx.w))[..., None]
    if ctx.steel:
        st = np.abs(((y % 0.9) - 0.45)) < 0.03
        out["height"][st] += 0.004
    _dirt(out, y, B, ctx, 0.14)
    return out


def p_rail(A, B, isl, ctx, ox, oy):
    out = _new(A, isl.get("color") or ctx.P["rail"], 0.45)
    g = fbm(A * 0.6, B * 20, ctx.seed + 2)
    out["col"] *= (1 + 0.1 * g)[..., None]
    return out


def p_paint(A, B, isl, ctx, ox, oy):
    out = _new(A, isl.get("color") or "#B0ABA0", 0.5)
    top = isl.get("face") in ("+z", "cap+1")
    _dirt(out, A, B, ctx, 0.16, streak=not top)
    if not top:
        foot = np.clip(1 - B / 0.25, 0, 1)
        out["col"] *= (1 - 0.3 * foot * ctx.w)[..., None]
    _windows(out, A, B, isl, ctx)
    return out


def p_varnish(A, B, isl, ctx, ox, oy):
    out = _new(A, isl.get("color") or "#7A4A26", 0.35)
    col = out["col"]
    side = isl.get("face") not in ("+z",)
    if side:
        f = (B / 0.095) % 1.0                         # tongue-and-groove boards
        out["height"][f < 0.08] -= 0.0015
        col[f < 0.08] *= 0.8
        k = np.floor(B / 0.095)
        col *= (1 + 0.07 * (vnoise(k * 2.3, k * 0.9, ctx.seed) - 0.5))[..., None]
    g = fbm(A * 9.0, B * 0.9 + (0 if side else A * 0.0), ctx.seed + 11)
    col *= (1 + 0.12 * g)[..., None]
    wear = fbm(A * 2, B * 2, ctx.seed + 12) > 0.3 - 0.15 * ctx.w
    col[wear] = _mix(col[wear][None], "#9B8A70", 0.45)[0]
    out["rough"][wear] = 0.6
    _windows(out, A, B, isl, ctx)
    return out


def p_roof(A, B, isl, ctx, ox, oy):
    out = _new(A, isl.get("color") or ctx.P["roof"], 0.8)
    out["col"] *= (1 + 0.12 * fbm(A * 1.5, B * 1.5, ctx.seed + 21))[..., None]
    out["col"] *= (1 - 0.2 * ctx.w * np.clip(fbm(A * 0.7, B * 0.7, ctx.seed + 22) + 0.2, 0, 1))[..., None]
    return out


def p_canvas(A, B, isl, ctx, ox, oy):
    out = _new(A, isl.get("color") or ctx.P.get("sail") or "#8A6A4E", 0.85)
    if str(isl.get("face", "")).startswith("cap"):
        f = (B / 0.6) % 1.0                              # sail cloths
        out["height"][f < 0.02] += 0.002
        out["col"][f < 0.02] *= 0.85
        out["col"] *= (1 + 0.08 * fbm(A * 2, B * 2, ctx.seed + 31))[..., None]
    else:                                                # furled: folds round the spar
        fold = np.sin(A * 9.0 + 3.0 * fbm(A * 0.5, B * 0.8, ctx.seed + 32) * 6.0)
        out["height"] += 0.012 * fold
        out["col"] *= (1 + 0.12 * fold)[..., None]
    return out


def p_tarp(A, B, isl, ctx, ox, oy):
    out = _new(A, isl.get("color") or ctx.P.get("tarp") or "#4A574B", 0.85)
    wr = fbm(A * 3, B * 3, ctx.seed + 41)
    out["height"] += 0.01 * wr
    out["col"] *= (1 + 0.15 * wr)[..., None]
    bat = (np.abs(((B % 1.2) - 0.6)) < 0.025)
    out["col"][bat] *= 0.6
    return out


def p_net(A, B, isl, ctx, ox, oy):
    out = _new(A, isl.get("color") or "#3C3A2E", 0.92)
    k = (np.abs(np.sin(A * 60)) < 0.25) | (np.abs(np.sin(B * 60)) < 0.25)
    out["col"][k] *= 0.55
    out["height"] += 0.01 * fbm(A * 4, B * 4, ctx.seed + 51)
    fl = ((A % 0.32) < 0.07) & ((np.abs(B) % 0.5) < 0.06)
    out["col"][fl] = _rgb("#B08A4A")
    out["height"][fl] += 0.01
    return out


def p_metal(A, B, isl, ctx, ox, oy):
    out = _new(A, isl.get("color") or "#2E3133", 0.6)
    rust = fbm(A * 3, B * 3, ctx.seed + 61) > 0.25 - 0.15 * ctx.w
    out["col"][rust] = _mix(out["col"][rust][None], "#5E3420", 0.65)[0]
    out["rough"][rust] = 0.85
    _windows(out, A, B, isl, ctx)
    return out


def p_mast(A, B, isl, ctx, ox, oy):
    out = _new(A, isl.get("color") or ctx.P["mast"], 0.45)
    out["col"] *= (1 + 0.1 * fbm(A * 12, B * 0.6, ctx.seed + 71))[..., None]
    out["col"] *= (1 - 0.18 * ctx.w * np.clip(fbm(A * 2, B * 0.4, ctx.seed + 72) + 0.2, 0, 1))[..., None]
    return out


def p_funnel(A, B, isl, ctx, ox, oy):
    out = _new(A, isl.get("color") or "#171717", 0.5)
    col = out["col"]
    bands = isl.get("bands") or []
    for b0, b1, c in bands:
        col[(B >= b0) & (B < b1)] = _rgb(c)
    if isl.get("face") == "side":
        top = isl["b1"]
        soot = np.clip(1 - (top - B) / 1.4, 0, 1) * (0.6 + 0.4 * fbm(A * 4, B * 0.5, ctx.seed + 81))
        col[:] = _mix(col, "#0E0D0C", 0.7 * soot)
        circ = isl["a1"] - isl["a0"]
        if isl.get("star"):
            b_mid = (bands[2][0] + bands[2][1]) / 2 if len(bands) > 2 else (isl["b0"] + isl["b1"]) / 2
            r = (bands[2][1] - bands[2][0]) * 0.36 if len(bands) > 2 else 0.3
            for a_c in (circ * 0.25, circ * 0.75):
                ang = np.arctan2(B - b_mid, A - a_c)
                d = np.sqrt((A - a_c) ** 2 + (B - b_mid) ** 2)
                rr = r * (0.55 + 0.45 * np.cos(5 * (ang - math.pi / 2)) ** 8 ** 0)
                k5 = (np.cos(5 * (ang - math.pi / 2)) + 1) / 2
                star = d < r * (0.42 + 0.58 * k5 ** 3)
                col[star] = _rgb(isl["star"])
    _dirt(out, A, B, ctx, 0.12)
    return out


def p_timber(A, B, isl, ctx, ox, oy):
    base = isl.get("color") or "#B59B6E"
    out = _new(A, base, 0.85)
    col = out["col"]
    face = isl.get("face")
    if face in ("+y", "-y") and isl.get("ends"):
        ca, cb = (A % 0.15), (B % 0.075)
        gap = (ca < 0.012) | (cb < 0.01)
        cell = np.floor(A / 0.15) * 7.1 + np.floor(B / 0.075) * 3.3
        col *= (0.92 + 0.16 * (vnoise(cell, cell * 0.3, ctx.seed) - 0.5) + 0.12)[..., None]
        col[gap] = _rgb("#2E271E")
        out["height"][gap] -= 0.01
    elif face == "+z":
        f = (A % 0.15) < 0.01
        col[f] = _rgb("#3A3125")
        out["height"][f] -= 0.006
        col *= (1 + 0.1 * fbm(A * 2, B * 10, ctx.seed + 91))[..., None]
    else:
        f = (B % 0.075) < 0.008
        k = np.floor(B / 0.075)
        butt = np.abs(((A + k * 1.7) % 4.8) - 2.4) < 0.01
        col[f | butt] = _rgb("#3A3125")
        out["height"][f | butt] -= 0.006
        col *= (1 + 0.1 * (vnoise(k * 4.1, k, ctx.seed) - 0.5))[..., None]
    col[:] = _mix(col, "#8C8A80", 0.25 * ctx.w)
    return out


def p_break(A, B, isl, ctx, ox, oy):
    out = _new(A, isl.get("color") or ctx.P["bulwark"], 0.55)
    _dirt(out, A, B, ctx, 0.16)
    return out


PAINTERS = {"hull": p_hull, "transom": p_transom, "deck": p_deck, "bulwark": p_bulwark, "rail": p_rail,
            "break": p_break, "paint": p_paint, "varnish": p_varnish, "roof": p_roof, "canvas": p_canvas,
            "tarp": p_tarp, "net": p_net, "metal": p_metal, "mast": p_mast, "funnel": p_funnel,
            "timber": p_timber, "timber_end": p_timber}


def paint(vid, out_dir=TEX):
    """Paint the vessel's atlas: base colour, roughness, metal, normal (OpenGL), emission."""
    from PIL import Image
    ctx = Ctx(vid)
    m = make(vid)
    col = np.zeros((N, N, 3))
    col[:] = _rgb("#555555")
    rough, metal = np.full((N, N), 0.8), np.zeros((N, N))
    nrm = np.zeros((N, N, 3))
    nrm[:] = (0.5, 0.5, 1.0)
    emit = np.zeros((N, N, 3))
    for isl in m.isl:
        x0, y0, w, h = isl["rect"]
        cx0, cy0 = max(x0 - PAD, 0), max(y0 - PAD, 0)
        cx1, cy1 = min(x0 + w + PAD, N), min(y0 + h + PAD, N)
        if isl["shared"]:
            c, r, e = SHARED_LOOK[isl["kind"]]
            col[cy0:cy1, cx0:cx1] = _rgb(c)
            rough[cy0:cy1, cx0:cx1] = r
            if e and ctx.lit:
                emit[cy0:cy1, cx0:cx1] = e
            continue
        cc, rr = np.meshgrid(np.arange(cx0, cx1) + 0.5, np.arange(cy0, cy1) + 0.5)
        q = isl["ppm"]
        if isl["rot"]:
            B = isl["b0"] + (cc - x0) / q
            A = isl["a0"] + (rr - y0) / q
        else:
            A = isl["a0"] + (cc - x0) / q
            B = isl["b0"] + (y0 + h - rr) / q
        o = PAINTERS[isl["kind"]](A, B, isl, ctx, cx0, cy0)
        col[cy0:cy1, cx0:cx1] = np.clip(o["col"], 0, 1)
        rough[cy0:cy1, cx0:cx1] = np.clip(o["rough"], 0.04, 1)
        metal[cy0:cy1, cx0:cx1] = o["metal"]
        emit[cy0:cy1, cx0:cx1] = np.clip(o["emit"], 0, 1)
        hm = o["height"]
        dx = (np.roll(hm, -1, 1) - np.roll(hm, 1, 1)) * 0.5 * q
        dy = (np.roll(hm, -1, 0) - np.roll(hm, 1, 0)) * 0.5 * q
        dx[:, [0, -1]] = 0
        dy[[0, -1], :] = 0
        if isl["rot"]:      # the island's pixel axes are (b, -a): tangent space follows the UVs, nothing to do
            pass
        nx, ny, nz = -dx, dy, np.ones_like(hm)
        ln = np.sqrt(nx * nx + ny * ny + nz * nz)
        nrm[cy0:cy1, cx0:cx1] = np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5
    out_dir.mkdir(parents=True, exist_ok=True)
    Id = VESSELS[vid]["Id"]
    files = {}

    def save(a, name, mode):
        p = out_dir / ("T_Vessel_%s_%s.png" % (Id, name))
        Image.fromarray(np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8), mode).save(p)
        files[name] = str(p.relative_to(WS))
    save(col, "base", "RGB")
    save(rough, "rough", "L")
    save(metal, "metal", "L")
    save(nrm, "normal", "RGB")
    if emit.max() > 0:
        save(emit, "emit", "RGB")
    return dict(vid=vid, files=files, emissive=bool(emit.max() > 0), ppm=round(m.meta["ppm"], 1))


# ------------------------------------------------------------------ GLB reader and checks (host; pytest uses it)
def read_glb(path):
    data = Path(path).read_bytes()
    assert data[:4] == b"glTF", "not a GLB"
    off, js, binc = 12, None, b""
    while off < len(data):
        ln, typ = struct.unpack("<I4s", data[off:off + 8])
        chunk = data[off + 8:off + 8 + ln]
        if typ == b"JSON":
            js = json.loads(chunk)
        elif typ == b"BIN\x00":
            binc = chunk
        off += 8 + ln
    return js, binc


def accessor(js, binc, i):
    a = js["accessors"][i]
    bv = js["bufferViews"][a["bufferView"]]
    comp = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a["componentType"]]
    ncomp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride", 0)
    item = np.dtype(comp).itemsize * ncomp
    if stride and stride != item:
        raw = np.frombuffer(binc, np.uint8, count=stride * a["count"], offset=start).reshape(a["count"], stride)
        return raw[:, :item].copy().view(comp).reshape(a["count"], ncomp)
    return np.frombuffer(binc, comp, count=a["count"] * ncomp, offset=start).reshape(a["count"], ncomp)


def latest_glb(export_name, root=EXPORTS):
    fs = sorted(Path(root).glob(export_name + "_v[0-9][0-9][0-9].glb"))
    return fs[-1] if fs else None


def glb_checks(path, vid):
    """The exported file as Godot will read it: glTF Y-up, bow -Z, port -X."""
    V = VESSELS[vid]
    js, binc = read_glb(path)
    r = {"vid": vid, "file": str(Path(path).name)}
    P, NRM, UV, IDX = [], [], [], []
    mats = set()
    voff = 0
    for mesh in js.get("meshes", []):
        for pr in mesh["primitives"]:
            pos = accessor(js, binc, pr["attributes"]["POSITION"]).astype(np.float64)
            nr = accessor(js, binc, pr["attributes"]["NORMAL"]).astype(np.float64)
            uv = accessor(js, binc, pr["attributes"]["TEXCOORD_0"]).astype(np.float64)
            ix = accessor(js, binc, pr["indices"]).astype(np.int64).reshape(-1, 3)
            P.append(pos)
            NRM.append(nr)
            UV.append(uv)
            IDX.append(ix + voff)
            voff += len(pos)
            mats.add(pr.get("material"))
    P, NRM, UV, IDX = np.vstack(P), np.vstack(NRM), np.vstack(UV), np.vstack(IDX)
    r["tris"] = int(len(IDX))
    r["materials"] = len(js.get("materials", []))
    r["material_names"] = [m_.get("name") for m_ in js.get("materials", [])]
    r["uv_sets"] = max(len([k for k in pr["attributes"] if k.startswith("TEXCOORD")])
                       for mesh in js["meshes"] for pr in mesh["primitives"])
    imgs = []
    for im in js.get("images", []):
        bv = js["bufferViews"][im["bufferView"]]
        b = binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + 24]
        imgs.append(struct.unpack(">II", b[16:24]) if b[:8] == b"\x89PNG\r\n\x1a\n" else None)
    r["images"] = imgs
    a, b, c = P[IDX[:, 0]], P[IDX[:, 1]], P[IDX[:, 2]]
    fn = np.cross(b - a, c - a)
    area = np.linalg.norm(fn, axis=1)
    vn = NRM[IDX[:, 0]] + NRM[IDX[:, 1]] + NRM[IDX[:, 2]]
    ok = area > 1e-10
    agree = (np.einsum("ij,ij->i", fn[ok], vn[ok]) > 0).mean()
    r["normals_agree_winding"] = round(float(agree), 4)
    # signed volume per welded shell
    key = np.round(P / 1e-4).astype(np.int64)
    _, weld = np.unique(key, axis=0, return_inverse=True)
    weld = weld.reshape(-1)
    T = weld[IDX]
    parent = np.arange(weld.max() + 1)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for t0, t1, t2 in T:
        r0, r1, r2 = find(t0), find(t1), find(t2)
        parent[r1] = r0
        parent[find(r2)] = r0
    roots = np.array([find(t) for t in T[:, 0]])
    vol = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0
    shells = defaultdict(float)
    for rt, v in zip(roots, vol):
        shells[rt] += v
    r["shells"] = len(shells)
    r["inward_shells"] = int(sum(v <= 0 for v in shells.values()))
    r["uv_in_unit"] = bool(((UV >= -1e-6) & (UV <= 1 + 1e-6)).all())
    names = [n.get("name", "") for n in js.get("nodes", [])]
    empt = {n["name"]: n.get("translation", [0, 0, 0]) for n in js.get("nodes", []) if "mesh" not in n}
    r["nodes"] = names
    need = EMPTY_NAMES + (("DECK_aft",) if V["design"] == "coaster" else ())
    r["empties_missing"] = [e for e in need if e not in empt]
    r["hint_suffix_names"] = [n for n in names if n.lower().endswith(HINT_SUFFIXES)]
    r["bounds_min"] = [round(float(x), 3) for x in P.min(0)]
    r["bounds_max"] = [round(float(x), 3) for x in P.max(0)]
    r["bow_is_minus_z"] = bool(empt.get("NAV_stern", [0, 0, 0])[2] > 0 and float(P[:, 2].min()) < -0.4 * (
        float(P[:, 2].max() - P[:, 2].min())))
    r["port_is_minus_x"] = bool(empt.get("NAV_port", [1, 0, 0])[0] < 0 < empt.get("NAV_starboard", [-1, 0, 0])[0])
    fails = []
    if not TRI_MIN <= r["tris"] <= TRI_MAX:
        fails.append("tris")
    if r["materials"] != 1 or len(mats) != 1:
        fails.append("materials")
    if r["normals_agree_winding"] < 0.995:
        fails.append("normals")
    if r["inward_shells"]:
        fails.append("inward shells")
    if r["uv_sets"] != 1 or not r["uv_in_unit"]:
        fails.append("uv")
    if r["empties_missing"] or r["hint_suffix_names"]:
        fails.append("names")
    if not (r["bow_is_minus_z"] and r["port_is_minus_x"]):
        fails.append("axes")
    if any(i is None or i != (N, N) for i in imgs):
        fails.append("textures not 1024")
    if V["kind"]:
        dx, dy, dz = DIMS[V["kind"]]
        if (P[:, 0].max() - P[:, 0].min()) > dx + 1e-3 or (P[:, 2].max() - P[:, 2].min()) > dz + 1e-3:
            fails.append("DIMS")
    r["result"] = "FAIL" if fails else "PASS"
    r["fails"] = fails
    return r


# ------------------------------------------------------------------ Blender
def _bl_img_load(path, colorspace):
    img = bpy.data.images.load(str(path), check_existing=False)
    img.colorspace_settings.name = colorspace
    return img


def _bl_pixels(img):
    a = np.empty(N * N * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(N, N, 4)[::-1].copy()            # top-down, as the painter's rows


def _bl_save(arr_rgb, path, name, colorspace):
    rgba = np.ones((N, N, 4), np.float32)
    rgba[..., :3] = arr_rgb if arr_rgb.ndim == 3 else arr_rgb[..., None]
    img = bpy.data.images.new(name, N, N, alpha=False)
    img.colorspace_settings.name = colorspace
    img.pixels.foreach_set(rgba[::-1].ravel())
    img.filepath_raw = str(path)
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def _gltf_group():
    ng = bpy.data.node_groups.get("glTF Material Output")
    if ng is None:
        ng = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        ng.interface.new_socket(name="Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    return ng


def bl_material(V, albedo, orm, normal, emit):
    name = "M_Vessel_" + V["Id"]
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    L = nt.links
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    L.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    def tex(img, x, y):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = img
        n.location = (x, y)
        return n
    tb = tex(albedo, -700, 300)
    L.new(tb.outputs["Color"], bsdf.inputs["Base Color"])
    to = tex(orm, -700, 0)
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    sep.location = (-400, 0)
    L.new(to.outputs["Color"], sep.inputs["Color"])
    L.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
    L.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
    tn = tex(normal, -700, -300)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.location = (-400, -300)
    L.new(tn.outputs["Color"], nm.inputs["Color"])
    L.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    if emit is not None:
        te = tex(emit, -700, -600)
        L.new(te.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 2.0
    g = nt.nodes.new("ShaderNodeGroup")
    g.node_tree = _gltf_group()
    g.location = (-150, 250)
    L.new(sep.outputs["Red"], g.inputs["Occlusion"])
    return mat


def bl_build(vid):
    """Mesh object, empties (named NAV_x.<vid> in the .blend; --export strips the suffix), AO bake, material."""
    from lib.scene_utils import get_collection
    V = VESSELS[vid]
    m = make(vid)
    coll = get_collection("ASSET_" + V["export"])
    me = bpy.data.meshes.new("SM_Vessel_" + V["Id"])
    me.from_pydata(m.v, [], [tuple(f) for f in m.f])
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    uvl.data.foreach_set("uv", np.asarray([c for f in corner_uvs(m) for c in f], np.float32).ravel())
    me.polygons.foreach_set("use_smooth", m.fs)
    me.set_sharp_from_angle(angle=math.radians(40))
    me.validate()
    ob = bpy.data.objects.new(me.name, me)
    coll.objects.link(ob)
    for name, p in m.empties.items():
        e = bpy.data.objects.new("%s.%s" % (name, vid), None)
        e.empty_display_type = "SPHERE"
        e.empty_display_size = 0.15
        e.location = p
        coll.objects.link(e)
    return ob, m


def bl_bake_ao(ob, m, vid):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 64
    sc.cycles.device = "CPU"
    if sc.world is None:
        sc.world = bpy.data.worlds.new("World")
    H = m.meta["hull"]
    sc.world.light_settings.distance = max(0.8, 0.12 * H.B)
    tmp = bpy.data.materials.new("bake_tmp")
    tmp.use_nodes = True
    img = bpy.data.images.new("ao_" + vid, N, N, alpha=False)
    img.colorspace_settings.name = "Non-Color"
    n = tmp.node_tree.nodes.new("ShaderNodeTexImage")
    n.image = img
    tmp.node_tree.nodes.active = n
    ob.data.materials.clear()
    ob.data.materials.append(tmp)
    hidden = []
    for o in bpy.data.objects:
        o.select_set(False)
        if o is not ob and o.type == "MESH" and not o.hide_render:
            o.hide_render = True
            hidden.append(o)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.bake(type="AO", margin=PAD, use_clear=True)
    ao = _bl_pixels(img)[..., 0]
    for o in hidden:
        o.hide_render = False
    ob.data.materials.clear()
    bpy.data.materials.remove(tmp)
    bpy.data.images.remove(img)
    for isl in m.isl:                          # uniform kinds share pixels: no meaningful AO there
        if isl["shared"]:
            x0, y0, w, h = isl["rect"]
            ao[max(y0 - PAD, 0):y0 + h + PAD, max(x0 - PAD, 0):x0 + w + PAD] = 1.0
    return ao


def bl_finish(ob, m, vid, ao):
    V = VESSELS[vid]
    Id = V["Id"]
    f = lambda k: TEX / ("T_Vessel_%s_%s.png" % (Id, k))     # noqa: E731
    base = _bl_pixels(_bl_img_load(f("base"), "sRGB"))[..., :3]
    rough = _bl_pixels(_bl_img_load(f("rough"), "Non-Color"))[..., 0]
    metal = _bl_pixels(_bl_img_load(f("metal"), "Non-Color"))[..., 0]
    for img in list(bpy.data.images):
        if img.users == 0:
            bpy.data.images.remove(img)
    ao = np.clip(ao, 0, 1)
    _bl_save(base * (0.62 + 0.38 * ao[..., None]), f("albedo"), "albedo_tmp", "sRGB")
    _bl_save(np.stack([ao, rough, metal], -1), f("orm"), "orm_tmp", "Non-Color")
    imgs = dict(albedo=_bl_img_load(f("albedo"), "sRGB"), orm=_bl_img_load(f("orm"), "Non-Color"),
                normal=_bl_img_load(f("normal"), "Non-Color"),
                emit=_bl_img_load(f("emit"), "sRGB") if f("emit").exists() and V["lit"] else None)
    for k, img in imgs.items():
        if img is not None:
            img.name = "T_Vessel_%s_%s" % (Id, k)
            img.pack()
    mat = bl_material(V, imgs["albedo"], imgs["orm"], imgs["normal"], imgs["emit"])
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return dict(ao_mean=round(float(ao.mean()), 3), ao_min=round(float(ao.min()), 3))


def bl_mesh_check(ob):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    me = ob.data
    me.calc_loop_triangles()
    return dict(bl_tris=len(me.loop_triangles), bl_nonmanifold=nm, bl_materials=len(me.materials),
                bl_uv_layers=len(me.uv_layers))


def bl_export(vids, out):
    sys.path.insert(0, str(WS / "scripts"))
    sys.path.insert(0, str(WS / "scripts" / "exports"))
    from export_asset import export_one
    res = []
    for vid in vids:
        V = VESSELS[vid]
        coll = bpy.data.collections["ASSET_" + V["export"]]
        objs = [o for o in coll.all_objects if o.type in {"MESH", "EMPTY"}]
        renamed = []
        for o in objs:
            if o.type == "EMPTY" and "." in o.name:
                old = o.name
                o.name = old.split(".")[0]
                assert o.name == old.split(".")[0], "name clash for " + old
                renamed.append((o, old))
        try:
            res.append(export_one("gltf", objs, out, V["export"], ""))
        finally:
            for o, old in renamed:
                o.name = old
    return res


# ------------------------------------------------------------------ CLI
def _args(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--paint", action="store_true")
    ap.add_argument("--check-glb", nargs="*", default=None)
    ap.add_argument("--new", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--bake", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--export", default="")
    ap.add_argument("--out", default="exports/last_light")
    ap.add_argument("--json", default="")
    return ap.parse_args(argv)


def main():
    if bpy is not None:
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        sys.path.insert(0, str(WS / "scripts"))
    else:
        argv = sys.argv[1:]
    a = _args(argv)
    vids = [v for v in a.only.split(",") if v] or ORDER
    res = {}
    if bpy is None:
        if a.report:
            res["report"] = {v: checks(make(v), v) for v in vids}
        if a.paint:
            res["paint"] = [paint(v) for v in vids]
        if a.check_glb is not None:
            out = {}
            for v in vids:
                pth = latest_glb(VESSELS[v]["export"])
                out[v] = glb_checks(pth, v) if pth else {"result": "MISSING"}
            res["glb"] = out
        tag = "VESSELS_RESULT"
    else:
        from lib.scene_utils import clear_scene, save_versioned, set_metric_units
        if a.new:
            clear_scene()
            set_metric_units()
        if a.build:
            res["build"] = {}
            for v in vids:
                ob, m = bl_build(v)
                r = checks(m, v)
                if a.bake:
                    ao = bl_bake_ao(ob, m, v)
                    r.update(bl_finish(ob, m, v, ao))
                if a.check:
                    r.update(bl_mesh_check(ob))
                    if r["bl_nonmanifold"] or r["bl_tris"] != r["tris"] or r["bl_materials"] != 1:
                        r["result"] = "FAIL"
                        r["fails"].append("blender mesh")
                res["build"][v] = {k: r[k] for k in r if k not in ("empties",)}
        if a.save:
            res["saved"] = save_versioned(HERE, "last_light_vessels")
        if a.export:
            ex = ORDER if a.export == "all" else a.export.split(",")
            res["export"] = bl_export(ex, a.out)
        tag = "VESSELS_RESULT"
    txt = json.dumps(res, default=str)
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1, default=str))
    print(tag, txt)


if __name__ == "__main__":
    main()
