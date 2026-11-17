extends SceneTree
## Audit Stage E2: ship visuals (scripts/fp/ship_view2.gd) with the Blender vessel models.
##   godot --headless --path godot -s res://tests/ship_view_test.gd     -> SHIPVIEW_RESULT {json}
## Model by name then kind; lights at the model's NAV_* / DECK_* empties (none when unlit); the vessel
## materials kept; sizes within DIMS; the hull riding the displaced surface the GPU draws; motion scaled by
## size; the stand-in hull (fallback) wound outward.

var SHIP_VIEW: GDScript       # loaded at run time: LLMaterials names the GameState autoload
const CASES := [
	["Kittiwake", "fishing", false, "ship_fishing"], ["Corrie May", "fishing", false, "ship_corrie_may"],
	["Visitor", "launch", true, "ship_launch"], ["Gannet", "schooner", false, "ship_schooner"],
	["Lowestoft Star", "schooner", false, "ship_lowestoft_star"], ["Iona Star", "steamer", false, "ship_steamer"],
	["Hendrika", "steamer", false, "ship_hendrika"], ["Capture fishing", "fishing", false, "ship_fishing"]]

var _fails: Array[String] = []
var _count := 0
var _info := {}


func check(cond: bool, label: String) -> void:
	_count += 1
	if not cond:
		_fails.append(label)
		printerr("FAIL: ", label)


func _ship(n: String, kind: String, unlit: bool) -> FleetShip:
	var s := FleetShip.new()
	s.name = n
	s.kind = kind
	s.unlit = unlit
	s.pos = Vector2(0, -200)
	s.heading = 0.6
	return s


func _view(s: FleetShip) -> Node3D:
	var v: Node3D = SHIP_VIEW.new()
	root.add_child(v)
	v.setup(s)
	return v


func _initialize() -> void:
	process_frame.connect(_run, CONNECT_ONE_SHOT)


func _run() -> void:
	SHIP_VIEW = load("res://scripts/fp/ship_view2.gd")
	test_models_and_lights()
	test_surface_matches_gpu()
	test_motion_scales_with_size()
	test_stand_in_outward()
	test_wake_and_spray()
	test_tick_cost()
	print("SHIPVIEW_RESULT ", JSON.stringify({"tests": _count, "failed": _fails.size(), "failures": _fails, "info": _info}))
	quit(1 if _fails.size() > 0 else 0)


func test_models_and_lights() -> void:
	for c in CASES:
		var v := _view(_ship(c[0], c[1], c[2]))
		var tag: String = c[0]
		check(String(v.model_path).ends_with("/%s.glb" % c[3]), "%s loads %s (got %s)" % [tag, c[3], v.model_path])
		var meshes: Array = v.find_children("*", "MeshInstance3D", true, false)
		var vessel_meshes := 0
		for mi in meshes:
			var m: MeshInstance3D = mi
			if m.mesh == null or m.mesh is SphereMesh:
				continue
			vessel_meshes += 1
			var mat: Material = m.mesh.surface_get_material(0)
			check(mat != null and mat.resource_name.begins_with("M_Vessel_"), "%s material is the vessel's" % tag)
			check(m.get_surface_override_material(0) == null, "%s material not swapped" % tag)
		check(vessel_meshes == 1, "%s has one vessel mesh (%d)" % [tag, vessel_meshes])
		var lights: Array = v.find_children("*", "OmniLight3D", true, false)
		var d: Vector3 = SHIP_VIEW.DIMS[c[1]]
		if c[2]:
			check(lights.is_empty(), "%s runs dark (%d lights)" % [tag, lights.size()])
		else:
			var want := 6 if c[1] == "steamer" else 5
			check(lights.size() == want, "%s has %d lights (got %d)" % [tag, want, lights.size()])
			var by := {}
			for l in lights:
				by[(l as OmniLight3D).light_color.to_html(false)] = (l as OmniLight3D).position
			var port: Vector3 = by.get(Color(1.0, 0.12, 0.08).to_html(false), Vector3.ZERO)
			var stbd: Vector3 = by.get(Color(0.2, 1.0, 0.35).to_html(false), Vector3.ZERO)
			check(port.x < -0.3 and stbd.x > 0.3, "%s red to port, green to starboard (%s, %s)" % [tag, port, stbd])
			var empties := {}
			for n in v.find_children("*", "Node3D", true, false):
				if String(n.name).begins_with("NAV_") or String(n.name).begins_with("DECK_"):
					empties[String(n.name)] = v._to_self(n).origin
			check(empties.has("NAV_port") and port.distance_to(empties["NAV_port"]) < 0.01,
				"%s port light sits at its empty" % tag)
		if c[3] != "ship_lowestoft_star":
			check(v.length <= d.z + 0.01 and v.beam <= d.x + 0.01, "%s within DIMS %s (%.2f x %.2f)" % [tag, d, v.length, v.beam])
		_info[tag] = {"model": String(v.model_path).get_file(), "length": snappedf(v.length, 0.01),
			"beam": snappedf(v.beam, 0.01), "lights": lights.size()}
		v.queue_free()


