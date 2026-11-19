extends Node3D
## Visual for a FleetShip: Blender model or a shaped stand-in hull, proper navigation lights (white
## masthead, red port, green starboard, white stern), warm deck lights, and motion that rides the sea the
## GPU draws (heave, pitch, roll) with banking into turns.
## Audit Stage E2 (DECISIONS Q21): the model is looked up by ship name first (ship_<name>.glb, e.g.
## ship_corrie_may), then by kind (ship_<kind>.glb). A model carries NAV_* / DECK_* empties at its real
## lantern fittings and the lights go there; DIMS (and the stand-in) remain the fallback for a missing file.

const DIMS := {"fishing": Vector3(4.2, 2.4, 13.0), "schooner": Vector3(5.0, 2.6, 19.0), "steamer": Vector3(7.5, 4.2, 30.0),
	"launch": Vector3(3.4, 1.9, 10.0)}
const WATERLINE := 0.4          # the model's design waterline above its origin (vessels.py WL)
## empty name -> colour, energy, range, deck light
const LAMPS := {"NAV_masthead": [Color(1.0, 0.95, 0.85), 1.6, 26.0, false],
	"NAV_port": [Color(1.0, 0.12, 0.08), 1.2, 9.0, false], "NAV_starboard": [Color(0.2, 1.0, 0.35), 1.2, 9.0, false],
	"NAV_stern": [Color(1.0, 0.95, 0.85), 0.8, 7.0, false], "DECK_work": [Color(1.0, 0.7, 0.4), 1.0, 14.0, true],
	"DECK_aft": [Color(1.0, 0.7, 0.4), 0.9, 12.0, true]}

var ship: FleetShip
var done := false
var model_path := ""            # the GLB in use ("" = stand-in)
var length := 13.0              # metres, from the model's bounds (or DIMS)
var beam := 4.2
var _sink := 0.0
var _fade := 0.0
var _prev_heading := 0.0
var _bank := 0.0
var _heave := 0.0
var _pitch := 0.0
var _roll := 0.0
var _settled := false
const SAMPLE_DT := 0.05         # s: the sea under the hull is sampled at 20 Hz (damping tau >= 1 s)
var _sample_acc := 0.0
var _tgt := Vector3.ZERO
var _wake_cache := Vector3(-1, -1, -1)   # storm, intensity, daylight last sent to the wake shader
var _lights: Array[OmniLight3D] = []
var _bulbs: Array[StandardMaterial3D] = []
# wake (audit E2): the stern's track as a ribbon in world space, displaced on the GPU like the sea
const WAKE_STEP := 0.25         # s between samples
const WAKE_LIFE := 16.0         # s a sample lasts
var _wake: MeshInstance3D
var _wake_mat: ShaderMaterial
var _wake_pts: Array = []       # [Vector2 world xz, float time]
var _wake_clock := 0.0
var _spray: GPUParticles3D
var _bow_y := 0.0
var _spray_ready := false


static func model_for(s: FleetShip) -> String:
	var by_name := "res://assets/models/ship_%s.glb" % s.name.to_lower().replace(" ", "_")
	if ResourceLoader.exists(by_name):
		return by_name
	var by_kind := "res://assets/models/ship_%s.glb" % s.kind
	return by_kind if ResourceLoader.exists(by_kind) else ""


