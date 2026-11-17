"""THE LAST LIGHT, audit Stage S: the stairwell behind the watch room's stair door (ASSET_stairwell).

Built by build.py::build() into its own collection and exported as stairwell.glb, so the room keeps its
33-material cap. Two parts:

  inside the housing (SM_Well_*, always shown): limewashed masonry where the room's painted wall used to
    run on, a conduit, a chequer-plate landing on the hinge side, the hatch with a raised coaming, a guard
    rail from a newel along the door side, and a drop chain across the ladder head.
  the ship's ladder (SM_Ladder_*) and the service landing one flight down (SM_Lower_*), which Godot shows
    only while the door is open: curved masonry, fuel drums on a rack, a semi-rotary hand pump with its line
    rising to the day tank, the clockwork weight tube, the shut door of the dead main engine room, and the
    storm door the stair continues down behind.

Plan section 5 (docs/last_light/audit-2026-11/C_stairwell.md). Coordinates use build.py's dp(bearing, along,
z above the room floor, dist from the centre); H is the build module (helpers and constants).
"""
import math

from mathutils import Vector

LOWER_Z = -3.1           # service landing floor top, below the room floor
CEIL_Z = -0.2            # underside of the room's floor slab
LAND_EDGE = -0.25        # hatch edge on the landing (hinge) side, along the housing
LADDER_DEG = 75.0        # ship's ladder pitch
SECTOR = (130.0, 230.0)  # service landing bearings (partitions at both ends)
R_INNER = 1.3            # service landing's inner wall (engine room behind it)
R_OUT_LOW = 3.95         # tower wall's outer face at this height (spec tower: 3.99 at z 16.9)


