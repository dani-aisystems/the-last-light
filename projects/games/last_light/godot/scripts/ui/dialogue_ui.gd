extends Control
## Cinematic dialogue presentation for THE LAST LIGHT.
##  radio   : compact panel lower-left, identity card (call sign / vessel / station), signal meter,
##            typewriter text with punctuation pauses, squelch on each line. Choices only unlock
##            at the radio (the keeper has to pick up the handset).
##  person  : low centred subtitles, speaker name, nothing covering the scene (the door scene).
##  thought : italic low subtitles, no name (Callum's mind; a genuine italic face since Stage 3A).
##  sound   : a caption for a sound the player must know about ("[ Three slow knocks ]"), small caps.
## Stage 3A: who is speaking comes resolved from Speakers (via DialogueRunner.present): the name, the
## identity line and the look. A hidden identity (Ross before his name is spoken) never reaches this layer.
## The line is laid out ONCE and revealed with visible_characters (after shaping), so words never jump
## to the next line while typing and the panel doesn't grow as it types.
## Input (brief items 7 and 25, 2026-11-06): responsibilities are separate.
##   E (interact) is NEVER read here: it always reaches the player, so devices work while a line shows.
##   Audit D1 (2026-11-16, DECISIONS Q15): no line can be finished early or skipped. EVERY line (radio,
##   in-room, thought, sound) advances by itself after its reading time (line_read_s), counted only while
##   nothing holds the screen (pause, a document, a fade). Slower readers lengthen it with Options >
##   Reading time; nobody can shorten it below the base. (Before: Space / RT finished and advanced lines,
##   and radio lines waited for it, which stalled the story and let a tap skip a line unread.)
##   Replies: number keys 1-4 only (physical keys); a click in a device view; the pad d-pad + A. The wheel,
##   E, W/S, the arrows and Space never pick a reply, and nothing is picked in its first CHOICE_GUARD_S.
## This layer never touches the mouse mode (game_fp owns it). Radio replies show only in the radio view.

signal advance_requested
signal choice_made(index: int)
signal blip(kind: String)                  # audio hooks: "char", "squelch", "open", "close"


var mode := "radio"                         # the conversation's mode (radio replies are gated on it)
var line_look := "radio"                        # how the current line is drawn (radio / person / thought)
var speed_cps := 42.0                       # Settings: typewriter speed
var text_scale := 1.0                       # Settings: subtitle size
var at_radio_fn: Callable                   # returns true when the player is at the handset
var mouse_restore_fn: Callable              # game_fp.refresh_mouse: re-applies the single mouse policy
var in_view_fn: Callable                    # true while the player is in a device view (the pointer is free)
var doc_open_fn: Callable                   # true while a document / the chart is being read: no dialogue input
var hold_fn: Callable                       # true while the screen is faded / a transition runs: the typewriter waits
var choice_hint: Label                      # "1-4 or the wheel, then E" (one-time tip, Settings "replies")
var radio_panel: PanelContainer
var card: Control
var r_name: Label
var r_ident: Label                          # identity line ("STORNOWAY COASTGUARD · HM Coastguard ...") at readable size
var r_text: RichTextLabel
var r_hint: Label
var sub_box: VBoxContainer
var s_name: Label
var s_text: RichTextLabel
var choice_box: VBoxContainer
var _full := ""
var _shown := 0.0
var _speaker := ""
var _item := {}                             # the resolved line (name, call, sub, art, look)
var _bb := ""                               # the whole line as BBCode, set once per line
var _pause := 0.0
var _done_t := 0.0
var _choices: Array = []
var _active := false
var _t := 0.0
var _choice_age := 0.0                      # seconds since the replies appeared (CHOICE_GUARD_S)
var _auto_t := 0.0                          # R1: unheld seconds this line has been on screen
var _advance_sent := false                  # R1: one advance per line (a wait after it must not be skipped)
var auto_advance := true                    # tests only: false freezes every line (proof runs)
var reading_mul := 1.0                      # D1: Settings "reading_time" (0.75 to 3)
var _read_s := 0.0                          # D1: this line's reading time
var _prev_speaker := ""                     # D1: the previous line's speaker in this conversation
var _source := ""                           # D3: the whole message as written
var _pages: Array = [""]                    # D3: the message in pages of MAX_LINES lines or fewer
var _page := 0
const MAX_LINES := 3                        # D3: no message shows more than three lines
const RADIO_W := 820.0                      # the radio panel's width (offsets below)
const RADIO_SEP := 18.0                     # card | text gap
const SUB_W := 1280.0                       # the subtitle column
const WRAP_MARGIN := 3.0                    # measured fit is this much narrower than the label

