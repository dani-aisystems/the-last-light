class_name DutyHUD
extends Control
## G2b layer A (Daniel 2026-11-06): the keeper's current duty, top-left, instead of the permanent
## checklist. A small amber caption ("THE WATCH") over one line in Callum's register ("Get the engine
## running. Then CHARGE the cells."), on a soft dark plate so it reads on any wall (>= 4.5:1).
##   Standard (default): the line fades in when a duty begins, holds Settings "duty_hold_s", fades out.
##   Full: the line stays, with a checkbox for the duty and its known sub-tasks as "•" one-liners.
##   Minimal: the line only shows when the player asks for it (J / R3).
## Hints share the plate (one sentence under the line). In device views (radio, console) the duty line
## steps aside unless the guidance is Full or the player recalled it; hints still show there.

const GUIDE_MINIMAL := 0
const GUIDE_STANDARD := 1
const GUIDE_FULL := 2
const FADE_IN := 0.6
const FADE_OUT := 1.2
const MAX_W := 0.30             # of the viewport width
const MARGIN := 0.04            # safe margin, of the viewport size
const TOP := 0.085              # top edge, of the viewport height: below the notices' band (fp_ui, y 36-80)

var plate: PanelContainer
var box: VBoxContainer
var caption: Label
var line: Label                 # the duty line (presenter.objective points here)
var check: Control              # Full: the duty's checkbox
var subs: VBoxContainer         # Full: the known sub-tasks
var hint: Label                 # presenter.hint points here (hints and the room's one-line asides)
var compact := false            # a device view is open (game_fp sets it every frame)
var view: Dictionary = {}       # {title, caption, duty, steps: [{text, id}], complete}
var done: Array = []            # indices into view.steps that are really done
var _show_t := 0.0              # seconds the duty line still shows (Standard / recall)
var _forced := false            # recalled by the player: shows even in a device view
var _duty_a := 0.0              # current alpha of the duty part


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	plate = PanelContainer.new()
	plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.025, 0.035, 0.05, 0.68)
	sb.set_corner_radius_all(12)
	sb.shadow_color = Color(0.025, 0.035, 0.05, 0.42)   # the soft edge: a blurred halo, not a hard box
	sb.shadow_size = 22
	sb.content_margin_left = 20
	sb.content_margin_right = 22
	sb.content_margin_top = 12
	sb.content_margin_bottom = 14
	plate.add_theme_stylebox_override("panel", sb)
	add_child(plate)
	box = VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	plate.add_child(box)
	caption = UIStyle.label("", 16, Color(1.0, 0.78, 0.46), _caption_font())   # 14 px amber read ~2.3:1 (S2 captures)
	box.add_child(caption)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(row)
	check = Control.new()
	check.custom_minimum_size = Vector2(UIStyle.px(16), UIStyle.px(16))
	check.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	check.draw.connect(_draw_check)
	row.add_child(check)
	line = UIStyle.label("", 21, UIStyle.INK, UIStyle.serif())
	line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	line.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(line)
	subs = VBoxContainer.new()
	subs.add_theme_constant_override("separation", 2)
	subs.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(subs)
	hint = UIStyle.label("", 17, Color(0.80, 0.83, 0.86), UIStyle.sans_italic())
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(hint)
	plate.modulate.a = 0.0


static func _caption_font() -> Font:
	var f := FontVariation.new()
	f.base_font = UIStyle.sans_semibold()
	f.spacing_glyph = 2                    # letter-spaced capitals read as small caps
	return f


static func guidance() -> int:
	return int(_settings().get("guidance", GUIDE_STANDARD))


## The Settings autoload's values, looked up at run time: a -s test script compiles this class before
## the autoloads exist, so the bare identifier would not compile there.
static func _settings() -> Dictionary:
	var st: Node = (Engine.get_main_loop() as SceneTree).root.get_node_or_null("Settings")
	return st.v if st else {}


## The duty to show: {title, caption, duty, steps, complete} ({} clears it). A new duty (or a new line)
## is announced; sub-task changes alone are not (they show in Full and in the logbook).
func set_view(v: Dictionary) -> void:
	var fresh: bool = v.get("duty", "") != view.get("duty", "") or v.get("title", "") != view.get("title", "")
	view = v
	done = []
	if v.is_empty():
		_show_t = 0.0
		_forced = false
	_rebuild()
	if fresh and not v.is_empty():
		if guidance() >= GUIDE_STANDARD:
			announce()
		elif not _forced:
			_show_t = 0.0                  # Minimal: a new duty never inherits the last one's time on screen


