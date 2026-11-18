extends Node3D
## Everything beyond the watch-room glass: environment, storm sky, ocean, island, reefs, the lighthouse
## exterior and its beam, rain, lightning, ships, and the dawn at the end. Driven by KeeperSim state.

const SHIP_VIEW := preload("res://scripts/fp/ship_view2.gd")
const SEA_MESH := preload("res://scripts/fp/sea_mesh.gd")
const ATMOS := preload("res://scripts/fp/atmosphere.gd")
## Stage M (M1): the bolt's foot. The far skirt (y -0.6) used to cover a foot at -1.5; with one sea, the foot
## must be under the deepest trough at strike range (400 m, full storm: -1.84 m with the faded wave set). The
## strip's width reaches about 0.5 m lower, and g5_weather_audio_test wants the bolt's lowest vertex above -3.
const BOLT_FOOT_Y := -2.2
const LANTERN_Y := 24.8
## Render layer 2 = the watch-room interior (station.gd LAYER_INTERIOR). Exterior lights skip it:
## the room is lit only by its own lamps and by what comes in through the windows.
const EXTERIOR_ONLY := 0xFFFFF & ~2 & ~8192   # not the room (2), not the stairwell's lower level (station.LAYER_LOWER)

var sim: KeeperSim
var env: Environment
var sky_mat: ShaderMaterial
var ocean_mat: ShaderMaterial
var sea: MeshInstance3D                  # Stage M: the ocean surface (radial, or the legacy square)
var sea_legacy := false                  # Stage M: --sea=legacy (the old square sea, fog and sky, for A/B)
var beam_mat: ShaderMaterial
var moon: DirectionalLight3D
var bolt_light: DirectionalLight3D
var beam_pivot: Node3D
var beam_light: SpotLight3D
var beam_cone: MeshInstance3D
var lamp_glow: OmniLight3D
var door_lamp: OmniLight3D               # G6d: the bulkhead lamp over the base door
var island_glb := false                  # G6d: island.glb (Blender exterior.py) brings its own landing + walkway
var title_boat: Node3D                   # G6d: the keeper's boat, title screen only (setup_title)
var _coast := PackedFloat32Array()       # G6d: island.glb's coast radius per degree of bearing (shore foam)
var _boat_bow := Vector3.ZERO            # the bow ring, boat-local
var _rope: Array[MeshInstance3D] = []
const BOAT_GLB := "res://assets/models/boat.glb"
## G6d stage D: the title's storm (setup_title only; the story's rain, beam and lightning are untouched).
## Counts per quality preset (Low, Medium, High).
const TITLE_NEAR_RAIN := [700, 1400, 2400]     # the camera-near streak layer
const TITLE_SPLASHES := [0, 220, 420]          # drops bursting on the pier and walkway decks
const TITLE_SPRAY := [3, 6, 10]                # spray emitters fired where the swell meets the ledges
const TITLE_SPRAY_N := 64                      # particles per spray burst (many faint ones read as mist)
## The menu column's right edge in screen width (16:9; main_fp's column ends near 0.5): the beam's cone
## fades out over this span and its fog scatter drops while it points into the column.
const TITLE_BEAM_MASK := Vector2(0.50, 0.66)
## R2: the shaft keeps 45 % over the column (it used to stop dead at a vertical line left of the lantern),
## and the mask follows the column's real right edge (set_title_column), not a fixed 16:9 guess.
const TITLE_BEAM_FLOOR := 0.45
var title_mask := TITLE_BEAM_MASK
var title_fx: Node3D                           # every title-only effect lives under this node
var near_rain: GPUParticles3D
var splashes: GPUParticles3D
var spray: Array[GPUParticles3D] = []
var spray_fired := 0                           # tests and QA
var _streak_mats: Array[ShaderMaterial] = []
var _spray_mat: StandardMaterial3D
var _spray_pts: Array = []                     # [world pos, outward Vector3, last height, cooldown until]
var _spray_next := 0
var _spray_gap := 0.0
var _flash_light := 1.0                        # the current flash's light gain (title events set it per kind)
var optic: Node3D
var rain: GPUParticles3D
var ship_views := {}
var dawn := 0.0
var dusk := 0.0          # story: lighting-up time at 16:20 fades to night
var _sky_mode := "night"
var attract := false     # title shot from the sea: thinner fog so the night and the beam read


func set_sky(kind: String) -> void:
	_sky_mode = kind
	match kind:
		"dusk":
			dusk = 1.0
		"dawn":
			dusk = 0.0
		_:
			dusk = 0.0
var flash := 0.0
var flash_now := 0.0      # the flicker-shaped flash actually shown this frame (station window lights read it)
var _t := 0.0
var _flash_dir := Vector2(0, -1)
var _noise_tex: NoiseTexture2D
## G5 / finding 29: distant bolts. Only some strikes show one; the rest stay in-cloud (flash only).
const BOLT_FLICKER_S := 2.0 * PI / 47.0     # the flash flicker period (sin(_t * 47) below): restrikes land on it
var bolt: MeshInstance3D
var bolt_mat: ShaderMaterial
var bolts_shown := 0                         # counters for tests and QA
var bolts_skipped := 0
var _bolt_age := -1.0
var _bolt_life := 0.0
var _bolt_power := 0.0
var _bolt_strokes: Array = []
var _bolt_rng := RandomNumberGenerator.new()


func setup(k: KeeperSim) -> void:
	sim = k
	_noise_tex = _noise(256, 0.02, false)
	_environment()
	_island()                            # G6d: before the ocean, whose shore foam follows its coastline
	_ocean()
	_reefs()
	if not island_glb:
		_jetty()                         # the old procedural stand-in, only without island.glb
	_lighthouse()
	_beam()
	_rain()
	_bolt_setup()


# ------------------------------------------------------------------ build

func _bolt_setup() -> void:
	_bolt_rng.seed = 29
	bolt_mat = ShaderMaterial.new()
	bolt_mat.shader = load("res://shaders/bolt.gdshader")
	bolt = MeshInstance3D.new()
	bolt.name = "LightningBolt"
	bolt.material_override = bolt_mat
	bolt.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	bolt.visible = false
	add_child(bolt)


