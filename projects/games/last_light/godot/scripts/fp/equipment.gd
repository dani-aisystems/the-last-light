class_name Equipment
extends Node3D
## G3a (Daniel 2026-11-07): what the keeper carries besides the torch. Both lie on the desk from the start
## and are picked up there (IA_compass on the centre window sill (R5), IA_binoculars by the radar).
##   compass     G   left hand, low and tilted to the eye; the needle points to north (world -Z) at any yaw
##   binoculars  B   both hands, raised to the eyes: FOV 72 -> 10 deg (about 7x) over RAISE_S, look slowed by
##                   the same ratio, a two-eyepiece mask, walking slowed; the torch goes out while they're up
## One held item at a time (the torch is separate and stays on with the compass). E with the binoculars up
## lowers them first; a device view puts everything away. Until G3b's arms, the held copies sway with the
## walk on their own. The held meshes are copies of the desk props (same meshes and materials).
## Child of the player's camera (game_fp); this node is placed at the camera, so held items use camera space.

signal changed(held: String)

const ITEMS := ["compass", "binoculars"]
const BINO_FOV := 10.0
const RAISE_S := 0.45                     # G3b: 0.35 zoomed before the binoculars and hands were ever in view
const ZOOM_FROM := 0.6                    # the raise brings them up in view first; the zoom and mask take the rest
const COMPASS_HELD := Vector3(-0.12, -0.22, -0.40)   # G3b: lower, so the hand under it reads as holding it
const COMPASS_TILT := 40.0                # degrees the card is tipped toward the eye (G3a 64: the hand stood upright)
const COMPASS_DOWN := Vector3(-0.15, -0.42, -0.26)
const BINO_UP := Vector3(0.0, -0.035, -0.125)
const BINO_DOWN := Vector3(0.06, -0.38, -0.28)
const BINO_MID := Vector3(0.0, -0.14, -0.30)    # halfway: at arm's length, low in the view, both hands on them
const NORTH := Vector3(0, 0, -1)          # Geo: bearing 0 = (x 0, z -1)
## G3b: the keeper's hands (assets/models/hands.glb, blender/hands.py). Hand frame: origin at the wrist,
## fingers -Y, palm -Z, thumb +X (left) / -X (right). Each grip is the hand's transform in the held item's
## frame: the compass in the left palm, the torch in a right fist (thumb toward the head), a hand on each
## binocular barrel (palms in, knuckles up). G_H is the grip centre in hand coords, so origin = grip - B * G_H.
const TORCH_POS := Vector3(0.16, -0.21, -0.32)
const G_H := Vector3(0.0, -0.15, -0.03)
const POSE_BLEND := 10.0                  # per second, toward the target pose
const LAYER_HELD := 512                   # render layer 10: the hands and the held torch (the fill light's only target)
const LIGHT_GAP := 0.03                   # the torch light stops this short of a wall between the eye and the lens
const TORCH_EYE := Vector3(0.07, -0.08, -0.12)   # R4: where the beam starts when looking steeply down

var player: Node
var station: Node
var has := {"compass": false, "binoculars": false}
var held := ""
var compass_node: Node3D
var needle: Node3D
var bino_node: Node3D
var mask: CanvasLayer
var _mask_rect: ColorRect
var _compass_t := 0.0                     # 0 put away .. 1 in hand
var _bino_t := 0.0                        # 0 lowered .. 1 at the eyes
var _torch_was := false
var _sway := 0.0
var hands: Node3D
var hand := {}                            # "L" / "R" -> the ARM_hand_* node
var skel := {}                            # "L" / "R" -> Skeleton3D
var poses := {}                           # "L_torch" ... -> {bone index: Quaternion}
var pose_now := {"L": "", "R": ""}        # the pose each hand is moving to
var fill: OmniLight3D                     # see setup: the torch spill on the hands
var torch_node: Node3D                    # a copy of the shelf torch, in the right hand while it's on
var grips := {}                           # "compass_L" / "torch_R" / "bino_L" / "bino_R" -> Transform3D in the item frame
var hold_raise := -1.0                    # captures: hold the binoculars part-way up (0..1); -1 off