const CHOICE_GUARD_S := 0.4                 # replies ignore input this long after they appear
const AUTO_BASE_S := 1.0                    # R1: reading time = base + per character, clamped
const AUTO_PER_CHAR_S := 0.06
const AUTO_MIN_S := 2.8
const AUTO_MAX_S := 12.0                    # D1: was 9 (radio lines now advance by themselves too)
const AUTO_AFTER_SHOWN_S := 1.2             # and always at least this long after the last character
const SPEAKER_CHANGE_S := 0.7               # D1: a new voice takes a moment to place
const FULL_STOP_S := 0.4                    # D1: a message that ends a sentence lets it land
const READING_MIN := 0.75                   # D1: Options > Reading time range
const READING_MAX := 3.0
## Stage 3C: the card is a print. The photo is 4:5 (the portraits are 512x640) inside a paper border.
const CARD_SIZE := Vector2(152, 190)
const PHOTO_RECT := Rect2(8, 10, 136, 170)  # pre-D4 window (kept for reference; photo_rect() is drawn)
const KEYLINE := 2.0                        # D4: the dark line round the photo
const KEYLINE_COLOR := Color(0.07, 0.06, 0.05, 0.95)

var _portrait: Texture2D                    # the current radio speaker's print, or null (line drawing)


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	# --- radio panel ---
	radio_panel = PanelContainer.new()
	var sb := UIStyle.panel_box(0.8)
	sb.bg_color = Color(0.03, 0.045, 0.05, 0.86)
	sb.border_color = Color(0.35, 0.55, 0.42, 0.45)
	radio_panel.add_theme_stylebox_override("panel", sb)
	radio_panel.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	radio_panel.offset_left = 48
	radio_panel.offset_right = 48 + 820
	radio_panel.offset_top = -270
	radio_panel.offset_bottom = -48
	radio_panel.grow_vertical = Control.GROW_DIRECTION_BEGIN   # long lines / large text grow UP, never off-screen
	radio_panel.visible = false
	add_child(radio_panel)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", int(RADIO_SEP))
	radio_panel.add_child(h)
	card = Control.new()
	card.custom_minimum_size = CARD_SIZE
	card.size_flags_vertical = Control.SIZE_SHRINK_CENTER   # D4: the card never stretches with the row
	card.draw.connect(_draw_card)
	h.add_child(card)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	# name, then the identity line on its own row (beside the name it wrapped badly at large text sizes)
	r_name = UIStyle.label("", 20, Color(0.55, 0.95, 0.65), UIStyle.sans_semibold())
	v.add_child(r_name)
	r_ident = UIStyle.label("", 15, Color(0.62, 0.72, 0.64), UIStyle.sans())
	r_ident.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(r_ident)
	r_text = _rich(25)
	r_text.fit_content = false                 # D3: a fixed three-line box (fix_heights), never fit-to-text
	v.add_child(r_text)
	r_hint = UIStyle.label("", 15, UIStyle.DIM)
	r_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(r_hint)
	# --- subtitles (person / thought) ---
	sub_box = VBoxContainer.new()
	sub_box.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	sub_box.offset_left = -640
	sub_box.offset_right = 640
	sub_box.offset_top = -210
	sub_box.offset_bottom = -60
	sub_box.alignment = BoxContainer.ALIGNMENT_END
	sub_box.grow_vertical = Control.GROW_DIRECTION_BEGIN
	sub_box.visible = false
	add_child(sub_box)
	s_name = UIStyle.label("", 18, UIStyle.AMBER, UIStyle.sans_semibold())
	s_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub_box.add_child(s_name)
	s_text = _rich(28)
	s_text.custom_minimum_size = Vector2(1280, 0)
	sub_box.add_child(s_text)
	# --- choices ---
	# Lower-left, stacked directly above whatever text is showing (radio panel or subtitles) and growing
	# upwards (_layout_choices), so replies sit next to the line they answer at any text size and never
	# cover the radio command panel (right edge) or the subtitles.
	choice_box = VBoxContainer.new()
	choice_box.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	choice_box.offset_left = 48
	choice_box.offset_right = 48 + 700
	choice_box.offset_bottom = -270 - 14
	choice_box.offset_top = -270 - 14 - 236
	choice_box.grow_vertical = Control.GROW_DIRECTION_BEGIN
	choice_box.alignment = BoxContainer.ALIGNMENT_END
	choice_box.add_theme_constant_override("separation", 8)
	add_child(choice_box)
	choice_hint = UIStyle.label("", 16, Color(0.86, 0.82, 0.72, 0.78), UIStyle.serif_italic())
	choice_hint.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	choice_hint.offset_left = 52
	choice_hint.offset_right = 52 + 700
	choice_hint.visible = false
	add_child(choice_hint)
	fix_heights()


