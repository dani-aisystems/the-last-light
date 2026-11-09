extends CanvasLayer
## Story presentation layer: dialogue UI, document viewer, objective line, hints, chapter cards,
## time-skip fades. Owned by game_fp in story mode; talks to StoryDirector via signals.

signal document_closed(doc_id: String)
signal log_card_shown(entry: Dictionary)   # G2b: a log line starts being written on screen (game_fp: pen sound)

const CARD_ON_BLACK_S := 1.8          # the clock or chapter card is fully up on black at least this long (item 21)
var director: StoryDirector
var dialogue: Control
var objective: Label
var hint: Label
var card: Control
var card_title: Label
var card_sub: Label
var fade: ColorRect
var doc_root: Control
var doc_tex: TextureRect
var doc_text: RichTextLabel
var doc_title: Label
var docs := {}
var caption: Label                       # 3B: sound captions outside conversations ("[Footsteps on the stair]")
var thought: Label                       # brief item 16: Callum's short, non-blocking thought when checking a device
var duty_hud: DutyHUD                     # G2b layer A: the duty line top-left (replaced the item 20 panel)
var _last_hint := ""                     # G2b: the last story hint, for the J / R3 recall
var _queued_thought := ""                # G2b: a thought held back while dialogue was up
## G2b layer C: the logbook (the log page with tonight's written rows, the pencil Duties page) and the
## completion slip that appears top-right as Callum writes a row.
var log_pages: LogbookPages
var log_card: Control
var _card_bg: TextureRect
var _card_clip: Control
var _card_ink: TextureRect
var _card_queue: Array = []
var _card_tw: Tween
const LOG_DOCS := ["log_1971", "duties"]
var _thought_tw: Tween
var _caption_tw: Tween
## 3B ending card (§15.5): warm black, the ending's title, the epilogue lines one at a time.
var ending_root: Control
var ending_bg: ColorRect
var ending_title: Label
var ending_box: VBoxContainer
var _ending_open := false
var _end_wait := 0.0
var _end_skip := false
var _end_guard := 0
var _hint_t := 0.0
var _hint_next := ""                        # item 26: the hint waiting behind the current one
const HINT_MIN_S := 2.5
var _doc_open := ""
var _transcript := false
## Inspection viewer (cabin pass): zoom and pan; it closes only on interact / back / pause / right click,
## never on a stray left click or the wheel (a click used to skip the 1954 clipping).
const ZOOM_MAX := 4.0
const OPEN_GUARD_FRAMES := 3            # the press that opened the document must not also close it
var doc_view: Control                   # clipping frame the document is drawn in
var _zoom := 1.0
var _pan := Vector2.ZERO
var _dragging := false
var _open_frame := 0
## Documents that are not story PNGs. The chart is the desk chart's own texture (keeper's pencil marks
## included), so the inspection shows exactly what lies on the desk; the physical chart never moves.
const BUILTIN_DOCS := {
	"chart": {"title": "Chart: North Point and approaches", "tex": "res://assets/models/watch_room_T_LL_Chart.png",
		"text": "NORTH POINT and approaches. Soundings in metres.\n\nLeading lines: West Gut, North Sound (000°), East Gut (046°).\n\nIn pencil: clearing bearings, clear 336° and clear 022°. A fix marked 13/11 2100. An older line, half rubbed out.\n\nKEEPER'S TERMS (brief item 27)\nBearing: the direction of a ship from the light, in degrees clockwise from north (000° due north, 046° north-east, 314° north-west).\nHeading: the direction a ship is pointing.\nLeading line: a safe track into a channel. A ship on the line, heading in, is clear of the rocks.\nPort: the ship's own left. Starboard: her right. \"Turn port\" swings her bow to her left.\nGut: a narrow channel between rocks (West Gut, East Gut).\nLee: the sheltered side, out of the wind.\nAbeam: straight out to one side of a ship.\nOver: \"my turn is done, go ahead\". Out: \"end of the call\"."},
}


