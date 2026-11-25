extends SceneTree
## Play-time helper (competition build tooling, does not touch the game).
## Runs the same story bot as tests/story_test.gd::_campaign, but with the scripted waits at FULL length
## (bot_wait_mul = 1.0; story_test compresses them to 2 %) and every dialogue line held for the time the
## real dialogue UI would hold it (the formula of scripts/ui/dialogue_ui.gd: line_read_s, typing time with
## punctuation pauses + 1.2 s, pages of at most 3 lines). A reply is held for --choice seconds (reading
## the options, picking one at the radio). Ships sail, the generator runs and scripted waits elapse WHILE
## lines are on screen, so concurrent text / animation / sim is not counted twice.
##   godot --headless --path godot -s /abs/path/realtime_campaign.gd -- --route=truth_saved --choice=8 --mul=1.0
## Routes: truth_saved, lie_saved, truth_lost, lie_lost (same reply preferences as story_test SCENARIOS).
## Not modelled: human walking time, replies' decision time (added in the Python model).

const ROUTES := {
	"truth_saved": {"prefs": {}, "idle_at": ""},
	"lie_saved": {"prefs": {"ch6_morag_dawn": "Nothing to report"}, "idle_at": ""},
	"truth_lost": {"prefs": {}, "idle_at": "iona"},
	"lie_lost": {"prefs": {"ch6_morag_dawn": "Nothing to report"}, "idle_at": "iona"},
}


# --- the dialogue UI's constants (scripts/ui/dialogue_ui.gd) ---
const CPS := 42.0
const BASE := 1.0
const PER_CHAR := 0.06
const MIN_S := 2.8
const MAX_S := 12.0
const AFTER_SHOWN := 1.2
const SPEAKER_CHANGE := 0.7
const FULL_STOP := 0.4
const RADIO_PAGE_CHARS := 150          # about 3 lines of 25 px serif in the radio column (approximation)
const OTHER_PAGE_CHARS := 285          # about 3 lines of 28 px serif in the 1280 px subtitle column
var reading_mul := 1.0
var _prev := ""
var n_lines := 0
var n_chars := 0
var line_total := 0.0
var n_picks := 0


func _page_s(text: String, changed: bool) -> float:
	var read := clampf(BASE + PER_CHAR * text.length(), MIN_S, MAX_S)
	if changed:
		read += SPEAKER_CHANGE
	if text.strip_edges().ends_with("."):
		read += FULL_STOP
	read *= reading_mul
	var typing := 0.15 + text.length() / CPS
	for ch in text:
		if ch in ".!?":
			typing += 0.32
		elif ch in ",;:":
			typing += 0.14
		elif ch == "-" or ch == "…":
			typing += 0.2
	return maxf(read, typing + AFTER_SHOWN)


func _pages(text: String, cap: int) -> Array:
	# whole sentences packed up to `cap` characters (the UI packs by measured line count)
	var out: Array = []
	var cur := ""
	for piece in text.replace("? ", "?|").replace(". ", ".|").replace("! ", "!|").split("|"):
		if cur != "" and (cur + " " + piece).length() > cap:
			out.append(cur)
			cur = piece
		else:
			cur = piece if cur == "" else cur + " " + piece
	if cur != "":
		out.append(cur)
	return out


func _on_line(dir, item: Dictionary) -> void:
	var text := String(item.get("text", ""))
	var look := String(item.get("look", "radio"))
	var cap := RADIO_PAGE_CHARS if look == "radio" else OTHER_PAGE_CHARS
	var spk := String(item.get("speaker", ""))
	var changed := _prev != "" and _prev != spk
	_prev = spk
	var total := 0.0
	var first := true
	for pg in _pages(text, cap):
		total += _page_s(String(pg), changed and first)
		first = false
	n_lines += 1
	n_chars += text.length()
	line_total += total
	dir._line_timer = total


func _initialize() -> void:
	_run.call_deferred()


func _arg(name: String, default: String) -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--%s=" % name):
			return a.substr(name.length() + 3)
	return default


