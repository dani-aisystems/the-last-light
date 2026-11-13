"""THE LAST LIGHT G6d (stage C): North Point's island, landing and walkway (ASSET_island) and the title-only
keeper's boat (ASSET_boat). Called from build.py, which passes itself as `H` (its geometry helpers: box, cyl,
seg_cyl, sphere, torus, basis, wall_frame, ...) to avoid a circular import.

Blender coordinates, metres, Z up; Godot is (x, z, -y). A bearing b points along (sin b, cos b).
Canon and layout this has to agree with:
  - the island radius 21 (spec.py layout; ships collide with that circle), the tower plinth 1.4-3.6 m;
  - the landing at bearing 028: the pier root 18.5 m out, deck top 1.2 m, 9 m long (outside.gd had it
    as a procedural stand-in; the visitor's launch docks at its head in ch4, keeper_sim / chapters.json);
  - the base door at bearing 35, its granite step 5.99-6.61 m out, top 3.5 m (build.py build_entrance);
  - the storm comes from the south-west: that side is the steeper, barer, more broken one.
Everything is deterministic (mathutils.noise, fixed offsets), so rebuilds are identical.
"""

import math

import bmesh
from mathutils import Vector, noise

LANDING_B = 28.0
LANDING_R = 18.5
PIER_LEN, PIER_W, DECK_TOP = 9.0, 3.2, 1.2
STEP_N, STEP_RISE, STEP_RUN, STEP_Y0, STEP_X = 8, 0.3, 0.45, 1.25, -0.6
DOOR_B, DOOR_STEP_R, DOOR_STEP_TOP = 35.0, 6.65, 3.5
WALK_W = 1.0
# knolls: (bearing, distance, height, radius). None near the tower, the landing (028) or the walkway.
KNOLLS = ((228.0, 13.0, 2.4, 4.6), (262.0, 9.8, 1.6, 3.4), (196.0, 15.0, 1.5, 3.6), (318.0, 12.5, 1.3, 3.0),
          (112.0, 14.5, 1.0, 3.0), (152.0, 11.5, 0.9, 2.8), (75.0, 16.5, 0.8, 2.4))