func _ready() -> void:
	layer = 15
	process_mode = Node.PROCESS_MODE_ALWAYS
	var f := FileAccess.get_file_as_string("res://assets/docs/docs.json")
	if f != "":
		docs = JSON.parse_string(f)
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	# G2b (Daniel 2026-11-06): the duty HUD, top-left, replaces the item 9/20 checklist panel. objective
	# and hint keep their names for the rest of the game: they are the HUD's duty line and hint row.
	duty_hud = DutyHUD.new()
	root.add_child(duty_hud)
	log_pages = LogbookPages.new()
	add_child(log_pages)
	log_card = Control.new()
	log_card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	log_card.modulate.a = 0.0
	log_card.visible = false
	root.add_child(log_card)
	_card_bg = TextureRect.new()
	_card_bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_card_bg.stretch_mode = TextureRect.STRETCH_SCALE
	_card_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	log_card.add_child(_card_bg)
	_card_clip = Control.new()
	_card_clip.clip_contents = true
	_card_clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	log_card.add_child(_card_clip)
	_card_ink = TextureRect.new()
	_card_ink.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_card_ink.stretch_mode = TextureRect.STRETCH_SCALE
	_card_ink.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_card_clip.add_child(_card_ink)
	objective = duty_hud.line
	hint = duty_hud.hint
	dialogue = preload("res://scripts/ui/dialogue_ui.gd").new()
	root.add_child(dialogue)
	# chapter card
	card = Control.new()
	card.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.modulate.a = 0.0
	root.add_child(card)
	var cv := VBoxContainer.new()
	cv.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	cv.offset_left = -700
	cv.offset_right = 700
	# upper-middle (~37 % of the height): clear of the interaction prompt under the crosshair
	cv.offset_top = -300
	cv.offset_bottom = -140
	cv.alignment = BoxContainer.ALIGNMENT_CENTER
	card.add_child(cv)
	card_title = UIStyle.label("", 64, UIStyle.INK, UIStyle.serif())
	card_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	cv.add_child(card_title)
	card_sub = UIStyle.label("", 22, UIStyle.AMBER, UIStyle.serif())
	card_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	cv.add_child(card_sub)
	# document viewer: its own top canvas layer, above the HUD (radio chatter and notices drew over it, cp2)
	var doc_layer := CanvasLayer.new()
	doc_layer.layer = 30
	add_child(doc_layer)
	doc_root = Control.new()
	doc_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	doc_root.visible = false
	doc_layer.add_child(doc_root)
	var shade := ColorRect.new()
	shade.color = Color(0, 0, 0, 0.82)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	doc_root.add_child(shade)
	doc_view = Control.new()
	doc_view.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	doc_view.offset_left = 120
	doc_view.offset_right = -120
	doc_view.offset_top = 80
	doc_view.offset_bottom = -110
	doc_view.clip_contents = true
	doc_view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	doc_root.add_child(doc_view)
	doc_tex = TextureRect.new()
	doc_tex.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	doc_tex.stretch_mode = TextureRect.STRETCH_SCALE        # _layout_doc keeps the aspect ratio
	doc_tex.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	doc_tex.mouse_filter = Control.MOUSE_FILTER_IGNORE
	doc_view.add_child(doc_tex)
	doc_text = RichTextLabel.new()
	doc_text.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	doc_text.offset_left = 260
	doc_text.offset_right = -260
	doc_text.offset_top = 140
	doc_text.offset_bottom = -140
	doc_text.add_theme_font_override("normal_font", UIStyle.serif())
	doc_text.add_theme_font_override("italics_font", UIStyle.serif_italic())
	UIStyle.track(doc_text, 28)
	doc_text.visible = false
	doc_root.add_child(doc_text)
	doc_title = UIStyle.label("", 22, UIStyle.AMBER, UIStyle.serif())
	doc_title.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	doc_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	doc_title.offset_top = -90
	doc_title.offset_bottom = -40
	doc_root.add_child(doc_title)
	caption = UIStyle.label("", 20, UIStyle.INK, UIStyle.sans())     # 3B checkpoint: 18 px DIM was lost on the dark room
	caption.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	caption.offset_left = -560
	caption.offset_right = 560
	caption.offset_top = -330
	caption.offset_bottom = -296
	caption.grow_vertical = Control.GROW_DIRECTION_BEGIN
	caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	caption.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	caption.modulate.a = 0.0
	root.add_child(caption)
	thought = UIStyle.label("", 22, UIStyle.INK, UIStyle.serif_italic())
	thought.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	thought.offset_left = -620
	thought.offset_right = 620
	thought.offset_top = -170
	thought.offset_bottom = -120
	thought.grow_vertical = Control.GROW_DIRECTION_BEGIN
	thought.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	thought.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	thought.modulate.a = 0.0
	root.add_child(thought)
	fade = ColorRect.new()
	fade.color = Color(0, 0, 0, 0)
	fade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(fade)
	# The clock and chapter card draws ABOVE the black (brief item 21): it used to be added before the fade,
	# so at full black the time was hidden and was only ever seen half-dimmed while the fade moved.
	root.move_child(card, -1)
	_build_ending()


