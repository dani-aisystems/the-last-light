extends SceneTree
## Stage 0 regression tests for the three gameplay blockers (2026-11-04 audit):
##  R1  mouse look stays on with replies open in free walk and after picking one (cabin pass); the pointer
##      stays free inside a device view
##  R2  dialogue choices never overlap the radio command panel (several window aspect ratios)
##  R3  input under the pause menu does not advance dialogue, pick choices, or run the typewriter
##  R4  speakerless narration inside a radio conversation shows as a thought, not a blank transmission
##  R5  Stage 2A interaction state: prompt keys, refusals with reasons (once), the door prompt, no dead
##      prompts in device views (radio -> chart switches), pause releases a held START
##  R6  Stage 2B radio panel: stable vessel buttons, a click across a refresh, Space after an order, tips
##  R7  Stage 2C gamepad and camera: no shared pad inputs, right-stick look and deadzone, A / B / LB / RB,
##      the device-view pad cursor (room controls and screen buttons), reply focus, glyphs, head bob
##  R9  Stage 3A dialogue foundation: bundled fonts with a real italic, the identity resolver (no early
##      "Ross" in names, history or backlog), line looks (in-room speakers, sound captions), a typewriter
##      that lays out once and waits behind fades and documents, objective tokens, one text scale for all
##      roles, and the dialogue history (pauses, never advances, mouse and pad focus restored)
##  R10 Stage 3B narrative mechanics: the story jam (any mode, no MAIN trip, never cleared by a power loss,
##      freed only by hand: OFF + handwheel back), Ross's beam assist, transitions that hold the story and
##      block dialogue input under black, the ending card, optional calls that defer the next beat's talk,
##      no early "Alasdair Ross", the stair-door bolt and the 1953 photograph props
##  R11 brief 2026-11-06, group G1: E is never taken by dialogue, Space finishes then advances only after
##      the dwell, replies ignore their first 0.4 s, the clock card draws above the black, the radar is its
##      own target (never the radio view), sim radio chatter waits behind a story line and is logged
##  R12 brief G2: the pause menu (no saving; Transcript / Options / Main menu with a confirm), Options handed
##      to main_fp, device checks answered with a logged thought, the step objective panel (ticks, compact
##      in device views, clear of the radio panel at every text size)
##   godot --path godot -s res://tests/regress_test.gd            (windowed: all checks)
##   godot --headless --path godot -s res://tests/regress_test.gd (R1 mouse checks SKIPPED: the headless
##                                                                  display server ignores mouse modes)

var fails: Array[String] = []
var skips: Array[String] = []
var passes := 0
var g: Node3D
var dlg: Control
var _real_saves := {}                   # G6d: the player's save files (name -> mtime) before the run


func _initialize() -> void:
	_run.call_deferred()


func _check(ok: bool, what: String) -> void:
	if ok:
		passes += 1
		print("  PASS ", what)
	else:
		fails.append(what)
		print("  FAIL ", what)


## Wait for the frame right after the radio panel's vessel refresh (fp_ui: every 30 process frames, which
## clears selected_ship when no vessel is on the channel), so a key sent now has 28 frames' margin. The
## radio-order checks failed about 1 run in 4 under load when the refresh landed between set and key.
func _after_vessel_refresh() -> void:
	while Engine.get_process_frames() % 30 != 1:
		await process_frame


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _key(code: Key) -> void:
	var e := InputEventKey.new()
	e.keycode = code
	e.physical_keycode = code
	e.pressed = true
	Input.parse_input_event(e)
	var u := e.duplicate()
	u.pressed = false
	Input.parse_input_event(u)


func _run() -> void:
	await process_frame
	_real_saves = _save_mtimes("user://saves")
	g = load("res://scripts/fp/game_fp.gd").new()
	root.add_child(g)
	g.start(7, "", false, true)          # story mode, human (no bot)
	await _frames(3)
	g.director.process_mode = Node.PROCESS_MODE_DISABLED   # keep the campaign from talking over the tests
	# the ch1 card now starts on black and holds dialogue input until it lifts (item 21): let it finish
	var lift := 0
	while g.presenter.is_screen_held() and lift < 900:
		await process_frame
		lift += 1
	# ch1 now opens with flat cells and the lights off (brief item 8); these checks were written for a
	# powered station, so give it charge (the dark opening has its own checks in story_test)
	g.sim.battery = 80.0
	# windowed runs capture the real pointer: Daniel's own mouse must not turn the camera or flip the device
	# mode mid-test (cabin pass). In memory only: persist is off, so settings.cfg is never written.
	var st_node: Node = root.get_node("Settings")
	st_node.persist = false
	st_node.v["mouse_sens"] = 0.0
	dlg = g.presenter.dialogue
	if dlg.is_active():
		dlg.close()
	await _r1_mouse()
	await _r2_overlap()
	await _r3_pause()
	await _r4_thought_in_radio()
	await _r5_interaction_state()
	await _r6_radio_panel()
	await _r7_gamepad_and_camera()
	await _r8_cabin_reliability()
	await _r9_dialogue_foundation()
	await _r10_narrative_mechanics()
	await _r11_brief_g1()
	await _r12_brief_g2()
	print("REGRESS_RESULT ", JSON.stringify({"passed": passes, "failed": fails.size(), "failures": fails, "skipped": skips}))
	quit(1 if fails.size() > 0 else 0)


## Stage 2A: interaction state, refusals with reasons, no dead prompts, door prompt, pause releases holds.
func _r5_interaction_state() -> void:
	print("R5 interaction state (Stage 2A)")
	var st: Node3D = g.station
	var k: KeeperSim = g.sim
	# a) valid prompt in free walk carries the interact key
	var p: Dictionary = st.prompt_info("radio", false)
	_check(p["ok"] and p["key"] == "[E]" and p["text"] == "Use the radio", "radio prompt is '[E]  Use the radio' (%s)" % p)
	# b) G2b (Daniel 2026-11-06): START with the valve shut is no longer refused: the engine cranks,
	#    fails after crank_fail_time (gen_crank_fail, why valve) and is back to OFF; the keeper learns by trying
	k.gen = KeeperSim.Gen.OFF
	k.fuel_valve = false
	k.start_held = false
	p = st.prompt_info("start", false)
	_check(p["ok"] and p["key"] != "", "START with the valve shut can be tried (%s)" % p)
	var ev: Array = st.use("start", "press")
	_check(ev.any(func(x): return x["type"] == "gen_crank") and k.gen == KeeperSim.Gen.CRANKING, "START press with the valve shut cranks (%s)" % [ev])
	var fail_ev: Array = []
	for i in 90:
		fail_ev += k.step(1.0 / 30.0)
	_check(fail_ev.any(func(x): return x["type"] == "gen_crank_fail" and x["why"] == "valve") and k.gen == KeeperSim.Gen.OFF,
		"with the valve shut the crank fails (why: valve) and the engine is off again")
	ev = st.use("start", "release")
	k.start_held = false
	k.gen = KeeperSim.Gen.RUNNING
	_check(st.availability("start")["reason"] == "The generator is already running.", "START while running says so")
	k.gen = KeeperSim.Gen.OFF
	k.fuel_valve = true
	_check(st.availability("start")["ok"], "START with the valve open and the engine stopped is available")
	# c) the refusal notice is shown once, not on every press
	g.ui.notice.text = ""
	g._route([{"type": "refused", "device": "start", "reason": "Test reason."}])
	var first: String = g.ui.notice.text
	g.ui.notice.text = ""
	g._route([{"type": "refused", "device": "start", "reason": "Test reason."}])
	_check(first == "Test reason." and g.ui.notice.text == "", "a repeated refusal within 3 s is not shown again")
	# d) charging on with the generator stopped explains why nothing flows
	k.charge_on = false
	ev = st.use("charge", "press")
	_check(ev.any(func(e): return e["type"] == "note"), "charging ON with the engine stopped adds a note")
	k.charge_on = false
	# e) the door prompt follows the story: ch1 usable, ch4 bolted (no key), open (no key)
	g.director.state.chapter = 1
	st.door_open = false
	g._update_door_prompt()
	_check(st.prompt_info("door", false)["key"] == "[E]", "door in ch1: '[E]  Try the stair door'")
	g.director.state.chapter = 4
	g.director.state.beat = 0
	g._update_door_prompt()
	p = st.prompt_info("door", false)
	_check(p["key"] == "" and p["text"] == "The stair door", "door in ch4 before the boat is alongside: no key (%s)" % p)
	g.director.state.beat = 2                      # 3B: from `hail` the keeper may bolt it
	g._update_door_prompt()
	p = st.prompt_info("door", false)
	_check(p["key"] == "[E]" and "bolt" in p["text"], "door in ch4 once she's alongside: '[E]  Draw the bolt' (%s)" % p)
	g.director.state.flags["bolted"] = 1
	g._update_door_prompt()
	p = st.prompt_info("door", false)
	_check(p["key"] == "" and "bolted" in p["text"], "bolted door: no key (%s)" % p)
	g.director.state.flags.erase("bolted")
	g.director.state.beat = 0
	st.door_open = true
	g._update_door_prompt()
	_check(st.prompt_info("door", false)["text"] == "The stair door stands open", "open door says so")
	st.door_open = false
	g.director.state.chapter = 1
	g._update_door_prompt()
	# f) device views: every control the cursor can reach either acts on a click or shows no key; the
	#    chart seen from the radio view switches straight to the chart view (it used to be a dead prompt)
	for view in ["radio", "console", "chart"]:
		g.player.enter_focus(view)
		await _frames(40)
		await _settle_focus()
		var ids := {}
		var space: PhysicsDirectSpaceState3D = g.player.get_world_3d().direct_space_state
		var vp: Vector2 = g.player.get_viewport().get_visible_rect().size
		for ix in 32:
			for iy in 18:
				var sp := Vector2((ix + 0.5) / 32.0 * vp.x, (iy + 0.5) / 18.0 * vp.y)
				var id: String = g.player.pick(space, g.player.camera.project_ray_origin(sp), g.player.camera.project_ray_normal(sp), g.player.REACH + 1.2)
				if id != "":
					ids[id] = true
		var dead: Array = []
		for id in ids:                            # the key the player would see (player._update_prompt rule)
			var key: String = st.prompt_info(id, true)["key"] if g.player._actionable(id) else ""
			if key == "[Click]" and st.DEVICES[id]["kind"] == "focus" and not g.player._can_switch(st.DEVICES[id].get("focus_id", id)):
				dead.append(id)
		_check(dead.is_empty(), "%s view: no clickable prompt that does nothing (reachable: %s)" % [view, ids.keys()])
		if view == "radio" and ids.has("chart"):      # cabin pass: the chart is a full-screen inspection (R8)
			_check(g.player._actionable("chart") and g.station.DEVICES["chart"]["kind"] == "doc",
				"radio view -> the chart is clickable and opens the chart inspection")
		g.player.leave_focus()
		await _frames(40)
		await _settle_focus()
	# g) pause while holding START stops the crank (the key-up is lost under the pause menu)
	k.gen = KeeperSim.Gen.OFF
	k.fuel_valve = true
	g.player._holding = "start"
	g._route(st.use("start", "press"))
	var cranking := k.gen == KeeperSim.Gen.CRANKING and k.start_held
	g.set_paused(true)
	await _frames(2)
	_check(cranking and not k.start_held and k.gen != KeeperSim.Gen.CRANKING, "pause while holding START stops cranking (was cranking=%s)" % cranking)
	g.set_paused(false)
	await _frames(2)


func _mouse(pos: Vector2, down: bool) -> void:
	var m := InputEventMouseMotion.new()
	m.position = pos
	m.global_position = pos
	root.push_input(m)
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_LEFT
	e.pressed = down
	e.position = pos
	e.global_position = pos
	root.push_input(e)


func _vessel_buttons() -> Array:
	return g.ui.vessel_list.get_children().filter(func(c): return c is Button and not c.is_queued_for_deletion())


## Stage 2B: the vessel list keeps its buttons (hover, focus, clicks survive the periodic refresh),
## and a clicked order button does not keep focus (Space / Enter / pad A would send it again).
func _r6_radio_panel() -> void:
	print("R6 radio panel (Stage 2B)")
	var settings: Node = root.get_node("Settings")
	if "persist" in settings:
		settings.persist = false               # tips counted here must not reach user://settings.cfg
	for n in ["Testboat One", "Testboat Two"]:
		g._route(g.sim.spawn_story_ship({"name": n, "kind": "fishing", "bearing": 20, "aim": 24, "hold": true, "protected": true}))
	g.player.enter_focus("radio")
	await _frames(40)
	await _settle_focus()
	g.ui._refresh_vessels()
	await _frames(2)
	var before := _vessel_buttons().map(func(b): return b.get_instance_id())
	await _frames(125)                         # four 30-frame refresh cycles
	var after := _vessel_buttons().map(func(b): return b.get_instance_id())
	_check(before.size() >= 2 and before == after, "vessel buttons keep their identity across refreshes (%d buttons)" % before.size())
	# a click whose press and release straddle a refresh still selects the vessel
	var act: Array = g.sim.active_ships()
	var target_id: int = act[1].id if act.size() > 1 else -1
	g.ui.selected_ship = act[0].id
	g.ui._refresh_vessels()
	await _frames(2)
	var btn: Button = _vessel_buttons()[1]
	var pos: Vector2 = btn.get_global_rect().get_center()
	while Engine.get_process_frames() % 30 != 28:
		await process_frame
	_mouse(pos, true)
	await _frames(4)                           # the refresh lands between press and release
	_mouse(pos, false)
	await _frames(2)
	_check(g.ui.selected_ship == target_id, "a click across a list refresh selects the vessel (selected %d, wanted %d)" % [g.ui.selected_ship, target_id])
	# Space after clicking an order must not send it again
	var sent := [0]
	var counter := func(_id, _cmd): sent[0] += 1
	g.ui.command_requested.connect(counter)
	var order: Button = null
	for c in g.ui.radio_panel.find_children("*", "Button", true, false):
		if String(c.text).contains("Hold position"):
			order = c
	var opos: Vector2 = order.get_global_rect().get_center()
	_mouse(opos, true)
	await _frames(2)
	_mouse(opos, false)
	await _frames(2)
	var after_click: int = sent[0]
	var sp := InputEventKey.new()
	sp.keycode = KEY_SPACE
	sp.physical_keycode = KEY_SPACE
	sp.pressed = true
	root.push_input(sp)
	var spu := sp.duplicate()
	spu.pressed = false
	root.push_input(spu)
	await _frames(3)
	_check(after_click == 1 and sent[0] == 1, "Space after clicking an order does not send it again (click sent %d, total %d)" % [after_click, sent[0]])
	g.ui.command_requested.disconnect(counter)
	# one-time tips: shown until the control has been used twice, then gone (counted in memory only here)
	var saved_tips: Dictionary = settings.v["tips"].duplicate()
	settings.v["tips"] = {}
	g.ui._refresh_vessels()
	var tab_shown: bool = g.ui.tab_tip.visible
	for i in 2:
		var t := InputEventKey.new()
		t.keycode = KEY_TAB
		t.physical_keycode = KEY_TAB
		t.pressed = true
		root.push_input(t)
		var tu := t.duplicate()
		tu.pressed = false
		root.push_input(tu)
		await _frames(2)
	_check(tab_shown and not g.ui.tab_tip.visible, "Tab tip shows with two vessels and retires after two uses (shown=%s, now=%s)" % [tab_shown, g.ui.tab_tip.visible])
	g.player.leave_focus()
	await _frames(40)
	await _settle_focus()
	g.player.enter_focus("console")
	await _frames(40)
	await _settle_focus()
	var sub0: String = g.station.prompt_info("mode", true)["sub"]
	g.player._turn("mode", "next", "wheel")
	g.player._turn("mode", "prev", "wheel")
	var sub1: String = g.station.prompt_info("mode", true)["sub"]
	_check("[Wheel]" in sub0 and not ("[Wheel]" in sub1) and "Right click" in sub1, "knob tip: '%s' -> '%s' after two wheel turns" % [sub0, sub1])
	_check(not FileAccess.file_exists("user://settings.cfg") or not FileAccess.get_file_as_string("user://settings.cfg").contains("wheel"),
		"tips counted by tests are not written to settings.cfg")
	settings.v["tips"] = saved_tips
	g.player.leave_focus()
	await _frames(40)
	await _settle_focus()


