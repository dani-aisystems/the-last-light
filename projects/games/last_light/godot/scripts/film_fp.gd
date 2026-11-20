extends Node
## Gameplay film: a scripted keeper plays the opening of chapter 1 in first person through the real
## player controls (walking with move_forward, looking by yaw / pitch, pressing with player._press), so
## the film shows the real crosshair, prompts, duty HUD and dialogue. Record it with Godot's Movie Maker:
##   tools/godot_bg --write-movie /abs/out.avi --fixed-fps 30 --path projects/games/last_light/godot \
##       -- --capture=film --film [--film_secs=N] [--audio]
## Runs inside capture_fp (so the unattended-run guards hold: no mouse capture, no settings writes, real
## input swallowed). Walk paths come from an A* grid built from the room's collision at start.
## Prints FILM_STEP lines and FILM_RESULT {json} at the end.

const CELL := 0.1
const HALF := 3.4
const FLOOR := 20.0

var main: Node
var g: Node
var astar := AStarGrid2D.new()
var t := 0.0                     # film time (Movie Maker: fixed steps)
var cap_secs := 1.0e9
var steps: Array = []


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	cap_secs = float(GameState.user_args.get("film_secs", "1e9"))
	if GameState.user_args.has("film_ending"):
		_run_ending.call_deferred(String(GameState.user_args["film_ending"]))
	else:
		_run.call_deferred()


## Release R3: one ending played in real time through the shipping path (the director's ending card: the
## ending's music cue, the warm-black fade, the four panels with their crossfades and holds, the epilogue
## lines beside P4, the closing card), then a little of the credits. Record it with Movie Maker:
##   tools/godot_bg --write-movie /abs/out.avi --fixed-fps 30 --path projects/games/last_light/godot \
##       -- --capture=film --film --film_ending=correction --audio
const FILM_ENDINGS := {
	"correction": [{"told_truth": 1, "gave_letter": 1, "ross_wheel": 1}, "saved"],
	"heard_together": [{"told_truth": 1, "ross_wheel": 1}, "lost"],
	"nothing_to_report": [{"kept_lie": 1, "reunion": 1, "gave_letter": 1, "ross_wheel": 1}, "saved"],
	"light_exhibited": [{"kept_lie": 1}, "lost"],
}


func _run_ending(id: String) -> void:
	await _wait(2.0)
	main.start_game("", true)
	g = main.game
	await _wait(3.0)
	var st: StoryState = g.director.state
	for k in FILM_ENDINGS[id][0]:
		st.flags[k] = FILM_ENDINGS[id][0][k]
	st.rescues["Iona Star"] = FILM_ENDINGS[id][1]
	_step("ending %s panels=%s" % [id, g.director.ending_panels()])
	g.director._ending_card("ch6_epilogue")
	await _wait(0.5)
	_step("panels %s" % [g.director.ending_panels()])
	var shown := ""
	var done := false
	var end := t + 400.0
	while t < end:
		var cur: String = g.presenter.ending_seq.current_id
		if cur != shown:
			shown = cur
			_step("panel %s" % cur)
		if not g.presenter._ending_open:
			done = true
			break
		await get_tree().process_frame
	_step("card closed=%s" % done)
	await _wait(10.0)
	_finish("ending")


func _process(delta: float) -> void:
	t += delta
	if t > cap_secs:
		_finish("cap")


func _wait(s: float) -> void:
	var end := t + s
	while t < end:
		await get_tree().process_frame


func _wait_until(cond: Callable, timeout: float) -> bool:
	var end := t + timeout
	while t < end:
		if cond.call():
			return true
		await get_tree().process_frame
	return false


func _step(what: String) -> void:
	steps.append({"t": snappedf(t, 0.1), "step": what})
	print("FILM_STEP %.1f %s" % [t, what])


func _finish(why: String) -> void:
	set_process(false)
	for a in ["move_forward", "move_back", "move_left", "move_right"]:
		Input.action_release(a)
	print("FILM_RESULT ", JSON.stringify({"end": why, "t": snappedf(t, 0.1), "steps": steps}))
	get_tree().quit(0)


# ------------------------------------------------------------------ the film