func bind(d: StoryDirector) -> void:
	director = d
	d.line_shown.connect(dialogue.show_line)
	d.choices_shown.connect(dialogue.show_choices)
	d.dialogue_closed.connect(dialogue.close)
	dialogue.advance_requested.connect(d.advance_line)
	dialogue.choice_made.connect(d.choose)
	d.objective_changed.connect(set_objective)
	d.objective_progress.connect(set_progress)
	d.duty_logged.connect(show_log_entry)
	dialogue.hold_fn = is_screen_held
	d.chapter_started.connect(show_chapter)
	d.transition_requested.connect(_on_transition)


## G2b: the director's duty view (or a legacy objective: a string, or {title, steps}) goes to the duty HUD.
## Text keeps the {interact} {move} ... tokens; the HUD resolves them for the current device.
func set_objective(o) -> void:
	hint.text = ""
	_hint_next = ""
	if o is Dictionary:
		duty_hud.set_view(o)
	elif String(o) == "":
		duty_hud.set_view({})
	else:
		duty_hud.set_view({"title": String(o), "caption": "", "steps": []})


func set_progress(done: Array) -> void:
	duty_hud.set_done(done)


func is_step_done(i: int) -> bool:
	return duty_hud.is_step_done(i)


## A device view is open (radio, console...): the duty line steps aside unless Full or recalled.
func set_compact(on: bool) -> void:
	duty_hud.compact = on


## G2b layer C: Callum writes a log row. A paper slip top-right (below the notices, clear of the radio
## panel and the subtitles); its ink appears left to right as if written, then it fades. One at a time.
func show_log_entry(entry: Dictionary) -> void:
	_card_queue.append(entry)


func _tick_log_card() -> void:
	var busy: bool = _card_tw != null and _card_tw.is_running()
	log_card.visible = busy and not is_document_open()          # G4a: never over (or through) a document
	if _card_queue.is_empty() or busy or is_screen_held() or is_document_open():
		return
	var e: Dictionary = _card_queue.pop_front()
	var bg: Texture2D = load(LogbookPages.DIR + "card_%s.png" % e["id"])
	var ink: Texture2D = load(LogbookPages.DIR + "card_ink_%s.png" % e["id"])
	if bg == null or ink == null:
		return
	var vp := log_card.get_viewport_rect().size
	var s := minf(1.0, vp.x * 0.34 / float(bg.get_width())) * minf(1.0 + (UIStyle.text_scale - 1.0) * 0.5, 1.25)
	var sz := Vector2(bg.get_width(), bg.get_height()) * s
	log_card.size = sz
	log_card.position = Vector2(vp.x * (1.0 - DutyHUD.MARGIN) - sz.x, vp.y * DutyHUD.TOP)
	_card_bg.texture = bg
	_card_bg.size = sz
	_card_ink.texture = ink
	_card_ink.size = sz
	_card_clip.size = Vector2(0, sz.y)
	log_card.visible = true
	log_card.set_meta("entry", e["id"])
	log_card_shown.emit(e)
	_card_tw = create_tween()
	_card_tw.tween_property(log_card, "modulate:a", 1.0, 0.35)
	_card_tw.tween_property(_card_clip, "size:x", sz.x, 1.5)
	_card_tw.tween_interval(4.0)
	_card_tw.tween_property(log_card, "modulate:a", 0.0, 1.0)
	_card_tw.tween_callback(func(): log_card.visible = false)


