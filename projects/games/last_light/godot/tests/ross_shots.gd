extends SceneTree
## Audit Stage R, part 2: in-game frames of Ross's staging (visitor_figure.gd) that capture_fp.gd has no
## state for: the live walk-in after the door swings, the walk to the wheel and the wheel pose (D), the walk
## to the chair and the chair pose (C), the seated look back at C, and a close look at the wet coat. It boots
## the real main scene and drives the real game_fp / station / director, so the figure stages itself exactly
## as in play; only the story state is set by hand (the director is held). Needs a window (rendering), and
## runs silent:
##   tools/godot_bg --path projects/games/last_light/godot -s res://tests/ross_shots.gd -- --tag=r2
## Writes renders/last_light/<tag>_*.png and prints ROSS_SHOTS_RESULT {json}.

const F := 20.0

var main: Node
var cam: Camera3D
var out_dir := ""
var tag := "r2"
var files: Array = []
var notes: Array = []


func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--tag="):
			tag = a.substr(6)
	_run.call_deferred()


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _secs(s: float) -> void:
	var t := 0.0
	while t < s:
		await process_frame
		t += root.get_process_delta_time() if root.get_process_delta_time() > 0.0 else 1.0 / 60.0


static func Fig_pos(key: String) -> Vector3:
	return (load("res://scripts/fp/visitor_figure.gd")).mark_position(key)


static func _pt(bearing: float, dist: float, z: float) -> Vector3:
	var b := deg_to_rad(bearing)
	return Vector3(sin(b) * dist, F + z, -cos(b) * dist)


func _view(eye: Vector3, at: Vector3, fov: float) -> void:
	cam.global_position = eye
	cam.look_at(at, Vector3.UP)
	cam.fov = fov
	cam.current = true


func _save(name_: String, fig: Node) -> void:
	await _frames(2)
	var img := root.get_viewport().get_texture().get_image()
	if img.get_width() != 1920:
		img.resize(1920, int(1920.0 * img.get_height() / img.get_width()), Image.INTERPOLATE_LANCZOS)
	var path := out_dir.path_join("%s_%s.png" % [tag, name_])
	img.save_png(path)
	files.append(path)
	var an: String = fig.ap.current_animation if fig and fig.ap else ""
	notes.append({"shot": name_, "visible": fig.visible if fig else false, "mark": fig.mark if fig else "",
		"walking": fig.is_walking() if fig else false, "anim": an,
		"pos": [snappedf(fig.global_position.x, 0.001), snappedf(fig.global_position.z, 0.001)] if fig else []})
	print("SHOT ", path)
	if fig and fig.head_turn:
		var gg = main.game
		print("HEAD ", name_, " yaw=", snappedf(fig.head_turn.yaw, 0.001), " target=", snappedf(fig.head_turn_target(), 0.001),
			" cam=", gg.player.camera.global_position, " player=", gg.player.global_position, " active=", fig.head_turn.active,
			" in_tree=", fig.head_turn.is_inside_tree())