func setup(s: FleetShip) -> void:
	_fog_fade.call_deferred(0.0, 0.5)         # Stage M (M4): invisible before her first drawn frame (she fades in)
	ship = s
	name = "Ship_%s" % s.name.replace(" ", "_")
	_prev_heading = s.heading
	var d: Vector3 = DIMS[s.kind]
	length = d.z
	beam = d.x
	model_path = model_for(s)
	var empties := {}
	if model_path != "":
		var m: Node3D = load(model_path).instantiate()
		add_child(m)
		_swap(m)
		var box := _bounds(m, Transform3D.IDENTITY)
		if box.size.z > 1.0:
			length = box.size.z
			beam = box.size.x
		for n in m.find_children("*", "Node3D", true, false):
			var base := String(n.name).get_slice(".", 0)
			if LAMPS.has(base) and not n is MeshInstance3D:
				empties[base] = _to_self(n).origin
	else:
		_stand_in(s.kind)
	_make_wake()
	_make_spray()
	if s.unlit:
		return      # the visitor's boat runs dark
	if empties.is_empty():
		empties = {"NAV_masthead": Vector3(0, d.y + d.z * 0.35, -d.z * 0.15),
			"NAV_port": Vector3(-d.x * 0.5, d.y * 1.15, -d.z * 0.1), "NAV_starboard": Vector3(d.x * 0.5, d.y * 1.15, -d.z * 0.1),
			"NAV_stern": Vector3(0, d.y * 1.1, d.z * 0.48), "DECK_work": Vector3(0, d.y * 1.5, d.z * 0.05)}
	for k in LAMPS:
		if empties.has(k):
			var l: Array = LAMPS[k]
			_nav(l[0], empties[k], l[1], l[2], l[3], model_path != "")


## The node's transform relative to this ship node (works before the ship is in the tree).
func _to_self(n: Node3D) -> Transform3D:
	var xf := n.transform
	var p := n.get_parent()
	while p != null and p != self:
		if p is Node3D:
			xf = (p as Node3D).transform * xf
		p = p.get_parent()
	return xf


func _bounds(root: Node, _xf: Transform3D) -> AABB:
	var box := AABB()
	var first := true
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var b: AABB = _to_self(mi) * (mi as MeshInstance3D).get_aabb()
		box = b if first else box.merge(b)
		first = false
	return box


func _swap(root: Node) -> void:
	for n in root.find_children("*", "MeshInstance3D", true, false):
		for i in n.mesh.get_surface_count():
			var m: Material = n.mesh.surface_get_material(i)
			if m:
				var rep := LLMaterials.get_mat(m.resource_name)
				if rep:
					n.set_surface_override_material(i, rep)


func _stand_in(kind: String) -> void:
	var d: Vector3 = DIMS[kind]
	var hull := MeshInstance3D.new()
	hull.mesh = _hull_mesh(d)
	hull.material_override = LLMaterials.get_mat("M_LL_SteelPaint" if kind == "steamer" else ("M_LL_Iron" if kind == "launch" else "M_LL_WoodDark"))
	add_child(hull)
	var house := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(d.x * 0.62, d.y * 0.9, d.z * (0.22 if kind != "steamer" else 0.18))
	house.mesh = bm
	house.position = Vector3(0, d.y + bm.size.y * 0.5, d.z * (0.18 if kind in ["fishing", "launch"] else 0.25))
	house.material_override = LLMaterials.get_mat("M_LL_Concrete" if kind == "steamer" else "M_LL_SteelPaint")
	add_child(house)
	var win := MeshInstance3D.new()
	var wb := BoxMesh.new()
	wb.size = Vector3(bm.size.x * 1.01, bm.size.y * 0.22, bm.size.z * 0.6)
	win.mesh = wb
	win.position = house.position + Vector3(0, bm.size.y * 0.18, -bm.size.z * 0.05)
	var wm := StandardMaterial3D.new()
	wm.albedo_color = Color(0.1, 0.08, 0.05)
	wm.emission_enabled = true
	wm.emission = Color(1.0, 0.7, 0.38)
	wm.emission_energy_multiplier = 0.0 if kind == "launch" else 1.6
	win.material_override = wm
	add_child(win)
	var masts := {"fishing": [-0.1], "schooner": [-0.25, 0.1], "steamer": [-0.3], "launch": [-0.2]}
	for z in masts[kind]:
		var m := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.08
		cm.bottom_radius = 0.14
		cm.height = d.z * (0.55 if kind == "schooner" else 0.4)
		m.mesh = cm
		m.position = Vector3(0, d.y + cm.height * 0.5, d.z * z)
		m.material_override = LLMaterials.get_mat("M_LL_WoodDark")
		add_child(m)
	if kind == "steamer":
		var fun := MeshInstance3D.new()
		var fm := CylinderMesh.new()
		fm.top_radius = 0.9
		fm.bottom_radius = 1.0
		fm.height = 4.5
		fun.mesh = fm
		fun.position = Vector3(0, d.y + 2.6, d.z * 0.02)
		fun.material_override = LLMaterials.get_mat("M_LL_Red")
		add_child(fun)
	if kind == "fishing":
		var g := MeshInstance3D.new()
		var gm := CylinderMesh.new()
		gm.top_radius = 0.05
		gm.bottom_radius = 0.05
		gm.height = d.z * 0.5
		g.mesh = gm
		g.rotation_degrees = Vector3(-55, 0, 0)
		g.position = Vector3(0, d.y + 2.5, d.z * 0.3)
		g.material_override = LLMaterials.get_mat("M_LL_Iron")
		add_child(g)


