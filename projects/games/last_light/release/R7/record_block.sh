#!/usr/bin/env bash
# THE LAST LIGHT release R7: every windowed Movie Maker / capture run in one sequential block (one window at a
# time, silent, never focused). Each recording is gated: Movie Maker's drawn-frame count must equal the AVI's
# packet count (an occluded window draws nothing and would repeat stale frames).
#   record_block.sh endings|reel|ch1|shots|all
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../../../../.." && pwd)"
ws="$root"
R7="$ws/renders/last_light/r7"
what="${1:-all}"

guard() {
  local front
  front=$(osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true' 2>/dev/null)
  if [[ "$front" == *Brave* || "$front" == *Chrome* ]]; then
    osascript -e 'tell application "System Events" to set frontmost of process "Electron" to true' 2>/dev/null
  fi
}

gate() {   # gate AVI LOG -> 0 if every written frame was drawn
  local n pk
  n=$(grep -o '^[0-9]* frames at 30 FPS' "$2" | grep -o '^[0-9]*')
  pk=$(ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of csv=p=0 "$1" 2>/dev/null)
  echo "gate $(basename "$1"): drawn=$n written=$pk"
  [[ -n "$n" && "$n" == "$pk" ]]
}

if [[ "$what" == endings || "$what" == all ]]; then
  for e in light_exhibited correction; do
    avi="$R7/endings/$e.avi"; log="$R7/endings/$e.log"
    [[ -e "$R7/endings/TheLastLight_Ending_${e}.ok" ]] && continue
    for attempt in 1 2; do
      guard
      (cd "$root" && tools/godot_bg --write-movie "$avi" --fixed-fps 30 --path projects/games/last_light/godot \
        -- --capture=film --film --film_ending=$e --film_credits=90 --audio) > "$log" 2>&1
      if gate "$avi" "$log"; then touch "$R7/endings/TheLastLight_Ending_${e}.ok"; echo "OK ending $e"; break; fi
      echo "RETRY ending $e (attempt $attempt failed the gate)"; mv "$log" "$R7/endings/bad_occluded/${e}_gate_fail_$attempt.log"; rm -f "$avi"
    done
  done
fi

if [[ "$what" == reel || "$what" == all ]]; then
  bash "$here/trailer/record_reel.sh" "$here/trailer/reel_shots.txt" "$R7/reel"
fi

if [[ "$what" == ch1 || "$what" == all ]]; then
  avi="$R7/gameplay/ch1_film.avi"; log="$R7/gameplay/ch1_film.log"; mkdir -p "$R7/gameplay"
  if [[ ! -e "$R7/gameplay/ch1_film.ok" ]]; then
    guard
    (cd "$root" && tools/godot_bg --write-movie "$avi" --fixed-fps 30 --path projects/games/last_light/godot \
      -- --capture=film --film --audio --quality=2) > "$log" 2>&1
    gate "$avi" "$log" && touch "$R7/gameplay/ch1_film.ok" && echo "OK ch1 film"
  fi
fi

if [[ "$what" == shots || "$what" == all ]]; then
  out="$R7/screens"; mkdir -p "$out"
  run_cap() {   # name, extra args...
    local name="$1"; shift
    guard
    (cd "$root" && tools/godot_bg --path projects/games/last_light/godot -- --capture="$name" --win=1920x1080 \
      --quality=2 "$@") > "$out/$name.log" 2>&1
    echo "capture $name exit $?"
  }
  run_cap r7s_scenic --nohud \
    "--shots=tmenu,tmenu@47!focus=new_game,tmenu@90!hide!bolt,tmenu!hide!view=ext_landing,40@fp_window,60@fp_desk,120@fp_window!storm_full!bolt,130@cu_optic!storm_80,140@cu_lamp!storm_80,150@fp_desk!dawn,160@fp_window!dawn"
  run_cap r7s_ui \
    "--shots=66@focus_radio!say_radio,90@pp_radio!take_kit!binoculars!face_north!pitch_m10!storm_80!vessel_iona_star_700,100@pp_start!gen_off!valve_shut,110@focus_console~mode,120@player!ending_heard_together,121@player!ending_correction" \
    --ending_steps=p4
  run_cap r7s_door --nohud --bot=expert "--shots=2010@fp_stair,2020@fp_stair,2035@fp_stair"
  # the PNGs land in the worktree's renders/ (capture_fp writes next to the project): collect them
  mkdir -p "$out/png"; find "$root/renders" -name 'r7s_*.png' -exec mv {} "$out/png/" \; 2>/dev/null
fi
echo "BLOCK_RESULT done ($what)"
