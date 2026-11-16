# THE LAST LIGHT: Stage B evidence (cabin and interface), 2026-11-16

Stage B of the audit plan, started on Daniel's word ("Start stage B") with Stage A still to do. Index: [README](README.md). Build: `last_light_v064.blend`, `watch_room_v053.glb`.

## 1. What changed

| ID | Fix | Where |
|---|---|---|
| C1 | The well-glass lamp over the stair door (`LMP_wall_4`, `LIGHT_wall_4`) is gone. Wall lamps 2 (148) and 3 (-160) light the door. It cast no shadows on any preset, so no shadow slot moves. | `build.py` `build_stair` |
| C2, C3 | West wall re-planned. The charger moves from -55 to -61.5 and narrows from 0.85 to 0.76 m, so its right edge (-54.8) is 13 cm clear of the west bay's jamb (-52.5). The supply diagram hangs centred over it (frame 1.925 to 2.275 m, 7.5 cm above the cabinet top). All four conduits enter at the cabinet's ends (`CHARGER_GLANDS`), clear of the diagram. Lamp 0 moves from -62 to -70, into the gap between the distribution board and the charger. | `spec.py` `charger`, `wall_lamps`; `build.py` `build_power`, `build_conduits`, `build_props` |
| C4 | Stair-door handwheel: a hub with a cap nut, five round spokes, and a rim with a grip bulge per spoke (the old diagonal "spokes" were unrotated 17 cm boxes that formed a brass square). Each lever dog is now a wedge block, a lever on a pivot bolt with a hex nut, and a rounded handle end. Animation is Stage S. | `build.py` `build_stair` |
| C5 | The coat drape is 4.5 mm thick (was 2), and the settled cloth gets four smoothing passes before the thickness goes on. It now has its own bucket (`SM_CoatCloth`), shaded smooth with no 35-degree split; that split had turned every tight fold into a hard ridge. | `coat_cloth.py`; `build.py` `build_coat_rack`, `SMOOTH_ONLY` |
| C7 | Mug moved from (0.62, back - 0.62), where it stood 1.9 cm into the pipe's ashtray, to (0.70, back - 0.50): beside the radar case, 11 cm from the ashtray. | `build.py` `build_desk_detail` |
| C8 | The brass bearing dial on the chart is removed. The working hand compass on the east sill is untouched. | `build.py` `build_desk` |
| C9 | Radio-check card lowered from y 0.122 to 0.108, so only its top edge tucks under the bezel. | `build.py` `build_desk_detail` |
| C10 | Binoculars moved 4 cm toward the room and 1 cm left; an objective was 1.3 cm into the phone's plinth. | `build.py` `build_desk_detail` |
| D5 | VHF panel: default width 330 px (was 430), 24 px from the right edge, so at 1080p it runs from x 1566 to 1896. The scope's projected rim ends at x 1478 at 16:9 and 1535 at 16:10, which leaves gaps of 88 px and 31 px. The panel's buttons had a fixed 380 px minimum width that held it at 424 px; their labels now wrap instead. The title row is a drag handle, clamped on screen, with the position kept in Settings (`vhf_pos`, as a fraction of the screen). A double click puts it back. The title accepts the press, so it never reaches the room. | `fp_ui.gd`, `settings.gd` |
| D7 | KEEPER'S ORDERS, the supply diagram and the radio-check card open in the document viewer (`orders`, `diagram`, `radio_card`). They are drawn by the same code that paints them into the atlases (`textures.notice` at 2x, `documents.wiring_diagram`, `documents.sked_card` at 3x), with transcriptions. Reading the Orders still sets `used_orders`, so the fuel-valve step is still learned there. New volumes: `IA_diagram`, `IA_radio_card`. `documents.py --extra` writes only these three, so no other document PNG changes. | `textures.py`, `documents.py`, `build.py`, `station.gd`, `game_fp.gd` |
| D8 | A step's hint, once given (60 s without progress, or at once on Full guidance), is recorded in the saved story state (`duties[id].hinted`). The Duties page then keeps it pencilled under its step until the step is done. `log_strips.py` pre-renders all 35 hints from chapters.json. The HUD hint still fades after 14 s. | `story_state.gd`, `story_director.gd`, `logbook_pages.gd`, `log_strips.py` |

Also: `review_views.py` and `capture_fp.gd` gained the matched views `cu_west`, `cu_wheel` and `cu_phone`; `cu_battery` follows the charger to -61.5.

## 2. Verification

