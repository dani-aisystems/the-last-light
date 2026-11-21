# THE LAST LIGHT: R7 submission checklist (final state 2026-11-21)

- **Branch:** `release-r7` (worktree `exports/worktrees/last_light_r7`, from main `eff547c`). Local commits only, never pushed. Merging into main is Daniel's call.
- **Package:** `projects/games/last_light/build/R7/TheLastLight_R7/`.
- **Intermediates and masters:** `renders/last_light/r7/`.
- **Competition:** National Autumn IT Tournament "Джон Атанасов" 2026/27. **Registration (in Bulgarian) closes 29.11.2026**; the defence is in Sofia, 4–6.12.2026.

| # | Item | Status | Output | Evidence |
|---|---|---|---|---|
| A | Endings in motion, through to the credits (all four) | **DONE** | `04_Media/Endings/TheLastLight_Ending_{HeardTogether,NothingToReport,LightExhibited,Correction}.mp4` | `qa/ENDINGS_QA.md`. Every take was gated (drawn frames = written frames). The occlusion fault was proven by an A/B test and fixed. Sheets viewed. Audio by measurement only. |
| B | Screenshots (8) plus contact sheet | **DONE** | `04_Media/Screenshots/` | `SCREENSHOTS.md`. In-engine, High preset, 1920×1080, unaltered. |
| C | Source archive and clean room | **DONE** | `02_Source/TheLastLight-source.zip` (713.2 MB, SHA-256 `397dea04…7a4d`) | `qa/BUILDS_SOURCE_R30_QA.md`. `--verify` PASS. The independent clean-room import, tests, export and boot all PASS. |
| D | READMEs (EN and BG), Bulgarian documentation (full and ≤ 5-page print), leaflet, Appendix 4 draft | **DONE** (personal fields, R6 play time and the Appendix 4 decision left for Daniel) | `03_Documentation/` | Fact-checked against code and canon. Corrections made: the premise, "8 men", the 11-minute spoiler, regress 503, the performance framing. |
| E | Trailer (77.3 s) plus master, EDL, shot list, cue sheet, EN/BG subtitles, thumbnail, narration stem | **DONE** (Daniel's ear pending) | `04_Media/Trailer/` | `qa/TRAILER_QA.md`: −16 LUFS, −1 dBTP, 0 clipping, sheets viewed. |
| E2 | Gameplay video (separate from the trailer, labelled honestly) | **DONE** (scripted capture); R6 human run PENDING | `04_Media/Gameplay/TheLastLight_Gameplay_Ch1_scripted_capture.mp4` | An in-engine automated keeper playing chapter 1 through the real controls, 139.8 s, High preset. |
| F | ElevenLabs narration (Q28) | **DONE** (voice provisional) | `trailer/VO_SCRIPT.md`; originals in `renders/…/VO_original/` | Free plan, Multilingual v2. Adam chosen by measurement (Hector distorted, David band-limited). Terms saved. |
| G | R30 deterministic | **RESOLVED** | `godot/tests/regress_test.gd`, `tests/r30_repeat.gd` | Old logic fails 50/50 at a ≥ 150 ms stall; fixed, 200/200 pass. regress 10× 503/503. |
| H | Windows export | **EXPORTED, NOT RUN-TESTED** | `01_Build/Windows/TheLastLight-Windows.zip` (236.5 MB) | Official templates, SHA-512 verified; PE32+; pck 929 files. |
| I | Integration and final gate | **DONE** | `build/R7/TheLastLight_R7/` (with SHA256SUMS) | Suites green on `release-r7`; the no-game-change diff is empty. |
| R6 | Daniel's timed playthrough | **BLOCKED (Daniel)** | `[[R6_PLAY_TIME]]` in the READMEs and docx | |
| P | Defence presentation (listed among the files to upload) | **NOT DONE** (not in the R7 brief) | | Offered. |