## A strike event: maybe show a bolt 400-900 m out along the strike bearing, from the cloud base down
## to the sea. With reduce-flashing on, no bolt is drawn at all.
func _strike_bolt(e: Dictionary) -> void:
	if e.has("bolt"):                          # G6d title events decide for themselves (no draw from _bolt_rng)
		if Settings.v["reduce_flashing"] or not e["bolt"]:
			bolts_skipped += 1
			return
	else:
		var chance := 0.35 + 0.3 * (sim.storm if sim else 0.5)
		if Settings.v["reduce_flashing"] or _bolt_rng.randf() > chance:
			bolts_skipped += 1
			return
	var d: float = e.get("distance", 650.0)
	var dir2 := Geo.dir(e.get("bearing", 0.0))
	var out := Vector3(dir2.x, 0.0, dir2.y)
	var side := Vector3(-out.z, 0.0, out.x)
	var cam_node := get_viewport().get_camera_3d() if is_inside_tree() else null
	var cam := cam_node.global_position if cam_node else Vector3(0, 21.0, 0)
	var foot := out * d + Vector3(0, BOLT_FOOT_Y, 0)   # ends under the sea surface (depth-tested: the water hides it)
	var top := out * d + side * _bolt_rng.randf_range(-60.0, 60.0) + Vector3(0, _bolt_rng.randf_range(260.0, 360.0), 0)
	var w := d * 0.007                                  # about 3-6 px wide on Medium's render scale
	var st := {"v": PackedVector3Array(), "uv": PackedVector2Array(), "c": PackedColorArray(), "i": PackedInt32Array()}
	var main := _bolt_path(top, foot, side, out, 6, 0.22)
	_bolt_strip(st, main, cam, w, 0.5, 1.0)
	for _b in _bolt_rng.randi_range(2, 4):
		var k := _bolt_rng.randi_range(int(main.size() * 0.1), int(main.size() * 0.65))
		var s: Vector3 = main[k]
		var drop := (s.y + 1.5) * _bolt_rng.randf_range(0.2, 0.4)
		var lat := drop * _bolt_rng.randf_range(0.3, 0.8) * (1.0 if _bolt_rng.randf() < 0.5 else -1.0)
		_bolt_strip(st, _bolt_path(s, s + Vector3(0, -drop, 0) + side * lat, side, out, 4, 0.3), cam, w * 0.5, 0.2, 0.45)
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = st["v"]
	arr[Mesh.ARRAY_TEX_UV] = st["uv"]
	arr[Mesh.ARRAY_COLOR] = st["c"]
	arr[Mesh.ARRAY_INDEX] = st["i"]
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	bolt.mesh = m
	# visible 0.15-0.35 s; the first stroke plus 1-2 restrikes on the flicker peaks
	_bolt_life = _bolt_rng.randf_range(0.15, 0.35)
	_bolt_strokes = [0.0]
	var n := 1
	while n * BOLT_FLICKER_S < _bolt_life and n <= 2:
		_bolt_strokes.append(n * BOLT_FLICKER_S)
		n += 1
	_bolt_power = e.get("power", 0.7)
	_bolt_age = 0.0
	bolt.visible = true
	bolts_shown += 1


## Midpoint displacement from a to b: jagged sideways (and a little in depth) at every scale.
func _bolt_path(a: Vector3, b: Vector3, side: Vector3, out: Vector3, depth: int, rough: float) -> PackedVector3Array:
	var pts := PackedVector3Array([a, b])
	for _level in depth:
		var nxt := PackedVector3Array()
		for i in pts.size() - 1:
			var p := pts[i]
			var q := pts[i + 1]
			var L := (q - p).length()
			nxt.append(p)
			nxt.append((p + q) * 0.5 + side * _bolt_rng.randf_range(-1.0, 1.0) * L * rough
				+ out * _bolt_rng.randf_range(-1.0, 1.0) * L * rough * 0.5)
		nxt.append(pts[pts.size() - 1])
		pts = nxt
	return pts


## A camera-facing quad strip along pts, tapering from width w to w * taper.
func _bolt_strip(st: Dictionary, pts: PackedVector3Array, cam: Vector3, w: float, taper: float, alpha: float) -> void:
	var n := pts.size()
	var base: int = st["v"].size()
	for i in n:
		var tg := (pts[mini(i + 1, n - 1)] - pts[maxi(i - 1, 0)]).normalized()
		var off := tg.cross((pts[i] - cam).normalized()).normalized() * w * 0.5 * lerpf(1.0, taper, float(i) / float(n - 1))
		st["v"].append(pts[i] - off)
		st["v"].append(pts[i] + off)
		st["uv"].append(Vector2(0, 0))
		st["uv"].append(Vector2(1, 0))
		st["c"].append(Color(1, 1, 1, alpha))
		st["c"].append(Color(1, 1, 1, alpha))
	for i in n - 1:
		var a := base + i * 2
		st["i"].append_array(PackedInt32Array([a, a + 1, a + 2, a + 1, a + 3, a + 2]))


func _bolt_step(delta: float) -> void:
	if _bolt_age < 0.0:
		return
	_bolt_age += delta
	var e := 0.0
	for s in _bolt_strokes:
		if _bolt_age >= s:
			e = maxf(e, exp(-(_bolt_age - s) / 0.05))
	e = maxf(e, 0.2) if _bolt_age < _bolt_life else 0.2 * maxf(0.0, 1.0 - (_bolt_age - _bolt_life) / 0.08)
	bolt_mat.set_shader_parameter("intensity", e * (0.55 + 0.45 * sin(_t * 47.0)) * _bolt_power)
	if _bolt_age > _bolt_life + 0.08:
		_bolt_age = -1.0
		bolt.visible = false

func _noise(size: int, freq: float, normal: bool, seamless := true) -> NoiseTexture2D:
	var n := FastNoiseLite.new()
	n.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n.frequency = freq
	n.fractal_octaves = 4
	var t := NoiseTexture2D.new()
	t.width = size
	t.height = size
	t.seamless = seamless
	t.noise = n
	t.as_normal_map = normal
	t.bump_strength = 6.0
	t.generate_mipmaps = true
	return t


func _environment() -> void:
	var we := WorldEnvironment.new()
	env = Environment.new()
	sky_mat = ShaderMaterial.new()
	sky_mat.shader = load("res://shaders/sky.gdshader")
	sky_mat.set_shader_parameter("clouds", _noise(512, 0.012, false))
	var sky := Sky.new()
	sky.sky_material = sky_mat
	sky.radiance_size = Sky.RADIANCE_SIZE_64
	env.sky = sky
	env.background_mode = Environment.BG_SKY
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.9
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = 1.35
	env.glow_enabled = true
	env.glow_intensity = 0.45
	env.glow_bloom = 0.04
	env.glow_hdr_threshold = 1.4
	env.ssao_enabled = true
	env.ssao_radius = 0.9
	env.ssao_intensity = 1.6
	env.fog_enabled = true
	env.fog_light_color = Color(0.05, 0.065, 0.085)
	env.fog_density = 0.0035
	env.fog_sky_affect = 0.6
	env.fog_height = 30.0
	env.fog_height_density = 0.02
	env.volumetric_fog_enabled = true
	env.volumetric_fog_density = 0.008
	env.volumetric_fog_albedo = Color(0.7, 0.75, 0.82)
	env.volumetric_fog_emission = Color(0.006, 0.008, 0.012)
	env.volumetric_fog_length = 180.0
	env.volumetric_fog_detail_spread = 2.0
	env.volumetric_fog_sky_affect = 0.4
	sea_legacy = String(GameState.user_args.get("sea", "")) == "legacy"
	if not sea_legacy:
		# Stage M (M2): no flat height-fog veil (it put 45 % on every sea pixel, near or far); the depth fog and
		# the sky's bank share one colour (atmosphere.gd), so aerial perspective (the radiance map) is not used
		env.fog_height_density = 0.0
		env.fog_aerial_perspective = 0.0
		# the volumetric fog lays its last froxel slice (180 m of it) over every pixel beyond, sea and sky alike,
		# but only sky_affect of it over the sky: at 0.4 the far sea came out 7 to 14 / 255 darker than the sky
		# at the rim on Medium (Low, without volumetrics, matched to 1 / 255). 1.0 treats both the same.
		env.volumetric_fog_sky_affect = float(GameState.user_args.get("volsky", "1.0"))   # --volsky: A/B for Daniel
		sky_mat.set_shader_parameter("bank", 1.0)
	else:
		sky_mat.set_shader_parameter("bank", 0.0)
	env.adjustment_enabled = true
	env.adjustment_saturation = 0.88
	# perf bisect flags: --novolfog --nossao --nossil --halfao --norain --noglow --noshadows
	var a: Dictionary = GameState.user_args
	env.volumetric_fog_enabled = not a.has("novolfog") and Settings.q_volumetric()
	env.ssao_enabled = not a.has("nossao") and Settings.q_ssao()
	env.ssil_enabled = not a.has("nossil") and Settings.q_ssil()
	env.ssil_radius = 2.0                      # the room is 6.5 m across: short-range bounce only
	env.ssil_intensity = 1.0
	var half: bool = Settings.q_half_size() or a.has("halfao")   # --halfao: perf bisect
	RenderingServer.environment_set_ssao_quality(RenderingServer.ENV_SSAO_QUALITY_LOW if half else RenderingServer.ENV_SSAO_QUALITY_MEDIUM, half, 0.5, 2, 50.0, 300.0)
	RenderingServer.environment_set_ssil_quality(RenderingServer.ENV_SSIL_QUALITY_LOW if half else RenderingServer.ENV_SSIL_QUALITY_MEDIUM, half, 0.5, 4, 50.0, 300.0)
	env.glow_enabled = not a.has("noglow")
	we.environment = env
	add_child(we)
	moon = DirectionalLight3D.new()
	moon.light_color = Color(0.55, 0.64, 0.82)
	moon.light_energy = 0.45
	moon.rotation_degrees = Vector3(-34, 160, 0)
	moon.shadow_enabled = not GameState.user_args.has("nomoonshadow")   # --nomoonshadow: perf bisect
	moon.directional_shadow_max_distance = 140.0
	moon.light_volumetric_fog_energy = 0.3
	moon.light_cull_mask = EXTERIOR_ONLY
	add_child(moon)
	bolt_light = DirectionalLight3D.new()
	bolt_light.light_color = Color(0.78, 0.84, 1.0)
	bolt_light.light_energy = 0.0
	bolt_light.rotation_degrees = Vector3(-50, 0, 0)
	bolt_light.light_volumetric_fog_energy = 1.2
	bolt_light.light_cull_mask = EXTERIOR_ONLY   # lightning reaches the room through the windows (station.gd)
	add_child(bolt_light)


