class_name MenuLinks
extends HBoxContainer
## G6c (item 1, DECISIONS Q12): the bottom-right corner of the title. The signature "A game by Daniel
## Yanchev" is always there, in small letterspaced caps. To its left, the developer's links, read from
## data/links.json:
##   {"links": [{"label": "Instagram", "url": "https://...", "icon": "camera"}, ...]}
## icon: instagram | camera | mail | play (anything else draws a plain link arrow). Only https:// and mailto:
## URLs are accepted. The icons are drawn here in code (no image files). R2 (Daniel's playtest 2026-11-15):
## the Instagram link uses the recognisable Instagram glyph (rounded square, lens, dot), as Instagram's
## brand resources allow for linking to a profile; it replaced the generic camera. Each link
## rests at 45 % alpha and rises to full on hover or focus (hover takes the focus: one highlight only);
## pressing it opens the system browser or mail client. With no links (the shipped file is empty until
## Daniel sends them) only the signature shows.

const DEFAULT_PATH := "res://data/links.json"
const ICONS := ["instagram", "camera", "mail", "play"]
const REST_ALPHA := 0.45
const SIGNATURE := "A GAME BY DANIEL YANCHEV"

## Tests replace the opener (so nothing launches a browser); empty: OS.shell_open.
static var open_hook := Callable()

var entries: Array = []
var buttons: Array[Button] = []
var links_box: HBoxContainer
var divider: ColorRect
var signature: Label


## Read and validate a links file. Bad entries are skipped with a warning; a missing file is no links.
static func load_links(path: String) -> Array:
	var out := []
	if path == "" or not FileAccess.file_exists(path):
		return out
	var j = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(j) != TYPE_DICTIONARY or typeof(j.get("links")) != TYPE_ARRAY:
		push_warning("MenuLinks: %s has no \"links\" list" % path)
		return out
	for e in j["links"]:
		if typeof(e) != TYPE_DICTIONARY:
			continue
		var label := String(e.get("label", "")).strip_edges()
		var url := String(e.get("url", "")).strip_edges()
		if label == "" or not valid_url(url):
			push_warning("MenuLinks: skipped link '%s' (%s)" % [label, url])
			continue
		var icon := String(e.get("icon", ""))
		out.append({"label": label, "url": url, "icon": icon if icon in ICONS else "link"})
	return out


static func valid_url(url: String) -> bool:
	if url.contains(" ") or url.contains("\n") or url.contains("\t"):
		return false
	return (url.begins_with("https://") and url.length() > 9) or (url.begins_with("mailto:") and url.contains("@"))


static func open(url: String) -> void:
	if open_hook.is_valid():
		open_hook.call(url)
	elif valid_url(url):
		OS.shell_open(url)


func setup(path := DEFAULT_PATH) -> MenuLinks:
	entries = load_links(path)
	alignment = BoxContainer.ALIGNMENT_END
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_theme_constant_override("separation", 22)
	links_box = HBoxContainer.new()
	links_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	links_box.add_theme_constant_override("separation", 22)
	add_child(links_box)
	for e in entries:
		var b := LinkItem.new(e)
		links_box.add_child(b)
		buttons.append(b)
	divider = ColorRect.new()
	divider.color = Color(UIStyle.INK, 0.25)
	divider.custom_minimum_size = Vector2(1, 14)
	divider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	divider.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(divider)
	signature = UIStyle.label(SIGNATURE, UIStyle.MENU_CORNER, UIStyle.INK_SUB, UIStyle.caps())   # 0.64 measured 2.8:1
	signature.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	signature.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(signature)
	links_box.visible = not entries.is_empty()
	divider.visible = links_box.visible
	return self


## Lock (a panel is open over the title) or unlock the links.
func set_locked(on: bool) -> void:
	for b in buttons:
		b.focus_mode = Control.FOCUS_NONE if on else Control.FOCUS_ALL
		b.mouse_filter = Control.MOUSE_FILTER_IGNORE if on else Control.MOUSE_FILTER_STOP


