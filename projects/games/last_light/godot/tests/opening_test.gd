extends SceneTree
## Remediation R1 (2026-11-15): the ch1 opening played the way a person plays it.
## Daniel's playtest stalled after the engine and the light: the six dusk thoughts waited for an unprompted
## Space, and every later beat waited behind them; the engine / charge beats also polled live state, so an
## overheat or CHARGE switched off left the story waiting with no guidance. Every older opening test ran
## the director in bot mode (auto-advance) or poked sim setters, so none of them could see it.
## Here: the real game (game_fp + presenter + dialogue UI), the director live in HUMAN mode, devices used
## through station.use -> game_fp._route (the player's path), and Space is NEVER pressed for thoughts.
##   O1  the usual order (valve, START, CHARGE, MODE, LAMP) after the dusk thoughts: reaches radio_check
##   O2  every device used while the first dusk thought is still on screen: no stall
##   O3  CHARGE switched off again (the hot-engine notice asks for it) and the engine overheating: no stall
##   O4  CHARGE before START, valve last: no stall
##   O5  save at the light beat, load it into a fresh game: the beat resumes and reaches radio_check
##   O6  radio lines still wait for Space (they never auto-advance) and show the cue; thoughts clear
##   godot --headless --path godot -s res://tests/opening_test.gd

var fails: Array[String] = []
var passes := 0
var g: Node3D
const TIME_SCALE := 6.0
const LIMIT_S := 240.0                   # game seconds any phase may take before it counts as a stall


func _initialize() -> void:
	_run.call_deferred()


func _check(ok: bool, what: String) -> void:
	if ok:
		passes += 1
		print("  PASS ", what)
	else:
		fails.append(what)
		print("  FAIL ", what)


func _frames(n: int) -> void:
	for i in n:
		await process_frame


## Wait up to `limit` game seconds for cond; returns true if it became true.
func _until(cond: Callable, limit := LIMIT_S) -> bool:
	var t := 0.0
	while t < limit:
		if cond.call():
			return true
		await process_frame
		t += root.get_process_delta_time()
	return cond.call()


func _secs(s: float) -> void:
	var t := 0.0
	while t < s:
		await process_frame
		t += root.get_process_delta_time()


func _beat_id() -> String:
	var b: Array = g.director._beats()
	return String(b[g.director.state.beat]["id"]) if g.director.state.beat < b.size() else "<end>"


func _beat_ix(id: String) -> int:
	var b: Array = g.director._beats()
	for i in b.size():
		if String(b[i]["id"]) == id:
			return i
	return -1


func _past(id: String) -> bool:
	return g.director.state.chapter > 1 or g.director.state.beat > _beat_ix(id)


func _at_or_past(id: String) -> bool:
	return g.director.state.chapter > 1 or g.director.state.beat >= _beat_ix(id)


func _use(dev: String, action := "press") -> void:
	g._route(g.station.use(dev, action))


func _new_game(save: Dictionary = {}) -> void:
	if g:
		g.queue_free()
		await _frames(3)
	g = load("res://scripts/fp/game_fp.gd").new()
	root.add_child(g)
	g.start(11, "", false, true, save)   # story mode, HUMAN (no bot): the UI advances lines
	await _frames(3)
	_check(not g.director.bot, "the director runs in human mode")
	if OS.get_cmdline_user_args().has("--no-auto"):
		g.presenter.dialogue.auto_advance = false     # proof run: the pre-R1 behaviour must fail O1
	await _until(func(): return not g.presenter.is_screen_held(), 30.0)


func _start_engine() -> void:
	_use("start", "press")
	await _until(func(): return g.sim.gen == KeeperSim.Gen.RUNNING or g.sim.gen == KeeperSim.Gen.OFF, 30.0)
	_use("start", "release")


func _dusk_line_up() -> bool:
	var d: Control = g.presenter.dialogue
	return d.is_active() and String(d._full).begins_with("Dark as a press")


func _run() -> void:
	await process_frame
	var st_node: Node = root.get_node("Settings")
	st_node.persist = false
	Engine.time_scale = TIME_SCALE
	await _o1_usual_order()
	await _o2_all_during_dusk()
	await _o3_charge_off_and_overheat()
	await _o4_charge_first()
	await _o5_save_load()
	Engine.time_scale = 1.0
	print("OPENING_RESULT ", JSON.stringify({"passed": passes, "failed": fails.size(), "failures": fails}))
	quit(1 if fails.size() > 0 else 0)


func _o1_usual_order() -> void:
	print("O1 the usual order, no Space for thoughts")
	await _new_game()
	_check(await _until(_dusk_line_up, 60.0), "the 'Dark as a press… cells are flat' line shows")
	_check(await _until(func(): return not _dusk_line_up(), 20.0), "and leaves by itself (no Space)")
	_check(await _until(func(): return not g.presenter.dialogue.is_active() and not g.director._talking, 90.0),
		"the six dusk thoughts all advance by themselves")
	_use("fuel_valve")
	await _start_engine()
	_check(g.sim.gen == KeeperSim.Gen.RUNNING, "the engine runs")
	_use("charge")
	_check(await _until(func(): return _at_or_past("light")), "engine and charge beats pass (now %s)" % _beat_id())
	_use("mode")
	_use("intensity")
	_check(g.sim.mode == 1 and g.sim.intensity >= 1, "MODE AUTO, LAMP NORMAL (mode %d, lamp %d)" % [g.sim.mode, g.sim.intensity])
	_check(await _until(func(): return _at_or_past("radio_check")), "the light beat passes (now %s)" % _beat_id())
	await _o6_radio_waits()