func _ocean() -> void:
	# Stage M (M1): one radial sea out to a 6 km rim (sea_mesh.gd), the waves fading with distance
	# (OceanWaves.FADE), no skirt. --sea=legacy keeps the 1100 m square, the skirt and no fade, for A/B.
	var legacy := String(GameState.user_args.get("sea", "")) == "legacy"
	OceanWaves.legacy = legacy
	var mi := MeshInstance3D.new()
	sea = mi
	if legacy:
		var pm := PlaneMesh.new()
		pm.size = Vector2(1100, 1100)
		pm.subdivide_width = 330
		pm.subdivide_depth = 330
		mi.mesh = pm
	else:
		var t0 := Time.get_ticks_usec()
		mi.mesh = SEA_MESH.build(SEA_MESH.CELL_MUL[clampi(int(Settings.v["quality"]), 0, 2)])
		var rim: float = SEA_MESH.RIM
		mi.custom_aabb = AABB(Vector3(-rim, -8.0, -rim), Vector3(2.0 * rim, 16.0, 2.0 * rim))   # displaced in the shader
		print("SEA radial: %d triangles, built in %.0f ms" % [(mi.mesh as ArrayMesh).surface_get_array_index_len(0) / 3,
			(Time.get_ticks_usec() - t0) / 1000.0])
	ocean_mat = ShaderMaterial.new()
	ocean_mat.shader = load("res://shaders/ocean.gdshader")
	ocean_mat.set_shader_parameter("waves", OceanWaves.shader_array())
	ocean_mat.set_shader_parameter("wave_fade", OceanWaves.shader_fade_array())
	ocean_mat.set_shader_parameter("detail_a", _noise(512, 0.03, true))
	ocean_mat.set_shader_parameter("detail_b", _noise(512, 0.06, true))
	ocean_mat.set_shader_parameter("foam_noise", _noise(256, 0.05, false))
	ocean_mat.set_shader_parameter("shore_field", _shore_field())
	mi.material_override = ocean_mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.visible = not GameState.user_args.has("noocean")
	add_child(mi)
	if not legacy:
		return
	# far skirt so the horizon never shows the edge (legacy sea only)
	var far := MeshInstance3D.new()
	var fm := PlaneMesh.new()
	fm.size = Vector2(6000, 6000)
	far.mesh = fm
	far.position.y = -0.6
	var fmat := StandardMaterial3D.new()
	fmat.albedo_color = Color(0.012, 0.03, 0.045)
	fmat.roughness = 0.2
	far.material_override = fmat
	add_child(far)


## Foam proximity field: 1 at rocks/shore, fading out over ~10 m. 256 px over 520 m.
func _shore_field() -> ImageTexture:
	var N := 256
	var img := Image.create(N, N, false, Image.FORMAT_R8)
	var rect := Vector4(-260, -260, 520, 520)
	var circles: Array = []
	for r in sim.layout.reefs:
		circles.append([r["pos"], r["r"]])
	if _coast.is_empty():
		circles.append([Vector2.ZERO, sim.layout.island_radius + 2.0])
	for y in N:
		for x in N:
			var p := Vector2(rect.x + (x + 0.5) / N * rect.z, rect.y + (y + 0.5) / N * rect.w)
			var best := 99.0
			for c in circles:
				best = minf(best, p.distance_to(c[0]) - c[1])
			if not _coast.is_empty():                # the real coastline (island.glb), not a circle
				var bi := int(fposmod(rad_to_deg(atan2(p.x, -p.y)), 360.0)) % 360
				best = minf(best, p.length() - _coast[bi])
			img.set_pixel(x, y, Color(clampf(1.0 - best / 11.0, 0.0, 1.0), 0, 0))
	return ImageTexture.create_from_image(img)


func _island() -> void:
	var model := "res://assets/models/island.glb"
	if ResourceLoader.exists(model):
		var isl: Node3D = load(model).instantiate()
		add_child(isl)
		_apply_mats(isl)
		island_glb = isl.find_child("SM_Landing*", true, false) != null
		_coast_from(isl.find_child("SM_Island_Terrain", true, false) as MeshInstance3D)
		isl.visible = not GameState.user_args.has("noisland")   # --noisland: perf bisect (the coast still loads)
		return
	# procedural stand-in: rugged dome with cliffs, rises to the tower plinth (3.5 m)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var noise := FastNoiseLite.new()
	noise.frequency = 0.08
	noise.fractal_octaves = 4
	var R := sim.layout.island_radius + 6.0
	var n := 90
	var step := 2.0 * R / n
	var hgt := func(x: float, z: float) -> float:
		var r := Vector2(x, z).length() + noise.get_noise_2d(x, z) * 4.0
		var top := 3.4 + noise.get_noise_2d(x * 2.0, z * 2.0) * 0.6
		var cliff := smoothstep(R - 1.0, R - 9.0, r)
		var h := lerpf(-3.0, top, cliff)
		if Vector2(x, z).length() < 6.5:
			h = maxf(h, 3.5)
		return h + noise.get_noise_2d(x * 4.0, z * 4.0) * 0.4 * cliff
	for iz in n:
		for ix in n:
			var x0 := -R + ix * step
			var z0 := -R + iz * step
			var q := [Vector3(x0, hgt.call(x0, z0), z0), Vector3(x0 + step, hgt.call(x0 + step, z0), z0),
				Vector3(x0 + step, hgt.call(x0 + step, z0 + step), z0 + step), Vector3(x0, hgt.call(x0, z0 + step), z0 + step)]
			if q[0].y < -2.9 and q[1].y < -2.9 and q[2].y < -2.9 and q[3].y < -2.9:
				continue
			for idx in [0, 1, 2, 0, 2, 3]:
				st.add_vertex(q[idx])
	st.index()
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = _terrain_mat()
	add_child(mi)