## G2b escalation, by the Guidance option: 0 a new current step (Full shows its hint at once; the others
## keep it for J / R3), 1 Callum's nudge as a thought (all modes), 2 the hint with the duty line
## (Standard and Full; Minimal keeps it for J / R3).
func duty_nudge(level: int, nudge: String, hint_text: String) -> void:
	var g := DutyHUD.guidance()
	if hint_text != "":
		_last_hint = hint_text
	match level:
		0:
			if g == DutyHUD.GUIDE_FULL and hint_text != "":
				show_hint(hint_text, true)
		1:
			if nudge != "" and show_thought(nudge) and director:
				director.log_thought(nudge)
			elif nudge != "":
				_queued_thought = nudge
		_:
			if g >= DutyHUD.GUIDE_STANDARD and hint_text != "":
				show_hint(hint_text, true)
				duty_hud.announce()


## G2b: J / R3. Tap: the current duty for a few seconds. Hold: the latest hint as well.
func recall_duty(with_hint := false) -> void:
	duty_hud.recall()
	if with_hint and _last_hint != "" and hint.text != _last_hint:
		show_hint(_last_hint)
	elif with_hint and _last_hint != "":
		_hint_t = 14.0


## True while the screen is (partly) black or the ending card is up: dialogue must not type out unseen.
func is_screen_held() -> bool:
	return fade.color.a > 0.02 or _ending_open


## Item 26: a hint stays up at least HINT_MIN_S before a different one replaces it; one more can queue.
func show_hint(t: String, remember := false) -> void:
	if remember:
		_last_hint = t                     # G2b: a story hint the player can call back with J / R3
	var txt := InputSetup.resolve(t)      # {interact} {move} ... -> keyboard or pad glyphs (Stage 2C)
	if _hint_t > 0.0 and hint.text != "" and hint.text != txt and 14.0 - _hint_t < HINT_MIN_S:
		_hint_next = txt
		return
	hint.text = txt
	_hint_t = 14.0


## The chapter card (3B; order fixed for brief item 21). The chapter has already switched under black.
## Order: black -> the card (title, date and time) fades in ON the black and holds, readable -> the scene
## fades in under it -> the story is released as the card fades out, so the first line never types under it.
## At a new game or a load the presenter's black is set at once (the HUD's own start-up fade is black too).
func show_chapter(n: int, title: String, sub: String) -> void:
	card_title.text = "%s · %s" % [["", "I", "II", "III", "IV", "V", "VI"][clampi(n, 0, 6)], title]
	card_sub.text = sub
	fade.color.a = 1.0
	var tw := create_tween()
	tw.tween_property(card, "modulate:a", 1.0, 1.0)
	tw.tween_interval(CARD_ON_BLACK_S)
	tw.tween_property(fade, "color:a", 0.0, 1.0)
	tw.tween_interval(0.8)
	tw.tween_callback(_release)
	tw.tween_property(card, "modulate:a", 0.0, 1.4)


func _release() -> void:
	if director:
		director.transition_done()


func _midpoint() -> void:
	if director:
		director.transition_midpoint()


## The director asks for a transition; it holds the story until we call back.
func _on_transition(kind: String, args: Array) -> void:
	match kind:
		"chapter":
			var tw := create_tween()
			tw.tween_property(fade, "color:a", 1.0, 0.6)
			tw.tween_interval(0.25)
			tw.tween_callback(_midpoint)     # the chapter switches under black, then show_chapter fades in
		"timeskip":
			timeskip(String(args[1]) if args.size() > 1 else "")
		"ending":
			pass                             # show_ending (story event) drives it and releases at the end


## A time skip (order fixed for brief item 21): the scene fades to black, the new clock time appears on
## the black and holds (the world changes under it at the midpoint), the time fades, then the scene returns
## and the story is released.
func timeskip(clock_text: String) -> void:
	card_title.text = clock_text
	card_sub.text = ""
	var tw := create_tween()
	tw.tween_property(fade, "color:a", 1.0, 0.9)
	tw.tween_property(card, "modulate:a", 1.0, 0.5)
	tw.tween_callback(_midpoint)
	tw.tween_interval(CARD_ON_BLACK_S)
	tw.tween_property(card, "modulate:a", 0.0, 0.5)
	tw.tween_property(fade, "color:a", 0.0, 1.1)
	tw.tween_callback(_release)


