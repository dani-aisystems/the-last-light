class_name EndingSequence
extends Control
## G6a (item 34): the ending's panel sequence, played by the story presenter over its warm black before the
## closing card. Four panels per campaign (StoryDirector.ending_panels): each crossfades in, holds, and
## moves on by itself; Space (or a click) moves on sooner, but never before the panel's dwell. The fourth
## panel slides left and the ending's own epilogue lines read beside it, one at a time, on the same rule.
## Panel images come from res://assets/ending/<id>.png (data/ending/panels.json); a missing image shows a
## stand-in plate until the art lands (G6b). Every image is drawn through shaders/panel_grade.gdshader.

const DATA_PATH := "res://data/ending/panels.json"
const TEX_DIR := "res://assets/ending/"
const GRADE := preload("res://shaders/panel_grade.gdshader")
const FADE_S := 1.2                     # the crossfade between panels
const LINE_DWELL_S := 2.0               # P4's lines: Space can't move on before this
const WARM_BLACK := Color(0.035, 0.026, 0.02)

var data := {}
var playing := false
var current_id := ""
var shown: Array = []                   # panel ids shown this run, in order (tests, captures)
var lines_shown := 0
var early_presses := 0                  # presses that came before the dwell and were ignored (tests)
var grade_override := -1.0              # captures: >= 0 replaces the panel's grade strength
var _slot: Control
var _side: VBoxContainer
var _t := 0.0
var _press := false


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var f := FileAccess.open(DATA_PATH, FileAccess.READ)
	if f:
		var j = JSON.parse_string(f.get_as_text())
		if j is Dictionary:
			data = j.get("panels", {})
	_side = VBoxContainer.new()
	_side.anchor_left = 0.635
	_side.anchor_right = 0.94
	_side.anchor_top = 0.14
	_side.anchor_bottom = 0.86
	_side.alignment = BoxContainer.ALIGNMENT_CENTER
	_side.add_theme_constant_override("separation", 22)
	_side.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_side)


## A command-line user arg (GameState.user_args) read through the tree: class_name scripts are compiled
## before the autoloads exist when a test runs with -s, so they can't name GameState directly.
static func user_arg(key: String, default := "") -> String:
	var tree := Engine.get_main_loop() as SceneTree
	var gs: Node = tree.root.get_node_or_null("GameState") if tree else null
	if gs == null:
		return default
	return String(gs.user_args.get(key, default))


func panel_info(id: String) -> Dictionary:
	return data.get(id, {})


func has_image(id: String) -> bool:
	return ResourceLoader.exists(TEX_DIR + id + ".png")


## Space / click from the presenter. Before the dwell it is counted and ignored.
func press() -> void:
	if not playing:
		return
	_press = true


## Plays the panels in order; `body` are the lines read beside the last panel. Returns when the last panel
## has faded back to black (the presenter then shows the closing card).
func play(panels: Array, body: Array) -> void:
	playing = true
	shown.clear()
	lines_shown = 0
	early_presses = 0
	_clear_side()
	for i in panels.size():
		var id := String(panels[i])
		var last := i == panels.size() - 1
		var info := panel_info(id)
		await _show_slot(id, last and not body.is_empty(), false)
		await _wait(float(info.get("dwell", 3.0)), float(info.get("auto", 8.0)))
		if last:
			for k in body.size():
				var l := line_label(String(body[k]))
				l.modulate.a = 0.0
				_side.add_child(l)
				lines_shown += 1
				create_tween().tween_property(l, "modulate:a", 1.0, 1.0)
				await _wait(LINE_DWELL_S, maxf(5.0, String(body[k]).length() * 0.06))
			if not body.is_empty():
				await _wait(1.0, 2.5)
	var tw := create_tween().set_parallel(true)
	if _slot:
		tw.tween_property(_slot, "modulate:a", 0.0, FADE_S)
	tw.tween_property(_side, "modulate:a", 0.0, FADE_S)
	await tw.finished
	_clear_slot()
	_clear_side()
	_side.modulate.a = 1.0
	current_id = ""
	playing = false


