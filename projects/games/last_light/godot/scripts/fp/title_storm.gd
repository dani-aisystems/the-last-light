class_name TitleStorm
extends RefCounted
## G6d stage D: the title screen's weather, the middle watch at its worst (canon: ch4, 02:21, 14-15 Nov
## 1971, a south-west gale at storm 0.75). Attract mode only: game_fp holds the sim's storm at STORM, drops
## the sim's own lightning (its strikes are spread round the north for the watch-room windows, behind the
## title camera) and routes these events instead. The story's weather never comes through here.
##
## Lightning: gaps of about 4-14 s, skewed short with a long tail, never regular (a gap never repeats the
## last one within REPEAT_S), never under GAP_MIN_S. The mix is mostly distant flickers, some sheet flashes
## in the cloud, and now and then a bolt whose flash lights the island. Reduce flashing: no bolts (the
## flash itself is scaled x0.3 in outside.gd as everywhere). Reduce motion: the cadence slows by CALM_MUL.

const STORM := 0.75
## Toward the north-east (a gale FROM the south-west), m/s of drift given to rain and spray.
const WIND := Vector3(0.7071, 0.0, -0.7071) * 12.0
const RAIN_FALL := 15.0                      # m/s: heavy rain, read as streaks
const GAP_MIN_S := 4.0
const GAP_MAX_S := 14.0
const REPEAT_S := 0.9                        # a gap differs from the one before by at least this much
const CALM_MUL := 1.6                        # Reduce motion: every gap (and the floor) this much longer
const MIX := {"flicker": 0.58, "sheet": 0.29, "bolt": 0.13}
const BOLT_EVERY_MAX := 7                    # a bolt at least every few events, so it never goes stale
## Where the title camera looks (bearings from the island, radians): the bolts stand right of the menu
## column, behind and beside the tower; flickers and sheets anywhere in the southern sky.
const BOLT_BEARINGS := Vector2(deg_to_rad(194.0), deg_to_rad(214.0))   # x ~0.66-0.95 of a 16:9 title
const SKY_BEARINGS := Vector2(deg_to_rad(120.0), deg_to_rad(250.0))

var rng := RandomNumberGenerator.new()
var reduce_flashing := false
var reduce_motion := false
var t := 0.0
var next_t := 2.5                            # the first event soon after the menu comes up
var last_gap := 0.0
var since_bolt := 0
var gaps: Array[float] = []                  # history for tests and QA
var kinds: Array[String] = []
var _pulses: Array = []                      # [time, event] follow-up pulses of a flash in progress


func _init(seed_value := 0) -> void:
	rng.seed = seed_value


## The next gap in seconds. A skewed draw (most gaps 5-9 s, a tail toward 14), re-drawn if it would repeat
## the last gap, then floored; Reduce motion stretches it.
func next_gap() -> float:
	var g := 0.0
	var last := last_gap / (CALM_MUL if reduce_motion else 1.0)
	for _i in 6:
		var u := rng.randf()
		g = lerpf(GAP_MIN_S, GAP_MAX_S, pow(u, 1.7))
		if last == 0.0 or absf(g - last) >= REPEAT_S:
			break
	if last != 0.0 and absf(g - last) < REPEAT_S:      # still too alike: step clear of it, inside the range
		g = last + REPEAT_S if last + REPEAT_S <= GAP_MAX_S else last - REPEAT_S
	g = clampf(g, GAP_MIN_S, GAP_MAX_S)
	if reduce_motion:
		g *= CALM_MUL
	last_gap = g
	return g


func pick_kind() -> String:
	if since_bolt >= BOLT_EVERY_MAX and not reduce_flashing:
		return "bolt"
	var u := rng.randf()
	var k := "flicker"
	if u > MIX["flicker"] + MIX["sheet"]:
		k = "bolt"
	elif u > MIX["flicker"]:
		k = "sheet"
	if k == "bolt" and reduce_flashing:
		k = "sheet"                           # no bolts: the strongest event is a sheet flash
	return k


## One lightning event of a kind. Bearings in radians (Geo). "bolt" decides whether a bolt is drawn;
## "light" scales the flash's directional light (bolts light the island, flickers barely do); a flash can
## come with quick follow-up pulses (event type "lightning_pulse": the flash only, no thunder).
func make_event(kind: String) -> Dictionary:
	var e := {"type": "lightning", "kind": kind, "bolt": kind == "bolt", "title": true}
	match kind:
		"flicker":
			e["power"] = rng.randf_range(0.22, 0.42)
			e["distance"] = rng.randf_range(1600.0, 3200.0)
			e["bearing"] = rng.randf_range(SKY_BEARINGS.x, SKY_BEARINGS.y)
			e["light"] = 0.35
		"sheet":
			e["power"] = rng.randf_range(0.5, 0.75)
			e["distance"] = rng.randf_range(900.0, 1800.0)
			e["bearing"] = rng.randf_range(SKY_BEARINGS.x, SKY_BEARINGS.y)
			e["light"] = 0.8
		_:
			e["power"] = rng.randf_range(0.9, 1.0)
			e["distance"] = rng.randf_range(520.0, 880.0)
			e["bearing"] = rng.randf_range(BOLT_BEARINGS.x, BOLT_BEARINGS.y)
			e["light"] = 1.7
	e["thunder_delay"] = float(e["distance"]) / 343.0
	return e


## Advance by dt; returns the events due (a "lightning" event per strike, plus its pulses).
func step(dt: float) -> Array:
	t += dt
	var out: Array = []
	var keep: Array = []
	for p in _pulses:
		if t >= p[0]:
			out.append(p[1])
		else:
			keep.append(p)
	_pulses = keep
	if t >= next_t:
		var gap := next_gap()
		gaps.append(gap)
		next_t = t + gap
		var kind := pick_kind()
		kinds.append(kind)
		since_bolt = 0 if kind == "bolt" else since_bolt + 1
		var e := make_event(kind)
		out.append(e)
		# a flash is rarely one pulse: a flicker stutters, a sheet glows twice or three times in the cloud
		var n := 0
		match kind:
			"flicker":
				n = rng.randi_range(0, 2)
			"sheet":
				n = rng.randi_range(1, 3)
			_:
				n = rng.randi_range(0, 1)
		var at := t
		for _i in n:
			at += rng.randf_range(0.09, 0.32)
			_pulses.append([at, {"type": "lightning_pulse", "power": float(e["power"]) * rng.randf_range(0.45, 0.85),
				"bearing": e["bearing"], "light": e["light"], "title": true}])
	return out


## A bolt now (captures: the mid-bolt still). Ignores the schedule; Reduce flashing still wins.
func force_bolt() -> Array:
	var e := make_event("sheet" if reduce_flashing else "bolt")
	kinds.append(String(e["kind"]))
	return [e]
