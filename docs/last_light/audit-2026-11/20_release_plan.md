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
| R3 Endings and credits | Make every ending complete for a judge: Daniel's panel images if he has them, otherwise confirm the fallback reads well (captured). Agree the credits wording with Daniel. Under Q11 and Q12 there is **no AI line**, since R0 says none is required. The wording covers "A game by Daniel Yanchev", the music credit for his own score, the CC0 sources (`assets/ASSET_LICENSES.md`), the fonts' OFL notice and the system-font line. | Each of the four endings captured with its panels, cue and credits; credits wording approved |
| R4 Performance for judges | On a quiet Mac (Daniel says when): bench Medium and Low, plus High once if time allows, including E3's `--seafx` levels. Pick the default quality a judge's machine gets on first launch. If a cost is over budget, cap the sea level or a preset (no new tech). | Medium meets section G; the first-launch default is decided and recorded |
| R5 Builds | Export the macOS build. **Windows decision point at the end of R4:** if the organisers need Windows, ask Daniel before downloading the 4.7.2 Windows template. That build can be exported here but is NOT TESTED as running unless Daniel has a PC. Web is excluded (Forward+). Record the zip's size against any limit that turns up. Smoke-test the exported app windowed: launch, new game, one save/load, an ending skip if one exists for testing, quit. Handle signing honestly: an unsigned or ad-hoc app shows Gatekeeper's warning, so the submission says how to open it. | The exported app runs from the zip on this Mac; size and run notes recorded |
| R6 Daniel's timed playthrough | Daniel plays start to finish on the exported build. Claude records the time and his notes, and fixes only blockers, then re-exports. | Daniel approves the build |
| R7 Submission package | R0 asks for four things. (1) **The build**, with a short README / description: the story pitch, the controls, how to open it on macOS, the play time and the credits (no AI statement, per R0). (2) **Screenshots** from the `tools/godot_bg` capture states. (3) **A gameplay video or trailer**, decided at R7. Claude recommends that Daniel screen-records his R6 playthrough and Claude cuts it with ffmpeg into `renders/`; Movie Maker and the other session's `--film` are used only on his OK. (4) **The source code**: a `git archive` of the tracked files in `projects/games/last_light/`, plus their LFS content, after R1's sweep. It leaves out the other workspace projects, `character-refs/` and the raw `Music Tracks/` takes, and Daniel confirms the form. Local commit; never push. | Daniel has everything to submit |

## Backlog (after delivery)

- **Stage F:** radar ranges, the larger sea and the fuel run (section 10). The hand pump sound waits here.
- **Stage H, the rest:** easter eggs (Addendum D); any ending panels not done in R3.
- **E3 follow-ups:**
  - the paired bench of every `--seafx` level, if not done in R4;
  - the far-sea patches (PARTIAL: try the volumetric fog's range on the binocular camera);
  - removing `--sea=legacy`.
- **High preset to 25 ms** (P2 and P3 from the perf bisect).
- **A web (HTML5) build**, only if the organisers ask for one. It needs the Compatibility renderer and a visual pass, so it is not a release-track fix.
- **Stage G, in full:** the whole test matrix (section 26).
- **Cleanup, each on Daniel's OK:**
  - the merged branches `stage-c-data` and `stage-m-e2-merge`;
  - the superseded Ross `.blend` versions;
  - `music_menu.wav` and `music_tension.wav`;
  - the stale ROADMAP audit table.
- **Daniel's ear:** the Stage D sounds and the 15 score picks (any pick swaps in `audio/score.py` `PICKS`).
