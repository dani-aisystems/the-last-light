extends Node3D
## Alasdair Ross (audit Stage R): the rigged figure built in blender/ross.py (assets/models/ross.glb; the
## CC0 Blender Studio base mesh, an oilskin, sou'wester and sea boots, body.py's rig with hands.py's fingers).
## The brim keeps his eyes dark from every standing view (NARRATIVE.md: read through light and posture, not a
## face); the stills and ray sweep are in docs/last_light/audit-2026-11/17_stageR_evidence.md.
##
## game_fp owns this node (_spawn_visitor, the save's "visitor", the capture restore that frees it) and sets
## where it first stands. This script then stages him from the story, without touching the story:
##   * live (a conversation is running when he is spawned): he waits for the door to swing, then walks in from
##     the stair landing (mark A) through the doorway to just inside it (B);
##   * a loaded save or a capture: he is on his mark at once;
##   * B: just inside the door, left hand on the jamb (ch4, ch5: "He won't take the chair");
##   * D: at the console handwheel once he has the wheel (ross_wheel, ch6 "Two men to one wheel");
##   * C: behind the desk chair, a hand on its back, from the rescue call on (ch6: "Hand Ross the handset",
##     and at dawn "Ross lets go of the back of the chair").
## Each held pose was solved in Blender at its mark (IK to the spec hand target), so the root must stand on the
## mark facing its bearing. Moves are walked at the walk clip's own ground speed, so the boots do not skate.

const MODEL := "res://assets/models/ross.glb"
const FLOOR_Y := 20.0
# spec.py ross_marks (verified by ross.py --marks): [bearing deg, distance from the room centre m, z above the
# floor m, facing bearing deg]
const MARKS := {
	"A": [160.7, 2.878, 0.006, 345.0],
	"B": [176.74, 2.129, 0.0, 330.0],
	"C": [0.0, 1.16, 0.0, 0.0],
	"D": [76.91, 1.766, 0.0, 60.0],
}
const POSE := {"A": "idle", "B": "door", "C": "chair", "D": "wheel"}
# walking routes between marks, as [bearing, dist] waypoints (renders/last_light/stageR/marks/plan_room.png):
# through the doorway's centre; B to D passes the open leaf's free edge by about 0.5 m; D to C steps back
# toward the room centre first, clear of the console stool by 0.8 m
const ROUTES := {
	"AB": [[170.0, 2.45]],
	"BD": [],
	"DC": [[82.0, 1.11]],
	"BC": [[150.0, 1.2]],
}
const WALK_SPEED := 0.953      # m/s: ross.py walk_speed, the planted foot's slide in the walk clip
const TURN_RATE := 3.0         # rad/s while walking
const SETTLE_S := 0.6          # turning onto a mark's facing at the end of a walk
const BLEND := 0.35
const DOOR_SWING_TO_ENTER := 0.8   # he steps in once the leaf is this far through its swing
# Godot's glTF import drops sheen; the waxed cotton gets the rim term (as player_body.gd's wool) so the black
# coat's outline catches the room lamps instead of reading as a cut-out
const RIM := {"M_LL_Ross_Oilskin": 0.18}
# the import also drops KHR_materials_clearcoat (the water film on the wax). The ORM texture it keeps as the
# roughness map carries the wet mask in red, as Godot's clearcoat texture reads it (strength red, roughness
# scale green): the shoulders, hat and rain runs get the film back
# r2 close-up (2026-11-18): at [1.0, 0.25] each lamp made a mirror-sharp hot spot on the wet shoulders and the
# coat read as black plastic; [0.6, 0.6] is a broader, softer film
const CLEARCOAT := {"M_LL_Ross_Oilskin": [0.6, 0.6]}      # [strength, roughness scale]
const NORMAL_SCALE := {"M_LL_Ross_Oilskin": 1.6}          # the folds and the wax crumple, which the film had flattened
# he acknowledges the keeper: standing (not walking), the head turns toward the player's eye when the keeper is
# within HEAD_RANGE and in front of him, at most HEAD_MAX either way. Yaw only, so the brim stays down over the
# eyes (part 1's ray sweep: no eye surface seen and lit from 0 to 90 degrees off his face).
const HEAD_RANGE := 3.5
const HEAD_MAX := 0.61         # 35 degrees
const HEAD_FRONT := 1.9        # rad: beyond about 110 degrees off his facing the keeper is behind him; no turn
const HEAD_EASE := 2.5         # 1/s, the turn's exponential ease

