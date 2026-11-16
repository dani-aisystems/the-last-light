extends Node
## Autoload: session-only state (personal best this session) and run settings from the command line.

var best_score := 0
var best_rescued := 0
var games_played := 0
var last_result: Dictionary = {}
var seed_override := -1
var user_args := {}
var prof := {}          # name -> accumulated usec (perf investigation)


func prof_add(name_: String, usec: int) -> void:
	prof[name_] = prof.get(name_, 0) + usec


func _ready() -> void:
	InputSetup.ensure()
	if not dev_flags_allowed():
		return                                # audit D9: a release build ignores every -- flag
	for a in OS.get_cmdline_user_args():
		var kv := a.trim_prefix("--").split("=", true, 1)
		user_args[kv[0]] = kv[1] if kv.size() > 1 else "1"
	if user_args.has("seed"):
		seed_override = int(user_args["seed"])


## Audit D9 (2026-11-16): the developer flags (--capture, --autotest, --bot, --bench, --load, --seed, ...)
## work only in the editor and debug exports. A release export (template_release) is not a debug build,
## so a player's command line can't start the test bot, jump to a save slot or turn on captures.
static func dev_flags_allowed() -> bool:
	return OS.is_debug_build()


func reset_session() -> void:
	best_score = 0
	best_rescued = 0
	games_played = 0
	last_result = {}


## Returns true if this is a new personal best.
func record_result(stats: Dictionary) -> bool:
	games_played += 1
	last_result = stats
	var is_best: bool = stats.get("score", 0) > best_score
	best_score = maxi(best_score, stats.get("score", 0))
	best_rescued = maxi(best_rescued, stats.get("rescued", 0))
	return is_best


func next_seed() -> int:
	if seed_override >= 0:
		return seed_override
	return int(Time.get_unix_time_from_system()) % 100000 + games_played
