extends Node
## Layered soundscape (all sounds synthesised by audio/synth.py).
##  Ambient (2D, storm-scaled): wind, rain on glass, sea.   Music bus: the score (data/music_cues.json).
##  Positional (3D) in the room: generator (cage), electrical hum (power cabinet), clockwork (optic drive),
##  radio static (desk speaker), motor grind (ceiling gear).  Events: thunder (delayed after the flash),
##  switches, breaker, crank, horns, squelch/typewriter blips, and the visitor's approach:
##  steps on the jetty -> the base door far below -> iron steps up the stair -> three knocks.
##
## G5 / finding 30 (2026-11-06):
##  - exterior sounds (wind, gusts, roof rain, sea, thunder, horns) go through an "Exterior" bus that
##    sends into Ambient (so the Ambient slider still governs them) and carries a low-pass: in the
##    game the keeper hears the storm through stone and glass; in the attract menu (camera outside)
##    it opens up;
##  - the close rain on the glass (amb_rain_glass) is unmuffled and placed at the window bays;
##  - gusts: amb_gust follows a runtime gust envelope whose depth and rate follow the storm value;
##  - thunder: near strikes (< 700 m) use thunder_0..2, mid ones (< 1500 m) thunder_3..5, far ones
##    thunder_6..7 (R3, 2026-11-15: re-synthesised with a rolling body, an echo and a fade; each play is
##    pitched +-6 % so repeats never sound identical); the delay is the strike distance / 343 m/s
##    (KeeperSim / TitleStorm), and the level falls with distance.

const A := "res://assets/audio/%s.wav"
const EXT_BUS := "Exterior"
const MUFFLE_HZ := 2400.0          # indoors: the storm heard through the lantern glass and stone
const OPEN_HZ := 6500.0            # attract menu: the camera is outside (R3: was 20 kHz, which laid every
                                   # raindrop's top end bare; 6.5 kHz is open air heard through a downpour)
const NEAR_STRIKE_M := 700.0
const FAR_STRIKE_M := 1500.0
const GLASS_LAYERS := 3            # amb_rain_glass emitters, spread round the window bays
# audit Stage D (04 7.8, 05 18.4): what is heard from the stair comes through the stairwell (a reverb) and then
# the steel door (a low-pass that opens with the door's swing); the room itself gets a small reverb on SFX;
# radio static dips under a radio message on screen.
const STAIR_BUS := "Stair"
const DOOR_SHUT_HZ := 700.0
const DOOR_OPEN_HZ := 8000.0
const STATIC_DIP_DB := 6.0
const STATIC_DIP_S := 0.3

var sim: KeeperSim
var station: Node3D
var loops := {}
var _streams := {}
var _menu := false
var _pending: Array = []        # [time, callable]
var _t := 0.0
var _static_t := 0.0
var _music: AudioStreamPlayer      # the bed now playing (audit music: one of _beds)
var _lp: AudioEffectLowPassFilter
var _cutoff := MUFFLE_HZ
var _glass: Array = []          # amb_rain_glass players at the windows
var _rng := RandomNumberGenerator.new()
var _gust := 0.0
var _gust_target := 0.0
var _gust_next := 0.0
# audit music stage (F 23.8): the score. Two bed players crossfade; a layer plays over its bed (M04's restless
# layer); a stinger plays over the bed without stopping it (M08). Cue ids, files and kinds: CUES_PATH. The Music
# bus ducks DUCK_DB under any message on screen (an AudioEffectAmplify at the head of the bus, so the player's
# Music volume setting is untouched). From "docked" to the first stair footstep nothing may play (_hold).
const CUES_PATH := "res://data/music_cues.json"
const DUCK_DB := -8.0
const DUCK_IN_S := 0.4
const DUCK_OUT_S := 1.2
const SILENT_DB := -60.0
var cues := {}                  # the whole cue table (cues, title, credits, endings, legacy)
var _beds: Array = []           # two AudioStreamPlayers on Music
var _bed_i := 0
var _layer: AudioStreamPlayer
var _stinger: AudioStreamPlayer
var _fades := {}                # player -> [from_db, to_db, elapsed, length, stop_at_end]
var _cue := ""                  # the bed cue playing ("" none)
var _cue_t := 0.0
var _layers_on := {}            # layer cue ids that are on
var _hold := false              # the silence from "docked" to the first stair footstep
var _duck_fx: AudioEffectAmplify
var _duck_db := 0.0
var message_probe: Callable     # audit D: game_fp.message_on_screen (any line, thought, caption or subtitle)
var radio_probe: Callable       # audit D: game_fp.radio_message_on_screen (a radio line or a radio subtitle)
var _static_dip := 0.0          # 0..1: how far the static has dipped under a radio message
var _stair_lp: AudioEffectLowPassFilter
var visitor_probe: Callable     # audit D: where Ross stands (game_fp), Vector3.INF when he isn't in the room
var player_probe: Callable      # audit D: {"pos": Vector3, "walk": bool} for the keeper's own footsteps
var _last_cough := -1
var _breath_t := -99.0
var _stride := 0.0
var _last_pos := Vector3.INF
var _step_k := 0
const COUGHS := 8               # ross_cough_0..7 (recorded CC0, audio/recorded.py)
const BREATHS := 4
const STEPS_CONCRETE := 6
const STEPS_STAIR := 8
const STRIDE_M := 0.72          # the keeper's step, metres walked per footfall
const LANDING_M := 1.3          # within this of the stair door (horizontally) he is on the chequer plate


