extends SceneTree
## Audit Stage D: listening sections for Daniel, recorded silently (headless, the Dummy audio driver: nothing is
## played; an AudioEffectRecord on Master captures the mix in real time):
##   godot --headless --path godot -s res://tests/listen_d.gd -- --out=<dir> [--ambience]
## Each section is recorded on its own into <dir>/<name>.wav and prints LISTEN <name> <wall s> <recorded s>; run it
## at normal priority (a throttled mixer falls behind real time, which the two lengths would show). The storm ambience is muted unless --ambience, so
## each sound is heard on its own; the real game mixes it under the storm.

var g: Node3D
var au: Node
var t0_ms := 0
var _sections: Array = []


func _initialize() -> void:
	_run.call_deferred()


func _now() -> float:
	return (Time.get_ticks_msec() - t0_ms) / 1000.0


func _secs(s: float) -> void:
	await create_timer(s).timeout


var rec: AudioEffectRecord
var out_dir := "user://"


func _section(name: String, body: Callable, tail := 1.5) -> void:
	await _secs(0.5)
	rec.set_recording_active(true)
	var a := _now()
	await body.call()
	await _secs(tail)
	rec.set_recording_active(false)
	var w: AudioStreamWAV = rec.get_recording()
	var ok := w != null and w.save_to_wav(out_dir.path_join(name + ".wav")) == OK
	var got: float = w.get_length() if w else 0.0
	print("LISTEN %s wall %.2f recorded %.2f saved %s" % [name, _now() - a, got, ok])
	_sections.append([name, snappedf(_now() - a, 0.01), snappedf(got, 0.01), ok])
	await _secs(1.0)                              # a gap between sections


## The keeper at a device (as when he uses it): 0.8 m in front of it toward the room's centre, eye height.
func _stand_at(ia: String) -> void:
	var p: Vector3 = au._dev(ia, Vector3(0, 20.6, 0))
	var c := Vector3(-p.x, 0.0, -p.z).normalized()
	g.player.global_position = Vector3(p.x, 20.1, p.z) + c * 0.8


func _run() -> void:
	await process_frame
	Engine.max_fps = 60                           # headless runs uncapped; the sounds' timers want real frames
	rec = AudioEffectRecord.new()
	AudioServer.add_bus_effect(0, rec)
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
	g = load("res://scripts/fp/game_fp.gd").new()
	root.add_child(g)
	g.start(3, "", false, true, {})
	await _secs(1.0)
	g.director.process_mode = Node.PROCESS_MODE_DISABLED
	au = g.audio
	var amb := "--ambience" in OS.get_cmdline_user_args()
	for bus in ["Ambient", "Exterior"]:
		var i := AudioServer.get_bus_index(bus)
		if i != -1:
			AudioServer.set_bus_mute(i, not amb)
	g.sim.main_breaker = true
	g.sim.battery = maxf(g.sim.battery, 60.0)
	g.sim.storm_override = 0.5
	var walk := {"pos": Vector3.INF, "walk": false}
	au.player_probe = func(): return walk
	await _secs(1.0)
	t0_ms = Time.get_ticks_msec()

	# 1. static: 3 s alone, 4 s under a radio message (-6 dB), 3 s after; heard from the chair at the set
	var rad: Vector3 = au.loops["static"].global_position
	g.player.global_position = rad + Vector3(0.0, -0.5, 0.0) + Vector3(-rad.x, 0.0, -rad.z).normalized() * 0.9
	var msg := [false]
	au.radio_probe = func(): return msg[0]
	await _section("01_static_dip", func():
		for i in 100:
			au._static_t = 5.0
			if i == 30:
				msg[0] = true
			if i == 70:
				msg[0] = false
			await _secs(0.1))
	au.radio_probe = func(): return false
	g.sim.main_breaker = false                    # the room's hum off for the rest: each sound on its own
	g.player.global_position = Vector3(0.0, 20.1, 0.0)

	# 2. Ross on the stair: the door shut (muffled), then the same climb with the door open
	g.station.door_open = false
	g.station.snap_door()
	await _section("02_stair_door_shut", func():
		au.footsteps("stair", g.station.door_position())
		await _secs(14.0))
	g.station.door_open = true
	g.station.snap_door()
	await _section("03_stair_door_open", func():
		au.footsteps("stair", g.station.door_position())
		await _secs(14.0))
	g.station.door_open = false
	g.station.snap_door()

	# 3. the base door far below, then his cough on the stair (through the door)
	await _section("04_base_door_and_stair_cough", func():
		au.footsteps("base_door", g.station.door_position())
		await _secs(3.0)
		au.story_cue("sfx", ["ross_cough"])
		await _secs(6.0))

	# 4. the door opened: dogs, the heavy leaf, the hinge
	await _section("05_door_opens", func():
		g._on_story_event("door_open", [])
		await _secs(4.0))

	# 5. Ross in the room: a cough (a stage direction), then breaths between lines
	au.visitor_probe = func(): return g.station.door_position() * 0.8 + Vector3(0, -1.6, 0)
	await _section("06_ross_cough_in_room", func():
		au.on_line({"type": "line", "speaker": "", "line_kind": "sound", "text": "[He coughs. It goes on too long.]"})
		await _secs(5.0))
	await _section("07_ross_breaths", func():
		for k in au.BREATHS:
			au.sfx_at("ross_breath_%d" % k, g.station.door_position() * 0.8, -4.0, 2.0)
			await _secs(2.2))

	# 6. documents: open (slide) and close (the softer lay-down), twice
	await _section("08_documents_open_close", func():
		for i in 2:
			g.presenter.open_document("chart")
			await _secs(2.0)
			g.presenter.close_document()
			await _secs(1.5))

	# 7. the title pad fading as a game starts (2.6 s, from where it is)
	await _section("09_title_pad_fade", func():
		au.set_menu(true)
		await _secs(4.0)
		au.set_menu(false, 2.6)
		await _secs(3.5))

	# 8. the keeper's boots: across the room (concrete), then onto the landing (steel)
	var door: Vector3 = g.station.door_position()
	var dh := Vector3(door.x, 0.0, door.z).normalized()
	await _section("10_keeper_steps_concrete_then_landing", func():
		walk["walk"] = true
		for i in 50:                            # 1.4 m/s (0.1 m every 1/14 s) across the room
			walk["pos"] = Vector3(-dh.z, 0, dh.x) * (-2.5 + i * 0.1) + Vector3(0, 20.0, 0)
			await _secs(1.0 / 14.0)
		for i in 22:                            # then out to the door and onto the chequer plate
			walk["pos"] = dh * (1.0 + i * 0.1) + Vector3(0, 20.0, 0)
			await _secs(1.0 / 14.0)
		walk["walk"] = false)

	# 9. handled objects
	_stand_at("IA_phone")
	await _section("11_phone_lift_dead_line", func():
		au.phone()
		await _secs(3.0))
	_stand_at("IA_drawer")
	await _section("12_drawer", func():
		au.drawer()
		await _secs(1.5))
	_stand_at("IA_primus")
	await _section("13_kettle_on_the_primus", func():
		au.kettle()
		await _secs(18.5))
	_stand_at("IA_forecast")
	await _section("14_teleprinter", func():
		au.story_cue("sfx", ["teleprinter"])
		await _secs(10.5))
	_stand_at("IA_sediment_bowl")
	await _section("15_sediment_bowl_drain", func():
		au.on_events([{"type": "bowl_drained"}])
		await _secs(3.5))
	print("LISTEN_RESULT ", JSON.stringify({"sections": _sections, "ambience": amb, "dir": out_dir}))
	quit(0)