var _terrain_m: ShaderMaterial


func _terrain_mat() -> ShaderMaterial:
	if _terrain_m == null:
		_terrain_m = ShaderMaterial.new()
		_terrain_m.shader = load("res://shaders/terrain.gdshader")
		_terrain_m.set_shader_parameter("rock_a", load("res://assets/textures/cliff_side_diff.png"))
		_terrain_m.set_shader_parameter("rock_n", load("res://assets/textures/cliff_side_nor_gl.png"))
		_terrain_m.set_shader_parameter("grass_a", load("res://assets/textures/sparse_grass_diff.png"))
		_terrain_m.set_shader_parameter("shore_a", load("res://assets/textures/coast_land_rocks_01_diff.png"))
	return _terrain_m


## The coast radius on each degree of bearing: the farthest island vertex near the waterline.
func _coast_from(mi: MeshInstance3D) -> void:
	if mi == null or mi.mesh == null:
		return
	_coast.resize(360)
	_coast.fill(0.0)
	var verts: PackedVector3Array = mi.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	for v0 in verts:
		var v: Vector3 = mi.transform * v0
		if v.y > -0.5 and v.y < 0.5:
			var bi := int(fposmod(rad_to_deg(atan2(v.x, -v.z)), 360.0)) % 360
			_coast[bi] = maxf(_coast[bi], Vector2(v.x, v.z).length())
	for k in 360:                                  # fill any empty degree from its neighbours
		if _coast[k] == 0.0:
			_coast[k] = maxf(_coast[(k + 359) % 360], _coast[(k + 1) % 360])
		if _coast[k] == 0.0:
			_coast[k] = sim.layout.island_radius


## Blender material names -> the game's materials (LLMaterials; the island's terrain shader).
func _apply_mats(root_: Node) -> void:
	var stack: Array = [root_]
	while stack.size() > 0:
		var n: Node = stack.pop_back()
		stack.append_array(n.get_children())
		if n is MeshInstance3D and n.mesh:
			for i in n.mesh.get_surface_count():
				var m: Material = n.mesh.surface_get_material(i)
				if m == null:
					continue
				var rep: Material = _terrain_mat() if m.resource_name == "M_LL_Terrain" else LLMaterials.get_mat(m.resource_name)
				if rep:
					n.set_surface_override_material(i, rep)


func _reefs() -> void:
	var meshes: Array = []
	for v in 3:
		meshes.append(_rock_mesh(v))
	var mat := LLMaterials.get_mat("M_LL_Rock")
	for r in sim.layout.reefs:
		var mi := MeshInstance3D.new()
		mi.mesh = meshes[r["variant"] % 3]
		mi.material_override = mat
		mi.position = Geo.to_v3(r["pos"], -0.6)
		mi.rotation.y = deg_to_rad(r["rot"])
		mi.scale = Vector3(r["r"], r["r"] * (0.55 + 0.6 * r["height"]), r["r"])
		add_child(mi)


## G6d: the title screen's own props. The keeper's boat is moored alongside the landing, riding the swell,
## its painter (bow line) sagging to the near bollard. Title only: in the story the landing is empty until
## the visitor's launch comes alongside in ch4 (canon; DECISIONS Q14).
func setup_title() -> void:
	if title_boat != null or not ResourceLoader.exists(BOAT_GLB):
		return
	title_boat = load(BOAT_GLB).instantiate()
	add_child(title_boat)
	_apply_mats(title_boat)
	var ring := title_boat.find_child("ROPE_bow", true, false) as Node3D
	_boat_bow = ring.position if ring else Vector3(2.0, 0.6, 0)
	var rope_m := LLMaterials.get_mat("M_LL_Rope")
	for i in 12:
		var seg := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.02
		cm.bottom_radius = 0.02
		cm.height = 1.0
		cm.radial_segments = 6
		cm.rings = 1
		seg.mesh = cm
		seg.material_override = rope_m
		seg.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(seg)
		_rope.append(seg)
	_tick_boat(0.0, sim.storm if sim else 0.75)
	_title_storm_fx()


# ------------------------------------------------------------------ G6d stage D: the title's storm

static func _qn(counts: Array) -> int:
	return int(counts[clampi(int(Settings.v["quality"]), 0, counts.size() - 1)])


func _streak_mat(tint: Color, length_m: float, width_m: float, px_per_m: float) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/rain_streak.gdshader")
	m.set_shader_parameter("tint", tint)
	m.set_shader_parameter("length_m", length_m)
	m.set_shader_parameter("width_m", width_m)
	m.set_shader_parameter("px_per_m", px_per_m)
	_streak_mats.append(m)
	return m


func _streak_quad(mat: ShaderMaterial) -> QuadMesh:
	var q := QuadMesh.new()
	q.size = Vector2(1, 1)
	q.material = mat
	return q


## The title's storm: wind-slanted rain in two layers (the ring round the tower, far, and a streak layer
## near the camera, for parallax), splashes on the landing and walkway decks, spray where the swell meets
## the ledges, and a beam tuned for the menu. Off with --norain (rain, splashes, spray) like the story rain.
func _title_storm_fx() -> void:
	if title_fx != null:
		return
	title_fx = Node3D.new()
	title_fx.name = "TitleStorm"
	add_child(title_fx)
	var raining := not GameState.user_args.has("norain")
	# perf bisect: --title_off=ring,near,splash,spray leaves that part as it was before stage D (ring) or out
	var off := String(GameState.user_args.get("title_off", "")).split(",")
	var wind_dir := (TitleStorm.WIND + Vector3(0, -TitleStorm.RAIN_FALL, 0)).normalized()
	var speed := (TitleStorm.WIND + Vector3(0, -TitleStorm.RAIN_FALL, 0)).length()
	# 1) the ring layer (far, round the tower) drifts with the gale and is drawn as streaks
	var pm: ParticleProcessMaterial = rain.process_material
	if not off.has("ring"):
		pm.direction = wind_dir
		pm.spread = 5.0
		pm.initial_velocity_min = speed * 0.9
		pm.initial_velocity_max = speed * 1.1
		pm.gravity = Vector3(0, -4.0, 0)
		pm.particle_flag_align_y = true
		rain.draw_pass_1 = _streak_quad(_streak_mat(Color(0.7, 0.76, 0.85, 0.2), 0.8, 0.006, 0.0011))
	# 2) the near layer: a box of streaks 2-26 m in front of the camera, following it
	near_rain = GPUParticles3D.new()
	near_rain.name = "NearRain"
	near_rain.amount = _qn(TITLE_NEAR_RAIN)
	near_rain.lifetime = 0.7
	near_rain.preprocess = 0.7
	near_rain.local_coords = false
	near_rain.visibility_aabb = AABB(Vector3(-22, -16, -22), Vector3(44, 32, 44))
	near_rain.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var npm := ParticleProcessMaterial.new()
	npm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	npm.emission_box_extents = Vector3(10, 6, 11)            # the 32 deg title lens (stage E): 4-26 m ahead
	npm.direction = wind_dir
	npm.spread = 3.0
	npm.initial_velocity_min = speed * 0.9
	npm.initial_velocity_max = speed * 1.1
	npm.gravity = Vector3.ZERO
	npm.particle_flag_align_y = true
	near_rain.process_material = npm
	var nm := _streak_mat(Color(0.66, 0.72, 0.8, 0.26), 0.75, 0.004, 0.0013)
	nm.set_shader_parameter("mask_x", TITLE_BEAM_MASK - Vector2(0.08, 0.08))
	nm.set_shader_parameter("mask_floor", 0.35)            # the near rain thins over the menu column
	near_rain.draw_pass_1 = _streak_quad(nm)
	near_rain.emitting = raining and not off.has("near")
	near_rain.visible = not off.has("near")
	title_fx.add_child(near_rain)
	_title_splashes(raining and not off.has("splash"))
	_title_spray(raining and not off.has("spray"))
	# 3) the beam: a longer, stronger shaft than the story's (seen from 100 m, not from the gallery), its
	# cone faded out before the menu column (beam.gdshader mask_x)
	beam_mat.set_shader_parameter("mask_x", title_mask)
	beam_mat.set_shader_parameter("mask_floor", TITLE_BEAM_FLOOR)
	beam_mat.set_shader_parameter("near_fade", Vector2(2.0, 12.0))
	beam_mat.set_shader_parameter("decay", 2.6)


