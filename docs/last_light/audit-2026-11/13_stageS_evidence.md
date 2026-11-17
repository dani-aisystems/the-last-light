# THE LAST LIGHT: Stage S evidence (stairwell and door), 2026-11-16

Stage S of the audit plan (section 5, [C_stairwell.md](C_stairwell.md)), after the Stage A commit (`e79e7a1`). Index: [README](README.md). Performance bisect: [12_perf_bisect.md](12_perf_bisect.md). Build: `last_light_v075.blend`, `watch_room_v058.glb`, `lighthouse_v050.glb`, new `stairwell_v002.glb`.

## 1. What changed

| ID | Change | Where |
|---|---|---|
| R5 | Behind the stair housing the room's painted wall, skirting and dado rail stop (each wall segment is split at the housing's side-plate centre lines; above the housing's top plate the room wall goes on). The span is lined with limewashed masonry, with a conduit, saddle clips, a junction box and a switch box. | `build.py` `build_shell`, `housing_span`, `housing_split`; `stairwell.py` |
| R5 | The room floor is cut exactly to the housing (its front plane and side-plate lines, `cut_away` with bmesh bisects). The old hole followed the world-axis 25 cm grid, not bearing 170, and stepped. | `build.py` floor |
| R6 | The oak rail that rose out of the uncut floor is gone. An oak top rail now runs from a steel newel on the landing, on a stanchion and a mid rail, to a wall flange on the side plate. Nothing passes through any floor. | `stairwell.py` |
| R7 | **Cause found by raycast:** the white patch was the exterior tower's top cap (white `M_LL_TowerPaint`) at exactly the room floor's height, seen through the stepped hole (65 of 117 rays from the `pp_door` eye into the hatch hit it; the shaft concrete was not the cause). The tower cylinder is now open-ended. In v073, 0 of 117 rays reach it. | `build.py` `build_lighthouse` |
| Section 5 | Chequer-plate landing on the hinge side; the hatch with a 6 mm coaming 50 mm proud and a 70 mm flat; a drop chain across the ladder head; a 75 degree ship's ladder (12 treads with worn nosing bars, flat-bar stringers, a wall-side handrail) whose head sits inside the hatch so a climber's head clears the room's floor slab. | `stairwell.py` |
| Section 5 | The service landing one flight down (bearings 130 to 230, floor 3.1 m below the room): curved limewashed masonry, stone flags, two partitions, two 45-gallon drums on a rack, a semi-rotary hand pump with its delivery line rising through the slab to the day tank and a suction line to a drum, the clockwork weight tube, the padlocked engine-room door, the storm door the stair continues down behind, and a bulkhead lamp. | `stairwell.py`, new collection `ASSET_stairwell` → `stairwell.glb` |
| C4, R8 | The handwheel and the two lever dogs are their own parts (`PT_stair_handwheel`, `PT_stair_dog_0/1`). The leaf has its own collider (`COL_stair_leaf`); the shut-shaped `COL_stair_door` and the invisible `COL_stair_well` box are gone. | `build.py` `build_stair` |
| C4, R8 | Door sequence: the wheel turns 1.5 turns while the dogs lift 78 degrees (0.8 s, eased), then the leaf swings to -105 degrees (1.6 s, smoothstep). Closing reverses, the dogs dropping after the leaf is home. The wheel, dogs and collider are reparented under the leaf at load. A loaded save is posed at once (`snap_door`). | `station.gd` `_bind_door`, `_update_door`, `snap_door`; `game_fp.gd` |
| Sound | New synthesised `door_dogs` (wheel rasp and two dog clanks); `door_heavy` follows 0.8 s later as the leaf swings. Not listened to by Claude. | `audio/synth.py`, `game_fp.gd` |
| Lighting | The lower level is its own render layer (`LAYER_LOWER`, 8192): room lamps and the exterior lights never reach it; the stair pendant does (down the hatch, shadowed); its bulkhead lamp (`stair_low`, red in a blackout) lights only it. It has its own reflection probe (5 cm blend, as R4) and fog cut, and it is hidden with the door shut. | `station.gd`, `outside.gd` `EXTERIOR_ONLY` |
| Materials | Limewash, stone flags and red-oxide drums use the room shader with no dado bands; chequer plate is a standard material with a tread-plate normal map drawn in code (no texture file). The room keeps its 33 materials. | `materials.gd`, `build.py` `MATS` |
| S4 | The stair door: a soft unshadowed spot from the ceiling 0.7 m in front of it, aimed at the leaf's centre (the lit room's bounce; off and flickering with the room lights; energy 1.6). Door mean luminance in `cu_door`: 0.032 (Stage B) → **0.121**. | `station.gd` `_make_fills`, `DOOR_FILL_ENERGY` |
| S4 (optional) | A diffuse-only glint at the sediment bowl (0.1, range 0.22 m). | `station.gd` `BOWL_GLINT_ENERGY` |
| Found on the way | A "touched-up paint" patch at bearing 158 reached 159.9, inside the housing, and showed as a pale card on the side plate: moved to 156, with an assert that no patch enters the housing. The generator cage's light had the default all-layers mask and reached the lower level: it now uses the room mask (R26 caught it). | `build.py`, `station.gd` |
| Perf (bisect) | The room probe's ambient energy and intensity are written only when they change (`_probe_set`). No visual change. | `station.gd` |
| Capture tool | Detached views now hide the keeper's body every time (right after a restore it had not yet shown itself, so the check skipped it and the body then stood in front of `cu_wheel`, `fp_stair` and `doorseq`). `door_open` poses the door at once. | `capture_fp.gd` |
| Tools | `blender/contact_check.py` (committed from the Stage B scratch copy, probes as arguments), `blender/measure_luma.py` (the door crop; reproduces Stage B's 0.032 on `b1_t060_cu_door.png`), `review_views.py --door_open --dogs_up` and views `pp_door`, `cu_landing`, `in_hatch`, `plan_hatch`, `low_ladder`, `low_engine`; capture views `cu_landing`, `in_hatch` and the `doorseq` frame series. | |

**Canon note (Daniel, 2026-11-16):** the steel bulkhead door stays; `ch4.dlg:127` ("Two inches of oak and a bolt my father fitted") goes to the Stage C script document. No `.dlg` was changed.

## 2. Verification

| Check | Result | Evidence |
|---|---|---|
| R7 cause | Confirmed by raycast (tower top cap), fixed; 0 of 117 rays reach it in v073 | scratch `r7_ray.py` on v067 and v073 |
| Blender geometry: R5, R6, landing, hatch, rails, chain, ladder, service landing | PASS by eye | `renders/last_light/s1_v073/open/*.png`, `shut/cu_wheel.png`, `dogs/cu_wheel.png` |
| Contact check | PASS after four fixes (oak rail into the door's right jamb 1.7 cm → rail moved 2.5 cm in; drum against the 130 partition; the two drums end to end; the hose through a drum). Touches left: by design (rail on newel, stanchion and flange; ladder head on the landing and 1 mm against the newel; landing against the side plate) | `renders/last_light/s1_v068/contact_v069..v073.json` |
| Pipeline | PASS: validation FAIL = 0 and reimport ok for watch_room, lighthouse and stairwell (v074, v075) | `pipeline.sh` output |
| Budgets (pytest hooks) | PASS: room 128,090 tris, 214 of 220 meshes, 33 of 33 materials; stairwell 8,246 tris, 10 materials | `tests/test_last_light_hooks.py` (new `test_stair_door_parts`, `test_stairwell_glb`) |
| In-game, door open (window batch, Daniel's OK) | PASS: no cream wall, dado or skirting inside the housing; limewash, conduit, rail, newel, chain; looking down: landing, coaming, chain, ladder | `s5_t060_cu_door-door_open.png`, `pp_door-door_open-pitch_m30`, `cu_landing-door_open`, `in_hatch-door_open`, `fp_stair-door_open` |
| In-game, blackout | PASS: the housing goes red from the emergency light; no red lines round the closed door's edges were looked for in this batch (NOT TESTED) | `s5_t060_cu_door-door_open-dark.png`, `in_hatch-door_open-dark` |
| Door sequence | PASS: shut and dogged, then the leaf swings into the room, open by about 1 s of capture time | `s5_sheet_doorseq.png` (the first batch still showed the body: capture-tool bug, fixed) |
| Door luminance (target 0.10 to 0.14) | PASS: **0.121** (0.084 at fill 0.8; 0.032 before) | `s5r1_t060_cu_door.png`, `s5r2_t060_cu_door.png`, `measure_luma.py` |
| Wheel and dogs read | PASS | `s5r1_t060_cu_wheel.png` |
| Bowl glint | PARTIAL: the bowl's glass and diesel now read (dark smudge before), but the copper fuel line beside it takes a warm 10 cm hotspot. For Daniel: keep or remove | `s5r2_sheet_bowl.png` (left Stage A, right now) |
| R26 (door order, easing, collider on the leaf, doorway, hatch closed, lower layer, save poses) | PASS (26 checks) | regress |

## 3. Suites

Final state, headless under `taskpolicy -b`, 2026-11-17 (the Stage S code; after P1, qa_sweep, regress and g5 were rerun and stayed green).

| Suite | Result | New in Stage S |
|---|---|---|
| regress_test | PASS (417 / 417, 4 headless skips) | R26, 26 checks |
| story_test | PASS (0 failed) | |
| opening_test | PASS (31 / 31) | |
| interaction_test | PASS (164 checks, 12 warnings: the standing "no sound when a document opens", Stage D) | |
| qa_sweep_test | PASS (5,881) | preset check: SSIL on High only (P1) |
| g5_weather_audio_test | PASS (50) | |
| run_tests | PASS (95) | |
| sim_v2, seeds 1 to 5 | PASS, no gate failures | |
| save_compat_test | PASS (305) | |
| pytest | PASS | `test_stair_door_parts`, `test_stairwell_glb`; normals and import hints for the stairwell |

**Daniel, 2026-11-17:** Stage S approved; the bowl glint stays (DECISIONS Q18).

## 4. Not done, and why

- **Hinge and latch sounds by ear:** `door_dogs` is synthesised and placed, `door_heavy` follows it; neither was listened to (Claude never plays audio). Daniel's ear, or Stage D.
- **The lower level walkable:** it is seen, lit and probed, but has no floor or wall colliders. The player only goes down in the Stage F fuel run, which needs ladder climbing; the colliders belong there.
- **Open-door frame cost:** the bench views keep the door shut (the lower level hidden). The Stage S build with the door shut benches at 17.6 to 18.1 ms (same as before Stage S). The door-open cost is NOT TESTED; the lower level is 8.2k triangles and one unshadowed light.
- **Red lines round the shut door in a blackout (R4):** not re-captured in this batch.
