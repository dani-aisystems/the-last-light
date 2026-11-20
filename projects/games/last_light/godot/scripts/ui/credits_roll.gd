class_name CreditsRoll
extends Control
## G6a (item 34): rolling credits over warm black. data/credits.txt (BBCode) scrolls up from below the
## screen at a reading pace (audit D1: Space no longer speeds it up); Esc (or pad B) jumps to the end. At the end the
## "Return to the title" button fades in (after an ending) or "Back" (from the menu's Credits). From the
## menu the wheel and a drag also move it. After an ending the credits music plays on the Music bus
## (CREDITS_MUSIC: cue M14, a synthesised placeholder until the real tracks; audit music stage).

signal finished

const CREDITS_PATH := "res://data/credits.txt"
const CREDITS_MUSIC := "res://assets/audio/music_m14_credits.wav"   # audit music: cue M14 (data/music_cues.json)
const SPEED_PX := 46.0                  # at 1080 p; scaled with the window height
const MUSIC_DB := 0.0                 # the cue file is mastered to its level (-16 LUFS)
const WARM_BLACK := Color(0.035, 0.026, 0.02)

var ending := false
var at_end := false
var scroll := 0.0                       # px the text has moved up from its start (below the screen)
var music: AudioStreamPlayer
var text: RichTextLabel
var end_button: Button
var _clip: Control
var _dragging := false
var _leaving := false
var frozen := false                     # captures: held at one scroll position


func setup(after_ending: bool) -> CreditsRoll:
	ending = after_ending
	return self


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP      # nothing under the roll (the title menu) takes clicks
	focus_mode = Control.FOCUS_ALL                 # ... or keys: the roll holds the focus until its button
	var bg := ColorRect.new()
	bg.color = WARM_BLACK
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	_clip = Control.new()
	_clip.clip_contents = true
	_clip.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_clip)
	text = RichTextLabel.new()
	text.bbcode_enabled = true
	text.fit_content = true
	text.scroll_active = false
	text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	text.add_theme_font_override("normal_font", UIStyle.serif())
	text.add_theme_font_override("italics_font", UIStyle.serif_italic())
	text.add_theme_color_override("default_color", UIStyle.INK)
	text.add_theme_constant_override("line_separation", 6)
	UIStyle.track(text, 22)
	text.text = FileAccess.get_file_as_string(CREDITS_PATH)
	_clip.add_child(text)
	end_button = UIStyle.button("Return to the title" if ending else "Back")
	end_button.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	end_button.offset_left = -170
	end_button.offset_right = 170
	end_button.offset_top = -120
	end_button.offset_bottom = -62
	end_button.modulate.a = 0.0
	end_button.visible = false
	end_button.pressed.connect(leave)
	add_child(end_button)
	if ending:
		music = AudioStreamPlayer.new()
		var s = load(CREDITS_MUSIC)
		music.stream = s
		music.bus = "Music"
		music.volume_db = -40.0
		add_child(music)
		music.play()
		create_tween().tween_property(music, "volume_db", MUSIC_DB, 3.0)
	_layout()
	resized.connect(_layout)
	grab_focus.call_deferred()


func _layout() -> void:
	var w := minf(size.x - 120.0, 1100.0)
	text.size = Vector2(w, 0)
	text.custom_minimum_size = Vector2(w, 0)
	text.position = Vector2((size.x - w) * 0.5, size.y - scroll)


## The scroll distance at which the last line has passed the upper third.
func end_scroll() -> float:
	return size.y * 0.66 + text.get_content_height()


func _process(delta: float) -> void:
	if _leaving:
		return
	if not at_end and not frozen:
		var k := size.y / 1080.0                 # audit D1: no Space speed-up after an ending (Esc still leaves)
		if not _dragging:
			scroll += SPEED_PX * k * delta
		if scroll >= end_scroll():
			jump_to_end()
	text.position.y = size.y - scroll


## Captures: hold the roll `px` in (no music after an ending is involved: menu mode).
func freeze_at(px: float) -> void:
	frozen = true
	scroll = px


func jump_to_end() -> void:
	if at_end:
		return
	at_end = true
	scroll = maxf(scroll, end_scroll())
	end_button.visible = true
	create_tween().tween_property(end_button, "modulate:a", 1.0, 1.2)
	end_button.grab_focus.call_deferred()


## The music fades out, then `finished`.
func leave() -> void:
	if _leaving:
		return
	_leaving = true
	if music:
		var tw := create_tween()
		tw.tween_property(music, "volume_db", -40.0, 1.5)
		await tw.finished
		music.stop()
	finished.emit()


func _unhandled_input(event: InputEvent) -> void:
	if _leaving:
		return
	if event.is_action_pressed("pause") or event.is_action_pressed("back"):
		if at_end or not ending:
			leave()
		else:
			jump_to_end()
		get_viewport().set_input_as_handled()
		return


func _gui_input(event: InputEvent) -> void:
	if _leaving or ending or at_end:
		return
	if event is InputEventMouseButton:              # from the menu: the wheel and a drag move it
		if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			scroll = maxf(0.0, scroll - 60.0)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			scroll += 60.0
		elif event.button_index == MOUSE_BUTTON_LEFT:
			_dragging = event.pressed
	elif event is InputEventMouseMotion and _dragging:
		scroll = maxf(0.0, scroll - event.relative.y)