def build_stairwell(H, B):
    b = H.R["stair"]
    r, o, u = H.wall_frame(b)
    bs = H.wb(b)
    front = H.back_dist(1.3, 0.0) - H.STAIR_DEPTH
    inner = H.HOUSING_HALF - 0.02                      # inner faces of the side plates
    dmid = (front + H.back_dist(1.3, 0.0)) / 2

    def wall_d(al):
        return math.sqrt(H.R_IN ** 2 - al ** 2)

    def P(al, z, d):
        return H.dp(b, al, z, d)

    def ring(bm, b0, b1, r0, r1, z0, z1, step=2.0):
        n = max(1, int(math.ceil((b1 - b0) / step)))
        for k in range(n):
            H.ring_seg(bm, b0 + (b1 - b0) * k / n, b0 + (b1 - b0) * (k + 1) / n, r0, r1, z0, z1)

    lime = B.bm("M_LL_Limewash", "SM_Well")
    iron = B.bm("M_LL_Iron", "SM_Well")
    paint = B.bm("M_LL_SteelPaint", "SM_Well")
    # ---------------------------------------------------------------- the housing
    # masonry lining: the span the room's wall left open below the housing's top plate, and down through the
    # slab to the service landing's ceiling (just inside the side plates, so no seam shows)
    half = math.degrees(math.asin((H.HOUSING_HALF - 0.005) / H.R_IN))
    ring(lime, b - half, b + half, H.R_IN, H.R_OUT, CEIL_Z, H.HOUSING_H, step=1.5)
    # conduit down the back wall from the pendant's junction box, with saddle clips
    cx = 0.42
    cd = wall_d(cx) - 0.022
    H.seg_cyl(iron, P(cx, 0.35, cd), P(cx, 2.2, cd), 0.011, 8)
    H.box(iron, P(cx, 2.2, cd - 0.005), (0.09, 0.05, 0.09), bs)                       # junction box
    H.seg_cyl(iron, P(cx - 0.045, 2.2, cd), P(0.03, 2.2, cd), 0.009, 8)               # run to the pendant
    for k in range(5):
        H.box(iron, P(cx, 0.55 + k * 0.38, cd + 0.008), (0.03, 0.03, 0.016), bs, bevel=0.0)
    H.box(iron, P(cx, 0.35, cd - 0.002), (0.06, 0.045, 0.07), bs)                     # switch box at the foot

    # chequer-plate landing over the hinge side, its top 6 mm proud of the room floor; solid to the slab's
    # underside so the cut floor's edge never shows
    chq = B.bm("M_LL_Chequer", "SM_Well")
    pts = [P(-inner, 0, front), P(LAND_EDGE, 0, front)]
    for k in range(7):
        al = LAND_EDGE + (-inner - LAND_EDGE) * k / 6
        pts.append(P(al, 0, wall_d(al) - 0.002))
    H.prism(chq, [(p.x, p.y) for p in pts], H.F + CEIL_Z - 0.06, H.F + 0.006)
    # threshold flat across the doorway, room side (the 20 mm gap under the leaf stays: 14 mm clear)
    H.box(paint, P(0.0, 0.003, front - 0.026), (1.12, 0.048, 0.006), bs, bevel=0.0)

    # the hatch coaming: 6 mm plate standing 50 mm proud, down past the slab, with a 70 mm flat on top that
    # carries the guard rail's stanchions (the rail runs 6 cm behind the door line, clear of the frame's jambs). Door side (behind the shut leaf, clear of it) and landing side.
    hc = front + 0.011
    H.box(paint, P((LAND_EDGE + inner) / 2, (CEIL_Z - 0.06 + 0.05) / 2, hc), (inner - LAND_EDGE, 0.006, 0.05 - CEIL_Z + 0.06), bs, bevel=0.0)
    H.box(paint, P((LAND_EDGE + inner) / 2, 0.053, hc + 0.032), (inner - LAND_EDGE, 0.07, 0.006), bs, bevel=0.0)
    wl = wall_d(LAND_EDGE)
    H.box(paint, P(LAND_EDGE - 0.003, (CEIL_Z - 0.06 + 0.05) / 2, (hc + wl) / 2), (0.006, wl - hc, 0.05 - CEIL_Z + 0.06), bs, bevel=0.0)
    # liner on the side plate's foot (the floor was cut to the plate's centre line)
    H.box(paint, P(inner + 0.003, (CEIL_Z - 0.06) / 2, (front + wall_d(inner)) / 2), (0.006, wall_d(inner) - front, -CEIL_Z + 0.06), bs, bevel=0.0)

    # newel on the landing corner, and the guard rail along the door side: oak top rail on steel stanchions
    # (R6: the old oak rail rose out of the uncut floor; nothing passes through any floor now)
    nd = front + 0.06
    na = LAND_EDGE - 0.035
    H.box(paint, P(na, 0.53, nd), (0.05, 0.05, 1.05), bs)                              # newel post
    H.box(paint, P(na, 1.065, nd), (0.07, 0.07, 0.02), bs)                             # its cap plate
    oak = B.bm("M_LL_Wood", "SM_Well")
    H.seg_cyl(oak, P(na, 1.0, nd), P(inner - 0.004, 1.0, nd), 0.022, 10)               # oak top rail
    H.seg_cyl(paint, P(na, 0.52, nd), P(inner - 0.004, 0.52, nd), 0.011, 8)            # mid rail
    for al in (0.17,):
        H.seg_cyl(paint, P(al, 0.056, nd), P(al, 0.98, nd), 0.014, 8)                   # stanchion on the flat
    H.cyl(paint, P(inner - 0.012, 1.0, nd), 0.04, 0.04, 0.016, 12, H.basis_z(r))        # wall flanges on the plate
    H.cyl(paint, P(inner - 0.012, 0.52, nd), 0.03, 0.03, 0.016, 12, H.basis_z(r))
    # drop chain across the ladder head: newel to an eye on the masonry, sagging 7 cm
    ce = wall_d(na) - 0.03
    H.seg_cyl(iron, P(na, 0.9, ce), P(na, 0.9, ce + 0.03), 0.006, 6)                  # wall eye's shank
    H.torus(iron, P(na, 0.9, ce - 0.012), 0.016, 0.004, 10, 4, H.basis_z(r))
    n_links = 21
    for k in range(n_links + 1):
        t = k / n_links
        d = nd + 0.03 + (ce - 0.03 - nd) * t
        z = 0.9 - 0.07 * 4 * t * (1 - t)
        lb = H.basis_z(r) if k % 2 == 0 else H.basis_z(u)     # link planes contain the chain line
        H.torus(iron, P(na, z, d), 0.016, 0.0035, 8, 4, lb)

    # ---------------------------------------------------------------- the ladder
    lad = B.bm("M_LL_SteelPaint", "SM_Ladder")
    run = 1.0 / math.tan(math.radians(LADDER_DEG))
    top_al = LAND_EDGE + 0.02

    def at(z, side):
        return P(top_al + (-z) * run, z, dmid + side * 0.22)

    for side in (-1, 1):                                                             # flat-bar stringers
        p0, p1 = at(0.04, side), at(LOWER_Z, side)
        dv = (p1 - p0)
        H.box(lad, (p0 + p1) / 2, (0.012, 0.075, dv.length), H.basis(o * side, dv.normalized().cross(o * side), dv.normalized()), bevel=0.0)
    n_t = 12
    for k in range(1, n_t + 1):
        z = LOWER_Z * k / (n_t + 0.4)
        c = (at(z, -1) + at(z, 1)) / 2
        H.box(lad, c, (0.12, 0.43, 0.014), bs, bevel=0.002)                          # tread
        H.box(B.bm("M_LL_Iron", "SM_Ladder"), c + r * 0.055 + u * 0.009, (0.012, 0.42, 0.006), bs, bevel=0.0)   # worn nosing bar
    # wall-side handrail, steel pipe, 0.85 m above the stringer line, its top bent down onto the landing
    hr = [P(top_al + (-z) * run, z + 0.85, dmid + 0.27) for z in (LOWER_Z + 0.3, 0.12)]
    H.seg_cyl(lad, hr[0], hr[1], 0.016, 8)
    top = hr[1]
    land = P(LAND_EDGE - 0.07, 0.006, dmid + 0.27)
    H.seg_cyl(lad, top, top + (land - top) * Vector((1, 1, 0)) * 1.0 + u * 0, 0.016, 8)
    H.seg_cyl(lad, Vector((land.x, land.y, top.z)), land, 0.016, 8)
    H.cyl(lad, land + u * 0.004, 0.035, 0.035, 0.008, 12)                             # foot plate

    # ---------------------------------------------------------------- the service landing
    s0, s1 = SECTOR
    lw = B.bm("M_LL_Limewash", "SM_Lower")
    ring(B.bm("M_LL_Flags", "SM_Lower"), s0, s1, R_INNER, H.R_IN + 0.02, LOWER_Z - 0.12, LOWER_Z)
    ring(lw, s0, s1, H.R_IN, R_OUT_LOW, LOWER_Z, CEIL_Z)                                 # outer (tower) wall
    ring(lw, s0, s1, R_INNER - 0.3, R_INNER, LOWER_Z, CEIL_Z)                            # inner wall
    # ceiling: limewashed underside of the slab, open over the housing's footprint (the hatch)
    for k in range(int((s1 - s0) / 2)):
        c0, c1 = s0 + 2 * k, s0 + 2 * (k + 1)
        h0, h1 = H.housing_span()
        if c1 <= h0 or c0 >= h1:
            H.ring_seg(lw, c0, c1, R_INNER - 0.3, H.R_IN + 0.02, CEIL_Z - 0.06, CEIL_Z)
        else:
            H.ring_seg(lw, c0, c1, R_INNER - 0.3, front - 0.01, CEIL_Z - 0.06, CEIL_Z)
    for pb in (s0, s1):                                                                  # partitions
        pr, po, pu = H.wall_frame(pb)
        H.box(lw, H.dp(pb, 0, (LOWER_Z + CEIL_Z) / 2, (R_INNER + H.R_IN) / 2), (0.24, H.R_IN - R_INNER + 0.3, CEIL_Z - LOWER_Z), H.wb(pb), bevel=0.0)

    st = B.bm("M_LL_SteelPaint", "SM_Lower")
    li = B.bm("M_LL_Iron", "SM_Lower")
    # the main engine room's door, shut for good: a steel door on the inner wall facing the ladder's foot
    eb = 186.0
    er, eo, eu = H.wall_frame(eb)
    ebs = H.wb(eb)
    ez = LOWER_Z
    H.box(st, H.dp(eb, 0, ez + 1.0, R_INNER + 0.025), (0.86, 0.05, 1.96), ebs)
    H.box(li, H.dp(eb, 0, ez + 1.0, R_INNER + 0.008), (0.98, 0.03, 2.08), ebs, bevel=0.0)   # frame
    for zz in (ez + 0.35, ez + 1.65):
        H.box(li, H.dp(eb, -0.38, zz, R_INNER + 0.055), (0.16, 0.012, 0.05), ebs)            # strap hinges
    H.box(li, H.dp(eb, 0.36, ez + 1.05, R_INNER + 0.06), (0.11, 0.014, 0.04), ebs)           # hasp
    H.torus(li, H.dp(eb, 0.40, ez + 0.98, R_INNER + 0.07), 0.018, 0.005, 10, 4, H.basis_z(er))   # padlock shackle
    H.box(B.bm("M_LL_Brass", "SM_Lower"), H.dp(eb, 0.40, ez + 0.94, R_INNER + 0.07), (0.04, 0.018, 0.045), ebs)   # padlock

    # the storm door the stair continues down behind, on the far partition
    sb = s1 - 0.5
    sr_, so_, su_ = H.wall_frame(sb)
    side = H.basis(so_, -sr_, su_)                                  # facing back into the landing
    sc = H.dp(sb, -0.13, LOWER_Z + 1.0, 2.25)
    H.box(st, sc, (0.86, 0.06, 1.96), side)
    H.box(li, sc + sr_ * 0.02, (0.98, 0.03, 2.08), side, bevel=0.0)
    for zz in (0.45, 1.55):
        H.box(li, sc + so_ * -0.4 + sr_ * -0.04 + su_ * (zz - 1.0), (0.05, 0.03, 0.08), side)   # dogs
    H.cyl(B.bm("M_LL_Brass", "SM_Lower"), sc + sr_ * -0.045 + so_ * 0.25, 0.08, 0.08, 0.02, 20, H.basis_z(sr_))   # its small wheel

    # fuel drums on a rack against the wall: two 45-gallon drums on their sides, with bungs and rolling hoops
    drum = B.bm("M_LL_Drum", "SM_Lower")
    drum_taps = []
    for db_ in (144.0, 164.5):           # chord-laid: their inner end corners need >= 19.2 deg
        dr, do_, du = H.wall_frame(db_)
        dc = H.dp(db_, 0, -3.1 + 0.12 + 0.29, H.R_IN - 0.36)
        H.cyl(drum, dc, 0.29, 0.29, 0.88, 24, H.basis_z(dr))
        for t in (-0.29, 0.29):
            H.torus(drum, dc + dr * t, 0.295, 0.012, 24, 6, H.basis_z(dr))
        H.cyl(li, dc + dr * 0.44 + du * 0.18, 0.025, 0.025, 0.02, 8, H.basis_z(dr))        # bung
        drum_taps.append((dc + dr * 0.45 + du * 0.18, dr))
        for t in (-0.3, 0.3):                                                             # cradle
            H.box(li, dc + dr * t + du * -0.33, (0.05, 0.5, 0.08), H.wb(db_), bevel=0.0)
        for s_ in (-1, 1):
            H.box(li, dc + do_ * (s_ * 0.2) + du * -0.39, (0.95, 0.04, 0.04), H.wb(db_), bevel=0.0)   # rack rails, on the floor

    # semi-rotary hand pump on the wall: body, lever, suction line down to the drums, delivery line rising
    # through the slab to the day tank above
    pb_ = 205.0
    pr, po, pu = H.wall_frame(pb_)
    pd = H.R_IN - 0.11
    pc = H.dp(pb_, 0, LOWER_Z + 1.0, pd)
    H.cyl(st, pc, 0.12, 0.12, 0.1, 20, H.basis_z(po))                                   # pump body
    H.cyl(li, pc - po * 0.06, 0.03, 0.03, 0.04, 10, H.basis_z(po))                      # spindle boss
    lever_end = pc - po * 0.08 + (pu * 0.5 + pr * 0.25)
    H.seg_cyl(li, pc - po * 0.08, lever_end, 0.012, 8)
    H.seg_cyl(B.bm("M_LL_Wood", "SM_Lower"), lever_end, lever_end + (pu * 0.5 + pr * 0.25).normalized() * 0.12, 0.018, 8)
    H.box(li, H.dp(pb_, 0, LOWER_Z + 1.0, H.R_IN - 0.03), (0.3, 0.06, 0.3), H.wb(pb_))  # wall plate
    pipe_d = H.R_IN - 0.06
    H.seg_cyl(li, pc + pu * 0.12, H.dp(pb_, 0, CEIL_Z + 0.01, pd), 0.018, 8)            # delivery to the day tank
    H.seg_cyl(li, pc - pu * 0.12, H.dp(pb_, 0, LOWER_Z + 0.2, pd), 0.018, 8)            # suction
    sweep = [H.dp(a_, 0, LOWER_Z + 0.2, pipe_d) for a_ in (205, 195, 185, 176)]
    for p0, p1 in zip(sweep, sweep[1:]):
        H.seg_cyl(li, p0, p1, 0.018, 8)
    H.seg_cyl(li, H.dp(pb_, 0, LOWER_Z + 0.2, pd), sweep[0], 0.018, 8)
    tap, tdr = drum_taps[-1]
    q = tap + tdr * 0.08                                                               # beyond the drum's end face
    H.seg_cyl(li, sweep[-1], Vector((q.x, q.y, sweep[-1].z)), 0.014, 8)                # hose along the floor
    H.seg_cyl(li, Vector((q.x, q.y, sweep[-1].z)), q, 0.014, 8)                        # up past the drum's end
    H.seg_cyl(li, q, tap, 0.014, 8)                                                    # into the near drum's bung

    # the clockwork's weight tube passing through, slab to floor, with flanges
    wt = H.dp(216.0, 0, 0, 1.75)
    H.cyl(li, Vector((wt.x, wt.y, H.F + (LOWER_Z + CEIL_Z) / 2)), 0.13, 0.13, CEIL_Z - LOWER_Z, 24)
    for zz in (LOWER_Z + 0.02, CEIL_Z - 0.02, (LOWER_Z + CEIL_Z) / 2):
        H.cyl(li, Vector((wt.x, wt.y, H.F + zz)), 0.17, 0.17, 0.03, 24)

    # bulkhead lamp on the outer wall over the ladder's foot (Godot: LIGHT_stair_low, red in a blackout)
    lb_ = 196.0
    lr, lo, lu = H.wall_frame(lb_)
    ld = H.R_IN - 0.02
    H.cyl(li, H.dp(lb_, 0, -1.0, ld), 0.09, 0.09, 0.03, 16, H.basis_z(lo))               # back plate
    bm = H.bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    H.sphere(bm, H.dp(lb_, 0, -1.0, ld - 0.06), 0.06, 12, 8)
    B.mesh_obj("LMP_stair_low", bm, "M_LL_Lamp")
    for k in range(4):                                                                 # cage bars
        a = math.pi * k / 4
        dv = lr * math.cos(a) + lu * math.sin(a)
        H.seg_cyl(li, H.dp(lb_, 0, -1.0, ld - 0.015) + dv * 0.075, H.dp(lb_, 0, -1.0, ld - 0.015) - dv * 0.075, 0.004, 4)
    B.empty("LIGHT_stair_low", H.dp(lb_, 0, -1.05, ld - 0.25), (0.05, 0.05, 0.05), kind="SPHERE")

    # colliders: the guard rail and the drop chain close the hatch (no invisible box). The landing stands on
    # the room's floor collider.
    B.collider("hatch_rail", P((na + inner) / 2, 0.55, nd), (inner - na + 0.05, 0.06, 1.1), bs)
    B.collider("hatch_chain", P(na, 0.55, (nd + ce) / 2), (0.06, ce - nd, 1.1), bs)
