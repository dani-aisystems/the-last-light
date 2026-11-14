extends Node
## THE LAST LIGHT root: cinematic title over the live lighthouse exterior, Continue / New Game / Load /
## Options / Credits / Quit, a loading screen that tracks real threaded loading, and the transition
## into the watch room. CLI (after --): --seed=N --windowed --bot=expert --mode=watch|story
##   --capture=NAME --shots=...   --autotest=SECONDS [--autotest-out=PATH]   --load=SLOT

const GAME := preload("res://scripts/fp/game_fp.gd")
const PRELOAD := ["res://assets/models/watch_room.glb", "res://assets/models/lighthouse.glb"]

var game: Node3D
var menu_bg: Node3D
var menu: CanvasLayer
var panel: Control
var _loading: CanvasLayer

## G6c "Still Water" title (FINDINGS item 1). Captures and tests (presenter-side user args):
##   --links=PATH (another links file)  --menu_focus=<item>  --menu_nosave  --menu_fake_save  --win=WxH
const LOGO_W := 640.0
const LOGO_INK_W := LOGO_W - 16.0          # the logotype's glyphs (8 px clear each side in the PNG)
## G6d stage E (DECISIONS Q14): two lines, centred under the logotype's visual width.
const SUBTITLE := ["NORTH POINT LIGHT  ·  OUTER HEBRIDES", "THE MIDDLE WATCH  ·  14–15 NOVEMBER 1971"]
const META_FADE_S := 0.25
const ROMAN := ["", "I", "II", "III", "IV", "V", "VI", "VII"]
const MONTHS := ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
const FAKE_SAVE := {"story": {"chapter": 1, "play_seconds": 1320}, "chapter_title": "The Watch", "clock": "20:20",
	"saved_at": "2026-11-06T12:01:00"}
var menu_items: Array[MenuItem] = []
var menu_col: VBoxContainer
var menu_meta: Label                   # G6d stage E: the save, shown only while Continue has the focus
var menu_sub: VBoxContainer
var menu_corner: MenuLinks
var credits_roll: CreditsRoll
var _menu_root: Control
var _menu_margin: MarginContainer
var _last_item: Control
var _small_text: Array[Control] = []   # subtitle, save line, corner: kept legible in small windows


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var args: Dictionary = GameState.user_args
	if args.has("windowed") or args.has("capture") or args.has("autotest"):
		var win := Vector2i(1920, 1080)
		var wp := String(args.get("win", "")).split("x")
		if wp.size() == 2 and int(wp[0]) >= 640 and int(wp[1]) >= 360:
			win = Vector2i(int(wp[0]), int(wp[1]))
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_size(win)
		if args.has("win"):
			_resize_later(win)
		DisplayServer.window_set_position(DisplayServer.screen_get_usable_rect().position + Vector2i(10, 10))
	Settings.apply_render_scale()          # preset x HiDPI fit (or --scale3d), re-applied on resize
	if args.has("capture"):
		var cap := preload("res://scripts/capture_fp.gd").new()
		cap.main = self
		add_child(cap)
		show_menu()
	elif args.has("autotest"):
		var at := preload("res://scripts/autotest.gd").new()
		at.main = self
		add_child(at)
		start_game(args.get("bot", "expert"), args.get("mode", "story") == "story")
	elif args.has("load"):
		load_slot(args["load"])
	else:
		show_menu()


## --win=WxH (G6c captures at other aspects): macOS leaves the project's start-up fullscreen
## asynchronously and drops a size set during that, so set it again once the window has settled. The size
## is in screen points on a Retina display (1280x720 -> a 2560x1440 px 16:9 frame).
func _resize_later(win: Vector2i) -> void:
	for i in 3:
		await get_tree().create_timer(0.35).timeout
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_size(win)
		DisplayServer.window_set_position(DisplayServer.screen_get_usable_rect().position + Vector2i(10, 10))


func _unhandled_input(event: InputEvent) -> void:
	if (event.is_action_pressed("pause") or event.is_action_pressed("back")) and panel and is_instance_valid(panel):
		_close_panel()                     # Options opened from the pause menu: Esc goes back to the pause menu
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("pause") and game and get_tree().paused:
		game.set_paused(false)
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("fullscreen"):
		var full := DisplayServer.window_get_mode() == DisplayServer.WINDOW_MODE_FULLSCREEN
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED if full else DisplayServer.WINDOW_MODE_FULLSCREEN)


