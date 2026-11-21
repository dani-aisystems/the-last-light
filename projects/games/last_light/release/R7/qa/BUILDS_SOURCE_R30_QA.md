# THE LAST LIGHT R7: builds, source archive, R30 and compliance (2026-11-21)

## macOS build (unchanged since R5)
- **File:** `build/TheLastLight.zip`, 261,035,832 bytes. It contains `The Last Light.app` (universal arm64 + x86_64, ad-hoc signed with the hardened runtime) and `THIRD_PARTY_LICENSES.txt`. It is an export of `d354b39`.
- **No game change since then:** `git diff eff547c..release-r7 -- godot ':!tests' ':!film_fp.gd' ':!capture_fp.gd' ':!export_presets.cfg'` is empty.
- **R5 evidence:** export, pck contents, headless and windowed boots PASS. Gatekeeper requires Open Anyway.
- **Not tested by Claude:** a new game, save/load and an ending played in the exported app. These are Daniel's R6.

## Windows build: exported, NOT run-tested
- **Templates:** the official Godot 4.7.2 export templates (`Godot_v4.7.2-stable_export_templates.tpz`, 1,281,349,702 bytes, from the godotengine GitHub release). The SHA-512 matched the official `SHA512-SUMS.txt`: `ca4d71c4…84079`. Only the four `windows_*_x86_64*` templates were extracted, and the `.tpz` was deleted. The macOS template is unchanged (md5 `1faaf4e3…8953` before and after).
- **Preset:** "Windows Desktop" (branch `release-r7`). Same include/exclude filters as macOS, x86_64, embedded pck, S3TC/BPTC textures, no code signing.
- **Export:** headless `--export-release`, exit 0, no errors, 20 s. `TheLastLight.exe` is 333,404,352 bytes, `file` reports PE32+ executable (GUI) x86-64.
- **Embedded pck:** carved from the exe footer (GDPC, 224,187,572 bytes) and listed with `release/pck_list.py`. It holds 929 files, the same count as the macOS R5 pck. There are no `tests/`, `capture_fp`, `film_fp` or `autotest` scripts. It has 36 S3TC textures and no ETC2/ASTC. `credits.txt`, `panels.json` and `chapters.json` are present.
- **Zip:** `build/R7/TheLastLight-Windows.zip`, 236,521,493 bytes (exe plus `THIRD_PARTY_LICENSES.txt`). `unzip -t` OK. SHA-256 `28ea07dc…6eff8`.
- **Runtime:** NOT TESTED. There is no Windows machine. Godot's Forward+ renderer needs Vulkan or Direct3D 12 on Windows 10/11.