## Item 16: a device check's thought. It never waits for a key (it fades by itself) and is skipped while a
## story line is on screen, so it can't talk over the story. Returns true if it was shown.
## G2b: a thought that must not be lost (a failed crank, a duty nudge) waits for the dialogue to finish.
func queue_thought(t: String) -> void:
	if not show_thought(t):
		_queued_thought = t


func show_thought(t: String) -> bool:
	if t == "" or dialogue.is_active() or _ending_open:
		return false
	thought.text = t
	if _thought_tw:
		_thought_tw.kill()
	_thought_tw = create_tween()
	_thought_tw.tween_property(thought, "modulate:a", 0.95, 0.25)
	_thought_tw.tween_interval(2.6 + t.length() * 0.035)
	_thought_tw.tween_property(thought, "modulate:a", 0.0, 0.6)
	return true


## A sound caption outside a conversation: small capitals, low centre, about three seconds.
func show_caption(t: String) -> void:
	caption.text = t.strip_edges().trim_prefix("[").trim_suffix("]").strip_edges().to_upper()
	if _caption_tw:
		_caption_tw.kill()
	_caption_tw = create_tween()
	_caption_tw.tween_property(caption, "modulate:a", 0.9, 0.3)
	_caption_tw.tween_interval(3.2)
	_caption_tw.tween_property(caption, "modulate:a", 0.0, 0.6)


func _build_ending() -> void:
	var lay := CanvasLayer.new()
	lay.layer = 25                           # over the HUD and dialogue, under the document viewer
	add_child(lay)
	ending_root = Control.new()
	ending_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ending_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ending_root.visible = false
	lay.add_child(ending_root)
	ending_bg = ColorRect.new()
	ending_bg.color = Color(0.035, 0.026, 0.02, 0.0)          # warm black
	ending_bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ending_root.add_child(ending_bg)
	var col := VBoxContainer.new()
	col.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	col.offset_left = -560
	col.offset_right = 560
	col.offset_top = -330
	col.offset_bottom = 330
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	col.add_theme_constant_override("separation", 26)
	ending_root.add_child(col)
	ending_title = UIStyle.label("", 46, UIStyle.INK, UIStyle.serif())
	ending_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ending_title.modulate.a = 0.0
	col.add_child(ending_title)
	ending_box = VBoxContainer.new()
	ending_box.add_theme_constant_override("separation", 16)
	col.add_child(ending_box)


## "Correction" -> "C O R R E C T I O N" (words kept apart by a wider gap).
static func spaced_caps(t: String) -> String:
	var out := ""
	for i in t.length():
		var ch := t[i].to_upper()
		out += ("   " if ch == " " else ch + (" " if i < t.length() - 1 and t[i + 1] != " " else ""))
	return out


func is_ending_open() -> bool:
	return _ending_open


## The ending card (§15.5): a slow fade from the dawn view to warm black, the title in spaced capitals,
## then each epilogue line in italic serif, one at a time (input or about four seconds each). The last two
## lines (the place and date, and "The light was kept.") are set apart. Releases the story at the end.
func show_ending(_id: String, title: String, lines: Array) -> void:
	_ending_open = true
	for c in ending_box.get_children():
		c.queue_free()
	ending_title.text = spaced_caps(title)
	ending_title.modulate.a = 0.0
	ending_root.visible = true
	dialogue.visible = false
	var tw := create_tween()
	tw.tween_property(ending_bg, "color:a", 1.0, 2.4)
	await tw.finished
	tw = create_tween()
	tw.tween_property(ending_title, "modulate:a", 1.0, 1.4)
	await tw.finished
	await _ending_pause(1.2)
	for i in lines.size():
		var l := _ending_line(lines, i)
		l.modulate.a = 0.0
		ending_box.add_child(l)
		var t2 := create_tween()
		t2.tween_property(l, "modulate:a", 1.0 if i < lines.size() - 2 else 0.9, 1.0)
		await _ending_pause(maxf(4.0, String(lines[i]).length() * 0.05))
	await _ending_pause(2.5)
	_ending_open = false
	_release()