func _clear() -> void:
	get_tree().paused = false
	for n in [game, menu_bg, menu, _loading]:
		if n and is_instance_valid(n):
			n.queue_free()
	game = null
	menu_bg = null
	menu = null
	panel = null
	_loading = null
	menu_items.clear()
	menu_col = null
	menu_meta = null
	menu_sub = null
	menu_corner = null
	credits_roll = null
	_menu_root = null
	_menu_margin = null
	_last_item = null
	_small_text.clear()


# ------------------------------------------------------------------ title

func show_menu() -> void:
	_clear()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	menu_bg = GAME.new()
	add_child(menu_bg)
	menu_bg.start(GameState.next_seed(), "expert", true, false)
	menu = CanvasLayer.new()
	add_child(menu)
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	menu.add_child(root)
	_menu_root = root
	var grad := TextureRect.new()
	var gt := GradientTexture2D.new()
	var g := Gradient.new()
	g.set_color(0, Color(0, 0.01, 0.02, 0.78))
	g.set_color(1, Color(0, 0.01, 0.02, 0.0))
	gt.gradient = g
	gt.fill_to = Vector2(0.6, 0)
	grad.texture = gt
	grad.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	grad.stretch_mode = TextureRect.STRETCH_SCALE
	grad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(grad)
	var low := TextureRect.new()                 # G6c: a soft floor so the corner reads over the near reef
	var lt := GradientTexture2D.new()
	var lg := Gradient.new()
	lg.set_color(0, Color(0, 0.01, 0.02, 0.62))
	lg.set_color(1, Color(0, 0.01, 0.02, 0.0))
	lt.gradient = lg
	lt.fill_from = Vector2(0.5, 1.0)
	lt.fill_to = Vector2(0.5, 0.8)
	low.texture = lt
	low.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	low.stretch_mode = TextureRect.STRETCH_SCALE
	low.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(low)
	# the column: margins from the screen size (_layout_menu), the text on one left edge; the lamp tick
	# hangs in the items' gutter to the left of it
	_menu_margin = MarginContainer.new()
	_menu_margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_menu_margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_menu_margin)
	menu_col = VBoxContainer.new()
	menu_col.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	menu_col.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	menu_col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	menu_col.add_theme_constant_override("separation", 0)
	_menu_margin.add_child(menu_col)
	var logo := TextureRect.new()             # Daniel's logotype (branding/make_branding.py)
	logo.texture = preload("res://assets/branding/logo_title.png")
	logo.custom_minimum_size = Vector2(LOGO_W, round(LOGO_W * 219.0 / 760.0))
	logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var logo_box := _indent(logo)
	logo_box.add_theme_constant_override("margin_left", MenuItem.GUTTER - 8)   # the PNG's glyphs start 8 px in
	_gap(14)
	menu_sub = VBoxContainer.new()
	menu_sub.mouse_filter = Control.MOUSE_FILTER_IGNORE
	menu_sub.custom_minimum_size = Vector2(LOGO_INK_W, 0)
	menu_sub.add_theme_constant_override("separation", 4)
	for line in SUBTITLE:
		var sl := UIStyle.label(line, UIStyle.MENU_SUB, UIStyle.INK, UIStyle.caps())
		sl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		sl.mouse_filter = Control.MOUSE_FILTER_IGNORE
		menu_sub.add_child(sl)
		_small_text.append(sl)
	var sub := _indent(menu_sub)
	_gap(44)
	var seq: Array[Control] = []
	var latest := _menu_latest()
	if latest != "":
		seq.append(_item("Continue", true, func(): load_slot(latest)))
		menu_meta = UIStyle.label(save_line(FAKE_SAVE if latest == "__fake__" else SaveSystem.read(latest)), UIStyle.MENU_META, UIStyle.INK_FAINT, UIStyle.typewriter())
		menu_meta.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.0))
		menu_meta.modulate.a = 0.0                # its slot is always reserved: showing it moves nothing
		_small_text.append(menu_meta)
		seq.append(_indent(menu_meta))
		_gap(10)
	seq.append(_item("New Game", latest == "", _new_game, true))
	_gap(30)
	for it in [["Load Game", _open_load], ["Options", _open_options], ["Credits", _open_credits], ["Quit", func(): get_tree().quit()]]:
		seq.append(_item(it[0], false, it[1]))
	menu_corner = MenuLinks.new().setup(String(GameState.user_args.get("links", MenuLinks.DEFAULT_PATH)))
	menu_corner.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	menu_corner.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	menu_corner.grow_vertical = Control.GROW_DIRECTION_BEGIN
	root.add_child(menu_corner)
	_small_text.append(menu_corner.signature)
	_small_text.append_array(menu_corner.buttons)
	for c in _small_text:
		c.set_meta("menu_base", int(c.get_meta("ui_base", 14)))
	for b in menu_corner.buttons:
		b.pressed.connect(func():
			if menu_bg and menu_bg.audio:
				menu_bg.audio.sfx("ui_click", -6.0, "SFX"))
	root.resized.connect(_layout_menu)
	if not get_window().size_changed.is_connected(_layout_menu):
		get_window().size_changed.connect(_layout_menu)   # a smaller window keeps the canvas: re-floor the text
	_layout_menu()
	_wire_focus()
	_entrance(logo_box, sub, seq)
	menu_items[0].grab_focus.call_deferred()
	if GameState.user_args.has("menu_hide"):
		root.visible = false                 # G6d: exterior audit captures from the title world
	var want := String(GameState.user_args.get("menu_focus", "")).to_lower()
	for b in menu_items:
		if want != "" and b.text.to_lower() == want:
			b.grab_focus.call_deferred()