func _rich(size: int) -> RichTextLabel:
	var r := UIStyle.rich(size)             # Libre Baskerville with its real italic (thoughts were upright before 3A)
	r.visible_characters_behavior = TextServer.VC_CHARS_AFTER_SHAPING   # layout once; typing never re-wraps
	return r


## Typewriter speed, and the text size (UIStyle scales every registered label, button and rich text).
func apply_settings(cps: float, scale: float, reading := 1.0) -> void:
	speed_cps = cps
	text_scale = scale
	reading_mul = clampf(reading, READING_MIN, READING_MAX)
	if not is_equal_approx(UIStyle.text_scale, scale):
		UIStyle.set_text_scale(scale, get_tree())
	fix_heights()


## D3: the radio panel is one fixed size per text size. The text box holds exactly MAX_LINES lines
## (no fit-to-content); the identity row and the hint row reserve the most lines any speaker / the reply
## gate needs at this size. So the panel never changes size between lines, pages or speakers.
func fix_heights() -> void:
	var serif: Font = UIStyle.serif()
	var tsz := UIStyle.px(25)
	r_text.custom_minimum_size.y = ceilf(serif.get_height(tsz) * MAX_LINES) + 4.0
	var w := text_width("radio")
	var most := 1
	for sp in Speakers.TABLE:
		var e: Dictionary = Speakers.TABLE[sp]
		if String(e.get("where", "")) != "radio":
			continue
		var r := Speakers.resolve(sp, null)
		var parts: Array = []
		for k in ["call", "sub"]:
			if String(r.get(k, "")) != "":
				parts.append(String(r[k]))
		most = maxi(most, _label_lines("  ·  ".join(parts), UIStyle.sans(), UIStyle.px(15), w))
	r_ident.custom_minimum_size.y = _label_h(UIStyle.sans(), UIStyle.px(15), most)
	var gate := InputSetup.resolve("▸ Look at the radio on the desk and press {interact} to answer.")
	var hint_font: Font = r_hint.get_theme_font("font")
	r_hint.custom_minimum_size.y = _label_h(hint_font, UIStyle.px(15), _label_lines(gate, hint_font, UIStyle.px(15), w))


func _label_lines(t: String, font: Font, size: int, w: float) -> int:
	var p := TextParagraph.new()
	p.width = w - WRAP_MARGIN
	p.break_flags = TextServer.BREAK_MANDATORY | TextServer.BREAK_WORD_BOUND | TextServer.BREAK_ADAPTIVE
	p.add_string(t, font, size)
	return maxi(1, p.get_line_count())


