class_name StoryState
extends RefCounted
## Everything the story remembers: chapter, director beat, flags, clues, relationships, choices,
## rescues, the dialogue history and the current objective. Serialises to a plain Dictionary.

var chapter := 1
var beat := 0
var flags := {}
var clues := {}
var rel := {"morag": 0, "elspeth": 0, "ross": 0}
var rescues := {}             # ship name -> "saved" | "lost"
var convs_done := {}
var history: Array = []       # {speaker (as shown), name, text, mode, look, chapter, conv, clock[, choice]}
## Brief item 9: a plain String, or {"title": .., "steps": [{"text": .., "done": <expr>, "live": bool}]}.
var objective = ""
var obj_done: Array = []      # indices of latched (completed) steps of the current objective
## G2b (Daniel 2026-11-06): duties replace the step checklist. Keyed by duty id (chapters.json "duties"),
## so they survive beat-layout changes. s: DUTY_HIDDEN / KNOWN / ACTIVE / DONE; "known" and "done" list the
## sub-task ids the keeper has discovered / really done (both latch); "dropped" lists optional sub-tasks
## that no longer matter (the torch once the lights are on).
const DUTY_HIDDEN := 0
const DUTY_KNOWN := 1
const DUTY_ACTIVE := 2
const DUTY_DONE := 3
var duties := {}               # id -> {"s": int, "known": [sub ids], "done": [sub ids], "dropped": [sub ids],
                               #        "hinted": [sub ids whose hint was given; "_" = the duty's own] (audit D8)}
var focus_duty := ""           # the duty the HUD is about: the one a beat made active last ("" = none)
var log_written: Array = []    # station-log entry ids Callum has written tonight, in order (G2b layer C)
var sim: KeeperSim             # for conditions that read the station
var play_seconds := 0.0
## An autosave inside a beat (3B): the beat had started and these actions were still to run.
var in_beat := false
var resume: Array = []
## Beat layout of chapters.json. Saves are by beat INDEX, so older layouts are remapped on load.
## 2 = Stage 3B (ch1 15 -> 11 beats, ch6 3 -> 7 beats).
## 3 = brief 2026-11-06 item 8 (ch1: the dark arrival; engine and charge come before the console).
const LAYOUT := 3
const REMAP := {          # chapter -> {from layout: old index -> index in the next layout}
	1: {1: [0, 1, 1, 1, 2, 2, 3, 4, 5, 5, 6, 7, 8, 9, 10], 2: [0, 1, 1, 2, 4]},
	6: {1: [0, 4, 5]},
}


func has_objective() -> bool:
	if has_active_duty():
		return true
	if objective is Dictionary:
		return not objective.is_empty()
	return String(objective) != ""


## G2b: is any duty active and not yet done?
func has_active_duty() -> bool:
	for id in duties:
		if int(duties[id].get("s", 0)) == DUTY_ACTIVE:
			return true
	return false


func duty_state(id: String) -> int:
	return int(duties.get(id, {}).get("s", DUTY_HIDDEN))


## Audit D8 (2026-11-16): the step's hint has been shown, so the Duties page keeps it under the step.
func mark_hinted(duty: String, sub: String) -> void:
	if not duties.has(duty):
		return
	var h: Array = duties[duty].get("hinted", [])
	if not (sub in h):
		h.append(sub)
	duties[duty]["hinted"] = h


## For conditions: the duty (or "duty.sub") is done.
func duty_done(id: String) -> bool:
	if "." in id:
		var p := id.split(".", true, 1)
		return String(p[1]) in duties.get(p[0], {}).get("done", [])
	return duty_state(id) == DUTY_DONE


func flag(name_: String):
	return flags.get(name_, 0)


func has_flag(name_: String) -> bool:
	if not flags.has(name_):
		return false
	var v = flags[name_]
	if v is bool:
		return v
	if v is int or v is float:
		return v != 0
	return v != null and str(v) != ""


func clue(name_: String) -> bool:
	return clues.has(name_)


func relation(name_: String) -> int:
	return rel.get(name_, 0)


func saved(ship: String) -> bool:
	return rescues.get(ship, "") == "saved"


func lost(ship: String) -> bool:
	return rescues.get(ship, "") == "lost"


func ship(name_: String) -> FleetShip:
	return sim.find_ship_named(name_) if sim else null