def _smooth(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def _frame(bearing_deg):
    b = math.radians(bearing_deg)
    o = Vector((math.sin(b), math.cos(b), 0.0))      # outward
    r = Vector((math.cos(b), -math.sin(b), 0.0))     # right, looking outward
    return r, o, Vector((0, 0, 1))


def _seg_dist(p, a, b):
    """Distance from p to segment ab (2D) and the parameter t along it."""
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length, t


# ------------------------------------------------------------------ the island's shape

def coast_r(theta):
    """Coastline radius on bearing theta (radians): 19-24 m, smaller and harder on the weather side."""
    n = noise.noise(Vector((math.sin(theta) * 1.9, math.cos(theta) * 1.9, 7.3)))
    n2 = noise.noise(Vector((math.sin(theta) * 5.1, math.cos(theta) * 5.1, 2.1)))
    sw = max(math.cos(theta - math.radians(225.0)), 0.0)
    return 21.6 + 2.2 * n + 0.7 * n2 - 1.4 * sw


def landing_line():
    """2D points: the top of the landing steps and the foot of the door step (the walkway's ends)."""
    r, o, _ = _frame(LANDING_B)
    root = o * LANDING_R
    top = root - o * (0.3 + (STEP_N - 1) * STEP_RUN + 0.35) + r * STEP_X
    d = _frame(DOOR_B)[1] * DOOR_STEP_R
    return Vector((top.x, top.y)), Vector((d.x, d.y))


def ground_h(x, y):
    """Terrain height (m) at (x, y): a turf crown round the tower, ledged slopes, a cliff toe into the sea,
    a cut for the landing steps and a levelled bed under the walkway."""
    p = Vector((x, y))
    rr = p.length
    th = math.atan2(x, y)
    rc = coast_r(th)
    sw = max(math.cos(th - math.radians(225.0)), 0.0)
    shoulder = rc - (8.5 - 3.5 * sw)            # the crown ends sooner on the weather side
    top = 3.45 - 0.035 * rr
    if rr < shoulder:
        # rough turf over rock: broad swells and small hummocks, not a level lawn (capture g6d_c: "a pancake")
        h = top + 0.22 * noise.noise(Vector((x * 0.22, y * 0.22, 1.0))) + 0.08 * noise.noise(Vector((x * 0.9, y * 0.9, 4.0)))
    else:
        s = min((rr - shoulder) / max(rc - shoulder, 0.5), 1.0)
        v = top * (1.0 - s ** 1.25) + 0.25 * s ** 1.25
        q = 0.7                                   # ledges: flats and short steep risers
        fv = v / q
        terr = q * (math.floor(fv) + _smooth(0.62, 1.0, fv - math.floor(fv)))
        h = v * 0.35 + terr * 0.65
        h += (0.25 + 0.3 * sw) * noise.noise(Vector((x * 0.6, y * 0.6, 3.0))) * s
    # rock knolls standing out of the turf, bigger and barer on the weather side (bearing, r, height, radius)
    for kb, kr, kh, krad in KNOLLS:
        kp = Vector((kr * math.sin(math.radians(kb)), kr * math.cos(math.radians(kb))))
        d = (p - kp).length
        if d < krad * 2.2:
            bump = kh * math.exp(-(d / krad) ** 2)
            bump *= 1.0 + 0.35 * noise.noise(Vector((x * 0.8, y * 0.8, kb)))
            h += bump
    if rr > rc:                                   # the cliff toe, down under the sea
        h = min(h, 0.25) - 3.4 * _smooth(rc, rc + 2.6, rr)
        h += 0.35 * noise.noise(Vector((x * 0.9, y * 0.9, 5.0)))
    # the plinth: level turf round the tower's stone plinth (its top 3.6 m shows a hand's width)
    if rr < 7.2:
        h = h + (3.3 + 0.03 * noise.noise(Vector((x, y, 9.0))) - h) * (1.0 - _smooth(6.0, 7.2, rr))
    # the landing cut: the rock dressed to the line of the steps
    rgt, out, _ = _frame(LANDING_B)
    root = out * LANDING_R
    a = Vector(((root - out * 0.3 + rgt * STEP_X).x, (root - out * 0.3 + rgt * STEP_X).y))
    b = Vector(((root - out * (0.3 + STEP_N * STEP_RUN) + rgt * STEP_X).x,
                (root - out * (0.3 + STEP_N * STEP_RUN) + rgt * STEP_X).y))
    d, t = _seg_dist(p, a, b)
    if d < 2.6:
        line = STEP_Y0 + t * (STEP_N - 1) * STEP_RISE - 0.2
        h = h + (line - h) * (1.0 - _smooth(1.2, 2.6, d))
    # the walkway's bed: levelled a little below the boards
    w0, w1 = landing_line()
    d, t = _seg_dist(p, w0, w1)
    if d < 2.2:
        bed = (STEP_Y0 + (STEP_N - 1) * STEP_RISE) * (1 - t) + DOOR_STEP_TOP * t - 0.28
        h = h + (bed - h) * (1.0 - _smooth(0.8, 2.2, d))
    return h


def build_island(H, B):
    """The terrain as a polar grid (fine at the shore, coarse at the crown), plus boulders on the coast."""
    bm = B.bm("M_LL_Terrain", "SM_Island")
    segs = 200
    radii = [0.0]
    r = 0.8
    while r < 29.0:
        radii.append(r)
        r += 0.55 if r < 12.0 else 0.38
    rows = []
    centre = bm.verts.new((0.0, 0.0, ground_h(0.0, 0.0)))
    for rr in radii[1:]:
        row = []
        for k in range(segs):
            a = 2.0 * math.pi * k / segs
            x, y = rr * math.sin(a), rr * math.cos(a)
            row.append(bm.verts.new((x, y, ground_h(x, y))))
        rows.append(row)
    for k in range(segs):
        bm.faces.new((centre, rows[0][k], rows[0][(k + 1) % segs]))
    for i in range(len(rows) - 1):
        a_, b_ = rows[i], rows[i + 1]
        for k in range(segs):
            k1 = (k + 1) % segs
            bm.faces.new((a_[k], b_[k], b_[k1], a_[k1]))
    # coastal boulders: broken, wet, away from the landing
    rock = B.bm("M_LL_Rock", "SM_IslandRocks")
    for i in range(34):
        b = 360.0 * (i + 0.37 * math.sin(i * 12.9898)) / 34
        if abs(((b - LANDING_B + 180) % 360) - 180) < 11.0:
            continue
        th = math.radians(b)
        rr = coast_r(th) + 0.4 + 1.4 * (0.5 + 0.5 * math.sin(i * 78.233))
        size = 0.55 + 1.1 * (0.5 + 0.5 * math.sin(i * 3.7))
        x, y = rr * math.sin(th), rr * math.cos(th)
        _boulder(bm_=rock, c=Vector((x, y, ground_h(x, y) + size * 0.25)), size=size, seed=i)
    build_landing(H, B)
    build_walkway(H, B)


def _boulder(bm_, c, size, seed):
    res = bmesh.ops.create_icosphere(bm_, subdivisions=2, radius=1.0)
    for v in res["verts"]:
        d = v.co.normalized()
        n = noise.noise(d * 1.7 + Vector((seed * 3.1, seed * 1.7, 0.0)))
        k = 1.0 + 0.32 * n
        v.co = c + Vector((d.x * size * 1.25 * k, d.y * size * k, d.z * size * 0.7 * k))


# ------------------------------------------------------------------ the landing

def build_landing(H, B):
    """The Board's landing: the concrete pier kept, with weathered timber decking, piles and wales, an iron
    ladder, bollards and a coil of rope; concrete steps up the cut in the rock, with an iron handrail."""
    r, o, u = _frame(LANDING_B)
    bs = H.basis(r, o, u)
    root = o * LANDING_R
    conc = B.bm("M_LL_ConcreteExt", "SM_Landing")
    wood = B.bm("M_LL_WoodDark", "SM_Landing")
    iron = B.bm("M_LL_Iron", "SM_Landing")
    deck_c = root + o * (PIER_LEN / 2)
    H.box(conc, deck_c + u * (DECK_TOP - 2.2), (PIER_W, PIER_LEN, 4.4), bs)
    # timber decking across the pier, 24 cm boards with gaps
    k = 0
    a = 0.25
    while a < PIER_LEN - 0.2:
        H.box(wood, root + o * a + u * (DECK_TOP + 0.03) + r * (0.006 * math.sin(k * 2.3)),
              (PIER_W - 0.1, 0.2, 0.06), bs)
        a += 0.24
        k += 1
    # piles and wales on both sides
    for sd in (-1, 1):
        for i in range(7):
            along = 0.6 + i * (PIER_LEN - 1.2) / 6
            H.cyl(wood, root + o * along + r * (sd * (PIER_W / 2 + 0.15)) + u * (DECK_TOP - 1.9), 0.15, 0.14, 4.6, 10)
        for z in (DECK_TOP - 0.55, DECK_TOP - 0.1):
            H.box(wood, deck_c + r * (sd * (PIER_W / 2 + 0.3)) + u * z, (0.16, PIER_LEN - 0.4, 0.2), bs)
        for along in (2.0, PIER_LEN - 1.2):           # bollards with caps
            bp = root + o * along + r * (sd * (PIER_W / 2 - 0.35)) + u * (DECK_TOP + 0.06)
            H.cyl(iron, bp + u * 0.22, 0.17, 0.14, 0.44, 14)
            H.cyl(iron, bp + u * 0.46, 0.21, 0.21, 0.05, 14)
    # an iron ladder down the right side near the head
    lad = root + o * (PIER_LEN - 2.4) + r * (PIER_W / 2 + 0.42)
    for s_ in (-0.22, 0.22):
        H.seg_cyl(iron, lad + o * s_ + u * (DECK_TOP + 0.9), lad + o * s_ + u * -1.6, 0.022, 6)
    for i in range(10):
        z = DECK_TOP + 0.6 - i * 0.28
        H.seg_cyl(iron, lad + o * -0.22 + u * z, lad + o * 0.22 + u * z, 0.014, 6)
    # a coil of rope by the left bollard
    rope = B.bm("M_LL_Rope", "SM_Landing")
    rc_ = root + o * 3.1 + r * (-(PIER_W / 2) + 0.75) + u * (DECK_TOP + 0.08)
    for j in range(3):
        H.torus(rope, rc_ + u * (j * 0.045), 0.32 - j * 0.035, 0.025, 20, 6)
    # the steps up the cut, each one carried down into the rock
    for i in range(STEP_N):
        c = root - o * (0.3 + i * STEP_RUN) + r * STEP_X
        top = STEP_Y0 + i * STEP_RISE + 0.16
        H.box(conc, c + u * (top - 0.7), (1.4, STEP_RUN + 0.02, 1.4), bs)
    # handrail on the open side of the steps
    p0 = root - o * 0.1 + r * (STEP_X - 0.75)
    p1 = root - o * (0.3 + (STEP_N - 1) * STEP_RUN) + r * (STEP_X - 0.75)
    posts = []
    for i in range(5):
        t = i / 4
        pp = p0.lerp(p1, t)
        z = STEP_Y0 + 0.16 + t * (STEP_N - 1) * STEP_RISE
        H.seg_cyl(iron, pp + u * (z - 0.1), pp + u * (z + 0.95), 0.022, 6)
        posts.append(pp + u * (z + 0.95))
    for i in range(4):
        H.seg_cyl(iron, posts[i], posts[i + 1], 0.024, 8)


# ------------------------------------------------------------------ the walkway

def build_walkway(H, B):
    """Timber boards on sleepers from the top of the landing steps to the door step, laid on the levelled bed,
    with an iron handrail on the seaward side."""
    w0, w1 = landing_line()
    a3 = Vector((w0.x, w0.y, 0.0))
    b3 = Vector((w1.x, w1.y, 0.0))
    along = (b3 - a3)
    length = along.length
    fwd = along.normalized()
    side = Vector((fwd.y, -fwd.x, 0.0))
    up = Vector((0, 0, 1))
    bs = H.basis(side, fwd, up)
    wood = B.bm("M_LL_WoodDark", "SM_Walkway")
    iron = B.bm("M_LL_Iron", "SM_Walkway")
    z0, z1 = STEP_Y0 + (STEP_N - 1) * STEP_RISE + 0.16, DOOR_STEP_TOP

    def z_at(t):
        return z0 * (1 - t) + z1 * t - 0.03

    # sleepers every 1.1 m
    s = 0.3
    while s < length - 0.2:
        t = s / length
        H.box(wood, a3 + fwd * s + up * (z_at(t) - 0.1), (WALK_W + 0.2, 0.14, 0.1), bs)
        s += 1.1
    # boards across the way
    s, k = 0.1, 0
    while s < length - 0.05:
        t = s / length
        H.box(wood, a3 + fwd * s + side * (0.01 * math.sin(k * 1.7)) + up * (z_at(t) - 0.02), (WALK_W, 0.16, 0.04), bs)
        s += 0.19
        k += 1
    # handrail on the seaward (right-hand, walking up) side
    n = max(int(length / 1.6), 2)
    tops = []
    for i in range(n + 1):
        t = i / n
        p = a3 + fwd * (length * t) + side * (WALK_W / 2 + 0.06)
        H.seg_cyl(iron, p + up * (z_at(t) - 0.15), p + up * (z_at(t) + 0.95), 0.022, 6)
        tops.append(p + up * (z_at(t) + 0.95))
    for i in range(n):
        H.seg_cyl(iron, tops[i], tops[i + 1], 0.024, 8)
        H.seg_cyl(iron, tops[i] - up * 0.5, tops[i + 1] - up * 0.5, 0.016, 6)


# ------------------------------------------------------------------ the keeper's boat (title only)

BOAT_L, BOAT_BEAM, BOAT_DEPTH = 4.3, 1.55, 0.62
STRAKES = 6


def _hull_point(x, s, side, inset=0.0):
    """A point on the hull surface. x along (bow +), s 0 at the keel .. 1 at the sheer, side +1/-1. `inset`
    moves it in toward the centreline (and up at the bottom): the inside skin."""
    u = max(-1.0, min(1.0, x / (BOAT_L / 2)))
    if u >= 0:
        half = BOAT_BEAM / 2 * max(1 - u ** 2.2, 0.0) ** 0.55      # fine entry to a stem at the bow
    else:
        half = BOAT_BEAM / 2 * (1 - 0.38 * (-u) ** 2.5)              # full quarters to a wide transom
    sheer = 0.55 + 0.16 * u * u + (0.05 * u if u > 0 else 0.0)        # the sheer rises to the bow
    keel = -0.12 + 0.1 * u ** 4
    ang = s * math.pi / 2
    y = half * math.sin(ang) ** 0.75
    z = keel + (sheer - keel) * (1 - math.cos(ang)) ** 0.9
    if inset:
        return Vector((x, side * max(y - inset, 0.0), z + inset * (1.0 - s)))
    return Vector((x, side * y, z))


def build_boat(H, B):
    """A 4.3 m clinker-built wooden workboat of the kind kept at Hebridean landings, painted, with two thwarts,
    bottom boards, a transom-hung outboard and a bow ring for the painter (ROPE_bow). The shell is two-sided
    in Godot (StandardMaterial, cull off), so its surfaces need no closing."""
    paint = bmesh.new()
    paint.loops.layers.uv.new("UVMap")
    inner = bmesh.new()
    inner.loops.layers.uv.new("UVMap")
    stations = 28
    xs = [-BOAT_L / 2 + BOAT_L * i / stations for i in range(stations + 1)]
    lap = 0.014
    for side in (1, -1):
        for sk in range(STRAKES):
            s0, s1 = sk / STRAKES, (sk + 1) / STRAKES
            lo, hi = [], []
            for x in xs:
                pl = _hull_point(x, s0, side)
                ph = _hull_point(x, s1, side)
                # the clinker lap: each strake's lower edge stands proud of the one below
                out = Vector((0.0, side, -0.25)).normalized() * lap if sk > 0 else Vector()
                lo.append(paint.verts.new(pl + out))
                hi.append(paint.verts.new(ph))
            for i in range(stations):
                f = (lo[i], lo[i + 1], hi[i + 1], hi[i]) if side > 0 else (lo[i], hi[i], hi[i + 1], lo[i + 1])
                paint.faces.new(f)
        # the inside: one smooth skin a little in from the planking
        rows = []
        for sk in range(STRAKES + 1):
            s = sk / STRAKES
            rows.append([inner.verts.new(_hull_point(x, s, side, inset=0.03)) for x in xs])
        for sk in range(STRAKES):
            for i in range(stations):
                a_, b_ = rows[sk], rows[sk + 1]
                f = (a_[i], b_[i], b_[i + 1], a_[i + 1]) if side > 0 else (a_[i], a_[i + 1], b_[i + 1], b_[i])
                inner.faces.new(f)
    # transom: a flat board across the stern
    st = -BOAT_L / 2
    pts = [_hull_point(st, k / 8, 1) for k in range(9)] + [_hull_point(st, 1 - k / 8, -1) for k in range(9)]
    tv = [paint.verts.new(p) for p in pts]
    paint.faces.new(tv)
    B.mesh_obj("SM_Boat_Hull", paint, "M_LL_BoatPaint", keep_uv=True)
    B.mesh_obj("SM_Boat_Inside", inner, "M_LL_BoatWood", keep_uv=True)
    wood = B.bm("M_LL_BoatWood", "SM_Boat")
    # gunwale rails, thwarts, bottom boards, a stem post
    for side in (1, -1):
        for i in range(stations):
            p0 = _hull_point(xs[i], 1.0, side)
            p1 = _hull_point(xs[i + 1], 1.0, side)
            H.seg_cyl(wood, p0 + Vector((0, 0, 0.015)), p1 + Vector((0, 0, 0.015)), 0.028, 6)
    for x, w in ((0.55, 1.0), (-0.85, 1.0)):
        sh = _hull_point(x, 1.0, 1)
        H.box(wood, (x, 0.0, sh.z - 0.2), (0.24, sh.y * 2 - 0.08, 0.035), None)
    for k in range(-2, 3):
        H.box(wood, (0.0, k * 0.14, -0.05), (BOAT_L * 0.62, 0.11, 0.025), None)
    bow = _hull_point(BOAT_L / 2, 1.0, 1)
    H.seg_cyl(wood, Vector((BOAT_L / 2 - 0.02, 0, -0.1)), Vector((BOAT_L / 2 + 0.03, 0, bow.z + 0.06)), 0.035, 6)
    iron = B.bm("M_LL_Iron", "SM_Boat")
    ring = Vector((BOAT_L / 2 - 0.08, 0, bow.z - 0.02))
    H.torus(iron, ring, 0.045, 0.009, 12, 5)
    B.empty("ROPE_bow", ring, (0.05, 0.05, 0.05), kind="SPHERE")
    # a small outboard on the transom: clamp, cowl, tiller, shaft, skeg and a three-bladed prop
    tz = _hull_point(st, 1.0, 1).z
    eng = B.bm("M_LL_Iron", "SM_Boat")
    H.box(eng, (st - 0.06, 0, tz - 0.05), (0.08, 0.16, 0.16), None)
    H.cyl(eng, (st - 0.2, 0, tz + 0.2), 0.14, 0.12, 0.34, 14)
    H.sphere(eng, (st - 0.2, 0, tz + 0.38), 0.12, 12, 6)
    H.seg_cyl(eng, Vector((st - 0.2, 0, tz + 0.25)), Vector((st + 0.35, 0.0, tz + 0.32)), 0.018, 6)
    H.seg_cyl(eng, Vector((st - 0.2, 0, tz + 0.05)), Vector((st - 0.2, 0, -0.55)), 0.03, 8)
    H.box(eng, (st - 0.2, 0, -0.55), (0.18, 0.05, 0.1), None)
    for j in range(3):
        a = 2 * math.pi * j / 3
        H.box(eng, (st - 0.28, 0.06 * math.cos(a), -0.5 + 0.06 * math.sin(a)), (0.02, 0.1, 0.05), None)
