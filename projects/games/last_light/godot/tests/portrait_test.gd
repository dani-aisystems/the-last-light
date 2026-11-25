extends SceneTree
## Stage 3C / item 22: the radio portrait card.
##  P1  every main radio speaker has a neutral print (512x640) in assets/portraits/
##  P2  Speakers.portrait: an exact expression, the neutral fallback for a missing one, and no portrait for
##      the procedural voices, the Mary Ellen caller, the man at the door and narration
##  P3  every SPEAKER(expr) tag in the .dlg files names a print that exists (no silent typo fallbacks)
##  P4  the card: 152x190, the print for a radio line (expression honoured), the drawing for a voice
##      without one, and the identity resolver still hides Ross (an unrevealed ROSS gets no print)
##   tools/godot --headless --path godot -s res://tests/portrait_test.gd

var fails: Array[String] = []
var passes := 0


func _initialize() -> void:
	_run.call_deferred()


func _ok(cond: bool, what: String) -> void:
	if cond:
		passes += 1
	else:
		fails.append(what)


func _run() -> void:
	# P1
	for id in ["CALLUM", "MORAG", "RORY", "ELSPETH", "HECTOR", "ROSS"]:
		var p := Speakers.portrait(id)
		_ok(p.ends_with("/%s_neutral.png" % id.to_lower()), "P1 %s neutral print: '%s'" % [id, p])
		if p != "":
			var t := load(p) as Texture2D
			_ok(t != null and t.get_size() == Vector2(512, 640), "P1 %s print is 512x640" % id)
	# P2
	_ok(Speakers.portrait("MORAG", "worried").ends_with("/morag_worried.png"), "P2 exact expression")
	_ok(Speakers.portrait("MORAG", "neutral").ends_with("/morag_neutral.png"), "P2 explicit neutral")
	_ok(Speakers.portrait("MORAG", "no_such_face").ends_with("/morag_neutral.png"), "P2 missing expression falls back")
	for id in ["", "CORRIE", "LOWESTOFT", "MARY ELLEN", "VISITOR"]:
		_ok(Speakers.portrait(id, "worried") == "", "P2 no print for '%s'" % id)
	_ok(Speakers.portrait(Speakers.resolve("ROSS", null)["id"]) == "", "P2 an unrevealed ROSS (VISITOR) gets no print")
	# P3
	var db := DialogueDB.new()
	db.load_dir("res://data/story")
	var tagged := 0
	for cid in db.convs:
		for s in db.convs[cid]["steps"]:
			var ex := String(s.get("expr", ""))
			if ex == "":
				continue
			tagged += 1
			var want := "/%s_%s.png" % [String(s["speaker"]).to_lower().replace(" ", "_"), ex]
			_ok(Speakers.portrait(String(s["speaker"]), ex).ends_with(want), "P3 %s: %s(%s) has no print %s" % [cid, s["speaker"], ex, want])
	_ok(tagged >= 20, "P3 expression tags parsed from the .dlg files (%d)" % tagged)
	# P4
	var ui: Control = load("res://scripts/ui/dialogue_ui.gd").new()
	root.add_child(ui)
	await process_frame
	_ok(ui.card.custom_minimum_size == Vector2(152, 190), "P4 card is 152x190")
	ui.show_line({"type": "line", "mode": "radio", "speaker": "MORAG", "name": "Morag Fraser", "look": "radio",
		"expr": "worried", "text": "North Point! Callum! Answer me!"})
	_ok(ui._portrait != null and ui._portrait.resource_path.ends_with("/morag_worried.png"), "P4 runner item: worried print")
	ui.show_line({"mode": "radio", "speaker": "ELSPETH", "expr": "cold", "text": "Mackay."})
	_ok(ui._portrait != null and ui._portrait.resource_path.ends_with("/elspeth_cold.png"), "P4 bare item: expr carried through _resolved")
	ui.show_line({"mode": "radio", "speaker": "RORY", "expr": "grin", "text": "Och."})
	_ok(ui._portrait != null and ui._portrait.resource_path.ends_with("/rory_neutral.png"), "P4 missing grin shows neutral")
	ui.show_line({"mode": "radio", "speaker": "CORRIE", "text": "North Point, Corrie May."})
	_ok(ui._portrait == null, "P4 Corrie May keeps the drawing")
	ui.show_line({"mode": "radio", "speaker": "MARY ELLEN", "text": "...we cannot see your light..."})
	_ok(ui._portrait == null, "P4 the Mary Ellen caller keeps the registry drawing")
	ui.queue_free()
	print("PORTRAIT_RESULT ", JSON.stringify({"passed": passes, "failed": fails.size(), "failures": fails}))
	quit(1 if fails.size() > 0 else 0)
