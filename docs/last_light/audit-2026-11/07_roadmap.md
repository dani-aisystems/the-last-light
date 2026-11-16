# THE LAST LIGHT: Document 7 and Addendum G: implementation roadmap and test matrix

> Audit of 2026-11-15 at commit `2b5d3ee`. Paths are relative to `projects/games/last_light/` unless they start with `docs/`, `assets/`, `renders/` or `tools/`; `g/` means `godot/`. Section numbers are those of the approved plan. Index: [README](README.md).

## 12. Roadmap

Each stage: inspect, implement, run every suite, capture and view, four-part checkpoint, Daniel's approval, local commit. Never push.

| Stage | Scope | Main files | Days | Depends on | Acceptance |
|---|---|---|---|---|---|
| 0 Baseline and documents | Windowed capture run of every reported issue; clean bench; timed dialogue total; write the audit documents into `docs/last_light/audit-2026-11/` | docs only; `capture_fp.gd` views | 3 | Daniel's OK for windows and a free Mac | Every register row has a capture or a stated reason; baseline bench recorded |
| A Critical systems | Save fixtures captured first; then D1, D2, D3, D4, D6, D9; generator lock; save version 2; `p1_alone` selection | `dialogue_ui.gd`, `story_director.gd`, `story_state.gd`, `keeper_sim.gd`, `station.gd`, `game_fp.gd`, `save_system.gd`, `settings.gd`, `.dlg` splits, tests | 9 to 10 | 0 | New regress groups pass; all suites green; every old fixture save loads and plays to the end |
| B Cabin and interface | C1 to C10; D5, D7, D8; documents; journal page | `blender/build.py`, `documents.py`, `fp_ui.gd`, `logbook_pages.gd`, `story_presenter.gd` | 7 to 8 | A | Matched before/after sheets; interaction_test extended |
| S Stairwell and door | Section 5 | `build.py`, new `stairwell.py`, `station.gd` | 5 to 6 | B | Open-door captures; collision test |
| P Player body | Section 4 | `body.py`, `hands.py`, `player_body.gd`, `equipment.gd` | 5 to 6 | none | Five comparison captures; sit tests |
| C Narrative | Script document for review, then sections 7.3 to 7.6 | `data/story/*`, `speakers.gd`, `chapters.json` | 10 to 12 | A; Daniel's script approval | story_test: all endings, new calls, canon checks |
| R Ross | Section 6 | new `ross.py`, `visitor_figure.gd` replaced, `game_fp.gd`, `.dlg` cues | 9 to 12 | S, A | Sequence captures on both door paths; lock tests |
| D Audio | Section 7.8; cough; foley; reverb; ducking | `audio_director.gd`, `synth.py`, assets | 5 to 6 | R, S; Daniel's download OK | Listening files approved by Daniel |
| E Sea and vessels | Section 9 | new `vessels.py`, `ship_view2.gd`, `outside.gd`, `ocean.gdshader` | 9 to 11 | 0 | Binocular QA sheet; bench within limit |
| F Radar, larger sea, fuel run | Section 10 | `radar.gd`, `layout.py`, `keeper_sim.gd`, `keeper_config.gd`, `chapters.json` | 9 to 11 | E, S, C | Route feasibility test; sim gates; fuel-run test |
| H Endings and score | Sections 11.2, 11.3; easter eggs | `ending_sequence.gd`, `panels.json`, `audio_director.gd` | 4 to 5 | Daniel's images and tracks | Each ending captured with its own panels and cue |
| G Integration | Full regression, performance pass, re-export, timed playthrough by Daniel | all | 5 | all | Test matrix green; bench within targets; measured runtime |

**Can start straight after approval:** 0, A, P, B. **Needs Daniel's material or decisions:** C (script review), D (download OK), H (images, tracks), new-voice portraits.

**Main risks.** Ross's figure failing to convince (mitigated by shadowed face and early capture checkpoint); the larger sea changing rescue timings (mitigated by seeded sim gates); performance on Medium already 1 ms over budget (every visual stage benched); scope, at 75 to 90 days (stages are independently shippable).

## 24. Document 7 in full: roadmap detail

**Stage 0, baseline and documents (3 days).** *Scope:* capture every reported issue in a silent windowed run; a clean bench when the Mac is free; reading-time totals per ending path; BVH contact scan; write Part II out as documents with the captures. *Files:* new files under `docs/last_light/audit-2026-11/`; temporary views in `g/scripts/capture_fp.gd`. *Dependencies:* Daniel's OK for the window batch and the bench. *Result:* every register row has evidence. *Alternatives:* skipping the captures was rejected, since five causes are still unconfirmed on screen. *Risk:* low. *Acceptance:* each U or P row becomes C or is re-investigated.