func set_done(d: Array) -> void:
	done = d.duplicate()
	_rebuild()


func is_step_done(i: int) -> bool:
	return i in done


## Bring the duty line up for the hold time (a new duty, a hint escalation).
func announce() -> void:
	_show_t = float(_settings().get("duty_hold_s", 6.0))


## The player asked (J / R3): show it now, even in a device view and under Minimal guidance.
func recall() -> void:
	if view.is_empty():
		return
	announce()
	_forced = true


func duty_visible() -> bool:
	return _duty_a > 0.01


func _rebuild() -> void:
	caption.text = String(view.get("caption", "")).to_upper()
	caption.visible = caption.text != ""
	line.text = InputSetup.resolve(String(view.get("title", "")))
	var full := guidance() == GUIDE_FULL
	# Full always has the box; in every mode a finished duty shows its tick (a recall after the fact)
	check.visible = not view.is_empty() and (full or bool(view.get("complete", false)))
	check.queue_redraw()
	for c in subs.get_children():
		subs.remove_child(c)
		c.queue_free()
	if full:
		var steps: Array = view.get("steps", [])
		for i in steps.size():
			var l := UIStyle.label("•  " + InputSetup.resolve(String(steps[i].get("text", ""))), 18, UIStyle.INK, UIStyle.serif())
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			l.modulate.a = 0.6 if i in done else 1.0
			subs.add_child(l)
	subs.visible = full and subs.get_child_count() > 0


func _draw_check() -> void:
	var s := check.size
	var y0 := UIStyle.px(5)
	check.draw_rect(Rect2(0, y0, s.x, s.x), Color(UIStyle.INK, 0.75), false, 1.5)
	if bool(view.get("complete", false)):
		check.draw_polyline(PackedVector2Array([Vector2(s.x * 0.18, y0 + s.x * 0.52), Vector2(s.x * 0.42, y0 + s.x * 0.78),
			Vector2(s.x * 0.86, y0 + s.x * 0.2)]), UIStyle.AMBER, 2.2, true)


## held: the screen is black (a fade or a chapter card): nothing counts down or shows under it.
func tick(delta: float, held: bool) -> void:
	var full := guidance() == GUIDE_FULL
	if not held and _show_t > 0.0:
		_show_t -= delta
		if _show_t <= 0.0:
			_forced = false
	var want_duty := not view.is_empty() and not held and (full or _show_t > 0.0) and (not compact or full or _forced)
	_duty_a = move_toward(_duty_a, 1.0 if want_duty else 0.0, delta / (FADE_IN if want_duty else FADE_OUT))
	var hint_a := hint.modulate.a if hint.text != "" else 0.0
	caption.modulate.a = _duty_a
	line.get_parent().modulate.a = _duty_a
	subs.modulate.a = _duty_a
	var show_duty_rows := _duty_a > 0.01
	caption.visible = show_duty_rows and caption.text != ""
	line.get_parent().visible = show_duty_rows
	subs.visible = show_duty_rows and full and subs.get_child_count() > 0
	hint.visible = hint_a > 0.01
	plate.modulate.a = maxf(_duty_a, hint_a)
	plate.visible = plate.modulate.a > 0.01
	_layout()


## Top-left inside the safe margin (below the notices); as wide as its longest text, at most MAX_W of the screen.
func _layout() -> void:
	var vp := get_viewport_rect().size
	var max_w := vp.x * MAX_W
	var w := 0.0
	for l in [caption, line, hint]:
		if l.visible and l.text != "":
			w = maxf(w, _text_w(l))
	if subs.visible:
		for l in subs.get_children():
			w = maxf(w, _text_w(l))
	if check.visible and line.get_parent().visible:
		w += check.custom_minimum_size.x + 10
	w = clampf(w + 2.0, UIStyle.px(120), max_w)
	check.custom_minimum_size = Vector2(UIStyle.px(16), UIStyle.px(16))
	box.custom_minimum_size.x = w
	plate.position = Vector2(vp.x * MARGIN, vp.y * TOP)
	plate.size = Vector2(0, 0)              # shrink to content (PanelContainer grows to its minimum)


static func _text_w(l: Label) -> float:
	var f: Font = l.get_theme_font("font")
	return f.get_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1, l.get_theme_font_size("font_size")).x