func _run() -> void:
	await _wait(7.0)                                   # the title screen over the live exterior
	_step("start_game")
	main.start_game("", true)
	g = main.game
	await get_tree().process_frame
	await get_tree().process_frame
	if g.director:
		g.director.bot = true                          # dialogue advances at reading pace, replies picked
		g.director.bot_line_s = 3.4
	_build_nav()
	await _wait(3.0)

	# dusk, batteries flat: look round the dark room
	_step("look_round")
	await _look(-0.35, -0.10, 2.2)
	await _look(0.75, -0.02, 2.6)
	await _wait(0.6)

	# the torch, top shelf by the stair door
	await _walk_to(Vector2(1.15, 1.25))
	await _aim_at("torch")
	await _wait(0.4)
	await _press("torch")
	await _wait(1.2)
	await _look(g.player._yaw + 1.6, -0.25, 2.4)       # sweep the beam across the room
	await _wait(0.4)

	# generator cage: fuel valve, then hold START
	await _walk_to(Vector2(-0.30, 0.80))
	await _aim_at("fuel_valve")
	await _wait(0.4)
	await _press("fuel_valve")
	await _wait(1.0)
	await _walk_to(Vector2(-0.55, 0.30))
	await _aim_at("start")
	await _wait(0.4)
	_step("hold start")
	g.player._press(InputEventAction.new())
	var caught := await _wait_until(func(): return g.sim.gen == KeeperSim.Gen.RUNNING, 25.0)
	g.player._release()
	_step("engine running=%s" % caught)
	await _wait(2.5)

	# the charger
	await _walk_to(Vector2(-1.55, -1.20))
	await _aim_at("battery")
	await _wait(1.0)
	await _aim_at("charge")
	await _wait(0.3)
	await _press("charge")
	await _wait(5.0)

	# lighting-up time at the console
	await _walk_to(Vector2(1.45, -0.30))
	await _aim_at("console")
	await _wait(0.3)
	await _press("console")
	await _wait(1.2)
	for i in 4:
		if g.sim.mode == 1:
			break
		await _press_in_view("mode")
		await _wait(0.9)
	for i in 4:
		if g.sim.intensity >= 1:
			break
		await _press_in_view("intensity")
		await _wait(0.9)
	_step("console mode=%d lamp=%d" % [g.sim.mode, g.sim.intensity])
	await _wait(2.5)
	g.player.leave_focus()
	await _wait(1.0)

	# out of the sea windows: the light working
	await _walk_to(Vector2(0.95, -1.40))
	await _look(deg_to_rad(-20.0), 0.02, 2.0)         # yaw 0 = north; negative = east of north
	await _wait(3.0)
	await _look(deg_to_rad(25.0), 0.0, 4.0)
	_step("waiting for the 18:30 radio check")
	var beat0: int = g.director.state.beat
	await _wait_until(func(): return g.director.state.beat > beat0, 30.0)
	await _wait(5.0)                                   # the clock card fades through
	await _aim_at("radio")                             # Stornoway on the set: look at it while it talks
	await _wait_until(func(): return g.director.state.beat > beat0 + 1, 40.0)
	await _aim_at("radar")
	await _wait(2.0)

	# the binoculars from the desk, then Kittiwake out in the Sound
	await _aim_at("binoculars")
	await _wait(0.4)
	await _press("binoculars")
	await _wait(1.0)
	_step("waiting for Kittiwake")
	await _wait_until(func(): return _ship("Kittiwake") != null, 40.0)
	await _wait(1.0)
	var ship = _ship("Kittiwake")
	var spot := _clear_spot(ship)                      # a window pier must not fill the glasses
	await _walk_to(spot)
	var aim: Array = _aim_ship(ship)
	_step("kittiwake look yaw=%.1f pitch=%.2f" % [rad_to_deg(aim[0]), aim[1]])
	await _look(aim[0], aim[1], 2.2)
	if g.player.equipment.held != "binoculars":
		g.player.equipment.toggle("binoculars")
		g.player.events.emit([{"type": "equip", "item": "binoculars", "held": g.player.equipment.held}])
	_step("binoculars up")
	var hold_end := t + 9.0                            # follow her through the glasses
	while t < hold_end:
		aim = _aim_ship(_ship("Kittiwake"))
		var dt := get_process_delta_time()
		g.player._yaw = lerp_angle(g.player._yaw, aim[0], minf(1.0, dt * 1.5))
		g.player._pitch = lerpf(g.player._pitch, aim[1], minf(1.0, dt * 1.5))
		g.player._apply_look()
		await get_tree().process_frame
	g.player.equipment.toggle("binoculars")
	g.player.events.emit([{"type": "equip", "item": "binoculars", "held": g.player.equipment.held}])
	await _wait(4.0)
	_finish("done")