func _pad_button(b: JoyButton, down := true) -> void:
	var e := InputEventJoypadButton.new()
	e.button_index = b
	e.pressed = down
	e.pressure = 1.0 if down else 0.0
	Input.parse_input_event(e)


func _pad_axis(a: JoyAxis, v: float) -> void:
	var e := InputEventJoypadMotion.new()
	e.axis = a
	e.axis_value = v
	Input.parse_input_event(e)


func _tap(b: JoyButton) -> void:
	_pad_button(b, true)
	await _frames(2)
	_pad_button(b, false)
	await _frames(2)


## Stand 1.2 m from a control (towards the room centre) and look at it, as a player would.
func _aim_at(id: String) -> void:
	var p := _ia_pos(id)
	var inward := Vector3(-p.x, 0, -p.z).normalized()
	g.player.global_position = Vector3(p.x + inward.x * 1.2, g.player.global_position.y, p.z + inward.z * 1.2)
	var to: Vector3 = p - (g.player.global_position + Vector3(0, g.player.EYE, 0))
	g.player._yaw = atan2(-to.x, -to.z)
	g.player._pitch = atan2(to.y, Vector2(to.x, to.z).length())
	g.player._apply_look()
	await _frames(6)


## A device-view ease (0.45 s, time-based) blends the camera, and with it the crosshair ray, between the
## views. A fixed frame count is not enough windowed: at a 120 Hz display 40 frames can end inside the ease
## (cabin pass CP4: R6/R7 failed windowed with the camera 1.97 m off the eye). Wait for the ease itself.
func _settle_focus() -> void:
	var n := 0
	while g.player._focus_t < 1.0 and n < 600:
		await process_frame
		n += 1
	await physics_frame                         # one tick so hover and the body update from the settled camera


func _ia_pos(id: String) -> Vector3:
	for b in g.station.get_children():
		if b is StaticBody3D and String(b.get_meta("ia", "")) == id:
			return b.global_position
	return Vector3.INF


## Stage 2C: pad bindings have no overlaps, right-stick look with a deadzone, A / B / LB / RB, the
## device-view pad cursor (room controls and on-screen buttons), pad focus on replies, glyphs, and the
## interpolated camera.
func _r7_gamepad_and_camera() -> void:
	print("R7 gamepad and camera (Stage 2C)")
	var settings: Node = root.get_node("Settings")
	settings.persist = false
	InputSetup.pad_forced = false
	# a) no two first-person actions share a pad input; v1 boost is off A
	var seen := {}
	var dup: Array = []
	for action in InputSetup.PAD_FP:
		var b: Array = InputSetup.PAD_FP[action]
		var key := ("b%d" % b[1]) if b[0] == "button" else ("a%d%s" % [b[1], "+" if b[2] > 0 else "-"])
		if seen.has(key):
			dup.append("%s/%s" % [seen[key], action])
		seen[key] = action
	_check(dup.is_empty(), "no two first-person actions share a pad input (%s)" % [dup])
	var boost_on_a := InputMap.action_get_events("boost").any(func(e): return e is InputEventJoypadButton and e.button_index == JOY_BUTTON_A)
	_check(not boost_on_a, "v1 boost no longer shares A with interact")
	# b) right-stick look: a small deflection inside the deadzone does nothing, a full one turns
	g.player.focused = ""
	var y0: float = g.player._yaw
	_pad_axis(JOY_AXIS_RIGHT_X, 0.1)
	await _frames(20)
	var y_small: float = g.player._yaw
	_pad_axis(JOY_AXIS_RIGHT_X, 1.0)
	await _frames(20)
	var y_full: float = g.player._yaw
	_pad_axis(JOY_AXIS_RIGHT_X, 0.0)
	await _frames(5)
	var y_rest: float = g.player._yaw
	await _frames(10)
	_check(is_equal_approx(y0, y_small) and absf(y_full - y0) > 0.1 and is_equal_approx(y_rest, g.player._yaw),
		"right stick: deadzone %.4f, full turn %.2f rad in 20 frames, stops on release" % [y_small - y0, y_full - y0])
	_check(InputSetup.pad_active, "a pad input switches the prompts to pad glyphs")
	InputSetup.pad_forced = true              # a pad-only player from here on (real mouse noise ignored)
	_check(g.station.prompt_info("radio", false)["key"] == "[A]", "pad prompt key is [A] (%s)" % g.station.prompt_info("radio", false)["key"])
	# c) pad A uses the control under the crosshair (free walk): aim at the radar breaker
	var p := _ia_pos("brk_radar")
	var inward := Vector3(-p.x, 0, -p.z).normalized()
	g.player.global_position = Vector3(p.x + inward.x * 1.2, g.player.global_position.y, p.z + inward.z * 1.2)
	var to: Vector3 = p - (g.player.global_position + Vector3(0, g.player.EYE, 0))
	g.player._yaw = atan2(-to.x, -to.z)
	g.player._pitch = atan2(to.y, Vector2(to.x, to.z).length())
	g.player._apply_look()
	await _frames(6)
	var radar0: bool = g.sim.brk_radar
	await _tap(JOY_BUTTON_A)
	_check(g.sim.brk_radar != radar0, "pad A switches the radar breaker under the crosshair (hovered=%s)" % g.player.hovered)
	g._route(g.sim.set_breaker("radar", radar0))
	# camera follows the body exactly after a placement (no interpolation smear)
	var cam_err: float = g.player.camera.global_position.distance_to(g.player.global_position + Vector3(0, g.player.EYE + g.player._bob_y, 0))
	_check(cam_err < 0.01, "camera sits at the eye right after a placement (%.3f m)" % cam_err)
	# generator: hold pad A on START cranks, letting go stops (hold-to-crank, valve open)
	g.sim.gen = KeeperSim.Gen.OFF
	g.sim.fuel_valve = true
	g.sim.start_held = false
	await _aim_at("start")
	_pad_button(JOY_BUTTON_A, true)
	await _frames(4)
	var cranking: bool = g.sim.start_held and g.sim.gen == KeeperSim.Gen.CRANKING
	_pad_button(JOY_BUTTON_A, false)
	await _frames(4)
	_check(cranking and not g.sim.start_held, "pad: hold A on START cranks, release stops (hovered=%s)" % g.player.hovered)
	g.sim.gen = KeeperSim.Gen.OFF
	# stair door: pad A gives the chapter-gated line (ch1)
	g.presenter.hint.text = ""
	await _aim_at("door")
	await _tap(JOY_BUTTON_A)
	_check(g.presenter.hint.text != "", "pad: A on the stair door gives the bolted-door line (hovered=%s)" % g.player.hovered)
	# d) device view: the pad cursor picks the MODE knob, A turns it, LB turns it back, B steps back
	g.player.enter_focus("console")
	await _frames(40)
	await _settle_focus()
	_check(g.player.virtual_cursor.is_finite(), "entering a device view on the pad starts the pad cursor")
	if DisplayServer.get_name() == "headless":
		skips.append("R7 OS pointer hidden in a pad device view (headless)")
	else:
		_check(Input.mouse_mode == Input.MOUSE_MODE_HIDDEN, "pad device view hides the OS pointer (mode %d)" % Input.mouse_mode)
	g.player.virtual_cursor = g.player.camera.unproject_position(_ia_pos("mode"))
	await _frames(3)
	var m0: int = g.sim.mode
	await _tap(JOY_BUTTON_A)
	var m1: int = g.sim.mode
	await _tap(JOY_BUTTON_LEFT_SHOULDER)
	_check(m1 == (m0 + 1) % 3 and g.sim.mode == m0, "pad cursor + A turns MODE (%d -> %d), LB turns it back (%d)" % [m0, m1, g.sim.mode])
	var c0: Vector2 = g.player.virtual_cursor
	_pad_axis(JOY_AXIS_RIGHT_X, 1.0)
	await _frames(15)
	_pad_axis(JOY_AXIS_RIGHT_X, 0.0)
	await _frames(2)
	_check(g.player.virtual_cursor.x > c0.x + 40.0, "right stick moves the device-view cursor (%.0f -> %.0f px)" % [c0.x, g.player.virtual_cursor.x])
	await _tap(JOY_BUTTON_B)
	await _frames(30)
	_check(g.player.focused == "", "pad B steps back out of the device view")
	# e) radio view: the pad cursor presses an on-screen order button; RB picks the next vessel
	g.player.enter_focus("radio")
	await _frames(40)
	await _settle_focus()
	g.ui._refresh_vessels()
	var sent := [0]
	var counter := func(_id, _cmd): sent[0] += 1
	g.ui.command_requested.connect(counter)
	var order: Button = null
	for c in g.ui.radio_panel.find_children("*", "Button", true, false):
		if String(c.text).contains("Maintain course"):
			order = c
	g.player.virtual_cursor = order.get_global_rect().get_center()
	await _tap(JOY_BUTTON_A)
	g.ui.command_requested.disconnect(counter)
	_check(sent[0] == 1, "pad cursor + A presses the radio order under it (sent %d)" % sent[0])
	var s0: int = g.ui.selected_ship
	await _tap(JOY_BUTTON_RIGHT_SHOULDER)
	_check(g.ui.sim.active_ships().size() < 2 or g.ui.selected_ship != s0, "RB selects the next vessel in the radio view")
	g.player.leave_focus()
	await _frames(30)
	await _settle_focus()
	# f) dialogue replies take pad focus; A picks the focused reply
	var picked := [-1]
	var on_pick := func(i): picked[0] = i
	dlg.choice_made.connect(on_pick)
	_choices("person")
	await _frames(4)
	var focus_owner := root.gui_get_focus_owner()
	var first_focused: bool = focus_owner != null and dlg.choice_box.get_child_count() > 0 and focus_owner == dlg.choice_box.get_child(0)
	await _tap(JOY_BUTTON_A)
	dlg.choice_made.disconnect(on_pick)
	_check(first_focused and picked[0] == 0, "pad: the first reply has focus and A picks it (focused=%s, picked=%d)" % [first_focused, picked[0]])
	if dlg.is_active():
		dlg.close()
	# g) head bob off keeps the eye level
	settings.v["head_bob"] = false
	g.player.velocity = Vector3(1.6, 0, 0)
	for i in 20:
		g.player._process(1.0 / 60.0)
	_check(absf(g.player._bob_y) < 0.0005 and absf(g.player._roll) < 0.0001, "Head bob off: no bob or roll while walking")
	settings.v["head_bob"] = true
	g.player.velocity = Vector3.ZERO
	# back to keyboard and mouse for anything after this
	InputSetup.pad_forced = false
	var k := InputEventKey.new()
	k.keycode = KEY_SHIFT
	k.physical_keycode = KEY_SHIFT
	k.pressed = true
	Input.parse_input_event(k)
	await _frames(2)
	var ku := k.duplicate()
	ku.pressed = false
	Input.parse_input_event(ku)
	await _frames(2)
	_check(not InputSetup.pad_active and g.station.prompt_info("radio", false)["key"] == "[E]", "a key press switches back to keyboard glyphs")


func _mouse_btn(b: MouseButton, down: bool) -> void:
	var e := InputEventMouseButton.new()
	e.button_index = b
	e.pressed = down
	e.position = Vector2(960, 540)
	e.global_position = e.position
	root.push_input(e)


func _act(action: String) -> void:
	var e := InputEventAction.new()
	e.action = action
	e.pressed = true
	Input.parse_input_event(e)
	await _frames(2)
	var u := InputEventAction.new()
	u.action = action
	u.pressed = false
	Input.parse_input_event(u)
	await _frames(2)


## Cabin pass checkpoint 1: one owner for the mouse mode, replies answered without losing mouse look,
## radio replies re-gated, a document / chart viewer that only closes on purpose, the blackout torch,
## and a repeated interaction loop that must always come back to free-walk mouse look (IMG_3140).
func _r8_cabin_reliability() -> void:
	print("R8 cabin pass: cursor, chart, torch")
	var settings: Node = root.get_node("Settings")
	settings.persist = false
	InputSetup.pad_active = false
	# a) a single owner: in-game scripts never set Input.mouse_mode except player.capture_mouse (main_fp's
	#    menu has the screen when no game exists)
	var writers: Array = []
	for f in ["fp/game_fp.gd", "fp/fp_ui.gd", "fp/station.gd", "ui/dialogue_ui.gd", "story/story_presenter.gd", "story/story_director.gd"]:
		var src := FileAccess.get_file_as_string("res://scripts/" + f)
		for line in src.split("\n"):
			if line.strip_edges().begins_with("Input.mouse_mode =") or line.contains("Input.mouse_mode = "):
				writers.append(f)
				break
	_check(writers.is_empty(), "only player.capture_mouse sets the mouse mode in-game (other writers: %s)" % [writers])
	# b) free-walk replies keep mouse look; only the number keys answer (brief item 25: the wheel, E and
	#    the arrows never pick a reply)
	g.player.leave_focus()
	await _frames(30)
	await _settle_focus()
	var picked := [-1]
	var on_pick := func(i): picked[0] = i
	dlg.choice_made.connect(on_pick)
	_choices("person")
	await _frames(3)
	_check(g.mouse_should_capture(), "replies open in free walk: mouse look stays on")
	_mouse_btn(MOUSE_BUTTON_WHEEL_DOWN, true)
	_mouse_btn(MOUSE_BUTTON_WHEEL_DOWN, false)
	await _frames(2)
	await _act("interact")
	_key(KEY_DOWN)
	_key(KEY_SPACE)
	await _frames(3)
	_check(picked[0] == -1 and dlg.has_open_choices(), "the wheel, E, Down and Space do not answer (picked %d)" % picked[0])
	_key(KEY_2)
	await _frames(3)
	_check(picked[0] == 1, "key 2 answers the second reply (picked %d)" % picked[0])
	dlg.choice_made.disconnect(on_pick)
	if dlg.is_active():
		dlg.close()
	# c) radio replies only in the radio view (item 23): standing at the handset is not enough
	var at: Vector3 = g.station.focus["radio"]["at"]
	g.player.global_position = Vector3(at.x, g.player.global_position.y, at.z)
	g.player._apply_look()
	_choices("radio")
	await _frames(3)
	var hidden_near: bool = not dlg.has_open_choices()
	g.player.enter_focus("radio")
	await _settle_focus()
	await _frames(3)
	var shown_in_view: bool = dlg.has_open_choices()
	g.player.leave_focus()
	await _settle_focus()
	await _frames(3)
	var hidden_after: bool = not dlg.has_open_choices()
	_check(hidden_near and shown_in_view and hidden_after, "radio replies: hidden beside the radio, shown in the radio view, hidden after leaving it (%s/%s/%s)" % [hidden_near, shown_in_view, hidden_after])
	g.player.enter_focus("radio")
	await _settle_focus()
	await _frames(3)
	_check(dlg.has_open_choices(), "back in the radio view the replies return")
	dlg.close()
	g.player.leave_focus()
	await _settle_focus()
	# d) the chart opens full screen; a left click or the wheel never closes it; right click / E / Esc do
	g._on_doc("chart")
	await _frames(4)
	var opened: bool = g.presenter.is_document_open()
	_mouse_btn(MOUSE_BUTTON_LEFT, true)
	_mouse_btn(MOUSE_BUTTON_LEFT, false)
	_mouse_btn(MOUSE_BUTTON_WHEEL_UP, true)
	_mouse_btn(MOUSE_BUTTON_WHEEL_UP, false)
	await _frames(3)
	var still_open: bool = g.presenter.is_document_open()
	var zoomed: bool = g.presenter._zoom > 1.0
	_check(opened and not g.mouse_should_capture(), "chart inspection opens and frees the pointer")
	_check(still_open and zoomed, "a left click and the wheel zoom instead of closing the chart (zoom %.2f)" % g.presenter._zoom)
	_mouse_btn(MOUSE_BUTTON_RIGHT, true)
	_mouse_btn(MOUSE_BUTTON_RIGHT, false)
	await _frames(3)
	_check(not g.presenter.is_document_open() and g.player.enabled and g.mouse_should_capture(),
		"right click closes the chart and gives free-walk mouse look back (open=%s enabled=%s focused=%s paused=%s capture=%s)" % [
		g.presenter.is_document_open(), g.player.enabled, g.player.focused, g._paused, g.mouse_should_capture()])
	var tex_ok: bool = g.presenter.doc_info("chart").get("tex", "") != "" and ResourceLoader.exists(g.presenter.doc_info("chart")["tex"])
	_check(tex_ok, "the chart inspection uses the desk chart's own texture")
	# e) E on a document never also advances the dialogue underneath
	_choices("person")
	await _frames(2)
	dlg.close()
	dlg.show_line({"mode": "person", "speaker": "VISITOR", "text": "Evening, keeper."})
	await _frames(2)
	dlg._shown = dlg._full.length()
	dlg._done_t = 1.0
	var adv := [0]
	var on_adv := func(): adv[0] += 1
	dlg.advance_requested.connect(on_adv)
	g._on_doc("forecast")
	await _frames(4)
	await _act("interact")
	dlg.advance_requested.disconnect(on_adv)
	_check(not g.presenter.is_document_open() and adv[0] == 0, "E closes the document without advancing the line under it (advances %d)" % adv[0])
	dlg.close()
	# f) the blackout torch: not with the lights on; taken in the dark; F switches it; it stays taken
	g._route(g.sim.set_breaker("lights", true))
	await _frames(2)
	var p_on: Dictionary = g.station.prompt_info("torch", false)
	_check(not p_on["ok"] and p_on["key"] == "" and p_on["text"].contains("power fails"), "torch with the lights on: no key, 'for when the power fails' (%s)" % p_on)
	g._route(g.sim.set_breaker("lights", false))
	await _frames(2)
	var p_off: Dictionary = g.station.prompt_info("torch", false)
	_check(p_off["ok"] and p_off["key"] == "[E]" and p_off["text"] == "Pick up the torch", "torch in a blackout: '[E]  Pick up the torch' (%s)" % p_off)
	await _aim_at("torch")
	_check(g.player.hovered == "torch", "the crosshair finds the torch on the shelf (hovered=%s)" % g.player.hovered)
	await _act("interact")
	var held: bool = g.player.torch_held and g.player.torch_light != null and g.player.torch_light.visible
	var gone: bool = g.station.torch_taken and g.station._torch_nodes.all(func(n): return not n.visible)
	_check(held and gone and not g.station._torch_nodes.is_empty(), "E takes the torch: the beam is on and the shelf torch is gone (%d meshes)" % g.station._torch_nodes.size())
	await _act("torch")
	var off: bool = not g.player.torch_light.visible
	await _act("torch")
	_check(off and g.player.torch_light.visible, "F switches the torch off and on again")
	_check(g.player.torch_light.shadow_enabled and g.player.torch_light.spot_range >= 8.0, "the beam casts shadows and reaches across the room")
	_check(bool(g.save_dict()["player"].get("torch", false)), "the save remembers the keeper has the torch")
	g._route(g.sim.set_breaker("lights", true))
	# g) repeated sequences always come back to free-walk mouse look
	var bad: Array = []
	for i in 4:
		g.player.enter_focus("radio")
		await _frames(30)
		await _settle_focus()
		_choices("radio")
		await _frames(2)
		_key(KEY_1)
		await _frames(2)
		g.player.leave_focus()
		await _frames(30)
		await _settle_focus()
		if not g.mouse_should_capture():
			bad.append("radio#%d" % i)
		g._on_doc("chart")
		await _frames(4)
		await _act("pause")                       # Esc closes the chart, never pauses under it
		if g._paused or g.presenter.is_document_open() or not g.mouse_should_capture():
			bad.append("chart#%d" % i)
		await _act("pause")                       # Esc pauses ...
		if paused:
			g.set_paused(false)                   # ... and main_fp resumes on Esc under pause (not loaded here)
		await _frames(2)
		if g._paused or not g.mouse_should_capture():
			bad.append("pause#%d" % i)
		g.player.enter_focus("console")
		await _frames(30)
		await _settle_focus()
		await _act("pause")                       # Esc steps back out of the view
		await _frames(30)
		if g.player.focused != "" or not g.mouse_should_capture():
			bad.append("console#%d" % i)
		if dlg.is_active():
			dlg.close()
	_check(bad.is_empty(), "4 rounds of radio, chart, pause and console all return to mouse look (failures: %s)" % [bad])
	if DisplayServer.get_name() == "headless":
		skips.append("R8 real Input.mouse_mode after the loop (headless)")
	else:
		_check(Input.mouse_mode == Input.MOUSE_MODE_CAPTURED, "after the loop the pointer is captured (mode %d)" % Input.mouse_mode)