func _label_h(font: Font, size: int, lines: int) -> float:
	return ceilf(font.get_height(size) * lines + 3.0 * (lines - 1)) + 2.0


# ------------------------------------------------------------------ API

func show_line(item: Dictionary) -> void:
	_active = true
	_clear_choices()
	mode = item["mode"]
	_item = _resolved(item)
	_speaker = _item["speaker"]
	line_look = _item["look"]
	var changed := _prev_speaker != "" and _prev_speaker != _speaker
	_prev_speaker = _speaker
	var radio := line_look == "radio"
	radio_panel.visible = radio
	sub_box.visible = not radio
	_source = String(item["text"])
	_pages = paginate(_source, line_look)
	_set_page(0, changed)


## D3: one page of the message: typed, read and timed like a line of its own. The panel, the name and the
## card do not change between pages (only the first page squelches).
func _set_page(i: int, speaker_changed := false) -> void:
	_page = i
	_full = String(_pages[i])
	_shown = 0.0
	_pause = 0.15
	_done_t = 0.0
	_auto_t = 0.0
	_advance_sent = false
	_read_s = line_read_s(_full, speaker_changed)
	var radio := line_look == "radio"
	if radio and i == 0:
		r_name.text = _item["name"]
		var ident: Array = []
		for k in ["call", "sub"]:
			if String(_item[k]) != "":
				ident.append(String(_item[k]))
		r_ident.text = "  ·  ".join(ident)
		_set_cue(false)
		var pp := Speakers.portrait(_speaker, String(_item.get("expr", "")))
		_portrait = load(pp) as Texture2D if pp != "" else null
		card.queue_redraw()
		blip.emit("squelch")
	elif not radio:
		s_name.text = _item["name"] if line_look == "person" else ""
		s_name.visible = s_name.text != ""
	_bb = _compose()
	var target := r_text if radio else s_text
	target.text = _bb
	target.visible_characters = 0
	_render()


## Items from the runner arrive resolved; bare items (tests, previews) are resolved here with hidden
## identities kept hidden.
func _resolved(item: Dictionary) -> Dictionary:
	if item.has("look") and item.has("name"):
		return {"speaker": String(item.get("speaker", "")), "name": String(item["name"]), "call": String(item.get("call", "")),
			"sub": String(item.get("sub", "")), "art": String(item.get("art", "")), "look": String(item["look"]),
			"expr": String(item.get("expr", ""))}
	var r := Speakers.resolve(String(item.get("speaker", "")), null)
	var kind := "thought" if r["id"] == "" else "speech"
	return {"speaker": r["id"], "name": r["name"], "call": r["call"], "sub": r["sub"], "art": r["art"],
		"look": Speakers.look(kind, r["where"], "", String(item.get("mode", "radio"))), "expr": String(item.get("expr", ""))}


## The whole line as BBCode. Brackets in the script are escaped so a caption like [ Knocks ] is text.
func _compose() -> String:
	var t := _full.replace("[", "[lb]")
	match line_look:
		"thought":
			return "[center][i]" + t + "[/i][/center]"
		"sound":
			var cap := Speakers.caption_text(_full).to_upper().replace("[", "[lb]")
			return "[center][color=#c8b88c][font_size=%d][lb] %s ][/font_size][/color][/center]" % [UIStyle.px(20), cap]
		"radio":
			return t
	return "[center]" + t + "[/center]"


func show_choices(item: Dictionary) -> void:
	_choices = item["choices"]
	_refresh_choices()


func close() -> void:
	_active = false
	_prev_speaker = ""
	radio_panel.visible = false
	sub_box.visible = false
	_choices = []
	_clear_choices()
	_restore_mouse()
	blip.emit("close")


func is_active() -> bool:
	return _active


func has_open_choices() -> bool:
	return not _choices.is_empty() and choice_box.get_child_count() > 0


