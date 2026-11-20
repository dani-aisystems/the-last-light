#!/usr/bin/env bash
# THE LAST LIGHT: source archive for the competition (release track R7; Daniel, 2026-11-20).
#
# Builds build/TheLastLight-source.zip from a COMMITTED revision (default HEAD), never from the working
# tree, so other sessions' uncommitted work cannot leak in:
#   1. a local clone of the workspace repo at <rev>, with the game's LFS objects pulled (no network: the
#      origin is this repo);
#   2. the game folder's tracked files (INCLUDE below), LFS content in place of pointer files;
#   3. plus the six CC0 interior texture sets that .gitignore keeps out of git (R1 finding F1, Daniel's
#      decision: CC0 1.0 allows redistribution), copied from godot/assets/textures/ with their .import files;
#   4. plus THIRD_PARTY_LICENSES.txt (tests/make_licenses.gd), the asset licence log and a SOURCE_README.
# --verify then unzips the archive, imports it headless and runs run_tests and opening_test, failing on any
# "Resource file not found" (the F1 check) or SCRIPT ERROR.
#
# Usage:  projects/games/last_light/release/make_source_archive.sh [--rev=<commit>] [--with-docs] [--verify]
#         [--force]   (overwrite an existing build/TheLastLight-source.zip; ask Daniel first)
# Nothing is deleted: the work folder is left in $TMPDIR and its path is printed.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"           # the workspace (git root)
GAME_REL="projects/games/last_light"
GAME="$ROOT/$GAME_REL"
OUT="$GAME/build/TheLastLight-source.zip"
REV="HEAD"; WITH_DOCS=0; VERIFY=0; FORCE=0
for a in "$@"; do
  case "$a" in
    --rev=*) REV="${a#--rev=}" ;;
    --with-docs) WITH_DOCS=1 ;;
    --verify) VERIFY=1 ;;
    --force) FORCE=1 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done
# What goes in. character-refs/ (Daniel's reference dossiers) and the process notes stay out by default.
INCLUDE=(godot blender audio branding)
DOCS=(DESIGN.md NARRATIVE.md REFERENCE_SPEC.md SCRIPT_REVISION_2026-11.md STAGE3_NARRATIVE_MASTER.md)
TEXTURE_SETS=(plastered_wall_02 concrete_floor_worn_001 oak_veneer_01 dark_wooden_planks green_metal_rust metal_plate_02)

if [[ -e "$OUT" && $FORCE -eq 0 ]]; then
  echo "refusing: $OUT exists (pass --force to overwrite)" >&2; exit 1
fi
SHA="$(git -C "$ROOT" rev-parse --verify "$REV^{commit}")"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/lastlight_source.XXXXXX")"
echo "rev $SHA  work $WORK"

# 1. clone at the revision, pull only the game's LFS objects
GIT_LFS_SKIP_SMUDGE=1 git clone -q --no-checkout "$ROOT" "$WORK/clone"
git -C "$WORK/clone" checkout -q "$SHA"
git -C "$WORK/clone" lfs pull --include="$GAME_REL/**" >/dev/null
if git -C "$WORK/clone" lfs ls-files --include="$GAME_REL/**" | grep -q ' - '; then
  echo "LFS objects missing (pointer files left):" >&2
  git -C "$WORK/clone" lfs ls-files --include="$GAME_REL/**" | grep ' - ' >&2; exit 1
fi

# 2. stage the included folders (tracked files only, as checked out)
STAGE="$WORK/TheLastLight-source"
mkdir -p "$STAGE"
for d in "${INCLUDE[@]}"; do
  [[ -d "$WORK/clone/$GAME_REL/$d" ]] && ditto "$WORK/clone/$GAME_REL/$d" "$STAGE/$d"
done
if [[ $WITH_DOCS -eq 1 ]]; then
  mkdir -p "$STAGE/docs"
  for f in "${DOCS[@]}"; do [[ -f "$WORK/clone/$GAME_REL/$f" ]] && cp "$WORK/clone/$GAME_REL/$f" "$STAGE/docs/"; done
fi