## R2: main_fp tells the title where its text column ends (fraction of the width). The cone softens from
## just inside that edge to well clear of it, never below TITLE_BEAM_FLOOR.
func set_title_column(right: float) -> void:
	title_mask = Vector2(clampf(right - 0.05, 0.05, 0.9), clampf(right + 0.15, 0.1, 0.98))
	if title_fx:
		beam_mat.set_shader_parameter("mask_x", title_mask)


## Splashes: drops bursting up off every upward face of the landing and walkway (decks, steps, bollards).
func _title_splashes(raining: bool) -> void:
	var n := _qn(TITLE_SPLASHES)
	if n == 0 or not raining:
		return
	var pts := PackedVector3Array()
	var areas := PackedFloat32Array()
	var total := 0.0
	for mi in find_children("SM_*", "MeshInstance3D", true, false):
		var nm := String(mi.name)
		if not (nm.begins_with("SM_Landing") or nm.begins_with("SM_Walkway")) or mi.mesh == null:
			continue
		var xf: Transform3D = mi.global_transform
		for s in mi.mesh.get_surface_count():
			var arr: Array = mi.mesh.surface_get_arrays(s)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			var tri_n := idx.size() / 3 if idx.size() > 0 else v.size() / 3
			for t in tri_n:
				var a := xf * v[idx[t * 3] if idx.size() > 0 else t * 3]
				var b := xf * v[idx[t * 3 + 1] if idx.size() > 0 else t * 3 + 1]
				var c := xf * v[idx[t * 3 + 2] if idx.size() > 0 else t * 3 + 2]
				var cr := (b - a).cross(c - a)
				var area := cr.length() * 0.5
				if area < 1e-4 or absf(cr.normalized().y) < 0.85:
					continue
				total += area
				pts.append(a)
				pts.append(b)
				pts.append(c)
				areas.append(total)
	if areas.is_empty():
		return
	# area-weighted samples on the upward faces, as an emission point texture (world space, emitter at origin)
	var rng := RandomNumberGenerator.new()
	rng.seed = 23
	var count := 512
	var img := Image.create(count, 1, false, Image.FORMAT_RGBF)
	for i in count:
		var k := areas.bsearch(rng.randf() * total)
		k = mini(k, areas.size() - 1)
		var u := rng.randf()
		var w := rng.randf()
		if u + w > 1.0:
			u = 1.0 - u
			w = 1.0 - w
		var p := pts[k * 3] + (pts[k * 3 + 1] - pts[k * 3]) * u + (pts[k * 3 + 2] - pts[k * 3]) * w + Vector3(0, 0.01, 0)
		img.set_pixel(i, 0, Color(p.x, p.y, p.z))
	splashes = GPUParticles3D.new()
	splashes.name = "DeckSplashes"
	splashes.amount = n
	splashes.lifetime = 0.24
	splashes.local_coords = false
	splashes.visibility_aabb = AABB(Vector3(-5, -2, -30), Vector3(25, 12, 32))
	splashes.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var spm := ParticleProcessMaterial.new()
	spm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_POINTS
	spm.emission_point_texture = ImageTexture.create_from_image(img)
	spm.emission_point_count = count
	spm.direction = Vector3(0, 1, 0)
	spm.spread = 38.0
	spm.initial_velocity_min = 0.9
	spm.initial_velocity_max = 2.0
	spm.gravity = Vector3(TitleStorm.WIND.x * 0.15, -9.8, TitleStorm.WIND.z * 0.15)
	spm.particle_flag_align_y = true
	splashes.process_material = spm
	splashes.draw_pass_1 = _streak_quad(_streak_mat(Color(0.8, 0.84, 0.9, 0.6), 0.16, 0.009, 0.0014))
	splashes.emitting = raining
	title_fx.add_child(splashes)


## Spray: a pool of one-shot bursts, fired along the ledges that face the swell as a crest arrives there
## (OceanWaves, the same surface the ocean shader draws), carried downwind by the gale.
func _title_spray(raining: bool) -> void:
	if not raining or _coast.is_empty():
		return
	var tex := GradientTexture2D.new()
	var gr := Gradient.new()
	gr.set_color(0, Color(1, 1, 1, 0.5))           # no hot core: a flat soft puff (g6d_d3 read as glowing dots)
	gr.set_color(1, Color(1, 1, 1, 0))
	gr.set_offset(1, 1.0)
	gr.add_point(0.3, Color(1, 1, 1, 0.4))
	gr.add_point(0.62, Color(1, 1, 1, 0.12))
	tex.gradient = gr
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	tex.width = 64
	tex.height = 64
	_spray_mat = StandardMaterial3D.new()
	_spray_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_spray_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_spray_mat.albedo_texture = tex
	_spray_mat.albedo_color = Color(0.5, 0.54, 0.58, 0.55)
	_spray_mat.vertex_color_use_as_albedo = true
	_spray_mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	_spray_mat.billboard_keep_scale = true
	_spray_mat.proximity_fade_enabled = true
	_spray_mat.proximity_fade_distance = 1.2
	_spray_mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	var quad := QuadMesh.new()
	quad.size = Vector2(1.8, 1.8)
	quad.material = _spray_mat
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1, 1, 1, 0))
	ramp.set_color(1, Color(1, 1, 1, 0))
	ramp.add_point(0.1, Color(1, 1, 1, 0.42))
	ramp.add_point(0.5, Color(1, 1, 1, 0.22))
	var ramp_t := GradientTexture1D.new()
	ramp_t.gradient = ramp
	var sc := Curve.new()
	sc.add_point(Vector2(0, 0.4))
	sc.add_point(Vector2(1, 2.4))
	var sc_t := CurveTexture.new()
	sc_t.curve = sc
	for i in _qn(TITLE_SPRAY):
		var e := GPUParticles3D.new()
		e.name = "Spray%d" % i
		e.amount = TITLE_SPRAY_N
		e.lifetime = 1.8
		e.one_shot = true
		e.explosiveness = 0.8
		e.local_coords = false
		e.emitting = false
		e.visibility_aabb = AABB(Vector3(-14, -2, -14), Vector3(28, 18, 28))
		e.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var pm := ParticleProcessMaterial.new()
		pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
		pm.emission_sphere_radius = 1.8
		pm.direction = Vector3(0, 1, 0)
		pm.spread = 26.0
		pm.initial_velocity_min = 3.5
		pm.initial_velocity_max = 7.5
		pm.gravity = Vector3(TitleStorm.WIND.x * 0.45, -9.8, TitleStorm.WIND.z * 0.45)
		pm.damping_min = 1.0
		pm.damping_max = 2.0
		pm.scale_min = 0.6
		pm.scale_max = 1.5
		pm.scale_curve = sc_t
		pm.color_ramp = ramp_t
		e.process_material = pm
		e.draw_pass_1 = quad
		title_fx.add_child(e)
		spray.append(e)
	# the ledges that face the swell (the waves run roughly south, so the north side takes it), every 5
	# degrees, but not the landing (bearings 16-40: the pier and the boat)
	var swell := Vector2.ZERO
	for w in OceanWaves.WAVES:
		swell += Vector2(w.x, w.y).normalized() * w.z
	swell = swell.normalized()
	for deg in range(0, 360, 5):
		if deg >= 16 and deg <= 40:
			continue
		var b := deg_to_rad(float(deg))
		var out2 := Geo.dir(b)
		var expo := out2.dot(-swell)
		if expo < 0.2:
			continue
		var p2 := Geo.polar(b, _coast[deg] + 0.5)
		_spray_pts.append([Vector3(p2.x, 0.15, p2.y), Vector3(out2.x, 0, out2.y), 0.0, 0.0, expo])