# ------------------------------------------------------------------ internals

func _refresh_choices() -> void:
	_clear_choices()
	if _choices.is_empty():
		return
	var gated: bool = mode == "radio" and at_radio_fn.is_valid() and not at_radio_fn.call()
	if gated:
		r_hint.text = InputSetup.resolve("▸ Look at the radio on the desk and press {interact} to answer.")
		r_hint.modulate.a = 1.0
		return
	r_hint.text = ""
	for c in _choices:
		var b := UIStyle.button("%d   %s" % [c["index"] + 1, c["text"]])
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		# keyboard and mouse: replies never take focus, so Space (ui_accept) and the arrows can't press or
		# move them; a pad player gets focus (d-pad + A) the moment a pad button is used (_pad_focus)
		b.focus_mode = Control.FOCUS_ALL if InputSetup.pad_active else Control.FOCUS_NONE
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART    # long replies wrap inside the 700 px column
		b.custom_minimum_size = Vector2(700, 46)
		UIStyle.track(b, 21)                   # replies follow the text size like every other label
		var idx: int = c["index"]
		b.pressed.connect(func(): _pick(idx))
		choice_box.add_child(b)
	_layout_choices()
	_choice_age = 0.0
	if InputSetup.pad_active:
		focus_first_choice()               # pad: the highlighted reply is what A answers
	_update_choice_hint()
	_restore_mouse()


## The first reply takes focus (pad only): the d-pad moves it and A answers it.
func focus_first_choice() -> void:
	if choice_box.get_child_count() == 0:
		return
	var fo := get_viewport().gui_get_focus_owner()
	if fo == null or not choice_box.is_ancestor_of(fo):
		(choice_box.get_child(0) as Control).grab_focus.call_deferred()


## A pad button was used while replies are up: let the replies take focus (they are created without it
## for keyboard and mouse) and highlight the first, so the d-pad and A work.
func _pad_focus() -> void:
	for c in choice_box.get_children():
		(c as Control).focus_mode = Control.FOCUS_ALL
	focus_first_choice()


func _update_choice_hint() -> void:
	var show := choice_box.get_child_count() > 0 and Settings.tip_wanted("replies")
	choice_hint.visible = show
	if show:
		var free_walk: bool = not (in_view_fn.is_valid() and in_view_fn.call())
		if InputSetup.pad_active:
			choice_hint.text = "D-pad to choose  ·  %s to answer" % InputSetup.glyph("interact")
		elif free_walk:
			choice_hint.text = "Press 1 – %d to answer" % choice_box.get_child_count()
		else:
			choice_hint.text = "Press 1 – %d, or click a reply" % choice_box.get_child_count()


## Keep the reply stack 14 px above the top of the visible speech block (radio panel or subtitles).
func _layout_choices() -> void:
	var vp_h := get_viewport_rect().size.y
	var top := vp_h - 48.0
	if radio_panel.visible:
		top = radio_panel.get_global_rect().position.y
	elif sub_box.visible:
		top = sub_box.get_global_rect().position.y
	choice_box.offset_bottom = top - 14.0 - vp_h
	choice_box.offset_top = choice_box.offset_bottom - 236.0
	var stack_h := choice_box.get_combined_minimum_size().y
	choice_hint.offset_bottom = choice_box.offset_bottom - stack_h - 6.0
	choice_hint.offset_top = choice_hint.offset_bottom - 24.0


func _clear_choices() -> void:
	for c in choice_box.get_children():
		choice_box.remove_child(c)      # detach now so the box is empty this frame (layout, tests)
		c.queue_free()
	if choice_hint:
		choice_hint.visible = false


## Ask the game to re-apply its single mouse policy (game_fp.mouse_should_capture). This layer never
## sets Input.mouse_mode itself: two owners fighting over it left the pointer stuck on (IMG_3140).
func _restore_mouse() -> void:
	if mouse_restore_fn.is_valid():
		mouse_restore_fn.call()


