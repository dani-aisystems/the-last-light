extends SceneTree
## Audit Stage A (2026-11-16): old saves keep working.
## Every version-1 fixture in tests/fixtures/saves_v1 (recorded by make_save_fixtures.gd before any story
## change) must:
##   S1 migrate to the current save version;
##   S2 load onto the beat it was saved at: the same beat id, or the beat its id is now aliased to;
##   S3 resume with a NEW conversation (never one it had already played) or finish the campaign;
##   S4 (one per chapter and door path, all with --full) play on to an ending; a door-shut save keeps the
##      door shut.
## Plus: S5 a v2 save names its beat and round-trips; S6 aliases and backfill; S7 SaveSystem.read migrates
## a v1 file, backs it up once, and refuses a newer build's save.
##   godot --headless --path godot -s res://tests/save_compat_test.gd [-- --full]

const FIXTURES := "res://tests/fixtures/saves_v1"
const SAVE_SYSTEM := preload("res://scripts/save_system.gd")
const PLAYER_FLAGS := ["moved", "looked", "used_battery", "read_log_1971", "read_log_1953", "read_letter", "at_door"]
var fails: Array[String] = []
var passed := 0
var lay: LayoutData


func _initialize() -> void:
	_run.call_deferred()


func _check(ok: bool, what: String) -> void:
	if ok:
		passed += 1
	else:
		fails.append(what)
		print("  FAIL ", what)


func _run() -> void:
	lay = LayoutData.load_file()
	var full := "--full" in OS.get_cmdline_user_args()
	var files := Array(DirAccess.get_files_at(FIXTURES)).filter(func(f): return f.ends_with(".json"))
	files.sort()
	_check(files.size() >= 60, "S0 the v1 fixture set is there (%d files)" % files.size())
	var played := {}
	for f in files:
		var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURES.path_join(f)))
		var fx: Dictionary = raw["fixture"]
		var key := "%s:%d" % [fx["path"], int(fx["chapter"])]
		var to_end := full or not played.has(key)
		played[key] = true
		await _one(f, raw, fx, to_end)
	_roundtrip(files)
	_aliases_backfill(files)
	_file_migration(files)
	print("SAVE_COMPAT_RESULT ", JSON.stringify({"passed": passed, "failed": fails.size(), "failures": fails}))
	quit(1 if not fails.is_empty() else 0)


func _load(raw: Dictionary) -> Array:
	var d: Dictionary = SAVE_SYSTEM.migrate(raw.duplicate(true))
	var k := KeeperSim.new()
	k.setup(KeeperConfig.new(), lay, {"ships": [], "faults": []}, 11)
	k.story_mode = true
	k.from_dict(d["sim"])
	var dir := StoryDirector.new()
	root.add_child(dir)
	dir.setup(k, true)
	dir.load_data(d["story"])
	dir.story_event.connect(func(n, a): if n == "sim_events": dir.on_sim_events(a[0]))
	return [d, k, dir]


func _one(f: String, raw: Dictionary, fx: Dictionary, to_end: bool) -> void:
	var r := await _resume(f, raw, fx, to_end)
	print("  %s -> %s" % [f, r])


func _resume(f: String, raw: Dictionary, fx: Dictionary, to_end: bool) -> String:
	var t := _load(raw)
	var d: Dictionary = t[0]
	var k: KeeperSim = t[1]
	var dir: StoryDirector = t[2]
	_check(int(d["version"]) == SAVE_SYSTEM.VERSION, "S1 %s migrates to v%d" % [f, SAVE_SYSTEM.VERSION])
	var want_i := dir.resolve_beat(int(fx["chapter"]), String(fx["beat_id"]))
	var want := String(dir.chapter_data(int(fx["chapter"]))["beats"][want_i]["id"]) if want_i >= 0 else "(gone)"
	_check(dir.state.chapter == int(fx["chapter"]) and dir.beat_id() == want and want_i >= 0,
		"S2 %s loads onto ch%d '%s' (got ch%d '%s')" % [f, int(fx["chapter"]), want, dir.state.chapter, dir.beat_id()])
	var done: Dictionary = dir.state.convs_done.duplicate()
	var first := [""]
	dir.line_shown.connect(func(_i): if first[0] == "": first[0] = String(dir.runner.conv.get("id", "")))
	var ended := [false, {}]
	dir.campaign_finished.connect(func(e): ended[0] = true; ended[1] = e)
	var prefs: Dictionary = {"ch4_door": "Keep the door shut", "ch6_jam": "Stay where you are"} if fx["path"] == "door_shut" else {}
	dir.bot_pick_fn = func(conv: String, choices: Array) -> int:
		if prefs.has(conv):
			for c in choices:
				if String(prefs[conv]) in String(c["text"]):
					return int(c["index"])
		return 0
	dir.begin(false)
	var bot := KeeperBot2.new("expert", 1)
	var dt := 1.0 / 30.0
	var g := 0.0
	var limit := 6000.0 if to_end else 400.0
	while not ended[0] and g < limit and (to_end or first[0] == ""):
		g += dt
		for fl in PLAYER_FLAGS:
			if dir.state.has_objective():
				dir.state.flags[fl] = 1
		var ev := bot.act(k, dt) + k.step(dt)
		dir.on_sim_events(ev)
		dir._process(dt)
		if int(g / dt) % 60 == 0:
			await process_frame
	_check(first[0] != "" or ended[0], "S3 %s resumes (a conversation or the ending within %.0f s)" % [f, g])
	_check(first[0] == "" or not done.has(first[0]), "S3 %s does not replay '%s'" % [f, first[0]])
	var out := "next %s" % first[0]
	if to_end:
		_check(ended[0], "S4 %s plays on to an ending (stuck at ch%d beat %d)" % [f, dir.state.chapter, dir.state.beat])
		if fx["path"] == "door_shut":
			_check(not dir.state.has_flag("door_open"), "S4 %s keeps the door shut" % f)
		out += ", ending %s" % ended[1].get("ending", "-")
	dir.queue_free()
	await process_frame
	return out