func _choices(mode: String) -> void:
	dlg.show_line({"mode": mode, "speaker": "MORAG" if mode == "radio" else "VISITOR",
		"text": "North Point, Stornoway Coastguard. Are you receiving, Callum? Over." if mode == "radio" else "Evening, keeper."})
	dlg.show_choices({"choices": [{"index": 0, "text": "Receiving you, Morag. All quiet here. Over."},
		{"index": 1, "text": "Go ahead, Stornoway. Over."}]})
	dlg._choice_age = 9.0          # past the 0.4 s anti-accident guard (item 25; checked on its own in R10)


func _r1_mouse() -> void:
	print("R1 mouse restore after a reply")
	var headless := DisplayServer.get_name() == "headless"
	var picked := []
	var cb := func(i): picked.append(i)
	dlg.choice_made.connect(cb)
	# a) free-walk, person mode (the ch4 door scene)
	g.refresh_mouse()
	_check(g.mouse_should_capture(), "free-walk wants mouse-look before dialogue")
	_choices("person")
	await _frames(2)
	_check(dlg.has_open_choices(), "person choices are shown")
	# cabin pass (Daniel 2026-11-05): replies no longer free the pointer in free walk (IMG_3140)
	_check(g.mouse_should_capture(), "open choices keep mouse-look in free walk")
	_key(KEY_1)
	await _frames(2)
	_check(picked == [0], "key 1 picks the first reply (got %s)" % [picked])
	_check(not dlg.has_open_choices(), "choices close after the pick")
	_check(g.mouse_should_capture(), "mouse-look wanted again after the pick")
	if headless:
		skips.append("R1 Input.mouse_mode checks (headless)")
	else:
		_check(Input.mouse_mode == Input.MOUSE_MODE_CAPTURED, "Input.mouse_mode is CAPTURED after the pick")
	dlg.close()
	# b) inside the radio device view the cursor must stay free after a pick, and the number key must
	#    pick the reply WITHOUT also sending a radio order (both layers listen to 1-6)
	picked.clear()
	var orders := [0]
	var co := func(_s, _c): orders[0] += 1
	g.ui.command_requested.connect(co)
	g.ui.selected_ship = 999          # any id: sim.command answers "no answer" for unknown ships
	g.player.enter_focus("radio")
	await _frames(2)
	await _settle_focus()
	_choices("radio")
	await _frames(2)
	_check(dlg.has_open_choices(), "radio choices unlocked inside the radio view")
	await _after_vessel_refresh()
	g.ui.selected_ship = 999
	_key(KEY_2)
	await _frames(1)
	_check(picked == [1], "key 2 picks the second reply (got %s)" % [picked])
	_check(orders[0] == 0, "picking a reply sends no radio order (orders=%d)" % orders[0])
	await _after_vessel_refresh()
	g.ui.selected_ship = 999          # re-set: _refresh_vessels clears it every 30 frames (no ships)
	_key(KEY_3)
	await _frames(1)
	_check(orders[0] == 1, "with no replies open, key 3 sends a radio order (orders=%d)" % orders[0])
	g.set_paused(true)
	await _after_vessel_refresh()
	g.ui.selected_ship = 999
	_key(KEY_4)
	await _frames(1)
	_check(orders[0] == 1, "no radio orders under pause (orders=%d)" % orders[0])
	g.set_paused(false)
	g.ui.command_requested.disconnect(co)
	g.ui.selected_ship = -1
	_check(not g.mouse_should_capture(), "device view keeps the cursor free after a pick")
	if not headless:
		_check(Input.mouse_mode == Input.MOUSE_MODE_VISIBLE, "Input.mouse_mode stays VISIBLE in the device view")
	# c) unpausing with choices open must not capture the mouse (buttons would become unclickable)
	_choices("radio")
	await _frames(2)
	g.player.leave_focus()
	await _frames(2)
	await _settle_focus()
	g.set_paused(true)
	g.set_paused(false)
	_check(g.mouse_should_capture(), "leaving the radio view with replies open gives mouse-look back (no stuck pointer)")
	_check(not dlg.has_open_choices() or not g._at_radio(), "radio replies hide once the keeper is away from the handset")
	dlg.close()
	dlg.choice_made.disconnect(cb)
	await _frames(2)


func _r2_overlap() -> void:
	print("R2 choices vs radio command panel")
	g.player.enter_focus("radio")
	await _frames(2)
	await _settle_focus()
	_choices("radio")
	await _frames(2)
	var sizes := [Vector2i(1920, 1080), Vector2i(1280, 720), Vector2i(1920, 1200), Vector2i(1440, 1080), Vector2i(2560, 1080)]
	for s in sizes:
		root.size = s
		await _frames(3)
		var panel: Control = g.ui.radio_panel
		var box: Control = dlg.choice_box
		var vp := box.get_viewport_rect()
		var a := box.get_global_rect()
		var b := panel.get_global_rect()
		var speech: Rect2 = dlg.radio_panel.get_global_rect()
		var tag := "%dx%d (canvas %dx%d)" % [s.x, s.y, vp.size.x, vp.size.y]
		_check(panel.visible and box.get_child_count() > 0, "%s both visible" % tag)
		_check(not a.intersects(b), "%s choices %s clear of command panel %s" % [tag, a, b])
		_check(not a.intersects(speech), "%s choices clear of the speech panel" % tag)
		_check(vp.encloses(a), "%s choices fully on screen" % tag)
	root.size = Vector2i(1920, 1080)
	if DisplayServer.get_name() != "headless":      # visual evidence for the checkpoint
		await _frames(45)                           # let the focus camera ease in and the text type out
		dlg._shown = dlg._full.length()
		dlg._render()
		await _frames(3)
		var out := ProjectSettings.globalize_path("res://").path_join("../../../../renders/last_light").simplify_path()
		DirAccess.make_dir_recursive_absolute(out)
		root.get_texture().get_image().save_png(out.path_join("s0_regress_reply_layout.png"))
		print("  saved s0_regress_reply_layout.png")
	dlg.close()
	g.player.leave_focus()
	await _frames(2)
	await _settle_focus()


func _r3_pause() -> void:
	print("R3 input under pause")
	var adv := [0]
	var picks := [0]
	var ca := func(): adv[0] += 1
	var cc := func(_i): picks[0] += 1
	dlg.advance_requested.connect(ca)
	dlg.choice_made.connect(cc)
	dlg.show_line({"mode": "person", "speaker": "VISITOR", "text": "A long line that the typewriter should still be revealing when the keeper pauses the game."})
	await _frames(2)
	g.set_paused(true)
	await _frames(2)
	var shown_before: float = dlg._shown
	for i in 3:
		_key(KEY_E)
		await _frames(3)
	await _frames(20)
	_check(adv[0] == 0, "E under pause does not advance (advances=%d)" % adv[0])
	_check(is_equal_approx(dlg._shown, shown_before), "typewriter frozen under pause (%.1f -> %.1f)" % [shown_before, dlg._shown])
	_check(dlg._shown < dlg._full.length(), "E under pause does not complete the line")
	_choices("person")
	await _frames(2)
	_key(KEY_1)
	await _frames(3)
	dlg._pick(0)                     # a mouse click on a button under the pause menu reaches _pick
	await _frames(2)
	_check(picks[0] == 0, "choices cannot be picked under pause (picks=%d)" % picks[0])
	g.set_paused(false)
	await _frames(2)
	_key(KEY_1)
	await _frames(3)
	_check(picks[0] == 1, "after unpause key 1 picks (picks=%d)" % picks[0])
	dlg.advance_requested.disconnect(ca)
	dlg.choice_made.disconnect(cc)
	dlg.close()


## R4 (Stage 1 s1f): narration inside a radio conversation is the keeper thinking. It must be drawn as an
## italic thought subtitle, not as a radio call with a blank identity card and a live signal meter.
func _r4_thought_in_radio() -> void:
	dlg.show_line({"mode": "radio", "speaker": "", "text": "Static. Then nothing. Not even the carrier."})
	await _frames(2)
	_check(not dlg.radio_panel.visible, "radio narration does not open the radio panel")
	_check(dlg.sub_box.visible and dlg.s_text.text.contains("[i]"), "radio narration is an italic subtitle")
	_check(dlg.s_name.text == "", "radio narration has no speaker name")
	_check(dlg.mode == "radio", "the conversation stays a radio conversation (reply gating)")
	dlg.show_line({"mode": "radio", "speaker": "MORAG", "text": "North Point, Stornoway. Over."})
	await _frames(2)
	_check(dlg.radio_panel.visible and not dlg.sub_box.visible, "the next radio line opens the radio panel again")
	dlg.close()
	# the handset hint lives in the radio panel, so radio replies must never follow narration directly
	var db := DialogueDB.new()
	db.load_dir("res://data/story")
	var bad: Array = []
	for id in db.convs:
		var c: Dictionary = db.convs[id]
		if c["mode"] != "radio":
			continue
		var last_narr := false
		for st in c["steps"]:
			if st["kind"] == "line":
				last_narr = st["speaker"] == ""
			elif st["kind"] == "choice":
				if last_narr:
					bad.append(id)
				last_narr = false
			elif st["kind"] == "goto":
				last_narr = false
	_check(bad.is_empty(), "no radio replies directly after narration (the handset hint would be hidden): %s" % [bad])


