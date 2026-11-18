extends SceneTree
## Audit Stage R: Ross as a rigged figure (assets/models/ross.glb from blender/ross.py; visitor_figure.gd).
##  R1  the model: one skinned mesh under ARM_ross/Skeleton3D, within budget (<= 25k triangles, 2 materials),
##      the five actions (idle, walk, door, chair, wheel), the coat's clearcoat and the stubble's alpha
##      scissor survived the import
##  R2  each held pose, stood on its mark, puts the hand bone where Blender's IK put it (the spec hand target,
##      ross.py place_and_pose): within 3 cm
##  R3  staging (a stand-in game: director, station, presenter): live, he is hidden until the door has swung,
##      then walks A -> B and holds the jamb; ross_wheel walks him to D; the rescue beat walks him to C;
##      a loaded save puts him on his mark at once; a black screen hides a move (no walk)
##  R4  the walk: the root moves at the clip's ground speed (ross.py walk_speed) and no step leaves the route
##  R5  the head turns toward the keeper standing 30 degrees to his left (and stops at 35 for one at 70), not for
##      one behind him or out of range, and never while he walks
##   tools/godot --headless --path godot -s res://tests/ross_test.gd

const Fig := preload("res://scripts/fp/visitor_figure.gd")

var fails: Array[String] = []
var passes := 0


class FakeState:
	extends RefCounted
	var chapter := 4
	var flags := {}

	func has_flag(n: String) -> bool:
		return bool(flags.get(n, false))


class FakeDirector:
	extends RefCounted
	var state := FakeState.new()
	var talking := false
	var reached := {}

	func is_talking() -> bool:
		return talking

	func beat_reached(id: String) -> bool:
		return bool(reached.get(id, false))


class FakeStation:
	extends RefCounted
	var swing := 0.0

	func door_phase() -> Vector2:
		return Vector2(1.0, swing)


class FakePresenter:
	extends RefCounted
	var fade := ColorRect.new()


class FakeGame:
	extends Node
	var director = FakeDirector.new()
	var station = FakeStation.new()
	var presenter = null
	var player = null


func _initialize() -> void:
	_run.call_deferred()


func _ok(cond: bool, what: String) -> void:
	if cond:
		passes += 1
	else:
		fails.append(what)


func _run() -> void:
	_r1()
	await _r2()
	await _r3()
	await _r5()
	print("ROSS_RESULT ", JSON.stringify({"passed": passes, "failed": fails.size(), "failures": fails}))
	quit(1 if fails.size() > 0 else 0)