**Stage A, critical systems (9 to 10 days).** *Scope:* save fixtures first; non-skippable dialogue; paginator and fixed panel; portrait card; Tide Tables document and queued asides; generator lock; save version 2; release gating; `p1_alone`. *Files:* `g/scripts/ui/dialogue_ui.gd`, `g/scripts/story/story_director.gd`, `story_state.gd`, `story_presenter.gd`, `ending_sequence.gd`, `g/scripts/core/keeper_sim.gd`, `keeper_bot2.gd`, `g/scripts/fp/game_fp.gd`, `station.gd`, `g/scripts/save_system.gd`, `settings.gd`, `main_fp.gd`, `g/scripts/ui/credits_roll.gd`, `g/data/story/*`, `blender/documents.py`, tests. *Approach:* section 7.7, 6.3, 16. *Alternatives:* hand-splitting lines only (fails at large text); greying out START (rejected: the game teaches by trying). *Risks:* real-time tests slowing down (every human-mode test sets the test multiplier); measured wrap differing from the label's (2 to 3 px margin and an assertion). *Acceptance:* new regress groups pass, all suites green, every fixture save loads.

**Stage B, cabin and interface (7 to 8 days).** *Scope:* C1 to C10; draggable VHF panel; documents for Orders, diagram, card, teleprinter sheets; journal page; hint persistence; the 1953 tide volume. *Files:* `blender/build.py`, `spec.py`, `documents.py`, `textures.py`, `log_strips.py`; `g/scripts/fp/fp_ui.gd`, `station.gd`, `g/scripts/story/logbook_pages.gd`, `story_presenter.gd`; hooks fixture and tests. *Approach:* positions settled in Blender with a top-down check, then `pipeline.sh`. *Alternatives for the panel:* fixed re-layout only (simpler, but Daniel asked for dragging; both are done, since the new default removes the overlap even if the player never drags). *Risks:* removing `LIGHT_wall_4` changes shadow-slot assignment and the hooks fixture; document regeneration churning unrelated PNGs (diff before commit). *Acceptance:* matched before/after sheets; interaction_test extended; validation FAIL 0.

**Stage S, stairwell and door (5 to 6 days).** Section 5. *Files:* `blender/build.py`, new `blender/stairwell.py`, `g/scripts/fp/station.gd`, `materials.gd`. *Risks:* probe coverage of the lower level; the 33-material cap (the stairwell is a separate GLB). *Acceptance:* captures; collision tests.

**Stage P, player body (5 to 6 days).** Section 4. *Files:* `blender/body.py`, `hands.py`, `g/scripts/fp/player_body.gd`, `equipment.gd`. *Risks:* cloth-simulated garment deforming badly on the rig (bake the drape, then weight); frame cost of the body's shadows (already budgeted). *Acceptance:* five comparison captures; sit tests.

**Stage C, narrative (10 to 12 days).** *Scope:* a script document with every new and changed line for Daniel's review; then data. *Files:* new `SCRIPT_REVISION_2026-11.md` in the project folder; `g/data/story/ch1..ch6.dlg`, `chapters.json`, `g/scripts/story/speakers.gd`. *Gate:* no `.dlg` change before Daniel approves the script. *Risks:* section 17.7. *Acceptance:* story_test reaches all endings and every new call; a canon lint (names, dates, ages) passes.

**Stage R, Ross (9 to 12 days).** Section 6 and 20.4. *Files:* new `blender/ross.py`; `g/scripts/fp/visitor_figure.gd` rewritten to load and drive the model; `game_fp.gd`; cue actions in ch4 to ch6 `.dlg`. *Checkpoint inside the stage:* the three lit stills before animation work. *Risks:* the figure not convincing; clip timing against auto-advancing lines. *Acceptance:* frame series on both door paths; lock tests; no pop-in.

**Stage D, audio (5 to 6 days).** Section 7.8 and 18.4. *Files:* `g/scripts/audio_director.gd`, `audio/synth.py`, `audio/analyze.py`, new files in `g/assets/audio/`, `assets/ASSET_LICENSES.md`. *Dependency:* Daniel's OK on the CC0 download list. *Acceptance:* `analyze.py --strict` clean; Daniel approves listening files.

**Stage E, sea and vessels (9 to 11 days).** Section 9. *Files:* new `blender/vessels.py`; `g/scripts/fp/ship_view2.gd`, `outside.gd`, `ocean_waves.gd`; `g/shaders/ocean.gdshader`. *Risks:* frame time. *Acceptance:* binocular sheet for every vessel at three ranges; bench within the limit.

