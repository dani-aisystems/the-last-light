extends SceneTree
## Audit Stage D (docs/last_light/audit-2026-11/18_stageD_audio.md): the 18.4 actions, checked without ears.
##   godot --headless --path godot -s res://tests/audio_d_test.gd
## The stairwell (Stair bus: reverb, then the steel door's low-pass that follows the door's swing), the room
## reverb on SFX, the static's dip under a radio message, paper on opening and closing a document, and the
## title pad's fade on New Game. Whether it SOUNDS right is Daniel's call (listening files in renders/).
## Prints one line per check and AUDIOD_RESULT {json}; exit 1 on any FAIL.

var g: Node3D
var fails := 0
var checks := 0
var failures: Array = []


func _initialize() -> void:
	_run.call_deferred()


func _ok(name: String, cond: bool, note := "") -> void:
	checks += 1
	if not cond:
		fails += 1
		failures.append(name)
	print("  %-4s %-46s %s" % ["PASS" if cond else "FAIL", name, note])


func _ok_silent(cond: bool) -> void:
	if not cond:
		fails += 1
		failures.append("silent check")


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
	g = load("res://scripts/fp/game_fp.gd").new()
	root.add_child(g)
	g.start(3, "", false, true, {})
	await _frames(3)
	g.director.process_mode = Node.PROCESS_MODE_DISABLED
	var au: Node = g.audio

	# --- the stairwell and the door
	var si := AudioServer.get_bus_index(au.STAIR_BUS)
	_ok("Stair bus exists", si != -1)
	_ok("Stair sends to SFX", si != -1 and AudioServer.get_bus_send(si) == &"SFX")
	_ok("Stair: stairwell reverb first", si != -1 and AudioServer.get_bus_effect(si, 0) is AudioEffectReverb)
	_ok("Stair: door low-pass after it", si != -1 and AudioServer.get_bus_effect(si, 1) is AudioEffectLowPassFilter)
	var sfx_i := AudioServer.get_bus_index("SFX")
	var rooms := 0
	for k in AudioServer.get_bus_effect_count(sfx_i):
		if AudioServer.get_bus_effect(sfx_i, k) is AudioEffectReverb:
			rooms += 1
	au._ensure_room_reverb()                    # a second setup (the menu game has its own director) adds nothing
	var rooms2 := 0
	for k in AudioServer.get_bus_effect_count(sfx_i):
		if AudioServer.get_bus_effect(sfx_i, k) is AudioEffectReverb:
			rooms2 += 1
	_ok("one room reverb on SFX, added once", rooms == 1 and rooms2 == 1, "%d, %d" % [rooms, rooms2])
	var rv: AudioEffectReverb = AudioServer.get_bus_effect(sfx_i, 0) if rooms == 1 else null
	_ok("room reverb is light", rv != null and rv.wet <= 0.15 and rv.dry == 1.0, "wet %.2f" % (rv.wet if rv else -1.0))
	_ok("door cutoff: shut 700 Hz, open 8 kHz", is_equal_approx(au.door_cutoff(0.0), au.DOOR_SHUT_HZ) and is_equal_approx(au.door_cutoff(1.0), au.DOOR_OPEN_HZ))
	g.station.door_open = false
	g.station.snap_door()
	for i in 60:
		au._process(0.05)
	var shut_hz: float = au._stair_lp.cutoff_hz
	g.station.door_open = true
	g.station.snap_door()
	for i in 60:
		au._process(0.05)
	var open_hz: float = au._stair_lp.cutoff_hz
	g.station.door_open = false
	g.station.snap_door()
	_ok("the door's low-pass follows its swing", shut_hz < 900.0 and open_hz > 7000.0, "shut %.0f Hz, open %.0f Hz" % [shut_hz, open_hz])
	au.footsteps("stair", g.station.door_position())
	au.footsteps("base_door", g.station.door_position())
	for i in 300:
		au._process(0.05)
	var steps := []
	for k in au.STEPS_STAIR:
		steps += _players("step_stair_%d" % k)
	var base: Array = _players("door_base")
	_ok("stair steps play through the Stair bus", steps.size() > 0 and steps.all(func(p): return p.bus == &"Stair"), "%d players" % steps.size())
	_ok("the base door plays through the Stair bus", base.size() > 0 and base[0].bus == &"Stair")
	au.sfx_at("knock", Vector3(0, 21, 0), 0.0, 3.0, "Stair")
	var kn: Array = _players("knock")
	_ok("sfx_at takes a bus", kn.size() > 0 and kn[-1].bus == &"Stair")

	# --- the static's dip under a radio message
	var full: float = au.static_db(1.0, 0.5, 0.0, true)
	var dipped: float = au.static_db(1.0, 0.5, 1.0, true)
	_ok("static: -6 dB under a message", is_equal_approx(full - dipped, 6.0), "%.1f -> %.1f dB" % [full, dipped])
	_ok("static: silent with the radio dead", au.static_db(1.0, 0.5, 0.0, false) <= -80.0)
	var msg := [false]
	au.radio_probe = func(): return msg[0]
	g.sim.storm_override = 0.5
	g.sim.main_breaker = true                   # the radio needs power (a fresh game starts with it off)
	g.sim.battery = maxf(g.sim.battery, 50.0)
	au._static_t = 5.0
	for i in 10:
		au._process(0.05)
	var before: float = au.loops["static"].volume_db
	msg[0] = true
	au._static_t = 5.0
	for i in 10:
		au._process(0.05)
	var under: float = au.loops["static"].volume_db
	_ok("static dips while a radio message shows", g.sim.radio_on() and absf((before - under) - 6.0) < 0.6, "%.1f -> %.1f dB (radio %s)" % [before, under, g.sim.radio_on()])
	msg[0] = false
	au._static_t = 5.0
	for i in 10:
		au._process(0.05)
	_ok("and comes back after it", absf(au.loops["static"].volume_db - before) < 0.6, "%.1f dB" % au.loops["static"].volume_db)
	au.radio_probe = g.radio_message_on_screen
	_ok("no message on screen at rest", not g.message_on_screen() and not g.radio_message_on_screen())
	g.ui.add_subtitle("Kittiwake", "Test, over.", false)
	_ok("a radio subtitle is a radio message", g.radio_message_on_screen() and g.message_on_screen())
	g.presenter.show_caption("[Footsteps on the stair]")
	await _frames(30)
	_ok("a caption counts as a message", g.presenter.is_caption_visible())

	# --- paper in the hands
	var docs: Array = g.presenter.BUILTIN_DOCS.keys()
	var doc: String = docs[0] if docs.size() > 0 else "log_1953"
	var n0 := _players("paper_slide").size()
	g.presenter.open_document(doc)
	await _frames(2)
	_ok("paper_slide as a document opens", g.presenter.is_document_open() and _players("paper_slide").size() > n0, doc)
	var c0 := _players("paper_close").size()
	g.presenter.close_document()
	await _frames(2)
	_ok("paper_close as it closes", _players("paper_close").size() > c0)
	_ok("paper_close is the softer of the two", load("res://assets/audio/paper_close.wav").get_length() < load("res://assets/audio/paper_slide.wav").get_length())

	# --- the title pad fades on New Game (from where it is, over the camera move)
	au.set_menu(true)
	au._music.volume_db = -14.0
	au.set_menu(false, 2.6)
	for i in 13:
		au._process(0.1)
	var mid: float = au._music.volume_db
	for i in 15:
		au._process(0.1)
	_ok("set_menu(false) fades from its level over fade_s", mid > -45.0 and mid < -20.0 and not au._music.playing, "%.1f dB at half way" % mid)
	var src: String = FileAccess.get_file_as_string("res://scripts/main_fp.gd")
	_ok("main_fp fades the title pad as a game starts", src.contains("menu_bg.audio.set_menu(false"))

	# --- 7.8: Ross (recorded CC0), the handled objects, the keeper's own boots
	var prev := -1
	var repeats := 0
	for i in 200:
		var k: int = au.cough_take()
		if k == prev:
			repeats += 1
		_ok_silent(k >= 0 and k < au.COUGHS)
		prev = k
	_ok("Ross's cough never repeats a take (200 draws)", repeats == 0)
	var takes := {}
	for i in 200:
		takes[au.cough_take()] = true
	_ok("and uses all %d takes" % au.COUGHS, takes.size() == au.COUGHS, "%d" % takes.size())
	var cf0 := 0
	for k in au.COUGHS:
		cf0 += _players("ross_cough_%d" % k).size()
	au.story_cue("sfx", ["ross_cough"])
	for i in 120:
		au._process(0.05)
	var fit: Array = []
	for k in au.COUGHS:
		fit += _players("ross_cough_%d" % k)
	_ok("the stair cough is a fit, through the Stair bus", fit.size() - cf0 >= 3 and fit.all(func(p): return p.bus == &"Stair"), "%d coughs" % (fit.size() - cf0))
	au.on_line({"type": "line", "speaker": "", "line_kind": "sound", "text": "[He coughs. It goes on too long.]"})
	for i in 120:
		au._process(0.05)
	var fit2: Array = []
	for k in au.COUGHS:
		fit2 += _players("ross_cough_%d" % k)
	_ok("a stage direction that has him cough plays one", fit2.size() > fit.size())
	for cue in [["phone", "phone_lift"], ["drawer", "drawer_slide"], ["kettle", "kettle_boil"]]:
		au.call(cue[0])
		for i in 20:
			au._process(0.05)
		_ok("%s plays %s" % cue, _players(cue[1]).size() > 0)
	for i in 20:
		au._process(0.05)
	_ok("the phone's dead line follows the lift", _players("phone_dead").size() > 0)
	au.story_cue("sfx", ["teleprinter"])
	_ok("the teleprinter cue plays at the machine", _players("teleprinter").size() > 0 and _players("teleprinter")[0] is AudioStreamPlayer3D)
	au.on_events([{"type": "bowl_drained"}])
	_ok("draining the sediment bowl is heard", _players("bowl_drain").size() > 0)
	var walk := {"pos": Vector3(0.0, 20.0, 1.5), "walk": true}
	au.player_probe = func(): return walk
	var n_c := 0
	for k in au.STEPS_CONCRETE:
		n_c += _players("step_concrete_%d" % k).size()
	var dh := Vector3(g.station.door_position().x, 0.0, g.station.door_position().z).normalized()
	var across := Vector3(-dh.z, 0.0, dh.x)       # through the centre, square to the door: well off the landing
	for i in 40:                                 # 40 x 0.1 m = 3.9 m across the room
		walk["pos"] = across * (-1.95 + i * 0.1) + Vector3(0, 20.0, 0)
		au._keeper_steps()
	var n_c2 := 0
	for k in au.STEPS_CONCRETE:
		n_c2 += _players("step_concrete_%d" % k).size()
	_ok("the keeper's boots on the concrete: one step per stride", n_c2 - n_c >= 4 and n_c2 - n_c <= 6, "%d steps over 4 m" % (n_c2 - n_c))
	var dpos: Vector3 = g.station.door_position()
	var n_s := 0
	for k in au.STEPS_STAIR:
		n_s += _players("step_stair_%d" % k).size()
	for i in 12:
		walk["pos"] = Vector3(dpos.x + 0.3 + i * 0.07, 20.0, dpos.z)
		au._keeper_steps()
	var n_s2 := 0
	for k in au.STEPS_STAIR:
		n_s2 += _players("step_stair_%d" % k).size()
	_ok("on the chequer-plate landing: steel", n_s2 > n_s, "%d" % (n_s2 - n_s))
	au._stride = 0.0
	var before_tp := 0
	for k in au.STEPS_CONCRETE:
		before_tp += _players("step_concrete_%d" % k).size()
	walk["pos"] = Vector3(-2.5, 20.0, -2.0)      # a teleport (a load) is not a step
	au._keeper_steps()
	walk["pos"] = Vector3(-2.5, 20.0, -1.95)
	au._keeper_steps()
	var after_tp := 0
	for k in au.STEPS_CONCRETE:
		after_tp += _players("step_concrete_%d" % k).size()
	_ok("a teleport is not a step", after_tp == before_tp)
	walk["walk"] = false
	for i in 20:
		walk["pos"] = Vector3(i * 0.2, 20.0, 0.0)
		au._keeper_steps()
	var seated := 0
	for k in au.STEPS_CONCRETE:
		seated += _players("step_concrete_%d" % k).size()
	_ok("no steps out of free walk (seated, a device view)", seated == after_tp)

	print("AUDIOD_RESULT ", JSON.stringify({"checks": checks, "failed": fails, "failures": failures}))
	quit(1 if fails > 0 else 0)