## Hull: tapered bow (-z), flat transom (+z), flared sides, sheer line rising to the bow.
func _hull_mesh(d: Vector3) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 10
	var sections: Array = []
	for i in n + 1:
		var u := float(i) / n                       # 0 = stern, 1 = bow
		var z := lerpf(d.z * 0.5, -d.z * 0.5, u)
		var half_w := d.x * 0.5 * (1.0 - pow(maxf(u - 0.55, 0.0) / 0.45, 1.6))
		var deck := d.y * (1.0 + 0.25 * u * u)
		var keel := -d.y * 0.55 * (1.0 - 0.6 * u)
		sections.append([Vector3(-half_w, deck, z), Vector3(-half_w * 0.75, keel * 0.4, z), Vector3(0, keel, z),
			Vector3(half_w * 0.75, keel * 0.4, z), Vector3(half_w, deck, z)])
	for i in n:
		var a: Array = sections[i]
		var b: Array = sections[i + 1]
		for j in 4:
			# audit M1 / E2: wound so the faces look outward (they were culled from outside)
			st.add_vertex(a[j]); st.add_vertex(b[j + 1]); st.add_vertex(b[j])
			st.add_vertex(a[j]); st.add_vertex(a[j + 1]); st.add_vertex(b[j + 1])
		st.add_vertex(a[0]); st.add_vertex(b[4]); st.add_vertex(a[4])       # deck
		st.add_vertex(a[0]); st.add_vertex(b[0]); st.add_vertex(b[4])
	var s0: Array = sections[0]
	for j in range(1, 4):                                                    # transom
		st.add_vertex(s0[0]); st.add_vertex(s0[j]); st.add_vertex(s0[j + 1])
	st.generate_normals()
	return st.commit()


func _nav(c: Color, p: Vector3, energy: float, rng_m: float, deck := false, on_model := false) -> void:
	var l := OmniLight3D.new()
	l.light_color = c
	l.light_energy = energy
	l.omni_range = rng_m
	l.position = p
	l.shadow_enabled = false
	l.light_volumetric_fog_energy = 0.6 if not deck else 0.2
	l.set_meta("e0", energy)                  # Stage M (M4): _fog_fade scales from these
	add_child(l)
	_lights.append(l)
	if on_model and deck:
		return      # the model's own lens shows the deck light; no blob over it
	var b := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = (0.22 if not deck else 0.3) if not on_model else 0.09     # on a model: the glow of the lens
	sm.height = sm.radius * 2.0
	sm.radial_segments = 8
	sm.rings = 4
	b.mesh = sm
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_color = c * 1.6
	m.disable_fog = true                      # Stage M (M4): _fog_fade dims it by the fog itself (lights read first)
	m.set_meta("c0", c * 1.6)
	b.material_override = m
	b.position = p
	b.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(b)
	_bulbs.append(m)


func wreck() -> void:
	_sink = 0.001