## surface_y must land on the GPU's displaced surface: displace a rest point as the shader does, then ask
## surface_y for the height at the displaced x/z.
func test_surface_matches_gpu() -> void:
	var worst := 0.0
	var worst_naive := 0.0
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for i in 40:
		var q := Vector2(rng.randf_range(-400, 400), rng.randf_range(-400, 400))
		var t := rng.randf_range(0, 300)
		var storm := 1.0
		var amp := OceanWaves.amp_mul(storm)
		var hd := Vector2.ZERO
		for wv in OceanWaves.WAVES:
			var w: Vector4 = wv
			var k := TAU / w.w
			var dd := Vector2(w.x, w.y).normalized()
			hd += dd * (w.z * amp / k) * cos(k * (dd.dot(q) - sqrt(9.8 / k) * t))
		var calm := lerpf(0.35, 1.0, smoothstep(15.0, 45.0, q.length()))
		var p := q + hd * calm
		var h := OceanWaves.height_at(q, t, storm)
		worst = maxf(worst, absf(SHIP_VIEW.surface_y(p, t, storm) - h))
		worst_naive = maxf(worst_naive, absf(OceanWaves.height_at(p, t, storm) - h))
	_info["surface_err_m"] = snappedf(worst, 0.001)
	_info["naive_err_m"] = snappedf(worst_naive, 0.001)
	check(worst < 0.08, "surface_y within 8 cm of the GPU surface (worst %.3f m; height_at alone %.3f m)" % [worst, worst_naive])


func _motion_stats(n: String, kind: String) -> Dictionary:
	var v := _view(_ship(n, kind, false))
	var pitches: Array[float] = []
	var rolls: Array[float] = []
	var ok := true
	var t := 100.0
	for i in 1800:                       # 60 s at 30 fps, storm 1.0
		t += 1.0 / 30.0
		v.tick(t, 1.0 / 30.0, 1.0, null)
		var b: Basis = v.transform.basis
		ok = ok and b.is_finite() and absf(b.determinant() - 1.0) < 1e-3
		if i > 90:
			pitches.append(v._pitch)
			rolls.append(v._roll)
	v.queue_free()
	return {"pitch_sd": _sd(pitches), "roll_sd": _sd(rolls), "ok": ok}


func _sd(a: Array[float]) -> float:
	var m := 0.0
	for x in a:
		m += x
	m /= a.size()
	var s := 0.0
	for x in a:
		s += (x - m) * (x - m)
	return sqrt(s / a.size())


func test_motion_scales_with_size() -> void:
	var small := _motion_stats("Visitor", "launch")
	var big := _motion_stats("Iona Star", "steamer")
	_info["motion_deg"] = {"launch": [snappedf(rad_to_deg(small.pitch_sd), 0.01), snappedf(rad_to_deg(small.roll_sd), 0.01)],
		"steamer": [snappedf(rad_to_deg(big.pitch_sd), 0.01), snappedf(rad_to_deg(big.roll_sd), 0.01)]}
	check(small.ok and big.ok, "motion stays a proper rotation, no NaN")
	check(small.pitch_sd > big.pitch_sd * 1.3, "a 10 m boat pitches more than a 30 m coaster (%s)" % str(_info["motion_deg"]))
	check(small.roll_sd > big.roll_sd * 1.3, "a 10 m boat rolls more than a 30 m coaster")
	check(rad_to_deg(small.pitch_sd) > 0.5 and rad_to_deg(big.pitch_sd) < 6.0, "motion in a plausible range")


