#!/usr/bin/env bash
# THE LAST LIGHT release R7: record the trailer's in-engine shots with Godot's Movie Maker (film_fp.gd
# --film_reel), one Godot run per shot, then keep only the roll as a CRF 12 clip.
#   record_reel.sh SHOTS_FILE OUT_DIR [only_name ...]
# SHOTS_FILE lines:  name | --film_reel=... [more film args]      (# comments and blank lines skipped)
# Every recording is checked: Movie Maker's "N frames" must equal the AVI's packet count. A covered (occluded)
# window makes Godot skip drawing, and Movie Maker then repeats stale frames (seen in R7's first ending
# runs), so a mismatch fails the shot and keeps its log.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../../../../../.." && pwd)"        # the worktree / workspace root (tools/ lives here)
shots="$1"; out="$2"; shift 2
only=("$@")
mkdir -p "$out"
fails=0
while IFS='|' read -r -u 3 name args; do       # fd 3: Godot's launcher must not read the shot list (stdin)
  name="$(echo "$name" | xargs)"; args="$(echo "$args" | xargs)"
  [[ -z "$name" || "$name" == \#* ]] && continue
  if (( ${#only[@]} )) && [[ ! " ${only[*]} " == *" $name "* ]]; then continue; fi
  avi="$out/$name.avi"; log="$out/$name.log"; clip="$out/$name.mp4"
  [[ -e "$clip" ]] && { echo "skip $name (exists)"; continue; }
  # A maximised browser in front occludes the Godot window and Movie Maker then repeats stale frames
  # (R7: proven by an A/B, 483 of 1323 frames drawn with Brave in front, 1323 of 1323 with the IDE in front).
  front=$(osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true' 2>/dev/null)
  if [[ "$front" == *Brave* || "$front" == *Chrome* ]]; then
    osascript -e 'tell application "System Events" to set frontmost of process "Electron" to true' 2>/dev/null
  fi
  # shellcheck disable=SC2086
  (cd "$root" && tools/godot_bg --write-movie "$avi" --fixed-fps 30 --path projects/games/last_light/godot \
      -- --capture=film --film $args --audio) < /dev/null > "$log" 2>&1
  n=$(grep -o '^[0-9]* frames at 30 FPS' "$log" | grep -o '^[0-9]*')
  pk=$(ffprobe -v error -select_streams v:0 -count_packets -show_entries stream=nb_read_packets -of csv=p=0 "$avi" 2>/dev/null)
  roll=$(grep -o 'FILM_ROLL frame=[0-9]*' "$log" | grep -o '[0-9]*$')
  secs=$(echo "$args" | grep -o 'film_reel_secs=[0-9.]*' | cut -d= -f2); secs=${secs:-12}
  if [[ -z "$n" || -z "$pk" || "$n" != "$pk" || -z "$roll" ]]; then
    echo "FAIL $name frames=$n packets=$pk roll=$roll (log kept)"; fails=$((fails+1)); continue
  fi
  ss=$(python3 -c "print(f'{($roll + 1) / 30:.3f}')")
  ffmpeg -v error -ss "$ss" -t "$secs" -i "$avi" \
    -vf "scale=in_range=full:out_range=tv,format=yuv420p" -c:v libx264 -profile:v high -crf 12 -preset slow \
    -pix_fmt yuv420p -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
    -c:a aac -b:a 320k -movflags +faststart "$clip"
  # keep a lossless-audio sidecar of the roll for the mix
  ffmpeg -v error -ss "$ss" -t "$secs" -i "$avi" -vn -c:a pcm_s24le "$out/$name.wav"
  rm "$avi"
  echo "OK $name frames=$n roll@$ss s -> $(basename "$clip")"
done 3< "$shots"
echo "REEL_RESULT fails=$fails"
exit $(( fails > 0 ))