## The sea surface the GPU draws (shaders/ocean.gdshader): Gerstner waves displace horizontally as well as
## vertically, so the rest point q whose displaced position lands on p is found first (two fixed-point steps),
## then its height is taken (the same sum as OceanWaves.height_at). OceanWaves.height_at alone reads the
## height at the undisplaced point (up to 0.4 m off in a storm). Wave constants are computed once.
static var _wc := PackedFloat64Array()  # per wave, 5 values: dir.x, dir.y, k, k*c, steepness/k


static func _consts() -> PackedFloat64Array:
	if _wc.is_empty():
		for wv in OceanWaves.WAVES:
			var w: Vector4 = wv
			var k := TAU / w.w
			var d := Vector2(w.x, w.y).normalized()
			_wc.append_array(PackedFloat64Array([d.x, d.y, k, k * sqrt(9.8 / k), w.z / k]))
	return _wc


## OceanWaves.FADE flattened for surface_ys: [nearest fade start, then x, y per wave].
static var _fd := PackedFloat64Array()


static func _fades() -> PackedFloat64Array:
	if _fd.is_empty():
		var lo := INF
		for f in OceanWaves.FADE:
			lo = minf(lo, (f as Vector2).x)
		_fd.append(lo)
		for f in OceanWaves.FADE:
			_fd.append_array(PackedFloat64Array([(f as Vector2).x, (f as Vector2).y]))
	return _fd


static func surface_y(p: Vector2, t: float, storm: float) -> float:
	return surface_ys([p], t, storm)[0]


## Several points at once (one pass over the waves per step).
static func surface_ys(ps: Array, t: float, storm: float) -> PackedFloat32Array:
	var wc := _consts()
	var nw := wc.size() / 5
	var amp := OceanWaves.amp_mul(storm)
	var n := ps.size()
	var qs: Array = ps.duplicate()
	# Stage M (M1): wave i is scaled by OceanWaves.wave_gain(i, r) at the rest point's range, as ocean.gdshader does.
	# Inlined (the same 1 - smoothstep(FADE[i]) as wave_gain, read from _fades()): inside the first fade every
	# gain is 1 and nothing is evaluated; --sea=legacy (OceanWaves.legacy, read per call) has no fade.
	var fd := _fades()
	var fade_on := not OceanWaves.legacy
	for _i in 2:
		for j in n:
			var q: Vector2 = qs[j]
			var r := q.length()
			var near := not fade_on or r <= fd[0]
			var hx := 0.0
			var hz := 0.0
			for i in nw:
				var g := 1.0 if near else 1.0 - smoothstep(fd[1 + i * 2], fd[2 + i * 2], r)
				if g <= 0.0:
					continue
				var o := i * 5
				var c: float = cos(wc[o + 2] * (wc[o] * q.x + wc[o + 1] * q.y) - wc[o + 3] * t) * wc[o + 4] * amp * g
				hx += wc[o] * c
				hz += wc[o + 1] * c
			var calm := OceanWaves.calm(r)
			var p0: Vector2 = ps[j]
			qs[j] = Vector2(p0.x - hx * calm, p0.y - hz * calm)
	var out := PackedFloat32Array()
	out.resize(n)
	for j in n:
		var q: Vector2 = qs[j]
		var r := q.length()
		var near := not fade_on or r <= fd[0]
		var h := 0.0
		for i in nw:
			var g := 1.0 if near else 1.0 - smoothstep(fd[1 + i * 2], fd[2 + i * 2], r)
			if g <= 0.0:
				continue
			var o := i * 5
			h += wc[o + 4] * amp * g * sin(wc[o + 2] * (wc[o] * q.x + wc[o + 1] * q.y) - wc[o + 3] * t)
		out[j] = h * OceanWaves.calm(r)
	return out


