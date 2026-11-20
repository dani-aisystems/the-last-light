extends SceneTree
## R30 (vessels in fog) determinism harness. Runs the R30 fade-in measurement of regress_test.gd many times with a
## deliberate stall injected into the frame in which the vessel is spawned (so that frame's real delta is large),
## in two modes: "old" = the pre-fix fixture (outside.gd keeps ticking the new view during the awaited frame) and
## "fixed" = the fixture of regress_test.gd now (outside's _process paused around spawn -> measurement).
##   tools/godot --headless --path projects/games/last_light/godot -s res://tests/r30_repeat.gd -- --reps=10 [--mode=old|fixed|both]
## Prints R30_REPEAT_RESULT {json}; exit code 1 when a FIXED-mode iteration fails (old-mode failures are expected).

const STALLS := [0, 50, 150, 400]
var g: Node3D
var rows: Array = []


func _initialize() -> void:
	_run.call_deferred()


func _arg(key: String, dflt: String) -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--%s=" % key):
			return a.get_slice("=", 1)
	return dflt


func _run() -> void:
	var reps := int(_arg("reps", "10"))
	var mode := _arg("mode", "both")
	var t0 := Time.get_ticks_msec()
	await process_frame
	g = load("res://scripts/fp/game_fp.gd").new()
	root.add_child(g)
	g.start(7, "", false, true)
	await _frames(3)
	g.director.process_mode = Node.PROCESS_MODE_DISABLED
	var lift := 0
	while g.presenter.is_screen_held() and lift < 900:
		await process_frame
		lift += 1
	g.sim.battery = 80.0
	var st_node: Node = root.get_node("Settings")
	st_node.persist = false
	var modes: Array = ["old", "fixed"] if mode == "both" else [mode]
	var n := 0
	for m in modes:
		for stall in STALLS:
			for r in reps:
				n += 1
				var row: Dictionary = await _one(m, stall, n)
				rows.append(row)
				print("  %s stall=%d #%d: appear0=%.4f alpha0=%.4f frame_dt=%.3f half=%.3f ok=%s" % [m, stall, r, row["appear0"], row["alpha0"], row["frame_dt"], row["half"], row["ok"]])
	var summary := {}
	var fixed_fail := 0
	for row in rows:
		var key := "%s/%d" % [row["mode"], row["stall"]]
		var sm: Dictionary = summary.get(key, {"n": 0, "fail": 0, "half_min": 99.0, "half_max": -99.0, "appear0_max": 0.0, "dt_max": 0.0})
		sm["n"] += 1
		sm["fail"] += 0 if row["ok"] else 1
		sm["half_min"] = minf(sm["half_min"], row["half"])
		sm["half_max"] = maxf(sm["half_max"], row["half"])
		sm["appear0_max"] = maxf(sm["appear0_max"], row["appear0"])
		sm["dt_max"] = maxf(sm["dt_max"], row["frame_dt"])
		summary[key] = sm
		if row["mode"] == "fixed" and not row["ok"]:
			fixed_fail += 1
	print("R30_REPEAT_RESULT ", JSON.stringify({"iterations": rows.size(), "fixed_failures": fixed_fail, "seconds": (Time.get_ticks_msec() - t0) / 1000.0, "summary": summary}))
	quit(1 if fixed_fail > 0 else 0)


func _frames(n: int) -> void:
	for i in n:
		await process_frame


## One R30 fade-in measurement. The stall goes in the frame BEFORE the spawn frame: the engine measures a frame's
## delta before process_frame fires, so a delay here is the delta of the next frame (the one we resume at).
func _one(mode: String, stall_ms: int, idx: int) -> Dictionary:
	var k: KeeperSim = g.sim
	var out := {"mode": mode, "stall": stall_ms, "appear0": -1.0, "alpha0": -1.0, "half": -1.0, "frame_dt": 0.0, "ok": false}
	if stall_ms > 0:
		OS.delay_msec(stall_ms)
	await process_frame                       # resumed with the stalled delta pending for this frame's node _process
	var fixed := mode == "fixed"
	if fixed:
		g.outside.set_process(false)
	var name_ := "R30 Rep %d" % idx
	g._route(k.spawn_story_ship({"name": name_, "kind": "fishing", "bearing": 0, "aim": 90, "range": 230.0,
		"hold": true, "protected": true}))
	await _frames(1)
	var s: FleetShip = k.find_ship_named(name_)
	var v = g.outside.ship_views.get(s.id) if s else null
	if v == null:
		if fixed:
			g.outside.set_process(true)
		return out
	out["appear0"] = v._appear
	out["frame_dt"] = v._appear * 3.0         # the delta outside.gd's tick fed the view (APPEAR_S = 3)
	out["alpha0"] = v.fade_alpha()
	if fixed and not (not g.outside.is_processing() and v._appear == 0.0 and v._fade == 0.0):
		out["half"] = -2.0                        # fixture not at rest: report as failure
		g.outside.set_process(true)
		return out
	var dt := 1.0 / 60.0
	var t := 0.0
	var half_at := -1.0
	for i in int(3.2 * 60):
		t += dt
		v.tick(t, dt, k.storm, k)
		if half_at < 0.0 and v.fade_alpha() >= 0.5:
			half_at = t
	out["half"] = half_at
	out["ok"] = is_equal_approx(v.fade_alpha(), 1.0) and absf(half_at - 1.5) < 0.1 and v.fade_alpha() < 1.0001
	# tidy: drop the vessel (no frees mid-loop), restore the tick
	g.outside.ship_views.erase(s.id)
	v.queue_free()
	k.ships.erase(s)
	if fixed:
		g.outside.set_process(true)
	return out