## Per frame on the title: the near rain follows the camera, lightning lights the rain and spray, spray
## fires on arriving crests, and the beam's fog scatter drops while the beam points into the menu column.
func _title_step(delta: float, storm: float, level: float) -> void:
	var cam := get_viewport().get_camera_3d() if is_inside_tree() else null
	for m in _streak_mats:
		m.set_shader_parameter("flash", flash_now)
	if _spray_mat:
		var k := 1.0 + 2.5 * flash_now
		_spray_mat.albedo_color = Color(0.5 * k, 0.54 * k, 0.58 * k, 0.55)
	if cam and near_rain:
		near_rain.global_position = cam.global_position - cam.global_basis.z * 15.0
	# spray: a rising crest past the threshold at a ledge fires the next free emitter there
	_spray_gap = maxf(0.0, _spray_gap - delta)
	if not spray.is_empty():
		for sp in _spray_pts:
			var h := OceanWaves.height_at(Vector2(sp[0].x, sp[0].z), _t, storm)
			var thr: float = 0.42 - 0.12 * sp[4]
			if h > thr and sp[2] <= thr and _t >= sp[3] and _spray_gap <= 0.0:
				var e: GPUParticles3D = spray[_spray_next]
				if not e.emitting:
					var pm: ParticleProcessMaterial = e.process_material
					var strength := clampf((h - thr) * 6.0 + sp[4], 0.6, 1.6)
					pm.direction = (Vector3.UP + sp[1] * 0.35).normalized()
					pm.initial_velocity_min = 5.0 * strength      # plumes 1-6 m: visible from the title camera
					pm.initial_velocity_max = 10.5 * strength
					e.global_position = sp[0]
					e.restart()
					e.emitting = true
					_spray_next = (_spray_next + 1) % spray.size()
					spray_fired += 1
					sp[3] = _t + 3.5
					_spray_gap = 0.45
			sp[2] = h
	# the beam's fog scatter (it can't be masked like the cone): full while the beam points right of the
	# column or along the camera's line, low while its near 120 m lies over the menu
	if cam:
		var vw := get_viewport().get_visible_rect().size.x
		var fwd := -beam_light.global_transform.basis.z
		var minx := 1.0
		for d in [25.0, 60.0, 120.0]:
			var p: Vector3 = beam_pivot.global_position + fwd * d
			if not cam.is_position_behind(p):
				minx = minf(minx, cam.unproject_position(p).x / maxf(vw, 1.0))
		var k2 := smoothstep(title_mask.x, title_mask.y, minx)
		# R2: the scatter keeps half its strength over the column too (it used to drop to 0.3: the beam
		# visibly went out as it crossed the title)
		var face := beam_facing_cam(cam)
		beam_light.light_volumetric_fog_energy = lerpf(0.85, 1.7, k2) + 0.6 * face
		beam_mat.set_shader_parameter("intensity", 0.72 * level * (1.0 + 0.25 * face))
		# R2 (issue 10): as the beam swings toward the lens the night answers a little: a touch more glow
		# and exposure, the lantern brighter. Physically modest, no flare; follows the beam frame by frame.
		env.glow_intensity = 0.45 + 0.2 * face
		env.tonemap_exposure *= 1.0 + 0.05 * face
		lamp_glow.light_energy = 2.5 * level * (1.0 + 1.2 * face)


## 0..1: how squarely the turning beam points at the camera (horizontal plane, sharpened so it only swells
## as the beam sweeps past). game_fp.beam_facing() is the same measure for the menu's glow.
func beam_facing_cam(cam: Camera3D) -> float:
	var f: Vector3 = -beam_pivot.global_transform.basis.z
	var to_cam: Vector3 = cam.global_position - beam_pivot.global_position
	f.y = 0.0
	to_cam.y = 0.0
	if f.length() < 1e-4 or to_cam.length() < 1e-4:
		return 0.0
	return pow(maxf(f.normalized().dot(to_cam.normalized()), 0.0), 10.0)


func _landing_frame() -> Array:
	var b := deg_to_rad(28.0)
	var o := Vector3(sin(b), 0, -cos(b))                   # outward along the pier
	var r := Vector3(cos(b), 0, sin(b))                    # right, looking out
	return [Geo.to_v3(Geo.polar(b, 18.5), 0.0), o, r]


func _tick_boat(t: float, storm: float) -> void:
	var f := _landing_frame()
	var root_: Vector3 = f[0]
	var o: Vector3 = f[1]
	var r: Vector3 = f[2]
	var berth := root_ + o * (3.0 + 0.18 * sin(t * 0.31)) - r * 2.75     # alongside the pier's left side
	var p2 := Vector2(berth.x, berth.z)
	var h := OceanWaves.height_at(p2, t, storm)
	var nrm := OceanWaves.normal_at(p2, t, storm, 1.0)
	var fwd := o.rotated(Vector3.UP, 0.05 * sin(t * 0.23) + 0.03 * sin(t * 0.71))
	var basis := Basis(fwd, Vector3.UP, fwd.cross(Vector3.UP))
	var tilt := Basis(Quaternion(Vector3.UP, nrm.lerp(Vector3.UP, 0.45).normalized()))
	title_boat.transform = Transform3D(tilt * basis, Vector3(berth.x, h + 0.02, berth.z))
	# the painter: bow ring to the near bollard top, a sag that tightens as the boat surges out
	var a := title_boat.transform * _boat_bow
	var b := root_ + o * 2.0 - r * 1.25 + Vector3.UP * 1.72
	var span := a.distance_to(b)
	var sag := clampf(0.9 - span * 0.12, 0.08, 0.7)
	var prev := a
	for i in _rope.size():
		var k := float(i + 1) / _rope.size()
		var q := a.lerp(b, k) - Vector3.UP * sag * 4.0 * k * (1.0 - k)
		var seg := _rope[i]
		var d := q - prev
		seg.scale = Vector3(1.0, maxf(d.length(), 0.001), 1.0)
		seg.global_position = (prev + q) * 0.5
		if d.length() > 0.001:
			var y := d.normalized()
			var x := y.cross(Vector3.FORWARD if absf(y.dot(Vector3.FORWARD)) < 0.9 else Vector3.RIGHT).normalized()
			seg.global_basis = Basis(x, y, x.cross(y)).scaled(Vector3(1.0, d.length(), 1.0))
		prev = q