func _pick(i: int) -> void:
	if get_tree().paused or _choice_age < CHOICE_GUARD_S:
		return                             # nothing is answered in the first moments (item 25: no accidental picks)
	if choice_box.get_child_count() > 0 and not (in_view_fn.is_valid() and in_view_fn.call()):
		Settings.tip_used("replies")       # answered with the keys in free walk: the hint has done its job
	_choices = []
	_clear_choices()
	_restore_mouse()
	choice_made.emit(i)


## Reveal up to _shown characters of the already laid-out line (no re-parse, no re-wrap).
func _render() -> void:
	var target := r_text if line_look == "radio" else s_text
	var n := int(_shown)
	target.visible_characters = -1 if n >= _full.length() else n


func _process(delta: float) -> void:
	_t += delta
	_choice_age += delta
	card.queue_redraw()
	if not _active or get_tree().paused:      # the typewriter freezes under the pause menu
		return
	if not _choices.is_empty() and choice_box.get_child_count() == 0:
		_refresh_choices()      # the player may have walked to the radio
	elif choice_box.get_child_count() > 0 and mode == "radio" and at_radio_fn.is_valid() and not at_radio_fn.call():
		_clear_choices()        # walked away from the handset: hide the replies again (they come back at the radio)
		r_hint.text = InputSetup.resolve("▸ Look at the radio on the desk and press {interact} to answer.")
		r_hint.modulate.a = 1.0
		_restore_mouse()
	if choice_box.get_child_count() > 0:
		_layout_choices()       # the speech block can grow while the line types out
	var held: bool = (doc_open_fn.is_valid() and doc_open_fn.call()) or (hold_fn.is_valid() and hold_fn.call())
	if not held:
		_auto_t += delta
	if _shown < _full.length():
		if held:
			return                  # reading a document / the screen is faded: nothing types unseen
		if _pause > 0.0:
			_pause -= delta
			return
		var before := int(_shown)
		_shown = minf(_full.length(), _shown + delta * speed_cps)
		var after := int(_shown)
		if after > before:
			var ch := _full[after - 1]
			if ch in ".!?":
				_pause = 0.32
			elif ch in ",;:":
				_pause = 0.14
			elif ch == "-" or ch == "…":
				_pause = 0.2
			if after % 3 == 0:
				blip.emit("char")
			_render()
	else:
		if not held:
			_done_t += delta
		if auto_advance and _choices.is_empty() and not _advance_sent and not held \
				and _done_t >= AUTO_AFTER_SHOWN_S and _auto_t >= _read_s:
			if _page < _pages.size() - 1:
				_set_page(_page + 1)        # D3: the next page of the same message
			else:
				_advance_sent = true
				advance_requested.emit()


# ------------------------------------------------------------------ D3: three lines at most

## The width the line's text wraps in, in px (radio: the column beside the card; others: the subtitles).
func text_width(look: String) -> float:
	if look == "radio":
		var sb := radio_panel.get_theme_stylebox("panel")
		var inner := RADIO_W - (sb.get_content_margin(SIDE_LEFT) + sb.get_content_margin(SIDE_RIGHT) if sb else 44.0)
		return inner - CARD_SIZE.x - RADIO_SEP
	return SUB_W


## How many lines `text` takes in the label that shows `look` (TextParagraph with the label's own font,
## size and word-smart wrapping, less a small safety margin so a measured fit always fits on screen).
func line_count(text: String, look: String) -> int:
	var p := TextParagraph.new()
	p.width = text_width(look) - WRAP_MARGIN
	p.break_flags = TextServer.BREAK_MANDATORY | TextServer.BREAK_WORD_BOUND | TextServer.BREAK_ADAPTIVE
	var font: Font = UIStyle.serif_italic() if look == "thought" else UIStyle.serif()
	var size := UIStyle.px(25 if look == "radio" else 28)
	var t := Speakers.caption_text(text).to_upper() if look == "sound" else text
	p.add_string(t, font, size)
	return p.get_line_count()


