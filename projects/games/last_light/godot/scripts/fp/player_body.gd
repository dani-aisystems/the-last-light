## G3c (Daniel 2026-11-08): the keeper's body. Legs, boots and torso are seen when he looks down; his arms
## and head only cast shadows (the G3b camera hands stay). Walks and idles by ground speed, sits on the
## chair in the radio view (item 24), and is put away in the other device views.
## body.glb: blender/body.py (front is +Z after the glTF axis change, so it turns half round to face -Z).
## Audit Stage P (C11): sitting down and standing up follow the camera. Each frame the body is placed from the
## camera's CURRENT (blended) transform and posed by player.sit_amount() on the sitdown clip, so the head is
## always under the eye; before, the body was seated on the chair on the frame E was pressed and the
## still-standing camera looked at a headless torso (Stage 0 a0_sheet_sit, Stage P p0_sheet_sit).
class_name PlayerBody
extends Node3D

const WALK_SPEED := 1.6          # the speed the walk cycle is keyed for (body.py: two 0.72 m steps in 0.9 s)
const BODY_BACK := 0.12          # metres behind the eye looking level ...
const BODY_BACK_DOWN := 0.28     # ... and looking straight down, so the view clears the chest to the legs and boots
const BLEND := 0.25
const SEAT_EYE_FWD := 0.03       # seated: the eye a little ahead of the head bone

const LAYER_BODY := 4096                  # R4: render layer 13, the keeper's own body (see the torch)
var player: Node
var body: Node3D
var ap: AnimationPlayer
var skel: Skeleton3D
var meshes := {}                 # "view" / "shadow" -> MeshInstance3D
var state := ""                  # "idle" / "walk" / "turn" / "sit" / "away"
var _yaw_prev := 0.0
var _turn_rate := 0.0
var _head_at := PackedVector3Array()   # the head bone in the body frame at s = 0, 0.1 .. 1 of sitdown
const SIT_SAMPLES := 11


func setup(p: Node, station: Node) -> void:
	player = p
	var scn: PackedScene = load("res://assets/models/body.glb")
	if scn == null:
		return
	body = scn.instantiate()
	add_child(body)
	ap = body.get_node("AnimationPlayer")
	skel = body.get_node("ARM_body/Skeleton3D")
	for an in ["idle", "walk"]:
		ap.get_animation(an).loop_mode = Animation.LOOP_LINEAR
	meshes["view"] = skel.get_node("SK_body")
	meshes["shadow"] = skel.get_node("SK_body_shadow")
	for k in meshes:
		var mi: MeshInstance3D = meshes[k]
		mi.layers = station.LAYER_INTERIOR | LAYER_BODY   # lit by the room lights, as the props are
		# (R4: LAYER_BODY lets the torch leave the body out of its shadow casters: held in front of the
		# chest, its beam was sliced by the torso and arm when looking down)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if k == "view" \
			else GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
		if (get_node("/root/GameState").user_args as Dictionary).has("nobodyshadow"):   # perf bisect (debug only): the body casts nothing (run-time lookup: tests compile this class before autoloads)
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			if k == "shadow":
				mi.visible = false
	for k in meshes:
		fabric_rim((meshes[k] as MeshInstance3D).mesh)
	var hb := skel.find_bone("head")
	ap.play("sitdown")
	var sl: float = ap.get_animation("sitdown").length
	for i in SIT_SAMPLES:
		ap.seek(sl * i / float(SIT_SAMPLES - 1), true)
		_head_at.append(skel.get_bone_global_pose(hb).origin)          # body frame (skeleton at the body origin)
	process_priority = 10              # after the player, which moves the camera this frame
	_play("idle")
	_yaw_prev = player._yaw


func _play(an: String, speed := 1.0) -> void:
	if ap.current_animation != an:
		ap.play(an, BLEND)
	ap.speed_scale = speed