## Stage 3A: dialogue and typography foundation.
func _r9_dialogue_foundation() -> void:
	print("R9 dialogue foundation")
	var st_node: Node = root.get_node("Settings")
	if dlg.is_active():
		dlg.close()
	# --- fonts: bundled files, a genuine italic face
	var serif_base: Font = (UIStyle.serif() as FontVariation).base_font
	var ital_base: Font = (UIStyle.serif_italic() as FontVariation).base_font
	_check(serif_base is FontFile and ital_base is FontFile and serif_base != ital_base,
		"serif and its italic are bundled font files (%s / %s)" % [serif_base, ital_base])
	_check(dlg.s_text.get_theme_font("italics_font") == UIStyle.serif_italic(), "subtitle italics use the italic face")
	for f in [UIStyle.sans(), UIStyle.typewriter(), UIStyle.hand()]:
		_check((f as FontVariation).base_font is FontFile, "bundled font loads: %s" % (f as FontVariation).base_font.resource_path.get_file())
	# --- parser: presence tags, expressions, sound captions
	var db := DialogueDB.new()
	db.parse_text("""== r9a mode=radio
ROSS: That's my girl.
MORAG(worried): Mayday received.
~ A thought.
> Three slow knocks.
ROSS@radio: On the handset.
== r9b mode=thought
VISITOR: Callum! Open the door.
== r9c mode=person
Ross said: not a speaker line
""", "r9")
	_check(db.errors.size() == 1 and String(db.errors[0]).contains("cannot parse"), "only the lower-case 'Ross said:' line is rejected (%s)" % [db.errors])
	_check(String(db.convs["r9a"]["steps"][1]["expr"]) == "worried" and db.convs["r9a"]["steps"][1]["speaker"] == "MORAG", "MORAG(worried): parses with its expression")
	# --- runner: resolved speaker, looks, history
	var stt := StoryState.new()
	var run := DialogueRunner.new(db, stt)
	run.start("r9a")
	var looks: Array = []
	var names: Array = []
	for i in 5:
		var it: Dictionary = run.advance()
		looks.append(it["look"])
		names.append(it["name"])
	_check(looks == ["person", "radio", "thought", "sound", "radio"], "looks: in-room / radio / thought / sound / @radio (%s)" % [looks])
	_check(names[0] == "The man at the door" and not "Alasdair Ross" in names, "Ross is the man at the door before his name (%s)" % [names])
	var hist_txt := JSON.stringify(stt.history)
	_check(not hist_txt.contains("ROSS") and not hist_txt.contains("Alasdair"), "history keeps the name as shown (no ROSS before the reveal)")
	_check(int(stt.history[0].get("chapter", 0)) == stt.chapter and String(stt.history[0].get("conv", "")) == "r9a", "history entries carry chapter and conversation")
	stt.flags["knows_name"] = 1
	run.start("r9a")
	_check(String(run.advance()["name"]) == "Alasdair Ross", "after knows_name the same line is Alasdair Ross")
	run.start("r9b")
	_check(String(run.advance()["look"]) == "person", "a named speaker inside a thought scene is a person subtitle, not Callum's thought")
	var legacy := Speakers.sanitize_history([{"speaker": "ROSS", "text": "x", "mode": "person"}], stt)
	_check(String(legacy[0]["name"]) == "The man at the door" and String(legacy[0]["speaker"]) == "VISITOR", "pre-3A saves: raw ROSS entries are rewritten as shown")
	# --- dialogue UI: names and the identity line
	dlg.show_line({"mode": "radio", "speaker": "MORAG", "text": "North Point, Stornoway. Over."})
	await _frames(2)
	_check(dlg.r_name.text == "Morag Fraser" and dlg.r_ident.text.contains("STORNOWAY COASTGUARD"), "radio name row carries the identity line (%s | %s)" % [dlg.r_name.text, dlg.r_ident.text])
	_check(dlg.r_ident.get_theme_font_size("font_size") >= 15, "identity line is at least 15 px (was a 9-10 px drawing)")
	dlg.show_line({"mode": "radio", "speaker": "ROSS", "text": "That's my girl."})
	await _frames(2)
	_check(dlg.sub_box.visible and dlg.s_name.text == "The man at the door", "an unresolved ROSS item still shows only the man at the door (%s)" % dlg.s_name.text)
	dlg.show_line({"mode": "person", "speaker": "", "text": "He waits."})
	_check(dlg.s_text.text.contains("[i]"), "person-scene narration is an italic thought")
	dlg.show_line({"type": "line", "mode": "person", "speaker": "", "name": "", "look": "sound", "text": "Three slow knocks."})
	_check(dlg.s_text.text.contains("THREE SLOW KNOCKS") and dlg.s_name.text == "", "sound caption in capitals, no name")
	dlg.show_line({"type": "line", "mode": "person", "speaker": "", "name": "", "look": "sound", "text": "[A carrier on Channel 16. Two clicks.]"})
	_check(dlg.s_text.text.count("[lb]") == 1, "a caption already in brackets in the script is not double-bracketed (%s)" % dlg.s_text.text)
	# --- typewriter: laid out once, waits behind a fade and a document
	var long := "The bolt is stiff with salt. The door comes in with the storm behind it, and an old man in an oilskin stands on the top step with one hand on the rail and rain running off the brim of his sou'wester."
	dlg.show_line({"mode": "person", "speaker": "VISITOR", "text": long})
	await _frames(3)
	var h0: float = dlg.s_text.size.y
	dlg._shown = dlg._full.length()
	dlg._render()
	await _frames(2)
	_check(absf(dlg.s_text.size.y - h0) < 1.0, "the subtitle block keeps its height while typing (%.0f -> %.0f px)" % [h0, dlg.s_text.size.y])
	dlg.show_line({"mode": "person", "speaker": "VISITOR", "text": long})
	g.presenter.fade.color.a = 1.0
	await _frames(20)
	_check(dlg._shown < 1.0, "nothing types while the screen is black (%.1f chars)" % dlg._shown)
	g.presenter.fade.color.a = 0.0
	await _frames(30)
	_check(dlg._shown > 1.0, "typing resumes when the fade lifts (%.1f chars)" % dlg._shown)
	g.presenter.open_document("forecast")
	await _frames(2)
	var s0: float = dlg._shown
	await _frames(20)
	_check(is_equal_approx(dlg._shown, s0), "the typewriter waits while a document is open")
	g.presenter.close_document()
	g.player.enabled = true
	g.refresh_mouse()
	dlg.close()
	# --- duty line tokens and one text scale (G2b: the HUD layout itself is R13 in _r12_brief_g2)
	g.presenter.set_objective("Get your bearings. Walk with {move}; look around with {look}.")
	_check(not g.presenter.objective.text.contains("{"), "duty line tokens resolve (%s)" % g.presenter.objective.text)
	for sc in [0.8, 1.0, 1.5]:
		st_node.v["subtitle_size"] = sc
		st_node.apply()
		await _frames(3)
		_check(g.presenter.objective.get_theme_font_size("font_size") == UIStyle.px(21) and g.presenter.card_title.get_theme_font_size("font_size") == UIStyle.px(64)
			and g.ui.notice.get_theme_font_size("font_size") == UIStyle.px(24), "x%.1f duty line, chapter card and notices follow the text size" % sc)
	st_node.v["subtitle_size"] = 1.0
	st_node.apply()
	g.presenter.set_objective("")
	# --- dialogue history: pauses, never advances, keeps the mouse owner and the pad focus
	var adv := [0]
	var ca := func(): adv[0] += 1
	dlg.advance_requested.connect(ca)
	g.director.state.history.append({"speaker": "VISITOR", "name": "The man at the door", "text": "Evening, keeper.", "look": "person", "chapter": 4, "clock": "02:51"})
	_choices("person")
	await _frames(3)
	InputSetup.pad_active = true
	dlg._pad_focus()
	await _frames(2)
	(dlg.choice_box.get_child(1) as Control).grab_focus()
	var focus_before: Control = g.get_viewport().gui_get_focus_owner()
	var mouse_before: bool = g.mouse_should_capture()
	await _act("history")
	await _frames(3)
	_check(g.backlog.visible and g.get_tree().paused and not g.mouse_should_capture(), "H / View opens the history, pauses and frees the pointer")
	_check(g.backlog.text.text.contains("The man at the door") and not g.backlog.text.text.contains("Alasdair"), "the history shows names as they were shown")
	for i in 3:
		_key(KEY_E)
		await _frames(3)
	_key(KEY_1)
	await _frames(3)
	_check(adv[0] == 0 and dlg.has_open_choices(), "E and 1 under the history neither advance nor answer")
	await _act("history")
	await _frames(3)
	_check(not g.backlog.visible and not g.get_tree().paused and g.mouse_should_capture() == mouse_before, "H closes it: play resumes, mouse policy as before")
	_check(g.get_viewport().gui_get_focus_owner() == focus_before, "the highlighted reply is still highlighted for the pad")
	InputSetup.pad_active = false
	g.set_paused(true)
	await _frames(2)
	g.ui.backlog_requested.emit()
	await _frames(2)
	_check(g.backlog.visible and g.ui.pause_panel != null and not g.ui.pause_panel.visible, "pause menu > Dialogue history opens over the pause menu")
	g.close_backlog()
	await _frames(2)
	_check(not g.backlog.visible and g.get_tree().paused and g.ui.pause_panel.visible, "closing it returns to the pause menu, still paused")
	g.set_paused(false)
	await _frames(2)
	dlg.advance_requested.disconnect(ca)
	dlg.close()
	# the history must never write the mouse mode (R8's single-owner rule)
	var src := FileAccess.get_file_as_string("res://scripts/ui/backlog_ui.gd")
	_check(not src.contains("mouse_mode"), "backlog_ui never touches Input.mouse_mode")


## Stage 3B: the narrative mechanics behind the approved script (STAGE3_NARRATIVE_MASTER §18).
func _r10_narrative_mechanics() -> void:
	print("R10 narrative mechanics (Stage 3B)")
	# --- a) the story jam: binds on the tooth in any mode, no MAIN trip, survives a power loss (ch2 race)
	var k := KeeperSim.new()
	k.setup(KeeperConfig.new(), LayoutData.load_file(), {"ships": [], "faults": []}, 3)
	k.story_mode = true
	k.battery = 90
	k.set_mode(KeeperSim.Mode.AUTO)
	k.set_intensity(1)
	var ev := k.trigger_fault("jam", ["story"])
	_check(k.jammed and k.story_jam and ev.size() == 1 and absf(rad_to_deg(k.bearing) - 46.0) < 0.5,
		"a story jam binds at once with the repeater on 046 (%.1f°)" % rad_to_deg(k.bearing))
	var cleared := false
	for i in 600:                                   # 10 s in AUTO
		for e in k.step(1.0 / 60.0):
			cleared = cleared or e["type"] == "jam_cleared"
	_check(k.main_breaker and k.jammed and not cleared, "10 s jammed in AUTO: MAIN does not trip, the jam holds")
	k.trigger_fault("trip")
	for i in 120:
		for e in k.step(1.0 / 60.0):
			cleared = cleared or e["type"] == "jam_cleared"
	_check(k.jammed and not cleared, "losing MAIN does not clear a story jam (the ch2 race)")
	k.set_breaker("main", true)
	k.set_mode(KeeperSim.Mode.MANUAL)
	var b0 := k.bearing
	k.set_wheel(1.0)
	for i in 120:
		k.step(1.0 / 60.0)
	_check(absf(k.bearing - b0) < 0.001, "MANUAL on the tooth: the handwheel is rigid")
	k.set_mode(KeeperSim.Mode.OFF)
	for i in 120:
		k.step(1.0 / 60.0)
	_check(k.jammed and absf(k.bearing - b0) < 0.001, "OFF: the wheel will not drive her forward past the tooth")
	k.set_wheel(-1.0)
	for i in 240:
		for e in k.step(1.0 / 60.0):
			cleared = cleared or (e["type"] == "jam_cleared")
	_check(cleared and not k.jammed and rad_to_deg(k.bearing) < 46.0 - k.cfg.jam_back_deg + 0.5,
		"backing the handwheel past the tooth frees it (%.1f°)" % rad_to_deg(k.bearing))
	k.set_wheel(0.0)
	# --- b) Ross on the handwheel keeps the beam on the ship in MANUAL (lit_by_hand)
	k.spawn_story_ship({"name": "Iona Star", "kind": "steamer", "bearing": 66, "aim": 30, "speed_mul": 0.55, "hold": true, "protected": true,
		"range": 150.0})                              # inside the hand beam's reach
	var st := StoryState.new()
	st.sim = k
	k.set_mode(KeeperSim.Mode.MANUAL)
	k.assist = true
	for i in 360:
		k.step(1.0 / 60.0)
	_check(st.lit_by_hand("Iona Star"), "Ross assist: the beam is held on the Iona Star in MANUAL")
	k.set_mode(KeeperSim.Mode.AUTO)
	_check(not st.lit_by_hand("Iona Star"), "the assist is only a MANUAL thing")
	# --- c) transitions hold the story; nothing types or advances under black
	var d: StoryDirector = g.director
	d._do(["timeskip", 1110, "18:30"])
	_check(d.is_held(), "a timeskip holds the story")
	dlg.show_line({"mode": "person", "speaker": "MORAG", "text": "This line must wait for the fade to lift."})
	await _frames(70)                                 # the screen is black by now (1.0 s fade)
	_key(KEY_E)
	await _frames(3)
	_check(g.presenter.fade.color.a > 0.5 and dlg._shown < 1.0, "under black: no typing, and E does not finish the line")
	var t := 0
	while d.is_held() and t < 400:
		await process_frame
		t += 1
	_check(not d.is_held() and g.presenter.fade.color.a < 0.05, "the hold is released when the fade has lifted (%d frames)" % t)
	dlg.close()
	# --- d) the ending card: title, the lines one by one, Space moves it on (G6a: never E), then it releases
	var lines := ["The Board opened a new inquiry in the spring.", "North Point Light. Fifteenth of November, nineteen seventy-one.", "The light was kept."]
	var done := [false]
	g.presenter.show_ending("correction", "Correction", lines)
	await _frames(5)
	_check(g.presenter.ending_root.visible and g.presenter.is_screen_held(), "the ending card covers the screen and holds dialogue")
	_check(g.presenter.ending_title.text.begins_with("C O R R E C T I O N"), "the title is set in spaced capitals (%s)" % g.presenter.ending_title.text)
	t = 0
	while g.presenter.is_ending_open() and t < 2400:
		if t > 30 and t % 25 == 0:
			_key(KEY_SPACE)
		await process_frame
		t += 1
	_check(not g.presenter.is_ending_open() and g.presenter.ending_box.get_child_count() == lines.size(),
		"every epilogue line was shown, then the card released (%d frames)" % t)
	g.presenter.ending_root.visible = false
	g.presenter.ending_bg.color.a = 0.0
	g.presenter.dialogue.visible = true
	# --- e) optional calls: offered between their beats, deferring the next beat's talk until they end
	var k2 := KeeperSim.new()
	k2.setup(KeeperConfig.new(), LayoutData.load_file(), {"ships": [], "faults": []}, 5)
	k2.story_mode = true
	var d2 := StoryDirector.new()
	root.add_child(d2)
	d2.setup(k2, true)
	d2.state.chapter = 2
	d2.state.beat = 4                                  # second_call: wait 8, then the Mary Ellen talks
	d2._enter_beat()
	var ids: Array = d2.available_calls().map(func(c): return String(c["id"]))
	_check(ids.has("opt_ch2_rory") and ids.has("opt_ch2_morag"), "ch2 after Gannet: Rory and Morag can be called (%s)" % [ids])
	d2.state.beat = 6
	_check(d2.available_calls().is_empty(), "the calls close once the archive beat has run")
	d2.state.beat = 4
	_check(d2.request_call("opt_ch2_morag") and d2.optional_running() == "opt_ch2_morag", "a call starts from the panel")
	var convs := {}
	for i in 900:                                     # 15 s: the Mary Ellen would have spoken by now
		d2._process(1.0 / 60.0)
		if d2.is_talking():
			convs[String(d2.runner.conv.get("id", ""))] = true
		if not d2.is_talking() and i > 10:
			break
	_check(not convs.has("ch2_mary_ellen") and d2.state.clue("sister_boat"), "the beat's talk waits for the optional call (%s)" % [convs.keys()])
	for i in 900:
		d2._process(1.0 / 60.0)
		if d2.is_talking():
			convs[String(d2.runner.conv.get("id", ""))] = true
	_check(convs.has("ch2_mary_ellen"), "then the Mary Ellen calls")
	_check(not d2.available_calls().any(func(c): return c["id"] == "opt_ch2_morag"), "a call is offered once")
	d2.queue_free()
	g.director.state.chapter = 2
	g.director.state.beat = 4
	g.ui._refresh_calls()
	_check(g.ui.calls_box.visible and g.ui.calls_list.get_child_count() == 2, "the radio panel lists both calls")
	g.director.state.chapter = 1
	g.director.state.beat = 0
	g.ui._refresh_calls()
	_check(not g.ui.calls_box.visible, "no calls, no 'Call a station' box")
	# --- f) nobody sees "Alasdair Ross" before his name is spoken: ch4 door kept shut, then ch5's first line
	var st3 := StoryState.new()
	var r := DialogueRunner.new(g.director.db, st3)
	r.start("ch4_door")
	var shown: Array = []
	var item := r.advance()
	while item["type"] != "end":
		if item["type"] == "choice":
			var pick := 0
			for c in item["choices"]:
				if "Keep the door shut" in String(c["text"]):
					pick = int(c["index"])
			item = r.choose(pick)
			continue
		if item["type"] == "line":
			shown.append(String(item["name"]))
		item = r.advance()
	r.start("ch5_ross")
	item = r.advance()
	while item["type"] != "line" or String(item["name"]) == "":     # past Callum's opening thought
		item = r.advance()
	var first_name: String = item["name"]                           # "Alasdair Ross. Master of the Mary Ellen..."
	item = r.advance()
	while item["type"] != "line" or String(item["name"]) == "":
		item = r.advance()
	_check(not shown.has("Alasdair Ross") and first_name != "Alasdair Ross" and String(item["name"]) == "Alasdair Ross",
		"his name shows only after he says it (door: %s, ch5: %s -> %s)" % [shown, first_name, item["name"]])
	_check(not JSON.stringify(st3.history.slice(0, -1)).contains("Alasdair Ross\""), "the history never stored the name before it was known")
	# --- g) the bolt, and h) the photograph props
	var gs: StoryState = g.director.state
	gs.chapter = 4
	gs.beat = 2
	g.station.door_open = false
	g._use_door()
	await _frames(2)
	_check(gs.has_flag("bolted") and g.director.is_talking(), "drawing the bolt sets `bolted` and says so")
	g.director._talking = false
	dlg.close()
	gs.flags.erase("bolted")
	gs.clues["photo_1953"] = true
	g._update_story_props()
	_check(g.station.story_prop_shown("photo53") and not g.station.story_prop_shown("photo53desk"), "door kept shut: the photograph lies inside the door")
	gs.clues.erase("photo_1953")
	gs.flags["door_open"] = 1
	gs.chapter = 5
	g._update_story_props()
	_check(g.station.story_prop_shown("photo53desk") and not g.station.story_prop_shown("photo53"), "door opened: from ch5 he has left it on the desk")
	gs.flags.erase("door_open")
	gs.chapter = 1
	gs.beat = 0
	g._update_story_props()



