# THE LAST LIGHT: Stage 0 evidence (2026-11-15)

Baseline for the audit plan, taken at commit `2b5d3ee` before any game change. Captures are in `renders/last_light/` (gitignored, reproducible with the commands at the end). Index: [README](README.md).

## 1. Headless suites: PASS
| Suite | Result |
|---|---|
| story_test | 0 failures (the two "Parse JSON failed" lines are its corrupt-save test) |
| opening_test | 31/31 |
| regress_test | 362 passed, 0 failed, 4 headless skips |
| interaction_test | 159 checks, 0 failed, 12 warnings (documents have no sound) |
| qa_sweep_test | 1,924 passed, 1 headless skip |
| g5_weather_audio_test | 50 checks, 0 fails |
| run_tests | 95/95 |
| sim_v2, seeds 1 to 5 | no gate failures |
| pytest | 23 passed |

## 2. Register rows now confirmed on screen
| ID | Capture | What it shows | Status |
|---|---|---|---|
| C11 sitting glimpse | `a0_t074_sitseq_f00.png`, `a0_sheet_sit.png` | In the first two frames after E, a headless, armless torso and legs stand at the chair in front of the still-standing camera | Confirmed |
| R5 door onto a wall | `a0_t060_cu_door-door_open.png`, `a0_sheet_door.png` | The room's cream wall and oak dado rail directly behind the open leaf | Confirmed |
| R6 wooden stick | `a0_t060_pp_door-door_open-pitch_m30.png` | The oak handrail rising diagonally out of the floor just inside the doorway | Confirmed |
| R7 white floor | same | A pale L-shaped patch on the floor at the foot of the rail, at the stair hatch. Not the photograph prop (it was not shown). One of the two floor-surface causes | Confirmed to exist; cause narrowed to two |
| R3 Ross | `a0_t060_fp_stair-visitor.png`, `a0_t060_cu_door-visitor.png` | A black blocky figure under a sou'wester; the door lamp burns directly above his head | Confirmed |
| C1 lamp over the door | `a0_t060_cu_door.png` | Glare on the door top and frame | Confirmed |
| C2 lamp against the diagram | `a0_t062_cu_power.png` | The lamp globe sits over the diagram's top corner | Confirmed |
| C3 charger cabinet | `a0_t062_cu_battery.png` | Sea visible behind the cabinet's right edge | Confirmed |
| C7, C8 mug, pipe, chart dial | `a0_t064_cu_desk_r.png`, `a0_t064_cu_chart.png` | Mug touching the ashtray; the brass dial beside it on the chart | Confirmed |
| C9 radio-check card | `a0_t064_cu_radio.png` | Small card on the upper left of the radio face | Confirmed |
| D4 portrait border | `a0_t060_fp_stair-visitor.png` | Cream margin round the photo, wider at the bottom | Confirmed |
| D5 VHF panel over the radar | `a0_t074_sitseq_f02.png` onward | The panel's left edge covers part of the radar scope in the radio view | Confirmed |
| M1 vessels | `a0b_sheet.png` | Through binoculars at 80 m in dawn light the fishing boat is one flat grey slab with no deck or near side, with oversized floating light discs and an orange box; the steamer is a long slab with a striped band | Confirmed |
| M2 sea patches | `a0b_t096_ext_far-dawn.png` | Flat, smooth-edged darker patches all over the water where the flat underlay shows through wave troughs. The repeating shore mask was not seen in these views | Underlay cause confirmed; mask repeat still unconfirmed |
| Endings | `a0s_sheet_endings.png` | All four final panels are "PANEL PENDING" plates beside their lines; the lines read correctly | Confirmed |

