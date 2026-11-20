# THE LAST LIGHT: release plan for the competition (2026-11-20)

Daniel has a competition coming up. The audit stages are reordered into a **release track**: only what a complete, deliverable build needs. Everything else moves to a **backlog** for after the build is delivered.

**The rule for the release track:** no new features or systems. Fix only what blocks or visibly harms a judge's playthrough. Everything else goes to the backlog with a note.

## Where things stand (main, `0eb146e`, local only)

**Done and committed:** stages 0, A, B, S, P, C, R, M, E (E1, E2, E3), D, and the music (the score system plus Daniel's 15 tracks). All suites are green, and `sim_v2` seeds 1 to 5 match Stage M's M0 reference exactly.

**Known state that matters for a release:**
- **Export:** a macOS export preset exists (`godot/export_presets.cfg` → `../build/TheLastLight.zip`), and the Godot 4.7.2 templates are installed. No Windows preset.
- **Performance:**
  - Medium is inside its budget (about 17.4 to 18.7 ms at the bench shots, Stage M's paired bench).
  - Low sits at the 60 Hz cap.
  - **High misses its 25 ms target** (28 to 39 ms on a loaded Mac); it was never cleanly benched.
  - E3's sea levels are not benched yet.
- **Endings:** `data/ending/panels.json` lists 12 panels; only the 3 generated log pages have images (`godot/assets/ending/`). Daniel's item 34 images (DECISIONS Q11) are not in yet. Before anything else, check what a judge sees for each of the four endings today.
- **Credits:** Q12 decides the wording. The game contains three kinds of AI-made material Daniel supplied: his ChatGPT portraits (Q13), the item 34 / 22 / photograph images (Q11), and his Suno score (Q16, Q27). Many competitions have rules on AI content and disclosure, so check them.
- **Uncommitted work belonging to other sessions** (leave alone unless Daniel says otherwise):
  - `CLAUDE.md`, `.claude/settings.json`;
  - ROADMAP's audit table;
  - two SESSION_HANDOFF hunks;
  - the `--film` hunk in `capture_fp.gd`;
  - the untracked `film_fp.gd`, `tests/portrait_test.gd`, and a `John Atanasov/` folder at the workspace root.

## R0 answers (Daniel, 2026-11-20)

| Question | Answer | What it changes |
|---|---|---|
| Deadline | "By next week I need to go through all essential stages, then overall 2 weeks". | **A submittable macOS build (R0 to R5) by Fri 2026-11-27**, and **the full package (R6, R7) by Fri 2026-12-04**. These dates are Claude's reading of his answer; Daniel corrects them if needed. |
| Platforms and build format | Not sure yet. | The macOS zip is the baseline. **Open:** Daniel checks the platform with the organisers by the end of R4. If they need Windows, Claude asks before downloading the 4.7.2 Windows template (R5). Web is out: the game uses Forward+ (backlog). |
| Size limit | None given. | Record the zip's size in R5 against any limit that turns up. |
| AI content and disclosure | Allowed, **no disclosure required**. | The credits keep Q11 and Q12 (no AI line). The README carries no AI statement either. |
| Length, rating, content rules | None given. | Record the play time in R6 (Daniel's timed run). |
| Submission | A written description, screenshots, a gameplay video or trailer, **and the source code**. | R1 gains a clean-checkout check. R7 gains the video and the source package. |
| Rules link | None given. | Open. Paste it here when there is one. |

**Facts checked at R0 (read-only):**
- Only the macOS export template is installed.
- `projects/games/last_light/build/TheLastLight.zip` dates from 4 Nov (94 MB) and is stale. R5 regenerates it.
- The renderer is `forward_plus`.
- `assets/ASSET_LICENSES.md` logs CC0 material and four OFL fonts, and has **no CC BY entries**.

## Release track (in order; each step has its own checkpoint)

**Schedule:** R0 to R5 by **2026-11-27** (a submittable build exists); R6 and R7 by **2026-12-04**.

| Step | What | Done when |
|---|---|---|
| R0 Requirements ✅ 2026-11-20 | Ask Daniel about the competition: the deadline; the platforms (macOS only, or Windows too); the build format and size limits; the rules on AI-generated content and how to disclose it; any required length, rating or content rules; and what must be submitted (build, description, screenshots, video, source). Write the answers into this file. **Done: see "R0 answers" above. The platform and the rules link stay open.** | The answers are recorded and the rest of the track is adjusted to them |
| R1 Release audit | A blocker hunt, not a feature pass. Run every suite. Scan the import and run logs for errors and missing assets. Play all four endings in bot campaigns (`story_test`) and once in human mode (`opening_test` pace) through to the credits. Check new game, continue, save/load (old saves too), pause, settings, quit, the menus and the credits. Capture one windowed set (`tools/godot_bg`) of the moments a judge sees first: the title, chapter 1's opening, the radio, the binoculars, the visitor's arrival, an ending, the credits. View every PNG. **Clean-checkout check (the source code is a deliverable, R0):** clone the local repo into the scratchpad and fetch its LFS objects. Import it headless and run `run_tests`. List every file the game needs that is untracked; the handoff flagged Stage P's `body_T_LL_*` / `hands_T_LL_*` textures. Sweep `projects/games/last_light/` for secrets and private references. | A blocker list with evidence, each item rated blocker / major / minor |
| R2 Fix the blockers and majors | Smallest fixes only, each with a test or capture. Minors go to the backlog. | The blocker and major list is empty; suites green; `sim_v2` identical |
| R3 Endings and credits | Make every ending complete for a judge. **Daniel generates all nine pending panels himself with AI (2026-11-20; covered by Q11's item 34 exception; R0 needs no disclosure):** `p1_wheel`, `p1_alone`, `p2_gut`, `p2_ledge`, `p4_correction`, `p4_heard_together`, `p4_nothing_tide`, `p4_nothing_pier` and `p4_light_exhibited`. The prompts, the style block and the spec (16:9, 3840 x 2160, no text in the image, Ross's face never readable) are in `E_ending_image_pack.md`. The three log pages stay rendered by `blender/ending_pages.py`. The files go to `godot/assets/ending/<id>.png`. Claude imports them, captures each ending's four panels and checks them against the pack. Any panel still missing at R5 falls back to the stand-in plate, which loses its "PANEL PENDING" label in R2 (F2). Agree the credits wording with Daniel. Under Q11 and Q12 there is **no AI line**, since R0 says none is required. The wording covers "A game by Daniel Yanchev", the music credit for his own score, the CC0 sources (`assets/ASSET_LICENSES.md`), the fonts' OFL notice and the system-font line. | Each of the four endings captured with its panels, cue and credits; credits wording approved |
| R4 Performance for judges | On a quiet Mac (Daniel says when): bench Medium and Low, plus High once if time allows, including E3's `--seafx` levels. Pick the default quality a judge's machine gets on first launch. If a cost is over budget, cap the sea level or a preset (no new tech). | Medium meets section G; the first-launch default is decided and recorded |
| R5 Builds | Export the macOS build. **Windows decision point at the end of R4:** if the organisers need Windows, ask Daniel before downloading the 4.7.2 Windows template. That build can be exported here but is NOT TESTED as running unless Daniel has a PC. Web is excluded (Forward+). Record the zip's size against any limit that turns up. Smoke-test the exported app windowed: launch, new game, one save/load, an ending skip if one exists for testing, quit. Handle signing honestly: an unsigned or ad-hoc app shows Gatekeeper's warning, so the submission says how to open it. | The exported app runs from the zip on this Mac; size and run notes recorded |
| R6 Daniel's timed playthrough | Daniel plays start to finish on the exported build. Claude records the time and his notes, and fixes only blockers, then re-exports. | Daniel approves the build |
| R7 Submission package | R0 asks for four things. (1) **The build**, with a short README / description: the story pitch, the controls, how to open it on macOS, the play time and the credits (no AI statement, per R0). (2) **Screenshots** from the `tools/godot_bg` capture states. (3) **A gameplay video or trailer**, decided at R7. Claude recommends that Daniel screen-records his R6 playthrough and Claude cuts it with ffmpeg into `renders/`; Movie Maker and the other session's `--film` are used only on his OK. (4) **The source code**: a `git archive` of the tracked files in `projects/games/last_light/`, plus their LFS content, after R1's sweep. **It includes the six gitignored CC0 interior texture sets** in `godot/assets/textures/` (303 MB; Daniel 2026-11-20, R1 finding F1): CC0 allows redistribution, so a judge's checkout opens textured. It leaves out the other workspace projects, `character-refs/` and the raw `Music Tracks/` takes, and Daniel confirms the form. Local commit; never push. | Daniel has everything to submit |

## R1 release audit (2026-11-20, main `73165c2`)

**Verdict: no blockers. Two majors (F1 resolved by decision, F2 for R2) and two minors for the backlog.** The evidence logs are in the session scratchpad; the PNGs are in `renders/last_light/` (`r1_judge_*`, `r1_full_*`, `r1_ch4_*`).

**Suites (headless, `taskpolicy -b`, judged by `*_RESULT` plus a "SCRIPT ERROR" grep):**

| Suite | Result |
|---|---|
| story_test | PASS. All four endings reached by 7 bot campaigns (correction ×2, nothing_to_report ×3, heard_together, light_exhibited) |
| run_tests | 95/95 |
| opening_test | 31/31 (chapter 1, human mode) |
| interaction_test | 164 checks, 0 failed, 1 old warning (no sound when a document opens, Stage 5) |
| qa_sweep_test | 7703 passed |
| save_compat_test | 305 passed (old saves) |
| regress_test | 501 passed |
| ross, ship_view, g5, music, audio_d | PASS. `ship_view`'s 0.4 ms check was re-run at normal priority (load 2.55): PASS |
| sim_v2 seeds 1 to 5 | **identical** to `renders/last_light/stageM/m0_sim_v2_seeds_1_5.json` |
| pytest | PASS |

**Log scan:** 0 `SCRIPT ERROR`s. Every `ERROR` line traces to a deliberate negative test or to the harness: the corrupt-save test, rejected links, and story_test's static dialogue walk, which runs with no sim.

**Windowed (`tools/godot_bg`):**
- the judge's-eye set `r1_judge`: 14 PNGs viewed;
- a full story run to the credits (`r1_full`): reaches the credits roll, 7 PNGs viewed;
- the chapter 4 visitor (`r1_ch4`, `r1_ross`): not tested at R1's commit, **PASS in R2**. Chapter 4 runs from about 1700 to 1980 s. With the door shut, "The man at the door" is a voice (`r1_ross_t1900`, `t1940`). At 2020 s Ross stands in the open stair door as a silhouette against the red stairwell light, his face hidden under the brim (`r1_ross_t2020_fp_stair.png`). The logs carry only the exit-time "resources still in use" notice.

**Clean checkout:** a clone at `73165c2` with its LFS objects imports without errors. `run_tests` 95/95 and `opening_test` 31/31 pass in the clone. The secrets sweep over 693 tracked text files is clean; the Instagram and email link is Q14's choice.

| # | Finding | Rating | Evidence | Action |
|---|---|---|---|---|
| F1 | A clean checkout lacks the six CC0 interior texture sets (303 MB, gitignored 2026-11-04). The room loads untextured and logs "Resource file not found". The exported build is not affected. | major (source only) | the clone's `opening_test` log; `.gitignore` lines 27–32 | **Resolved by Daniel's decision:** the R7 archive includes the textures. Verify by importing the extracted archive. |
| F2 | Every ending's stand-in panel shows the developer label "PANEL PENDING · P4_…" | major | `r1_judge_t100_player-ending_*.png`; `ending_sequence.gd:199` | R2: remove the label line. R3: Daniel's nine panels. |
| F3 | The `visitor` capture state forces Ross into chapter 1, slumped in the doorway. This is not what a judge sees. | none (capture tool) | `r1_judge_t096_*` | Judge the real staging from `r1_ch4`. |
| F4 | Chapter 3 with the room lights off (the battery duty) is nearly black apart from the windows, radar and lamps. | minor (design) | `r1_full_t1040/1100/1200_player.png`, `r1_ch4_t1300–1700_fp_stair.png` (the stair door barely visible) | Daniel's eye in R6. No change in R2. |
| F5 | The title's "Continue · Chapter IV · 16.20" entry is a leftover from tests in `user://saves_test`, which captures read. Daniel's `user://saves` holds chapter 1 saves. | none | the save headers | R5: confirm a fresh install shows no Continue. |
| F6 | Short in-room or thought lines sit left of centre while the speaker's name above them is centred. Long lines look centred. | minor | `r1_ross_t1940_fp_stair.png` ("Your father's boy."), `r1_ch4_t1700`, `r1_full_t960` | Backlog. |

## R2 blockers and majors (2026-11-20)

**Done: the blocker and major list is empty; the suites are green; `sim_v2` is identical.**
- **F2 fixed:** the stand-in plate no longer draws "PANEL PENDING · <id>" (`scripts/story/ending_sequence.gd`). Captures `r2_end_t100_player-ending_*.png` show only the italic subject on all four endings.
- **Test:** `regress_test` R19 now checks that the plate carries no developer label (502 checks, was 501). The old "p1 has no image" check would fail once Daniel's panels land in R3; it now accepts either state: the stand-in without its art, the image with it.
- **Suites:** all 13 PASS, 0 `SCRIPT ERROR`s, pytest PASS, `sim_v2` seeds 1 to 5 identical to M0. `interaction_test` shows 3 warnings, up from 1. They are the same old "no sound when a document opens (Stage 5)" warning, now on two more documents. The check counts live audio players right after the document opens, so it is timing-sensitive under `taskpolicy -b`; the F2 change does not touch documents or audio.
- **Note:** R3's `credits.txt` edit landed while the suites were running, so the later suites read the new credits text. The regress credits check passes on either text.

## R3 endings and credits (done, 2026-11-20)

**Credits (Daniel's choices: "Music by Daniel Yanchev"; the visitor stays "The man at the door"; the licence texts go in a file next to the app):**
- `godot/data/credits.txt`:
  - a "Music by Daniel Yanchev" section;
  - "Made with" corrected: Godot 4.7.2, and sound effects "synthesised for this game, with the recordings credited below". It no longer says every effect was made for the game or that the music was synthesised;
  - the nine Freesound CC0 recordings that play in the game, credited by author. The unused hand pump and steel-floor recordings are not credited;
  - the cast extended to all 13 voices in order of appearance;
  - a Licences line pointing to `THIRD_PARTY_LICENSES.txt`.
- Captured page by page with the new `tests/credits_shots.gd` (`r3_credits_p00`–`p02`, all viewed): every line is legible, and the ò in "Sgeir Mhòr" renders.
- **Licences:** the build shipped neither Godot's MIT notice nor the fonts' OFL texts; the export's `include_filter` takes only `data/*.txt`. The new `tests/make_licenses.gd` writes `THIRD_PARTY_LICENSES.txt` from the engine's own licence API (Godot MIT, 102 components, 19 licence texts) plus the four OFL texts. A test run produced 2,649 lines. R5 puts the file in the zip next to the .app.
- **Test:** `regress_test` R19 checks the new credits: the music line, Freesound, the licence pointer, the full cast, and no name for the visitor.

**Ending panels: done** (`e7074b6`, `b3343ae`).

**The panels:**
- **Source:** all nine came from Daniel, made in ChatGPT from the reference pack in `renders/last_light_ending_refs/` (game captures cropped clear of the HUD, plus portraits and three-angle face strips per panel).
- **Import:** the originals are committed in `Ending Card/`. `blender/ending_panels_import.py` maps each one to its panel id and crops it to 16:9.
- **Size:** kept at their native 1672 px. They show at about 1536 px and 1056 px at 1080p, and are imported without mipmaps, so a 4K upscale would add no detail and would shimmer.
- **`p4_heard_together`:** the source was portrait (1199 × 1312), so the panel is a 16:9 band around the hands (1199 × 674). Daniel kept the crop.
- **`p4_light_exhibited`:** "LIGHTHOUSE STATION LOG", "WEATHER" and "REMARKS" are legible at 1:1 on the page. That breaks the pack's no-text rule; Daniel kept them.

**Checked against `E_ending_image_pack.md`, all PASS:**
- Ross's face is never readable.
- `p1_wheel` has four hands, the oilskin and the darned navy cuff.
- `p1_alone` has one man. The handset by the wheel comes from the original pack prompt.
- `p2_ledge` sits upright on the sand with the crew on the bridge wing.
- Morag in `p4_correction` matches her portrait and has her notebook.
- `p4_nothing_tide`'s boat is dark and unlit.
- `p4_nothing_pier` has the flat cap and the pair a pace apart.

**`panel_grade.gdshader` bug, fixed:**
- **Cause:** in Godot 4, `COLOR` on entry to `fragment()` is already texture × vertex colour, and the shader multiplied its result by it again, so every panel was drawn squared.
- **Measured:** `p1_wheel`'s mean luma of 30.5 showed as 5.3 on screen; the prediction was 5.7.
- **Fix:** the vertex colour, which carries the crossfade modulate, is now passed through a varying.
- **Result:** at grade 0 every P1/P2 panel matches its PNG to within 0.3 of a level. The log pages were squared as well, but light paper hid it.

**Grade:**
- Photo panels: **0.3**. At 0.75 the duotone and halftone flatten the photographs to a muddy sepia (captures `r3p_t200`–`t226`: grades 0, 0.3 and 0.75 for all nine).
- Log pages: stay at 0.35 (`r3p_t227`, `t228`).

**Captures:**
- A capture step can now name a panel id (`p1_alone`, `p4_nothing_pier`); these two were unreachable before.
- **In motion:** `scripts/film_fp.gd --film_ending=<id>` plays an ending through the shipping path in Movie Maker. It sets the ending's flags, then fires the director's ending card: the music cue, the fade, the four panels, the lines and the card.
- `renders/last_light/r3_ending_correction.mp4` (95 s) runs the fade to warm black, `p1_wheel` for about 10 s, `p2_gut` about 10 s, the log page about 13 s, then `p4_correction` with its three lines fading in one at a time (about 31 s), then the closing card. The card closes 80 s after the ending trigger.
- **Sound:** measured, not listened to. It is never silent (−24 to −36 dB per second), with phrases rising at about 31, 62 and 87 s.
- **NOT TESTED:**
  - the move into the credits (the film stops 10 s after the card);
  - the other three endings in motion. Their panels are checked as stills, and `story_test` checks their panel order.

**Suites** after the shader and capture changes: all PASS (`story_test` 0 failed, `run_tests` 95/95, `regress_test` 502/502, `ross_test` 42/42, `opening_test` 31/31, `interaction_test` 164 checks with 0 warnings, `sim_v2` gates clean, pytest PASS). One `regress_test` run failed R30 ("she comes out of the murk over 3 s", half at 1.37 s against 1.5 ± 0.1) and passed on the rerun (1.48 s). This is a timing-sensitive check, logged in the backlog.

## R4 performance (in progress, 2026-11-20)

**Setup:** focused benches on Daniel's M3, which he left alone for the run (his OK, 20:34–20:44). Command: `tools/godot --audio-driver Dummy … --bench --novsync --bench_secs=20 --bench_shots=fp_desk,fp_window,fp_gen,fp_bino --quality=Q --seafx=L`. The window is fullscreen Retina, 3840 × 2410, so Auto renders 3D at 0.36 / 0.43 / 0.47 (about 1650 px wide on Medium). The JSON is in `renders/last_light/r4f_*_bench.json`.

**Results:** median / p95 in ms, focused shots only. The two first Medium runs (r1) reported themselves unfocused and are not used. The earlier `r4bench_*` runs were all unfocused.

| Preset, sea level | Desk | Window | Gen | Binoculars | Verdict |
|---|---|---|---|---|---|
| Low, 5 | 16.69 / 17.75 | 16.70 / 17.65 | 16.68 / 17.66 | 16.66 / 17.85 | PASS: at the 60 Hz cap |
| Medium, 5 (r2) | **17.70** / 18.75 | **18.02** / 19.63 | 16.63 / 17.04 | 16.73 / 17.22 | p95 PASS; median **FAIL** at the desk and window, 1.0–1.3 ms over 16.7 |
| Medium, 0 (r2) | 17.83 / 19.00 | 17.91 / 19.14 | 16.65 / 16.93 | 16.68 / 17.07 | same |
| High, 5 | 27.56 / 28.66 | 27.67 / 28.86 | 26.65 / 27.96 | 25.51 / 26.66 | FAIL against 25 ms (known; backlog P2/P3) |

**Findings:**
- **Sea level:** level 5 against 0 is within ±0.13 ms on every view, so the shipping level 5 stays.
- **VRAM:** PASS, at 1.08 / 1.18 / 1.32 GB against the 1.4 GB budget.
- **Medium is about 2 ms slower than after the perf bisect's P1** (17.7 here against about 15.7 expected). Later stages (M, E3, D) added cost.

**Trying a render-scale cap:** Medium's scale was lowered from 0.90 to 0.85 (`--scale3d=0.4023`) to test it. Focus was lost in both runs. The one focused shot, the desk on r2, read 17.37 / 18.71, about 0.3 ms better. The desk is not resolution-bound, so the scale cap is dropped.

**Next:**
- Try the bisect's **P2**: volumetric fog on Medium at 48 froxels instead of 64. In the bisect, fog cost 2.5 ms at the desk and 4.5 ms at the window.
- Then, if needed, **P3**: fewer glow levels on Medium.
- One focused bench pair, plus before and after captures of the beam through the windows.
- The first-launch default stays Medium until then. Daniel's decision is to keep Medium's look and trim it, not drop to Low.

## R5 macOS build (first export, 2026-11-20, main `d98db0b`)

This is an early build. It will be re-exported once Daniel's panels (R3) and the first-launch quality (R4) are in.

| Check | Result | Evidence |
|---|---|---|
| Export (`--export-release "macOS"`, template 4.7.2.stable, matching the engine) | PASS, 64 s, no errors or warnings | the export log |
| Size | **zip 248.4 MB** (248,359,592 bytes, including `THIRD_PARTY_LICENSES.txt`); the app is 366 MB unpacked (binary 171 MB, pck 211 MB). No size limit is known yet (R0). | `ls`, `unzip -l` |
| pck contents (911 files, read by a pck parser) | PASS. All 17 data files the game reads (dialogue, `chapters.json`, `music_cues.json`, `credits.txt`, `panels.json`, `docs.json`, …) are in; no `tests/`, capture, autotest or film scripts. Only the four fonts' `OFL.txt` are absent; `THIRD_PARTY_LICENSES.txt` in the zip covers them (R3). | `pck_list.py` |
| Licence file | PASS. `THIRD_PARTY_LICENSES.txt` is next to the app in the zip (Godot MIT, 102 components, 19 licence texts, 4 OFL texts). | `make_licenses.gd`, `unzip -l` |
| Headless boot of the exported binary | PASS: to the title, 900 frames, clean exit; only the usual exit-time leak notices | headless log |
| Windowed boot at the title (`open -g -j`, Dummy audio, `--quit-after 1800`) | PASS: Metal 4.0, Forward+ on the Apple M3; clean self-quit. The frontmost app differed afterwards (ChatGPT → Electron), possibly Godot's one-time activation. Future launches use `godot_bg`'s focus guard. | window log |
| Bundle | universal (arm64 + x86_64), `com.danielyanchev.thelastlight` 1.0 (1), © 2026 Daniel Yanchev | `lipo`, Info.plist |
| Signing | ad-hoc with the hardened runtime; `codesign --verify --deep --strict` OK. **Gatekeeper rejects it** (no Developer ID, no notarisation), so a judge must allow it once under System Settings → Privacy & Security → Open Anyway. The R7 README says so. | `codesign`, `spctl` |
| New game, save, load, an ending, quit in the exported app | **NOT TESTED** by Claude. A release build always uses the real `app_userdata/The Last Light/` folder (`XDG_DATA_HOME` does not redirect it), so a new game would autosave over Daniel's `slot_auto.json`. Daniel does this click-through (or R6 covers it). Daniel's save was verified unchanged (md5) after both boots; Godot did add a log file to that folder's `logs/`. | md5 before and after |
| Fresh install shows no Continue (F5) | NOT TESTED, for the same reason. | |

The stale `build/The Last Light.app` folder from 2026-11-04 is still next to the zip. Whether to delete it is Daniel's call.

## Backlog (after delivery)

- **Stage F:** radar ranges, the larger sea and the fuel run (section 10). The hand pump sound waits here.
- **Stage H, the rest:** easter eggs (Addendum D); any ending panels not done in R3.
- **E3 follow-ups:**
  - the paired bench of every `--seafx` level, if not done in R4;
  - the far-sea patches (PARTIAL: try the volumetric fog's range on the binocular camera);
  - removing `--sea=legacy`.
- **High preset to 25 ms** (P2 and P3 from the perf bisect).
- **R1 minors:** F4, chapter 3 and 4 near-black with the room lights off (Daniel's eye in R6 first); F6, the alignment of short subtitle lines against the centred speaker name.
- **A web (HTML5) build**, only if the organisers ask for one. It needs the Compatibility renderer and a visual pass, so it is not a release-track fix.
- **Stage G, in full:** the whole test matrix (section 26).
- **`regress_test` R30 is flaky** ("she comes out of the murk over 3 s"): it steps `tick` with a fixed dt, yet the half-way time moved between runs on the same code (1.37 s, then 1.48 s, against 1.5 ± 0.1). Something outside the loop advances the fade (`await _frames(1)` before the loop, or the view's own process). Make it deterministic.
- **Cleanup, each on Daniel's OK:**
  - the merged branches `stage-c-data` and `stage-m-e2-merge`;
  - the superseded Ross `.blend` versions;
  - `music_menu.wav` and `music_tension.wav`;
  - the stale ROADMAP audit table.
- **Daniel's ear:** the Stage D sounds and the 15 score picks (any pick swaps in `audio/score.py` `PICKS`).