func _r11_brief_g1() -> void:
	print("R11 brief G1: input split, guards, card order, radar, comms")
	g.player.leave_focus()
	await _settle_focus()
	# a) E while a line is up: the line neither finishes nor advances, and the press is not swallowed
	var adv := [0]
	var ca := func(): adv[0] += 1
	dlg.advance_requested.connect(ca)
	dlg.show_line({"mode": "person", "speaker": "VISITOR", "text": "A line long enough to still be typing when the keeper presses E."})
	await _frames(2)
	await _act("interact")
	_check(adv[0] == 0 and dlg._shown < dlg._full.length(), "E does not finish or advance a dialogue line (item 7)")
	var dsrc := FileAccess.get_file_as_string("res://scripts/ui/dialogue_ui.gd")
	_check(not dsrc.contains('is_action_pressed("interact")'), "the dialogue layer never reads the interact action, so E always reaches the player")
	# b) Space: the first press finishes the line; a second press inside the dwell does nothing; after it, advances
	_key(KEY_SPACE)
	await _frames(1)
	_check(dlg._shown >= dlg._full.length() and adv[0] == 0, "Space finishes the typewriter first")
	_key(KEY_SPACE)
	await _frames(1)
	_check(adv[0] == 0, "a second Space inside %.1f s does not skip the line" % dlg.ADVANCE_DWELL_S)
	dlg._done_t = dlg.ADVANCE_DWELL_S + 0.1
	_key(KEY_SPACE)
	await _frames(1)
	_check(adv[0] == 1, "Space advances once the full line has been up long enough")
	dlg.advance_requested.disconnect(ca)
	dlg.close()
	# c) replies ignore input in their first moments
	var picked := [-1]
	var cp := func(i): picked[0] = i
	dlg.choice_made.connect(cp)
	dlg.show_line({"mode": "person", "speaker": "VISITOR", "text": "Evening, keeper."})
	dlg.show_choices({"choices": [{"index": 0, "text": "Who's there?"}, {"index": 1, "text": "Say nothing."}]})
	_key(KEY_1)
	await _frames(1)
	_check(picked[0] == -1, "a number key in the replies' first 0.4 s is ignored (item 25)")
	dlg._choice_age = 1.0
	_key(KEY_1)
	await _frames(1)
	_check(picked[0] == 0, "after the guard, key 1 answers")
	dlg.choice_made.disconnect(cp)
	dlg.close()
	# d) the clock card draws above the black, and is fully up on black for at least CARD_ON_BLACK_S
	var pr: CanvasLayer = g.presenter
	_check(pr.card.get_index() > pr.fade.get_index(), "the clock / chapter card draws above the fade (item 21)")
	pr.timeskip("19:40")
	var on_black_ms := 0
	var last := Time.get_ticks_msec()
	var t := 0
	while t < 2000 and (pr.fade.color.a > 0.02 or t < 5):
		await process_frame
		var now := Time.get_ticks_msec()
		if pr.fade.color.a > 0.98 and pr.card.modulate.a > 0.98:
			on_black_ms += now - last
		last = now
		t += 1
	_check(pr.card_title.text == "19:40" and on_black_ms >= 1500, "the time skip clock is fully up on black for %d ms (>= 1500)" % on_black_ms)
	g.director._hold = 0
	# e) the radar is its own target and never opens the radio view
	_check(g.station.DEVICES["radar"]["kind"] == "info", "the radar is an info target, not a radio focus (item 23)")
	g.player.focused = ""
	_check(not g._at_radio(), "standing near the radio without the radio view does not answer it")
	# f) sim radio chatter waits while a story line is up, then shows; it is in the transcript either way
	g.director.process_mode = Node.PROCESS_MODE_INHERIT
	var hist0: int = g.director.state.history.size()
	var subs0: int = g.ui._sub_items.size()
	dlg.show_line({"mode": "radio", "speaker": "MORAG", "text": "North Point, Stornoway. Radio check, over."})
	g.sim.battery = maxf(g.sim.battery, 50.0)
	g.sim.main_breaker = true
	g._comms_radio("Kittiwake", "Position bearing 014, North Point.", false, "position", -1)
	await _frames(3)
	_check(g._comms_queue.size() == 1 and g.ui._sub_items.size() == subs0, "a sim radio line waits behind a story line (item 26)")
	_check(g.director.state.history.size() == hist0 + 1, "the sim radio line is in the transcript")
	dlg.close()
	g._comms_gap = 0.0
	await _frames(3)
	_check(g._comms_queue.is_empty() and g.ui._sub_items.size() >= 1, "it shows once the story line has closed")
	g.director.process_mode = Node.PROCESS_MODE_DISABLED


func _button_texts(n: Node) -> Array:
	var out: Array = []
	for c in n.find_children("*", "Button", true, false):
		out.append((c as Button).text)
	return out


func _r12_brief_g2() -> void:
	print("R12 brief G2: pause, feedback, objective panel")
	g.player.leave_focus()
	await _settle_focus()
	# a) the pause menu: no save buttons; Transcript, Options, Main menu
	g.set_paused(true)
	await _frames(2)
	var texts := _button_texts(g.ui.pause_panel)
	var no_save := texts.all(func(t): return not String(t).to_lower().contains("save"))
	var has := ["Resume", "Options", "Main menu"].all(func(w): return texts.any(func(t): return String(t).begins_with(w)))
	_check(no_save and has and texts.any(func(t): return String(t).begins_with("Transcript")), "pause menu: Resume / Transcript / Options / Main menu, no saving (%s)" % [texts])
	var opt := [0]
	var co := func(): opt[0] += 1
	g.options_requested.connect(co)
	for b in g.ui.pause_panel.find_children("*", "Button", true, false):
		if (b as Button).text == "Options":
			(b as Button).pressed.emit()
	await _frames(2)
	_check(opt[0] == 1 and not g.ui.pause_panel.visible, "Options is handed to main_fp and the pause menu steps aside")
	g.options_requested.disconnect(co)
	g.ui.pause_panel.visible = true
	var menu := [0]
	var cm := func(): menu[0] += 1
	g.ui.menu_requested.connect(cm)
	for b in g.ui.pause_panel.find_children("*", "Button", true, false):
		if (b as Button).text == "Main menu":
			(b as Button).pressed.emit()
	await _frames(2)
	_check(menu[0] == 0 and g.ui._confirm_panel != null, "Main menu asks first")
	g.ui.menu_requested.disconnect(cm)
	g.set_paused(false)
	await _frames(2)
	_check(g.ui._confirm_panel == null, "resuming closes the question")
	# b) checking the generator / battery answers with a thought that is kept in the transcript
	g.director.process_mode = Node.PROCESS_MODE_INHERIT
	var h0: int = g.director.state.history.size()
	g.sim.gen = KeeperSim.Gen.OFF
	g.sim.fuel_valve = false
	g.sim.fuel = 30.0
	g._route([{"type": "inspect", "device": "gen_panel"}])
	await _frames(2)
	_check(g.presenter.thought.text.contains("valve") and g.presenter.thought.modulate.a > 0.0 or g.presenter.thought.text.contains("valve"),
		"E on the generator: Callum says the valve is shut (%s)" % g.presenter.thought.text)
	_check(g.director.state.history.size() == h0 + 1, "the check's thought is in the transcript")
	g.sim.battery = 0.0
	_check(g.station.inspect_line("battery").begins_with("Flat"), "a flat battery is called flat")
	g.sim.battery = 80.0
	g.director.process_mode = Node.PROCESS_MODE_DISABLED
	await _r13_duty_hud()
	await _r14_logbook()
	await _r15_equipment()
	await _r16_hands()
	await _r17_body()
	await _r18_cabin_g4a()
	await _r19_ending_g6a()
	await _r20_portraits()
	await _r21_menu_g6c()
	_r22_saves_isolated()


## G3a R15: the hand compass and the binoculars. Desk pickups (nothing before), G / B never shared with
## another key, the compass needle on north within 1 degree at any yaw, the binoculars' 7x view (FOV,
## look sensitivity, mask, the torch out while up and back after), E lowers them first, a device view
## puts everything away, and a save restores what the keeper carries and what's left on the desk.
func _r15_equipment() -> void:
	print("R15 G3a equipment")
	var eq = g.player.equipment
	var st = g.station
	_check(eq != null and eq.compass_node.get_child_count() >= 3 and eq.bino_node.get_child_count() >= 3 and eq.needle != null,
		"the held compass and binoculars are built from the desk props (%d / %d meshes)" % [eq.compass_node.get_child_count(), eq.bino_node.get_child_count()])
	var keys := {}
	var dup := false
	for a in InputSetup.BINDINGS:
		for k in InputSetup.BINDINGS[a]:
			if k in [KEY_G, KEY_B]:
				dup = dup or keys.has(k)
				keys[k] = a
	_check(not dup and keys.get(KEY_G, "") == "compass" and keys.get(KEY_B, "") == "binoculars", "G and B belong to the compass and binoculars only")
	g.player.leave_focus()
	await _settle_focus()
	for id in ["compass", "binoculars"]:
		eq.has[id] = false
		st.set_item_taken(id, false)
	var r: Dictionary = eq.toggle("compass")
	_check(not r["ok"] and r["reason"].contains("chart") and eq.held == "", "no compass before it is taken from the chart (%s)" % r["reason"])
	var cia: Node3D = st._ia_bodies["compass"]          # aimed at the compass on the chart, the compass wins
	var org: Vector3 = cia.global_position + Vector3(0.0, 0.9, 0.6)
	var hit: String = g.player.pick(g.player.get_world_3d().direct_space_state, org, (cia.global_position - org).normalized(), 2.5)
	var seen: Array = []
	var ex: Array[RID] = []
	for i in 6:
		var q := PhysicsRayQueryParameters3D.create(org, org + (cia.global_position - org).normalized() * 2.5, 1 << 1, ex)
		var h: Dictionary = g.player.get_world_3d().direct_space_state.intersect_ray(q)
		if h.is_empty():
			break
		ex.append(h["rid"])
		seen.append("%s@%.2f(L%d)" % [h["collider"].get_meta("ia", "?"), org.distance_to(h["position"]), h["collider"].collision_layer])
	_check(hit == "compass", "looking at the compass on the chart targets the compass, not the chart (%s; ray: %s; compass layer %d)" % [hit, seen, cia.collision_layer])
	g._route([{"type": "pickup", "item": "compass"}, {"type": "pickup", "item": "binoculars"}])
	await _frames(2)
	var props_hidden: bool = st._item_nodes.get("compass", []).all(func(n): return not n.visible) \
		and st._item_nodes.get("binoculars", []).all(func(n): return not n.visible)
	_check(eq.has["compass"] and eq.has["binoculars"] and props_hidden and st._ia_bodies["compass"].collision_layer == 0
		and g.director.state.has_flag("took_compass"), "taking them hides the desk props and marks them taken")
	eq.toggle("compass")
	await create_timer(0.4).timeout
	var worst := 0.0
	for yaw in [0.0, 0.7, 1.9, 3.1, -2.4, -0.9]:
		g.player._yaw = yaw
		g.player._apply_look()
		await _frames(2)
		worst = maxf(worst, eq.point_needle(eq.needle))
	_check(eq.compass_node.visible and worst < 1.0, "the compass is in hand and its needle points north within 1 deg at every yaw (worst %.2f)" % worst)
	var desk_err: float = eq.point_needle(st.parts["PT_compass_needle"]["node"])
	_check(desk_err < 1.0, "the desk compass's needle points north too (%.2f deg)" % desk_err)
	# binoculars: torch on first, so we can see it go out and come back
	g.player.give_torch(true)
	eq.toggle("binoculars")
	await create_timer(0.6).timeout
	var cam: Camera3D = g.player.camera
	_check(eq.held == "binoculars" and absf(cam.fov - Equipment.BINO_FOV) < 0.6 and eq.mask.visible and not g.player.torch_light.visible
		and absf(eq.look_scale() - Equipment.BINO_FOV / float(root.get_node("Settings").v["fov"])) < 0.01,
		"binoculars up: FOV %.1f, mask on, torch out, look x%.3f" % [cam.fov, eq.look_scale()])
	var ev := InputEventAction.new()
	ev.action = "interact"
	ev.pressed = true
	g.player._unhandled_input(ev)
	await create_timer(0.6).timeout
	_check(eq.held == "" and absf(cam.fov - float(root.get_node("Settings").v["fov"])) < 0.6 and not eq.mask.visible and g.player.torch_light.visible,
		"E lowers the binoculars first; the view, mask and torch are back (FOV %.1f)" % cam.fov)
	eq.toggle("compass")
	g.player.enter_focus("radio")
	await _settle_focus()
	_check(eq.held == "", "a device view puts the compass away")
	g.player.leave_focus()
	await _settle_focus()
	eq.toggle("compass")
	var d: Dictionary = g.save_dict()
	eq.has = {"compass": false, "binoculars": false}
	eq.held = ""
	st.set_item_taken("compass", false)
	st.set_item_taken("binoculars", false)
	g._apply_save(d)
	await _frames(2)
	_check(eq.has["compass"] and eq.has["binoculars"] and eq.held == "compass" and st.items_taken.get("compass", false)
		and st._item_nodes.get("binoculars", []).all(func(n): return not n.visible), "a save restores the kit in hand and the empty desk")
	eq.put_away_now()


## G3b R16: the keeper's hands. hands.glb gives two 16-bone hands and the four grip poses each; no hands
## with nothing in them; the compass in the left hand, the torch (once it's on) in the right with its beam
## leaving from the lens (kept inside the capsule), both hands on the binoculars while raising and none at
## the eyes; each hand reaches its pose; nothing of a hand near the eye or inside the near plane; a device
## view hides them.
func _pose_err(eq, side: String, pose: String) -> float:
	var worst := 0.0
	var target: Dictionary = eq.poses.get(side + "_" + pose, {})
	for bi in target:
		var q: Quaternion = eq.skel[side].get_bone_pose_rotation(bi)
		worst = maxf(worst, rad_to_deg(q.angle_to(target[bi])))
	return worst if not target.is_empty() else 999.0


func _hand_depth(eq, side: String) -> float:
	var cam: Camera3D = g.player.camera
	var sk: Skeleton3D = eq.skel[side]
	var nearest := 99.0
	for bi in sk.get_bone_count():
		var p: Vector3 = cam.global_transform.affine_inverse() * (sk.global_transform * sk.get_bone_global_pose(bi).origin)
		nearest = minf(nearest, -p.z)
	return nearest


## The nearest vertex of a hand's meshes (each rigid to its strongest bone) inside a 10 x 10 cm box round
## the line of sight, as a distance in front of the eye. 1.0 when the box is empty or the hand hidden.
var _eye_verts := 0                        # vertices _eye_clear looked at (a guard: the box test saw the mesh)


func _eye_clear(eq, side: String) -> float:
	if not eq.hand[side].visible:
		return 1.0
	var sk: Skeleton3D = eq.skel[side]
	var to_cam: Transform3D = g.player.camera.global_transform.affine_inverse() * sk.global_transform
	var nearest := 1.0
	for mi in eq.hand[side].find_children("*", "MeshInstance3D", true, false):
		var m: Mesh = (mi as MeshInstance3D).mesh
		var skin: Skin = (mi as MeshInstance3D).skin
		if m == null or skin == null:
			continue
		for s in m.get_surface_count():
			var arr: Array = m.surface_get_arrays(s)
			var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var bones = arr[Mesh.ARRAY_BONES]
			var wts = arr[Mesh.ARRAY_WEIGHTS]
			if bones == null or wts == null or verts.is_empty():
				continue
			var per: int = bones.size() / verts.size()
			for i in range(0, verts.size(), 2):
				var best := 0
				for j in per:
					if wts[i * per + j] > wts[i * per + best]:
						best = j
				var bind: int = bones[i * per + best]
				var bi: int = skin.get_bind_bone(bind)
				if bi < 0:
					bi = sk.find_bone(skin.get_bind_name(bind))
				var p: Vector3 = to_cam * (sk.get_bone_global_pose(bi) * skin.get_bind_pose(bind) * verts[i])
				_eye_verts += 1
				if absf(p.x) < 0.05 and absf(p.y) < 0.05:
					nearest = minf(nearest, -p.z)
	return nearest


