extends RefCounted
## Audit Stage M (M1): the sea as one radial mesh, from a centre fan under the island out to a 6 km rim, so
## there is no square edge, no second surface and no far-plane gap to see (see
## docs/last_light/audit-2026-11/14_stageM_ocean_boundary_fog.md, section D.1).
##
## Cells are C0 (1.4 m) out to R1 (120 m), so the 5.3 m chop gets about lambda/3.8, then grow by K (2 cm per
## metre): 3.6 m at 230 m, 19 m at 1 km, 119 m at the rim. Each ring has a power-of-two segment count close
## to its circumference over the cell size. Where the count doubles or halves between two rings, a stitch
## strip joins them; vertices only sit on the rings, so there are no T-junctions and no cracks. The waves
## fade out with distance where the cells get too coarse for them (OceanWaves.FADE: each wave is gone before
## the Medium cell reaches a third of its length). Low and High scale the cell size (CELL_MUL).
## Loaded with preload (no class_name), so headless -s tests see it without an editor import.

const R0 := 12.0              # first ring: the centre fan inside it is under the island
const RIM := 6000.0           # the sea's edge, far beyond what the fog lets through (T(6 km) < 0.03 % at dawn)
const FAR := 6500.0           # camera far plane for the radial sea (the legacy square sea used 1200 / 2000 m)
const C0 := 1.4
const R1 := 120.0
const K := 0.02
const CELL_MUL := [1.4, 1.0, 0.8]     # Low, Medium, High


static func cell(r: float, mul := 1.0) -> float:
	return mul * (C0 if r < R1 else C0 + K * (r - R1))


## [radius, segments] per ring, from R0 to RIM. Segment counts change by at most a factor of two per ring.
static func rings(mul := 1.0) -> Array[Vector2]:
	var out: Array[Vector2] = []
	var r := R0
	var n := 0
	while r < RIM:
		var want := int(pow(2.0, roundf(log(maxf(8.0, TAU * r / cell(r, mul))) / log(2.0))))
		if n > 0:
			want = clampi(want, n / 2, n * 2)
		n = want
		out.append(Vector2(r, n))
		r += cell(r, mul)
	out.append(Vector2(RIM, n))
	return out


## Triangle count of build(mul) without building it.
static func triangle_count(mul := 1.0) -> int:
	var rs := rings(mul)
	var t := int(rs[0].y)                          # centre fan
	for j in rs.size() - 1:
		t += int(rs[j].y) + int(rs[j + 1].y)       # an even strip is 2n; a stitch strip n + 2n
	return t


## The mesh: one surface, flat at y 0 (the shader displaces it), normals up, tangents +X (the ocean shader's
## NORMAL_MAP needs them, as PlaneMesh provides). Godot's front faces are clockwise seen from the front; the
## vertex angle runs clockwise seen from above (north, then east), so (inner, outer, outer_next) and (inner,
## outer_next, inner_next) face up. regress_test R28 checks every triangle.
static func build(mul := 1.0) -> ArrayMesh:
	var rs := rings(mul)
	var verts := PackedVector3Array()
	var starts := PackedInt32Array()
	verts.append(Vector3.ZERO)
	for ring in rs:
		starts.append(verts.size())
		var n := int(ring.y)
		for i in n:
			var a := TAU * float(i) / float(n)
			verts.append(Vector3(sin(a) * ring.x, 0.0, -cos(a) * ring.x))
	var idx := PackedInt32Array()
	var n0 := int(rs[0].y)
	for i in n0:
		idx.append_array([0, starts[0] + i, starts[0] + (i + 1) % n0])
	for j in rs.size() - 1:
		_strip(idx, starts[j], int(rs[j].y), starts[j + 1], int(rs[j + 1].y))
	var normals := PackedVector3Array()
	normals.resize(verts.size())
	normals.fill(Vector3.UP)
	var tangents := PackedFloat32Array()
	tangents.resize(verts.size() * 4)
	for i in verts.size():
		tangents[i * 4] = 1.0
		tangents[i * 4 + 3] = 1.0
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = normals
	arr[Mesh.ARRAY_TANGENT] = tangents
	arr[Mesh.ARRAY_INDEX] = idx
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return m


## Joins an inner ring (na segments from index a) to the next ring out (nb from b): an even strip, or a
## stitch where nb is twice na (doubling outward) or half of it (halving outward).
static func _strip(idx: PackedInt32Array, a: int, na: int, b: int, nb: int) -> void:
	if nb == na:
		for i in na:
			var i1 := (i + 1) % na
			idx.append_array([a + i, b + i, b + i1, a + i, b + i1, a + i1])
	elif nb == na * 2:
		for i in na:
			var i1 := (i + 1) % na
			var o0 := b + 2 * i
			var o1 := b + 2 * i + 1
			var o2 := b + (2 * i + 2) % nb
			idx.append_array([a + i, o0, o1, a + i, o1, a + i1, a + i1, o1, o2])
	elif na == nb * 2:
		for j in nb:
			var j1 := (j + 1) % nb
			var i0 := a + 2 * j
			var i1 := a + 2 * j + 1
			var i2 := a + (2 * j + 2) % na
			idx.append_array([i0, b + j, i1, i1, b + j, b + j1, i1, b + j1, i2])
	else:
		push_error("SeaMesh: segment counts %d -> %d differ by more than a factor of two" % [na, nb])