## O6: the radio check is a radio conversation; its lines need Space / RT and show the cue.
func _o6_radio_waits() -> void:
	var d: Control = g.presenter.dialogue
	_check(await _until(func(): return d.is_active() and d.line_look == "radio"), "the radio check's first line shows")
	var txt := String(d._full)
	await _secs(20.0)
	_check(d.is_active() and String(d._full) == txt, "a radio line does not advance by itself (20 s)")
	_check(d.r_hint.text.contains("Space") and d.r_hint.modulate.a > 0.3, "the radio line shows the Space cue ('%s')" % d.r_hint.text)
	_check(not d.sub_box.visible, "no thought subtitle is left on screen under the radio panel")
	# Space through the real input path advances it (keyboard event -> dialogue_next -> advance_requested)
	var e := InputEventKey.new()
	e.keycode = KEY_SPACE
	e.physical_keycode = KEY_SPACE
	e.pressed = true
	Input.parse_input_event(e)
	var u := e.duplicate()
	u.pressed = false
	Input.parse_input_event(u)
	_check(await _until(func(): return String(d._full) != txt or not d.is_active() or not d._choices.is_empty(), 5.0),
		"Space (a real key event) moves the radio conversation on")


func _o2_all_during_dusk() -> void:
	print("O2 every device used while the first dusk thoughts are up")
	await _new_game()
	await _until(func(): return g.presenter.dialogue.is_active(), 60.0)
	_use("fuel_valve")
	await _start_engine()
	_use("charge")
	_use("mode")
	_use("intensity")
	_check(g.presenter.dialogue.is_active(), "the work was done while the dusk thoughts were still showing")
	_check(await _until(func(): return _at_or_past("radio_check")), "the story still reaches radio_check (now %s)" % _beat_id())


func _o3_charge_off_and_overheat() -> void:
	print("O3 CHARGE off again, then an overheat, before the beats are reached")
	await _new_game()
	await _until(func(): return g.presenter.dialogue.is_active(), 60.0)
	_use("fuel_valve")
	await _start_engine()
	_use("charge")
	await _secs(1.0)                                   # the power duty sees the charge flow
	g.sim.gen_temp = 99.9                              # charging hard: let her overheat
	_check(await _until(func(): return g.sim.gen != KeeperSim.Gen.RUNNING, 60.0), "the engine cuts out on the overheat")
	_use("charge")                                     # and CHARGE off, as "running hot" asks
	_check(await _until(func(): return _at_or_past("light")), "engine and charge beats pass with the engine stopped (now %s)" % _beat_id())
	_use("mode")
	_use("intensity")
	_check(await _until(func(): return _at_or_past("radio_check")), "and the story reaches radio_check (now %s)" % _beat_id())


func _o4_charge_first() -> void:
	print("O4 CHARGE before START, the valve opened last")
	await _new_game()
	await _until(func(): return not g.director._talking, 120.0)
	_use("charge")
	_use("start", "press")
	await _until(func(): return g.sim.gen == KeeperSim.Gen.OFF and g.director.state.has_flag("crank_failed"), 30.0)
	_use("start", "release")
	_check(g.director.state.has_flag("crank_failed"), "START with the valve shut fails and teaches the valve")
	_use("fuel_valve")
	await _start_engine()
	_check(await _until(func(): return _at_or_past("light")), "the engine and charge beats pass (now %s)" % _beat_id())
	_use("mode")
	_use("intensity")
	_check(await _until(func(): return _at_or_past("radio_check")), "and the story reaches radio_check (now %s)" % _beat_id())


func _o5_save_load() -> void:
	print("O5 save at the light beat, load into a fresh game")
	await _new_game()
	await _until(func(): return not g.director._talking, 120.0)
	_use("fuel_valve")
	await _start_engine()
	_use("charge")
	await _until(func(): return _at_or_past("light") and not g.director._talking and g.director._actions.is_empty())
	var d: Dictionary = g.save_dict()
	_check(int(d["story"].get("beat", -1)) == _beat_ix("light"), "the save is at the light beat (%s)" % d["story"].get("beat", -1))
	await _new_game(d)
	_check(_beat_id() == "light", "the loaded game resumes at the light beat (%s)" % _beat_id())
	_check(g.sim.gen == KeeperSim.Gen.RUNNING, "the engine is still running after the load")
	_use("mode")
	_use("intensity")
	_check(await _until(func(): return _at_or_past("radio_check")), "and reaches radio_check after the load (now %s)" % _beat_id())
	_check(await _until(func(): return g.director.state.has_flag("dusk_done"), 10.0), "dusk_done is set from the radio check on (the sky stays night on a later load)")