## Heave, pitch and roll from the sea under the hull: four points at 80 % of the length and beam, then damped
## with a time constant that grows with size (a 10 m boat answers each sea; a 30 m coaster rides through it).
func motion_targets(t: float, storm: float) -> Vector3:
	var p := ship.pos
	var hl := length * 0.4
	var hb := beam * 0.4
	var fw := _dir(1.0, 0.0)
	var sd := Vector2(-fw.y, fw.x)                       # starboard (to_v3: x -> x, y -> z)
	var hh := surface_ys([p + fw * hl, p - fw * hl, p - sd * hb, p + sd * hb, p], t, storm)
	var hbow := hh[0]
	var hst := hh[1]
	var hp := hh[2]
	var hs := hh[3]
	var hc := hh[4]
	return Vector3((hbow + hst + hp + hs + 2.0 * hc) / 6.0, atan2(hbow - hst, 2.0 * hl), atan2(hp - hs, 2.0 * hb))


## A world-plane offset from the ship: `along` metres toward the bow, `side` metres to starboard.
func _dir(along: float, side: float) -> Vector2:
	var w := Geo.to_v3(ship.pos, 0.0)
	var b := Basis(Vector3.UP, Geo.yaw_for(ship.heading))
	var o := b * Vector3(side, 0.0, -along)
	return Vector2(w.x + o.x, w.z + o.z) - Vector2(w.x, w.z)


func _make_wake() -> void:
	_wake = MeshInstance3D.new()
	_wake.name = "Wake"
	_wake.top_level = true                       # world space: the ship moves, its track stays
	_wake.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_wake_mat = ShaderMaterial.new()
	_wake_mat.shader = load("res://shaders/wake.gdshader")
	_wake_mat.set_shader_parameter("waves", OceanWaves.shader_array())
	_wake_mat.set_shader_parameter("wave_fade", OceanWaves.shader_fade_array())   # Stage M (M1): as ocean.gdshader
	_wake.material_override = _wake_mat
	add_child(_wake)


## Bow spray: a small burst where the stem drives into a sea. Driven in tick() by how fast the bow drops.
func _make_spray() -> void:
	_spray = GPUParticles3D.new()
	_spray.name = "BowSpray"
	_spray.amount = 48
	_spray.lifetime = 1.3
	_spray.local_coords = false
	_spray.emitting = false
	_spray.amount_ratio = 0.0
	_spray.position = Vector3(0, WATERLINE + 0.6, -length * 0.46)
	_spray.visibility_aabb = AABB(Vector3(-8, -4, -8), Vector3(16, 12, 16))
	var pm := ParticleProcessMaterial.new()
	pm.direction = Vector3(0, 1.0, -0.35)
	pm.spread = 38.0
	var v := 2.2 + 0.12 * length
	pm.initial_velocity_min = v * 0.6
	pm.initial_velocity_max = v
	pm.gravity = Vector3(0, -9.8, 0)
	pm.scale_min = 0.6
	pm.scale_max = 1.4
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(beam * 0.3, 0.2, 0.3)
	var fade := Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 0.55))
	fade.set_color(1, Color(1, 1, 1, 0.0))
	var ft := GradientTexture1D.new()
	ft.gradient = fade
	pm.color_ramp = ft
	_spray.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(0.7, 0.7) * clampf(length / 13.0, 0.8, 1.6)
	var dot := Gradient.new()
	dot.set_color(0, Color(1, 1, 1, 1))
	dot.set_color(1, Color(1, 1, 1, 0))
	var dt2 := GradientTexture2D.new()
	dt2.gradient = dot
	dt2.fill = GradientTexture2D.FILL_RADIAL
	dt2.fill_from = Vector2(0.5, 0.5)
	dt2.fill_to = Vector2(0.5, 0.0)
	dt2.width = 32
	dt2.height = 32
	var sm := StandardMaterial3D.new()
	sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	sm.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	sm.vertex_color_use_as_albedo = true
	sm.albedo_color = Color(0.85, 0.88, 0.9)
	sm.albedo_texture = dt2
	sm.roughness = 1.0
	q.material = sm
	_spray.draw_pass_1 = q
	add_child(_spray)


