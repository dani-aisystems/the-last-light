#!/bin/zsh
# Bot campaign at real wait lengths and per-line UI timing. Output: out/realtime.txt (one REALTIME line per run).
# A run that does not reach the ending (the headless bot occasionally stalls in chapter 6 when the machine is
# busy) is logged as REALTIME_STUCK and retried up to 3 times; only ended=true lines are used by the model.
cd "$(dirname "$0")/../../../.." || exit 1
OUT="competitions/john-atanasoff/build/playtime/out/realtime.txt"
[[ "$1" == "--append" ]] || : > "$OUT"
run() {
  for attempt in 1 2 3; do
    res=$(taskpolicy -b tools/godot --headless --path projects/games/last_light/godot \
      -s "$PWD/competitions/john-atanasoff/build/playtime/realtime_campaign.gd" -- "$@" 2>&1 | grep -E '^REALTIME')
    echo "$res" >> "$OUT"
    echo "$res" | grep -q 'ended=true' && return
  done
}
# The two "lost" routes (idle bot in chapter 6) are NOT run at real wait lengths: the idle station burns all its
# fuel and the bot stalls (REALTIME_STUCK ... fuel=0, observed 3x each). Those endings are bounded by the saved routes.
[[ "$1" == "--append" ]] || for route in truth_saved lie_saved; do run --route=$route --choice=8 --mul=1.0; done
run --route=truth_saved --choice=5  --mul=1.0
run --route=truth_saved --choice=15 --mul=1.0
run --route=truth_saved --choice=8  --mul=1.5
run --route=truth_saved --choice=8  --mul=2.0
echo DONE >> "$OUT"