## The landing below the light (bearing 028): concrete pier, timber fenders, bollards, steps up the rock.
func _jetty() -> void:
	var root := Node3D.new()
	add_child(root)
	var b := deg_to_rad(28.0)
	var outward := Vector3(sin(b), 0, -cos(b))
	root.position = Geo.to_v3(Geo.polar(b, 18.5), 0.0)
	root.look_at(root.position + outward, Vector3.UP)
	var conc := LLMaterials.get_mat("M_LL_ConcreteExt")
	var wood := LLMaterials.get_mat("M_LL_WoodDark")
	var iron := LLMaterials.get_mat("M_LL_Iron")
	_box(root, Vector3(3.2, 1.6, 9.0), Vector3(0, 0.4, -4.5), conc)                  # pier deck (top at 1.2 m)
	for k in 6:
		_box(root, Vector3(0.25, 2.2, 0.25), Vector3(1.72, 0.0, -1.0 - k * 1.5), wood)  # fenders
	for z in [-2.0, -7.5]:
		var bol := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.16
		cm.bottom_radius = 0.2
		cm.height = 0.45
		bol.mesh = cm
		bol.material_override = iron
		bol.position = Vector3(1.2, 1.42, z)
		root.add_child(bol)
	for k in 8:                                                                         # steps up to the island
		_box(root, Vector3(1.4, 0.32, 0.5), Vector3(-0.6, 1.25 + k * 0.3, 0.3 + k * 0.45), conc)


func _box(parent: Node3D, size: Vector3, pos: Vector3, mat: Material) -> void:
	var m := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	m.mesh = bm
	m.material_override = mat
	m.position = pos
	parent.add_child(m)


func _rock_mesh(variant: int) -> ArrayMesh:
	var sm := SphereMesh.new()
	sm.radius = 1.0
	sm.height = 2.0
	sm.radial_segments = 20
	sm.rings = 12
	var arr := sm.get_mesh_arrays()
	var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var noise := FastNoiseLite.new()
	noise.seed = 11 + variant * 7
	noise.frequency = 1.3
	noise.fractal_octaves = 3
	for i in verts.size():
		var v := verts[i]
		var d := 1.0 + noise.get_noise_3dv(v * 1.0) * 0.35
		v *= d
		v.y = maxf(v.y, -0.3) * 1.0
		if v.y > 0.0:
			v.y *= 0.8 + 0.3 * absf(noise.get_noise_2d(v.x * 3.0, v.z * 3.0))
		verts[i] = v
	arr[Mesh.ARRAY_VERTEX] = verts
	arr[Mesh.ARRAY_NORMAL] = null
	arr[Mesh.ARRAY_TANGENT] = null
	var st := SurfaceTool.new()
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	st.create_from(am, 0)
	st.generate_normals()
	return st.commit()


func _lighthouse() -> void:
	var lh: Node3D = load("res://assets/models/lighthouse.glb").instantiate()
	add_child(lh)
	_apply_mats(lh)
	var stack: Array = [lh]
	while stack.size() > 0:
		var n: Node = stack.pop_back()
		stack.append_array(n.get_children())
		if n is MeshInstance3D and String(n.name).begins_with("GLS_"):
			n.material_override = LLMaterials.glass()
		if String(n.name) == "PT_optic":
			optic = n
	# G6d: the bulkhead lamp over the base door (blender build_entrance: 6.13 m out on bearing 35, 6.18 m
	# up): a small warm pool on the door, the step and the walkway's last boards. No shadow (cost).
	door_lamp = OmniLight3D.new()
	door_lamp.position = Vector3(6.13 * 0.5736, 6.18, -6.13 * 0.8192)
	door_lamp.light_color = Color(1.0, 0.74, 0.46)
	door_lamp.omni_range = 7.0
	door_lamp.omni_attenuation = 1.4
	door_lamp.light_energy = 1.6
	door_lamp.light_volumetric_fog_energy = 0.6
	door_lamp.shadow_enabled = false
	door_lamp.light_cull_mask = EXTERIOR_ONLY
	add_child(door_lamp)
	lamp_glow = OmniLight3D.new()
	lamp_glow.position = Vector3(0, LANTERN_Y, 0)
	lamp_glow.light_color = Color(1.0, 0.76, 0.45)
	lamp_glow.omni_range = 9.0
	lamp_glow.light_energy = 2.5
	lamp_glow.light_volumetric_fog_energy = 2.0
	lamp_glow.shadow_enabled = false
	lamp_glow.light_cull_mask = EXTERIOR_ONLY    # unshadowed, 4.8 m above the floor: it lit the room through the roof
	add_child(lamp_glow)


func _beam() -> void:
	beam_pivot = Node3D.new()
	beam_pivot.position = Vector3(0, LANTERN_Y, 0)
	add_child(beam_pivot)
	beam_light = SpotLight3D.new()
	beam_light.light_color = Color(1.0, 0.78, 0.5)
	beam_light.light_energy = 40.0
	beam_light.spot_range = 230.0
	beam_light.spot_angle = 7.0
	beam_light.spot_attenuation = 0.5
	beam_light.light_volumetric_fog_energy = 5.0
	beam_light.shadow_enabled = false
	beam_light.light_cull_mask = EXTERIOR_ONLY
	beam_light.rotation_degrees.x = -3.0
	beam_pivot.add_child(beam_light)
	var tilt := Node3D.new()
	tilt.rotation_degrees.x = -3.0
	beam_pivot.add_child(tilt)
	beam_cone = MeshInstance3D.new()
	var cm := CylinderMesh.new()
	var L := 190.0
	cm.top_radius = 0.6
	cm.bottom_radius = tan(deg_to_rad(5.5)) * L
	cm.height = L
	cm.radial_segments = 24
	cm.rings = 8
	cm.cap_top = false
	cm.cap_bottom = false
	beam_cone.mesh = cm
	beam_cone.rotation_degrees.x = 90.0
	beam_cone.position = Vector3(0, 0, -L * 0.5)
	beam_mat = ShaderMaterial.new()
	beam_mat.shader = load("res://shaders/beam.gdshader")
	beam_mat.set_shader_parameter("length_m", L)
	beam_mat.set_shader_parameter("noise", _noise_tex)
	beam_cone.material_override = beam_mat
	beam_cone.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	tilt.add_child(beam_cone)