func _process(delta: float) -> void:
	if body == null or player == null:
		return
	var f: String = player.focused
	if f != "" and f != "radio":
		visible = false                                   # another device view: the camera is elsewhere
		state = "away"
		return
	var s: float = player.sit_amount()
	if f == "radio" or s > 0.0:
		_sit(s)
		return
	visible = true
	var home: Transform3D = player._home()
	var yaw: float = player._yaw
	var dyaw := wrapf(yaw - _yaw_prev, -PI, PI)
	_yaw_prev = yaw
	_turn_rate = lerpf(_turn_rate, absf(dyaw) / maxf(delta, 1e-4), clampf(delta * 8.0, 0.0, 1.0))
	var fwd := Vector3(-sin(yaw), 0.0, -cos(yaw))
	var down := clampf(-float(player._pitch) / 1.45, 0.0, 1.0)
	var feet := Vector3(home.origin.x, player.global_position.y, home.origin.z) - fwd * lerpf(BODY_BACK, BODY_BACK_DOWN, down)
	global_transform = Transform3D(Basis(Vector3.UP, yaw + PI), feet)
	var v: Vector3 = player.velocity
	var spd := Vector2(v.x, v.z).length()
	if spd > 0.15:
		state = "walk"
		_play("walk", spd / WALK_SPEED)
	elif _turn_rate > 1.2:
		state = "turn"                                    # stepping round on the spot
		_play("walk", 0.5)
	else:
		state = "idle"
		_play("idle")


## Sitting down at the radio (s 0 standing .. 1 seated) and standing up again, under the camera as it moves:
## the sitdown clip held at s, the body turned to the camera's heading, and its origin blended from the walk
## rule (feet BODY_BACK behind the eye) to the seat rule (the head bone under the eye) by the same s. At s 1
## with the camera at the view's eye this is the G3c seated placement exactly.
func _sit(s: float) -> void:
	visible = true
	state = "sit"
	_yaw_prev = player._yaw
	_turn_rate = 0.0
	if ap.current_animation != "sitdown":
		ap.play("sitdown")
	ap.speed_scale = 0.0
	ap.seek(ap.get_animation("sitdown").length * s, true)
	var cam: Transform3D = player.camera.global_transform
	var eul := cam.basis.get_euler()                      # YXZ: y the heading, x the pitch (both views are level-rolled)
	var yaw := eul.y
	var b := Basis(Vector3.UP, yaw + PI)
	var fwd := Vector3(-sin(yaw), 0.0, -cos(yaw))
	var down := clampf(-eul.x / 1.45, 0.0, 1.0)
	var walk := cam.origin - fwd * lerpf(BODY_BACK, BODY_BACK_DOWN, down)
	var seat := cam.origin - fwd * SEAT_EYE_FWD - b * head_offset(s)
	var o := walk.lerp(seat, s)
	global_transform = Transform3D(b, Vector3(o.x, player.global_position.y, o.z))


## The head bone in the body frame at sit amount s (from the table built in setup).
func head_offset(s: float) -> Vector3:
	var x := clampf(s, 0.0, 1.0) * (SIT_SAMPLES - 1)
	var i := mini(int(x), SIT_SAMPLES - 2)
	return _head_at[i].lerp(_head_at[i + 1], x - i)


## Audit Stage P (4.1, item 6): Godot's glTF import drops KHR_materials_sheen, so wool and cloth get the
## StandardMaterial3D rim term instead (a soft lift at grazing angles, as fibres catch the light). Applied to
## the guernsey, darn and trousers surfaces of a mesh (equipment.gd uses it for the sleeves too).
const RIM := {"M_LL_Guernsey": 0.35, "M_LL_GuernseyRib": 0.35, "M_LL_GuernseyDarn": 0.35, "M_LL_Trousers": 0.2,
	"M_LL_Shirt": 0.15}


static func fabric_rim(m: Mesh) -> void:
	if m == null:
		return
	for s in m.get_surface_count():
		var mat := m.surface_get_material(s) as StandardMaterial3D
		if mat and RIM.has(mat.resource_name):
			mat.rim_enabled = true
			mat.rim = RIM[mat.resource_name]
			mat.rim_tint = 0.6               # toward the cloth's own colour, not white


## The lowest foot bone in world space (tests: contact and sliding).
func foot_positions() -> Dictionary:
	var out := {}
	for s in ["L", "R"]:
		var bi := skel.find_bone("foot." + s)
		out[s] = skel.global_transform * skel.get_bone_global_pose(bi).origin
	return out