var _lights_was := true                         # G2b: last frame's sim.lights_on() (no clack on a lit load)


func setup(k: KeeperSim, st: Node3D) -> void:
	sim = k
	station = st
	_rng.seed = 30
	_ensure_exterior_bus()
	_ensure_stair_bus()
	_ensure_room_reverb()
	for n in ["amb_wind", "amb_gust", "amb_rain", "amb_sea"]:
		loops[n] = _player2d(n, EXT_BUS, -8.0)
	_make_glass_layers()
	_setup_music()
	loops["gen_idle"] = _player3d("gen_idle", _dev("IA_gen_panel", Vector3(-2.2, 20.6, 1.7)), 4.0)
	loops["hum"] = _player3d("hum", _dev("IA_power_panel", Vector3(-2.9, 21.2, 0.5)), 2.0)
	loops["clockwork"] = _player3d("clockwork", Vector3(1.9, 22.6, -1.9), 3.0)
	loops["static"] = _player3d("static", _dev("IA_radio", Vector3(0, 21.0, -2.8)), 2.0, "Dialogue")
	loops["motor_grind"] = _player3d("motor_grind", Vector3(0, 22.8, 0), 3.0)
	for n in ["gen_idle", "hum", "clockwork", "static", "motor_grind"]:
		loops[n].volume_db = -80.0
		loops[n].play()
	for n in ["amb_wind", "amb_gust", "amb_rain", "amb_sea"]:
		loops[n].play()


## The Exterior bus: created once (it survives scene reloads), sending into Ambient.
func _ensure_exterior_bus() -> void:
	var i := AudioServer.get_bus_index(EXT_BUS)
	if i == -1:
		AudioServer.add_bus()
		i = AudioServer.bus_count - 1
		AudioServer.set_bus_name(i, EXT_BUS)
		AudioServer.set_bus_send(i, "Ambient")
		var lp := AudioEffectLowPassFilter.new()
		lp.resonance = 0.5
		lp.db = AudioEffectFilter.FILTER_12DB
		AudioServer.add_bus_effect(i, lp)
	_lp = AudioServer.get_bus_effect(i, 0) as AudioEffectLowPassFilter
	_cutoff = OPEN_HZ if _menu else MUFFLE_HZ
	if _lp:
		_lp.cutoff_hz = _cutoff


## audit music: the players, the cue table and the duck on the Music bus.
func _setup_music() -> void:
	var f := FileAccess.open(CUES_PATH, FileAccess.READ)
	cues = JSON.parse_string(f.get_as_text()) if f else {}
	if not cues.has("cues"):
		cues = {"cues": {}}
	for i in 2:
		var p := AudioStreamPlayer.new()
		p.bus = "Music"
		p.volume_db = SILENT_DB
		add_child(p)
		_beds.append(p)
	_music = _beds[0]
	_layer = AudioStreamPlayer.new()
	_layer.bus = "Music"
	add_child(_layer)
	_stinger = AudioStreamPlayer.new()
	_stinger.bus = "Music"
	add_child(_stinger)
	var mi := AudioServer.get_bus_index("Music")
	if mi != -1:
		for k in AudioServer.get_bus_effect_count(mi):
			if AudioServer.get_bus_effect(mi, k) is AudioEffectAmplify:
				_duck_fx = AudioServer.get_bus_effect(mi, k)
		if _duck_fx == null:
			_duck_fx = AudioEffectAmplify.new()
			AudioServer.add_bus_effect(mi, _duck_fx, 0)
		_duck_fx.volume_db = 0.0