## Fallback (no GLB): the stand-in hull's generated normals point away from its centre line.
func test_stand_in_outward() -> void:
	var v: Node3D = SHIP_VIEW.new()
	var mesh: ArrayMesh = v._hull_mesh(Vector3(4.2, 2.4, 13.0))
	var arr := mesh.surface_get_arrays(0)
	var pos: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var nrm: PackedVector3Array = arr[Mesh.ARRAY_NORMAL]
	var out := 0
	var tot := 0
	for i in pos.size():
		var c := Vector3(0, 0.6, pos[i].z)            # a point on the hull's centre line
		var r := pos[i] - c
		if r.length() < 0.3:
			continue
		tot += 1
		out += 1 if nrm[i].dot(r) > 0.0 else 0
	_info["stand_in_outward"] = "%d/%d" % [out, tot]
	check(tot > 0 and out >= int(tot * 0.9), "stand-in hull wound outward (%d of %d normals out)" % [out, tot])
	v.free()


## The wake follows the stern at rest height (the shader lifts it onto the sea); spray only where the bow
## plunges, never on the spawn frame, never on a sinking ship.
func test_wake_and_spray() -> void:
	var s := _ship("Kittiwake", "fishing", false)
	s.speed = 3.0
	s.cruise = 3.0
	var v := _view(s)
	var t := 50.0
	v.tick(t, 1.0 / 30.0, 1.0, null)
	check(v._spray.amount_ratio == 0.0, "no spray on the spawn frame")
	var max_ratio := 0.0
	var any := false
	for i in 300:                                     # 10 s steaming north-west in a full storm
		t += 1.0 / 30.0
		s.pos += Vector2(sin(s.heading), -cos(s.heading)) * s.speed / 30.0
		v.tick(t, 1.0 / 30.0, 1.0, null)
		max_ratio = maxf(max_ratio, v._spray.amount_ratio)
		any = any or v._spray.emitting
	var m: ArrayMesh = v._wake.mesh
	check(m != null and m.get_surface_count() == 1, "the wake has a mesh after 10 s under way")
	if m != null:
		var verts: PackedVector3Array = m.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
		var flat := true
		for p in verts:
			flat = flat and absf(p.y) < 1e-4
		var newest := Vector2(verts[0].x + verts[1].x, verts[0].z + verts[1].z) * 0.5
		var stern: Vector2 = s.pos + v._dir(-v.length * 0.47, 0.0)
		_info["wake"] = {"samples": verts.size() / 2, "newest_to_stern_m": snappedf(newest.distance_to(stern), 0.01)}
		check(flat, "wake vertices at rest height (the shader displaces them)")
		check(verts.size() / 2 >= 30, "wake keeps about 10 s of track (%d samples)" % (verts.size() / 2))
		check(newest.distance_to(stern) < s.speed * 0.3, "the newest wake sample sits at the stern")
	check(v._wake.top_level, "the wake is in world space")
	_info["spray_max_ratio"] = snappedf(max_ratio, 0.01)
	check(any and max_ratio <= 1.0, "bow spray fires in a storm under way (max ratio %.2f)" % max_ratio)
	v.wreck()
	for i in 60:
		t += 1.0 / 30.0
		v.tick(t, 1.0 / 30.0, 1.0, null)
	check(not v._spray.emitting, "no spray from a sinking ship")
	v.queue_free()


## CPU cost of one ship's frame (motion on the displaced sea at 20 Hz, wake upkeep and rebuilds, spray drive),
## measured over 600 ticks under `taskpolicy -b` (efficiency cores, so pessimistic). Budget: four ships' mean
## under 0.4 ms a frame (2.4 % of 16.7 ms).
func test_tick_cost() -> void:
	var out := {}
	var worst := 0.0
	for c in [["Kittiwake", "fishing"], ["Iona Star", "steamer"]]:
		var s := _ship(c[0], c[1], false)
		s.speed = 3.0
		s.cruise = 3.0
		var v := _view(s)
		var t := 10.0
		var us: Array[float] = []
		var total := 0.0
		for i in 600:
			t += 1.0 / 60.0
			s.pos += Vector2(sin(s.heading), -cos(s.heading)) * s.speed / 60.0
			var t0 := Time.get_ticks_usec()
			v.tick(t, 1.0 / 60.0, 1.0, null)
			var d := float(Time.get_ticks_usec() - t0)
			us.append(d)
			total += d
		us.sort()
		out[c[0]] = {"mean_us": snappedf(total / 600.0, 0.1), "median_us": us[300], "p95_us": us[570]}
		worst = maxf(worst, total / 600.0)
		v.queue_free()
	_info["tick_cost"] = out
	check(worst * 4.0 < 400.0, "four ships' ticks under 0.4 ms a frame (mean %.0f us a ship)" % worst)