var mark := ""                 # where he stands (or is walking to)
var model: Node3D
var ap: AnimationPlayer
var skel: Skeleton3D
var _path: Array[Vector3] = []
var _waiting_door := false
var _settle := 0.0
var _settle_from := 0.0
var _check_t := 0.0
var head_turn: HeadTurn


## Runs after the animation each frame (Skeleton3D modifier): neck 40 %, head 60 % of the turn about the
## vertical, so a stooped head turns sideways and keeps its downward tilt.
class HeadTurn:
	extends SkeletonModifier3D
	var fig: Node3D
	var yaw := 0.0

	func _process_modification_with_delta(delta: float) -> void:
		var sk := get_skeleton()
		if sk == null or fig == null:
			return
		var want: float = fig.head_turn_target()
		yaw = lerpf(yaw, want, 1.0 - exp(-fig.HEAD_EASE * delta))
		if absf(yaw) < 0.0005:
			return
		for pair in [["neck", 0.4], ["head", 0.6]]:
			var b := sk.find_bone(pair[0])
			if b < 0:
				continue
			var parent := sk.get_bone_parent(b)
			var pg: Transform3D = sk.get_bone_global_pose(parent) if parent >= 0 else Transform3D()
			var g: Transform3D = sk.get_bone_global_pose(b)
			var nb := Basis(Vector3.UP, yaw * float(pair[1])) * g.basis
			sk.set_bone_pose_rotation(b, (pg.basis.inverse() * nb).get_rotation_quaternion())


func _ready() -> void:
	model = (load(MODEL) as PackedScene).instantiate()
	add_child(model)
	ap = model.get_node_or_null("AnimationPlayer")
	skel = model.find_child("Skeleton3D", true, false)
	if ap:
		for an in ap.get_animation_list():
			ap.get_animation(an).loop_mode = Animation.LOOP_LINEAR
		ap.play("idle")
	for mi in model.find_children("*", "MeshInstance3D", true, false):
		var m := (mi as MeshInstance3D).mesh
		if m == null:
			continue
		for s in m.get_surface_count():
			var mat := m.surface_get_material(s) as StandardMaterial3D
			if mat and RIM.has(mat.resource_name):
				mat.rim_enabled = true
				mat.rim = RIM[mat.resource_name]
				mat.rim_tint = 0.5
			if mat and CLEARCOAT.has(mat.resource_name) and mat.roughness_texture:
				mat.clearcoat_enabled = true
				mat.clearcoat = CLEARCOAT[mat.resource_name][0]
				mat.clearcoat_roughness = CLEARCOAT[mat.resource_name][1]
				mat.clearcoat_texture = mat.roughness_texture
			if mat and NORMAL_SCALE.has(mat.resource_name):
				mat.normal_scale = NORMAL_SCALE[mat.resource_name]
			if mat and mat.resource_name == "M_LL_Ross_Skin":
				# the stubble and short hair are alpha-scissor dots; the mipmaps averaged them away and left a
				# smooth young jaw (r3). Alpha to coverage (MSAA) keeps them as a grey shadow of stubble at range.
				mat.alpha_antialiasing_mode = BaseMaterial3D.ALPHA_ANTIALIASING_ALPHA_TO_COVERAGE
				mat.alpha_scissor_threshold = 0.35
	if skel:
		head_turn = HeadTurn.new()
		head_turn.fig = self
		skel.add_child(head_turn)
	_begin.call_deferred()            # after game_fp has placed the node (it sets the position after add_child)


## The head's turn toward the keeper (radians about the vertical, + to his left as the model faces +Z), or 0.
func head_turn_target() -> float:
	if not visible or _waiting_door or not _path.is_empty() or _settle > 0.0:
		return 0.0
	var g := _game()
	var p = g.get("player") if g else null
	if p == null or not (p is Node3D):
		return 0.0
	var c = p.get("camera")
	var eye: Vector3 = (c as Node3D).global_position if c is Node3D else (p as Node3D).global_position
	var local := global_transform.affine_inverse() * eye
	var d := Vector2(local.x, local.z).length()
	if d > HEAD_RANGE or d < 0.3:
		return 0.0
	var a := atan2(local.x, local.z)
	if absf(a) > HEAD_FRONT:
		return 0.0
	return clampf(a, -HEAD_MAX, HEAD_MAX)


func _game() -> Node:
	return get_parent()


func _director():
	var g := _game()
	return g.get("director") if g else null


func _station():
	var g := _game()
	return g.get("station") if g else null


## Where the story wants him now (see the header).
func story_mark() -> String:
	var d = _director()
	if d == null:
		return "B"
	var st = d.state
	if st.chapter >= 6 and d.beat_reached("rescue"):
		return "C"
	if st.chapter >= 6 and st.has_flag("ross_wheel"):
		return "D"
	return "B"


