extends SceneTree
## Audit music stage: listening scenes for Daniel, recorded silently from the game's own mixer (headless, the
## Dummy audio driver; an AudioEffectRecord on Master; one recording per scene; nothing is played):
##   godot --headless --path godot -s res://tests/listen_music.gd -- --out=<dir>
## The cues themselves are godot/assets/audio/music_m*.wav. These scenes show the system: a crossfade, the
## stinger over a bed, the duck under a message, the title into a new game, and chapter 4 from "docked" to the
## first knock (the silence, then the stair cue). Run at normal priority (see tests/listen_d.gd).

var g: Node3D
var au: Node
var rec: AudioEffectRecord
var out_dir := "user://"
var _sections: Array = []


func _initialize() -> void:
	_run.call_deferred()


func _secs(s: float) -> void:
	await create_timer(s).timeout


func _section(name: String, body: Callable, tail := 1.5) -> void:
	await _secs(0.5)
	rec.set_recording_active(true)
	var a := Time.get_ticks_msec()
	await body.call()
	await _secs(tail)
	rec.set_recording_active(false)
	var w: AudioStreamWAV = rec.get_recording()
	var ok := w != null and w.save_to_wav(out_dir.path_join(name + ".wav")) == OK
	print("LISTEN %s wall %.2f recorded %.2f saved %s" % [name, (Time.get_ticks_msec() - a) / 1000.0, w.get_length() if w else 0.0, ok])
	_sections.append([name, ok])
	await _secs(1.0)


func _run() -> void:
	await process_frame
	Engine.max_fps = 60
	rec = AudioEffectRecord.new()
	AudioServer.add_bus_effect(0, rec)
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out_dir = a.substr(6)
	g = load("res://scripts/fp/game_fp.gd").new()
	root.add_child(g)
	g.start(5, "", false, true, {})
	await _secs(1.0)
	g.director.process_mode = Node.PROCESS_MODE_DISABLED
	au = g.audio
	for bus in ["Ambient", "Exterior"]:
		AudioServer.set_bus_mute(AudioServer.get_bus_index(bus), true)
	var msg := [false]
	au.message_probe = func(): return msg[0]
	await _secs(0.5)

	await _section("01_crossfade_arrival_to_watch", func():
		au.play_cue("M02", 0.0)
		await _secs(7.0)
		au.play_cue("M03", 3.0)
		await _secs(8.0))
	au.stop_cue(0.0)
	await _section("02_letter_stinger_over_ross", func():
		au.play_cue("M07", 0.0)
		await _secs(5.0)
		au.play_cue("M08")
		await _secs(16.0))
	au.stop_cue(0.0)
	await _section("03_duck_under_a_message", func():
		au.play_cue("M07", 0.0)
		await _secs(4.0)
		msg[0] = true                            # a line on screen: down 8 dB in 0.4 s
		await _secs(4.0)
		msg[0] = false                           # gone: back in 1.2 s
		await _secs(4.0))
	au.message_probe = g.message_on_screen
	au.stop_cue(0.0)
	await _section("04_title_into_new_game", func():
		au.set_menu(true)
		await _secs(6.0)
		au.set_menu(false, 2.6)
		await _secs(3.5))
	# the loop seams of Daniel's tracks: 8 s before the end of M07 and of M01, through the seam into the start
	await _section("06_loop_seams_ross_then_title", func():
		for id in ["M07", "M01"]:
			au.play_cue(id, 0.0)
			au._music.seek(maxf(0.0, au._music.stream.get_length() - 8.0))
			await _secs(14.0)
			au.stop_cue(0.0)
			await _secs(1.0))
	# chapter 4 as played, at real pace: the weather bed, "docked" (the silence), the jetty, the base door, the
	# cough, the first stair footstep (the stair cue), and the knock (it cuts)
	AudioServer.set_bus_mute(AudioServer.get_bus_index("Ambient"), false)
	AudioServer.set_bus_mute(AudioServer.get_bus_index("Exterior"), false)
	g.sim.storm_override = 0.6
	au.play_cue("M04", 0.0)
	await _secs(3.0)
	var dir: StoryDirector = g.director
	dir.bot = true
	dir.bot_wait_mul = 1.0
	dir.state.chapter = 4
	dir.state.flags["docked_Visitor"] = true
	dir.state.beat = dir.resolve_beat(4, "hail")
	dir._hold = 0
	dir._beat_done_pending = false
	dir._actions = []
	dir._wait = 0.0
	var knocked := [false]
	dir.story_event.connect(func(n, _a): if n == "knock": knocked[0] = true)
	await _section("05_ch4_docked_silence_stair_knock", func():
		dir.process_mode = Node.PROCESS_MODE_INHERIT
		dir._enter_beat()
		var t0 := Time.get_ticks_msec()
		while not knocked[0] and Time.get_ticks_msec() - t0 < 90000:
			await process_frame
		await _secs(4.0), 0.5)
	print("LISTEN_RESULT ", JSON.stringify({"sections": _sections, "dir": out_dir}))
	quit(0)
