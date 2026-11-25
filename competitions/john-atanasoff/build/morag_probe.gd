extends SceneTree
## Evidence probe for the defence (does not touch the game). Plays the real .dlg conversations through the
## real DialogueRunner + StoryState: first ch3_notes_b (the radio call at the breaker, three replies), then
## ch6_morag_dawn (the dawn call). Prints which of Morag's lines the player is shown in each case.
##   godot --headless --path godot -s /abs/path/morag_probe.gd
func _initialize() -> void:
	_run.call_deferred()


func _play(runner: DialogueRunner, choose_text: String) -> Dictionary:
	var shown: Array = []
	var picked := ""
	var item := runner.advance()
	var guard := 0
	while item["type"] != "end" and guard < 200:
		guard += 1
		match item["type"]:
			"line":
				shown.append("%s: %s" % [String(item["name"]).to_upper(), item["text"]])
				item = runner.advance()
			"choice":
				var idx := 0
				for c in item["choices"]:
					if choose_text != "" and choose_text in String(c["text"]):
						idx = int(c["index"])
				picked = String(item["choices"][idx]["text"])
				item = runner.choose(idx)
			_:
				item = runner.advance()
	return {"lines": shown, "picked": picked}


func _run() -> void:
	var db := DialogueDB.new()
	db.load_dir("res://data/story")
	var out := []
	var cases := [
		{"name": "no_ch3_call", "ch3": null, "dawn": "Amend my station log"},
		{"name": "lie_to_morag", "ch3": "The log says oh-two-ten", "dawn": "Amend my station log"},
		{"name": "deflect", "ch3": "eighteen years ago", "dawn": "Amend my station log"},
		{"name": "admit", "ch3": "I was there. The light was out", "dawn": "Amend my station log"},
		{"name": "admit_then_silence", "ch3": "I was there. The light was out", "dawn": "Nothing to report"},
	]
	for c in cases:
		var st := StoryState.new()
		st.rescues = {"Iona Star": "saved"}
		var r := DialogueRunner.new(db, st)
		var ch3 := {"lines": [], "picked": ""}
		if c["ch3"] != null:
			r.start("ch3_notes_b")
			ch3 = _play(r, String(c["ch3"]))
		r.start("ch6_morag_dawn")
		var dawn := _play(r, String(c["dawn"]))
		var morag_dawn: Array = dawn["lines"].filter(func(l): return String(l).begins_with("MORAG"))
		out.append({"case": c["name"], "ch3_choice": ch3["picked"], "flags": st.flags.duplicate(), "rel_morag": st.rel["morag"],
			"dawn_choice": dawn["picked"], "morag_lines_at_dawn": morag_dawn})
	print("MORAG_PROBE_RESULT ", JSON.stringify(out))
	quit(0)