## Source archive
- **Command:** `release/make_source_archive.sh --rev 0949da6 --verify --out build/TheLastLight-source.zip --tex-src <workspace>/assets/textures`. Exit 0, 4 min 37 s.
- **Output:** `build/TheLastLight-source.zip`, **713,240,750 bytes**, 1,204 files. **SHA-256 `397dea040287f521cacba714c66ec4650b0a28af4041535b44ccdf93522c7a4d`**, also in `build/SHA256SUMS.txt`.
- **Contents:**
  - `godot/`, `blender/`, `audio/`, `branding/`;
  - `Ending Card/` (Daniel's 9 original panels);
  - the six CC0 texture sets (36 files; the 18 PNGs are byte-identical to the Poly Haven originals in `assets/textures/`; `TEXTURES_SHA256.txt` inside);
  - `THIRD_PARTY_LICENSES.txt` (Godot MIT, 102 components, 19 licences, 4 OFL fonts), `ASSET_LICENSES.md`, `SOURCE_README.txt`.
- **Excluded:** `.godot/`, `character-refs/`, the raw `Music Tracks/`, the `John Atanasov/` folder, and other workspace projects.
- **Built-in verify:** fresh unzip, headless import, `run_tests` 95/95, `opening_test` 31/31, 0 "Resource file not found", 0 SCRIPT ERROR. **PASS.**
- **Independent clean room** (Worker C, the trial archive at `eff547c`, which has the same game files):
  - import exit 0, with 0 hits for any error pattern in 1,390 log lines;
  - 1,432 `res://` references scanned, 0 missing;
  - `--export-release macOS` from the extracted project: exit 0, no warnings. The pck file list is identical to R5's (5 imported-scene sizes differ by 1–5 bytes; glb import is not bit-deterministic);
  - the exported binary boots headless (900 frames) twice, exit 0. Daniel's `saves/` were unchanged by md5.
- **Against the old archive** (`TheLastLight-source-pre-r3-20261120-1424.zip`, kept): nothing removed; added are `Ending Card/`, the 9 imported ending panels, `ending_panels_import.py`, `film_fp.gd`, `TEXTURES_SHA256.txt` and the R7 test and tooling changes. Changed: `SOURCE_README`, the panel shader fix, `panels.json`, `settings.gd`, `story_presenter.gd`, `capture_fp.gd`.
- **Sweep fixed before archiving:** `tests/debug_station.gd` held an absolute machine path; it is now `user://`. No secrets or keys. The only e-mail is the public contact link in `data/links.json`, which ships in the game.

## R30: deterministic (test-only fix)
- **Mechanism (proven):** `outside.gd::_process` ticks every vessel view with the real frame delta. During the frame the test awaited after spawning, it ticked the new view once, so the hand-stepped loop began with `_appear = real_delta / 3`. The half-way time moved to 1.5 − real_delta. Godot caps delta at about 0.15 s, so the floor is about 1.35 s, matching the 1.37 s failure seen in R3.
- **Reproduction** (`tests/r30_repeat.gd`, an injected frame stall, 50 runs per level, old logic):

  | Stall | Failures |
  |---|---|
  | 0 ms | 0/50 |
  | 50 ms | 34/50 |
  | 150 ms | 50/50 |
  | 400 ms | 50/50 |

- **Fix (tests only, `regress_test.gd` +15/−1):**
  - pause `g.outside` processing from before the spawn to the end of the measurement, restored on every path;
  - assert the fixture is at rest (`_appear == 0`, `_fade == 0`) before the loop;
  - every original assertion and tolerance is unchanged.
- **Evidence after the fix:**
  - the stall harness passed 200/200 iterations at every stall level (half-way 1.517 s every time);
  - `regress_test` ran 10 times (5 of them under 4× `yes` CPU load), 503/503 each, 0 SCRIPT ERROR;
  - the final suite run on `release-r7` (2026-11-21): regress 503/503.
- **Verdict:** RESOLVED. The mechanism is removed and guarded by an explicit readiness check.

## Final suites on `release-r7` (headless, `taskpolicy -b`, 2026-11-21)

| Suite | Result |
|---|---|
| story_test | `STORY_RESULT {"failed":0}` |
| sim_v2 | `SIM2_RESULT {"gate_failures":[]}`; game code is unchanged, so the M0 seeds are unaffected |
| run_tests | 95/95 |
| opening_test | 31/31 |
| regress_test | 503/503 (4 headless-only skips) |
| pytest | pass (7 skipped) |
| SCRIPT ERROR (all suites) | 0 |

## Competition compliance
Source: `John Atanasov/Регламент 2026-2027.pdf`, read in full.

| Requirement | Status |
|---|---|
| Registration in Bulgarian on the host school's site by **29.11.2026** | **Daniel** |
| Everything uploaded online and the link shared (source, executable, documentation, presentation, other files) | Package ready in `build/R7/TheLastLight_R7/`; upload is **Daniel's** (outward-facing). The presentation is **not made** (not in the R7 brief; offered) |
| Source code (mandatory) | `TheLastLight-source.zip`, verified |
| Folder: labelled flash drive or CD | **Daniel** (physical) |
| Documentation ≤ 5 A4 sheets, Appendix 1 structure, TNR 12, spacing 1.5 | `The Last Light – печат.docx` (≤ 5 pages); the full version is `The Last Light.docx`. Personal fields are left for **Daniel** |
| One advertising leaflet | `Листовка.pdf` (A4 tri-fold, Bulgarian) |
| Appendix 4 declaration | `Декларация_Приложение4_чернова.docx` (draft). The "code is my work" box is **Daniel's decision**; sign it |
| Windows | Not required by the rules; an unsigned export is provided, NOT run-tested |
| Defence (15 min, flash drive or own laptop) | **Daniel** |
| Bulgarian language norms (a criterion) | The game is English-only (known risk). The docs, README_BG, leaflet and trailer subtitles are in Bulgarian |