func _r16_hands() -> void:
	print("R16 G3b hands")
	var eq = g.player.equipment
	var nb := 0
	for side in ["L", "R"]:
		nb += eq.skel.get(side, Skeleton3D.new()).get_bone_count()
	var want: Array = []
	for side in ["L", "R"]:
		for pose in ["relaxed", "torch", "compass", "binoculars"]:
			want.append(side + "_" + pose)
	_check(nb == 32 and want.all(func(k): return eq.poses.has(k) and not eq.poses[k].is_empty()),
		"hands.glb gives two 16-bone hands and all eight grip poses (%d bones, poses %s)" % [nb, eq.poses.keys()])
	g.player.leave_focus()
	await _settle_focus()
	eq.has = {"compass": true, "binoculars": true}
	eq.put_away_now()
	g.player.give_torch(false)
	await _frames(3)
	var hv: Dictionary = eq.hands_visible()
	_check(not hv["L"] and not hv["R"] and not eq.torch_node.visible, "nothing in hand, no hands (%s)" % hv)
	eq.toggle("compass")
	await create_timer(0.8).timeout
	hv = eq.hands_visible()
	_check(hv["L"] and not hv["R"] and _pose_err(eq, "L", "compass") < 3.0,
		"the compass sits in the left hand, compass grip reached (%.1f deg off); the right hand is empty and hidden" % _pose_err(eq, "L", "compass"))
	g.player.give_torch(true)
	await create_timer(0.8).timeout
	hv = eq.hands_visible()
	var lens: Vector3 = eq.torch_node.transform * Vector3(0.0, 0.12, 0.0)
	var lp: Vector3 = g.player.torch_light.position
	_check(hv["L"] and hv["R"] and eq.torch_node.visible and lp.distance_to(eq._light_pos(lens)) < 0.005
		and _pose_err(eq, "R", "torch") < 3.0,
		"torch on: it's in the right fist (%.1f deg off the grip), the beam leaves from its lens (%s)" % [_pose_err(eq, "R", "torch"), lp])
	# the poses are real curls, not the rest pose: read against the skeleton's own rest (G3b: each action
	# also carried the other hand's rest tracks, and a name-only read took those)
	var mid: int = eq.skel["R"].find_bone("middle_2")
	var curl: float = rad_to_deg(eq.skel["R"].get_bone_pose_rotation(mid).angle_to(eq.skel["R"].get_bone_rest(mid).basis.get_rotation_quaternion()))
	_check(curl > 70.0, "the torch fist is closed: middle finger PIP %.0f deg from rest" % curl)
	# nose to a wall: the lens is past the capsule, the light stays on the near side. A 1 m test wall 0.30 m
	# ahead of the eye (a real one depends on where the bot stands; pipes and rails are thinner than a beam)
	var cam: Camera3D = g.player.camera
	var wall := StaticBody3D.new()
	wall.collision_layer = g.player.collision_mask
	var wcs := CollisionShape3D.new()
	var wbox := BoxShape3D.new()
	wbox.size = Vector3(1.0, 1.0, 0.05)
	wcs.shape = wbox
	wall.add_child(wcs)
	g.add_child(wall)
	wall.global_transform = Transform3D(cam.global_basis, cam.global_position - cam.global_basis.z * 0.325)
	await physics_frame
	await _frames(3)
	var face: Vector3 = wall.global_position + wall.global_basis.z * 0.025       # the face toward the keeper
	var gap: float = (g.player.torch_light.global_position - face).dot(wall.global_basis.z)
	_check(gap > 0.005 and gap < 0.2, "nose to a wall the torch light stays this side of it (%.3f m short of the wall face)" % gap)
	wall.queue_free()
	await physics_frame
	await _frames(2)
	var shallow := 99.0
	for pitch in [-1.45, 1.45]:
		g.player._pitch = pitch
		g.player._apply_look()
		await _frames(3)
		shallow = minf(shallow, minf(_hand_depth(eq, "L"), _hand_depth(eq, "R")))
	_check(shallow > g.player.camera.near + 0.02, "no hand bone inside the near plane at either pitch limit (nearest %.3f m, near %.2f)" % [shallow, g.player.camera.near])
	_eye_verts = 0
	var clear := minf(_eye_clear(eq, "L"), _eye_clear(eq, "R"))
	_check(clear > 0.05 and _eye_verts > 1000, "compass and torch hands: no skin or sleeve within 5 cm of the eye in front of the face (nearest %.3f m, %d vertices)" % [clear, _eye_verts])
	g.player._pitch = -0.08
	g.player._apply_look()
	eq.toggle("binoculars")
	eq.hold_raise = 0.45                       # held halfway up: both hands on the barrels
	await create_timer(0.6).timeout
	hv = eq.hands_visible()
	clear = minf(_eye_clear(eq, "L"), _eye_clear(eq, "R"))
	_check(hv["L"] and hv["R"] and not eq.torch_node.visible and _pose_err(eq, "L", "binoculars") < 3.0 and _pose_err(eq, "R", "binoculars") < 3.0
		and clear > 0.05, "raising the binoculars: a hand on each barrel (%.1f / %.1f deg off), the torch away, the eye clear (%.3f m)"
		% [_pose_err(eq, "L", "binoculars"), _pose_err(eq, "R", "binoculars"), clear])
	eq.hold_raise = 0.5                        # at arm's length: in view, before the zoom
	await create_timer(0.3).timeout
	var cam_b: Camera3D = g.player.camera
	_check(cam_b.is_position_in_frustum(eq.bino_node.global_position) and absf(cam_b.fov - float(root.get_node("Settings").v["fov"])) < 0.5
		and eq.hands_visible()["L"] and eq.hands_visible()["R"],
		"halfway up, the binoculars and both hands are in view and the view has not zoomed yet (FOV %.1f)" % cam_b.fov)
	eq.hold_raise = -1.0
	await create_timer(0.8).timeout
	hv = eq.hands_visible()
	_check(eq.binoculars_up() and not hv["L"] and not hv["R"], "at the eyes only the view is left: no hands (%s)" % hv)
	eq.put_away_now()
	await create_timer(0.5).timeout
	hv = eq.hands_visible()
	_check(not hv["L"] and hv["R"] and eq.pose_now["R"] == "R_torch" and eq.torch_node.visible, "lowered: back to the torch hand (%s)" % hv)
	g.player.enter_focus("radio")
	await _settle_focus()
	await _frames(3)
	hv = eq.hands_visible()
	_check(not hv["L"] and not hv["R"], "a device view puts the hands away (%s)" % hv)
	g.player.leave_focus()
	await _settle_focus()
	eq.put_away_now()
	g.player.give_torch(false)


## G3c R17: the keeper's body. body.glb gives a 19-bone body; the legs, boots and torso are seen and cast
## shadows, the arms and head only cast shadows; idle standing, the walk while moving (its stance foot slides
## under 3 cm a step at the walking speed), stepping round when turning on the spot; seated in the radio
## view with the head under the view's eye; put away in the other device views; nothing of it near the eye.
func _r17_body() -> void:
	print("R17 G3c body")
	var pb = g.player.body
	_check(pb != null and pb.skel != null and pb.skel.get_bone_count() == 19
		and pb.meshes["view"].cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		and pb.meshes["shadow"].cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY,
		"body.glb: 19 bones; legs, boots and torso seen; arms and head shadow-only")
	g.player.leave_focus()
	await _settle_focus()
	g.player.equipment.put_away_now()
	# the longest clear line on the floor, to walk along
	var space: PhysicsDirectSpaceState3D = g.player.get_world_3d().direct_space_state
	var o: Vector3 = g.player.global_position + Vector3(0, 0.5, 0)
	var best := 0.0
	var best_yaw := 0.0
	for i in 16:
		var yaw := TAU * i / 16.0
		var d := Vector3(-sin(yaw), 0, -cos(yaw))
		var q := PhysicsRayQueryParameters3D.create(o, o + d * 6.0, g.player.collision_mask, [g.player.get_rid()])
		var h: Dictionary = space.intersect_ray(q)
		var dist: float = 6.0 if h.is_empty() else o.distance_to(h["position"])
		if dist > best:
			best = dist
			best_yaw = yaw
	g.player._yaw = best_yaw
	g.player._pitch = 0.0
	g.player._apply_look()
	await create_timer(0.5).timeout
	var floor_y: float = g.player.global_position.y
	var feet: Dictionary = pb.foot_positions()
	_check(pb.state == "idle" and pb.visible and absf(minf(feet["L"].y, feet["R"].y) - floor_y - 0.098) < 0.03,
		"standing still: idle, the ankles on the floor (%.3f m above it; the clear line ahead %.1f m)" % [minf(feet["L"].y, feet["R"].y) - floor_y, best])
	# walking plays the walk at the walking speed
	Input.action_press("move_forward")
	await create_timer(0.8).timeout
	var spd := Vector2(g.player.velocity.x, g.player.velocity.z).length()
	_check(pb.state == "walk" and absf(pb.ap.speed_scale - spd / PlayerBody.WALK_SPEED) < 0.02,
		"walking: the walk plays, its rate matched to the speed (%.2f m/s, x%.2f)" % [spd, pb.ap.speed_scale])
	Input.action_release("move_forward")
	# foot sliding, frame-rate independent: step the walk in 1/120 s and carry the body forward at the speed
	# it is keyed for; a planted foot (ankle within 2 cm of standing height) must stay put
	pb.set_process(false)
	pb.ap.play("walk")
	pb.ap.speed_scale = 1.0
	var worst := 0.0
	var stance := ""
	var start := 0.0
	var tau := 0.0
	var rest_y: float = pb.skel.get_bone_global_rest(pb.skel.find_bone("foot.L")).origin.y
	var cycle: float = pb.ap.get_animation("walk").length
	while tau < cycle * 2.0:
		pb.ap.seek(fmod(tau, cycle), true)
		var low := ""
		var fz := {}
		for sd in ["L", "R"]:
			var fpos: Vector3 = pb.skel.get_bone_global_pose(pb.skel.find_bone("foot." + sd)).origin
			fz[sd] = fpos.z + PlayerBody.WALK_SPEED * tau      # body front is +Z in the skeleton
			if fpos.y - rest_y < 0.02 and (low == "" or fpos.y < pb.skel.get_bone_global_pose(pb.skel.find_bone("foot." + low)).origin.y):
				low = sd
		if low != stance:
			stance = low
			if stance != "":
				start = fz[stance]
		elif stance != "":
			worst = maxf(worst, absf(fz[stance] - start))
		tau += 1.0 / 120.0
	pb.set_process(true)
	_check(worst < 0.03, "a planted foot slides %.3f m a step at the walking speed (under 0.03)" % worst)
	await create_timer(0.6).timeout
	# turning on the spot: 3 rad/s in fixed 1/60 s steps (frame-rate independent)
	pb.set_process(false)
	for i in 30:
		g.player._yaw += 3.0 / 60.0
		g.player._apply_look()
		pb._process(1.0 / 60.0)
	_check(pb.state == "turn", "turning on the spot steps round (%s, %.1f rad/s)" % [pb.state, pb._turn_rate])
	for i in 60:
		pb._process(1.0 / 60.0)
	_check(pb.state == "idle", "standing again once the turn stops (%s)" % pb.state)
	pb.set_process(true)
	await create_timer(0.8).timeout
	# nothing of the seen body near the eye, looking ahead or straight down
	var near := 1.0
	for pitch in [0.0, -1.45]:
		g.player._pitch = pitch
		g.player._apply_look()
		await _frames(3)
		near = minf(near, _mesh_eye_clear(pb.meshes["view"], pb.skel))
	_check(near > 0.08, "the seen body stays clear of the eye, level and looking down (nearest %.3f m in front)" % near)
	g.player._pitch = 0.0
	g.player._apply_look()
	# seated at the radio, put away elsewhere
	g.player.enter_focus("radio")
	await _settle_focus()
	await _frames(4)
	var eye: Vector3 = g.station.focus["radio"]["eye"]
	var head: Vector3 = pb.skel.global_transform * pb.skel.get_bone_global_pose(pb.skel.find_bone("head")).origin
	var hips: Vector3 = pb.skel.global_transform * pb.skel.get_bone_global_pose(pb.skel.find_bone("hips")).origin
	_check(pb.state == "sit" and pb.visible and Vector2(head.x - eye.x, head.z - eye.z).length() < 0.08 and absf(hips.y - floor_y - 0.55) < 0.05,
		"the radio view: seated, the head under the view's eye (%.3f m off), the hips at the seat (%.2f m)" % [Vector2(head.x - eye.x, head.z - eye.z).length(), hips.y - floor_y])
	g.player.leave_focus()
	await _settle_focus()
	g.player.enter_focus("console")
	await _settle_focus()
	await _frames(2)
	_check(not pb.visible and pb.state == "away", "another device view puts the body away")
	g.player.leave_focus()
	await _settle_focus()
	await _frames(2)
	_check(pb.visible and pb.state != "sit", "back on his feet after leaving the view (%s)" % pb.state)


## The nearest vertex of a skinned mesh (each rigid to its strongest bone) inside a 10 x 10 cm box round the
## line of sight, as a distance in front of the eye. 1.0 when the box is empty.
func _mesh_eye_clear(mi: MeshInstance3D, sk: Skeleton3D) -> float:
	var to_cam: Transform3D = g.player.camera.global_transform.affine_inverse() * sk.global_transform
	var nearest := 1.0
	var skin: Skin = mi.skin
	var m: Mesh = mi.mesh
	for s in m.get_surface_count():
		var arr: Array = m.surface_get_arrays(s)
		var verts: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var bones = arr[Mesh.ARRAY_BONES]
		var wts = arr[Mesh.ARRAY_WEIGHTS]
		if bones == null or wts == null or verts.is_empty() or skin == null:
			continue
		var per: int = bones.size() / verts.size()
		for i in range(0, verts.size(), 2):
			var bst := 0
			for j in per:
				if wts[i * per + j] > wts[i * per + bst]:
					bst = j
			var bind: int = bones[i * per + bst]
			var bi: int = skin.get_bind_bone(bind)
			if bi < 0:
				bi = sk.find_bone(skin.get_bind_name(bind))
			var p: Vector3 = to_cam * (sk.get_bone_global_pose(bi) * skin.get_bind_pose(bind) * verts[i])
			if absf(p.x) < 0.05 and absf(p.y) < 0.05 and p.z < 0.0:
				nearest = minf(nearest, -p.z)
	return nearest


## G4a R18: the cabin fixes. The KEEPER'S ORDERS board and Iain's pipe are readable (info targets with a
## thought) and the console note is the written note_046 (textured, seated on the plate). The shelf props
## are merged into shared meshes, so their clearances are checked in the cu_shelf capture, not here.
func _r18_cabin_g4a() -> void:
	print("R18 G4a cabin")
	var st = g.station
	for id in ["orders", "pipe", "note"]:
		_check(st._ia_bodies.has(id), "the %s can be looked at (interaction volume)" % id)
	_check(st.inspect_line("orders").contains("Five: fuel valve open before START"), "the orders' line 5 reads as a thought (%s)" % st.inspect_line("orders"))
	_check(st.inspect_line("pipe") != "", "Iain's pipe has its line (%s)" % st.inspect_line("pipe"))
	var note_tex := false
	for mi in st.room.find_children("*Note046*", "MeshInstance3D", true, false):
		note_tex = true
	_check(note_tex, "the console note carries the written note_046 texture")


## G6a R19 (item 34): the ending sequence and the rolling credits. No panels before the ending card; the
## four panels of a truth + saved + confessed campaign in order, then the ending's lines beside P4 and the
## closing card; Space before a panel's dwell is ignored, after it moves on; E, 1-4, F / G / B, J, L and H
## do nothing; sim radio chatter is logged but never shown; the credits roll on warm black with the music
## on the Music bus, Esc jumps to the end, and its button finishes.
func _wait_until(cond: Callable, max_frames: int) -> int:
	var t := 0
	while not cond.call() and t < max_frames:
		await process_frame
		t += 1
	return t