func _r1() -> void:
	var sc := load(Fig.MODEL) as PackedScene
	_ok(sc != null, "R1 ross.glb loads")
	if sc == null:
		return
	var m := sc.instantiate()
	var ap := m.get_node_or_null("AnimationPlayer") as AnimationPlayer
	_ok(ap != null, "R1 AnimationPlayer")
	if ap:
		for an in ["idle", "walk", "door", "chair", "wheel"]:
			_ok(ap.has_animation(an), "R1 action %s" % an)
	var sk := m.find_child("Skeleton3D", true, false) as Skeleton3D
	_ok(sk != null and sk.find_bone("hand.L") >= 0 and sk.find_bone("index_3.R") >= 0, "R1 skeleton with finger bones")
	var tris := 0
	var mats := {}
	var meshes := 0
	for mi in m.find_children("*", "MeshInstance3D", true, false):
		var mesh := (mi as MeshInstance3D).mesh
		if mesh == null:
			continue
		meshes += 1
		for s in mesh.get_surface_count():
			var arr := mesh.surface_get_arrays(s)
			var idx = arr[Mesh.ARRAY_INDEX]
			tris += (idx.size() if idx != null else (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()) / 3
			var mat := mesh.surface_get_material(s) as StandardMaterial3D
			if mat:
				mats[mat.resource_name] = mat
	_ok(meshes == 1, "R1 one mesh (got %d)" % meshes)
	_ok(tris > 15000 and tris <= 25000, "R1 triangles within budget (got %d)" % tris)
	_ok(mats.size() == 2, "R1 two materials (got %s)" % [mats.keys()])
	var oil: StandardMaterial3D = mats.get("M_LL_Ross_Oilskin")
	var skin: StandardMaterial3D = mats.get("M_LL_Ross_Skin")
	_ok(oil != null and oil.roughness_texture != null, "R1 the oilskin's ORM imported (roughness from green)")
	_ok(oil != null and oil.cull_mode == BaseMaterial3D.CULL_DISABLED, "R1 the oilskin is double-sided")
	_ok(skin != null and skin.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR, "R1 the stubble is alpha scissor")
	m.free()
	# the figure restores what the import drops: the clearcoat (wet mask in the ORM's red) and the cloth rim
	var fig := Fig.new()
	root.add_child(fig)
	var oil2: StandardMaterial3D = null
	for mi in fig.find_children("*", "MeshInstance3D", true, false):
		var mesh := (mi as MeshInstance3D).mesh
		for s in mesh.get_surface_count():
			var mt := mesh.surface_get_material(s) as StandardMaterial3D
			if mt and mt.resource_name == "M_LL_Ross_Oilskin":
				oil2 = mt
	_ok(oil2 != null and oil2.clearcoat_enabled and oil2.clearcoat_texture == oil2.roughness_texture, "R1 the figure's oilskin has its clearcoat")
	_ok(oil2 != null and oil2.rim_enabled, "R1 the figure's oilskin has the cloth rim")
	fig.free()


## The hand bone's target as ross.py place_and_pose sets it, in Blender room coordinates, then to Godot.
func _wrist_target(key: String, grip: String, side: String) -> Vector3:
	var spec := {"B": [182.4, 2.585, 1.05], "C": [7.42, 1.548, 0.94], "D": [72.78, 2.094, 0.70]}
	var h: Array = spec[key]
	var b := deg_to_rad(float(h[0]))
	var hand := Vector3(sin(b) * float(h[1]), cos(b) * float(h[1]), 20.0 + float(h[2]))   # Blender x, y, z
	var fb := deg_to_rad(float(Fig.MARKS[key][3]))
	var f := Vector3(sin(fb), cos(fb), 0.0)
	var rt := f.cross(Vector3(0, 0, 1))
	var up := Vector3(0, 0, 1)
	var w: Vector3
	if grip == "rail":
		w = hand + up * 0.045 - f * 0.075 + rt * (0.012 if side == "L" else -0.012)
	else:
		var n := -Vector3(hand.x, hand.y, 0.0).normalized()
		w = hand + up * 0.07 + n * 0.03
	return Vector3(w.x, w.z, -w.y)


func _r2() -> void:
	var g := FakeGame.new()
	root.add_child(g)
	var fig := Fig.new()
	g.add_child(fig)
	await process_frame
	fig.set_process(false)
	for c in [["B", "flat", "L"], ["C", "rail", "R"], ["D", "rail", "R"]]:
		fig.place(c[0])
		fig.ap.play(Fig.POSE[c[0]], 0.0)
		fig.ap.seek(0.0, true)
		await process_frame
		await process_frame
		var got: Vector3 = fig.bone_world("hand.%s" % c[2])
		var want := _wrist_target(c[0], c[1], c[2])
		var err := got.distance_to(want)
		_ok(err < 0.03, "R2 %s hand.%s on its contact: %.3f m off (got %s, want %s)" % [c[0], c[2], err, got, want])
		print("R2 %s hand err %.4f m" % [c[0], err])
	g.queue_free()
	await process_frame


func _drive(fig: Node, secs: float, dt := 0.05) -> void:
	for i in roundi(secs / dt):
		fig._process(dt)


func _r3() -> void:
	# live entrance
	var g := FakeGame.new()
	root.add_child(g)
	g.director.talking = true
	g.station.swing = 0.2
	var fig := Fig.new()
	g.add_child(fig)
	await process_frame
	fig.set_process(false)
	_ok(not fig.visible, "R3 live: hidden while the door is still swinging")
	_drive(fig, 0.5)
	_ok(not fig.visible, "R3 live: still hidden at swing 0.2")
	g.station.swing = 0.85
	_drive(fig, 0.1)
	_ok(fig.visible and fig.is_walking(), "R3 live: steps in once the door has swung")
	# R4: speed and route
	var p0: Vector3 = fig.global_position
	_drive(fig, 0.5)
	var v := Vector2(fig.global_position.x - p0.x, fig.global_position.z - p0.z).length() / 0.5
	_ok(absf(v - Fig.WALK_SPEED) < 0.05, "R4 walks at the clip's ground speed (%.3f m/s)" % v)
	_drive(fig, 4.0)
	_ok(fig.mark == "B" and not fig.is_walking(), "R3 live: arrives at B")
	_ok(fig.global_position.distance_to(Fig.mark_position("B")) < 0.01, "R3 live: on mark B")
	_ok(fig.ap.current_animation == "door", "R3 live: holds the jamb at B (got %s)" % fig.ap.current_animation)
	var yaw := fig.global_basis.get_euler().y
	_ok(absf(wrapf(yaw - Fig.bearing_yaw(330.0), -PI, PI)) < 0.02, "R3 live: faces B's bearing after settling")
	# ch6: the wheel, then the rescue call
	g.director.talking = false
	g.director.state.chapter = 6
	g.director.state.flags["ross_wheel"] = true
	_drive(fig, 0.3)
	_ok(fig.mark == "D" and fig.is_walking(), "R3 ross_wheel: walks to the wheel")
	var max_off := 0.0
	var a := Fig.mark_position("B")
	var b := Fig.mark_position("D")
	for i in 120:
		fig._process(0.05)
		var p: Vector3 = fig.global_position
		var ab := Vector2(b.x - a.x, b.z - a.z)
		var ap_ := Vector2(p.x - a.x, p.z - a.z)
		var t := clampf(ap_.dot(ab) / ab.length_squared(), 0.0, 1.0)
		max_off = maxf(max_off, (ap_ - ab * t).length())
	_ok(max_off < 0.02, "R4 B -> D stays on its straight route (%.3f m off)" % max_off)
	_ok(fig.mark == "D" and not fig.is_walking() and fig.ap.current_animation == "wheel", "R3 at D, on the wheel")
	g.director.reached["rescue"] = true
	_drive(fig, 8.0)
	_ok(fig.mark == "C" and not fig.is_walking() and fig.ap.current_animation == "chair", "R3 rescue: behind the chair (C)")
	_ok(fig.global_position.distance_to(Fig.mark_position("C")) < 0.01, "R3 on mark C")
	g.queue_free()
	await process_frame
	# a loaded save in ch6 after the rescue: on C at once
	var g2 := FakeGame.new()
	root.add_child(g2)
	g2.director.state.chapter = 6
	g2.director.reached["rescue"] = true
	var f2 := Fig.new()
	g2.add_child(f2)
	await process_frame
	_ok(f2.visible and f2.mark == "C" and not f2.is_walking(), "R3 load: on C at once")
	_ok(f2.ap.current_animation == "chair", "R3 load: the chair pose")
	# a black screen hides a move
	f2.set_process(false)
	g2.presenter = FakePresenter.new()
	(g2.presenter.fade as ColorRect).color = Color(0, 0, 0, 1)
	g2.director.reached["rescue"] = false
	_drive(f2, 0.3)
	_ok(f2.mark == "B" and not f2.is_walking(), "R3 a black screen: moved without a walk")
	(g2.presenter.fade as ColorRect).free()
	g2.queue_free()
	await process_frame


## The head bone's side axis, flattened: its yaw in the world, read in the final (modified) pose the skin
## gets: a modifier's change lives only inside the skeleton's update, so it is read on skeleton_updated.
var _hy := 0.0


func _head_yaw(fig) -> float:
	var sk: Skeleton3D = fig.skel
	var grab := func() -> void:
		var b: Basis = (sk.global_transform * sk.get_bone_global_pose(sk.find_bone("head"))).basis
		_hy = atan2(b.x.x, b.x.z)
	sk.skeleton_updated.connect(grab, CONNECT_ONE_SHOT)
	await sk.skeleton_updated
	await process_frame
	return _hy


func _settle_head(fig, want: float) -> bool:
	for i in 900:
		await process_frame
		if absf(fig.head_turn.yaw - want) < 0.01:
			return true
	return false


func _r5() -> void:
	var g := FakeGame.new()
	root.add_child(g)
	var fig := Fig.new()
	g.add_child(fig)
	await process_frame
	await process_frame
	fig.set_process(false)
	fig.place("B")
	var p := Node3D.new()
	g.add_child(p)
	g.player = p
	var face := Fig.bearing_yaw(330.0)
	var at := func(off_deg: float, dist: float) -> Vector3:
		var y := face + deg_to_rad(off_deg)
		return fig.global_position + Vector3(sin(y), 0.0, cos(y)) * dist + Vector3(0, 1.65, 0)
	p.global_position = at.call(0.0, 2.0)
	_ok(await _settle_head(fig, 0.0), "R5 straight ahead: no turn")
	var y0: float = await _head_yaw(fig)
	p.global_position = at.call(30.0, 2.0)
	_ok(await _settle_head(fig, deg_to_rad(30.0)), "R5 keeper 30 deg left: turns 30 (got %.1f)" % rad_to_deg(fig.head_turn.yaw))
	var y1: float = await _head_yaw(fig)
	var dy := wrapf(y1 - y0, -PI, PI)
	_ok(absf(dy - deg_to_rad(30.0)) < deg_to_rad(4.0), "R5 the head bone really turned 30 deg (got %.1f)" % rad_to_deg(dy))
	p.global_position = at.call(70.0, 2.0)
	_ok(await _settle_head(fig, Fig.HEAD_MAX), "R5 keeper 70 deg left: stops at 35")
	p.global_position = at.call(160.0, 2.0)
	_ok(await _settle_head(fig, 0.0), "R5 keeper behind him: no turn")
	p.global_position = at.call(-30.0, 5.0)
	_ok(await _settle_head(fig, 0.0), "R5 keeper 5 m away: no turn")
	p.global_position = at.call(-30.0, 2.0)
	fig.walk_to("C")
	_ok(fig.head_turn_target() == 0.0, "R5 no turn while walking")
	g.queue_free()
	await process_frame