func _wake_tick(t: float, dt: float, storm: float) -> void:
	_wake_clock += dt
	if _wake_clock >= WAKE_STEP:
		_wake_clock = 0.0
		if ship.speed > 0.2 and _sink <= 0.0:
			_wake_pts.push_front([ship.pos + _dir(-length * 0.47, 0.0), t])
		while _wake_pts.size() > 0 and t - float(_wake_pts[-1][1]) > WAKE_LIFE:
			_wake_pts.pop_back()
		_wake.mesh = _wake_mesh(t)
	_wake_mat.set_shader_parameter("time_s", t)
	var spd := clampf(ship.speed / maxf(ship.cruise, 0.5), 0.0, 1.0)
	var cur := Vector3(snappedf(storm, 0.01), snappedf((0.35 + 0.65 * spd) * (1.0 - _fade), 0.01), snappedf(_daylight(), 0.01))
	if cur != _wake_cache:
		_wake_cache = cur
		_wake_mat.set_shader_parameter("storm", storm)
		_wake_mat.set_shader_parameter("intensity", cur.y)
		_wake_mat.set_shader_parameter("glow", 0.05 + 0.5 * cur.z)


## The ribbon: one pair of vertices per sample, at rest (y = 0); it widens with age as the wake spreads.
func _wake_mesh(t: float) -> ArrayMesh:
	var n := _wake_pts.size()
	if n < 2:
		return null
	var verts := PackedVector3Array()
	var uvs := PackedVector2Array()
	var idx := PackedInt32Array()
	for i in n:
		var p: Vector2 = _wake_pts[i][0]
		var age := clampf((t - float(_wake_pts[i][1])) / WAKE_LIFE, 0.0, 1.0)
		var a: Vector2 = _wake_pts[maxi(i - 1, 0)][0]
		var b: Vector2 = _wake_pts[mini(i + 1, n - 1)][0]
		var dirv := (a - b)
		dirv = dirv.normalized() if dirv.length() > 0.001 else Vector2(0, 1)
		var side := Vector2(-dirv.y, dirv.x)
		var w := beam * (0.35 + 1.6 * sqrt(age))
		for k in 2:
			var q := p + side * w * (1.0 if k == 0 else -1.0)
			verts.append(Vector3(q.x, 0.0, q.y))
			uvs.append(Vector2(float(k), age))
		if i > 0:
			var j := (i - 1) * 2
			idx.append_array(PackedInt32Array([j, j + 1, j + 2, j + 1, j + 3, j + 2]))
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_TEX_UV] = uvs
	arr[Mesh.ARRAY_INDEX] = idx
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return m


## Daylight 0 (night) .. 1 (dawn), read from the exterior (outside.gd, the ship views' parent) when there is one.
func _daylight() -> float:
	var o := get_parent()
	if o != null:
		var d = o.get("dawn")
		if d != null:
			return clampf(float(d), 0.0, 1.0)
	return 0.0


func _spray_tick(dt: float, storm: float) -> void:
	var bow := _heave + sin(_pitch) * length * 0.46
	if not _spray_ready:                     # first frame: nothing to compare with yet
		_spray_ready = true
		_bow_y = bow
	var drop := maxf(0.0, (_bow_y - bow) / maxf(dt, 0.001))        # m/s the stem falls into the sea
	_bow_y = bow
	var spd := clampf(ship.speed / 2.5, 0.0, 1.0)
	var r := clampf(drop * 0.9 * (0.25 + storm) * (0.3 + 0.7 * spd), 0.0, 1.0)
	if _sink > 0.0 or _fade >= 1.0:
		r = 0.0
	_spray.amount_ratio = r
	_spray.emitting = r > 0.03