func cue_info(id: String) -> Dictionary:
	return cues.get("cues", {}).get(id, {})


## A cue's file: "name" is a synthesised WAV in assets/audio/; "score/m01.mp3" (with its extension) is one of
## Daniel's tracks built by audio/score.py.
func cue_file(id: String) -> String:
	var c := cue_info(id)
	if c.is_empty():
		return ""
	var f := String(c["file"])
	return ("res://assets/audio/" + f) if f.get_extension() != "" else (A % f)


func _cue_stream(id: String) -> AudioStream:
	var c := cue_info(id)
	var f := String(c["file"])
	if f.get_extension() == "":
		return _looped(f) if c.get("loop", false) else _stream(f)
	var s: AudioStream = load(cue_file(id))
	if s is AudioStreamMP3:
		s = s.duplicate()
		(s as AudioStreamMP3).loop = bool(c.get("loop", false))
		(s as AudioStreamMP3).loop_offset = 0.0
	return s


func _fade(p: AudioStreamPlayer, to_db: float, sec: float, stop := false) -> void:
	if sec <= 0.0:
		p.volume_db = to_db
		_fades.erase(p)
		if stop:
			p.stop()
		return
	_fades[p] = [p.volume_db, to_db, 0.0, sec, stop]


## Start a cue: a bed crossfades from the one playing (over `fade` s), a layer joins its bed, a stinger plays
## over everything. Refused (false) during the silence hold or for an unknown id. The same bed again is a no-op.
func play_cue(id: String, fade := 2.0) -> bool:
	if _hold:
		return false
	var c := cue_info(id)
	if c.is_empty():
		push_warning("music: unknown cue '%s'" % id)
		return false
	match String(c.get("kind", "bed")):
		"layer":
			return set_layer(id, true, fade)
		"stinger":
			_stinger.stream = _cue_stream(id)
			_stinger.volume_db = 0.0
			_stinger.play()
			return true
	if id == _cue and _music.playing:
		return true
	var old: AudioStreamPlayer = _beds[_bed_i]
	if old.playing:
		_fade(old, SILENT_DB, fade, true)
	for l in _layers_on.keys():
		set_layer(l, false, fade)
	_bed_i = 1 - _bed_i
	var nb: AudioStreamPlayer = _beds[_bed_i]
	nb.stream = _cue_stream(id)
	nb.volume_db = SILENT_DB if fade > 0.0 else 0.0
	nb.play()
	_fade(nb, 0.0, fade)
	_music = nb
	_cue = id
	_cue_t = 0.0
	return true


## Stop the bed and its layers (a stinger plays out).
func stop_cue(fade := 2.0) -> void:
	for b in _beds:
		if b.playing:
			_fade(b, SILENT_DB, fade, true)
	for l in _layers_on.keys():
		set_layer(l, false, fade)
	_cue = ""


func set_layer(id: String, on: bool, fade := 2.0) -> bool:
	var c := cue_info(id)
	if c.is_empty() or String(c.get("kind", "")) != "layer":
		return false
	if on:
		if _hold:
			return false
		if not _layers_on.has(id):
			_layer.stream = _cue_stream(id)
			_layer.volume_db = SILENT_DB if fade > 0.0 else 0.0
			_layer.play()
			_fade(_layer, 0.0, fade)
		_layers_on[id] = true
	elif _layers_on.has(id):
		_layers_on.erase(id)
		_fade(_layer, SILENT_DB, fade, true)
	return true


## The silence (F 23.2): from "docked" to the first footstep on the stair nothing plays.
func hold(on: bool, fade := 3.0) -> void:
	if on:
		stop_cue(fade)
	_hold = on


func current_cue() -> String:
	return _cue


## What a save keeps: the bed cue, its layers, and whether the silence holds (a stinger is never saved).
func cue_state() -> Dictionary:
	return {"cue": _cue, "layers": _layers_on.keys(), "hold": _hold}