class LinkItem extends Button:
	var url := ""
	var kind := "link"
	var _tw: Tween

	func _init(e: Dictionary) -> void:
		text = String(e["label"]).to_upper()
		url = String(e["url"])
		kind = String(e["icon"])
		tooltip_text = url.trim_prefix("mailto:")
		focus_mode = Control.FOCUS_ALL
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		add_theme_font_override("font", UIStyle.caps())
		var box := StyleBoxEmpty.new()
		box.content_margin_left = 26
		box.content_margin_top = 6
		box.content_margin_bottom = 6
		for s in ["normal", "hover", "pressed", "hover_pressed", "focus", "disabled"]:
			add_theme_stylebox_override(s, box)
		for k in ["font_color", "font_hover_color", "font_focus_color", "font_pressed_color", "font_hover_pressed_color"]:
			add_theme_color_override(k, UIStyle.INK)
		UIStyle.track(self, UIStyle.MENU_CORNER)
		modulate.a = MenuLinks.REST_ALPHA
		focus_entered.connect(func(): _lit(true))
		focus_exited.connect(func(): _lit(false))
		mouse_entered.connect(func():
			if focus_mode != Control.FOCUS_NONE and not has_focus():
				grab_focus())
		pressed.connect(func(): MenuLinks.open(url))

	## Icon scale: the icon follows the label's size (text size option, small-window floor).
	func _k() -> float:
		return get_theme_font_size("font_size") / float(UIStyle.MENU_CORNER)

	func _notification(what: int) -> void:
		if what == NOTIFICATION_THEME_CHANGED:
			var box := get_theme_stylebox("normal") as StyleBoxEmpty
			var m := roundf(26.0 * _k())
			if box and absf(box.content_margin_left - m) > 0.5:   # (setting it re-sends THEME_CHANGED)
				box.content_margin_left = m
			queue_redraw()

	func _lit(on: bool) -> void:
		if _tw:
			_tw.kill()
		var a := 1.0 if on else MenuLinks.REST_ALPHA
		if MenuItem.calm():
			modulate.a = a
			return
		_tw = create_tween()
		_tw.tween_property(self, "modulate:a", a, 0.15)

	func _draw() -> void:
		var c := UIStyle.INK
		var k := _k()
		# R2 (issues 5, 6): the icon is centred on the capitals, not on the button (the camera and the envelope
		# sat at different heights against the text), and drawn on one 16-unit grid with one stroke weight.
		var f := get_theme_font("font")
		var fs := get_theme_font_size("font_size")
		var cy := (size.y - f.get_height(fs)) * 0.5 + f.get_ascent(fs) - 0.66 * fs * 0.5
		var o := Vector2(2.0, roundf(cy - 8.0 * k))
		var w := 1.5 * k
		match kind:
			"instagram":                 # the Instagram glyph: rounded square, lens ring, viewfinder dot
				_rrect(Rect2(0, 0, 16, 16), 4.6, o, c, w)
				draw_arc(o + Vector2(8, 8) * k, 3.7 * k, 0.0, TAU, 36, c, w, true)
				draw_circle(o + Vector2(12.3, 3.7) * k, 1.05 * k, c, true, -1.0, true)
			"camera":                    # a generic camera: body, viewfinder hump, round lens
				_poly([Vector2(0, 5), Vector2(4, 5), Vector2(5.5, 2.5), Vector2(10.5, 2.5), Vector2(12, 5),
					Vector2(16, 5), Vector2(16, 15), Vector2(0, 15), Vector2(0, 5)], o, c, w)
				draw_arc(o + Vector2(8, 10) * k, 3.4 * k, 0.0, TAU, 28, c, w, true)
			"mail":                      # an envelope: rounded corners, the flap meeting just below the middle
				_rrect(Rect2(0, 2.5, 16, 11), 1.6, o, c, w)
				_poly([Vector2(0.9, 3.6), Vector2(8, 9.2), Vector2(15.1, 3.6)], o, c, w)
			"play":                      # a play triangle in a rounded screen
				_poly([Vector2(2, 2), Vector2(14, 2), Vector2(16, 4), Vector2(16, 12), Vector2(14, 14), Vector2(2, 14),
					Vector2(0, 12), Vector2(0, 4), Vector2(2, 2)], o, c, w)
				draw_colored_polygon(PackedVector2Array([o + Vector2(6.5, 5) * k, o + Vector2(6.5, 11) * k, o + Vector2(11.5, 8) * k]), c)
			_:                           # a plain "opens elsewhere" arrow
				_poly([Vector2(8, 2), Vector2(1, 2), Vector2(1, 15), Vector2(14, 15), Vector2(14, 8)], o, c, w)
				_poly([Vector2(7, 9), Vector2(15, 1)], o, c, w)
				_poly([Vector2(10, 1), Vector2(15, 1), Vector2(15, 6)], o, c, w)

	## A rounded rectangle outline (grid units), closed, with 6 segments per corner.
	func _rrect(r: Rect2, rad: float, o: Vector2, c: Color, w: float) -> void:
		var pts: Array = []
		var corners := [[r.position + Vector2(r.size.x - rad, rad), -PI * 0.5], [r.end - Vector2(rad, rad), 0.0],
			[Vector2(r.position.x + rad, r.end.y - rad), PI * 0.5], [r.position + Vector2(rad, rad), PI]]
		for cn in corners:
			for i in 7:
				var a: float = cn[1] + PI * 0.5 * i / 6.0
				pts.append(cn[0] + Vector2(cos(a), sin(a)) * rad)
		pts.append(pts[0])
		_poly(pts, o, c, w)

	func _poly(pts: Array, o: Vector2, c: Color, w: float) -> void:
		var k := _k()
		var p := PackedVector2Array()
		for q in pts:
			p.append(o + q * k)
		draw_polyline(p, c, w, true)
