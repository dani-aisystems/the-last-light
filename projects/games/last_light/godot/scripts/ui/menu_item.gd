class_name MenuItem
extends Button
## G6c ("Still Water", Daniel 2026-11-09), G6d stage E: one title-menu entry. No box in any state. The rank
## shows in brightness: the primary pair (Continue and New Game; New Game alone with no save) is full
## parchment, the rest a quieter tone; the `top` item (Continue, or New Game with no save) is also larger.
## The focused item alone is amber, with a soft warm glow behind its text (menu_glow.gdshader: an ellipse
## about 1.6x the text width, fading in over 0.25 s, eased each frame from has_focus()); hover takes the
## focus, so there is only ever one highlight. While the item is focused its glow brightens a little each
## time the real beam sweeps towards the camera (glow_source, 0..1). Reduce motion: the glow appears at once
## and holds still (no beam); Reduce flashing: no beam swell either.

const GUTTER := 30                 # left margin before the text (lines the column up with the logo)
const PAD := 12                    # vertical content margin; the entrance "rise" moves text within it
const GLOW_W := 1.6                # the glow's width, in text widths
const GLOW_H := 2.6                # its height, in font sizes
const GLOW_BASE := 0.2             # its strength when focused ...
const GLOW_BEAM := 0.12            # ... plus this much as the beam faces the camera
const FADE_S := 0.25

var top := false
var bright := false
var glow_source := Callable()      # -> float 0..1 (game_fp.beam_facing); empty: no glow
var mark := 0.0                    # the focus glow's fade 0..1
var glow := 0.0                    # last beam factor drawn
var rise := 0.0                    # entrance offset in px (text drawn this much lower)
var _box: StyleBoxEmpty
var _glow_rect: ColorRect
var _glow_mat: ShaderMaterial
var _was_focused := false


func setup(text_: String, size_: int, top_: bool, bright_ := top_) -> MenuItem:
	text = text_
	top = top_
	bright = bright_
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
	_glow_mat = ShaderMaterial.new()
	_glow_mat.shader = preload("res://shaders/menu_glow.gdshader")
	_glow_rect = ColorRect.new()
	_glow_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_glow_rect.show_behind_parent = true          # under the text, which the Button draws itself
	_glow_rect.material = _glow_mat
	_glow_rect.visible = false
	add_child(_glow_rect)
	resized.connect(_place_glow)
	_tone()
	_place_glow()
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
	return UIStyle.INK if bright else UIStyle.INK_QUIET


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
	_place_glow()


func set_rise(px: float) -> void:
	_set_rise(clampf(px, 0.0, PAD))


## Every frame the glow follows has_focus() itself (a 0.25 s fade, at once with Reduce motion), so no
## order of focus signals (window focus changes, deferred grabs) can leave a focused item without it.
func _process(delta: float) -> void:
	var focused := has_focus()
	if focused != _was_focused:
		_was_focused = focused
		_tone()
	var target := 1.0 if focused else 0.0
	var changed := false
	if mark != target:
		mark = target if calm() else move_toward(mark, target, delta / FADE_S)
		changed = true
	var g := 0.0
	if mark > 0.0 and glow_source.is_valid() and not calm() and not bool(setting("reduce_flashing", false)):
		g = clampf(float(glow_source.call()), 0.0, 1.0)
	if absf(g - glow) > 0.01 or (g == 0.0 and glow != 0.0):
		glow = g
		changed = true
	if changed:
		_place_glow()


## Width of the label text in its current font and size (the glow is centred on it).
func text_width() -> float:
	return get_theme_font("font").get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, get_theme_font_size("font_size")).x


## The glow rect: centred on the text (its centre line, following the entrance rise), GLOW_W text widths
## wide, whole canvas pixels; drawn behind the Button's own text.
func _place_glow() -> void:
	if _glow_rect == null:
		return
	var tw := text_width()
	var fs := float(get_theme_font_size("font_size"))
	var w := roundf(tw * GLOW_W)
	var h := roundf(fs * GLOW_H)
	_glow_rect.position = Vector2(roundf(GUTTER + tw * 0.5 - w * 0.5), roundf(size.y * 0.5 + rise - h * 0.5))
	_glow_rect.size = Vector2(w, h)
	_glow_rect.visible = mark > 0.0
	_glow_mat.set_shader_parameter("strength", mark * (GLOW_BASE + GLOW_BEAM * glow))


## The glow's rect and strength now (tests).
func glow_rect() -> Rect2:
	return _glow_rect.get_global_rect() if _glow_rect.visible else Rect2()


func glow_strength() -> float:
	return float(_glow_mat.get_shader_parameter("strength")) if _glow_rect.visible else 0.0


func _notification(what: int) -> void:
	if what == NOTIFICATION_THEME_CHANGED:        # the text size option: the glow follows the text
		_place_glow()
