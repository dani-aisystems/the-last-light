extends SceneTree
## G5 (findings 29, 30): distant lightning bolts, storm and cabin SFX. Runs against the real game.
##   godot --headless --path godot -s res://tests/g5_weather_audio_test.gd
## Checks what can be checked without ears or eyes: buses, routing, loop lengths, thunder timing and
## variant choice, the bolt's geometry and lifetime, reduce-flashing, and the three fixed defects.
## Whether it SOUNDS or LOOKS right is Daniel's call (listening session, window capture).
## Prints one line per check and G5_RESULT {json}; exit 1 on any FAIL.

var g: Node3D
var fails := 0
var checks := 0


func _initialize() -> void:
	_run.call_deferred()


func _ok(name: String, cond: bool, note := "") -> void:
	checks += 1
	if not cond:
		fails += 1
	print("  %-4s %-34s %s" % ["PASS" if cond else "FAIL", name, note])


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _players(n: String) -> Array:
	var out: Array = []
	for c in g.audio.get_children():
		if (c is AudioStreamPlayer or c is AudioStreamPlayer3D) and c.stream and c.stream.resource_path.ends_with("/%s.wav" % n):
			out.append(c)
	return out


func _run() -> void:
	await process_frame
	var settings: Node = root.get_node("Settings")
	g = load("res://scripts/fp/game_fp.gd").new()
	root.add_child(g)
	g.start(3, "", false, true, {})
	await _frames(3)
	g.director.process_mode = Node.PROCESS_MODE_DISABLED
	var au: Node = g.audio

	# --- 30: the Exterior bus and routing
	var ei := AudioServer.get_bus_index("Exterior")
	_ok("exterior bus exists", ei != -1)
	_ok("exterior sends to Ambient", ei != -1 and AudioServer.get_bus_send(ei) == &"Ambient")
	var lp := AudioServer.get_bus_effect(ei, 0) if ei != -1 and AudioServer.get_bus_effect_count(ei) > 0 else null
	_ok("exterior low-pass present", lp is AudioEffectLowPassFilter)
	_ok("muffled in game", lp is AudioEffectLowPassFilter and absf(lp.cutoff_hz - au.MUFFLE_HZ) < 1.0, "%.0f Hz" % (lp.cutoff_hz if lp else -1.0))
	for n in ["amb_wind", "amb_gust", "amb_rain", "amb_sea"]:
		_ok("%s on Exterior" % n, au.loops.has(n) and au.loops[n].bus == &"Exterior" and au.loops[n].playing)
	var glass: Array = au._glass
	_ok("glass layers placed", glass.size() >= 1 and glass.size() <= au.GLASS_LAYERS, "%d" % glass.size())
	_ok("glass layers unmuffled + playing", glass.all(func(p): return p.bus == &"Ambient" and p.playing))
	_ok("glass layers 3D at the windows", glass.all(func(p): return p is AudioStreamPlayer3D and Vector2(p.global_position.x, p.global_position.z).length() > 1.0))

	# --- 30: loop lengths (no constant layer repeats faster than 20 s)
	for n in ["amb_wind", "amb_gust", "amb_rain", "amb_sea", "gen_idle", "hum", "clockwork", "static", "motor_grind"]:
		var L: float = au.loops[n].stream.get_length() if au.loops.has(n) else 0.0
		_ok("%s loop >= 20 s" % n, L >= 20.0, "%.1f s" % L)
	_ok("amb_rain_glass loop >= 20 s", glass.size() > 0 and glass[0].stream.get_length() >= 20.0)

	# --- 30 defects: _dev() finds devices, _player2d honours loop=false, set_menu(false) works
	var gen_pos: Vector3 = au.loops["gen_idle"].global_position
	_ok("_dev finds IA_gen_panel", gen_pos.distance_to(Vector3(-2.2, 20.6, 1.7)) > 0.01, str(gen_pos))
	var rad_pos: Vector3 = au.loops["static"].global_position
	_ok("_dev finds IA_radio", rad_pos.distance_to(Vector3(0, 21.0, -2.8)) > 0.01, str(rad_pos))
	au.set_menu(true)
	_ok("menu opens the filter", absf(lp.cutoff_hz - au.OPEN_HZ) < 1.0)
	_ok("menu music plays", au._music.playing)
	au.set_menu(false)
	for i in 30:
		au._process(0.1)
	_ok("set_menu(false) fades music out", not au._music.playing)
	_ok("set_menu(false) re-muffles", absf(lp.cutoff_hz - au.MUFFLE_HZ) < 50.0, "%.0f Hz" % lp.cutoff_hz)

	# --- 30: carrier_click exists and plays on the Dialogue bus
	au.story_cue("sfx", ["carrier_click"])
	var cc := _players("carrier_click")
	_ok("carrier_click plays on Dialogue", cc.size() == 1 and cc[0].bus == &"Dialogue")

	# --- 29/30: the sim's lightning event
	var ev: Array = []
	g.sim._next_lightning = g.sim.t
	g.sim._weather_step(ev)
	var le: Dictionary = ev[0] if ev.size() > 0 else {}
	var d: float = le.get("distance", -1.0)
	_ok("strike distance 400-900 m", d >= 400.0 and d <= 900.0, "%.0f m" % d)
	_ok("thunder delay = distance / 343", absf(le.get("thunder_delay", -1.0) - d / 343.0) < 0.001)

	# --- 30: thunder variant by distance, delayed by the speed of sound
	for case in [[450.0, 0, 2], [850.0, 3, 5]]:
		var before: int = au._pending.size()
		au.on_events([{"type": "lightning", "power": 0.8, "distance": case[0], "thunder_delay": case[0] / 343.0, "bearing": 0.3}])
		_ok("thunder queued @%d m" % int(case[0]), au._pending.size() == before + 1 and absf(au._pending[-1][0] - au._t - case[0] / 343.0) < 0.01)
		for i in 40:
			au._process(0.1)
		var hit := -1
		for k in 6:
			for p in _players("thunder_%d" % k):
				if p.bus == &"Exterior":
					hit = k
		_ok("thunder variant @%d m in %d..%d" % [int(case[0]), case[1], case[2]], hit >= case[1] and hit <= case[2], "thunder_%d" % hit)
		for k in 6:
			for p in _players("thunder_%d" % k):
				p.queue_free()
		await process_frame

	# --- 29: the bolt
	var o: Node3D = g.outside
	settings.v["reduce_flashing"] = false
	var shown0: int = o.bolts_shown
	var skip0: int = o.bolts_skipped
	for i in 200:
		o._strike_bolt({"power": 0.9, "distance": 600.0, "bearing": 0.5})
	var frac := float(o.bolts_shown - shown0) / 200.0
	_ok("a bolt is shown", o.bolts_shown > shown0)
	_ok("only some strikes show a bolt", frac > 0.2 and frac < 0.9, "%.0f %% shown, %d in-cloud" % [frac * 100.0, o.bolts_skipped - skip0])
	if not o.bolt.visible:                       # make sure the last strike drew one, for the geometry checks
		for i in 50:
			o._strike_bolt({"power": 0.9, "distance": 600.0, "bearing": 0.5})
			if o.bolt.visible and o._bolt_age == 0.0:
				break
	var m: ArrayMesh = o.bolt.mesh
	var verts: PackedVector3Array = m.surface_get_arrays(0)[Mesh.ARRAY_VERTEX] if m else PackedVector3Array()
	_ok("bolt mesh built", verts.size() > 100, "%d verts" % verts.size())
	var lo := INF
	var hi := -INF
	var rmin := INF
	var rmax := -INF
	for v in verts:
		lo = minf(lo, v.y)
		hi = maxf(hi, v.y)
		var r := Vector2(v.x, v.z).length()
		rmin = minf(rmin, r)
		rmax = maxf(rmax, r)
	_ok("bolt from cloud base to the sea", lo > -3.0 and lo < 0.0 and hi > 200.0 and hi < 420.0, "y %.1f..%.1f" % [lo, hi])
	_ok("bolt stays far out (no near-ocean clip)", rmin > 300.0 and rmax < 1000.0, "r %.0f..%.0f m" % [rmin, rmax])
	_ok("bolt visible while live", o.bolt.visible)
	var life: float = o._bolt_life
	_ok("bolt life 0.15-0.35 s", life >= 0.15 and life <= 0.35, "%.2f s" % life)
	_ok("restrikes 1-2, on the flicker", o._bolt_strokes.size() >= 2 and o._bolt_strokes.size() <= 3, str(o._bolt_strokes))
	for i in 10:
		o._bolt_step(0.05)
	_ok("bolt gone after its life", not o.bolt.visible)
	settings.v["reduce_flashing"] = true
	var s1: int = o.bolts_shown
	for i in 20:
		o._strike_bolt({"power": 0.9, "distance": 600.0, "bearing": 0.5})
	_ok("reduce-flashing: no bolt", o.bolts_shown == s1)
	settings.v["reduce_flashing"] = false

	print("G5_RESULT ", JSON.stringify({"checks": checks, "fails": fails}))
	quit(1 if fails else 0)