**Not captured, still owed:** the longest radio line (Morag's chapter 3 gale warning) on screen at text 1.0 and 1.5; the radio view at exactly 1920 x 1080; the four ending title cards (the capture state shows the last panel, not the card); lamp 0 and the diagram in a dedicated close-up; any audio.

**Capture artefact to ignore:** in room views taken with the capture camera, the keeper's own headless body stands where the player is. The player never sees it from there.

**Binocular note for Stage E:** from the desk the window mullion crosses the binocular view, and magnified rain drops on the glass blot parts of it. Vessels at 90 m sit about 13 degrees below the horizon line of sight.

## 3. Reading time
Summed over every branch of the six story files with today's reading formula: 38.3 minutes (chapter 1: 6.4; 2: 5.2; 3: 5.2; 4: 5.9; 5: 6.8; 6: 8.8). One path through is shorter; this is an upper bound for dialogue alone. Whole-game runtime is still NOT TESTED.

## 4. Performance: FAIL against budget, cause not isolated
Worst-case bench (storm 1.0, lightning every 3 s, generator running, one ship), 30 s per view, no vsync, Auto resolution (3D scale 0.43 Medium, 0.47 High), window in the foreground. Files: `a0f_q1`, `a0f_q2` printed to the log; the unfocused runs are `a0_q1_bench.json`, `a0_q2_bench.json`.

| Preset | View | Median ms | p95 ms | Draw calls | Primitives | Last clean bench (5 Nov, `s15f`) median |
|---|---|---|---|---|---|---|
| Medium | desk | 27.0 | 34.6 | 905 | 1.94 M | 18.0 |
| Medium | window | 30.4 | 35.0 | 866 | 1.88 M | 18.6 |
| Medium | generator | 27.4 | 36.5 | 1,392 | 2.46 M | 16.6 |
| High | desk | 40.6 | 50.4 | 1,368 | 2.64 M | 29.0 |
| High | window | 38.8 | 46.3 | 1,300 | 2.56 M | 28.0 |
| High | generator | 37.0 | 50.2 | 1,852 | 3.15 M | 26.7 |

- Budget is 16.7 ms on Medium and 25 ms on High. Medium is about 10 to 14 ms over.
- Against 5 November, Medium is 50 to 65% slower and desk draw calls rose from about 534 to 905. Much was added since (body, hands, title storm, exterior island and boat, torch shadows, cabin props), so a real regression is likely, but this session's editor and tools were also running, so part may be machine load.
- VRAM 1.15 GB (Medium), 1.25 GB (High).
- **Consequence for the plan:** a performance bisect (the existing `--bench_toggle` and `--no*` flags) is added at the start of Stage A, before anything that costs frame time is built.

## 5. Changes made in Stage 0
- New: this folder (`docs/last_light/audit-2026-11/`, 16 files).
- `docs/architecture/DECISIONS.md`: Q15 and Q16 added.
- `godot/scripts/capture_fp.gd`: capture-only states `door_open`, `storm_full`, `ship_<kind>_<range>` and the `sitseq` frame series. No game behaviour changed.
- Nothing committed.

## 6. Commands
```
tools/godot_bg --path projects/games/last_light/godot -- --capture=a0 --bot=expert --shots='60@cu_door,60@cu_door!door_open,60@fp_stair!door_open,60@pp_door!door_open!pitch_m30,60@cu_door!door_open!dark,60@cu_door!visitor,60@fp_stair!visitor,62@cu_battery,62@cu_power,62@cu_lamp,64@cu_coat,64@cu_desk_r,64@cu_desk_l,64@cu_chart,64@cu_radio,66@pp_phone,66@pp_tide_tables,66@cu_orders,68@focus_radio!say_radio,68@focus_radio!say_radio!text15,70@pp_photo53!photo_door,72@player!look_down,72@player!take_kit!compass,74@sitseq,76@body_3p!in_radio'
tools/godot_bg --path projects/games/last_light/godot -- --capture=a0b --bot=expert --noglass --norain --shots='90@pp_radio!take_kit!binoculars!face_north!pitch_m10!dawn!ship_steamer_120,92@pp_radio!binoculars!face_north!pitch_m15!dawn!ship_fishing_80,94@pp_radio!binoculars!face_north!pitch_m15,96@pp_radio!binoculars!face_north!pitch_m3!dawn,96@ext_far!dawn'
tools/godot --audio-driver Dummy --path projects/games/last_light/godot -- --capture=a0f_q1 --bench --quality=1 --novsync --bench_secs=30 --bot=expert
```