## D3: the message as pages of MAX_LINES lines or fewer: whole sentences where they fit, else clauses, else
## words. Joined with single spaces the pages are the message (whitespace normalised).
func paginate(text: String, look: String) -> Array:
	var src := " ".join(text.strip_edges().split(" ", false))
	if src == "" or line_count(src, look) <= MAX_LINES:
		return [src]
	var pages: Array = []
	_pack(_split_after(src, ".!?…"), look, pages, 0)
	return pages


## Greedy packing; a piece that alone is too long is split at the next finer boundary.
func _pack(pieces: Array, look: String, pages: Array, level: int) -> void:
	var cur := ""
	for piece in pieces:
		var s := String(piece)
		if line_count(s, look) > MAX_LINES:
			if cur != "":
				pages.append(cur)
				cur = ""
			if level == 0:
				_pack(_split_after(s, ",;:—"), look, pages, 1)
			else:
				_pack(Array(s.split(" ", false)), look, pages, 2)
			continue
		var joined := s if cur == "" else cur + " " + s
		if line_count(joined, look) <= MAX_LINES:
			cur = joined
		else:
			pages.append(cur)
			cur = s
	if cur != "":
		pages.append(cur)


## Splits after any of `marks` followed by a space, keeping the mark with its piece.
static func _split_after(s: String, marks: String) -> Array:
	var out: Array = []
	var start := 0
	for i in s.length() - 1:
		if s[i] in marks and s[i + 1] == " ":
			out.append(s.substr(start, i + 1 - start))
			start = i + 2
	out.append(s.substr(start))
	return out.filter(func(x): return String(x) != "")


## D1: how long a line stays before it advances by itself. Longer lines read longer, a slower typewriter
## reads slower, a new voice and a closing full stop add a beat, and Options > Reading time scales it all.
func line_read_s(text: String, speaker_changed := false) -> float:
	var pace := clampf(42.0 / maxf(speed_cps, 1.0), 0.8, 1.6)
	var s := clampf(AUTO_BASE_S + AUTO_PER_CHAR_S * text.length(), AUTO_MIN_S, AUTO_MAX_S) * pace
	if speaker_changed:
		s += SPEAKER_CHANGE_S
	if text.strip_edges().ends_with("."):
		s += FULL_STOP_S
	return s * reading_mul


## R1: kept for callers that ask how long a plain line reads (no speaker change).
func auto_advance_s(text: String) -> float:
	return line_read_s(text)


## The hint row under the radio text is only the reply gate's "look at the radio" now (D1 removed the
## Space cue); clearing it is all that is left.
func _set_cue(_on: bool) -> void:
	r_hint.text = ""
	r_hint.modulate.a = 1.0


func _unhandled_input(event: InputEvent) -> void:
	if not _active or get_tree().paused:      # this layer keeps processing during pause: ignore input
		return
	if doc_open_fn.is_valid() and doc_open_fn.call():
		return                                # reading a document: E / clicks belong to the viewer
	if hold_fn.is_valid() and hold_fn.call():
		return                                # 3B: under a fade nothing can be finished or skipped unseen
	if not _choices.is_empty():
		if choice_box.get_child_count() == 0:
			return                            # radio replies gated: not in the radio view
		if event is InputEventKey and event.pressed and not event.echo \
				and event.physical_keycode >= KEY_1 and event.physical_keycode <= KEY_4:
			var i: int = event.physical_keycode - KEY_1
			if i < _choices.size():
				_pick(i)
				get_viewport().set_input_as_handled()
			return
		if (event is InputEventJoypadButton and event.pressed) and get_viewport().gui_get_focus_owner() == null:
			_pad_focus()
			get_viewport().set_input_as_handled()
		return                                # E, Space, the wheel and W/S are not answers (items 7, 25)
	# D1: nothing finishes or advances a line. Every other event passes through untouched (E belongs to
	# interaction, item 7).