## On load: the saved cue from the top with a 2 s fade (F 23.8), its layers, and the silence if it held.
func restore_cue(st: Dictionary, fade := 2.0) -> void:
	_hold = false
	stop_cue(0.0)
	var id := String(st.get("cue", ""))
	if id != "":
		play_cue(id, fade)
		for l in st.get("layers", []):
			set_layer(String(l), true, fade)
	_hold = bool(st.get("hold", false))


func _music_process(delta: float) -> void:
	for p in _fades.keys():
		var f: Array = _fades[p]
		f[2] += delta
		var k := clampf(f[2] / f[3], 0.0, 1.0)
		(p as AudioStreamPlayer).volume_db = lerpf(f[0], f[1], k)
		if k >= 1.0:
			_fades.erase(p)
			if f[4]:
				(p as AudioStreamPlayer).stop()
	if _cue != "":
		_cue_t += delta
		var c := cue_info(_cue)
		if c.has("max_s") and _cue_t > float(c["max_s"]):
			stop_cue(4.0)                        # M03 / M09: so long, then out
		elif not c.get("loop", false) and not _music.playing and not _fades.has(_music):
			_cue = ""                            # a once-through cue played out
	if _duck_fx:
		var msg: bool = message_probe.is_valid() and message_probe.call()
		_duck_db = move_toward(_duck_db, DUCK_DB if msg else 0.0, delta * absf(DUCK_DB) / (DUCK_IN_S if msg else DUCK_OUT_S))
		_duck_fx.volume_db = _duck_db


## audit D: the Stair bus (created once): the stairwell's reverb, then the steel door's low-pass, into SFX.
func _ensure_stair_bus() -> void:
	var i := AudioServer.get_bus_index(STAIR_BUS)
	if i == -1:
		AudioServer.add_bus()
		i = AudioServer.bus_count - 1
		AudioServer.set_bus_name(i, STAIR_BUS)
		AudioServer.set_bus_send(i, "SFX" if AudioServer.get_bus_index("SFX") != -1 else "Master")
		var rv := AudioEffectReverb.new()        # a tall, hard, round shaft of stone and iron
		rv.room_size = 0.75
		rv.damping = 0.5
		rv.spread = 0.8
		rv.hipass = 0.1
		rv.dry = 1.0
		rv.wet = 0.3
		rv.predelay_msec = 30.0
		AudioServer.add_bus_effect(i, rv)
		var lp := AudioEffectLowPassFilter.new() # the steel door
		lp.resonance = 0.5
		lp.db = AudioEffectFilter.FILTER_12DB
		lp.cutoff_hz = DOOR_SHUT_HZ
		AudioServer.add_bus_effect(i, lp)
	_stair_lp = AudioServer.get_bus_effect(i, 1) as AudioEffectLowPassFilter


## audit D: a small room reverb on SFX (the round watch room: stone, glass and steel), added once.
func _ensure_room_reverb() -> void:
	var i := AudioServer.get_bus_index("SFX")
	if i == -1:
		return
	for k in AudioServer.get_bus_effect_count(i):
		if AudioServer.get_bus_effect(i, k) is AudioEffectReverb:
			return
	var rv := AudioEffectReverb.new()
	rv.room_size = 0.32
	rv.damping = 0.6
	rv.spread = 0.6
	rv.hipass = 0.2
	rv.dry = 1.0
	rv.wet = 0.1
	rv.predelay_msec = 12.0
	AudioServer.add_bus_effect(i, rv)


## The Stair bus's door cutoff for a swing of 0 (shut) to 1 (open).
static func door_cutoff(swing: float) -> float:
	return lerpf(DOOR_SHUT_HZ, DOOR_OPEN_HZ, sqrt(clampf(swing, 0.0, 1.0)))


## The static's level: its envelope (_static_t) dipped by STATIC_DIP_DB while a radio message is on screen.
static func static_db(static_t: float, storm: float, dip: float, radio_on: bool) -> float:
	if not radio_on:
		return -80.0
	var base := lerpf(-80.0, -16.0 + 6.0 * storm, clampf(static_t, 0.0, 1.0))
	return maxf(-80.0, base - STATIC_DIP_DB * clampf(dip, 0.0, 1.0))


## audit D: paper in the keeper's hands: the slide as a document opens (or turns a page), a softer lay-down
## as it closes.
func paper(opening: bool) -> void:
	sfx("paper_slide" if opening else "paper_close", -8.0 if opening else -6.0)


