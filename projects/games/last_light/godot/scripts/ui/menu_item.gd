class_name MenuItem
extends Button
## G6c ("Still Water", Daniel 2026-11-09): one title-menu entry. No box in any state. The rank shows in
## brightness, not size: a `top` item (Continue, or New Game with no save) is full parchment, the rest a
## quieter tone. The focused item alone is amber, with a thin amber rule (the lamp tick) sliding in from
## the left gutter (child rects, eased each frame from has_focus()); hover takes the focus, so there is only ever one highlight. While the item is
## focused the tick swells a little each time the real beam sweeps towards the camera (glow_source,
## 0..1); Reduce motion and Reduce flashing turn the glow and the slide off.

const GUTTER := 30                 # the tick lives here, left of the text
const TICK_W := 16.0
const TICK_X := 4.0
const PAD := 8                     # vertical content margin; the entrance "rise" moves text within it

var top := false
var glow_source := Callable()      # -> float 0..1 (game_fp.beam_facing); empty: no glow
var mark := 0.0                    # tick progress 0..1 (tweened)
var glow := 0.0                    # last beam factor drawn
var rise := 0.0                    # entrance offset in px (text drawn this much lower)
var _box: StyleBoxEmpty
var _tick: ColorRect
var _was_focused := false
var _halo: ColorRect


func setup(text_: String, size_: int, top_: bool) -> MenuItem:
	text = text_
	top = top_
	alignment = HORIZONTAL_ALIGNMENT_LEFT
	focus_mode = Control.FOCUS_ALL
	size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	add_theme_font_override("font", UIStyle.serif())
	_box = StyleBoxEmpty.new()
	_box.content_margin_left = GUTTER
	_box.content_margin_right = 12
	_set_rise(0.0)
	for s in ["normal", "hover", "pressed", "hover_pressed", "focus", "disabled"]:
		add_theme_stylebox_override(s, _box)
	UIStyle.track(self, size_)
	_halo = ColorRect.new()
	_halo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_halo)
	_tick = ColorRect.new()
	_tick.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_tick)
	resized.connect(_place_tick)
	_tone()
	_place_tick()
	focus_entered.connect(_tone)
	focus_exited.connect(_tone)
	mouse_entered.connect(func():
		if focus_mode != Control.FOCUS_NONE and not disabled and is_visible_in_tree() and not has_focus():
			grab_focus())
	return self


## Settings, read through the tree: a class_name script can't name an autoload under -s (G6a gotcha).
static func setting(key: String, fallback = null):
	var tree := Engine.get_main_loop() as SceneTree
	var st: Node = tree.root.get_node_or_null("Settings") if tree else null
	return st.v.get(key, fallback) if st else fallback


static func calm() -> bool:
	return bool(setting("reduce_motion", false))


## The colour this item's text is drawn in now (tests read it).
func tone_color() -> Color:
	if has_focus():
		return UIStyle.AMBER
	return UIStyle.INK if top else UIStyle.INK_QUIET


func _tone() -> void:
	var c := tone_color()
	for k in ["font_color", "font_hover_color", "font_focus_color", "font_pressed_color", "font_hover_pressed_color"]:
		add_theme_color_override(k, c)
	add_theme_color_override("font_disabled_color", UIStyle.INK_FAINT)


## Entrance: the text sits `px` lower inside the same height (top margin up, bottom margin down).
func _set_rise(px: float) -> void:
	rise = px
	_box.content_margin_top = PAD + px
	_box.content_margin_bottom = maxf(PAD - px, 0.0)
	_place_tick()


func set_rise(px: float) -> void:
	_set_rise(clampf(px, 0.0, PAD))


## Every frame the tick follows has_focus() itself (0.15 s ease, at once with Reduce motion), so no
## order of focus signals (window focus changes, deferred grabs) can leave a focused item without it.
func _process(delta: float) -> void:
	var focused := has_focus()
	if focused != _was_focused:
		_was_focused = focused
		_tone()
	var target := 1.0 if focused else 0.0
	var changed := false
	if mark != target:
		mark = target if calm() else move_toward(mark, target, delta / 0.15)
		changed = true
	var g := 0.0
	if mark > 0.0 and glow_source.is_valid() and not calm() and not bool(setting("reduce_flashing", false)):
		g = clampf(float(glow_source.call()), 0.0, 1.0)
	if absf(g - glow) > 0.01 or (g == 0.0 and glow != 0.0):
		glow = g
		changed = true
	if changed:
		_place_tick()


## The tick and its halo are child rects (engine-drawn), placed on the text's centre line.
func _place_tick() -> void:
	if _tick == null:
		return
	# whole canvas pixels, and at least 2 window pixels tall: a small window shrinks the 1080-line canvas
	# (0.67x at 720p), and a 2 px rect on a half pixel was lost entirely (G6c small-window capture)
	var k := get_viewport_transform().get_scale().y if is_inside_tree() else 1.0
	var h := maxf(2.0, ceilf(2.0 / maxf(k, 0.1)))
	var y := roundf(size.y * 0.5 + rise - h * 0.5)
	var w := roundf(TICK_W * mark)
	_tick.visible = mark > 0.0
	_tick.position = Vector2(TICK_X, y)
	_tick.size = Vector2(w, h)
	_tick.color = Color(UIStyle.AMBER, 0.78 + 0.22 * glow)
	_halo.visible = mark > 0.0 and glow > 0.0      # a soft halo, only while the beam faces the camera
	_halo.position = Vector2(TICK_X - 3.0, y - 3.0)
	_halo.size = Vector2(w + 6.0, h + 6.0)
	_halo.color = Color(UIStyle.AMBER, 0.12 * glow * mark)
