class_name LogbookPages
extends SubViewport
## G2b layer C (Daniel 2026-11-06): the station logbook as the keeper sees it tonight.
##   "log"    the 14 November page with only the rows Callum has written so far (StoryState.log_written)
##   "duties" the pencil "Tonight" page at the back of the log: the duties he knows, done ones struck through
## Built from the strips blender/log_strips.py renders in his hand (assets/docs/log/, placed by manifest.json),
## drawn by this SubViewport, whose texture the document viewer shows like any other document page.
## A page is a stack of TextureRects, so tests can read exactly which rows and lines are on it.

const DIR := "res://assets/docs/log/"
const DUTY_X := 110
const SUB_X := 160
const HINT_X := 200                    # audit D8: hints under their step
const TOP_Y := 128
const DUTY_GAP := 52
const SUB_GAP := 46
const PENCIL := Color(0.30, 0.30, 0.31, 0.85)

var manifest: Dictionary = {}
var page := ""                    # "log" | "duties"
var shown: Array = []             # what is on the page: row ids, or "duty:<id>" / "sub:<id>.<sub>" (+ "~" if struck),
                                  # "hint:<id>.<sub>" for a hint kept under its step (audit D8)


func _init() -> void:
	size = Vector2i(1500, 1050)
	transparent_bg = false
	render_target_update_mode = SubViewport.UPDATE_DISABLED
	var f := FileAccess.get_file_as_string(DIR + "manifest.json")
	if f != "":
		manifest = JSON.parse_string(f)
	if manifest.has("page"):
		size = Vector2i(int(manifest["page"][0]), int(manifest["page"][1]))


func _clear() -> void:
	for c in get_children():
		remove_child(c)
		c.queue_free()
	shown = []


func _add_tex(path: String, pos: Vector2) -> TextureRect:
	var t := TextureRect.new()
	t.texture = load(path)
	t.position = pos
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(t)
	return t


## The log page with the rows already written. Returns the transcription (T).
func build_log(written: Array, rows: Array) -> String:
	_clear()
	page = "log"
	_add_tex(DIR + "page_log.png", Vector2.ZERO)
	var lines: Array = []
	for e in rows:                                   # canon order, whatever order they were written in
		var id := String(e["id"])
		if not (id in written) or not manifest.get("rows", {}).has(id):
			continue
		_add_tex(DIR + "row_%s.png" % id, Vector2(0, float(manifest["rows"][id]["y"])))
		shown.append(id)
		lines.append("%s %s, %s. %s" % [e["time"], e["wind"], String(e["weather"]).to_lower(), e["text"]])
	render_target_update_mode = SubViewport.UPDATE_ALWAYS
	if lines.is_empty():
		return "Station log, North Point, Sunday 14 November 1971.\n\nNothing written yet tonight."
	return "Station log, North Point, Sunday 14 November 1971.\n\n14.11.71 Sun.\n" + "\n".join(lines)


## The pencil page: the duties the keeper knows in this chapter of the night, its known steps under
## each; done ones struck through, optional ones he did without left off. Returns the transcription (T).
func build_duties(director: StoryDirector) -> String:
	_clear()
	page = "duties"
	_add_tex(DIR + "page_duties.png", Vector2.ZERO)
	var y := float(TOP_Y)
	var lines: Array = ["Tonight (pencil, at the back of the log):"]
	for c in director.chapters:
		if int(c["n"]) != director.state.chapter:
			continue
		for d in c.get("duties", []):
			var id := String(d["id"])
			var st := director.state.duty_state(id)
			if st == StoryState.DUTY_HIDDEN or y > size.y - 60:
				continue
			var e: Dictionary = director.state.duties.get(id, {})
			var done := st == StoryState.DUTY_DONE
			_strip(DIR + "duty_%s.png" % id, Vector2(DUTY_X, y), done)
			shown.append("duty:" + id + ("~" if done else ""))
			lines.append(("[done] " if done else "") + String(d.get("line", "")))
			y += DUTY_GAP
			if not done and d.get("sub", []).is_empty():
				y = _hint(id, "_", String(d.get("hint", "")), e, y, lines)
			for sb in d.get("sub", []):
				var sid := String(sb["id"])
				if not (sid in e.get("known", [])) or sid in e.get("dropped", []):
					continue
				var sdone: bool = sid in e.get("done", [])
				_strip(DIR + "sub_%s_%s.png" % [id, sid], Vector2(SUB_X, y), sdone)
				shown.append("sub:%s.%s%s" % [id, sid, "~" if sdone else ""])
				lines.append("    " + ("[done] " if sdone else "") + String(sb.get("line", "")))
				y += SUB_GAP
				if not sdone:
					y = _hint(id, sid, String(sb.get("hint", "")), e, y, lines)
			y += 14
	render_target_update_mode = SubViewport.UPDATE_ALWAYS
	return "\n".join(lines)


## Audit D8 (2026-11-16): a hint the keeper has been given stays under its step until the step is done.
func _hint(duty: String, sub: String, text: String, e: Dictionary, y: float, lines: Array) -> float:
	if not (sub in e.get("hinted", [])) or not manifest.get("duties", {}).get(duty, {}).get("hint", {}).has(sub):
		return y
	_add_tex(DIR + "hint_%s_%s.png" % [duty, sub], Vector2(HINT_X, y - 6))
	shown.append("hint:%s.%s" % [duty, sub])
	lines.append("        (hint) " + text)
	return y + float(manifest["duties"][duty]["hint"][sub]["h"]) - 4.0


func _strip(path: String, pos: Vector2, struck: bool) -> void:
	var t := _add_tex(path, pos)
	if struck and t.texture:
		var line := Line2D.new()                     # a pencil stroke through it, slightly uneven
		line.width = 2.6
		line.default_color = PENCIL
		var w := float(t.texture.get_width()) - 12.0
		# log_strips.py: text drawn 6 px down, strip height = font size + 22; strike at mid x-height
		var h := 6.0 + (float(t.texture.get_height()) - 22.0) * 0.6
		line.points = PackedVector2Array([pos + Vector2(4, h + 1.5), pos + Vector2(w * 0.5, h - 0.5), pos + Vector2(w, h + 1.0)])
		add_child(line)


func stop() -> void:
	render_target_update_mode = SubViewport.UPDATE_DISABLED