func _ship(name_: String) -> FleetShip:
	for s in g.sim.active_ships():
		if s.name == name_:
			return s
	return null


## A standing spot by the sea windows whose sightline to the ship meets the wall nearest the middle of a
## window bay (bays are centred every 45 degrees, piers between them), so no pier fills the glasses. The
## wall colliders cover the glass too, so the ray's hit point is used for its bearing only.
func _clear_spot(s: FleetShip) -> Vector2:
	var cands := [Vector2(-0.3, -1.25), Vector2(0.0, -1.2), Vector2(-0.6, -1.2), Vector2(0.6, -1.3), Vector2(0.95, -1.4), Vector2(-0.9, -1.1)]
	if s == null:
		return cands[0]
	var space: PhysicsDirectSpaceState3D = g.player.get_world_3d().direct_space_state
	var best: Vector2 = cands[0]
	var best_off := 999.0
	for c in cands:
		var eye := Vector3(c.x, FLOOR + g.player.EYE, c.y)
		var d := (Vector3(s.pos.x, 0.5, s.pos.y) - eye).normalized()
		var q := PhysicsRayQueryParameters3D.create(eye, eye + d * 6.0)
		q.exclude = [g.player.get_rid()]
		var hit := space.intersect_ray(q)
		if hit.is_empty():
			continue
		var hp: Vector3 = hit["position"]
		var brg := rad_to_deg(atan2(hp.x, -hp.z))
		var off := absf(wrapf(brg, -22.5, 22.5))     # degrees from the nearest bay centre
		_step("spot %s wall bearing %.1f, %.1f deg off bay centre, ship %.0f m" % [c, brg, off, Vector2(s.pos.x - c.x, s.pos.y - c.y).length()])
		if off < best_off:
			best_off = off
			best = c
	return best


## [yaw, pitch] from the keeper's eye to a ship (sim pos is world x / z at sea level); north if none.
func _aim_ship(s: FleetShip) -> Array:
	if s == null:
		return [g.player._yaw, 0.0]
	var eye: Vector3 = g.player.global_position + Vector3(0, g.player.EYE, 0)
	var to := Vector3(s.pos.x, 0.5, s.pos.y) - eye
	return [atan2(-to.x, -to.z), atan2(to.y, Vector2(to.x, to.z).length())]


# ------------------------------------------------------------------ looking and pressing

func _ia_pos(id: String) -> Vector3:
	for b in g.station.get_children():
		if b is StaticBody3D and String(b.get_meta("ia", "")) == id:
			return b.global_position
	push_warning("film: no interaction volume '%s'" % id)
	return Vector3.INF


## Ease the keeper's look to (yaw, pitch) over s seconds (smoothstep), as a hand on the mouse would.
func _look(yaw: float, pitch: float, s: float) -> void:
	var p: Node = g.player
	var y0: float = p._yaw
	var p0: float = p._pitch
	var dy := wrapf(yaw - y0, -PI, PI)
	var start := t
	while t - start < s:
		var k := smoothstep(0.0, 1.0, (t - start) / s)
		p._yaw = y0 + dy * k
		p._pitch = lerpf(p0, pitch, k)
		p._apply_look()
		await get_tree().process_frame
	p._yaw = y0 + dy
	p._pitch = pitch
	p._apply_look()


func _aim_at(id: String) -> void:
	var tgt := _ia_pos(id)
	if tgt == Vector3.INF:
		return
	var p: Node = g.player
	var to: Vector3 = tgt - (p.global_position + Vector3(0, p.EYE, 0))
	var yaw := atan2(-to.x, -to.z)
	var pitch := atan2(to.y, Vector2(to.x, to.z).length())
	var ang := absf(wrapf(yaw - p._yaw, -PI, PI)) + absf(pitch - p._pitch)
	await _look(yaw, pitch, clampf(0.45 + ang * 0.55, 0.5, 2.0))