func _r19_ending_g6a() -> void:
	print("R19 G6a ending sequence and credits")
	var pr = g.presenter
	var dir: StoryDirector = g.director
	var st: StoryState = dir.state
	var keep_flags: Dictionary = st.flags.duplicate(true)
	var keep_rescues: Dictionary = st.rescues.duplicate(true)
	var keep_hist := st.history.size()
	if dlg.is_active():
		dlg.close()
	st.flags["told_truth"] = 1
	st.flags["confessed_to_ross"] = 1
	st.rescues["Iona Star"] = "saved"
	_check(dir.ending_panels().is_empty(), "no ending panels before the ending card")
	dir._ending_card("ch6_epilogue")
	var want := ["p1_wheel", "p2_gut", "p3_correction_ross", "p4_correction"]
	_check(dir.ending_panels() == want, "a truth + saved + confessed campaign gets %s (%s)" % [want, dir.ending_panels()])
	await _wait_until(func(): return pr.ending_seq.current_id == "p1_wheel", 900)
	var seq: EndingSequence = pr.ending_seq
	_check(pr.is_ending_open() and seq.playing and seq.current_id == "p1_wheel", "the first panel follows the fade to warm black")
	_check(not seq.has_image("p1_wheel") and seq._slot.get_meta("standin", false), "p1 (art pending) shows its stand-in plate")
	# the gameplay keys do nothing during the sequence
	var held0: String = g.player.equipment.held if g.player.equipment else ""
	for k in [KEY_E, KEY_1, KEY_2, KEY_4, KEY_F, KEY_G, KEY_B, KEY_J, KEY_L, KEY_H]:
		_key(k)
		await _frames(2)
	_check(seq.current_id == "p1_wheel" and seq.early_presses == 0, "E, 1-4, F, G, B, J, L, H never move the ending on")
	_check((g.player.equipment.held if g.player.equipment else "") == held0 and not g.ui.logbook.visible
		and not (g.backlog and g.backlog.visible) and not pr.is_document_open(), "... and open nothing (held '%s')" % held0)
	# sim chatter during the ending: logged, not shown
	g.sim.main_breaker = true
	g.sim.battery = 80.0
	var subs0: int = g.ui._sub_items.size()
	var hist0 := st.history.size()
	g._comms_radio("Kittiwake", "R19 test chatter", false, "position", null)
	await _frames(3)
	_check(g.ui._sub_items.size() == subs0 and st.history.size() == hist0 + 1 and g._comms_queue.is_empty(),
		"sim radio chatter is logged but never shown over the ending (%d -> %d subtitles)" % [subs0, g.ui._sub_items.size()])
	# the dwell: Space at once is ignored; after the dwell it moves on
	await _wait_until(func(): return seq._slot.modulate.a >= 0.99, 300)
	_key(KEY_SPACE)
	await _frames(3)
	_check(seq.current_id == "p1_wheel" and seq.early_presses == 1, "Space before the panel's dwell is ignored (%d)" % seq.early_presses)
	await create_timer(float(seq.panel_info("p1_wheel")["dwell"]) + 0.2).timeout
	_key(KEY_SPACE)
	await _frames(4)
	_check(seq.current_id == "p2_gut", "Space after the dwell moves on to the Iona Star panel (%s)" % seq.current_id)
	# P3 is the real log page (blender/ending_pages.py), graded
	await _wait_until(func(): return seq.current_id == "p3_correction_ross", 1800)
	_check(seq.has_image("p3_correction_ross") and seq._slot is TextureRect and seq._slot.material is ShaderMaterial,
		"P3 is the rendered log page through the panel grade")
	# the rest plays by itself (Space every 0.5 s after the dwells), then the closing card, then the release
	var t := 0
	while pr.is_ending_open() and t < 7200:
		if t % 30 == 0:
			_key(KEY_SPACE)
		await process_frame
		t += 1
	_check(not pr.is_ending_open(), "the sequence and the closing card finish and release the story (%d frames)" % t)
	_check(seq.shown == want, "every panel was shown, in order (%s)" % [seq.shown])
	_check(seq.lines_shown == dir.ending_body.size() and dir.ending_body.size() > 0, "the ending's lines read beside P4 (%d)" % seq.lines_shown)
	var card_n := 0
	for c in pr.ending_box.get_children():
		if not c.is_queued_for_deletion():
			card_n += 1
	_check(card_n == dir.ending_closing.size() and pr.ending_title.text.begins_with("C O R R E C T I O N"),
		"the closing card shows the title and the %d closing lines (%d)" % [dir.ending_closing.size(), card_n])
	pr.hide_ending()
	# the rolling credits
	var layer := CanvasLayer.new()
	layer.layer = 40
	root.add_child(layer)
	var roll := CreditsRoll.new().setup(true)
	layer.add_child(roll)
	await _frames(3)
	_check(roll.music != null and roll.music.bus == "Music" and roll.music.playing, "the credits music plays on the Music bus")
	_check(roll.text.text.contains("Daniel Yanchev") and roll.text.text.contains("Human Base Meshes")
		and not roll.text.text.contains("AI-generated") and not roll.text.text.contains("Stage 3C"), "the credits text is the corrected one")
	var s0 := roll.scroll
	await create_timer(0.5).timeout
	_check(roll.scroll > s0 + 5.0 and not roll.at_end, "the credits roll up by themselves (%.0f -> %.0f px)" % [s0, roll.scroll])
	var esc := InputEventAction.new()
	esc.action = "pause"
	esc.pressed = true
	roll._unhandled_input(esc)
	await _frames(2)
	_check(roll.at_end and roll.end_button.visible and roll.end_button.text == "Return to the title", "Esc jumps to the end: 'Return to the title'")
	var fin := [false]
	roll.finished.connect(func(): fin[0] = true)
	roll.end_button.pressed.emit()
	await create_timer(1.8).timeout
	_check(fin[0], "its button finishes the credits (main_fp returns to the title)")
	layer.queue_free()
	st.flags = keep_flags
	st.rescues = keep_rescues
	st.history.resize(keep_hist)
	dir.ending_id = ""
	dir.ending_lines = []
	dir.ending_body = []
	dir.ending_closing = []
	g.player.enabled = true


## Stage 3C / item 22 R20: the radio card is a print for a speaker with a portrait (Daniel's prints,
## assets/portraits/<id>_<expr>.png), with the expression's print when there is one and the neutral one
## otherwise; the Mary Ellen's card is the boat; a caller with no print (the Corrie May) keeps the line
## drawing; the unrevealed visitor gets none, and Ross only the silhouette print.
func _r20_portraits() -> void:
	print("R20 item 22 radio portraits")
	_check(Speakers.portrait("MORAG", "worried").ends_with("morag_worried.png"), "Morag (worried) gets her worried print")
	_check(Speakers.portrait("MORAG", "furious").ends_with("morag_neutral.png"), "an expression with no print falls back to neutral")
	_check(Speakers.portrait("MARY ELLEN").ends_with("mary_ellen_neutral.png"), "the Mary Ellen's card is the boat print")
	_check(Speakers.portrait("CORRIE") == "" and Speakers.portrait("VISITOR") == "", "no print for the Corrie May or the unrevealed visitor")
	_check(Speakers.portrait("ROSS").ends_with("ross_neutral.png"), "Ross has only the silhouette print")
	if dlg.is_active():
		dlg.close()
	dlg.show_line({"mode": "radio", "speaker": "MARY ELLEN", "text": "...tell Iain... we cannot... see the light..."})
	await _frames(2)
	_check(dlg.radio_panel.visible and dlg._portrait != null and dlg._portrait.resource_path.ends_with("mary_ellen_neutral.png"),
		"a Mary Ellen radio line shows the boat print on the card")
	_check(dlg.card.size.x >= dlg.PHOTO_RECT.end.x and dlg.card.size.y >= dlg.PHOTO_RECT.end.y, "the print fits inside the card (%s)" % dlg.card.size)
	dlg.close()
	dlg.show_line({"mode": "radio", "speaker": "MORAG", "expr": "worried", "text": "North Point, Stornoway."})
	await _frames(2)
	_check(dlg._portrait != null and dlg._portrait.resource_path.ends_with("morag_worried.png"), "a tagged line shows that expression's print")
	dlg.close()
	dlg.show_line({"mode": "radio", "speaker": "CORRIE", "text": "Corrie May, Corrie May."})
	await _frames(2)
	_check(dlg._portrait == null, "a caller with no print keeps the line drawing")
	dlg.close()


## G6c R21 (item 1, "Still Water"): the title menu. The lantern sits at about 0.69 of the width at 16:9,
## 16:10 and 21:9 along the orbit, right of the column; the rank shows in brightness (the top item full
## parchment, the rest quiet; no Continue without a save); one highlight only (hover takes the focus; a
## hovered item that lost the focus to the keyboard is not lit); panels lock the column and give the
## focus back on close, as the credits do; the corner signature always shows, the links only from a
## file with valid entries (https / mailto), resting at 45 % alpha; no overlap at text sizes 0.8-1.5;
## keyboard and pad reach every item and the links; Reduce motion shows everything at once, no glow.
func _r21_mouse_to(c: Control) -> void:
	var m := InputEventMouseMotion.new()
	m.position = c.get_global_rect().get_center()
	m.global_position = m.position
	root.push_input(m)


func _r21_lit(main: Node) -> Array:
	var lit := []
	for b in main.menu_items:
		var c: Color = b.get_theme_color("font_color")
		if c.is_equal_approx(UIStyle.AMBER) or (b.is_hovered() and b.get_theme_color("font_hover_color").is_equal_approx(UIStyle.AMBER)):
			lit.append(b.text)
	return lit


func _r21_marks(main: Node) -> Array:
	return main.menu_items.filter(func(b): return b.mark > 0.5).map(func(b): return b.text)


func _r21_build(main: Node, args: Dictionary) -> void:
	var ga: Dictionary = root.get_node("GameState").user_args
	for k in ["menu_fake_save", "menu_nosave", "links"]:
		ga.erase(k)
	ga.merge(args, true)
	if main.is_inside_tree():
		main.show_menu()
	else:
		root.add_child(main)              # _ready -> show_menu()
	await create_timer(2.2).timeout       # the entrance (logo 2.0 s, items from 0.9 s, corner from 1.6 s)
	await _frames(3)


func _r21_menu_g6c() -> void:
	print("R21 G6c title menu")
	var st_node: Node = root.get_node("Settings")
	var ga: Dictionary = root.get_node("GameState").user_args
	var hidden := []
	for c in g.find_children("*", "CanvasLayer", true, false):
		if c.visible:
			hidden.append(c)
			c.visible = false
	g.process_mode = Node.PROCESS_MODE_DISABLED
	root.size = Vector2i(1920, 1080)
	var main: Node = load("res://scripts/main_fp.gd").new()
	# 1) no save, the shipped (empty) links file
	await _r21_build(main, {"menu_nosave": "1"})
	var texts: Array = main.menu_items.map(func(b): return b.text)
	_check(texts == ["New Game", "Load Game", "Options", "Credits", "Quit"], "no save: no Continue (%s)" % [texts])
	_check(main.menu_items[0].top and main.menu_items.slice(1).all(func(b): return not b.top), "no save: New Game is the top item")
	_check(main.menu_corner.signature.visible and main.menu_corner.signature.text == "A GAME BY DANIEL YANCHEV"
		and not main.menu_corner.links_box.visible and main.menu_corner.buttons.is_empty(), "the shipped links.json: the signature alone, no links")
	# 2) a save, the test links (three valid, http: and javascript: rejected)
	await _r21_build(main, {"menu_fake_save": "1", "links": "res://tests/fixtures/links_r21.json"})
	var items: Array = main.menu_items
	texts = items.map(func(b): return b.text)
	_check(texts == ["Continue", "New Game", "Load Game", "Options", "Credits", "Quit"], "a save: Continue first (%s)" % [texts])
	_check(items[0].top and items.slice(1).all(func(b): return not b.top), "only Continue is a top item")
	var by_tone := true
	for b in items:
		if b.has_focus():
			continue
		by_tone = by_tone and b.tone_color().is_equal_approx(UIStyle.INK if b.top else UIStyle.INK_QUIET)
	_check(by_tone and items.all(func(b): return b.get_theme_font_size("font_size") <= UIStyle.px(UIStyle.MENU_TOP)),
		"the rank is brightness: the top item full parchment, the rest quiet, all small")
	_check(main.menu_meta != null and main.menu_meta.text.begins_with("CH. I · THE WATCH · 20.20"), "the save line is a typed log line (%s)" % (main.menu_meta.text if main.menu_meta else ""))
	_check(main.save_line({"story": {"chapter": 3, "play_seconds": 3700}, "chapter_title": "The Storm", "clock": "01:05", "saved_at": "2026-11-07T23:59:10"})
		== "CH. III · THE STORM · 01.05 · 61 MIN PLAYED · SAVED 7 NOV 23.59", "save_line formats any save")
	var cor: MenuLinks = main.menu_corner
	_check(cor.buttons.size() == 3 and cor.links_box.visible and cor.divider.visible, "the test file: three links (%d)" % cor.buttons.size())
	_check(MenuLinks.load_links("res://tests/fixtures/links_r21.json").map(func(e): return e["url"]).all(func(u): return u.begins_with("https://") or u.begins_with("mailto:")),
		"http: and javascript: links are rejected")
	_check(cor.buttons.all(func(b): return absf(b.modulate.a - MenuLinks.REST_ALPHA) < 0.01), "the links rest at 45 % alpha")
	# framing: the lantern at 0.69 of the width along the orbit, at three aspects, right of the column
	var bg = main.menu_bg
	for s in [Vector2i(1920, 1080), Vector2i(1920, 1200), Vector2i(2560, 1080)]:
		root.size = s
		var xs := []
		for t in [0.0, 47.0, 133.0]:
			bg._cine_t = t
			await _frames(2)
			xs.append(bg.lantern_screen_x())
		var col_end: float = main.menu_col.get_global_rect().end.x / main.menu_col.get_viewport_rect().size.x
		_check(xs.all(func(x): return absf(x - 0.69) <= 0.04), "%dx%d: the lantern at 0.69 of the width (%s)" % [s.x, s.y, xs.map(func(x): return snappedf(x, 0.001))])
		_check(xs.all(func(x): return x > col_end + 0.05), "%dx%d: the lantern is clear of the column (ends at %.2f)" % [s.x, s.y, col_end])
	root.size = Vector2i(1920, 1080)
	await _frames(3)
	# one highlight: hover takes the focus; the keyboard moves it; a hovered item that lost it is not lit
	var opt: MenuItem = items[3]
	var cred: MenuItem = items[4]
	_r21_mouse_to(opt)
	await _frames(2)
	_check(opt.has_focus(), "hovering Options gives it the focus")
	await create_timer(0.3).timeout
	_check(_r21_lit(main) == ["Options"] and _r21_marks(main) == ["Options"], "one highlight after the hover (lit %s, ticks %s)" % [_r21_lit(main), _r21_marks(main)])
	_key(KEY_DOWN)
	await _frames(2)
	await create_timer(0.3).timeout
	_check(cred.has_focus() and _r21_lit(main) == ["Credits"] and _r21_marks(main) == ["Credits"],
		"keyboard down with the pointer still on Options: only Credits is lit (lit %s, ticks %s)" % [_r21_lit(main), _r21_marks(main)])
	_r21_mouse_to(items[2])
	await _frames(2)
	await create_timer(0.3).timeout
	_check(_r21_lit(main) == ["Load Game"] and _r21_marks(main) == ["Load Game"], "hover again: only Load Game (lit %s)" % [_r21_lit(main)])
	# the beam glow follows the beam (and only on the focused tick)
	items[2].glow_source = func() -> float: return 1.0
	await _frames(3)
	_check(items[2].glow > 0.9 and items[1].glow == 0.0, "the focused tick glows with the beam (%.2f)" % items[2].glow)
	# panels: Options locks the column; Esc closes it and gives the focus back to Options
	opt.grab_focus()
	opt.pressed.emit()
	await _frames(3)
	_check(main.panel != null and items.all(func(b): return b.focus_mode == Control.FOCUS_NONE)
		and cor.buttons.all(func(b): return b.focus_mode == Control.FOCUS_NONE), "an open panel locks the column and the links")
	var esc := InputEventAction.new()
	esc.action = "pause"
	esc.pressed = true
	main._unhandled_input(esc)
	await _frames(3)
	_check(main.panel == null and opt.has_focus() and items.all(func(b): return b.focus_mode == Control.FOCUS_ALL), "Esc closes Options and the focus is back on Options")
	cred.grab_focus()
	cred.pressed.emit()
	await _frames(3)
	_check(main.credits_roll != null and items.all(func(b): return b.focus_mode == Control.FOCUS_NONE), "the credits lock the column")
	main.credits_roll.finished.emit()
	await _frames(3)
	_check(cred.has_focus() and items.all(func(b): return b.focus_mode == Control.FOCUS_ALL), "after the credits the focus is back on Credits")
	# the links: hover lifts one to full alpha; pressing it opens its URL (through the test hook)
	var opened := []
	MenuLinks.open_hook = func(u: String): opened.append(u)
	var l0: Button = cor.buttons[0]
	_r21_mouse_to(l0)
	await _frames(2)
	await create_timer(0.3).timeout
	_check(l0.has_focus() and l0.modulate.a > 0.99 and _r21_lit(main).is_empty(), "hovering a link lifts it to full alpha and takes the focus (%.2f)" % l0.modulate.a)
	l0.pressed.emit()
	_check(opened == ["https://example.com/instagram"], "pressing a link opens its URL (%s)" % [opened])
	MenuLinks.open_hook = Callable()
	# layout: no overlap, all on screen, at text sizes 0.8 / 1.0 / 1.5 and 16:9 / 16:10
	for s in [Vector2i(1920, 1080), Vector2i(1920, 1200)]:
		root.size = s
		for k in [0.8, 1.0, 1.5]:
			UIStyle.set_text_scale(k, self)
			await _frames(4)
			var a: Rect2 = main.menu_col.get_global_rect()
			var b2: Rect2 = cor.get_global_rect()
			var vp: Rect2 = main.menu_col.get_viewport_rect()
			_check(not a.intersects(b2) and vp.encloses(a) and vp.encloses(b2), "%dx%d text %.1f: column %s and corner %s apart, on screen" % [s.x, s.y, k, a, b2])
	UIStyle.set_text_scale(float(st_node.v["subtitle_size"]), self)
	root.size = Vector2i(1920, 1080)
	await _frames(3)
	# navigation: keyboard and pad reach every item, then the links; up comes back
	items[0].grab_focus()
	await _frames(2)
	var seen := [items[0].text]
	for i in 8:
		if i < 4:
			_key(KEY_DOWN)
		else:
			_pad_button(JOY_BUTTON_DPAD_DOWN, true)
			_pad_button(JOY_BUTTON_DPAD_DOWN, false)
		await _frames(2)
		var fo := main.get_viewport().gui_get_focus_owner()
		seen.append(fo.text if fo is Button else "?")
	_check(seen == ["Continue", "New Game", "Load Game", "Options", "Credits", "Quit", "INSTAGRAM", "TRAILER", "CONTACT"],
		"down (keys, then d-pad) walks the menu and then the links (%s)" % [seen])
	cor.buttons[0].grab_focus()
	_key(KEY_UP)
	await _frames(2)
	_check(items[5].has_focus(), "up from the links comes back to Quit")
	# Reduce motion: everything at once, no glow
	var keep_rm = st_node.v.get("reduce_motion", false)
	st_node.v["reduce_motion"] = true
	ga.erase("links")
	ga["menu_fake_save"] = "1"
	main.show_menu()
	await create_timer(1.1).timeout
	await _frames(2)
	var root_a: float = main.menu.get_child(0).modulate.a
	_check(root_a > 0.99 and main.menu_items.all(func(b): return b.modulate.a > 0.99 and b.rise == 0.0), "Reduce motion: the whole menu is up after 1.1 s (%.2f)" % root_a)
	main.menu_items[0].glow_source = func() -> float: return 1.0
	main.menu_items[0].grab_focus()
	await _frames(3)
	_check(main.menu_items[0].glow == 0.0 and main.menu_items[0].mark == 1.0, "Reduce motion: the tick shows at once and never glows")
	st_node.v["reduce_motion"] = keep_rm
	for k in ["menu_fake_save", "menu_nosave", "links"]:
		ga.erase(k)
	main.queue_free()
	await _frames(3)
	g.process_mode = Node.PROCESS_MODE_INHERIT
	for c in hidden:
		c.visible = true