| Check | Result | Evidence |
|---|---|---|
| Blender validation and reimport, watch room and lighthouse | PASS (FAIL = 0, reimport ok) | `pipeline.sh` output, v062 to v064 |
| Contact check (loose-part BVH overlap) for the mug, ashtray, phone, binoculars, lamp 0 and diagram | PASS: each touches only its own parts (the pipe rests in the ashtray by design) | scratch `contact_check.py`; before: the phone plinth intersected 2 binocular parts |
| Before/after Blender review renders | PASS by eye | `renders/last_light/b1_sheet_cabin.png`, `b1_before/`, `b1_after/` |
| Headless suites | see section 3 | |
| In-game captures (Godot window, Daniel's OK 2026-11-16) | PASS for C2, C3, C5, C7 to C10, D5 and D7. C1: the lamp is gone, but the door brightness target is not met (see the note under the table). C4: the geometry reads, but it is dark in the game | `renders/last_light/b1_t0*.png` (12 shots) |

**Captures.**

- `cu_west`: lamp 0 is well clear of the diagram, and the charger is on solid wall.
- `cu_phone`, `cu_chart`: there is a gap between the binoculars and the phone, the mug is off the ashtray, and there is no dial on the chart.
- `cu_radio`: the card sits beside the dial, not over it.
- `cu_coat`: the folds are smooth, with no ridges.
- `focus_radio` (1920x1205): the VHF panel starts at x 1566, and the scope's rim ends at about 1535.
- The three documents open full-screen and read cleanly.

**Two capture-tool fixes made on the way.**

- Detached views now hide the keeper's body. At t = 60 the bot stood in front of the door, and its body and shadow blocked `cu_door` and `cu_wheel`.
- `cu_wheel` was aimed at the wheel alone. It now also frames both lever dogs, in Godot and in `review_views.py`.

**C1 brightness: not met, and not caused by Stage B.** The plan asks for a mean luminance of 0.10 to 0.14 over the door in `cu_door`, measured as sRGB-weighted luminance on the door crop.

- Measured now: 0.032. Stage 0 measured 0.028 with lamp 4 still above the door, and the shot from before the remediation pass (`rq7d`) measured 0.127.
- So the door went dark during the remediation pass ("dark opening", R4), not by removing the lamp.
- The dark green leaf sits in shadow between lamps 2 and 3. The dogs and the wheel barely read in `cu_wheel`.
- The door's light moves to Stage S, which rebuilds the door and the stairwell lighting anyway.

## 3. Suites

Final state, run headless under `taskpolicy -b` on 2026-11-16.

| Suite | Result | New checks in Stage B |
|---|---|---|
| story_test | PASS (0 failed) | `D8_HINTS ok step=engine`: the hint is recorded once given, shown on the Duties page, kept through save and load, and gone once the step is done. Every hint strip named in the manifest exists |
| opening_test | PASS (31 / 31) | |
| regress_test | 370 pass, 1 fail, 4 skipped (headless only): see the note below | R24, VHF panel vs radar scope: the panel is clear of the scope at 1920x1080, 1920x1200 and 1280x720. Dragging moves the panel, keeps it on screen, stores the fraction and never changes what the player holds. Re-entering the radio view keeps the place, and a double click resets it |
| interaction_test | PASS (159 checks, 11 warnings; the warnings are the standing silent-document notes) | `orders`, `diagram`, `radio_card` open and close |
| qa_sweep_test | PASS (1924) | |
| g5_weather_audio_test | PASS (50) | |
| run_tests | PASS (95) | |
| sim_v2, seeds 1 to 5 | PASS, no gate failures | |
| pytest | PASS | |

**Regress, final:** 371 pass, 0 fail (rerun after the fix below). story_test rerun: PASS.

- **R22 failed once in the full run.** Its check is "the player's saves are untouched by the run". Daniel's real autosave folder (`user://saves`) was written at 09:41:30 and 09:41:32, during the regress run. The files hold a new chapter 1 game about 30 s in, at beats 1 and 2.
  - No test writes there. Every suite runs with `-s`, which `SaveSystem.isolated()` sends to `user://saves_test`, and no test changes the folder.
  - A rerun of regress left the files untouched and passed R22.
  - So the cause was a normal game launch outside the test runner at that minute. Its two autosaves rotated Daniel's earlier autosave out of both slots.
- **R19 failed once in the rerun:** "Space before the panel's dwell is ignored (0)". It was a timing race in `EndingSequence._wait`, which cleared a press that came during the panel's fade-in without counting it. Such a press is now counted as an early press and ignored, as before. This is a fix to the test signal only: an early press never advanced the panel either way.

## 4. Not done in this pass, and why

- **The 1953 Tide Tables volume** (canon fix 7.5) goes with the Tide Tables document (D6, Stage A): its spine needs a fourth slot in the props atlas, and the volume only matters once the shelf can be read.
- **C6 telephone** (P3): the model already has finger holes, a number card, cradle prongs and a coiled cord. The remaining polish (chrome separation, number ring) is left for the Stage G pass.
- **J opening the Duties page**: not done, by decision (Daniel left it to Claude, 2026-11-16). J keeps the duty line (tap) and the hint (hold). These help without a full-screen book covering the room. The pencil page stays one key away (L, then D), and a given hint now stays written there.
- **Draggable panel with a gamepad**: the pad cursor cannot drag. Pad players keep the default place, which is now clear of the scope.

## 5. Windowed captures proposed (Daniel's OK needed)

`tools/godot_bg --path projects/games/last_light/godot -- --capture=b1 --bot=expert --shots='60@cu_west,60@cu_battery,60@cu_door,60@cu_wheel,64@cu_coat,64@cu_phone,64@cu_radio,64@cu_chart,68@focus_radio!say_radio'`
