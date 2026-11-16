extends SceneTree
## Audit Stage A (2026-11-16): records version-1 saves at every autosave point of two full campaigns
## (door opened, door kept shut), BEFORE any chapters.json or .dlg change, so save_compat_test.gd can prove
## that every old save still loads onto the right beat after the story layout moves.
## Each file is what the game writes (SaveSystem.write: story, sim, chapter_title, clock, version 1) plus a
## "fixture" block with the beat id and chapter at the moment of saving.
##   godot --headless --path godot -s res://tests/make_save_fixtures.gd
## One-off: re-run only to add fixtures of a NEW layout; never overwrite the v1 set.

const OUT := "res://tests/fixtures/saves_v1"
## "from_chapter": the door-shut game is the same as the other until chapter 4, so only its own saves are kept.
const PATHS := [
	{"name": "door_open", "policy": 0, "prefs": {}, "from_chapter": 1},
	{"name": "door_shut", "policy": 0, "prefs": {"ch4_door": "Keep the door shut", "ch6_jam": "Stay where you are"}, "from_chapter": 4},
]
var written := 0
var fails: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var abs_out := ProjectSettings.globalize_path(OUT)
	if DirAccess.dir_exists_absolute(abs_out) and not DirAccess.get_files_at(abs_out).is_empty():
		print("FIXTURES_RESULT ", JSON.stringify({"written": 0, "failures": ["%s already holds fixtures; not overwriting" % OUT]}))
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(abs_out)
	for p in PATHS:
		await _record(p)
	print("FIXTURES_RESULT ", JSON.stringify({"written": written, "failures": fails}))
	quit(1 if not fails.is_empty() else 0)


func _record(p: Dictionary) -> void:
	var k := KeeperSim.new()
	k.setup(KeeperConfig.new(), LayoutData.load_file(), {"ships": [], "faults": []}, 11)
	k.story_mode = true
	var dir := StoryDirector.new()
	root.add_child(dir)
	dir.setup(k, true)
	dir.bot_choice = int(p["policy"])
	var prefs: Dictionary = p["prefs"]
	dir.bot_pick_fn = func(conv: String, choices: Array) -> int:
		if prefs.has(conv):
			for c in choices:
				if String(prefs[conv]) in String(c["text"]):
					return int(c["index"])
		return 0
	var seen := {}
	var snap := func(kind: String) -> void:
		if not dir.can_autosave() or dir.state.chapter < int(p["from_chapter"]):
			return
		var key := "%d:%d:%s" % [dir.state.chapter, dir.state.beat, dir.state.in_beat]   # one per place
		if seen.has(key):
			return
		seen[key] = true
		var c: Dictionary = dir.chapter_data(dir.state.chapter)
		var d := {"story": dir.state.to_dict(), "sim": k.to_dict(), "chapter_title": c.get("title", ""),
			"clock": k.clock_text(), "version": 1,
			"station": {"door_open": dir.state.has_flag("door_open"), "visitor": dir.state.has_flag("door_open")},
			"fixture": {"path": p["name"], "chapter": dir.state.chapter, "beat": dir.state.beat, "beat_id": dir.beat_id(),
				"in_beat": dir.state.in_beat, "kind": kind}}
		var fname := "%s_%02d_ch%d_b%02d_%s%s.json" % [p["name"], seen.size() - 1, dir.state.chapter, dir.state.beat,
			dir.beat_id(), "_in" if dir.state.in_beat else ""]
		var f := FileAccess.open(OUT.path_join(fname), FileAccess.WRITE)
		f.store_string(JSON.stringify(d))
		f.close()
		written += 1
	dir.beat_autosave.connect(func(): snap.call("beat"))
	dir.request_autosave.connect(func(): snap.call("action"))
	dir.story_event.connect(func(n, a): if n == "sim_events": dir.on_sim_events(a[0]))
	var ended := [false]
	dir.campaign_finished.connect(func(_e): ended[0] = true)
	dir.begin(true)
	var bot := KeeperBot2.new("expert", 1)
	var dt := 1.0 / 30.0
	var guard := 0.0
	while not ended[0] and guard < 6000.0:
		guard += dt
		for f in ["moved", "looked", "used_battery", "read_log_1971", "read_log_1953", "read_letter", "at_door"]:
			if dir.state.has_objective() and guard > 2.0:
				dir.state.flags[f] = 1
		var ev := bot.act(k, dt) + k.step(dt)
		dir.on_sim_events(ev)
		dir._process(dt)
		if int(guard / dt) % 30 == 0:
			await process_frame
	if not ended[0]:
		fails.append("%s: campaign stuck in chapter %d beat %d" % [p["name"], dir.state.chapter, dir.state.beat])
	print("PATH %s ended=%s fixtures=%d" % [p["name"], ended[0], seen.size()])
	dir.queue_free()
	await process_frame