## audit D (7.8): one of Ross's coughs, never the same take twice running.
func cough_take() -> int:
	var k := _rng.randi_range(0, COUGHS - 2)
	if k >= _last_cough and _last_cough >= 0:
		k += 1
	_last_cough = k
	return k


## A fit of n coughs at pos ("it goes on a long time"), through the stairwell and the door when he is outside.
func cough_fit(n: int, pos: Vector3, bus := "SFX", db := -4.0) -> void:
	var at := 0.0
	for i in n:
		var k := cough_take()
		_later(at, func(): sfx_at("ross_cough_%d" % k, pos, db - 1.5 * i, 3.0, bus))
		at += _rng.randf_range(0.7, 1.4)


## Where a cough or a breath of Ross's comes from: his figure in the room, else the far side of the door.
func _ross_source() -> Array:
	var p: Vector3 = visitor_probe.call() if visitor_probe.is_valid() else Vector3.INF
	if p != Vector3.INF:
		return [p + Vector3(0, 1.6, 0), "SFX"]
	var d: Vector3 = station.door_position() if station else Vector3(0, 20.0, 0)
	return [d + Vector3(d.x, 0, d.z).normalized() * 0.8 + Vector3(0, 1.4, 0), STAIR_BUS]


## The phone: the handset lifted, then the dead line.
func phone() -> void:
	var p := _dev("IA_phone", Vector3(-1.5, 21.0, -2.6))
	sfx_at("phone_lift", p, -6.0, 2.0)
	_later(0.6, func(): sfx_at("phone_dead", p, -10.0, 1.5))


func drawer() -> void:
	sfx_at("drawer_slide", _dev("IA_drawer", Vector3(0.4, 20.6, -2.6)), -4.0, 2.0)


## The Primus lit under the kettle: it comes to the boil (the kettle's own position).
func kettle() -> void:
	sfx_at("kettle_boil", _dev("IA_primus", Vector3(2.4, 20.9, 1.6)), -10.0, 2.0)


## The keeper's own footsteps (audit D, 7.8): one per STRIDE_M walked in free walk; steel on the chequer-plate
## landing by the stair door, concrete elsewhere in the room.
func _keeper_steps() -> void:
	if not player_probe.is_valid():
		return
	var st: Dictionary = player_probe.call()
	var pos: Vector3 = st.get("pos", Vector3.INF)
	if not st.get("walk", false) or pos == Vector3.INF:
		_last_pos = Vector3.INF
		return
	if _last_pos != Vector3.INF:
		var d := Vector2(pos.x - _last_pos.x, pos.z - _last_pos.z).length()
		if d < 1.0:                              # a teleport (a load, a test) is not a step
			_stride += d
	_last_pos = pos
	if _stride < STRIDE_M:
		return
	_stride = 0.0
	_step_k += 1
	var door: Vector3 = station.door_position() if station else Vector3.INF
	var landing := door != Vector3.INF and Vector2(pos.x - door.x, pos.z - door.z).length() < LANDING_M
	if landing:
		sfx("step_stair_%d" % (_step_k % STEPS_STAIR), -21.0, "SFX", _rng.randf_range(0.95, 1.05))
	else:
		sfx("step_concrete_%d" % (_step_k % STEPS_CONCRETE), -19.0, "SFX", _rng.randf_range(0.95, 1.05))


## Rain on the glass, at up to GLASS_LAYERS window bays, each started at a different offset so the
## emitters never repeat together. Falls back to one 2D player if the room has no windows.
func _make_glass_layers() -> void:
	var wins: Array = []
	var room: Node3D = station.get("room") if station else null
	if room:
		for mi in room.find_children("GLS_window*", "MeshInstance3D", true, false):
			wins.append((mi.global_transform * (mi as MeshInstance3D).get_aabb()).get_center())
	if wins.is_empty():
		_glass.append(_player2d("amb_rain_glass", "Ambient", -12.0))
	else:
		var n := mini(GLASS_LAYERS, wins.size())
		for k in n:
			_glass.append(_player3d("amb_rain_glass", wins[(k * wins.size()) / n], 2.5, "Ambient"))
	var length: float = _stream("amb_rain_glass").get_length()
	for k in _glass.size():
		_glass[k].play(length * float(k) / float(_glass.size()))


