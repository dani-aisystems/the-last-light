# Session handoff: 2026-11-04 (session 2, Stage 0)

## LATEST (2026-11-06, night): G2 + G5 checkpoint captured, presented, awaiting Daniel
- **Baseline at 3796c41 re-verified, all green:** story 0 failures; regress 202/202 (3 headless skips); interaction 159/0 (12 sound warnings); qa_sweep 1,924; sim_v2 no gate failures; run_tests 95; g5 44/44; pytest 21.
- **Two stray Claude sessions (PIDs 19478, 23732) were stopped at Daniel's request.** They had been editing `capture_fp.gd` in parallel.
- **`capture_fp.gd` (uncommitted):**
  - new states: `op_valve`, `op_start`, `op_charge`, `op_console`, `bolt`, `visitor`;
  - new view: `fp_bolt`;
  - `--story_auto`: with `--bot=`, the story advances but nothing plays the sim;
  - a `STATE` line printed per shot.
- **Capture run, with Daniel's OK:** `renders/last_light/g25_t*.png`; sheets `g25_sheet_opening.png`, `g25_sheet_mission.png`, `g25_sheet_g5.png`.
- **Findings:**
  - **The mission panel has no backing plate.** Its steps are unreadable over the lit cream wall: contrast 1.5:1 median, 1.1:1 worst (`g25_t076`).
  - **The bolt shot missed.** The old `fp_bolt` camera looked through the optic column; it is re-aimed but not re-shot.
  - **The Visitor figure is a primitive mannequin.** The black oilskin reads correctly.