func _save_mtimes(d: String) -> Dictionary:
	var out := {}
	var abs_dir := ProjectSettings.globalize_path(d)
	if DirAccess.dir_exists_absolute(abs_dir):
		for f in DirAccess.get_files_at(abs_dir):
			out[f] = FileAccess.get_modified_time(abs_dir.path_join(f))
	return out


## G6d R22 (saves): a test run saves into its own folder (user://saves_test); the player's saves in
## user://saves are exactly as they were before the run (the suites used to replace Daniel's autosave).
func _r22_saves_isolated() -> void:
	print("R22 saves isolated from the player's")
	var ss: Node = root.get_node("SaveSystem")
	_check(ss.dir == ss.TEST_DIR, "a test run saves to %s (%s)" % [ss.TEST_DIR, ss.dir])
	_check(_save_mtimes("user://saves") == _real_saves, "the player's saves are untouched by the run (%d files)" % _real_saves.size())
	# Stage B: the lighthouse. The base door faces the landing and the visitor's door sound is at it; the tower
	# has its own lit skin round the watch room; the window sky-spill lights make no specular (the white
	# discs on the panes that bloomed into "two white lights" from outside)
	var lh: Node3D = load("res://assets/models/lighthouse.glb").instantiate()
	root.add_child(lh)
	var door := lh.find_child("SM_Door_SteelPaint", true, false) as MeshInstance3D
	var skin := lh.find_child("SM_TowerSkin_TowerPaint", true, false) as MeshInstance3D
	var dc := (door.global_transform * door.get_aabb()).get_center() if door else Vector3.ZERO
	var door_b := fposmod(rad_to_deg(atan2(dc.x, -dc.z)), 360.0)
	var snd: Vector3 = load("res://scripts/audio_director.gd").BASE_DOOR
	var snd_b := fposmod(rad_to_deg(atan2(snd.x, -snd.z)), 360.0)
	_check(door != null and absf(door_b - 35.0) < 3.0, "the base door faces the landing (bearing %.1f, want 35)" % door_b)
	_check(absf(snd_b - door_b) < 3.0 and Vector2(snd.x, snd.z).distance_to(Vector2(dc.x, dc.z)) < 1.5,
		"the visitor's base-door sound is at the door (%.1f vs %.1f)" % [snd_b, door_b])
	var sa := (skin.global_transform * skin.get_aabb()) if skin else AABB()
	_check(skin != null and sa.position.y <= 20.0 and sa.end.y >= 23.2, "the tower's own skin covers the watch room (y %.2f-%.2f)" % [sa.position.y, sa.end.y])
	lh.queue_free()
	var spec_ok: bool = not g.station.windows.is_empty()
	for w in g.station.windows:
		spec_ok = spec_ok and (w["light"] as Light3D).light_specular == 0.0
	_check(spec_ok, "the window sky-spill lights make no specular (%d lights)" % g.station.windows.size())


## G2b R14: the logbook shows only the rows written so far (never tonight's future), the pencil Duties
## page lists the known duties with done ones struck, A / D turns the page, closing from either page is
## "read the log"; a written row appears as a slip top-right whose ink is revealed, then fades.
func _r14_logbook() -> void:
	print("R14 G2b logbook and log slips")
	var pr = g.presenter
	var dir: StoryDirector = g.director
	var written0: Array = dir.state.log_written.duplicate()
	dir.state.log_written = []
	pr.open_document("log_1971")
	await _frames(2)
	_check(pr.is_document_open() and pr.log_pages.page == "log" and pr.log_pages.shown.is_empty() and pr.doc_text.text.contains("Nothing written"),
		"an empty night: the log page shows no rows (%s)" % [pr.log_pages.shown])
	pr.close_document()
	dir.state.log_written = ["log_1622"]
	pr.open_document("log_1971")
	await _frames(2)
	_check(pr.log_pages.shown == ["log_1622"] and pr.doc_text.text.contains("Batteries flat") and not pr.doc_text.text.contains("Light exhibited"),
		"after 16.22 only the 16.22 row is on the page (%s)" % [pr.log_pages.shown])
	var closed: Array = []
	var cb := func(id): closed.append(id)
	pr.document_closed.connect(cb)
	var ev := InputEventAction.new()
	ev.action = "move_right"
	ev.pressed = true
	pr._input(ev)
	await _frames(2)
	_check(pr._doc_open == "duties" and pr.log_pages.page == "duties", "D turns to the pencil Duties page")
	_check(pr.log_pages.shown.any(func(x): return String(x).begins_with("duty:")), "the Duties page lists the duties known tonight (%s)" % [pr.log_pages.shown])
	pr.close_document()
	await _frames(1)
	_check(closed == ["log_1971"], "closing from the Duties page counts as reading the log (%s)" % [closed])
	pr.document_closed.disconnect(cb)
	dir.state.log_written = written0
	# the slip: a written row is shown top-right, ink revealed left to right, then gone
	dir.write_log("log_1830") if not ("log_1830" in written0) else pr.show_log_entry(dir.log_entry("log_1830"))
	await create_timer(0.6).timeout
	var vp: Rect2 = g.get_viewport().get_visible_rect()
	var cr: Rect2 = pr.log_card.get_global_rect()
	_check(pr.log_card.visible and String(pr.log_card.get_meta("entry", "")) == "log_1830" and vp.encloses(cr) and cr.position.x > vp.size.x * 0.5
		and cr.position.y < vp.size.y * 0.2, "a written row appears as a slip top-right (%s)" % cr)
	var w0: float = pr._card_clip.size.x
	await create_timer(0.8).timeout
	_check(pr._card_clip.size.x > w0 and pr._card_clip.size.x <= pr._card_bg.size.x + 0.5, "the ink is revealed left to right (%.0f -> %.0f px)" % [w0, pr._card_clip.size.x])
	await create_timer(6.0).timeout
	_check(not pr.log_card.visible, "the slip is gone after a few seconds")
	dir.state.log_written = written0


## G2b (Daniel 2026-11-06) R13: the duty HUD replaces the item 9/20 panel. Top-left in the safe margin,
## on a dark plate; Standard fades the line in and out, Full keeps it with the steps, Minimal only on
## J / R3; a device view hides the line (not the hints); never over the radio panel or a notice; fits at
## every text size and window size.
func _r13_duty_hud() -> void:
	print("R13 G2b duty HUD")
	var settings: Node = root.get_node("Settings")
	var hud = g.presenter.duty_hud            # untyped: a -s script must not compile UI classes early
	var wait := func(secs: float): await create_timer(secs).timeout
	settings.v["guidance"] = 1
	settings.v["duty_hold_s"] = 1.0
	var view := {"title": "Get the engine running. Then CHARGE the cells.", "caption": "The Watch", "duty": "r13_a",
		"steps": [{"text": "The torch, top shelf by the stair door", "id": "torch"}, {"text": "FUEL VALVE open", "id": "fuel"}]}
	g.presenter.set_objective(view)
	g.presenter.set_progress([0])
	await wait.call(0.8)
	var vp: Rect2 = g.get_viewport().get_visible_rect()
	var pr: Rect2 = hud.plate.get_global_rect()
	_check(hud.duty_visible() and hud.caption.text == "THE WATCH" and g.presenter.objective.text == view["title"],
		"Standard: a new duty fades in with its caption and line (%s)" % hud.caption.text)
	_check(not hud.subs.visible and not hud.check.visible, "Standard: no checkboxes or step list")
	g.presenter.set_objective({"title": view["title"], "caption": "The Watch", "duty": "r13_a", "steps": view["steps"], "complete": true})
	await _frames(2)
	_check(hud.check.visible and not hud.subs.visible, "Standard: a finished duty shows its tick (no step list)")
	g.presenter.set_objective(view)
	_check(pr.position.x < vp.size.x * 0.06 and pr.position.y < vp.size.y * 0.1 and vp.encloses(pr) and pr.size.x <= vp.size.x * 0.30 + 60,
		"the duty line sits top-left inside the safe margin (%s)" % pr)
	var sb: StyleBoxFlat = hud.plate.get_theme_stylebox("panel")
	_check(sb.bg_color.a >= 0.65 and sb.bg_color.get_luminance() < 0.08, "the plate is dark enough to carry the text on a lit wall (a=%.2f)" % sb.bg_color.a)
	await wait.call(2.6)
	_check(not hud.duty_visible(), "Standard: the line fades out after its hold time")
	g.presenter.recall_duty()
	await wait.call(0.8)
	_check(hud.duty_visible(), "J / R3 brings the duty back")
	# a device view: the line steps aside, hints still show, nothing over the radio panel
	await wait.call(2.6)
	g.player.enter_focus("radio")
	await _settle_focus()
	g.presenter.set_objective({"title": "MODE to AUTO, LAMP to NORMAL.", "caption": "Lighting-up time", "duty": "r13_b", "steps": []})
	g.presenter.show_hint("The light console stands under the east window. Look at the MODE knob and press {interact}.", true)
	await wait.call(0.8)
	_check(not hud.duty_visible() and hud.hint.visible, "Standard in a device view: no duty line, the hint still shows")
	for sc in [1.0, 1.5]:
		settings.v["subtitle_size"] = sc
		settings.apply()
		g.presenter.recall_duty(true)
		g.ui.radio_panel.visible = true
		await wait.call(0.8)
		var pl: Rect2 = hud.plate.get_global_rect()
		var rp: Rect2 = g.ui.radio_panel.get_global_rect()
		_check(hud.duty_visible() and not pl.intersects(rp), "x%.1f recalled in the radio view, clear of the radio panel (%s / %s)" % [sc, pl, rp])
		g.ui.radio_panel.visible = false
	g.player.leave_focus()
	await _settle_focus()
	# Full: the duty with a checkbox and its steps as one-liners; done steps dimmed, not struck through
	settings.v["guidance"] = 2
	g.presenter.set_objective(view)
	g.presenter.set_progress([0])
	await wait.call(0.8)
	var rows: Array = hud.subs.get_children()
	_check(hud.duty_visible() and hud.check.visible and rows.size() == 2 and String(rows[0].text).begins_with("•"),
		"Full: checkbox, and the steps as dotted one-liners (%d rows)" % rows.size())
	_check(rows.size() == 2 and rows[0].modulate.a < 0.7 and rows[1].modulate.a > 0.95 and g.presenter.is_step_done(0) and not g.presenter.is_step_done(1),
		"Full: the done step is dimmed, the open one is not")
	await wait.call(2.6)
	_check(hud.duty_visible(), "Full: the duty stays on screen")
	for sc in [0.8, 1.0, 1.5]:
		settings.v["subtitle_size"] = sc
		settings.apply()
		g.ui.show_notice("Let go too soon: hold START until the engine catches.", 3.0)
		await wait.call(0.3)
		var pl2: Rect2 = hud.plate.get_global_rect()
		var nf: Font = g.ui.notice.get_theme_font("font")
		var nw: float = nf.get_string_size(g.ui.notice.text, HORIZONTAL_ALIGNMENT_LEFT, -1, g.ui.notice.get_theme_font_size("font_size")).x
		var nr: Rect2 = g.ui.notice.get_global_rect()
		var ntext := Rect2(nr.get_center().x - nw * 0.5, nr.position.y, nw, nr.size.y)
		_check(vp.encloses(pl2) and not pl2.intersects(ntext), "x%.1f Full: on screen and clear of a long notice (%s / %s)" % [sc, pl2, ntext])
	settings.v["subtitle_size"] = 1.0
	settings.apply()
	# Minimal: nothing until the player asks
	settings.v["guidance"] = 0
	g.presenter.set_objective({"title": "Find Kittiwake.", "caption": "", "duty": "r13_c", "steps": []})
	await wait.call(1.6)                        # the Full line before it fades out (1.2 s) first
	_check(not hud.duty_visible(), "Minimal: a new duty does not announce itself")
	g.presenter.recall_duty()
	await wait.call(0.8)
	_check(hud.duty_visible(), "Minimal: J / R3 still shows it")
	# other window sizes: the plate stays top-left and inside the screen
	var win := g.get_window()
	var size0: Vector2i = win.size
	var sizes: Array = [Vector2i(1280, 720), Vector2i(2560, 1440), Vector2i(3440, 1440)]
	if DisplayServer.get_name() == "headless":
		skips.append("R13 window sizes (headless)")
		sizes = []
	for sz in sizes:
		win.size = sz
		await _frames(4)
		var vpz: Rect2 = g.get_viewport().get_visible_rect()
		var plz: Rect2 = hud.plate.get_global_rect()
		_check(vpz.encloses(plz) and plz.position.x < vpz.size.x * 0.06, "%dx%d: the duty line fits top-left (%s in %s)" % [sz.x, sz.y, plz, vpz])
	win.size = size0
	settings.v["guidance"] = 1
	settings.v["duty_hold_s"] = 6.0
	g.presenter.set_objective("")
