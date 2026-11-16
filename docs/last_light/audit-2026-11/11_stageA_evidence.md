# THE LAST LIGHT: Stage A evidence (critical systems), 2026-11-16

Stage A of the audit plan, started on Daniel's word ("Continue to next stage") after Stage B was committed (`797cff3`). Index: [README](README.md). Build: `last_light_v067.blend`, `watch_room_v056.glb`.

**Status:** A1 to A7 are done. The decisions were delegated by Daniel ("determine all choices ... according to suggested") and are recorded as DECISIONS Q17. Only the performance bisect is left from the plan's Stage A list. It needs a foreground bench when Daniel says the Mac is free.

## 1. What changed

| Phase | ID | Change | Where |
|---|---|---|---|
| A1 | Save fixtures | 70 version-1 saves recorded before any story change: every autosave point of a full campaign (door opened), plus the door-shut campaign from chapter 4, where the paths split. Each file is exactly what the game writes, plus a `fixture` block with the beat id. | `tests/make_save_fixtures.gd`, `tests/fixtures/saves_v1/` (2.5 MB) |
| A1 | Save v2 | Saves name their beat (`beat_id`) as well as its index. On load the director places the save by id. A renamed or merged beat is found through `chapters.json` `beat_aliases`, and `backfill` gives older saves the flags a later story change adds. A v1 save still loads by the old index remap. `SaveSystem` is now version 2: an older file is migrated on read and copied once to `slot_<slot>_v1_backup.json`; a file from a newer build is refused instead of misread. | `save_system.gd`, `story_director.gd` (`save_data`, `load_data`, `resolve_beat`, `_apply_backfill`), `game_fp.gd` |
| A1 | Compat test | New permanent `save_compat_test.gd`, checks S0 to S7: every fixture migrates, loads onto its beat, and resumes with a new conversation (never one it already played). One fixture per chapter and door path plays on to an ending (`--full`: all of them). It also covers the v2 round trip, the id beating a stale index, aliases (including an alias of an alias), backfill before and after its beat, and file migration with its backup. | `tests/save_compat_test.gd` |
| A2 | D1 | No line can be finished early or skipped. Space and RT are gone from the input map, and nothing in the dialogue layer reads input except the replies. Every line advances by itself after its reading time: radio, in-room, thought and sound alike. Radio lines used to wait for Space. The reading time is 1.0 s + 0.06 s per character, clamped from 2.8 to 12 s (was 9). A change of speaker adds 0.7 s, a closing full stop 0.4 s, and Options > Accessibility > **Reading time** scales it all from x0.75 to x3. Time under pause, a document or a fade does not count. The ending's panels and card advance only on their own clocks, also scaled by Reading time. The credits lose the Space speed-up; Esc still leaves them. The controls list no longer shows "Continue dialogue". | `dialogue_ui.gd`, `input_setup.gd`, `story_presenter.gd`, `ending_sequence.gd`, `credits_roll.gd`, `settings.gd`, `main_fp.gd` |
| A2 | D2 | E on an examinable while a conversation (or a transition) holds the story used to be dropped. It is now queued (at most 3, once each) and said as soon as the story is free; a queued aside is dropped if the chapter changes. | `story_director.gd` (`play_aside`, `_aside_queue`) |
| A3 | D3 | No message shows more than three lines. A long message is shown as pages: whole sentences where they fit, else clauses, else words, and each page is read and timed like a line of its own. The split is measured with a `TextParagraph` using the label's own font, size and wrapping, less a 3 px safety margin. The radio panel is one fixed size per text size: the text box is exactly three lines, and the identity and hint rows reserve the most lines any speaker needs. Lines paged: 3 at text x0.8, 16 at x1.0, 72 at x1.5. | `dialogue_ui.gd` (`paginate`, `line_count`, `fix_heights`) |
| A3 | D4 | The portrait fills the card edge to edge, cover-cropped (never stretched), inside a 2 px dark keyline. The cream margin and the band that grew under the photo are gone, and the card is always 152 x 190. Callers without a print keep the paper card and drawing. | `dialogue_ui.gd` (`_draw_card`, `photo_rect`, `cover_src`) |
| A4 | D6 | The Tide Tables open as a document: the 1953 volume at Stornoway, November 1953. The figures are **invented** for the game: a plain semi-diurnal series with springs about the 7th and 21st, 15 ft at springs and 8 ft at neaps. The Grant's thought is now the Tables' after-read line (any chapter, as before), queued if the story is talking. | `documents.py` (`tide_page_1953`, `tide_rows_1953`), `game_fp.gd`, `station.gd` |
| A4 | Canon 7.5 | A fourth, faded 1953 volume at the end of the Tables row (the dialogue's "Admiralty Tide Tables, nineteen fifty-three"). Its spine sits in the free strip of the props atlas, and the examine box is moved over all four volumes. `documents.py --extra=<ids>` now renders only the documents named. | `spec.py`, `build.py`, `documents.py` |
| A5 | Generator lock | The story faults `gen_out` and `gen_restore`. At the chapter 4 stair a running engine runs down ("fouled"); START turns over for 2.5 s and dies, with Callum's line; the cells cannot fall below 30 %, and the floor lifts once the engine has run again. The test bot never cranks a locked engine. Chapter 5 has a new beat, `bowl`, after the letter: the duty **Drain the sediment bowl**. The new device on the fuel line (`IA_sediment_bowl`: filter head, glass bowl with diesel, brass drain cock) refuses with a spoken reason until the story opens the step, then drains and clears the lock. The chapter 5 overheat touches only a running engine, and its blackout line about the engine shows only if it is running. Beat layout 4 (ch5: story, drawer, bowl, morag, mayday, power), with the v1 remap. The new lines are DECISIONS Q17. | `keeper_sim.gd`, `keeper_bot2.gd`, `station.gd`, `game_fp.gd`, `story_director.gd`, `story_state.gd`, `chapters.json`, `ch4.dlg`, `ch5.dlg`, `build.py` |
| A6 | D9 | The developer flags (`--capture`, `--autotest`, `--bot`, `--bench`, `--load`, ...) work only in debug builds; a release build ignores every one. `SaveSystem.isolated()` is false in a release build. The capture, autotest and film scripts are loaded only when used and are left out of the export. | `game_state.gd`, `save_system.gd`, `main_fp.gd`, `main.gd`, `export_presets.cfg` |
| A7 | E1 | Ending panel 1 is "two men to one wheel" only if Ross took the wheel (`ross_wheel`). Otherwise it is the new `p1_alone` ("One man at the wheel"; a stand-in plate until Daniel's image). | `story_director.gd`, `data/ending/panels.json` |

## 2. Verification

| Check | Result | Evidence |
|---|---|---|
| Release export ignores the flags | PASS | Exported with the release template into the scratchpad (the existing `build/` untouched). Run headless with `--autotest=3 --bot=expert --capture=d9probe`: no result line, no capture file, still at the title when the 45 s timeout hit. The pack contains no `capture_fp`, `capture.gd`, `autotest`, `film_fp` or `tests/` entries. |
| Tide Tables document | PASS by eye | `godot/assets/docs/tide_tables.png`: times run in order through each day, 14 November 1953 falls on a Saturday |
| Fourth volume | PASS | Blender `renders/last_light/a4_v065/cu_shelf.png`. Contact check: each volume touches only its own page block. Pipeline: validation FAIL = 0, reimport ok |
| Headless suites | see section 3 | |
| In-game captures (window batch, Q17) | PASS by eye | `renders/last_light/a1_t06*.png`. Gale warning page 1 and page 2 in the same panel at text x1.0. At x1.5 the panel is taller and fixed, and the identity wraps inside its reserved rows. Morag's photo fills the card with only the thin keyline. The Tide Tables open full-screen. The shelf shows four volumes. The bowl reads (amber glass under the black filter head) but sits in a dim corner of the cage |
| Sediment bowl in Blender | PASS | `renders/last_light/a5_bowl/cu_bowl.png`. Contact check: the filter head touches only its collar and the fuel line it clamps; the bowl and diesel touch nothing. Pipeline v067: FAIL = 0, reimport ok |
| Generator lock, campaigns | PASS | All 7 story_test campaigns (3 policies, 4 endings, door shut): locked from `ch4:steps`, cleared at `ch5:bowl`, the engine ran 0 steps while locked, lowest cells 63 to 72 %. Unit check: the floor held at 30.0 % over 900 s at lamp HIGH; save and load keep the lock; the drain is refused before the letter and clears the lock after it; the engine catches and the floor lifts |

**Side effect to note:** the release run read Daniel's real autosave for the menu's Continue line. That save is version 1, so it was copied once, as designed, to `slot_auto_v1_backup.json` and `slot_auto_prev_v1_backup.json` beside it. The originals are unchanged.

## 3. Suites

Final state, headless under `taskpolicy -b`, 2026-11-16.

| Suite | Result | New in Stage A |
|---|---|---|
| save_compat_test (new) | PASS (305 checks) | the 70 fixtures; 11 played on to an ending |
| story_test | PASS (0 failed) | ending P1 for 9 flag sets, including 3 `p1_alone` cases; the door-shut campaign must end on `p1_alone`; save v2 round trip and autosave resumes |
| opening_test | PASS (31 / 31) | O6 rewritten: a real Space key neither finishes nor advances the radio check's line; it moves on by itself |
| regress_test | PASS (391 / 391, 4 headless skips) | R25: Space, held Space, Enter, Tab, a click and RT never finish or advance an in-room, radio or thought line. Each line advances on its own clock at its reading time (8.9 to 9.3 s against 8.9 s). Reading time x2 doubles it and nothing goes below x0.75. No `dialogue_next` action is left. The Tide Tables open during a radio call and their thought is said as the call ends. D9 source and export checks. R11b, R19 and the ending card now run without input. R20: the photo fills the card inside its keyline, cover-cropped, and the card stays 152 x 190 at x0.8 and x1.5 |
| qa_sweep_test | PASS (5,854) | every page of every line in all six chapters, at x0.8 / x1.0 / x1.5: three lines or fewer, the pages join back to the line, the radio panel is the same rect for every line (222 px at x0.8 and x1.0, 340 px at x1.5), and the card is never stretched |
| interaction_test | PASS (159 checks, 12 warnings) | the Tide Tables now open and close as a document. The extra warning is the standing "documents open with no sound" note (Stage D) |
| g5_weather_audio_test | PASS (50) | |
| run_tests | PASS (95) | |
| sim_v2, seeds 1 to 5 | PASS, no gate failures | |
| pytest | PASS | |

One regress check failed in the full run and was fixed in the test: it timed a line from the start of its timing loop, not from when the line appeared, so a loaded machine made 8.3 s look short of 8.9 s. It now reads the dialogue layer's own on-screen clock.

**Suites after A5** (the final state): save_compat 305; story_test 0 failed (with the lock checks); opening 31 / 31; regress 391 / 391; interaction 164 checks, 0 failed (the bowl: reachable, picked from 0.6 to 1.6 m, drains, unlocks, sounds); qa_sweep 5,881; g5 50; run_tests 95; sim_v2 no gate failures; pytest PASS.

## 4. Decided (Q17) and still open

- **Decided, as suggested:** the lock's length and lines; J unchanged; the window batch run; a local commit.
- **Open:** the performance bisect, which needs a foreground bench when Daniel says the Mac is free (Stage 0: Medium 27 to 30 ms against 16.7). It is the first thing to do in the next session, before any stage that costs frame time.
- **Notes for later stages:**
  - the stair door is dark (0.032 luminance; Stage S);
  - the bowl corner is dim (it could take a small catch-light in Stage S or G);
  - the documents' missing open and close sounds (Stage D);
  - the four ending images and `p1_alone` art (Stage H).