func _press(id: String) -> void:
	var hit: String = g.player._ray_hit_id(false)
	g.player._press(InputEventAction.new())
	await _wait(0.15)
	g.player._release()
	_step("press %s (aimed at %s)" % [id, hit])


## A control inside a device view: the virtual cursor goes onto it, then a press.
func _press_in_view(id: String) -> void:
	var tgt := _ia_pos(id)
	if tgt == Vector3.INF:
		return
	g.player.virtual_cursor = g.player.camera.unproject_position(tgt)
	await _wait(0.3)
	await _press(id)


# ------------------------------------------------------------------ walking

func _cell(p: Vector2) -> Vector2i:
	return Vector2i(roundi((p.x + HALF) / CELL), roundi((p.y + HALF) / CELL))


func _world(c: Vector2i) -> Vector2:
	return Vector2(c.x * CELL - HALF, c.y * CELL - HALF)


func _build_nav() -> void:
	var n := roundi(2.0 * HALF / CELL) + 1
	astar.region = Rect2i(0, 0, n, n)
	astar.cell_size = Vector2(1, 1)
	astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	astar.update()
	var space: PhysicsDirectSpaceState3D = g.player.get_world_3d().direct_space_state
	var sh := CylinderShape3D.new()
	sh.radius = 0.34                                   # the player's 0.28 capsule plus a margin
	sh.height = 1.4
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = sh
	q.collision_mask = g.player.collision_mask
	q.exclude = [g.player.get_rid()]
	var solid := 0
	for x in n:
		for z in n:
			var w := _world(Vector2i(x, z))
			q.transform = Transform3D(Basis(), Vector3(w.x, FLOOR + 0.15 + 0.7, w.y))
			if space.intersect_shape(q, 1).size() > 0:
				astar.set_point_solid(Vector2i(x, z), true)
				solid += 1
	_step("nav %dx%d solid=%d" % [n, n, solid])


func _nearest_free(c: Vector2i) -> Vector2i:
	if not astar.is_point_solid(c):
		return c
	for r in range(1, 8):
		for dx in range(-r, r + 1):
			for dz in range(-r, r + 1):
				var o := c + Vector2i(dx, dz)
				if astar.is_in_boundsv(o) and not astar.is_point_solid(o):
					return o
	return c


## Walk along an A* path with move_forward, steering the look towards a point 0.45 m ahead on the path.
func _walk_to(goal: Vector2) -> void:
	var p: Node = g.player
	var from := _nearest_free(_cell(Vector2(p.global_position.x, p.global_position.z)))
	var to := _nearest_free(_cell(goal))
	var cells: Array = astar.get_id_path(from, to)
	if cells.is_empty():
		_step("walk: no path to %s" % goal)
		return
	var pts: Array = []
	for c in cells:
		pts.append(_world(c))
	pts[-1] = _world(to)
	_step("walk to %s (%d cells)" % [goal, pts.size()])
	var i := 0
	var start := t
	while t - start < 20.0:
		var pos := Vector2(p.global_position.x, p.global_position.z)
		while i < pts.size() - 1 and pos.distance_to(pts[i]) < 0.45:
			i += 1
		var aim: Vector2 = pts[i]
		var left := pos.distance_to(pts[-1])
		if i == pts.size() - 1 and left < 0.12:
			break
		var d := aim - pos
		var want := atan2(-d.x, -d.y)
		var err := wrapf(want - p._yaw, -PI, PI)
		var dt := get_process_delta_time()
		p._yaw += clampf(err, -2.4 * dt, 2.4 * dt) if absf(err) > 0.02 else err
		p._pitch = move_toward(p._pitch, -0.12, 0.6 * dt)
		p._apply_look()
		var strength := clampf(left / 0.6, 0.35, 1.0) if absf(err) < 0.7 else 0.0
		if strength > 0.0:
			Input.action_press("move_forward", strength)
		else:
			Input.action_release("move_forward")
		await get_tree().process_frame
	Input.action_release("move_forward")
	await _wait(0.35)                                  # let the body settle (velocity eases out)
