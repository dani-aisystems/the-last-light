## G3c (Daniel 2026-11-08): the keeper's body. Legs, boots and torso are seen when he looks down; his arms
## and head only cast shadows (the G3b camera hands stay). Walks and idles by ground speed, sits on the
## chair in the radio view (item 24), and is put away in the other device views.
## body.glb: blender/body.py (front is +Z after the glTF axis change, so it turns half round to face -Z).
class_name PlayerBody
extends Node3D

const WALK_SPEED := 1.6          # the speed the walk cycle is keyed for (body.py: two 0.72 m steps in 0.9 s)
const BODY_BACK := 0.12          # metres behind the eye looking level ...
const BODY_BACK_DOWN := 0.28     # ... and looking straight down, so the view clears the chest to the legs and boots
const BLEND := 0.25
const SEAT_EYE_FWD := 0.03       # seated: the eye a little ahead of the head bone

var player: Node
var body: Node3D
var ap: AnimationPlayer
var skel: Skeleton3D
var meshes := {}                 # "view" / "shadow" -> MeshInstance3D
var state := ""                  # "idle" / "walk" / "turn" / "sit" / "away"
var _yaw_prev := 0.0
var _turn_rate := 0.0
var _seat_off := Vector3.ZERO    # sit pose: the head bone relative to the body origin (body frame)


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
		mi.layers = station.LAYER_INTERIOR                # lit by the room lights, as the props are
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if k == "view" \
			else GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	ap.play("sit")
	ap.seek(0.0, true)
	var hb := skel.find_bone("head")
	_seat_off = skel.get_bone_global_pose(hb).origin                  # body frame (skeleton at the body origin)
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
	if f == "radio":
		_sit()
		return
	if f != "":
		visible = false                                   # another device view: the camera is elsewhere
		state = "away"
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


## The radio view: seated on the chair, the head under the view's eye, facing the set.
func _sit() -> void:
	visible = true
	state = "sit"
	_play("sit")
	var fv: Dictionary = player.station.focus.get("radio", {})
	if not fv.has("eye"):
		return
	var eye: Vector3 = fv["eye"]
	var at: Vector3 = fv.get("at", eye + Vector3.FORWARD)
	var look := at - eye
	var yaw := atan2(-look.x, -look.z)
	var b := Basis(Vector3.UP, yaw + PI)
	var fwd := Vector3(-sin(yaw), 0.0, -cos(yaw))
	var head_world := b * _seat_off                       # the head relative to the origin, turned
	var want := eye - fwd * SEAT_EYE_FWD
	global_transform = Transform3D(b, Vector3(want.x - head_world.x, player.global_position.y, want.z - head_world.z))


## The lowest foot bone in world space (tests: contact and sliding).
func foot_positions() -> Dictionary:
	var out := {}
	for s in ["L", "R"]:
		var bi := skel.find_bone("foot." + s)
		out[s] = skel.global_transform * skel.get_bone_global_pose(bi).origin
	return out
