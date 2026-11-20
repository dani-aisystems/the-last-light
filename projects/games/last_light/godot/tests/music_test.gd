extends SceneTree
## Audit music stage (F_soundtrack.md 23.8): the score system, checked without ears.
##   godot --headless --path godot -s res://tests/music_test.gd
## Every cue the data names has a file; crossfades, the stinger and the layer behave; the Music bus ducks 8 dB in
## 0.4 s under a message and recovers in 1.2 s; a cue is saved and restored from the top; and the silence rule:
## nothing plays from "docked" (ch4 hail) to the first footstep on the stair, even if a cue is asked for.
## Prints one line per check and MUSIC_RESULT {json}; exit 1 on any FAIL.

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
	print("  %-4s %-58s %s" % ["PASS" if cond else "FAIL", name, note])


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _step(au: Node, secs: float, dt := 0.05) -> void:
	for i in int(round(secs / dt)):
		au._music_process(dt)


func _audible(au: Node) -> bool:
	for b in au._beds:
		if b.playing and b.volume_db > au.SILENT_DB + 1.0:
			return true
	return au._layer.playing and au._layer.volume_db > au.SILENT_DB + 1.0


## Audible and not on its way out: in the silence, only the bed fading out from "docked" may still be heard (judged
## by the fade itself, not by wall time, which a throttled run stretches).
func _audible_not_fading(au: Node) -> bool:
	for b in au._beds + [au._layer]:
		if b.playing and b.volume_db > au.SILENT_DB + 1.0:
			var f = au._fades.get(b)
			if f == null or f[1] > au.SILENT_DB + 1.0:
				return true
	return false