## Which save Continue loads ("" none; "__fake__" a fixed sample save for captures and tests).
func _menu_latest() -> String:
	if GameState.user_args.has("menu_nosave"):
		return ""
	if GameState.user_args.has("menu_fake_save"):
		return "__fake__"
	return SaveSystem.latest()


## The save as a typed log line under Continue: "CHAPTER I · THE WATCH · 20.20 · SAVED 6 NOV" (G6d stage E:
## no minutes played, no time of the save).
func save_line(d: Dictionary) -> String:
	if d.is_empty() or d.has("corrupt"):
		return ""
	var st: Dictionary = d.get("story", {})
	var parts := PackedStringArray(["CHAPTER " + ROMAN[clampi(int(st.get("chapter", 1)), 1, ROMAN.size() - 1)]])
	var title := String(d.get("chapter_title", "")).strip_edges().to_upper()
	if title != "":
		parts.append(title)
	var clock := String(d.get("clock", "")).replace(":", ".")
	if clock != "":
		parts.append(clock)
	var at := String(d.get("saved_at", ""))                # 2026-11-06T12:01:00
	if at.length() >= 10:
		parts.append("SAVED %d %s" % [int(at.substr(8, 2)), MONTHS[clampi(int(at.substr(5, 2)), 1, 12) - 1]])
	return " · ".join(parts)


func _gap(px: int) -> void:
	var sp := Control.new()
	sp.custom_minimum_size = Vector2(0, px)
	sp.mouse_filter = Control.MOUSE_FILTER_IGNORE
	menu_col.add_child(sp)


## A column entry whose left edge lines up with the items' text (past their tick gutter).
func _indent(c: Control) -> MarginContainer:
	var m := MarginContainer.new()
	m.add_theme_constant_override("margin_left", MenuItem.GUTTER)
	m.mouse_filter = Control.MOUSE_FILTER_IGNORE
	m.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	m.add_child(c)
	menu_col.add_child(m)
	return m


func _item(text: String, top: bool, f: Callable, bright := top) -> MenuItem:
	var b := MenuItem.new().setup(text, UIStyle.MENU_TOP if top else UIStyle.MENU_ITEM, top, bright)
	b.glow_source = _beam_glow
	b.pressed.connect(func():
		_last_item = b
		if menu_bg and menu_bg.audio:
			menu_bg.audio.sfx("ui_click", -6.0, "SFX")
		f.call())
	b.mouse_entered.connect(func():
		if menu_bg and menu_bg.audio and b.focus_mode != Control.FOCUS_NONE:
			menu_bg.audio.sfx("ui_hover", -10.0, "SFX"))
	menu_col.add_child(b)
	menu_items.append(b)
	return b