## D4: where the photo is drawn on the card: everything inside the keyline.
func photo_rect() -> Rect2:
	return Rect2(Vector2(KEYLINE, KEYLINE), CARD_SIZE - Vector2(KEYLINE, KEYLINE) * 2.0)


## D4: the part of a `tex` sized image that covers `win` without stretching (centred crop).
static func cover_src(tex: Vector2, win: Vector2) -> Rect2:
	var k := maxf(win.x / tex.x, win.y / tex.y)
	var sz := win / k
	return Rect2((tex - sz) * 0.5, sz)


func _draw_card() -> void:
	# Stage 3A: the identity text moved to the name row (it was drawn here at 9-10 px and never scaled);
	# the card keeps the live signal meter; Stage 3C: a speaker with a portrait gets the print in a paper
	# border, everyone else (the Corrie May, the Lowestoft Star, the Mary Ellen caller) keeps the drawing
	# Audit D4 (2026-11-16): a portrait fills the card edge to edge (cover-cropped, centred) inside a thin
	# dark keyline; there is no cream margin or band, and the card is always CARD_SIZE (it never stretches).
	var w := card.size.x
	var h := card.size.y
	if _portrait != null:
		var win := photo_rect()
		card.draw_rect(Rect2(0, 0, w, h), KEYLINE_COLOR)
		card.draw_texture_rect_region(_portrait, win, cover_src(_portrait.get_size(), win.size))
	else:
		card.draw_rect(Rect2(0, 0, w, h), Color(0.86, 0.82, 0.7, 0.92))
		card.draw_rect(Rect2(4, 4, w - 8, h - 8), Color(0.25, 0.2, 0.15, 0.6), false, 2.0)
	var kind: String = "" if _portrait != null else String(_item.get("art", ""))
	var ink := Color(0.18, 0.14, 0.11)
	var cx := w * 0.5
	var cy := h * 0.52
	match kind:
		"fishing", "schooner", "steamer":
			var L := 120.0 if kind == "steamer" else 100.0
			card.draw_colored_polygon(PackedVector2Array([Vector2(cx - L / 2, cy), Vector2(cx + L / 2 + 12, cy - 6), Vector2(cx + L / 2 - 4, cy + 16), Vector2(cx - L / 2 + 8, cy + 16)]), ink)
			card.draw_rect(Rect2(cx - 14, cy - 22, 30, 22), ink)
			if kind == "schooner":
				card.draw_line(Vector2(cx - 24, cy), Vector2(cx - 24, cy - 62), ink, 2.0)
				card.draw_line(Vector2(cx + 22, cy), Vector2(cx + 22, cy - 54), ink, 2.0)
			elif kind == "steamer":
				card.draw_rect(Rect2(cx + 4, cy - 46, 12, 24), Color(0.5, 0.12, 0.08))
			else:
				card.draw_line(Vector2(cx - 30, cy), Vector2(cx - 30, cy - 50), ink, 2.0)
		"station":
			card.draw_rect(Rect2(cx - 10, cy - 50, 20, 64), ink)
			card.draw_colored_polygon(PackedVector2Array([Vector2(cx - 14, cy - 50), Vector2(cx + 14, cy - 50), Vector2(cx, cy - 66)]), ink)
			card.draw_line(Vector2(cx + 14, cy - 56), Vector2(cx + 60, cy - 70), Color(0.75, 0.5, 0.15), 3.0)
	if line_look == "radio" and _active:
		if _portrait != null:                   # a dark plate so the meter reads over the photo
			card.draw_rect(Rect2(w - 27, h - 82, 22, 52), Color(0.04, 0.035, 0.03, 0.55))
		for i in 5:
			var lit := (sin(_t * 9.0 + i) * 0.5 + 0.5) * 5.0 > i
			card.draw_rect(Rect2(w - 22, h - 40 - i * 9, 12, 6), Color(0.2, 0.6, 0.3) if lit else Color(0.4, 0.35, 0.3))