static func mark_position(key: String) -> Vector3:
	var m: Array = MARKS[key]
	var b := deg_to_rad(float(m[0]))
	return Vector3(sin(b) * float(m[1]), FLOOR_Y + float(m[2]), -cos(b) * float(m[1]))


## The yaw that faces the model (its front is +Z, as Blender's -Y exports) along a room bearing.
static func bearing_yaw(bearing_deg: float) -> float:
	return PI - deg_to_rad(bearing_deg)


static func _point(bd: Array) -> Vector3:
	var b := deg_to_rad(float(bd[0]))
	return Vector3(sin(b) * float(bd[1]), FLOOR_Y, -cos(b) * float(bd[1]))


func _begin() -> void:
	var d = _director()
	var target := story_mark()
	if target == "B" and d != null and d.is_talking():
		# live: the door scene. Hidden until the leaf has swung far enough, then in from the landing.
		_place("A")
		visible = false
		_waiting_door = true
		mark = "B"
		return
	_place(target)


## Stand on a mark at once, in its held pose.
func place(key: String) -> void:
	_place(key)


func _place(key: String) -> void:
	mark = key
	_path.clear()
	_settle = 0.0
	global_position = mark_position(key)
	global_basis = Basis(Vector3.UP, bearing_yaw(float(MARKS[key][3])))
	_play(POSE[key], 0.0)


func _play(an: String, blend: float = BLEND) -> void:
	if ap and ap.has_animation(an) and ap.current_animation != an:
		ap.play(an, blend)


## Walk from where he stands to a mark along its route (or straight there).
func walk_to(key: String) -> void:
	var from_key := mark
	_path.clear()
	for wp in ROUTES.get(from_key + key, []):
		_path.append(_point(wp))
	_path.append(mark_position(key))
	mark = key
	_settle = 0.0
	_play("walk")


func is_walking() -> bool:
	return not _path.is_empty()


func _process(delta: float) -> void:
	if _waiting_door:
		var st = _station()
		if st == null or not st.has_method("door_phase") or st.door_phase().y >= DOOR_SWING_TO_ENTER:
			_waiting_door = false
			visible = true
			mark = "A"
			walk_to("B")
		return
	if not _path.is_empty():
		_step_walk(delta)
		return
	if _settle > 0.0:
		_settle = maxf(0.0, _settle - delta)
		var k := 1.0 - _settle / SETTLE_S
		var to := bearing_yaw(float(MARKS[mark][3]))
		global_basis = Basis(Vector3.UP, lerp_angle(_settle_from, to, k * k * (3.0 - 2.0 * k)))
		return
	_check_t -= delta
	if _check_t <= 0.0:
		_check_t = 0.25
		var want := story_mark()
		if want != mark:
			if _screen_black():
				_place(want)                     # a fade hides the move: no walk to watch
			else:
				walk_to(want)


func _step_walk(delta: float) -> void:
	var tgt: Vector3 = _path[0]
	var pos := global_position
	var to := Vector3(tgt.x - pos.x, 0.0, tgt.z - pos.z)
	var dist := to.length()
	var step := WALK_SPEED * delta
	if dist > 0.001:
		var yaw_now := global_basis.get_euler().y
		var yaw_to := atan2(to.x, to.z)
		var diff := wrapf(yaw_to - yaw_now, -PI, PI)
		global_basis = Basis(Vector3.UP, yaw_now + clampf(diff, -TURN_RATE * delta, TURN_RATE * delta))
	if dist <= step:
		global_position = Vector3(tgt.x, tgt.y, tgt.z)
		_path.remove_at(0)
		if _path.is_empty():
			_settle_from = global_basis.get_euler().y
			_settle = SETTLE_S
			_play(POSE[mark])
		return
	pos += to / dist * step
	pos.y = lerpf(pos.y, tgt.y, clampf(step / dist, 0.0, 1.0))
	global_position = pos


func _screen_black() -> bool:
	var g := _game()
	var p = g.get("presenter") if g else null
	if p == null:
		return false
	var f = p.get("fade")
	return f != null and (f as ColorRect).color.a >= 0.98


## A bone's world position (tests: the held poses' hands on their contacts).
func bone_world(bone: String) -> Vector3:
	if skel == null:
		return Vector3.INF
	var i := skel.find_bone(bone)
	if i < 0:
		return Vector3.INF
	return skel.global_transform * skel.get_bone_global_pose(i).origin