## Captures: one panel as it looks once settled, with `body` beside it (P4), no animation.
func show_static(id: String, body: Array) -> void:
	_clear_side()
	await _show_slot(id, not body.is_empty(), true)
	for t in body:
		_side.add_child(line_label(String(t)))
	lines_shown = body.size()


func clear() -> void:
	_clear_slot()
	_clear_side()
	playing = false
	current_id = ""


## One epilogue line beside the panel: the ending card's italic serif, left-aligned in the side column.
func line_label(text: String) -> Label:
	var l := UIStyle.label(text, 24, UIStyle.INK, UIStyle.serif_italic())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	l.custom_minimum_size = Vector2(420, 0)
	return l


## The rect a panel sits in: full (centred, 80 % wide) or beside the lines (left 55 %).
func slot_rect_anchors(beside: bool) -> Array:
	return [0.05, 0.14, 0.60, 0.86] if beside else [0.1, 0.08, 0.9, 0.92]


func _show_slot(id: String, beside: bool, instant: bool) -> void:
	var old := _slot
	var s := _make_slot(id)
	var a := slot_rect_anchors(beside)
	s.anchor_left = a[0]
	s.anchor_top = a[1]
	s.anchor_right = a[2]
	s.anchor_bottom = a[3]
	add_child(s)
	move_child(s, 0)
	_slot = s
	current_id = id
	shown.append(id)
	if instant:
		s.modulate.a = 1.0
		if old:
			old.queue_free()
		return
	s.modulate.a = 0.0
	var tw := create_tween().set_parallel(true)
	tw.tween_property(s, "modulate:a", 1.0, FADE_S)
	if old:
		tw.tween_property(old, "modulate:a", 0.0, FADE_S)
	await tw.finished
	if old:
		old.queue_free()


func _make_slot(id: String) -> Control:
	var info := panel_info(id)
	if has_image(id):
		var tr := TextureRect.new()
		tr.texture = load(TEX_DIR + id + ".png")
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var m := ShaderMaterial.new()
		m.shader = GRADE
		var g := float(info.get("grade", 0.75))
		if user_arg("ending_grade", "") != "":                # captures: the grade on and off
			g = float(user_arg("ending_grade", ""))
		if grade_override >= 0.0:
			g = grade_override
		m.set_shader_parameter("strength", g)
		tr.material = m
		tr.set_meta("panel", id)
		return tr
	# stand-in plate (art pending): a dark warm card with a thin rule and the panel's subject
	var p := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.11, 0.085, 0.065)
	sb.border_color = Color(0.91, 0.87, 0.78, 0.18)
	sb.set_border_width_all(1)
	p.add_theme_stylebox_override("panel", sb)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var c := VBoxContainer.new()
	c.alignment = BoxContainer.ALIGNMENT_CENTER
	c.add_theme_constant_override("separation", 14)
	p.add_child(c)
	var t1 := UIStyle.label("PANEL PENDING  ·  " + id.to_upper(), 15, UIStyle.DIM, UIStyle.sans())
	t1.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	c.add_child(t1)
	var t2 := UIStyle.label(String(info.get("standin", id)), 28, UIStyle.INK, UIStyle.serif_italic())
	t2.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	t2.modulate.a = 0.75
	c.add_child(t2)
	p.set_meta("panel", id)
	p.set_meta("standin", true)
	return p


## Hold for at least `dwell`, at most `auto` seconds; a press after the dwell moves on. Paused time
## doesn't count.
func _wait(dwell: float, auto: float) -> void:
	_t = 0.0
	_press = false
	while _t < auto:
		await get_tree().process_frame
		if not get_tree().paused:
			_t += get_process_delta_time()
		if _press:
			_press = false
			if _t >= dwell:
				return
			early_presses += 1


func _clear_slot() -> void:
	if _slot:
		_slot.queue_free()
		_slot = null


func _clear_side() -> void:
	for c in _side.get_children():
		c.queue_free()