## Where a device sits in the room (its IA_ node), so its loop comes from the right place.
func _dev(name_: String, fallback: Vector3) -> Vector3:
	var room: Node3D = station.get("room") if station else null
	if room:
		var n := room.find_child(name_, true, false)
		if n is Node3D:
			return (n as Node3D).global_position
	return fallback


func _stream(n: String) -> AudioStream:
	if not _streams.has(n):
		var s: AudioStream = load(A % n)
		_streams[n] = s
	return _streams[n]


func _looped(n: String) -> AudioStream:
	var s: AudioStreamWAV = _stream(n).duplicate()
	s.loop_mode = AudioStreamWAV.LOOP_FORWARD
	s.loop_begin = 0
	s.loop_end = int(s.get_length() * s.mix_rate)
	return s


func _player2d(n: String, bus: String, db: float, loop := true) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.stream = _looped(n) if loop else _stream(n)
	p.bus = bus
	p.volume_db = db
	add_child(p)
	return p


func _player3d(n: String, pos: Vector3, unit: float, bus := "SFX") -> AudioStreamPlayer3D:
	var p := AudioStreamPlayer3D.new()
	p.stream = _looped(n)
	p.bus = bus
	p.unit_size = unit
	p.max_distance = 30.0
	add_child(p)
	p.global_position = pos
	return p


## on: the attract menu (menu pad, storm heard from outside). off: fade the pad out (from where it is, over
## fade_s; audit D: main_fp now calls this as New Game / Continue starts) and muffle again.
func set_menu(on: bool, fade_s := 2.0) -> void:
	_menu = on
	_cutoff = OPEN_HZ if on else MUFFLE_HZ
	if on:
		if _lp:
			_lp.cutoff_hz = _cutoff
		play_cue(String(cues.get("title", "M01")), 0.0)
	else:
		stop_cue(maxf(0.05, fade_s))


## R3: which thunder recording a strike at d metres gets (near 0-2, mid 3-5, far 6-7, varied at random).
static func thunder_variant(d: float) -> int:
	if d < NEAR_STRIKE_M:
		return randi_range(0, 2)
	if d < FAR_STRIKE_M:
		return randi_range(3, 5)
	return randi_range(6, 7)


## One-shot (2D unless pos given).
func sfx(n: String, db := 0.0, bus := "SFX", pitch := 1.0) -> void:
	var p := AudioStreamPlayer.new()
	p.stream = _stream(n)
	p.bus = bus
	p.volume_db = db
	p.pitch_scale = pitch
	add_child(p)
	p.play()
	p.finished.connect(p.queue_free)


func sfx_at(n: String, pos: Vector3, db := 0.0, unit := 3.0, bus := "SFX") -> void:
	var p := AudioStreamPlayer3D.new()
	p.stream = _stream(n)
	p.bus = bus
	p.volume_db = db
	p.unit_size = unit
	add_child(p)
	p.global_position = pos
	p.play()
	p.finished.connect(p.queue_free)


func _later(sec: float, f: Callable) -> void:
	_pending.append([_t + sec, f])


# ------------------------------------------------------------------ hooks

func on_events(events: Array) -> void:
	for e in events:
		match e["type"]:
			"lightning":
				var p: float = e.get("power", 0.7)
				var delay: float = e.get("thunder_delay", 1.0)
				var d: float = e.get("distance", delay * 343.0)
				var k := thunder_variant(d)
				var db := lerpf(-10.0, 0.0, p) - 10.0 * log(d / 400.0) / log(10.0)   # about -3.5 dB at 900 m
				var pitch := randf_range(0.94, 1.06)
				_later(delay, func(): sfx("thunder_%d" % k, db, EXT_BUS, pitch))
			"click":
				var dev: String = e["device"]
				sfx("click_knob" if dev in ["mode", "intensity"] else ("click_button" if dev == "start" else "click_switch"), -4.0)
			"breaker_trip":
				sfx("breaker_trip", 0.0)
			"gen_crank":
				# G2b: with the valve shut (or the tank dry) the whole attempt is one sound that never catches
				var dry: bool = sim != null and (not sim.fuel_valve or sim.fuel <= 0.0)
				sfx_at("gen_crank_dry" if dry else "gen_crank", loops["gen_idle"].global_position, 0.0)
			"gen_start":
				sfx_at("gen_catch", loops["gen_idle"].global_position, -1.0)      # G2b: she catches
			"torch":
				sfx("torch_click", -12.0)                                          # G2b: the torch switch
			"equip":
				sfx("torch_click", -16.0)                                          # G3a: compass / glasses in hand
			"gen_stop", "gen_overheat":
				sfx_at("gen_stop", loops["gen_idle"].global_position, -2.0)
			"ship_spawned":
				var s := sim.find_ship(e["ship"])
				if s and not s.unlit:
					_later(1.5, func(): sfx("horn_ship" if s.kind == "steamer" else "horn_fishing", -14.0, EXT_BUS))
			"radio", "tx":
				_static_t = 2.5
				sfx("squelch", -8.0, "Dialogue")
			"bowl_drained":                                                      # audit D: the drain cock
				sfx_at("bowl_drain", _dev("IA_sediment_bowl", Vector3(-2.0, 20.4, 1.9)), -4.0, 2.0)