- **Daniel rejected a checklist reskin and approved G2b, a cinematic duty system** (plan `~/.claude/plans/pasted-content-id-bdd5-the-last-twinkling-crab.md`; decisions in FINDINGS_LOG "G2 + G5 checkpoint").
- **Order of work:**
  1. Stage 0: commit the G2 + G5 close-out (with Daniel's OK).
  2. G2b S1, the duty model; S2 the HUD; S3 the ch1 slice; S4 the logbook; S5 ch2–6.
  3. Then G3, starting with the pipe question.
- **Still pending with Daniel:** the music pick, the listening pass, the Visitor figure.
- **G2b S1 committed** (`b37cdfc`).
- **G2b S2 committed** (`f21a5dc`).
- **G2b S3 committed** (`b550e29`).
- **G2b S4 committed** (`726f8c7`).
- **G2b S5 (all chapters) implemented, uncommitted, awaiting the closing G2b checkpoint:**
  - 19 duties across ch1–6 (no `objective` key left);
  - `"duty": []` ends a duty; duties without steps escalate; the Duties page is per chapter; the write-up counts only at the desk (`game_fp._at_desk`).
  - All suites green. **Evidence:** `renders/last_light/g2b6_*.png`.
  - **Approved and committed** (`95ee6a8`); G2b is complete.
- **Daniel, 2026-11-07: no pipe for Callum.** Item 19 is dropped; Iain's pipe as a cabin object is an option for G4.
- **G3 staging (Daniel, 2026-11-07):**
  - G3a: the equipment system, with compass and binoculars as held items and procedural sway;
  - G3b: arms and hands;
  - G3c: the full body and sitting at the radio.
  - Keys: G compass, B binoculars.
  - Both lie on the desk from the start; optional duty steps in the ch1 Kittiwake duties point them out.
- **G3a implemented, uncommitted, awaiting Daniel's checkpoint:**
  - `pipeline.sh --docs` is opt-in;
  - `build.py`: a new brass hand compass on the chart (near-left corner; `PROP_compass_*`, `PT_compass_needle`, `IA_compass`) and the binoculars split into `PROP_binoculars_*` + `IA_binoculars`; build v040, GLB `watch_room_v038` (0 FAIL, reimport OK);
  - `equipment.gd` (held copies, needle to north, 7× binoculars with mask);
  - station pickups; the player's G/B keys; a pick rule so a pickup on a document wins;
  - ch1 optional `nudge_first` steps;
  - regress R15. All suites green.
  - **Evidence:** `renders/last_light/g3a_*.png`, `g3a2_*`, `g3a3_*`.
  - **Pad:** G/B left unbound for now (Daniel 2026-11-07; a later controls pass).
  - **Approved by Daniel; committed** (`31afb9a`).
- **G3b, started 2026-11-07 (Daniel: "Continue"):**
  - **Inspection:** the CC0 bundle has no armature; it has "Hand  - Realistic" (831 vertices, multires) and GEO-body_male_realistic. Canon (PROFILE §G): fair to lightly ruddy skin, no scars, clean hands; a navy or charcoal wool guernsey, cuffs repaired.
  - **Plan:**
    - new `blender/player_hands.py`: the hand mirrored for the left; our own armature (detected finger chains, automatic weights); a knitted guernsey cuff with a darn; poses relaxed / torch / compass / binoculars; `hands.glb`, validated and reimport-checked;
    - in Godot, hands only while holding something; the torch light in the right hand;
    - regress R16, then captures.
- **G3b done; approved by Daniel 2026-11-08 ("Continue" on the checkpoint, with the 40° compass hold and the 0.45 s raise); committed locally.**
  - A duplicate session (PID 61377, a resumed copy of this conversation) was stopped at Daniel's word; its R16 was merged into ours.
  - Built as `blender/hands.py` (not `player_hands.py`), v007; record and evidence in FINDINGS_LOG "G3b record".
  - **Gotcha:** the glTF exporter writes every armature's tracks into every action. Read poses per armature (`equipment.gd` filters on the track path).
  - A separate session (PID 79015) is adding a gameplay-film mode (`--film`, `film_fp.gd`) to `capture_fp.gd`. Its hunk and files are not in the G3b commit.
- **G3c decisions (Daniel, 2026-11-08):**
  - the G3b camera hands stay; the body shows legs, boots and torso when looking down; its arms and head only cast shadows;
  - our own light rig (about 30 bones, automatic weights), built in a new `blender/body.py`;
  - walk / idle / sit / turn hand-keyed in Blender (no downloads);
  - the body casts shadows, with a frame-time check against the ROADMAP budget.
  - Source: `GEO-body_male_realistic` from the CC0 bundle (10,582 verts, 1.69 m, no armature). Canon §G: lean, upright; dark guernsey, worn shirt, wool trousers, stout boots.
- **G3c done; approved by Daniel 2026-11-08 and committed locally.** Record and evidence in FINDINGS_LOG "G3c record". G3 is complete.
  - **Gotchas:** bundle objects carry a layout offset in `matrix_world` (read it after `view_layer.update()`); Blender bone heat fails on the base body (use the distance weights in `body.py`); walk-sync and turn tests must step time themselves (real frames under load skip whole steps).
- **Next: G4** (cabin assets: KEEPER'S ORDERS line 5, Iain's pipe as a cabin object (option), the D8 doc re-render), then G6.
- **G4 decisions (Daniel, 2026-11-08):**
  - staged: **G4a** fixes (shelf intersections, floating papers, KEEPER'S ORDERS line 5, the console note texture, D8 document renders, Iain's pipe line); **G4b** the coat as baked Blender cloth with a real pocket and the note seated by raycast; **G4c** the photograph and the rest of the prop audit;
  - the desk pipe, ashtray and Skerry Flake tin stay as **Iain's pipe**, a memento, never smoked; one short inspect line drafted for Daniel's review.
- **G4a done; approved by Daniel 2026-11-09 and committed locally** (record in FINDINGS_LOG "G4a record"). Room material cap 33 (Daniel).
  - **Gotchas:** a test that fails to parse can still exit 0: read the `*_RESULT` line, never the exit code. Unseeded paper grain rewrites every doc PNG on `--docs` runs.
- **Next: G4b**, the coat as baked Blender cloth with a real pocket, the note seated by raycast (item 6).
- **G4b done; approved by Daniel 2026-11-09 and committed locally** (FINDINGS_LOG "G4b record"). The final v050 coat was checked in Blender renders, not re-shot in game.
  - **Gotchas:** build.py now adds its own folder to `sys.path` (coat_cloth.py); the cloth sim adds about 25 s to every build; `cu_coat_note` uses absolute coordinates read from IA_coat_note (re-read them if the coat moves).
- **Next: G4c** (item 15 photograph realism, item 17 prop audit, item 10 per-object shelf detail).
- **G4c done; approved by Daniel 2026-11-09 and committed locally** (FINDINGS_LOG "G4c record"). **G4 is complete.**
- **Next: G6** (items 1 menu external links, 22 radio character profiles, 34): item 1 needs Daniel's links; 22 is paused until Daniel's portrait images (and the "no AI images" check on how they were made); 34 can start. Inspect first, then ask Daniel.
- **G6 decisions (Daniel, 2026-11-09; DECISIONS Q11, Q12):**
  - staged **G6a** (34 flow + rolling credits, stand-in panels), **G6c** (item 1 menu redesign; the link strip reads `godot/data/links.json`, hidden until Daniel sends the links), **G6b** (34 panel art when Daniel's images arrive);
  - the P1/P2/P4 ending images come from Daniel (AI-built): the one exception to the no-AI rule; the credits drop the "no AI-generated images or voices" line and say nothing about AI; item 22 still gets the how-were-they-made check;
  - one light shared shader grade; credits music = the synth `music_menu` pad until item 33; "A game by Daniel Yanchev"; a factual macOS-fonts credit line, with the OFL re-render as its own ROADMAP task.
  - Plan: `~/.claude/plans/pasted-content-id-5833-continue-the-quirky-chipmunk.md`.
- **Item 22 radio portraits (portrait session, 2026-11-09): built, tests green, NOT yet seen in game and NOT committed.**
  - Daniel's ChatGPT prints are allowed for the radio card (DECISIONS Q13). The Blender bust probe is shelved.
  - Pipeline: `tools/py projects/games/last_light/blender/portraits_prepare.py` crops `character-refs/<id>/` sources (explicit `SOURCES` map) to 512x640 prints in `godot/assets/portraits/<id>_<expr>.png`.
  - `Speakers.portrait(id, expr)` tries `<id>_<expr>`, then `<id>_neutral`, then "" (the line drawing stays for Corrie May, Lowestoft Star and the Mary Ellen caller; VISITOR gets none).
  - `dialogue_ui`: card 152x190 with a 136x170 print in a paper border, a dark plate under the signal meter, and `expr` carried through `_resolved`.
  - 20 `.dlg` lines are tagged (Morag worried, Rory scared, Elspeth cold, Hector sorry, Callum guarded).
  - Still to make: Callum grief, Morag hurt, Rory grin, Elspeth moved, Hector warm.
  - Tests: new `tests/portrait_test.gd` (48 pass). On HEAD plus only these files: regress 256/0, story, run_tests 95, sim_v2 (5 seeds) and pytest all pass. The main tree's regress currently fails 19 checks (GameState compile error) from the parallel G6 session's uncommitted work, not from this change.
  - Files: `speakers.gd`, `dialogue_ui.gd`, ch1–ch5 `.dlg`, `portrait_test.gd`, `portraits_prepare.py`, `assets/portraits/`.
- **G6a implemented, uncommitted, awaiting Daniel's checkpoint** (FINDINGS_LOG "G6a record"). Baseline at `55c0689` re-verified first (all as handed over). After G6a: story 0, regress 275/0, interaction 159/0, qa_sweep 1,924, sim_v2 no gate failures, run_tests 95, g5 48, pytest 23.
  - **Captures not taken yet** (need Daniel's OK for one batched silent `tools/godot_bg` run): `ending_<id>` with `--ending_step=p1/p2/p3/p4/card`, `--ending_grade=0`, plus the credits.
  - **Gotchas:** `class_name` scripts can't name the `GameState` autoload under `-s` (use `EndingSequence.user_arg`); E no longer advances the ending card (regress R10 now presses Space).
  - `capture_fp.gd`'s gameplay-film hunk and `film_fp.gd` belong to another session: never staged.
  - **G6a captures taken with Daniel's OK** (`renders/last_light/g6a_*`, sheet `g6a_sheet.png`); credits reflowed afterwards (line widths measured, not re-shot).
- **A parallel session (PID 26206) was found working on item 22 and stopped by Daniel.** He then had this session **adopt its item 22 work** and add the Mary Ellen's card (`character-refs/ellen.png`) and his 1952 wall photograph (`character-refs/Picture-wall/`). Records: FINDINGS_LOG "Item 22 record", "Wall photograph". AI exceptions: DECISIONS Q11. Build v052. All suites green on the final tree (regress 284/0 with R20).
  - **Approved and committed:** G6a `c5614ab`; item 22 + the wall photo `d541d02`. Captures `renders/last_light/g22_t*` (cards and wall photo in game; the Mary Ellen card checked headless only).
  - **Next:** G6c (item 1 menu redesign; links later), then G6b when Daniel's ending panel images arrive.
- **G6c (item 1 main menu, "Still Water"), 2026-11-09 second session: implemented, all suites green, awaiting Daniel's checkpoint; NOT committed.**
  - Baseline at `e7bab26` re-verified first (all as handed over). Daniel widened the brief (research, three directions); he chose the hybrid "Still Water", small items ranked by brightness, no Continue without a save, the signature always bottom-right; mid-build: "make the lighthouse closer, the menu larger font size". Plan: `~/.claude/plans/pasted-content-id-ccb6-continue-the-nifty-alpaca.md`. Record: FINDINGS_LOG "G6c record".
  - Files: `game_fp.gd` (closer orbit, aspect-aware yaw, `lantern_screen_x`, `beam_facing`, `cine_hold`), `main_fp.gd` (title layout, focus return, panel lock, push-in slerp, capture hooks `--links/--menu_focus/--menu_nosave/--menu_fake_save/--win`), `style.gd` (`MENU_*`, `INK_QUIET/SUB/FAINT`, `caps()`, `focus_follows_hover`), `settings.gd` (`reduce_motion`), `fp_ui.gd` (pause buttons), new `ui/menu_item.gd`, `ui/menu_links.gd`, `data/links.json` (empty), `tests/fixtures/links_r21.json`, regress R21.
  - Suites after G6c: regress 322/0 (R21 38 checks); the others as at the baseline.
  - Captures (Daniel's OK): `renders/last_light/g6c_*_menu.png`.
  - **Gotchas:** `--win` sizes are screen points on this Retina Mac, and macOS drops a size set while leaving the start-up fullscreen (main_fp re-applies it); the old captures' 1920×1205 frames were the screen's aspect, not 16:9. A 2-canvas-px rect can vanish in a window below the 1080-line canvas: snap to whole pixels, at least 2 render px. `portrait_test.gd` (not in the suite list) still asserts the Mary Ellen has no print and fails 2 checks since `d541d02`; it is stale, not touched by G6c.
  - **Then:** Daniel's G6c checkpoint, then a local commit (G6c files only; never `capture_fp.gd`). Then G6b when the ending images arrive; the links when Daniel sends them (edit `godot/data/links.json` only).
- **G6c committed** (`81e71c5`). **G6d started** (Daniel's cinematic title + exterior brief; plan `~/.claude/plans/pasted-content-id-ccb6-continue-the-nifty-alpaca.md`; record FINDINGS_LOG "G6d record"). Stages: A saves + audit (committed `9952b00`), B lighthouse (committed `e88e26e`: tower skin, window spill specular, white weathered tower, the door at bearing 35 with a bulkhead lamp), C island/landing/walkway/boat (committed `3185128`: `blender/exterior.py`, island.glb + boat.glb, title-only boat in `outside.setup_title()`), D storm (implemented, awaiting Daniel's checkpoint; NOT committed), E title UI.
- **G6d Stage D (2026-11-13/14): the 02:00 storm on the title; implemented, all suites green, awaiting Daniel's checkpoint, NOT committed.** Record: FINDINGS_LOG "G6d record", Stage D.
  - Files: new `scripts/fp/title_storm.gd` (+ `.uid`) and `shaders/rain_streak.gdshader`; `outside.gd` (`_title_storm_fx`, `_title_step`, title strike handling, `_flash_light`), `game_fp.gd` (`title_storm`, `_title_events`, `force_title_bolt`), `keeper_sim.gd` (watch mode honours `storm_override`), `beam.gdshader` (`decay`, `mask_x`), `ocean.gdshader` (shore surf; global), `tests/regress_test.gd` (R23), `capture_fp.gd` (own hunks: `tmenu` shots, `--bench_menu`; the film hunk is NOT ours).
  - Suites: regress 354/0, story 0, interaction 159/0, qa_sweep 1,924, run_tests 95, g5 48, sim_v2 identical to baseline, pytest 23.
  - Captures (Daniel's OK): `renders/last_light/g6d_d_*`, `g6d_d2_*`, `g6d_d3_*`. Benches `g6d_d_bench_*_bench.json`, `g6d_d3_bench_bench.json`.
  - Open: the spray sprite still has bright cores (PARTIAL); the menu's p95 is about 19–22 ms against 16.7 (median on budget). The ring rain is the 10 ms item (`--norain` 6.9 ms), or a hidden-window pacing artifact: measure in a visible window in Stage 6.
  - **Gotchas:** `tools/godot --check-only -s capture_fp.gd` fails on the GameState autoload (expected); compile it from a running tree instead. Bench GPU time reads 0 in a hidden `godot_bg` window.
  - **Next:** Daniel's Stage D checkpoint, then a local commit of the Stage D files only (stage only our `capture_fp.gd` hunks, via `git apply --cached`). Then Stage E (title UI).
  - **Gotchas:** the scratchpad suite runner is wiped between sessions (recreate it); `tools/godot_bg --win=WxH` is in screen points on the Retina Mac.
  - **Saves:** tests, captures, autotests and benches now use `user://saves_test` (`SaveSystem.isolated()`); before that the suites overwrote the player's autosave.
- **G3a plan, for reference:**
  1. `pipeline.sh`: `documents.py` becomes opt-in (`--docs`), so asset runs stop churning the doc PNGs.
  2. `build.py`: the compass and binoculars get their own mesh buckets (`PROP_compass`, `PROP_binoculars`) plus `IA_compass` / `IA_binoculars`; then run the pipeline (validate, reimport).
  3. `equipment.gd` (new): one held item per hand. Torch: right hand, F. Compass: left hand, G; the needle follows world north. Binoculars: both hands, B; FOV 72° to 10° over 0.35 s, look sensitivity scaled, an eyepiece mask, walking slowed, the torch put away while they're up. E lowers the binoculars first. State is saved.
  4. Held meshes are instanced from the GLB parts, attached to the camera with procedural walk sway (real arms come in G3b).
  5. ch1 duties: optional steps "Take the hand compass" (kittiwake) and "Take the binoculars" (kittiwake_home), with nudges.
  6. Tests: regress R15 (key separation, pickup gating, needle to north within 1°, FOV and state restore after focus, pause and load), story pickup steps. One capture run with Daniel's OK.
- **G2b S4 (logbook + completion), for reference:**
  - `chapters.json` `station_log` holds tonight's five canon rows (verbatim `log_1971`); duties log by id, beats with the `["log", id]` action (18.30, 18.50, 23.25);
  - `blender/log_strips.py` (seeded, reproducible) renders the blank page, row strips, slips (paper + ink), the pencil Duties page and duty strips into `godot/assets/docs/log/` with a manifest;
  - `scripts/story/logbook_pages.gd` (a SubViewport) composes the log with only the written rows, plus the Duties page; L / desk logbook open it; A/D/Tab flip pages;
  - the completion slip top-right reveals its ink with the `pen_write` sound;
  - tests: story `_station_log_canon` plus the campaign writing all five rows once; regress R14.
  - **Evidence:** `renders/last_light/g2b5_*.png`. The strike-through was moved to mid x-height after the capture (verify in S5).
- **G2b S3 (ch1 slice), for reference:**
  - START is no longer refused with the valve shut: it cranks, coughs (`gen_crank_dry`) and fails; Callum's thought follows (queued if dialogue is up), and the fuel valve becomes known;
  - new synth sounds `gen_crank_dry`, `gen_catch`, `relay_clack` (lights on), `torch_click`; existing WAVs byte-identical;
  - per-step escalation in the director (`NUDGE_S` 25, `HINT_S` 60; required steps before optional), with nudge and hint texts in ch1 `chapters.json`; the duplicate beat hints retired;
  - darkness catch-lights on torch / fuel_valve / start / charge (`station.gd`);
  - fixes: battery_low only while draining; charge gauge about 14 A and climbing; radio "sixteen-forty"; "Now the charge." only if CHARGE is off.
  - **Not done:**
    - KEEPER'S ORDERS line 5: moved to G4, because it needs the full Blender pipeline;
    - the ch1 beat restructure: not needed; story_test proves every order works.
  - **Evidence:** `renders/last_light/g2b3_*.png`, `g2b4_sheet.png`.
- **G2b S2 (duty HUD), for reference:**
  - new `scripts/ui/duty_hud.gd`: top-left below the notices' band, a dark soft-edged plate;
  - Standard / Full / Minimal (`Settings.guidance`) and `duty_hold_s`;
  - J / R3 recall (hold for the hint); a tick on finished duties;
  - the old panel removed; regress R9 adapted, R13 added (207 pass).
- **Capture fixes:** the bolt strike bearing is now in radians (the flash shots keep raw 20 rad for comparability); new states guidance_min/full, recall, refuse_start; HUDRECT lines.
- **Evidence:** `renders/last_light/g2b_*.png`, `g2b2_*.png`, sheet `g2b_s2_sheet.png`. HUD text contrast 12–18:1 on every shot (was 1.1–1.5:1). The bolt is visible (item 29 verified).
- **Previous step (S1), for reference:**
  - `StoryState.duties`, `focus_duty` and `log_written` (saved);
  - the director's `_eval_duties` (discover, latch, optional drop, a log line written once) and `activate_duties`;
  - the `duty` and `duty_drop` actions; ch1 `duties` "power" and "light" in `chapters.json`;
  - discovery flags `crank_failed` / `refused_<device>`;
  - an adapter feeds the old panel.
  - story_test `_opening_duties`: the usual order, valve first with the torch skipped, CHARGE before START, console first, and save/load mid-sequence.
  - All suites green.

## CURRENT STATE (2026-11-06, end of day): one session took over all parallel work; read this first
- **All parallel sessions have ended.** The character session took over the G2 (brief) and G5 (weather and audio) work. The file-ownership split above is historical. One session can now own everything.
- **Commits** (local `main`, *not pushed* since `7ac1175`):
  - `af7019c`: character references;
  - `a1ed964`: G2 story_test fix;
  - `0b3e750`: G5 weather and audio.

  The tracked tree is clean.
- **Suites on `0b3e750`, all green (headless, `taskpolicy -b`):**

  | Suite | Result |
  |---|---|
  | story | 0 failures |
  | regress | 202/202 (3 headless skips) |
  | interaction | 159 checks, 0 failed (12 sound warnings, unchanged) |
  | qa_sweep | 1,924/1,924 |
  | run_tests | 95/95 |
  | sim_v2 | no gate failures |
  | g5_weather_audio | 44/44 |
  | pytest | 21/21 |
- **Waiting on Daniel:**
  1. **G2 + G5 checkpoint.** One batched silent `tools/godot_bg` capture run (needs his OK) covering:
     - the dark opening (torch → valve → START → CHARGE → lights → console);
     - the mission panel in free walk and in the radio view, at text 1.0 and 1.5;
     - the pause menu;
     - a lightning bolt;
     - the Visitor at the door (D5 black oilskin).
  2. His listening pass: `renders/last_light/g5_listen_before.wav` and `g5_listen_after.wav`. Never play audio ourselves.
  3. His music pick from `projects/games/last_light/audio/MUSIC_SHORTLIST.md` (item 33; nothing downloaded).
  4. Then the four-part checkpoint and his approval.
- **Parked by Daniel ("delay that for further notice"):**
  - character references: the rest of Morag's bible (G01), a Hector reference (G03), final consolidation on "ALL CHARACTER INFORMATION PROVIDED";
  - portraits (3C / item 22) until he supplies images. Confirm how they were made, because of the CLAUDE.md "no AI images" rule.
- **Untracked by design** (don't commit, delete or ignore without asking Daniel):
  - CC0 texture sources under `assets/textures/` and `assets/models/human_base_meshes/`;
  - `.blend` v028–v030, v032–v034, v036;
  - `cabin-photos/`;
  - the six dossier PNGs in `character-refs/` (19 MB, not LFS, public repo);
  - the paused portrait probe: `blender/portraits*.py`, `blender/tex/src/portraits_raw/`.
- **Gotchas:**
  - Background jobs die when a session restarts, so run long suites in the foreground, one or two at a time (each takes 1–4 min).
  - The scratchpad is wiped on restart. The suite runner is a 10-line bash loop over `tools/godot --headless --path projects/games/last_light/godot -s res://tests/<t>.gd` under `timeout` and `taskpolicy -b` (sim_v2 takes `-- --seeds=1-5`). The test file is `g5_weather_audio_test.gd`.
  - zsh doesn't word-split `$G`, so use bash or full paths.

### Next phases (proposed order)
1. **G2 + G5 checkpoint** (above).
2. **G3, body and equipment** (items 13 visible body, 14 hand animations, 12 compass pickup, 18 binoculars, 19 pipe).
   - **Decide first:** whose pipe is item 19? Callum's profile has no pipe (Iain, Ross and Hector have one). Ask Daniel before giving Callum a new trait.
   - The body's wardrobe follows `character-refs/callum/PROFILE.md` §G: a guernsey over a shirt.
3. **G4, cabin assets** (6 coat stand and pocket note, 10 shelf items, 11 console note, 15 photograph realism, 17 prop audit), plus character-refs D8:
   - the document re-render in Callum's hand to the F15 specification;
   - the log_1953 signature row in his hand (I02);
   - the photo captions (I08, I09).

   Use the document wording in `character-refs/CANON_INDEX.md` §6, Iain's likeness from the Iain dossier, and the `pipeline_nodocs` caution (the unseeded paper grain churns the doc PNGs).
4. **G6:**
   - 34: ending panels and rolling credits (the credits still mention fonts "until Stage 3C");
   - 1: main menu (needs Daniel's links);
   - 22 stays paused.
5. **Stage 3D:** Daniel's decisions on proposals 35–37 and item 31; the narrative QA pass against `character-refs`.
6. **Stages 4–6:** the remaining items in ROADMAP; the timed playthrough is in Stage 6.

**Each group:** Inspect → Plan → Implement → Test (every suite) → Review (captures, with OK) → the four-part checkpoint → Daniel's approval → a local commit. Never push without his explicit word.


## Parallel sessions and file ownership (Daniel, 2026-11-04; HISTORICAL: all parallel sessions ended 2026-11-06)
**Update (1b checkpoint): Daniel handed `build.py` (all geometry) to the staged-polish session.** The geometry session's open items (optic drive, generator, stair door, storage, windows) are folded into Stage 1 iterations 2–3. Its Iteration A was **committed with Daniel's OK** in `5f22e63` (iteration 2 checkpoint).

Two sessions worked on the cabin in parallel. **Daniel decided to split the work by layer.**

**Geometry: the "cabin repair" session (`CABIN_REPAIR.md`, Iterations A–D) owns:**
- `blender/build.py`, `documents.py`, `textures.py`, `photo_render.py`, `pipeline.sh`;
- the generated GLB and textures;
- the geometry repairs: optic drive, generator, stair door, storage, windows.

**Godot materials and lighting: the "staged polish" session (Stage 1 in `docs/ROADMAP.md`) owns:**
- `godot/scripts/fp/materials.gd`;
- `godot/shaders/room_pbr.gdshader` (new) and `rain_glass.gdshader`;
- `blender/sync_assets.py`, `settings.gd`, `outside.gd`;
- the lighting, probe and window-light functions in `station.gd`.

**Shared files (keep edits narrow):**
- `station.gd`: the material and texture list in `_swap_materials` belongs to geometry.
- `capture_fp.gd`: each session adds its own views.

**Names the lighting code depends on (keep them):** `GLS_window*`, `NDL_bearing`, `NDL_battery`, `NDL_temp`, `PT_brk_lights`, `LMP_cage`, `LIGHT_*`, `SM_CeilBeams`, `SM_WallLamps*`. New runtime interior meshes must use render layer 2 (`station.gd` `LAYER_INTERIOR`).

**After a geometry change, run both** `tests/test_last_light_hooks.py` and `godot/tests/interaction_test.gd`.

**Commits:** `4aff7b0` holds only Stage 1 steps 1.0 and 1a. The cabin-repair Iteration A is **still uncommitted** in the working tree, awaiting Daniel's review.

The staged-polish session won't edit `build.py` (needed for bevels, smooth shading and metric UVs in 1b) until the geometry session's iterations land.


Read this with `docs/ROADMAP.md`, which is now the **living stage tracker** (current stage and iteration, decisions, feedback log, next task), and with `docs/PROJECT_STATE.md`.

## Earlier status (2026-11-06, parallel G5 session: weather and audio; since committed as `0b3e750`, NOT checkpointed)
- **This session owns** (Daniel, 2026-11-06):
  - `audio/*` and `godot/assets/audio/*`;
  - `audio_director.gd`;
  - `outside.gd` (lightning);
  - `shaders/bolt.gdshader`;
  - the `_weather_step` hunk in `keeper_sim.gd`;
  - `tests/g5_weather_audio_test.gd` and `tests/test_last_light_audio.py` (workspace root).
- **Done:**
  - 29 bolts and 30 SFX are implemented;
  - for 33, a shortlist is in `audio/MUSIC_SHORTLIST.md`.

  Record and tests: FINDINGS_LOG "G5 implementation record". All suites pass except story, whose 3 failures are G2's.
- **Waiting on Daniel:**
  - the music pick (and whether the "released into the public domain by Musopen" wording is acceptable);
  - the OK for a Godot window capture of the bolt;
  - a listen (`renders/last_light/g5_listen_{before,after}.wav`);
  - the checkpoint, then a local commit of the G5 files only.
- **Gotchas:**
  - the audio WAVs are in git LFS: `git show HEAD:<wav> | git lfs smudge -- <wav>` recovers the old ones;
  - new WAVs need `tools/godot --headless --path … --import` before any `-s` test can load them (a test running in between logs missing-stream errors);
  - `-s` scripts can't compile `outside.gd` in `_init` (the `Settings` autoload isn't registered yet), so load it a frame later.

## Earlier status (2026-11-06, brief G2 committed, NOT checkpointed; continue in a new session)
- **Daniel: "push it and leave the rest for a new session".** Commits pushed to origin/main (public repo dani-aisystems/claude-blender-dev, a one-time push at his explicit request; the CLAUDE.md "never push" rule still applies otherwise).
- **G2 state.**
  - **Done:** items 4, 16 and 27 (commit `193fcf3`), then 8 and 9/20 (this commit):
    - flat-battery dark opening (D8-a): torch → valve → START → CHARGE → lights → console;
    - the `at_door_once` latch fixed;
    - step objectives with real-state ticks in a top-right panel (compact in device views);
    - concise objectives with nautical glosses; a terms legend in the chart transcription;
    - hints with `unless`;
    - save layout 3 with remap.
  - Also done: D7 (note_046 2.2.63) and the `log_1971` re-render, checked by eye (`renders/last_light/g2_docs_check.png`); D9 (in `193fcf3`).
- **NOT verified on the final G2 code.** The last full suite run was interrupted by the session ending, so first thing next session:
  - run all suites (story, regress, interaction, qa_sweep, sim_v2, run_tests, pytest). The last completed regress run was 200/201; the one failure was fixed after it, but the fix is not re-run;
  - capture the dark opening, the mission panel (free walk and radio view, text 1.0 and 1.5), and a pause-menu shot (ask Daniel before opening a Godot window);
  - then hold the G2 checkpoint with Daniel. Item 24 (seated at the radio) is a decision only and is implemented with G3.
- **Other sessions (stay out of their files):**
  - **G5 (audio and lightning, Daniel's own session):** `audio/*`, `godot/assets/audio/*`, `audio_director.gd`, `outside.gd`, `keeper_sim.gd`.
  - **Character session:** `character-refs/`, `blender/portraits*.py`, `visitor_figure.gd`, `NARRATIVE.md`. It also has D10 edits inside `STAGE3_NARRATIVE_MASTER.md`, which carries my §20b and D7/D9/log_1971 lines too; left uncommitted for that session to commit.
  - `dialogue_ui.gd`, `fp_ui.gd` and `speakers.gd` were released to the character session (portrait card integration) at `193fcf3`.
- **Still to do from the brief:**
  - G3: body and equipment;
  - G4: cabin assets, including D8's document re-render to the F15 hand, the I08/I09 captions and the console note texture (item 11, using CANON_INDEX §6 wording);
  - G6: menu, ending panels, credits.
- **Open decisions:** item 1 links; proposals 35–37; item 31.
- **Gotcha:** the scratchpad was wiped when the session restarted. The suite runner is a small bash loop over `tools/godot --headless -s res://tests/<t>.gd` under `timeout` and `taskpolicy -b`.

## Earlier status (2026-11-06, Daniel's 38-point brief: Phase A docs done)
- **Daniel sent a large brief.** It has 34 improvements, proposals 35–37, roadmap and log instructions, and a findings-log brief that arrived **truncated at its §4**. The plan was approved: `~/.claude/plans/the-last-light-cosmic-waffle.md`.
- **Daniel's decisions:**
  - documentation first, then work groups G1–G6, each checkpointed;
  - item 32: reuse the chapter-start fuel top-up once when the day tank runs dry, plus radio scenes that wait for power and power-aware hints;
  - item 12: the floor rose stays, and the chart compass is the pickup;
  - audio: SFX synthesised, music from a CC0 shortlist (no download before his pick).
- **Phase A written (docs only, no game changes):**
  - `projects/games/last_light/FINDINGS_LOG.md` (items 1–37);
  - `PROPOSAL_35_RADIO_CAST.md`, `PROPOSAL_36_TUTORIAL.md`, `PROPOSAL_37_JOURNAL.md` (all awaiting approval);
  - the ROADMAP section "Daniel's brief of 2026-11-06" plus the stage table;
  - PROJECT_STATE §5 item 13.
- **G1 implemented** (items 32, 7, 25, 23, 26, 21, 28, 3, 5). All suites green: story 0 failures, regress 188, interaction 159, qa 1,921, sim_v2, run_tests 95, pytest 18. Record: FINDINGS_LOG "G1 implementation record". Build v038 / GLB v036.
- **Uncommitted. Waiting on Daniel for:**
  - the G1 capture run (needs a Godot window);
  - whether to restore the churned doc and atlas PNGs (`pipeline.sh` regenerated `godot/assets/docs/*.png`, `T_LL_Photo`, `T_LL_Props` with new paper grain; the restore was blocked as an overwrite);
  - the commit.
- **Daniel added `projects/games/last_light/character-refs/`:** dossier images for Callum, Morag, Rory, Elspeth, Ross and Iain (Hector's folder is empty). These are the 3C / item 22 references; unread so far.
- **Open decisions:**
  - D8: the dark opening against the "41 %" lines in `ch1_lit` and `log_1971`;
  - the item 1 links;
  - the character profiles (22 and 3C still paused);
  - proposals 35–37;
  - item 31.

## Earlier status (2026-11-06, character session: references consolidated; portraits PAUSED by Daniel)
- **Character references: done as drafts**, in `projects/games/last_light/character-refs/`. Start with `README.md` (precedence, tags), then `CANON_INDEX.md` (single source of truth, document texts verbatim), `REVIEW_FLAGS.md` (every conflict resolved, with the rules used), `<id>/PROFILE.md` (callum, morag, rory, elspeth, ross, iain, plus hector as a secondary profile) and `sources/batch-01.md` (Daniel's text verbatim).
  - Daniel asked for all conflicts resolved with the AI dossiers as the reference. The dossiers decide looks, voice and backstory; shipped game text decides plot facts.
  - Still open:
    - G01: the rest of Morag's bible, which arrived cut off; ask Daniel to resend it.
    - G03: no Hector reference.
    - Final consolidation when Daniel says "ALL CHARACTER INFORMATION PROVIDED".
  - Check and sync: `tools/py projects/games/last_light/character-refs/tools/refs_check.py --sync` (OK, 52 flags).
  - Committed locally (text only). The dossier PNGs stay untracked: 19 MB, not LFS, and the repo is public.
  - regress_test after D5: 202 passed, 0 failed, 3 headless skips.
- **REVIEW_FLAGS §D follow-ups:**
  - D7 and D9 were done by the G2 session (`7ac1175`, `193fcf3`).
  - Done here, **uncommitted**: D5 (`visitor_figure.gd` oilskin black, not yet seen in game), D10 (master: character-refs pointer, Inquiry 17 Mar 1954, §5.3 order) and D11 (NARRATIVE.md "superseded" banner).
  - The master file also carries the G2 session's own uncommitted §20b/D7/D9/log_1971 lines. Commit it whole, with Daniel's OK.
  - D8 (document renders) belongs to the brief's G4.
- **Portraits (3C, item 22): PAUSED by Daniel (2026-11-06).** "I can provide images of each one I create … pause portraits for later when I am ready."
  - Don't resume the busts or build the portrait card until he sends images.
  - If his images are generated rather than drawn or photographed, the CLAUDE.md "no AI-generated images" rule needs his explicit call before they go into the game.
  - The probe stays uncommitted: `blender/portraits.py` (CC0 base meshes, surface-following hair curves with clumps, skin with flush, freckles and a lash line, resolved wardrobes, Ross silhouette mode, `--light lowkey`, Metal GPU) and `portraits_grade.py`.
  - The best result was low-key bible lighting plus the print grade. The faces still look CG and too similar to each other.
  - Known faults: Ross's face still reads in silhouette; Hector's beard is blob-like; Rory's cap reads as a helmet; Elspeth's hairline is hard.
  - Run: `tools/bl -P projects/games/last_light/blender/portraits.py -- --only callum --expr neutral --samples 48 --light lowkey --out <dir>` (about 1–1.5 min per portrait on the GPU).
- **3C scope still to do when portraits resume:**
  - the print card in the radio panel (170×190);
  - `expr` through `dialogue_ui._resolved`, with the key taken from the resolved speaker only;
  - Ross as a silhouette card even after `knows_name` (F12);
  - captures, including the 3B leftovers: the Calls box and the caption.

  `dialogue_ui.gd`, `fp_ui.gd` and `speakers.gd` were released to this session at `193fcf3`.

## Earlier status (2026-11-06, Stage 3B approved by Daniel and committed locally)
- **3A** (`dc87818`) and **3B** are approved and committed locally. Never push.
  - The untracked textures, base meshes, `cabin-photos/` and `.blend` v028–v030 and v032–v034 stay as they are.
  - v036 and v037 are this session's new versions (v036 is an intermediate build; v037 matches the GLB in Godot).
- **Master script approved by Daniel 2026-11-06** with fixes F1–F7.
  - `STAGE3_NARRATIVE_MASTER.md` §21 holds the fixes, and §21.1 the implementation notes, including the ch6 *Iona Star* hold-then-release change.
  - Playtime target: about 90 min.
- **What changed, the test results and the evidence:** ROADMAP Stage 3 log, "Iteration 3B". Sheets: `renders/last_light/s3b_pair_sheet_{1..3}.png` and `s3b_new_sheet_{1..3}.png`.
- **Tests (final code, headless):**

  | Suite | Result |
  |---|---|
  | story | 0 failures (all 4 endings plus variants; 13 autosave reloads) |
  | regress | 172/172 |
  | interaction | 159 checks, 0 failures, 12 sound warnings |
  | qa_sweep | 1,918/1,918 |
  | run_tests | 95/95 |
  | sim_v2 | no gate failures |
  | pytest | 18/18 |
- **Gotchas learned:**
  - The shell is zsh: `$G` holding a command is NOT word-split. Run the suites with a bash script (this session used a scratch `run_suites.sh`).
  - `pipeline.sh` reruns `documents.py`/`textures.py`. Their paper grain is unseeded, so every unchanged PNG churns. Restore the unchanged ones from HEAD, or run the build steps without them.
  - Vertex-based free-space probes miss big flat boxes (the radar cabinet has corner vertices only). Check placements with a top-down render.
  - A capture run can lose its game to a real key reaching the menu's focused button. `capture_fp` now swallows real input.
  - `jam_cleared` is cumulative; story beats use `jam_cleared_ch<N>`.
- **Daniel's 3B decisions:**
  - approved;
  - keep the ch6 rescue as built;
  - recapture the Calls box and the caption at 3C;
  - v037 is committed and v036 stays untracked.
- **Next:** plan 3C (portraits: `blender/portraits.py` from the CC0 base meshes, 6 characters × 3 expressions, a print card beside radio lines, Ross only after `knows_name`) and get Daniel's approval before building.

## Earlier status (2026-11-05, Stage 3 started: iteration 3A plus the master script)
- **Plan:** revision 2, approved by Daniel: `~/.claude/plans/the-last-light-stage3-plan-r2.md`. His decisions:
  - "targeted fill" lore scope;
  - the script written alongside 3A and reviewed at the 3A checkpoint;
  - about 90 min, measured later in Stage 6;
  - portraits on the radio, plus Ross in person after the reveal.
- **Master script (DRAFT, awaiting Daniel):** `projects/games/last_light/STAGE3_NARRATIVE_MASTER.md`. **Gate:** no `.dlg`, `chapters.json` or `docs.json` story rewrites until he approves. The only data edit so far is the ch1 objective, now using tokens.
- **3A code done:**
  - **Fonts.** The bundled OFL fonts are in `godot/assets/fonts/*`, pinned to google/fonts `fbe8181`, with each `OFL.txt` alongside and entries in `assets/ASSET_LICENSES.md`.
  - **Style.** `UIStyle` uses FontVariation plus a global text scale (group `ui_text`, driven from `Settings.apply`).
  - **Speakers.** `scripts/story/speakers.gd` is the identity resolver and line-look rules. It works with `DialogueRunner.present()`, and history entries are stored as shown.
  - **Parser.** `dialogue_db` accepts `>` sound captions, `SPEAKER@room|@radio:` and `SPEAKER(expr):`.
  - **Dialogue UI.** `dialogue_ui`:
    - lays the text out once and reveals it with `visible_characters`;
    - moves the identity line onto the name row;
    - holds the typewriter while a document or fade is up.
  - **Presenter.** The objective and hint share one VBox, and objectives resolve tokens.
  - **Backlog.** `scripts/ui/backlog_ui.gd` opens from the pause menu, H or pad View. It pauses the game, and `game_fp.open_backlog` / `close_backlog` keep `refresh_mouse` as the only mouse writer.
  - **Tests.** regress **R9** and qa_sweep at 0.8, 1.0 and 1.5.
- **New `class_name` gotcha:** after adding a `class_name` script, run `tools/godot --headless --path projects/games/last_light/godot --import` once. Otherwise every `-s` test hangs on "Identifier not declared".

## Earlier status (2026-11-05, cabin pass: Daniel's 8-photo brief, run before Stage 3)
- **Where it stands:** checkpoints 1–3 approved and committed (`91faeb1`, `9e0eeef`, `11b92d2`); **checkpoint 4 (final QA) approved by Daniel and committed.** Full log, the per-photo table (issue → root cause → fix → files) and a 7-step manual playtest: ROADMAP "Cabin pass".
- **Build:** v035 `.blend`, GLB v033, about 114k tris, 0 validation FAIL.
- **Tests (v035, headless):** regress 101/101, interaction 134/134 (7 warnings: documents have no sound), qa_sweep 948/948, story 0, sim_v2 no gate failures, run_tests 95/95, pytest 18/18.
- **Windowed regress 105/105** (no skips, twice). R6/R7 had failed windowed because the test waited a fixed 40 frames after a device-view enter or leave; at 120 Hz that can end inside the 0.45 s camera ease. `_settle_focus()` now waits for the ease itself. **When adding focus steps to tests, call it rather than a frame count.**
- **The mouse has one owner:** only `game_fp.refresh_mouse()` → `player.capture_mouse()` may change `Input.mouse_mode`. regress R8 checks this statically. Don't add a second writer in UI code.
- **Untracked on purpose:** `projects/games/last_light/cabin-photos/` (Daniel's photos) and `.blend` v028–v030, v032–v034 (Daniel: keep, don't delete).
- **Capture tool:** `cu_*` views now mute the player so the HUD prompt can't describe a different view. Torch and `fleet2` states aren't restored: put those shots last.
- **Stage 3** is still on hold: plan approved in principle, but Daniel has additions, so don't start 3A until he says go.

## Latest status (2026-11-05, Stage 1 iteration 5: cabin micro-detail)
- **Iteration 5 is approved by Daniel and committed locally.** It covers groups A–E: the desk, furniture, personal items and architectural fasteners.
- **Details:** the ROADMAP Stage 1 log, "Iteration 5". **Evidence:** `renders/last_light/s15f_vs_s15a_{a,b}.png` and `s15f_vs_s1_c.png`.
- **Build:** v026 `.blend`, GLB v024, 104k tris, 32 materials. All suites pass.
- **This session's files were** Blender/`tex`, `materials.gd`, the `station.gd` `_swap_materials` and PT_handset lines, the four desk views in `capture_fp.gd`, and its ROADMAP/REFERENCE_SPEC entries. Stage 2 (a parallel session) stages its own hunks only.
- **Bench done:** Medium +0–4 % median, inside budget rules; High desk +11 % median, at the threshold. See the ROADMAP for the suggested Stage 6 trim.

## Latest status (2026-11-05, Stage 2 approved by Daniel)
- **Stage 3 plan approved in principle (2026-11-05), but Daniel said "don't begin": he has additions.** The plan and all his decisions are in `~/.claude/plans/the-last-light-stage3-draft.md`: fonts, OFL exception, portraits, phone, optional content, script review, ch1, ending card, file ownership. **Do not start 3A** until his additions are folded in and he says go.
- **Commits (local, never pushed):** branding `0f18df3`; 2A `52bcb6f`; 2B `1359e44`; 2C `7a715c2`; 2D plus docs in the Stage 2 milestone commit.
- **Plan:** `~/.claude/plans/the-last-light-soft-hearth.md`. Audit, decisions and per-iteration logs: ROADMAP "Stage 2 log".
- **Tests at the stage end:**
  - regress 87/87 windowed (no skips), 84/84 headless;
  - interaction 134/134;
  - qa_sweep 948/948;
  - story 0 failures;
  - sim_v2 no gate failures;
  - run_tests 95/95;
  - pytest 18/18.
- **NOT TESTED (needs Daniel):** walking and look feel on his 120 Hz display; pad feel (he has no controller right now); the Options screen rows on screen.
- **If Daniel asks for another iteration:** stay in Stage 2; the iteration-5 session's work is committed (`81d9818`), so the tree has only Stage 2 changes.
- **How Stage 2 commits were made:** shared files were staged by reverse-applying the other session's hunks onto a temp copy (`git diff -U1` → keep only their hunks → `patch -R` → `git hash-object -w` → `git update-index --cacheinfo`). **Not** `git apply --unidiff-zero`, which mis-placed hunks.
- **Gotchas:**
  - a parse error makes a headless `-s` test hang idle; always run the suites under `timeout`;
  - `-s` test scripts can't name autoloads at compile time; use `root.get_node("Settings")`.

## Earlier status (2026-11-05, Stage 2 started)
- The plan was approved, branding was committed, the 6 leftover textures were deleted, and the "before" capture was taken from a worktree of `39fc0e7` (`renders/last_light/s2a_before_*`).

## Latest status (2026-11-05, later)
- **Stage 1 approved** and committed locally. Next: plan Stage 2 with Daniel (no implementation before he agrees the plan).
- New working rules:
  - windowed runs go through `tools/godot_bg` (no focus stealing, silent);
  - Medium is the default 60 fps preset;
  - the last few ms of frame time are tracked for Stage 6.

## Status (2026-11-05, earlier)
- **Stage 1** iterations 3b and 4 are done (uncommitted). The stage-end report has been presented, awaiting Daniel's verdict.
  - Matched sheets: `renders/last_light/s1f_vs_s0_{a,b,c}.png`.
  - Bench: High 27–29 ms median, **over the 16.7 ms budget**.
  - Open items: the blank radio card for narration lines; the oilskins not yet seen in Godot; 3 stale textures awaiting the OK to delete. Details are in the ROADMAP Stage 1 log.

## Status (2026-11-04, evening)
- **Stage 1:** iterations 1b and 2 approved and committed (`2559508`, `5f22e63`). **Next is iteration 3** (devices); see ROADMAP.

## Earlier status (2026-11-04, afternoon)
- **Done and reviewed:** Stage 0 (approved, commit `a7ffc25`), Stage 1 steps 1.0 and 1a (Daniel continued to 1b, commit `4aff7b0`).
- **Stage 1b:** the code is done but not committed. The **visual check is on hold until Daniel says the Mac is free.** Next step and the queued capture command are in ROADMAP.md, Stage 1 log.
- **Machine-load policy (Daniel):**
  - logic tests run headless at background priority (`taskpolicy -b … --headless`); all pass for 1b;
  - **ask before opening any Godot window**;
  - batch captures per checkpoint, at Auto resolution;
  - no benchmarks unless the Mac is free.
- **A parallel geometry session owns `build.py`** (see the ownership section above). Its Iteration A is uncommitted in the working tree, awaiting Daniel.

## Update: iteration 0.2 (same day)
Daniel asked for another iteration and selected every area: UI nits, the Retina fix, a play-issue sweep (controls, dialogue, visual and performance, menus, saves and audio), and more coverage. He gave no specific bug, so this was done as a self-run QA sweep. The full list is in ROADMAP.md, under "Iteration 0.2".

**Code changes:**
- `settings.gd`: `render_res` setting, `render_scale()`, `apply_render_scale()`.
- `main_fp.gd`: Render resolution option.
- `dialogue_ui.gd`: grow upwards, `_layout_choices()`, wrapped replies, italic scaling.
- `game_fp.gd`: `_on_settings_changed`.
- `story_presenter.gd`: chapter card moved up.
- `style.gd`: button padding.
- New `tests/qa_sweep_test.gd` and `audio/analyze.py`. `interaction_test.gd` now has the walkability flood-fill and the desk and document checks.

**Results:**

| Suite | Result |
|---|---|
| interaction | 134 checks, 0 failures, 6 warnings (no document sound) |
| qa_sweep (windowed) | 948/948 |
| regress | 40/40 windowed |
| story / sim_v2 / run_tests / pytest | all pass |

**Before/after of the reply layout:** `renders/last_light/s0_reply_before_after.png`, captured from a scratch worktree of `51cc8b9` (worktree removed afterwards).

**Still awaiting Daniel's Stage 0 approval.**

## Where we are
- Daniel started a **staged polish programme**. Each stage goes inspect → propose → agree → implement → validate, then needs **explicit approval** from him.
- He reviewed plan revision 1 and asked for changes. Revision 2 was approved and is saved at `~/.claude/plans/pasted-content-id-5a42-the-staged-crown.md`. The binding parts are copied into ROADMAP.md.
- **Stage 0 is implemented and waiting for Daniel's approval.** Do not start Stage 1 until he approves Stage 0.
- Stage 0's changes are **uncommitted**. Commit them as a local milestone only after approval, and never push.

## Stage 0: what changed
| Area | Change |
|---|---|
| Commit | `51cc8b9`: a local checkpoint of all session-1 work. The textures and base-mesh bundle stay untracked by design. |
| `scripts/ui/dialogue_ui.gd` | Replies moved lower-left above the speech panel. `mouse_restore_fn` and `_restore_mouse()` run before `choice_made`. `has_open_choices()`. Input, typewriter and `_pick` are ignored while paused. `_clear_choices` detaches immediately. |
| `scripts/fp/game_fp.gd` | `mouse_should_capture()` and `refresh_mouse()` are the single place that decides mouse capture. Pause, document close and focus changes all route through them. `ui.number_keys_taken_fn` is wired up. |
| `scripts/fp/fp_ui.gd` | No radio orders while paused. Number keys yield to open replies (`number_keys_taken_fn`). |
| `scripts/fp/player.gd` | New `pick()` and `_occluded()`, with the rules below. |
| `scripts/capture_fp.gd` | New views, forced-state suffixes `!dark`, `!flash`, `!gen_off` and `!dawn`, and flags `--quality=N`, `--nohud` and `--bench`. The plan view clips at the ceiling. The cutaway no longer hides the battery rack or the room's optic gears. |
| `blender/review_views.py` | Mirrors the new views, with `lens_for_vfov()`. |
| Tests | New `tests/test_last_light_hooks.py` with fixture `tests/fixtures/last_light_hooks_v006.json` (80 frozen hooks, 49 colliders). New `godot/tests/regress_test.gd` and `godot/tests/interaction_test.gd`. |
| Docs | ROADMAP rewritten as the stage tracker. PROJECT_STATE updated: decisions, tests, the performance finding. |

The new rules in `player.pick()`:
- a specific control beats its cabinet's info or focus volume;
- the focused device's own volume is ignored;
- only walls, floor, ceiling and stair occlude.

Before this, **START, all three breakers and the console mode/intensity knobs couldn't be targeted by the crosshair**.

## Evidence
| Item | Where |
|---|---|
| Baseline captures | `renders/last_light/s0_*` (19 shots), with sheets `s0_sheet_a.png` (room views) and `s0_sheet_b.png` (close-ups, plan, iso, focus views) |
| Reply layout | `renders/last_light/s0_regress_reply_layout.png` |
| Blender versions of the new views | `renders/last_light/blender_s0views_sheet.png` (rendered before `cu_door` was moved back to 1.75 m from the door) |
| Bench | `renders/last_light/s0_q{0,1,2}_bench.json` and `s0_q2_s50_bench.json`. Summary in PROJECT_STATE §5.1 |

**Tests: all green.** Commands are in PROJECT_STATE §4.

| Suite | Result |
|---|---|
| pytest | 18 pass |
| regress | 40/40 windowed, 38/38 headless |
| interaction | 93/93 |
| story_test | 0 failures |
| sim_v2 | no gate failures |
| run_tests | 95/95 |

## Key findings to carry into Stage 1
1. **Performance is fill-rate bound on Retina.** The window is 3840×2410 physical pixels.

   | Preset | 3D scale | Median frame time |
   |---|---|---|
   | High | 1.0 | 44–51 ms |
   | High | 0.5 (about 1080p-equivalent) | 18.1 ms |

   The default render resolution on HiDPI displays is a decision for Daniel.
2. **Lantern light leaks through the roof** (`fp_desk!dark`). With the room lights off, the walls and floor stay lit.
3. **Lightning lights the room uniformly through the roof**, not through the windows (`!flash`).
4. **Spoke shadows from the wall lamps** (`cu_lamp`). Green machinery reads as dark striped wood (`cu_console`, `cu_power`). The optic column shows white discs (`cu_optic`).
5. **Small UI issues for later stages:**
   - the chapter card overlaps the "Step back" prompt in the first seconds;
   - reply buttons have almost no left padding;
   - the radio ID card text was clipped in older captures (Stage 3).

## Next steps
1. Present the Stage 0 checkpoint and get Daniel's approval. (This handoff was written while waiting for it.)
2. After approval:
   - make the local commit: "THE LAST LIGHT Stage 0: gameplay blockers, interaction picking, QA tooling, baselines";
   - start **Stage 1, step 1.0**: the period-accuracy and story-readiness review, written into REFERENCE_SPEC.md;
   - then **iteration 1a** (lighting and import correctness), measured against the s0 captures and bench.

## Gotchas learned this session
- **Mouse mode in headless Godot:** the headless display server ignores mouse modes. Run `regress_test.gd` **windowed** for the real `Input.mouse_mode` checks; headless skips them and says so.
- **Vessel refresh:** `fp_ui._refresh_vessels()` runs every 30 frames and resets `selected_ship` to −1 when there are no ships. In tests, set the selection just before injecting a key.
- **Loads re-enter the beat:** loading re-enters the saved beat and re-runs its `do` actions (ch1 beat 0 sets mode and intensity to 0). This is by design. Test save/load from a beat that doesn't touch the station.
- **The door swings at 1.2 rad/s**, about 0.02 rad per frame. "Settled" checks need a tighter threshold than "moved" checks.
- **Units:** `sim.bearing` is in **radians**.
- **`COL_` colliders** are named `COL_x-convcolonly` in the GLB on purpose. The hook test requires the hint on `COL_` nodes and forbids hints everywhere else.
- **Metal GPU time:** `viewport_get_measured_render_time_gpu` returns 0 on Metal, so use frame time.
- **Corrupt-save errors:** `story_test.gd` prints two "Parse JSON failed" errors. They're expected, because it tests corrupt saves on purpose.

## Workspace cleanup candidates (NOT deleted; ask Daniel)
These are unchanged from session 1:
- `tests/debug_station.gd`;
- the v1 top-down code;
- the base-mesh zip;
- the stale `.app`;
- the scratchpad Godot export-template download.