## G6d stage E: the Continue info fades in while Continue has the focus and out when it leaves (at once
## under Reduce motion). Its slot never collapses, so nothing below it moves.
func _process(delta: float) -> void:
	if menu_meta == null or not is_instance_valid(menu_meta) or menu_items.is_empty():
		return
	var want := 1.0 if menu_items[0].text == "Continue" and menu_items[0].has_focus() else 0.0
	var a := menu_meta.modulate.a
	if a != want:
		menu_meta.modulate.a = want if MenuItem.calm() else move_toward(a, want, delta / META_FADE_S)


func _beam_glow() -> float:
	return menu_bg.beam_facing() if menu_bg and is_instance_valid(menu_bg) else 0.0


## Margins follow the canvas: the text at 6.5 % of the width, the logo's top at 20 % of the height, the
## corner inset by 3 % of a 16:9 width (so ultrawide doesn't push it into the far edge).
func _layout_menu() -> void:
	if _menu_root == null or not is_instance_valid(_menu_root):
		return
	var s := _menu_root.size
	# small windows shrink the 1080-line canvas: keep the small caps and the save line at >= 12 window px
	# (render pixels, not window points: a Retina window's size is in points)
	var phys := float(get_viewport().get_texture().get_size().y) / maxf(s.y, 1.0)
	var floor_px := mini(ceili(12.0 / maxf(phys, 0.1)), UIStyle.MENU_ITEM - 2)   # never above the items
	for c in _small_text:
		if is_instance_valid(c):
			UIStyle.track(c, maxi(int(c.get_meta("menu_base", 14)), floor_px))
	_menu_margin.add_theme_constant_override("margin_left", int(round(s.x * 0.065)) - MenuItem.GUTTER)
	_menu_margin.add_theme_constant_override("margin_top", int(round(s.y * 0.16)))
	var m := roundf(minf(s.x, s.y * 16.0 / 9.0) * 0.03)
	menu_corner.offset_right = -m
	menu_corner.offset_left = -m
	menu_corner.offset_bottom = -roundf(m * 0.75)
	menu_corner.offset_top = -roundf(m * 0.75)


## Explicit neighbours: down walks the items, then the links, and wraps; up walks back. Tab does the same.
func _wire_focus() -> void:
	var chain: Array[Control] = []
	chain.append_array(menu_items)
	chain.append_array(menu_corner.buttons)
	var n := chain.size()
	for i in n:
		var c := chain[i]
		var nx := chain[(i + 1) % n]
		var pv := chain[(i - 1 + n) % n]
		c.focus_neighbor_bottom = c.get_path_to(nx)
		c.focus_neighbor_top = c.get_path_to(pv)
		c.focus_next = c.get_path_to(nx)
		c.focus_previous = c.get_path_to(pv)
		var links := c in menu_corner.buttons
		c.focus_neighbor_left = c.get_path_to(pv if links and i > menu_items.size() else c)
		c.focus_neighbor_right = c.get_path_to(nx if links and i < n - 1 else c)


## The entrance: the logo, then the subtitle, then the items rise and fade in turn, then the corner.
## Reduce motion: one plain fade of everything.
func _entrance(logo: Control, sub: Control, seq: Array[Control]) -> void:
	if MenuItem.calm():
		_menu_root.modulate.a = 0.0
		_menu_root.create_tween().tween_property(_menu_root, "modulate:a", 1.0, 1.0)
		return
	logo.modulate.a = 0.0
	logo.create_tween().tween_property(logo, "modulate:a", 1.0, 2.0).set_trans(Tween.TRANS_SINE)
	sub.modulate.a = 0.0
	sub.create_tween().tween_property(sub, "modulate:a", 1.0, 1.0).set_delay(0.6)
	var t := 0.9
	for c in seq:
		c.modulate.a = 0.0
		var tw := c.create_tween().set_parallel(true)
		tw.tween_property(c, "modulate:a", 1.0, 0.45).set_delay(t)
		if c is MenuItem:
			(c as MenuItem).set_rise(MenuItem.PAD)
			tw.tween_method((c as MenuItem).set_rise, float(MenuItem.PAD), 0.0, 0.5).set_delay(t) \
				.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		t += 0.07
	menu_corner.modulate.a = 0.0
	menu_corner.create_tween().tween_property(menu_corner, "modulate:a", 1.0, 0.6).set_delay(1.6)