func on_line(item: Dictionary) -> void:
	if item.get("look", item.get("mode", "")) == "radio":    # an in-room speaker in a radio scene is no transmission
		_static_t = maxf(_static_t, 3.5)
	# audit D (7.8): Ross. A stage direction that has him cough plays a fit; between his own lines, now and then,
	# a tired breath (never two within 6 s). Through the door while he is outside it.
	var text := String(item.get("text", ""))
	var who := String(item.get("speaker", ""))
	if item.get("line_kind", "") == "sound" and text.contains("He coughs"):
		var src := _ross_source()
		cough_fit(3, src[0], src[1])
	elif who in ["VISITOR", "ROSS"] and _t - _breath_t > 6.0 and _rng.randf() < 0.5:
		_breath_t = _t
		var src2 := _ross_source()
		var k := _rng.randi_range(0, BREATHS - 1)
		_later(0.2, func(): sfx_at("ross_breath_%d" % k, src2[0], -4.0, 2.0, src2[1]))


func ui_blip(kind: String) -> void:
	match kind:
		"char":
			sfx("blip", -14.0, "Dialogue")
		"squelch":
			sfx("squelch", -10.0, "Dialogue")


func story_cue(name_: String, args: Array) -> void:
	match name_:
		"sfx":
			var n: String = args[0]
			match n:
				"static_burst":
					_static_t = 3.0
					sfx("squelch", -2.0, "Dialogue")
				"silence":
					_duck = 1.0
				"paper_slide":
					sfx_at("paper_slide", station.door_position(), -2.0, 2.0)
				"carrier_click":
					sfx("carrier_click", -6.0, "Dialogue")
					_static_t = maxf(_static_t, 1.0)
				"ross_cough":                    # audit D: on the stair, deep in the chest, a long time
					var d: Vector3 = station.door_position()
					cough_fit(4, Vector3(d.x * 1.6, d.y - 6.0, d.z * 1.6), STAIR_BUS, -2.0)
				"teleprinter":                   # audit D: the 2200 sheet coming through
					sfx_at("teleprinter", _dev("IA_forecast", Vector3(2.6, 21.0, -1.4)), -8.0, 2.5)
				_:
					if ResourceLoader.exists(A % n):
						sfx(n)
		"static":
			_static_t = 0.0 if (args.size() > 0 and args[0] == "fade") else (6.0 if args.size() > 0 and args[0] == "heavy" else 3.5)
		"music":                                 # ["music", id, fade?] (F 23.8)
			var id := String(args[0]) if args.size() > 0 else ""
			id = String(cues.get("legacy", {}).get(id, id))
			play_cue(id, float(args[1]) if args.size() > 1 else 2.0)
		"music_stop":                            # ["music_stop", fade?, "hold"?]: "hold" starts the silence
			var fd := float(args[0]) if args.size() > 0 else 2.0
			if "hold" in args:
				hold(true, fd)
			else:
				stop_cue(fd)


var _duck := 0.0


func knock(door: Vector3) -> void:
	for i in 3:
		_later(i * 1.15, func(): sfx_at("knock", door + Vector3(0, 1.3, 0), 2.0, 4.0))


## G6d: the base door faces the landing (blender/spec.py tower.door.bearing 35, the porch front 6.0 m out,
## Godot north = -Z): the visitor walks up from the pier head to it. regress R22 checks it against the GLB.
const BASE_DOOR_BEARING := 35.0
const BASE_DOOR := Vector3(6.0 * 0.5736, 4.0, -6.0 * 0.8192)   # sin / cos 35


