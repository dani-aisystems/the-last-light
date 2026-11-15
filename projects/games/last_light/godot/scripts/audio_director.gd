extends Node
## Layered soundscape (all sounds synthesised by audio/synth.py).
##  Ambient (2D, storm-scaled): wind, rain on glass, sea.   Music bus: menu pad / tension drone.
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

var sim: KeeperSim
var station: Node3D
var loops := {}
var _streams := {}
var _menu := false
var _pending: Array = []        # [time, callable]
var _t := 0.0
var _static_t := 0.0
var _music: AudioStreamPlayer
var _lp: AudioEffectLowPassFilter
var _cutoff := MUFFLE_HZ
var _glass: Array = []          # amb_rain_glass players at the windows
var _rng := RandomNumberGenerator.new()
var _gust := 0.0
var _gust_target := 0.0
var _gust_next := 0.0
var _music_fade := 0.0          # > 0: fading the music out (set_menu(false))


var _lights_was := true                         # G2b: last frame's sim.lights_on() (no clack on a lit load)


func setup(k: KeeperSim, st: Node3D) -> void:
	sim = k
	station = st
	_rng.seed = 30
	_ensure_exterior_bus()
	for n in ["amb_wind", "amb_gust", "amb_rain", "amb_sea"]:
		loops[n] = _player2d(n, EXT_BUS, -8.0)
	_make_glass_layers()
	_music = _player2d("music_menu", "Music", -6.0, false)
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


## on: the attract menu (menu pad, storm heard from outside). off: fade the pad out and muffle again.
func set_menu(on: bool) -> void:
	_menu = on
	_cutoff = OPEN_HZ if on else MUFFLE_HZ
	if on:
		if _lp:
			_lp.cutoff_hz = _cutoff
		_music_fade = 0.0
		_music.stream = _looped("music_menu")
		_music.volume_db = -8.0
		_music.play()
	elif _music.playing:
		_music_fade = 2.0


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


func sfx_at(n: String, pos: Vector3, db := 0.0, unit := 3.0) -> void:
	var p := AudioStreamPlayer3D.new()
	p.stream = _stream(n)
	p.bus = "SFX"
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


func on_line(item: Dictionary) -> void:
	if item.get("look", item.get("mode", "")) == "radio":    # an in-room speaker in a radio scene is no transmission
		_static_t = maxf(_static_t, 3.5)


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
				_:
					if ResourceLoader.exists(A % n):
						sfx(n)
		"static":
			_static_t = 0.0 if (args.size() > 0 and args[0] == "fade") else (6.0 if args.size() > 0 and args[0] == "heavy" else 3.5)
		"music":
			_music_fade = 0.0
			_music.stream = _looped("music_tension" if args[0] == "tension" else "music_menu")
			_music.volume_db = -12.0
			_music.play()


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
			sfx_at("door_base", BASE_DOOR, 0.0, 10.0)
		"stair":
			# iron spiral stair: steps climb toward the door over ~12 s, a pause half way
			for i in 18:
				var delay := i * 0.62 + (2.5 if i > 9 else 0.0)
				var y := lerpf(6.0, 19.6, i / 17.0)
				_later(delay, func(): sfx_at("step_metal_%d" % (i % 4), Vector3(door.x, y, door.z) + Vector3(door.x, 0, door.z).normalized() * 0.6, lerpf(-14.0, -2.0, i / 17.0), 4.0))


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
	if _music_fade > 0.0:
		_music_fade = maxf(0.0, _music_fade - delta)
		_music.volume_db = lerpf(-60.0, -8.0, _music_fade / 2.0)
		if _music_fade == 0.0:
			_music.stop()
	if _lp:
		_lp.cutoff_hz = lerpf(_lp.cutoff_hz, _cutoff, minf(1.0, delta * 2.0))
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
	loops["static"].volume_db = lerpf(-80.0, -16.0 + 6.0 * storm, clampf(_static_t, 0.0, 1.0)) if sim.radio_on() else -80.0


## Gusts: a new target every few seconds (more often in a full storm), rising faster than they fall.
func _step_gust(delta: float, storm: float) -> void:
	if _t >= _gust_next:
		_gust_next = _t + _rng.randf_range(1.5, 5.0) * lerpf(1.6, 0.7, storm)
		_gust_target = pow(_rng.randf(), 1.5)
	_gust = move_toward(_gust, _gust_target, delta * (1.2 if _gust_target > _gust else 0.5))