## A panel or the credits over the title: the column and the links take no input until it closes.
func _lock_menu(on: bool) -> void:
	for b in menu_items:
		if is_instance_valid(b):
			b.focus_mode = Control.FOCUS_NONE if on else Control.FOCUS_ALL
			b.mouse_filter = Control.MOUSE_FILTER_IGNORE if on else Control.MOUSE_FILTER_STOP
	if menu_corner and is_instance_valid(menu_corner):
		menu_corner.set_locked(on)


func _restore_menu_focus() -> void:
	if menu_items.is_empty():
		return
	var t: Control = menu_items[0]
	if _last_item and is_instance_valid(_last_item) and _last_item.is_visible_in_tree():
		t = _last_item
	t.grab_focus()
func _new_game() -> void:
	if SaveSystem.exists("auto"):
		_confirm("Start a new story? Your autosave will be replaced when the new night begins.", func(): _transition_in({}))
	else:
		_transition_in({})


func load_slot(slot: String) -> void:
	var d := SaveSystem.read(slot)
	if d.is_empty() or d.has("corrupt"):
		if menu == null:
			show_menu()
		return
	_transition_in(d)


# ------------------------------------------------------------------ loading + transition

func _transition_in(save: Dictionary) -> void:
	var cam: Camera3D = menu_bg.cine_cam if menu_bg else null
	if cam and menu:
		_lock_menu(true)
		create_tween().tween_property(menu.get_child(0), "modulate:a", 0.0, 0.8)
		menu_bg.cine_hold = true           # the orbit stops driving the camera
		var start := cam.position
		var q0 := cam.quaternion           # G6c: from the offset title framing, no snap to the tower
		var tw2 := create_tween()
		tw2.tween_method(func(k: float):
			var e := ease(k, 2.4)
			cam.position = start.lerp(Vector3(0, 21.5, -16.0), e)
			var aim := Transform3D(Basis(), cam.position).looking_at(Vector3(0, 21.5, 0), Vector3.UP)
			cam.quaternion = q0.slerp(aim.basis.get_rotation_quaternion(), e), 0.0, 1.0, 2.6)
		await tw2.finished
	_show_loading(save)


func _show_loading(save: Dictionary) -> void:
	var ch := int(save.get("story", {}).get("chapter", 1))
	_clear()
	_loading = CanvasLayer.new()
	_loading.layer = 40
	add_child(_loading)
	var root := ColorRect.new()
	root.color = Color(0.01, 0.015, 0.025)
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_loading.add_child(root)
	var t := UIStyle.label(["", "I · The Watch", "II · Strange Signals", "III · The Storm", "IV · The Visitor", "V · The Truth", "VI · The Last Light"][clampi(ch, 1, 6)], 44, UIStyle.INK, UIStyle.serif())
	t.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	t.offset_left = -600
	t.offset_right = 600
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	root.add_child(t)
	var bar := ProgressBar.new()
	bar.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	bar.offset_left = -220
	bar.offset_right = 220
	bar.offset_top = -120
	bar.offset_bottom = -112
	bar.show_percentage = false
	var fill := StyleBoxFlat.new()
	fill.bg_color = UIStyle.AMBER
	bar.add_theme_stylebox_override("fill", fill)
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(1, 1, 1, 0.08)
	bar.add_theme_stylebox_override("background", bg)
	root.add_child(bar)
	for p in PRELOAD:
		ResourceLoader.load_threaded_request(p)
	while true:
		var total := 0.0
		var done := true
		for p in PRELOAD:
			var prog := []
			var st := ResourceLoader.load_threaded_get_status(p, prog)
			total += 1.0 if st == ResourceLoader.THREAD_LOAD_LOADED else (float(prog[0]) if prog.size() > 0 else 0.0)
			if st == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
				done = false
		bar.value = total / PRELOAD.size() * 100.0
		if done:
			break
		await get_tree().process_frame
	for p in PRELOAD:
		ResourceLoader.load_threaded_get(p)      # now cached for the game's load()
	start_game("", true, save)
	var tw := create_tween()
	tw.tween_property(root, "modulate:a", 0.0, 1.2)
	tw.tween_callback(func():
		if _loading:
			_loading.queue_free()
			_loading = null)