func setup(p: Node, st: Node) -> void:
	player = p
	station = st
	compass_node = _copy("PROP_compass", "compass")
	needle = _copy_part("PT_compass_needle", "compass")
	if needle:
		compass_node.add_child(needle)
	add_child(compass_node)
	compass_node.rotation = Vector3(deg_to_rad(COMPASS_TILT), deg_to_rad(12.0), 0.0)   # the card toward the eye
	compass_node.visible = false
	bino_node = _copy("PROP_binoculars", "binoculars")
	add_child(bino_node)
	bino_node.visible = false
	mask = CanvasLayer.new()
	mask.layer = 14                       # under the story presenter (15): subtitles stay readable
	_mask_rect = ColorRect.new()
	_mask_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_mask_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh := Shader.new()
	sh.code = """shader_type canvas_item;
uniform float aspect = 1.7778;
uniform float alpha = 0.0;
void fragment() {
	vec2 p = vec2((UV.x - 0.5) * aspect, UV.y - 0.5);
	float r = 0.38;
	float d = min(length(p - vec2(-0.215, 0.0)), length(p - vec2(0.215, 0.0)));
	float inside = smoothstep(r, r - 0.035, d);
	float vig = 1.0 - smoothstep(r * 0.5, r, d) * 0.4;
	COLOR = vec4(0.0, 0.0, 0.0, alpha * (1.0 - inside * vig));
}"""
	var mat := ShaderMaterial.new()
	mat.shader = sh
	_mask_rect.material = mat
	mask.add_child(_mask_rect)
	mask.visible = false
	add_child(mask)
	point_needle(station.parts.get("PT_compass_needle", {}).get("node", null))   # the desk compass too
	torch_node = _copy("PROP_torch", "torch")
	add_child(torch_node)
	torch_node.rotation = Vector3(deg_to_rad(-90.0), 0.0, 0.0)     # its axis (local +Y) forward
	torch_node.position = TORCH_POS
	torch_node.visible = false
	for mi in torch_node.get_children():
		(mi as MeshInstance3D).layers |= LAYER_HELD
	# the beam's spill back onto the fist: faint, warm, unshadowed, and only on the hands and the torch
	fill = OmniLight3D.new()
	fill.light_color = Color(1.0, 0.85, 0.64)
	fill.light_energy = 0.18
	fill.omni_range = 0.4
	fill.light_cull_mask = LAYER_HELD
	fill.shadow_enabled = false
	fill.position = TORCH_POS + Vector3(-0.06, 0.1, -0.02)
	fill.visible = false
	add_child(fill)
	_setup_hands()


func _grip(basis: Basis, grip_point: Vector3) -> Transform3D:
	return Transform3D(basis, grip_point - basis * G_H)