func _rain() -> void:
	rain = GPUParticles3D.new()
	rain.amount = Settings.q_rain_amount()
	rain.lifetime = 1.4
	rain.visibility_aabb = AABB(Vector3(-40, -25, -40), Vector3(80, 50, 80))
	# particles are re-uploaded every frame; as a shadow caster whose AABB encloses the room, the rain forced
	# every shadowed interior light to re-render its shadow map every frame (1p performance)
	rain.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	rain.position = Vector3(0, 30, 0)
	var pm := ParticleProcessMaterial.new()
	# Rain fix: emit only from a ring OUTSIDE the tower (never above the roof), and kill every drop that
	# reaches solid geometry (roof, gallery, walls, island, sea) via the heightfield collider below.
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_RING
	pm.emission_ring_axis = Vector3.UP
	pm.emission_ring_radius = 34.0
	pm.emission_ring_inner_radius = 6.5
	pm.emission_ring_height = 3.0
	pm.collision_mode = ParticleProcessMaterial.COLLISION_HIDE_ON_CONTACT
	pm.collision_use_scale = false
	pm.direction = Vector3(0.35, -1, 0.15)
	pm.spread = 4.0
	pm.initial_velocity_min = 22.0
	pm.initial_velocity_max = 28.0
	pm.gravity = Vector3(0, -9.8, 0)
	rain.process_material = pm
	var quad := QuadMesh.new()
	quad.size = Vector2(0.018, 0.55)
	var rm := StandardMaterial3D.new()
	rm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	rm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	rm.albedo_color = Color(0.7, 0.76, 0.85, 0.18)
	rm.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
	quad.material = rm
	rain.draw_pass_1 = quad
	rain.emitting = not GameState.user_args.has("norain")
	rain.collision_base_size = 0.02
	add_child(rain)
	var hf := GPUParticlesCollisionHeightField3D.new()
	hf.size = Vector3(76, 44, 76)
	hf.position = Vector3(0, 12, 0)
	hf.resolution = GPUParticlesCollisionHeightField3D.RESOLUTION_512
	hf.update_mode = GPUParticlesCollisionHeightField3D.UPDATE_MODE_WHEN_MOVED
	add_child(hf)


# ------------------------------------------------------------------ per-frame

func on_events(events: Array) -> void:
	for e in events:
		match e["type"]:
			"lightning":
				flash = e["power"]
				_flash_dir = Geo.dir(e["bearing"])
				_flash_light = float(e.get("light", 1.0))
				if e.get("title", false):
					# G6d: the title camera sees the island's landing side, away from the strikes. A flash lights the
					# cloud deck overhead, so the title's flash light comes from high on the camera's side
					var lb: float = deg_to_rad(20.0) + (float(e["bearing"]) - PI) * 0.5
					bolt_light.rotation = Vector3(deg_to_rad(-58), Geo.yaw_for(lb) + PI, 0)
				else:
					bolt_light.rotation = Vector3(deg_to_rad(-40), Geo.yaw_for(e["bearing"]) + PI, 0)
				_strike_bolt(e)
			"lightning_pulse":                          # G6d title: a flash's follow-up pulse (no thunder, no bolt)
				flash = maxf(flash, float(e["power"]))
			"ship_spawned":
				var s := sim.find_ship(e["ship"])
				var v := SHIP_VIEW.new()
				add_child(v)
				v.setup(s)
				ship_views[s.id] = v
			"ship_lost":
				if ship_views.has(e["ship"]):
					ship_views[e["ship"]].wreck()


func _process(delta: float) -> void:
	var _pt := Time.get_ticks_usec()
	_process_body(delta)
	GameState.prof_add("outside", Time.get_ticks_usec() - _pt)


func _process_body(delta: float) -> void:
	if sim == null:
		return
	_t += delta
	var storm := sim.storm
	if sim.story_mode:
		if _sky_mode == "dawn":
			dawn = minf(1.0, dawn + delta / 25.0)
		dusk = maxf(0.0, dusk - delta / 240.0)     # dusk drains to night over four minutes
	elif sim.result != KeeperSim.Result.RUNNING or sim.t > sim.cfg.night_length - 40.0:
		dawn = minf(1.0, dawn + delta / 25.0)
	flash = maxf(0.0, flash - delta * 2.2)
	var f := flash * (0.55 + 0.45 * sin(_t * 47.0)) if flash > 0.05 else 0.0
	if Settings.v["reduce_flashing"]:
		f *= 0.3
	flash_now = f
	_bolt_step(delta)
	bolt_light.light_energy = f * 2.6 * _flash_light
	sky_mat.set_shader_parameter("storm", storm)
	sky_mat.set_shader_parameter("flash", f)
	sky_mat.set_shader_parameter("dawn", maxf(dawn, dusk * 0.55))
	sky_mat.set_shader_parameter("time_s", _t)
	sky_mat.set_shader_parameter("flash_dir", _flash_dir)
	ocean_mat.set_shader_parameter("storm", storm)
	ocean_mat.set_shader_parameter("time_s", _t)
	ocean_mat.set_shader_parameter("flash", f)
	beam_mat.set_shader_parameter("time_s", _t)
	env.tonemap_exposure = 1.35 * float(Settings.v["brightness"])
	env.volumetric_fog_density = lerpf(0.006, 0.016, storm) * (1.0 - 0.7 * dawn) * (0.3 if attract else 1.0)
	env.fog_density = ATMOS.fog_density(storm, dawn)
	if sea_legacy:
		env.fog_light_color = Color(0.05, 0.065, 0.085).lerp(Color(0.45, 0.42, 0.42), dawn)
	else:                                       # Stage M (M2): the fog and the sky's bank share the murk
		var murk := ATMOS.horizon_color(maxf(dawn, dusk * 0.55), f)
		env.fog_light_color = murk
		sky_mat.set_shader_parameter("murk", murk)
		sky_mat.set_shader_parameter("sky_gain", ATMOS.sky_gain(env.volumetric_fog_density, env.volumetric_fog_enabled)
			if env.volumetric_fog_sky_affect > 0.41 else 1.0)     # (--volsky=0.4, option B: the old share, no gain)
	env.ambient_light_energy = 0.9 + 1.6 * dawn + 2.0 * f
	moon.light_energy = 0.45 + 0.9 * dawn
	moon.light_color = Color(0.55, 0.64, 0.82).lerp(Color(1.0, 0.8, 0.66), dawn)
	rain.amount_ratio = clampf(0.25 + storm * 0.9 - dawn * 0.8, 0.05, 1.0)
	WindowGlass.set_weather(clampf(0.3 + storm * 0.8 - dawn * 0.5, 0.1, 1.0), f)
	# beam follows the sim; lamp output follows power + intensity; flicker on a low battery
	var lit := sim.lamp_on()
	var level: float = [0.55, 0.8, 1.15][sim.intensity]
	if lit and sim.battery < 8.0:
		level *= 0.6 + 0.4 * float(randf() > 0.2)
	var focused := sim.mode == KeeperSim.Mode.MANUAL
	var drawn := sim.draw_bearing()         # R2: interpolated between physics steps (no 60 Hz stepping)
	beam_pivot.rotation.y = Geo.yaw_for(drawn)
	if optic:
		optic.rotation.y = Geo.yaw_for(drawn)
	beam_light.visible = lit
	beam_cone.visible = lit
	beam_light.light_energy = 40.0 * level * (1.3 if focused else 1.0)
	beam_light.light_volumetric_fog_energy = 1.2 if attract else 5.0
	beam_light.spot_range = sim.vis_range() * (sim.cfg.focus_mul if focused else 1.0) + 40.0
	beam_mat.set_shader_parameter("intensity", (0.9 if focused else 0.6) * level * (1.0 - 0.6 * dawn))
	lamp_glow.light_energy = 2.5 * level if lit else 0.0
	if title_fx:
		_title_step(delta, storm, level)
	for id in ship_views.keys():
		var v = ship_views[id]
		if v.done:
			v.queue_free()
			ship_views.erase(id)
		else:
			v.tick(_t, delta, storm, sim)
	if title_boat:
		_tick_boat(_t, storm)