func start_game(bot_mode: String, story := true, save: Dictionary = {}) -> void:
	for n in [menu_bg, menu]:
		if n and is_instance_valid(n):
			n.queue_free()
	menu_bg = null
	menu = null
	if game and is_instance_valid(game):
		game.queue_free()
	game = GAME.new()
	game.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(game)
	if bot_mode == "" and GameState.user_args.has("bot"):
		bot_mode = GameState.user_args["bot"]
	if GameState.user_args.get("mode", "story") == "watch":
		story = false
	game.start(GameState.next_seed(), bot_mode, false, story, save)
	game.finished.connect(_on_finished)
	game.quit_to_menu.connect(func():
		if game.story_mode and game.can_save() and game.bot_mode == "":
			SaveSystem.write("auto", game.save_dict())
		show_menu())
	game.campaign_over.connect(_on_campaign_over)
	game.options_requested.connect(_open_options)


func _on_finished(stats: Dictionary) -> void:
	if stats.has("restart"):
		start_game("", game.story_mode if game else true)
		return
	var best := GameState.record_result(stats)
	if game:
		game.show_end(stats, best)


func _on_campaign_over(ending: Dictionary) -> void:
	# 3B: the ending card has already faded to warm black and been read; the credits follow at once
	await get_tree().create_timer(1.0 if ending.has("ending") else 4.0).timeout
	_open_credits(true)


# ------------------------------------------------------------------ panels