## The visitor's approach, placed in space: jetty (north-east below), base door (deep below), stair.
func footsteps(stage: String, door: Vector3) -> void:
	match stage:
		"jetty":
			var p := Vector3(11.3, 2.0, -21.2)
			for i in 10:
				_later(i * 0.62, func(): sfx_at("step_metal_%d" % (i % 4), p.lerp(BASE_DOOR + Vector3(0, -0.5, 0), i / 10.0), -10.0, 8.0))
		"base_door":
			sfx_at("door_base", BASE_DOOR, 0.0, 10.0, STAIR_BUS)
		"stair":
			_hold = false                        # audit music: the first footstep ends the silence
			# iron spiral stair: steps climb toward the door over ~12 s, a pause half way
			for i in 18:
				var delay := i * 0.62 + (2.5 if i > 9 else 0.0)
				var y := lerpf(6.0, 19.6, i / 17.0)
				_later(delay, func(): sfx_at("step_stair_%d" % (i % STEPS_STAIR), Vector3(door.x, y, door.z) + Vector3(door.x, 0, door.z).normalized() * 0.6, lerpf(-14.0, -2.0, i / 17.0), 4.0, STAIR_BUS))


func _process(delta: float) -> void:
	_t += delta
	if sim and loops.has("hum"):                 # G2b: the lighting contactor pulls in as the room lights come on
		var lit := sim.lights_on()
		if lit and not _lights_was and _t > 1.0:
			sfx_at("relay_clack", loops["hum"].global_position, -4.0)
		_lights_was = lit
	var keep: Array = []
	for p in _pending:
		if _t >= p[0]:
			p[1].call()
		else:
			keep.append(p)
	_pending = keep
	_keeper_steps()
	_music_process(delta)
	if _lp:
		_lp.cutoff_hz = lerpf(_lp.cutoff_hz, _cutoff, minf(1.0, delta * 2.0))
	if _stair_lp and station and station.has_method("door_phase"):
		_stair_lp.cutoff_hz = lerpf(_stair_lp.cutoff_hz, door_cutoff(station.door_phase().y), minf(1.0, delta * 8.0))
	if sim == null:
		return
	var storm := sim.storm
	_duck = maxf(0.0, _duck - delta * 0.12)
	var duck_db := -24.0 * _duck
	_step_gust(delta, storm)
	loops["amb_wind"].volume_db = lerpf(-18.0, -4.0, storm) + 2.0 * _gust + duck_db
	loops["amb_gust"].volume_db = linear_to_db(maxf(0.0005, _gust * lerpf(0.15, 1.0, storm))) - 6.0 + duck_db
	loops["amb_rain"].volume_db = lerpf(-20.0, -6.0, storm) + duck_db
	for g in _glass:
		g.volume_db = lerpf(-26.0, -8.0, storm) + duck_db
	loops["amb_sea"].volume_db = lerpf(-16.0, -6.0, storm) + duck_db
	loops["gen_idle"].volume_db = (-2.0 if sim.gen == KeeperSim.Gen.RUNNING else -80.0)
	loops["hum"].volume_db = -10.0 if sim.powered() else -80.0
	loops["clockwork"].volume_db = -8.0 if (sim.motor_on() and not sim.jammed) or sim.mode == KeeperSim.Mode.MANUAL and absf(sim._manual_vel) > 0.01 else -80.0
	loops["motor_grind"].volume_db = -2.0 if sim.jammed and sim.motor_on() else -80.0
	_static_t = maxf(0.0, _static_t - delta)
	var radio_msg: bool = radio_probe.is_valid() and radio_probe.call()
	_static_dip = move_toward(_static_dip, 1.0 if radio_msg else 0.0, delta / STATIC_DIP_S)
	loops["static"].volume_db = static_db(_static_t, storm, _static_dip, sim.radio_on())


## Gusts: a new target every few seconds (more often in a full storm), rising faster than they fall.
func _step_gust(delta: float, storm: float) -> void:
	if _t >= _gust_next:
		_gust_next = _t + _rng.randf_range(1.5, 5.0) * lerpf(1.6, 0.7, storm)
		_gust_target = pow(_rng.randf(), 1.5)
	_gust = move_toward(_gust, _gust_target, delta * (1.2 if _gust_target > _gust else 0.5))