func _roundtrip(files: Array) -> void:
	var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURES.path_join(files[files.size() / 2])))
	var t := _load(raw)
	var dir: StoryDirector = t[2]
	var sd := dir.save_data()
	_check(String(sd.get("beat_id", "")) == dir.beat_id() and dir.beat_id() != "", "S5 a v2 save names its beat ('%s')" % sd.get("beat_id", ""))
	var d2: Dictionary = JSON.parse_string(JSON.stringify({"story": sd}))
	var t2 := _load({"story": d2["story"], "sim": t[1].to_dict(), "version": SAVE_SYSTEM.VERSION})
	_check(t2[2].state.beat == dir.state.beat and t2[2].beat_id() == dir.beat_id(), "S5 the v2 save loads back onto '%s'" % dir.beat_id())
	# a v2 save is placed by id even when its index is wrong (the layout moved under it)
	sd["beat"] = 0
	var t3 := _load({"story": sd, "sim": t[1].to_dict(), "version": SAVE_SYSTEM.VERSION})
	_check(t3[2].beat_id() == dir.beat_id(), "S5 the id wins over a stale index ('%s')" % t3[2].beat_id())
	for x in [t, t2, t3]:
		x[2].queue_free()


func _aliases_backfill(files: Array) -> void:
	var late := ""
	var early := ""
	for f in files:
		if "_ch1_" in f and f.ends_with("_late.json"):
			late = f
		if "_ch1_b00_" in f:
			early = f
	var raw_late: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURES.path_join(late)))
	var raw_early: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURES.path_join(early)))
	var t := _load(raw_late)
	var dir: StoryDirector = t[2]
	var late_i := dir.state.beat
	dir.beat_aliases = {"1:old_late": "late", "1:older_late": "old_late"}
	_check(dir.resolve_beat(1, "old_late") == late_i and dir.resolve_beat(1, "older_late") == late_i,
		"S6 an alias (and an alias of an alias) finds the renamed beat")
	_check(dir.resolve_beat(1, "no_such_beat") == -1, "S6 an unknown beat id resolves to -1")
	var story: Dictionary = raw_late["story"].duplicate(true)
	story["beat_id"] = "old_late"
	story["beat"] = 0
	dir.load_data(story)
	_check(dir.beat_id() == "late", "S6 a save naming a renamed beat loads onto its new id ('%s')" % dir.beat_id())
	dir.backfill = [{"chapter": 1, "from_beat": "late", "set": {"test_backfill": 1}}]
	dir.load_data(raw_late["story"])
	_check(dir.state.has_flag("test_backfill"), "S6 backfill sets a new flag for a save past its beat")
	dir.load_data(raw_early["story"])
	_check(not dir.state.has_flag("test_backfill"), "S6 ... and not for a save before it")
	dir.queue_free()


func _file_migration(files: Array) -> void:
	var ss: Node = SAVE_SYSTEM.new()
	ss._ready()                                          # -s run: the test folder, never the player's
	_check(ss.dir == ss.TEST_DIR, "S7 the migration check runs in %s" % ss.TEST_DIR)
	var src := FileAccess.get_file_as_string(FIXTURES.path_join(files[0]))
	var f := FileAccess.open(ss.path("2"), FileAccess.WRITE)
	f.store_string(src)
	f.close()
	var backup: String = ss.dir.path_join("slot_2_v1_backup.json")
	if FileAccess.file_exists(backup):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(backup))
	var d: Dictionary = ss.read("2")
	_check(int(d.get("version", 0)) == SAVE_SYSTEM.VERSION and int(d.get("migrated_from", 0)) == 1 and not d.has("corrupt"),
		"S7 SaveSystem.read migrates a v1 file (%s)" % [d.get("version", "?")])
	_check(FileAccess.file_exists(backup) and FileAccess.get_file_as_string(backup) == src, "S7 the v1 file is backed up unchanged")
	var newer: Dictionary = JSON.parse_string(src)
	newer["version"] = SAVE_SYSTEM.VERSION + 1
	f = FileAccess.open(ss.path("2"), FileAccess.WRITE)
	f.store_string(JSON.stringify(newer))
	f.close()
	_check(ss.read("2").has("corrupt"), "S7 a save from a newer build is refused, not misread")
	ss.delete("2")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(backup))
	ss.free()