func _run() -> void:
	var choice_s := float(_arg("choice", "8.0"))
	reading_mul = float(_arg("mul", "1.0"))
	var route_id := _arg("route", "truth_saved")
	var sc: Dictionary = ROUTES[route_id]
	var k := KeeperSim.new()
	k.setup(KeeperConfig.new(), LayoutData.load_file(), {"ships": [], "faults": []}, int(_arg("seed", "11")))
	k.story_mode = true
	var dir := StoryDirector.new()
	root.add_child(dir)
	dir.setup(k, true)
	dir.bot_choice = 0
	dir.bot_wait_mul = 1.0
	dir.bot_line_s = choice_s              # used only for replies; lines are timed per line below
	dir.line_shown.connect(func(item): _on_line(dir, item))
	dir.dialogue_closed.connect(func(): _prev = "")
	var prefs: Dictionary = sc["prefs"]
	dir.bot_pick_fn = func(conv: String, choices: Array) -> int:
		n_picks += 1
		if prefs.has(conv):
			for c in choices:
				if String(prefs[conv]) in String(c["text"]):
					return int(c["index"])
		return 0
	var bot := KeeperBot2.new("expert", int(_arg("seed", "11")) - 10)
	var ended := [false, {}]
	dir.campaign_finished.connect(func(e): ended[0] = true; ended[1] = e)
	dir.story_event.connect(func(n, a): if n == "sim_events": dir.on_sim_events(a[0]))
	dir.begin(true)
	var dt := 1.0 / 30.0
	var guard := 0.0
	var chapter_t := {}
	var idle_at: String = sc["idle_at"]
	while not ended[0] and guard < 7000.0:
		guard += dt
		for f in ["moved", "looked", "used_battery", "read_log_1971", "read_log_1953", "read_letter", "at_door"]:
			if dir.state.has_objective() and guard > 2.0:
				dir.state.flags[f] = 1
		var ev: Array = []
		if idle_at != "" and dir.state.chapter == 6 and dir.beat_reached(idle_at):
			if k.story_jam:
				if k.mode != KeeperSim.Mode.OFF:
					ev += k.set_mode(KeeperSim.Mode.OFF)
				k.set_wheel(-1.0)
			elif k.mode != KeeperSim.Mode.MANUAL:
				k.set_wheel(0.0)
				ev += k.set_mode(KeeperSim.Mode.MANUAL)
			if not k.main_breaker:
				ev += k.set_breaker("main", true)
			if k.gen == KeeperSim.Gen.OFF and k.battery < 55.0 and k.fuel > 0.0 and not k.gen_locked:
				if not k.fuel_valve:
					ev += k.set_fuel_valve(true)
				ev += k.set_start(true)
			elif k.gen != KeeperSim.Gen.CRANKING and k.start_held:
				ev += k.set_start(false)
		else:
			ev = bot.act(k, dt)
		ev += k.step(dt)
		dir.on_sim_events(ev)
		dir._process(dt)
		chapter_t[dir.state.chapter] = chapter_t.get(dir.state.chapter, 0.0) + dt
		if int(guard / dt) % 30 == 0:
			await process_frame
	if not ended[0]:
		print("REALTIME_STUCK chapter=%d beat=%s objective=%s sim: gen=%d mode=%d batt=%.0f fuel=%.0f" % [dir.state.chapter, dir.beat_id(), dir.state.objective, k.gen, k.mode, k.battery, k.fuel])
	var rounded := {}
	for c in chapter_t:
		rounded[c] = int(chapter_t[c])
	print("REALTIME route=%s choice=%.1f mul=%.2f ended=%s ending=%s sim_seconds=%d per_chapter=%s lines=%d chars=%d modelled_line_s=%d picks=%d" % [
		route_id, choice_s, reading_mul, ended[0], ended[1].get("ending", "?"), int(guard), JSON.stringify(rounded),
		n_lines, n_chars, int(line_total), n_picks])
	quit(0 if ended[0] else 1)