## Captures (3B): the card as it looks once every line is up, no animation.
func show_ending_static(title: String, lines: Array) -> void:
	for c in ending_box.get_children():
		c.queue_free()
	ending_title.text = spaced_caps(title)
	ending_title.modulate.a = 1.0
	ending_bg.color.a = 1.0
	ending_root.visible = true
	dialogue.visible = false
	for i in lines.size():
		var l := _ending_line(lines, i)
		l.modulate.a = 1.0 if i < lines.size() - 2 else 0.9
		ending_box.add_child(l)


## One epilogue line: italic serif; the last two (place and date, "The light was kept.") smaller, in amber.
func _ending_line(lines: Array, i: int) -> Label:
	var tail := i >= lines.size() - 2
	var l := UIStyle.label(String(lines[i]), 24 if not tail else 21, UIStyle.AMBER if tail else UIStyle.INK,
		UIStyle.serif_italic())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.custom_minimum_size = Vector2(1080, 0)
	return l


func hide_ending() -> void:
	ending_root.visible = false
	ending_bg.color.a = 0.0
	dialogue.visible = true
	for c in ending_box.get_children():
		c.queue_free()


func _ending_pause(secs: float) -> void:
	_end_wait = secs
	_end_skip = false
	_end_guard = Engine.get_process_frames()
	while _end_wait > 0.0 and not _end_skip:
		await get_tree().process_frame
		if not get_tree().paused:
			_end_wait -= get_process_delta_time()


func fade_to(a: float, secs: float) -> Tween:
	var tw := create_tween()
	tw.tween_property(fade, "color:a", a, secs)
	return tw


func doc_info(id: String) -> Dictionary:
	return docs.get(id, BUILTIN_DOCS.get(id, {}))


## Open a document or the chart for inspection. The mouse policy is game_fp's (it re-applies it after
## opening and closing); this layer never sets the mouse mode.
func open_document(id: String) -> void:
	var d := doc_info(id)
	var composed := id in LOG_DOCS and director != null and not log_pages.manifest.is_empty()
	if d.is_empty() and not composed:
		return
	_doc_open = id
	if composed:                                   # G2b: tonight's log as written so far / the pencil page
		doc_text.text = log_pages.build_log(director.state.log_written, director.station_log) if id == "log_1971" \
			else log_pages.build_duties(director)
		doc_tex.texture = log_pages.get_texture()
	else:
		doc_tex.texture = load(String(d.get("tex", "res://assets/docs/%s.png" % id)))
		doc_text.text = d["text"]
	_transcript = false
	doc_text.visible = false
	doc_tex.visible = true
	doc_tex.modulate.a = 1.0
	_zoom = 1.0
	_pan = Vector2.ZERO
	_dragging = false
	_open_frame = Engine.get_process_frames()
	_update_doc_title()
	doc_root.visible = true
	dialogue.visible = false                     # its subtitles bled through the shade under the legend
	_layout_doc.call_deferred()


func _update_doc_title() -> void:
	var d := doc_info(_doc_open)
	if _doc_open == "duties":
		d = {"title": "Tonight · pencil, at the back of the log"}
	var pages := "  ·  %s page" % ("A / D" if not InputSetup.pad_active else "Left stick") if _doc_open in LOG_DOCS else ""
	var zoom_keys := "%s zoom · drag to move" % InputSetup.key("turn") if not InputSetup.pad_active \
		else "%s zoom · %s move" % [InputSetup.key("turn"), "[Right stick]"]
	doc_title.text = "%s        %s  ·  %s transcription%s  ·  %s / %s close" % [d.get("title", ""), zoom_keys,
		InputSetup.key("transcript"), pages, InputSetup.key("interact"), InputSetup.key("back")]


func is_document_open() -> bool:
	return doc_root.visible


func close_document() -> void:
	if not doc_root.visible:
		return
	doc_root.visible = false
	dialogue.visible = true
	_dragging = false
	var id := _doc_open
	_doc_open = ""
	if id in LOG_DOCS:
		log_pages.stop()
		id = "log_1971"                            # the Duties page is the back of the same book
	document_closed.emit(id)