func tick(t: float, dt: float, storm: float, _k: KeeperSim) -> void:
	var p := ship.pos
	_sample_acc -= dt
	if not _settled or _sample_acc <= 0.0:
		_tgt = motion_targets(t, storm)
		_sample_acc += SAMPLE_DT if _settled else SAMPLE_DT * fposmod(float(ship.id) * 0.37, 1.0)   # ships out of step
	var tgt := _tgt
	var tau := 0.32 * sqrt(maxf(length, 4.0))           # 10 m: 1.0 s, 30 m: 1.75 s
	var a := 1.0 if not _settled else 1.0 - exp(-dt / tau)
	var ah := 1.0 if not _settled else 1.0 - exp(-dt / (tau * 0.7))
	_settled = true
	_heave = lerpf(_heave, tgt.x, ah)
	_pitch = lerpf(_pitch, tgt.y, a)
	_roll = lerpf(_roll, tgt.z, a)
	var turn_rate := Geo.angle_diff(_prev_heading, ship.heading) / maxf(dt, 0.001)
	_prev_heading = ship.heading
	var bank_max := 0.18 * clampf(15.0 / length, 0.4, 1.0)
	_bank = lerpf(_bank, clampf(-turn_rate * 1.8, -bank_max, bank_max), minf(1.0, dt * 1.5))
	if _sink > 0.0:
		_sink = minf(1.0, _sink + dt * 0.06)
	if ship.state == FleetShip.State.SAVED:
		_fade = minf(1.0, _fade + dt / 10.0)
	var yaw := Geo.yaw_for(ship.heading)
	var basis := Basis(Vector3.UP, yaw) * Basis(Vector3.RIGHT, _pitch - _sink * 0.35) \
		* Basis(Vector3.FORWARD, _roll + _bank + _sink * 0.6)
	transform = Transform3D(basis, Geo.to_v3(p, _heave - WATERLINE - _sink * 9.0))
	_wake_tick(t, dt, storm)
	_spray_tick(dt, storm)
	var lights_on := _sink < 0.35
	for l in _lights:
		l.visible = lights_on and _fade < 1.0
	visible = _sink < 1.0 and _fade < 1.0
	done = (_sink >= 1.0) or (_fade >= 1.0)
	_fog_fade(dt, storm)


# ------------------------------------------------------------------ Stage M (M4): vessels in fog
# Self-contained so it survives Stage E2's rewrite of this file: E2's tick() keeps one call to _fog_fade(dt,
# storm), and its lights and bulbs (from the model's NAV_* / DECK_* empties) keep the same _lights / _bulbs
# arrays with the "e0" / "c0" metas set where they are made.

const APPEAR_S := 3.0                     # a new vessel comes out of the murk over 3 s
const ATMOS := preload("res://scripts/fp/atmosphere.gd")
var _appear := 0.0
var _alpha_set := -1.0                    # the instance transparency last written (written on change only)


## 0 = not drawn, 1 = fully there: in over APPEAR_S after she is made, out over the SAVED fade (10 s). Eased,
## so no 60 fps frame changes her by more than about 1 % of her contrast (H5's limit is 15 %).
func fade_alpha() -> float:
	return smoothstep(0.0, 1.0, _appear) * (1.0 - smoothstep(0.0, 1.0, _fade))


func _fog_fade(dt: float, storm: float) -> void:
	_appear = minf(1.0, _appear + dt / APPEAR_S)
	var a := fade_alpha()
	var tr := 1.0 - a
	if absf(tr - _alpha_set) > 0.002 or (tr == 0.0 and _alpha_set != 0.0):
		_alpha_set = tr
		for n in find_children("*", "GeometryInstance3D", true, false):
			(n as GeometryInstance3D).transparency = tr      # any material, GLB or stand-in; 0 = opaque pass again
	for l in _lights:
		l.light_energy = float(l.get_meta("e0", l.light_energy)) * a
	# the bulbs skip the depth fog and are dimmed by its square root instead: a lamp keeps much more of its light
	# through the murk than a hull keeps of its contrast, so at range the lights read before the hull
	var cam := get_viewport().get_camera_3d() if is_inside_tree() else null
	var d := cam.global_position.distance_to(global_position) if cam else 230.0
	var o := get_parent()
	var dawn: float = o.dawn if o and "dawn" in o else 0.0
	var k := sqrt(ATMOS.transmittance(d, storm, dawn)) * a
	for m in _bulbs:
		var c0: Color = m.get_meta("c0", m.albedo_color)
		m.albedo_color = Color(c0.r * k, c0.g * k, c0.b * k, 1.0)