func _panel(title: String, w := 980, h := 760) -> VBoxContainer:
	_free_panel()
	var layer: CanvasLayer = menu
	if layer == null:
		layer = CanvasLayer.new()
		layer.layer = 30
		add_child(layer)
	panel = PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UIStyle.panel_box(0.94))
	panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	panel.offset_left = -w / 2
	panel.offset_right = w / 2
	panel.offset_top = -h / 2
	panel.offset_bottom = h / 2
	layer.add_child(panel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	panel.add_child(v)
	var head := HBoxContainer.new()
	v.add_child(head)
	var t := UIStyle.label(title, 40, UIStyle.AMBER, UIStyle.serif())
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(t)
	var close := UIStyle.focus_follows_hover(UIStyle.button("Back"))
	close.custom_minimum_size = Vector2(140, 44)
	close.pressed.connect(_close_panel)
	head.add_child(close)
	if layer == menu and not menu_items.is_empty():
		_lock_menu(true)                   # G6c: the title column behind the panel takes no input
	close.grab_focus.call_deferred()       # keys and pad work in the panel at once
	return v


func _free_panel() -> void:
	if panel and is_instance_valid(panel):
		panel.queue_free()
	panel = null


func _close_panel() -> void:
	_free_panel()
	# Options opened from the in-game pause menu (item 4): return to it
	if game and is_instance_valid(game) and get_tree().paused and game.ui and game.ui.pause_panel:
		game.ui.pause_panel.visible = true
		game.ui.focus_pause()
	elif not menu_items.is_empty():
		_lock_menu(false)                  # G6c: back on the title, on the item that opened the panel
		_restore_menu_focus()


func _confirm(text: String, yes: Callable) -> void:
	var v := _panel("Are you sure?", 760, 300)
	var l := UIStyle.label(text, 24, UIStyle.INK, UIStyle.serif())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(l)
	var h := HBoxContainer.new()
	v.add_child(h)
	var y := UIStyle.focus_follows_hover(UIStyle.button("Yes"))
	y.pressed.connect(func():
		_close_panel()
		yes.call())
	h.add_child(y)
	var n := UIStyle.focus_follows_hover(UIStyle.button("No"))
	n.pressed.connect(_close_panel)
	h.add_child(n)
	n.grab_focus.call_deferred()           # the safe answer has the focus


func _open_load() -> void:
	var v := _panel("Load game")
	for slot in SaveSystem.SLOTS:
		if slot not in ["auto", "auto_prev"] and not SaveSystem.exists(slot):
			continue                       # item 4: old manual saves are listed only if one exists
		var row := HBoxContainer.new()
		v.add_child(row)
		var label: String = {"auto": "Latest autosave", "auto_prev": "Previous autosave"}.get(slot, "Old save (slot %s)" % slot)
		var b := UIStyle.focus_follows_hover(UIStyle.button(label + "    " + SaveSystem.summary(slot)))
		b.custom_minimum_size = Vector2(820, 56)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		UIStyle.track(b, 20)
		b.disabled = not SaveSystem.exists(slot)
		b.pressed.connect(func():
			_close_panel()
			load_slot(slot))
		row.add_child(b)
		if SaveSystem.exists(slot) and slot not in ["auto", "auto_prev"]:
			var del := UIStyle.focus_follows_hover(UIStyle.button("Delete"))
			del.custom_minimum_size = Vector2(110, 56)
			del.pressed.connect(func(): _confirm("Delete save slot %s?" % slot, func():
				SaveSystem.delete(slot)
				_open_load()))
			row.add_child(del)


## G6a (item 34): the rolling credits (CreditsRoll). After an ending they follow the closing card on warm
## black with the credits music, then return to the title; from the menu they roll over it and close.
func _open_credits(ending := false) -> void:
	if ending:
		_clear()
	var layer := CanvasLayer.new()
	layer.layer = 40
	add_child(layer)
	if ending:
		menu = layer                       # _clear() (show_menu) frees it
	var roll := CreditsRoll.new().setup(ending)
	credits_roll = roll
	layer.add_child(roll)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if not ending:
		_lock_menu(true)
	roll.finished.connect(func():
		credits_roll = null
		if ending:
			show_menu()
		else:
			layer.queue_free()
			_lock_menu(false)              # G6c: back on Credits
			_restore_menu_focus())


func _open_options() -> void:
	var v := _panel("Options", 1100, 860)
	var tabs := TabContainer.new()
	tabs.custom_minimum_size = Vector2(1040, 720)
	tabs.add_theme_font_override("font", UIStyle.serif())
	UIStyle.track(tabs, 20)
	v.add_child(tabs)
	var gfx := _tab(tabs, "Graphics")
	_opt_choice(gfx, "Window mode", "window_mode", [["Windowed", 0], ["Fullscreen", 3], ["Exclusive fullscreen", 4]])
	_opt_choice(gfx, "Resolution (windowed)", "resolution", [["1280×720", "1280x720"], ["1600×900", "1600x900"], ["1920×1080", "1920x1080"], ["2560×1440", "2560x1440"]])
	_opt_choice(gfx, "Quality", "quality", [["Low", 0], ["Medium", 1], ["High", 2]], "Medium targets 60 fps (default). High adds more shadowed lamps and 2x MSAA for quality at 30 fps or more. Applies when the next scene loads.")
	_opt_choice(gfx, "Render resolution", "render_res", [["Auto (1080p-equivalent, upscaled)", 0], ["Native (sharpest, slowest)", 1]], "On high-DPI screens Auto renders 3D at about 1920×1080 and keeps text sharp.")
	_opt_toggle(gfx, "VSync", "vsync")
	_opt_choice(gfx, "Frame-rate limit", "max_fps", [["Unlimited", 0], ["30", 30], ["60", 60], ["120", 120]])
	_opt_slider(gfx, "Field of view", "fov", 60.0, 90.0, 1.0)
	_opt_slider(gfx, "Brightness", "brightness", 0.6, 1.6, 0.05)
	var au := _tab(tabs, "Audio")
	for k in [["Master", "vol_master"], ["Music", "vol_music"], ["Sound effects", "vol_sfx"], ["Dialogue & radio", "vol_dialogue"], ["Ambience", "vol_ambient"]]:
		_opt_slider(au, k[0], k[1], 0.0, 1.0, 0.05)
	var ct := _tab(tabs, "Controls")
	_opt_slider(ct, "Mouse sensitivity", "mouse_sens", 0.3, 2.5, 0.05)
	_opt_toggle(ct, "Invert Y axis", "invert_y")
	_opt_slider(ct, "Gamepad look sensitivity", "stick_sens", 0.3, 2.5, 0.05)
	_opt_toggle(ct, "Head bob while walking", "head_bob")
	_opt_toggle(ct, "Hold E to crank the generator (off: press once to crank)", "hold_to_crank")
	ct.add_child(UIStyle.label("Controls", 22, UIStyle.AMBER, UIStyle.serif()))
	for b in [["", "Keyboard and mouse", "Gamepad"], ["Walk", "W A S D / arrows", "Left stick"], ["Look", "Mouse", "Right stick"],
			["Use", "E · left click", "A"], ["Continue dialogue", "Space", "RT"],
			["Choose a reply", "1 – 4 (click in a device view)", "D-pad + A"],
			["Walk faster", "Shift", "Left stick click"], ["Station log", "L", "Y"], ["Current duty (hold: latest hint)", "J", "Right stick click"], ["Hand compass", "G", "—"], ["Binoculars", "B", "—"], ["Step back", "Esc · right click", "B"],
			["Pause", "Esc", "Start"], ["Selector knobs", "Wheel · right click", "LB / RB"],
			["Turn handwheel (console)", "A / D", "Left stick · D-pad"], ["Device views: point and click", "Mouse", "Right stick + A"],
			["Radio: next vessel / send", "Tab / 1 – 6", "RB / point + A"], ["Document transcription", "T", "X"], ["Fullscreen", "F11", "—"]]:
		var row := HBoxContainer.new()
		var a := UIStyle.label(b[0], 19)
		a.custom_minimum_size = Vector2(380, 0)
		row.add_child(a)
		var kb := UIStyle.label(b[1], 19, UIStyle.DIM if b[0] != "" else UIStyle.AMBER)
		kb.custom_minimum_size = Vector2(330, 0)
		row.add_child(kb)
		row.add_child(UIStyle.label(b[2], 19, UIStyle.DIM if b[0] != "" else UIStyle.AMBER))
		ct.add_child(row)
	var ac := _tab(tabs, "Accessibility")
	_opt_toggle(ac, "Show ship radio chatter subtitles (story dialogue always shows)", "subtitles")
	_opt_slider(ac, "Text size (dialogue and interface)", "subtitle_size", 0.8, 1.5, 0.05)
	_opt_slider(ac, "Text speed (characters / s)", "text_speed", 15.0, 120.0, 1.0)
	_opt_toggle(ac, "Reduce flashing (lightning)", "reduce_flashing")
	_opt_toggle(ac, "Reduce motion (title menu animation and glow)", "reduce_motion")
	_opt_choice(ac, "Guidance", "guidance", [["Minimal: the room and the logbook", 0],
		["Standard: a short duty line, hints when stuck", 1], ["Full: the duty and its steps always shown", 2]],
		"J (gamepad: right stick click) shows the current duty at any time; hold it for the latest hint.")
	_opt_slider(ac, "Duty line time on screen (s)", "duty_hold_s", 3.0, 12.0, 0.5)


func _tab(tabs: TabContainer, name_: String) -> VBoxContainer:
	var s := ScrollContainer.new()
	s.name = name_
	tabs.add_child(s)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.add_child(v)
	return v


func _row(parent: Control, label: String) -> HBoxContainer:
	var h := HBoxContainer.new()
	var l := UIStyle.label(label, 20)
	l.custom_minimum_size = Vector2(460, 0)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	h.add_child(l)
	parent.add_child(h)
	return h


func _opt_choice(parent: Control, label: String, key: String, items: Array, note := "") -> void:
	var h := _row(parent, label)
	var ob := OptionButton.new()
	ob.custom_minimum_size = Vector2(320, 40)
	for i in items.size():
		ob.add_item(items[i][0], i)
		if items[i][1] == Settings.v[key]:
			ob.select(i)
	ob.item_selected.connect(func(i): Settings.set_value(key, items[i][1]))
	h.add_child(ob)
	if note != "":
		parent.add_child(UIStyle.label("      " + note, 15, UIStyle.DIM))


func _opt_toggle(parent: Control, label: String, key: String) -> void:
	var h := _row(parent, label)
	var cb := CheckButton.new()
	cb.button_pressed = Settings.v[key]
	cb.toggled.connect(func(on): Settings.set_value(key, on))
	h.add_child(cb)


func _opt_slider(parent: Control, label: String, key: String, lo: float, hi: float, step: float) -> void:
	var h := _row(parent, label)
	var s := HSlider.new()
	s.min_value = lo
	s.max_value = hi
	s.step = step
	s.value = float(Settings.v[key])
	s.custom_minimum_size = Vector2(360, 30)
	var val := UIStyle.label("%.2f" % s.value, 18, UIStyle.DIM)
	s.value_changed.connect(func(x):
		val.text = "%.2f" % x
		Settings.set_value(key, x))
	h.add_child(s)
	h.add_child(val)