func _run() -> void:
	AudioServer.set_bus_mute(0, true)
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_size(Vector2i(1920, 1080))
	out_dir = ProjectSettings.globalize_path("res://").path_join("../../../../renders/last_light").simplify_path()
	main = (load("res://scenes/main_fp.tscn") as PackedScene).instantiate()
	root.add_child(main)
	await _frames(30)
	main.start_game("expert", true)
	await _secs(4.0)
	var g = main.game
	g.director.process_mode = Node.PROCESS_MODE_DISABLED       # the story state is set by hand below
	g.player.enabled = false
	if g.player.body:
		g.player.body.process_mode = Node.PROCESS_MODE_DISABLED
		g.player.body.visible = false
	g.ui.visible = false
	if g.presenter.get("dialogue"):
		g.presenter.dialogue.visible = false
	cam = Camera3D.new()
	cam.near = 0.03
	cam.far = 500.0
	g.add_child(cam)
	var door_eye := _pt(170.0, 0.2, 1.65)
	var door_at := _pt(170.0, 2.0, 1.1)
	_view(door_eye, door_at, 55.0)                # capture_fp's cu_door
	await _frames(20)
	(g.presenter.fade as ColorRect).color.a = 0.0
	# 1. the live walk-in: the door opens, he is spawned mid-conversation (as ch4_door's "! visitor_enter")
	g.station.door_open = true
	g.director._talking = true
	g._spawn_visitor()
	await _frames(3)
	g.director._talking = false
	var fig = g.visitor_fig
	for t in [[1.4, "in_a_swinging"], [0.8, "in_b_landing"], [0.45, "in_c_doorway"], [0.45, "in_d_inside"],
			[1.0, "in_e_arrived"], [2.0, "in_f_door_pose"]]:
		await _secs(t[0])
		await _save(t[1], fig)
	# 2. ch6, "Two men to one wheel": ross_wheel. Watched from the west side, toward the console.
	g.director.state.chapter = 6
	g.director.state.flags["ross_wheel"] = 1
	_view(_pt(-110.0, 0.5, 1.65), _pt(78.0, 3.0, 0.95), 72.0)     # capture_fp's fp_console
	await _secs(1.6)
	await _save("wheel_a_walking", fig)
	await _secs(4.0)
	await _save("wheel_b_pose", fig)
	_view(_pt(20.0, 0.9, 1.6), _pt(76.0, 1.8, 0.9), 50.0)
	await _save("wheel_c_close", fig)
	# 3. the rescue beat: he comes to the radio, behind the chair (C)
	g.director.state.beat = 4                                     # chapters.json ch6: iona, jam, free, standby, rescue
	_view(_pt(120.0, 1.3, 1.65), _pt(20.0, 1.3, 1.1), 72.0)
	await _secs(2.0)
	await _save("chair_a_walking", fig)
	await _secs(4.5)
	_view(_pt(50.0, 1.9, 1.65), _pt(0.0, 1.16, 1.2), 60.0)
	await _save("chair_b_pose", fig)
	_view(_pt(4.0, 1.62, 1.2), _pt(4.0, 1.0, 1.75), 72.0)         # seated at the radio, looking back up at him
	await _save("chair_c_seated_look", fig)
	# 4. the nearest standing views: face-on to him at B from 1.3 m (he faces 330, into the room), and 3/4
	g.director.state.chapter = 4                  # back to the door scene, so the story keeps him at B
	g.director.state.beat = 0
	g.director.state.flags.erase("ross_wheel")
	fig.place("B")
	var head_b := Fig_pos("B") + Vector3(0, 1.45, 0)
	_view(_pt(197.0, 1.3, 1.65), head_b, 60.0)
	await _secs(0.6)
	await _save("b_close_front", fig)
	_view(_pt(150.0, 1.6, 1.65), head_b, 50.0)
	await _save("b_close_q34", fig)
	# 5. he turns his head to the keeper: the same camera, the keeper behind him (on the landing), then 2 m
	# away 35 degrees to his left
	var FigS = load("res://scripts/fp/visitor_figure.gd")
	var face: float = FigS.bearing_yaw(330.0)
	var bp: Vector3 = Fig_pos("B")
	# the player is disabled here, so its camera (positioned by the player's own update) is moved with it
	g.player.global_position = Fig_pos("A")
	g.player.camera.global_position = Fig_pos("A") + Vector3(0, 1.65, 0)
	_view(_pt(205.0, 1.25, 1.62), bp + Vector3(0, 1.5, 0), 45.0)
	await _secs(2.5)
	await _save("head_a_keeper_behind", fig)
	g.player.global_position = bp + Vector3(sin(face + 0.61), 0.0, cos(face + 0.61)) * 2.0
	g.player.camera.global_position = g.player.global_position + Vector3(0, 1.65, 0)
	await _secs(2.5)
	await _save("head_b_keeper_left", fig)
	print("ROSS_SHOTS_RESULT ", JSON.stringify({"files": files, "notes": notes}))
	quit(0)