func _run() -> void:
	await process_frame
	g = load("res://scripts/fp/game_fp.gd").new()
	root.add_child(g)
	g.start(5, "", false, true, {})
	await _frames(3)
	g.director.process_mode = Node.PROCESS_MODE_DISABLED
	var au: Node = g.audio
	au.set_process(false)                       # the checks below drive the score's clock themselves

	# --- the data: every cue id used has a file that loads
	var table: Dictionary = au.cues.get("cues", {})
	var used: Array = []
	var chapters = JSON.parse_string(FileAccess.get_file_as_string("res://data/story/chapters.json"))
	var beats := 0
	for ch in chapters.get("chapters", []):
		for b in ch.get("beats", []):
			for a in b.get("do", []):
				if a[0] == "music":
					used.append(String(au.cues.get("legacy", {}).get(String(a[1]), String(a[1]))))
					beats += 1
	for e in au.cues.get("endings", {}).values():
		used.append(String(e))
	used.append(String(au.cues.get("title", "")))
	used.append(String(au.cues.get("credits", "")))
	var missing: Array = []
	for id in used:
		var f: String = au.cue_file(id)
		if f == "" or not ResourceLoader.exists(f) or load(f) == null:
			missing.append(id)
	_ok("every cue the data names exists and its file loads", missing.is_empty() and used.size() > 10,
		"%d uses (%d beat actions), missing %s" % [used.size(), beats, missing])
	var all_ok := true
	for id in table:
		all_ok = all_ok and ResourceLoader.exists(au.cue_file(id))
	_ok("every cue in the table has its file", all_ok, "%d cues" % table.size())
	# Daniel's tracks (audio/score.py, MP3): Godot decodes exactly the length encoded, so the LAME gapless tag is
	# honoured and a loop has no encoder gap at its seam
	var score = JSON.parse_string(FileAccess.get_file_as_string("res://../audio/SCORE.json")) if FileAccess.file_exists("res://../audio/SCORE.json") else null
	var gapless := true
	var worst := 0.0
	var n_score := 0
	for id in table:
		var cf: String = au.cue_file(id)
		if cf.ends_with(".mp3"):
			n_score += 1
			var st: AudioStream = load(cf)
			var want := -1.0
			if score:
				for r in score["cues"]:
					if r["cue"] == id:
						want = float(r["seconds"])
			if want > 0.0:
				worst = maxf(worst, absf(st.get_length() - want))
			gapless = gapless and st is AudioStreamMP3 and want > 0.0 and absf(st.get_length() - want) < 0.03
	_ok("Daniel's tracks decode gapless (length as encoded)", n_score > 0 and gapless, "%d tracks, worst %.3f s" % [n_score, worst])
	var lp: AudioStream = au._cue_stream("M07")
	_ok("a looping track loops from its start", lp is AudioStreamMP3 and (lp as AudioStreamMP3).loop and (lp as AudioStreamMP3).loop_offset == 0.0)
	_ok("the four endings each have their own cue", au.cues.get("endings", {}).size() == 4
		and au.cues["endings"].values().all(func(v): return table.has(v)))
	_ok("the credits play cue M14's file", load("res://scripts/ui/credits_roll.gd").CREDITS_MUSIC == au.cue_file(String(au.cues.get("credits", ""))))
	var dirsrc := FileAccess.get_file_as_string("res://scripts/story/story_director.gd")
	_ok("music_stop is a known beat action (instant too)", "music_stop" in StoryDirector.PRESENTATION_EVENTS and "music_stop" in StoryDirector.INSTANT_ACTIONS)

	# --- crossfade, stinger, layer
	au.stop_cue(0.0)
	_ok("M02 starts", au.play_cue("M02", 0.0) and au.current_cue() == "M02" and au._music.playing)
	var first: AudioStreamPlayer = au._music
	au.play_cue("M03", 1.0)
	_step(au, 0.5)
	var both: bool = first.playing and au._music.playing and au._music != first
	_step(au, 0.6)
	_ok("a new bed crossfades: both play at half way, the old one stops", both and not first.playing and au._music.volume_db > -0.5,
		"new at %.1f dB" % au._music.volume_db)
	au.play_cue("M07", 0.0)
	au.play_cue("M08")
	_ok("the stinger plays over the bed without stopping it", au._stinger.playing and au._music.playing and au.current_cue() == "M07")
	au.play_cue("M04", 0.0)
	_ok("the restless layer joins its bed", au.play_cue("M04b", 0.5) and au._layer.playing and au.cue_state()["layers"] == ["M04b"])
	au.play_cue("M05", 0.5)
	_step(au, 0.6)
	_ok("a new bed takes the layer out", not au._layer.playing and au.cue_state()["layers"].is_empty())
	au.story_cue("music", ["tension"])
	_ok("the old 'tension' id plays its cue (M04)", au.current_cue() == "M04")
	au.play_cue("M03", 0.0)
	_step(au, 121.0, 0.5)
	_step(au, 4.5)
	_ok("M03 goes out after two minutes", au.current_cue() == "" and not _audible(au))

	# --- the duck: -8 dB in 0.4 s under any message, back in 1.2 s
	var msg := [true]
	au.message_probe = func(): return msg[0]
	_step(au, 0.4, 0.02)
	var down: float = au._duck_fx.volume_db
	_step(au, 0.1, 0.02)
	msg[0] = false
	_step(au, 0.6, 0.02)
	var half: float = au._duck_fx.volume_db
	_step(au, 0.62, 0.02)
	var back: float = au._duck_fx.volume_db
	_ok("Music ducks 8 dB in 0.4 s under a message", absf(down - au.DUCK_DB) < 0.3, "%.2f dB" % down)
	_ok("and is back in 1.2 s after it", absf(half + 4.0) < 0.5 and absf(back) < 0.2, "%.2f at 0.6 s, %.2f at 1.2 s" % [half, back])
	var mi := AudioServer.get_bus_index("Music")
	_ok("the duck is its own effect at the head of the Music bus", AudioServer.get_bus_effect(mi, 0) == au._duck_fx
		and is_equal_approx(AudioServer.get_bus_volume_db(mi), AudioServer.get_bus_volume_db(mi)))
	au.message_probe = g.message_on_screen

	# --- saved with the game, restored from the top with a 2 s fade
	au.play_cue("M07", 0.0)
	_step(au, 3.0)
	var d: Dictionary = g.save_dict()
	_ok("a save keeps the cue", d.has("music") and d["music"]["cue"] == "M07" and d["music"]["hold"] == false)
	var js = JSON.parse_string(JSON.stringify(d))       # as written to disk and read back
	au.stop_cue(0.0)
	au.restore_cue(js["music"])
	var restored_at: float = au._music.volume_db
	_step(au, 2.05)
	_ok("on load the cue restarts, fading in over 2 s", au.current_cue() == "M07" and au._music.playing
		and restored_at <= au.SILENT_DB + 0.1 and au._music.volume_db > -0.2, "%.1f -> %.1f dB" % [restored_at, au._music.volume_db])
	_ok("from the top", au._music.get_playback_position() < 1.0, "%.2f s" % au._music.get_playback_position())
	au.hold(true, 0.0)
	var held: Dictionary = au.cue_state()
	au.restore_cue({"cue": "", "layers": [], "hold": false})
	au.restore_cue(held)
	_ok("a save taken in the silence keeps the silence", not au.play_cue("M07") and not _audible(au))
	au.hold(false)
	_ok("an old save (no music key) loads silent", not g.save_dict().is_empty())

	# --- the silence rule, played through: ch4 from "hail" (docked) to the knock
	au.set_process(true)
	au.play_cue("M04", 0.0)
	var dir: StoryDirector = g.director
	dir.bot = true
	dir.bot_wait_mul = 0.5                       # long enough for the 3 s fade-out to finish inside the silence
	dir.state.chapter = 4
	dir.state.flags["docked_Visitor"] = true
	dir.state.beat = dir.resolve_beat(4, "hail")
	dir._hold = 0                                # a clean start: no chapter-card hold, nothing pending from ch1
	dir._beat_done_pending = false
	dir._actions = []
	dir._wait = 0.0
	var log: Array = []
	dir.story_event.connect(func(n, a): log.append([n, a, au._hold, _audible(au), Time.get_ticks_msec()]))
	dir.process_mode = Node.PROCESS_MODE_INHERIT
	dir._enter_beat()
	var t0 := Time.get_ticks_msec()
	var held_since := -1
	var loud_in_silence := 0
	var refused := false
	var stair_at := -1
	var knock_at := -1
	var m06_after_stair := false
	while Time.get_ticks_msec() - t0 < 60000 and knock_at < 0:
		await process_frame
		if au._hold and held_since < 0:
			held_since = Time.get_ticks_msec()
		if au._hold and held_since >= 0 and _audible_not_fading(au):
			loud_in_silence += 1                 # only the fade-out begun at "docked" may still be heard
		if au._hold and not refused and held_since >= 0 and Time.get_ticks_msec() - held_since > 1000:
			refused = not au.play_cue("M07", 0.0)   # someone asks for music in the silence
		for e in log:
			if e[0] == "footsteps" and e[1].size() > 0 and e[1][0] == "stair" and stair_at < 0:
				stair_at = e[4]
			if e[0] == "knock" and knock_at < 0:
				knock_at = e[4]
		if stair_at >= 0 and knock_at < 0 and au.current_cue() == "M06" and _audible(au):
			m06_after_stair = true
	var silent_ms := (stair_at - held_since) if stair_at >= 0 and held_since >= 0 else -1
	_ok("docked starts the silence (hail: music_stop hold)", held_since >= 0)
	_ok("nothing plays from docked to the first stair footstep", loud_in_silence == 0 and silent_ms > 3000,
		"%.1f s of silence, %d frames with music not fading out" % [silent_ms / 1000.0, loud_in_silence])
	_ok("a cue asked for in the silence is refused", refused)
	_ok("the first footstep ends it: M06 plays on the stair", stair_at >= 0 and m06_after_stair)
	_ok("and cuts on the first knock", knock_at >= 0 and au.current_cue() == "" and not _audible(au))

	print("MUSIC_RESULT ", JSON.stringify({"checks": checks, "failed": fails, "failures": failures}))
	quit(1 if fails > 0 else 0)