## Fit the texture inside the frame at zoom 1 (aspect kept), scale it by the zoom, and keep the pan
## inside the image so it can never be dragged off screen.
func _layout_doc() -> void:
	if doc_tex.texture == null:
		return
	var frame := doc_view.size
	var ts := doc_tex.texture.get_size()
	var fit := minf(frame.x / ts.x, frame.y / ts.y)
	var sz := ts * fit * _zoom
	var slack := ((sz - frame) * 0.5).max(Vector2.ZERO)
	_pan = _pan.clamp(-slack, slack)
	doc_tex.size = sz
	doc_tex.position = (frame - sz) * 0.5 + _pan


## Zoom by `factor` keeping the point under `at` (frame px) still.
func _zoom_at(factor: float, at: Vector2) -> void:
	var z := clampf(_zoom * factor, 1.0, ZOOM_MAX)
	if is_equal_approx(z, _zoom):
		return
	var centre := doc_view.size * 0.5 + _pan
	_pan += (at - centre) * (1.0 - z / _zoom)
	_zoom = z
	_layout_doc()


## _input, not _unhandled_input: the viewer owns every event while it is open (its full-screen shade is a
## GUI control that swallowed mouse buttons before _unhandled_input, so right click never closed it, R8).
func _input(event: InputEvent) -> void:
	if _ending_open:
		var press: bool = event.is_action_pressed("interact") or (event is InputEventKey and event.pressed and not event.echo \
			and event.keycode == KEY_SPACE) or (event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT)
		if press and Engine.get_process_frames() - _end_guard > 20:
			_end_skip = true
		if press:
			get_viewport().set_input_as_handled()
		return
	if not doc_root.visible:
		return
	get_viewport().set_input_as_handled()          # nothing under the viewer reacts while reading
	if _doc_open in LOG_DOCS and _zoom <= 1.01 and (event.is_action_pressed("move_left") or event.is_action_pressed("move_right")
			or (event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_TAB)):
		open_document("duties" if _doc_open == "log_1971" else "log_1971")   # G2b: turn to the other page
		return
	if event.is_action_pressed("transcript"):    # T, or pad X (Stage 2C)
		_transcript = not _transcript
		doc_text.visible = _transcript
		doc_tex.modulate.a = 0.15 if _transcript else 1.0
		return
	if event is InputEventMouseButton:
		var local: Vector2 = event.position - doc_view.get_global_rect().position
		if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			_zoom_at(1.15, local)
			return
		if event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			_zoom_at(1.0 / 1.15, local)
			return
		if event.button_index == MOUSE_BUTTON_LEFT:
			_dragging = event.pressed               # drag to move; a left click never closes
			return
	if event is InputEventMouseMotion and _dragging:
		_pan += event.relative
		_layout_doc()
		return
	if event.is_action_pressed("turn_next") or event.is_action_pressed("turn_prev"):
		_zoom_at(1.25 if event.is_action_pressed("turn_next") else 0.8, doc_view.size * 0.5)
		return
	var close: bool = event.is_action_pressed("interact") or event.is_action_pressed("pause") or event.is_action_pressed("back") \
		or (event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_RIGHT)
	if close and Engine.get_process_frames() - _open_frame >= OPEN_GUARD_FRAMES:
		close_document()


func _process(delta: float) -> void:
	if _hint_t > 0.0:
		_hint_t -= delta
		hint.modulate.a = clampf(_hint_t, 0.0, 1.0)
	duty_hud.tick(delta, is_screen_held() or is_document_open())
	duty_hud.visible = not is_document_open()                  # G4a: the 82 % shade let the plate read through
	_tick_log_card()
	if _queued_thought != "" and not dialogue.is_active() and not is_screen_held():
		var qt := _queued_thought
		_queued_thought = ""
		if show_thought(qt) and director:
			director.log_thought(qt)
	if _hint_next != "" and 14.0 - _hint_t >= HINT_MIN_S:
		hint.text = _hint_next
		_hint_next = ""
		_hint_t = 14.0
	if doc_root.visible and _zoom > 1.0:            # keys / sticks move around a zoomed document
		var mv := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
		var st := InputSetup.stick("look_left", "look_right", "look_up", "look_down")
		var d := (mv + st) * 700.0 * delta
		if d != Vector2.ZERO:
			_pan -= d
			_layout_doc()
