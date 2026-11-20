#!/usr/bin/env bash
# THE LAST LIGHT release R7: assemble the submission folder from verified artefacts. Files are APFS clones
# (cp -c: no extra disk space); nothing is re-encoded here. Re-run safely: it refuses to overwrite.
#   assemble.sh            -> projects/games/last_light/build/R7/TheLastLight_R7/
set -euo pipefail
ws="/Users/daniel/Documents/Projects OS/Tools : Software/Blender Dev"
here="$(cd "$(dirname "$0")" && pwd)"
R7r="$ws/renders/last_light/r7"
build="$ws/projects/games/last_light/build"
out="$build/R7/TheLastLight_R7"
[[ -e "$out" ]] && { echo "exists: $out (move it aside first)"; exit 1; }
mkdir -p "$out"/{01_Build/macOS,01_Build/Windows,02_Source,03_Documentation,04_Media/Trailer,04_Media/Endings,04_Media/Screenshots,04_Media/Gameplay,05_Licenses,06_QA}
c() { cp -c "$1" "$2"; }

# 01 builds
c "$build/TheLastLight.zip" "$out/01_Build/macOS/TheLastLight.zip"   # the name the READMEs and leaflet use
[[ -e "$build/R7/TheLastLight-Windows.zip" ]] && c "$build/R7/TheLastLight-Windows.zip" "$out/01_Build/Windows/"
# 02 source
c "$build/TheLastLight-source.zip" "$out/02_Source/"
[[ -e "$build/SHA256SUMS.txt" ]] && c "$build/SHA256SUMS.txt" "$out/02_Source/"
# 03 documentation
for f in "$here/docs/"*.docx "$here/docs/"*.pdf "$here/docs/README_EN.md" "$here/docs/README_EN.txt" "$here/docs/README_BG.txt"; do
  [[ -e "$f" ]] && c "$f" "$out/03_Documentation/"
done
c "$here/docs/README_EN.txt" "$out/README_EN.txt"
c "$here/docs/README_BG.txt" "$out/README_BG.txt"
# 04 media
for f in "$R7r/trailer/final/"TheLastLight_Trailer*.mp4 "$R7r/trailer/final/"*.srt "$R7r/trailer/final/"thumbnail*.png; do
  [[ -e "$f" ]] && c "$f" "$out/04_Media/Trailer/"
done
for f in "$R7r/endings/"TheLastLight_Ending_*.mp4; do
  [[ "$f" == *_master.mp4 ]] || c "$f" "$out/04_Media/Endings/"
done
[[ -d "$R7r/screens/final" ]] && cp -cR "$R7r/screens/final/" "$out/04_Media/Screenshots/"
for f in "$R7r/gameplay/"*.mp4; do [[ -e "$f" ]] && c "$f" "$out/04_Media/Gameplay/"; done
# 05 licences
c "$build/THIRD_PARTY_LICENSES.txt" "$out/05_Licenses/" 2>/dev/null || true
c "$ws/assets/ASSET_LICENSES.md" "$out/05_Licenses/"
c "$here/trailer/elevenlabs_terms_2026-11-20.txt" "$out/05_Licenses/"
# 06 QA
for f in "$here/qa/"*.md "$here/R7_CHECKLIST.md"; do [[ -e "$f" ]] && c "$f" "$out/06_QA/"; done
( cd "$out" && find . -type f ! -name 'SHA256SUMS.txt' -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS.txt )
du -sh "$out"; find "$out" -type f | wc -l
echo "ASSEMBLE_RESULT ok $out"
