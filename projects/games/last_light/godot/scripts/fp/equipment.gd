class_name Equipment
extends Node3D
## G3a (Daniel 2026-11-07): what the keeper carries besides the torch. Both lie on the desk from the start
## and are picked up there (IA_compass on the chart, IA_binoculars by the radar).
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
const RAISE_S := 0.35
const COMPASS_HELD := Vector3(-0.13, -0.18, -0.42)   # S3a captures: -0.34 read large and close
const COMPASS_DOWN := Vector3(-0.15, -0.42, -0.26)
const BINO_UP := Vector3(0.0, -0.035, -0.125)
const BINO_DOWN := Vector3(0.06, -0.38, -0.28)
const NORTH := Vector3(0, 0, -1)          # Geo: bearing 0 = (x 0, z -1)

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


func setup(p: Node, st: Node) -> void:
	player = p
	station = st
	compass_node = _copy("PROP_compass", "compass")
	needle = _copy_part("PT_compass_needle", "compass")
	if needle:
		compass_node.add_child(needle)
	add_child(compass_node)
	compass_node.rotation = Vector3(deg_to_rad(64.0), deg_to_rad(12.0), 0.0)   # the card faces the eye
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
		return {"ok": false, "reason": "The hand compass is on the chart." if id == "compass" else "The binoculars are on the desk, by the radar."}
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
	return lerpf(1.0, BINO_FOV / maxf(1.0, _base_fov()), _bino_t)


func move_scale() -> float:
	return lerpf(1.0, 0.4, _bino_t)


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
	var e := _ease(_bino_t)
	bino_node.visible = _bino_t > 0.01 and _bino_t < 0.97        # at the eyes only the view is left
	bino_node.position = BINO_DOWN.lerp(BINO_UP, e) + sway * (1.0 - e)
	mask.visible = _bino_t > 0.6
	(_mask_rect.material as ShaderMaterial).set_shader_parameter("alpha", clampf((_bino_t - 0.6) / 0.4, 0.0, 1.0))
	var vp := get_viewport().get_visible_rect().size
	(_mask_rect.material as ShaderMaterial).set_shader_parameter("aspect", vp.x / maxf(1.0, vp.y))
	var breathe := sin(Time.get_ticks_msec() / 1000.0 * 0.9) * 0.12 * e
	cam.fov = lerpf(_base_fov(), BINO_FOV, e) + breathe


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