# 3. the six gitignored CC0 texture sets (from the working tree; they are not in git)
n=0
for s in "${TEXTURE_SETS[@]}"; do
  for f in "$GAME/godot/assets/textures/${s}_"*; do
    [[ -e "$f" ]] || { echo "missing texture set $s in godot/assets/textures/" >&2; exit 1; }
    cp "$f" "$STAGE/godot/assets/textures/"; n=$((n+1))
  done
done
echo "added $n CC0 texture files (6 sets, with .import files)"

# 4. licences and a short source readme
"$ROOT/tools/godot" --headless --path "$WORK/clone/$GAME_REL/godot" -s res://tests/make_licenses.gd \
  -- --out="$STAGE/THIRD_PARTY_LICENSES.txt" 2>"$WORK/licenses.log" | grep -E "LICENSES_RESULT"
  # (stderr goes to the log: the clone is not imported, so its autoloads print parse errors; the script needs none)
cp "$WORK/clone/assets/ASSET_LICENSES.md" "$STAGE/ASSET_LICENSES.md"
cat > "$STAGE/SOURCE_README.txt" <<EOF
THE LAST LIGHT: source code (revision ${SHA:0:12})
A game by Daniel Yanchev.

godot/     the game: a Godot 4.7.2 project (open godot/project.godot in Godot 4.7.2).
           Tests: godot --headless --path godot -s res://tests/run_tests.gd
blender/   the Blender 5.2 scripts that build the game's models and textures (spec.py, build.py, ...)
audio/     the scripts that synthesise, cut and master the game's sound and music
branding/  the title art and icon sources

Licences: THIRD_PARTY_LICENSES.txt (Godot Engine and its components, the typefaces);
ASSET_LICENSES.md (every third-party asset, its source and licence; CC0 1.0 or SIL OFL 1.1).
Music by Daniel Yanchev. The characters, vessels, the North Point Light and the events of 1953
are fictional.
EOF

# 5. zip (no macOS metadata)
mkdir -p "$(dirname "$OUT")"
( cd "$WORK" && COPYFILE_DISABLE=1 zip -qr -X "$WORK/TheLastLight-source.zip" "TheLastLight-source" )
cp "$WORK/TheLastLight-source.zip" "$OUT"
echo "SOURCE_ARCHIVE $(stat -f %z "$OUT") bytes, $(unzip -l "$OUT" | tail -1 | awk '{print $2}') files -> $OUT"

# 6. optional: prove a judge's copy opens textured and passes the tests
if [[ $VERIFY -eq 1 ]]; then
  V="$WORK/verify"; mkdir -p "$V"; ( cd "$V" && unzip -q "$OUT" )
  P="$V/TheLastLight-source/godot"
  "$ROOT/tools/godot" --headless --path "$P" --import > "$WORK/verify_import.log" 2>&1 || true
  "$ROOT/tools/godot" --headless --path "$P" -s res://tests/run_tests.gd > "$WORK/verify_run_tests.log" 2>&1 || true
  "$ROOT/tools/godot" --headless --path "$P" -s res://tests/opening_test.gd > "$WORK/verify_opening.log" 2>&1 || true
  rt=$(grep -E '^TEST_RESULT' "$WORK/verify_run_tests.log" | tail -1)
  op=$(grep -E '^OPENING_RESULT' "$WORK/verify_opening.log" | tail -1)
  nf=$(cat "$WORK"/verify_*.log | grep -c "Resource file not found" || true)
  se=$(cat "$WORK"/verify_*.log | grep -c "SCRIPT ERROR" || true)
  echo "VERIFY run_tests: ${rt:-none}"
  echo "VERIFY opening:   ${op:-none}"
  echo "VERIFY missing resources: $nf   script errors: $se   (logs in $WORK)"
  [[ -n "$rt" && -n "$op" && "$nf" -eq 0 && "$se" -eq 0 && "$rt" == *'"failed":0'* && "$op" == *'"failed":0'* ]] \
    || { echo "VERIFY FAILED" >&2; exit 1; }
  echo "VERIFY PASS"
fi