**Stage F, radar, larger sea, fuel run (9 to 11 days).** Sections 10 and 19. *Files:* `g/scripts/fp/radar.gd`, `g/scripts/core/keeper_sim.gd`, `keeper_config.gd`, `keeper_bot2.gd`, `blender/layout.py`, `spec.py`, `textures.py` (chart), `chapters.json`. *Risks:* the only stage that can change seeded outcomes; landed behind one setting with the sim gates run before and after. *Acceptance:* feasibility test, sim gates, fuel-run test.

**Stage H, endings, score, easter eggs (4 to 5 days).** Sections 21 to 23. *Dependency:* Daniel's nine images and fourteen tracks. *Acceptance:* each ending captured with its own panels; cue tests.

**Stage G, integration (5 days).** Full regression; performance pass; re-export of the app; Daniel's timed playthrough; documentation and handoff.

**Required fixes:** D1 to D6, D9, R1, R2, R5, R8, C1 to C3, C7 to C9, C11, M1, M2, E1. **Recommended:** D7, D8, R3, R4, R6, R7, R9, C4 to C6, C10, C12, M4, E2. **Optional expansions (now approved in principle):** story expansion, new voices, radar range and larger sea, fuel run, easter eggs, score.

## 13. Verification

- **Headless, after every stage:** `story_test`, `sim_v2` (seeds 1 to 5), `run_tests`, `opening_test`, `regress_test`, `interaction_test`, `qa_sweep_test`, `g5_weather_audio_test`, and `tools/py -m pytest -q`, each under `timeout` and `taskpolicy -b`, reading the `*_RESULT` line.
- **New test groups:** no-skip input sweep; three-line and fixed-panel measure; portrait fill; panel/radar overlap at three resolutions; document open/close for every document in every chapter; generator lock interval with save/load; sit-blend body tracking; door collider; every vessel model loads with outward normals; route feasibility; journal completeness; ending panel selection for all eight flag combinations.
- **Windowed, with Daniel's OK per batch:** `tools/godot_bg --path projects/games/last_light/godot -- --capture=NAME --shots=...`, PNGs viewed with Read; binocular, door, Ross, sit and ending sequences as frame series.
- **Blender:** `projects/games/last_light/blender/pipeline.sh`, validation FAIL = 0, reimport OK, versioned `.blend` saved.
- **By Daniel:** all audio by ear; a timed start-to-finish playthrough in Stage G.
- **Results reported** as PASS / PARTIAL / FAIL / NOT TESTED with evidence.

## 26. Phase 16 in full: test matrix

| Area | Check | How |
|---|---|---|
| Narrative | Events in order; all four endings reachable; new calls reachable | `story_test` campaigns |
| | Canon lint: names, ages, dates, call signs | new check in `story_test` |
| | Dialogue advances by itself; no input skips | `opening_test`, regress |
| | Three lines or fewer; fixed panel and card | `qa_sweep_test`, `portrait_test` (repaired) |
| | Documents become available on cue; journal in step with the story | `story_test`, `interaction_test` |
| Ross | Arrival sequence order and timing | `story_test` beat audit |
| | Generator locked for the interval; save and load keeps it | sim test, `story_test` |
| | Photograph appears, is picked up and opens | `interaction_test` |
| | No softlock on either door path | bot campaigns with the door open and shut |
| | Cough natural and placed | Daniel, by ear, from listening files |
| | Figure, light and motion | windowed frame series |
| Cabin | Each C-row | Blender top-down and BVH checks; matched captures |
| | Working compass still works | regress R15 |
| | Every interactable responds | `interaction_test` |
| Documents | Orders, diagram, Tide Tables, card open and close; state restored | `interaction_test` |
| Sea | Hulls closed; five distinct silhouettes | model validation; binocular sheet |
| | Motion plausible | windowed clips at three ranges |
| | No patches | windowed captures at bearing 000 and storm 1.0 |
| | Radar position matches world position at each range | regress |
| | Rocks drawn; routes feasible; far spawns arrive | route test, `sim_v2` |
| | VHF panel clear of the scope | regress at three resolutions |
| Player | Sit and stand without a glimpse | regress and frame series |
| | Sleeves bend; no hand intersection | captures per grip |
| Endings | Right panels per flag set; cue per ending; nothing skippable | regress R19 rewritten; captures |
| Technical | No missing assets or broken references; no unexpected errors in logs | import log scan in the suite runner |
| | Old saves load | `save_compat_test` |
| | Frame time, draw calls, VRAM | bench when the Mac is free |
| | Controls outside dialogue unchanged, including Space in menus | regress |

Headless results never stand in for a visual or audio check; each row above names which kind it is.