## The named ship is held in the hand-trained (MANUAL) beam right now.
func lit_by_hand(name_: String) -> bool:
	var s := ship(name_)
	return s != null and sim.mode == KeeperSim.Mode.MANUAL and sim.ship_sees_light(s)


func piloting(name_: String) -> bool:
	var s := ship(name_)
	return s != null and s.state == FleetShip.State.PILOTING


func done(conv: String) -> bool:
	return convs_done.has(conv)


## Evaluate a condition string, e.g.  has_flag("door_open") and relation("morag") > 0
## Station values: sim.battery, sim.gen, sim.mode ... (sim may be null in tests).
func eval(expr: String) -> bool:
	if expr.strip_edges() == "":
		return true
	var e := Expression.new()
	var err := e.parse(expr, ["sim"])
	if err != OK:
		push_error("story condition parse error: %s (%s)" % [expr, e.get_error_text()])
		return false
	var v = e.execute([sim], self)
	if e.has_execute_failed():
		push_error("story condition failed: %s" % expr)
		return false
	return bool(v)


func apply_action(action: String, args: Array) -> void:
	match action:
		"set":
			for a in args:
				var kv: PackedStringArray = String(a).split("=", true, 1)
				flags[kv[0]] = _val(kv[1]) if kv.size() > 1 else 1
		"unset":
			for a in args:
				flags.erase(a)
		"add":
			var key: String = args[0]
			var amt := int(args[1]) if args.size() > 1 else 1
			if key.begins_with("rel."):
				var who := key.substr(4)
				rel[who] = clampi(rel.get(who, 0) + amt, -3, 3)
			else:
				flags[key] = int(flags.get(key, 0)) + amt
		"clue":
			for a in args:
				clues[a] = true


func _val(s: String):
	if s.is_valid_int():
		return int(s)
	if s.is_valid_float():
		return float(s)
	if s == "true":
		return true
	if s == "false":
		return false
	return s


func to_dict() -> Dictionary:
	return {"chapter": chapter, "beat": beat, "flags": flags, "clues": clues.keys(), "rel": rel, "rescues": rescues,
		"convs_done": convs_done.keys(), "history": history.slice(-300), "objective": objective, "obj_done": obj_done, "play_seconds": play_seconds,
		"layout": LAYOUT, "in_beat": in_beat, "resume": resume, "duties": duties, "focus_duty": focus_duty,
		"log_written": log_written}


func from_dict(d: Dictionary) -> void:
	chapter = int(d.get("chapter", 1))
	beat = remap_beat(chapter, int(d.get("beat", 0)), int(d.get("layout", 1)))
	in_beat = bool(d.get("in_beat", false))
	resume = d.get("resume", [])
	flags = d.get("flags", {})
	clues = {}
	for c in d.get("clues", []):
		clues[c] = true
	rel = d.get("rel", rel)
	rescues = d.get("rescues", {})
	convs_done = {}
	for c in d.get("convs_done", []):
		convs_done[c] = true
	history = Speakers.sanitize_history(d.get("history", []), self)   # pre-3A saves stored raw ids ("ROSS")
	objective = d.get("objective", "")
	obj_done = []
	for i in d.get("obj_done", []):
		obj_done.append(int(i))
	play_seconds = float(d.get("play_seconds", 0.0))
	duties = {}
	var dd: Dictionary = d.get("duties", {})
	for id in dd:
		var e: Dictionary = dd[id]
		duties[String(id)] = {"s": int(e.get("s", DUTY_HIDDEN)), "known": Array(e.get("known", [])).map(func(x): return String(x)),
			"done": Array(e.get("done", [])).map(func(x): return String(x)),
			"dropped": Array(e.get("dropped", [])).map(func(x): return String(x)),
			"hinted": Array(e.get("hinted", [])).map(func(x): return String(x))}     # audit D8 (older saves: none)
	focus_duty = String(d.get("focus_duty", ""))
	log_written = Array(d.get("log_written", [])).map(func(x): return String(x))


## A beat index from a save made with an older chapters.json layout, in today's layout.
static func remap_beat(ch: int, b: int, layout: int) -> int:
	while layout < LAYOUT:                 # chained: a layout-1 save goes 1 -> 2 -> 3
		if REMAP.has(ch) and REMAP[ch].has(layout):
			var m: Array = REMAP[ch][layout]
			b = m[clampi(b, 0, m.size() - 1)] if b < m.size() else b - m.size() + int(m[-1]) + 1
		layout += 1
	return b