func _setup_hands() -> void:
	var scn: PackedScene = load("res://assets/models/hands.glb")
	if scn == null:
		return
	hands = scn.instantiate()
	add_child(hands)
	for side in ["L", "R"]:
		hand[side] = hands.get_node("ARM_hand_" + side)
		skel[side] = hand[side].get_node("Skeleton3D")
		hand[side].visible = false
		for mi in hand[side].find_children("*", "MeshInstance3D", true, false):
			(mi as MeshInstance3D).layers = station.LAYER_INTERIOR | LAYER_HELD   # lit by the room, as the props are
			(mi as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var ap: AnimationPlayer = hands.get_node_or_null("AnimationPlayer")
	if ap:
		for an in ap.get_animation_list():
			var a: Animation = ap.get_animation(an)
			var side := String(an).substr(0, 1)
			var pose := {}
			for t in a.get_track_count():
				if a.track_get_type(t) != Animation.TYPE_ROTATION_3D:
					continue
				var path := a.track_get_path(t)
				if not String(path.get_concatenated_names()).contains("ARM_hand_" + side):
					continue              # each action also carries the other hand's rest tracks (same bone names)
				var bone := String(path.get_subname(0))
				var bi: int = skel[side].find_bone(bone)
				if bi >= 0:
					pose[bi] = a.track_get_key_value(t, 0)
			poses[String(an)] = pose
		ap.queue_free()                   # the poses are read; each hand is set on its own below
	# grips, in each item's own frame (see the comment at G_H)
	grips["compass_L"] = Transform3D(Basis(Vector3.RIGHT, deg_to_rad(90.0)), Vector3(0.0, -0.037, 0.12))   # the card on the palm centre
	grips["torch_R"] = _grip(Basis(Vector3(0, -1, 0), Vector3(0, 0, -1), Vector3(1, 0, 0)), Vector3(0.0, -0.03, 0.0))
	grips["bino_L"] = _grip(Basis(Vector3(0, 0, -1), Vector3(0, -1, 0), Vector3(-1, 0, 0)), Vector3(-0.058, -0.004, -0.02))
	grips["bino_R"] = _grip(Basis(Vector3(0, 0, 1), Vector3(0, -1, 0), Vector3(1, 0, 0)), Vector3(0.058, -0.004, -0.02))


## Move one hand toward a pose (blended), place it on its item, or hide it.
func _hand(side: String, item: Node3D, grip: String, pose: String, delta: float) -> void:
	if not hand.has(side):
		return
	var on := item != null and item.visible
	hand[side].visible = on
	if not on:
		return
	hand[side].transform = item.transform * grips[grip]
	var key := side + "_" + pose
	var target: Dictionary = poses.get(key, {})
	var snap: bool = pose_now[side] != key
	pose_now[side] = key
	var k := 1.0 if snap and delta == 0.0 else clampf(delta * POSE_BLEND, 0.0, 1.0)
	for bi in target:
		var cur: Quaternion = skel[side].get_bone_pose_rotation(bi)
		skel[side].set_bone_pose_rotation(bi, cur.slerp(target[bi], k))


func hands_visible() -> Dictionary:
	return {"L": hand.has("L") and hand["L"].visible, "R": hand.has("R") and hand["R"].visible}


## Copies of the desk prop's meshes, in the prop's own frame (the IA volume): origin at its centre.
func _copy(prefix: String, ia_id: String) -> Node3D:
	var root := Node3D.new()
	root.name = "Held_" + ia_id
	var frame := _frame(ia_id)
	if station.room == null:
		return root
	for mi in station.room.find_children(prefix + "*", "MeshInstance3D", true, false):
		root.add_child(_mesh_copy(mi, frame))
	return root


func _copy_part(part: String, ia_id: String) -> Node3D:
	var src: Node3D = station.parts.get(part, {}).get("node", null)
	if src == null or not (src is MeshInstance3D):
		return null
	return _mesh_copy(src, _frame(ia_id))


func _frame(ia_id: String) -> Transform3D:
	var ia: Node3D = station._ia_bodies.get(ia_id, null)
	return ia.global_transform.orthonormalized() if ia else Transform3D()


func _mesh_copy(mi: MeshInstance3D, frame: Transform3D) -> MeshInstance3D:
	var c := MeshInstance3D.new()
	c.name = String(mi.name)
	c.mesh = mi.mesh
	c.material_override = mi.material_override
	for i in mi.get_surface_override_material_count():
		c.set_surface_override_material(i, mi.get_surface_override_material(i))
	c.transform = frame.affine_inverse() * mi.global_transform
	c.layers = mi.layers
	c.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return c


## Turn a compass needle (tip = local -Z, card normal = local +Y after the glTF axis change) about the
## card normal so the tip points to north projected onto the card. Returns the remaining error in degrees.
func point_needle(n: Node3D) -> float:
	if n == null:
		return 0.0
	var up := n.global_basis.y.normalized()
	var want := NORTH - up * NORTH.dot(up)
	if want.length() < 0.05:              # card held on edge: no meaningful north
		return 0.0
	want = want.normalized()
	var tip := -n.global_basis.z
	tip = (tip - up * tip.dot(up)).normalized()
	var ang := atan2(up.dot(tip.cross(want)), tip.dot(want))
	n.rotate_object_local(Vector3.UP, ang)
	var tip2 := (-n.global_basis.z - up * (-n.global_basis.z).dot(up)).normalized()
	return rad_to_deg(acos(clampf(tip2.dot(want), -1.0, 1.0)))


func give(id: String) -> void:
	if id in ITEMS:
		has[id] = true


func toggle(id: String) -> Dictionary:
	if not has.get(id, false):
		return {"ok": false, "reason": "The hand compass is on the east window sill." if id == "compass" else "The binoculars are on the desk, by the radar."}
	if held == id:
		held = ""
	else:
		held = id
	_apply_torch()
	changed.emit(held)
	return {"ok": true, "reason": ""}


## A device view, a document, a reply: everything goes away at once.
func put_away_now() -> void:
	if held == "":
		return
	held = ""
	_bino_t = 0.0
	_compass_t = 0.0
	_apply_torch()
	changed.emit(held)


func _apply_torch() -> void:
	if player == null or not player.torch_held or player.torch_light == null:
		return
	if held == "binoculars":
		if player.torch_light.visible:
			_torch_was = true
			player.set_torch(false)
	elif _torch_was:
		_torch_was = false
		player.set_torch(true)


func binoculars_up() -> bool:
	return held == "binoculars" and _bino_t > 0.98


## Look sensitivity and walking speed while the binoculars are raised.
func look_scale() -> float:
	return lerpf(1.0, BINO_FOV / maxf(1.0, _base_fov()), _zoom())


func move_scale() -> float:
	return lerpf(1.0, 0.4, _bino_t)


## 0 .. 1 over the last part of the raise: the view narrows once the binoculars are nearly at the eyes.
func _zoom() -> float:
	return _ease(clampf((_bino_t - ZOOM_FROM) / (1.0 - ZOOM_FROM), 0.0, 1.0))


func _base_fov() -> float:
	var st: Node = get_tree().root.get_node_or_null("Settings") if is_inside_tree() else null
	return float(st.v.get("fov", 72.0)) if st else 72.0      # looked up at run time: -s tests compile this early


func _process(delta: float) -> void:
	if player == null:
		return
	var cam: Camera3D = player.camera
	global_transform = cam.global_transform
	var walking: float = clampf(Vector2(player.velocity.x, player.velocity.z).length() / 1.6, 0.0, 1.0)
	_sway += delta * (2.0 + 4.0 * walking)
	var sway := Vector3(sin(_sway) * 0.004, absf(cos(_sway)) * 0.005, 0.0) * (0.4 + walking)
	# compass
	_compass_t = move_toward(_compass_t, 1.0 if held == "compass" else 0.0, delta / 0.25)
	compass_node.visible = _compass_t > 0.01
	if compass_node.visible:
		compass_node.position = COMPASS_DOWN.lerp(COMPASS_HELD, _ease(_compass_t)) + sway
		point_needle(needle)
	# binoculars
	_bino_t = move_toward(_bino_t, 1.0 if held == "binoculars" else 0.0, delta / RAISE_S)
	if hold_raise >= 0.0 and held == "binoculars":
		_bino_t = hold_raise
	var e := _ease(_bino_t)
	var z := _zoom()
	bino_node.visible = _bino_t > 0.01 and _bino_t < 0.97        # at the eyes only the view is left
	var bp := BINO_DOWN.lerp(BINO_MID, _ease(_bino_t / 0.5)) if _bino_t < 0.5 else BINO_MID.lerp(BINO_UP, _ease((_bino_t - 0.5) / 0.5))
	bino_node.position = bp + sway * (1.0 - e)
	mask.visible = _bino_t > 0.6
	(_mask_rect.material as ShaderMaterial).set_shader_parameter("alpha", clampf((_bino_t - 0.6) / 0.4, 0.0, 1.0))
	var vp := get_viewport().get_visible_rect().size
	(_mask_rect.material as ShaderMaterial).set_shader_parameter("aspect", vp.x / maxf(1.0, vp.y))
	var breathe := sin(Time.get_ticks_msec() / 1000.0 * 0.9) * 0.12 * z
	cam.fov = lerpf(_base_fov(), BINO_FOV, z) + breathe
	# G3b: the torch in the right hand while it's on (the beam leaves from its lens), and the hands
	var torch_on: bool = player.torch_held and player.torch_light != null and player.torch_light.visible
	torch_node.visible = torch_on and held != "binoculars" and player.focused == ""   # a device view: hands off
	fill.visible = torch_node.visible
	if torch_node.visible:
		torch_node.position = TORCH_POS + sway
		# R4: looking down, the lens comes back to the chest (pitch -83 put the light ON the body); there the
		# beam starts from just below the eye instead, and it is always aimed at the crosshair 3 m out
		# (it was aimed once, from the old capsule position, so the pool sat low and right of the aim).
		var lens := torch_node.transform * Vector3(0.0, 0.12, 0.0)
		var down := smoothstep(-0.55, -1.15, player._pitch)
		var pos := _light_pos(lens.lerp(TORCH_EYE, down))
		player.torch_light.transform = Transform3D(Basis.looking_at(Vector3(0.0, 0.0, -3.0) - pos, Vector3.UP), pos)
	_hand("L", bino_node if bino_node.visible else compass_node, "bino_L" if bino_node.visible else "compass_L",
		"binoculars" if bino_node.visible else "compass", delta)
	_hand("R", bino_node if bino_node.visible else torch_node, "bino_R" if bino_node.visible else "torch_R",
		"binoculars" if bino_node.visible else "torch", delta)


## The torch light sits at the lens, unless a wall is between the eye and the lens (nose to a wall the
## lens is past the capsule): then just short of that wall, so the beam never starts inside it.
func _light_pos(lens: Vector3) -> Vector3:
	if not is_inside_tree():
		return lens
	var from: Vector3 = global_transform.origin
	var to: Vector3 = global_transform * lens
	var q := PhysicsRayQueryParameters3D.create(from, to, player.collision_mask, [player.get_rid()])
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	if hit.is_empty():
		return lens
	var d: float = maxf(0.0, from.distance_to(hit["position"]) - LIGHT_GAP)
	return global_transform.affine_inverse() * from.move_toward(to, d)


static func _ease(t: float) -> float:
	return t * t * (3.0 - 2.0 * t)


func to_dict() -> Dictionary:
	return {"has": has.duplicate(), "held": held if held != "binoculars" else ""}


func from_dict(d: Dictionary) -> void:
	var h: Dictionary = d.get("has", {})
	for id in ITEMS:
		has[id] = bool(h.get(id, false))
	held = String(d.get("held", ""))
	if not has.get(held, false):
		held = ""
	_compass_t = 1.0 if held == "compass" else 0.0
	_bino_t = 0.0
