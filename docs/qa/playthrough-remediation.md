# THE LAST LIGHT: playthrough remediation (Daniel's 29 issues, 2026-11-15)

Daniel played the build at `0704193` (after G6d) and sent a 29-issue brief. This file records each issue: its cause, the fix, the evidence and its status.
- **Plan:** `~/.claude/plans/pasted-content-id-46d5-the-misty-music.md`.
- **Captures:** in `renders/last_light/` (gitignored, reproducible).
- **Before shots:** `rq0_*` and `rq0b_*` come from a scratch worktree of `0704193` running the same capture tool, so before and after show the same shots and states.

**Statuses:**
- **Verified Fixed:** checked in the running game, by a test or a capture I looked at.
- **Implemented — Awaiting Verification:** done, but only Daniel can judge it (how audio sounds, how 120 Hz motion feels, taste).
- **Confirmed — Not Fixed**, **Unable to Reproduce**, **Blocked:** none at the end of this pass.

## Daniel's decisions for this pass (2026-11-15)
- Silent `tools/godot_bg` windows are pre-approved; benches only when he says the Mac is free.
- Rain and thunder are re-synthesised in `audio/synth.py`, with no downloads.
- Work through the phases autonomously, with phase commits; never push.
- The compass goes on a window sill.
- Thought and in-room subtitles advance by themselves; radio lines keep Space plus a cue.
- The opening is near-black with the windows readable.
- The material cap stays at 33.

## Issue matrix

| # | Issue | Pri. | Root cause (confirmed) | Fix | Evidence | Status |
|---|---|---|---|---|---|---|
| 1 | Dialogue stuck after engine + tower light | Critical | The six ch1 dusk thoughts advanced only on Space, with no on-screen cue, and E never advances dialogue. While a line was up the director checked no beats, gave no nudges and dropped device thoughts (`story_director.gd:548`, `game_fp.gd:712`). | Thought, in-room and sound lines advance by themselves after a reading time (`dialogue_ui.gd auto_advance_s`, clamped 2.8–9 s, paused under fades and documents). Space still skips. One advance per line. | `opening_test` O1 (31/31). Proof run with auto-advance off: the story never leaves `dusk` (8 FAILs), the stall reproduced. | Verified Fixed |
| 2 | Engine and tower-light interactions | Critical | The `engine` / `charge` beats polled live state, but their duty was already latched done (so no nudge). An overheat, a dry tank or CHARGE switched off (as the hot-engine notice asks) left the story waiting forever. | `chapters.json`: engine = `gen == 2 or gen_started`; charge = `charge_flow > 0 or duty_done("power")`. `dusk_done` is now set at `radio_check` (the sky stays night on later loads). An in-dialogue `wait` can no longer be skipped. | `opening_test` O2 (all devices during the dusk lines), O3 (CHARGE off + overheat), O4 (CHARGE before START, valve last), O5 (save at the light beat, load, continue). | Verified Fixed |
| 3 | Stuck subtitle about darkness / flat lights | Critical | `ch1.dlg:7`, "Dark as a press up here. The cells are flat again…", line 2 of `ch1_dusk`: the line Daniel saw waiting for Space. | Same as 1. A queued thought now waits 0.6 s after a conversation and is hidden when a story line appears, so no two subtitles overlap. Device answers are queued (6 s life) instead of dropped. | O1: "the 'Dark as a press…' line shows / and leaves by itself". O6: no thought subtitle left under the radio panel. | Verified Fixed |
| 4 | Opening soft-lock test | Critical | No test played the opening in human mode: all ran the director as a bot or poked sim setters. | New `tests/opening_test.gd`: the real game nodes, human mode, devices used through `station.use → game_fp._route` (the player's interact path), no Space for thoughts, and Space as a real key event for the radio. | 31/31. Radio lines do not auto-advance in 20 s and show the cue; Space (a real `InputEventKey`) moves them on. | Verified Fixed (headless). A hands-on run by Daniel is recommended. |
| 5 | Instagram icon | Medium | A generic camera glyph, drawn in code. | The recognisable Instagram glyph (rounded square, lens, dot), drawn in code and centred on the capitals. `links.json` icon `instagram`. | `rq2b_tmenu_t47_new_game.png`, `rq2b_detail.png`. Regress R21 (links, focus, opener) is in the suite run. | Verified Fixed |
| 6 | Email icon | Medium | A plain rectangle envelope at a different height from the camera. | A rounded envelope with a flap meeting below the middle, the same stroke and centring as Instagram. The link is unchanged (`mailto:`). | Same captures as 5. | Verified Fixed |
| 7 | Lighthouse exterior textures | Medium | A 1k scan with nearly flat roughness and normal maps (σ ≈ 0.02) that mipmaps to grey at 98 m. Triplanar seams showed as hard vertical lines on the round tower. | `tri_pbr`: a cylindrical wrap for the tower (`cyl_repeats` 3, no seams), macro variation (albedo ±6 %, roughness 0.45–0.8), faint masonry courses, a wetter and glossier SW side, streaks 0.85 → 0.7, scan contrast 0.45 → 0.3. Geometry unchanged. | `rq2a_tmenu_t20_ext_landing.png` (seam visible) → `rq2b_tmenu_t20_ext_landing.png`. | Verified Fixed (seam). The weathering is subtle at title distance: Daniel to judge the look. |
| 8 | Lighthouse stutters while turning | High | (a) `sim.bearing` advances only on the 60 Hz physics tick and was drawn without interpolation (`outside.gd:1090`), so on Daniel's 120 Hz screen it moved every other frame. (b) The title's expert bot took MANUAL to focus on ships and handled motor jams at 275 s / 500 s: the beam stopped, reversed, and its energy jumped ×1.3. | `KeeperSim.draw_bearing()` interpolates between physics steps (beam, optic, room drive gears). The title has no faults and `KeeperBot2.title` keeps the beam on AUTO. | `--beam_pace` (new), ~105 fps: frames where the beam didn't move 43 % → **0 %**; step CV 0.88 → **0.11** (`rq0_pace` / `rq2_pace`). | Verified Fixed (measured). 120 Hz feel: Daniel. |
| 9 | Beam clipped near the title | High | A fixed screen mask `smoothstep(0.50, 0.66, SCREEN_UV.x)` cut the cone with a vertical edge 3 % left of the lantern. The fog scatter dropped to 0.3 by the same rule. | The mask follows the menu column's real right edge (`set_title_column`), keeps a 45 % floor, and the scatter keeps 0.85. A near-camera fade prevents near-plane slicing. | `rq2a_tmenu_t47_new_game.png`: the beam passes behind the subtitle and stays readable. | Verified Fixed |
| 10 | Light interaction on the menu | Medium | The cone sat far below the glow threshold; `beam_facing` only fed the menu glow. | As the beam faces the lens: glow 0.45 → 0.65, exposure +5 %, cone +25 %, scatter +0.6, the lantern omni ×2.2. No flare. | `rq2c_facing_pair.png`: a frame at facing 0.85 (new title-shot state `!facing`) beside an ordinary one. The beam sweeps over the lens without clipping, the lantern brightens, the sky lifts near the shaft; no whiteout or flare. | Verified Fixed (restrained by design; taste: Daniel) |
| 11 | Menu button spacing | Medium | `_gap(30)` after New Game plus a 20 px save line reserved under Continue: about 90 px baseline to baseline, against 59 px elsewhere. | The save info tucks into Continue's padding (slot kept, nothing moves) and the gap is 14. Continue → New Game 66 px, New Game → Load Game 73 px, the rest 59 px. | `rq2a_tmenu_t6.png` (with save), `rq2b_720_tmenu_t3.png` (no save, 1280×720). Regress R21 "New Game doesn't move" in the suite run. | Verified Fixed |
| 12 | Rain sounds like clicking | High | Sparse sine "pings" whose envelopes were cut off mid-decay (88 % of roof pings: about 45 clicks/s). Centroid 5 kHz, almost nothing below 400 Hz. The title played it unfiltered (20 kHz). | `synth.py`: a pink wash, ~3,200 noise-grain impacts/s and a low-mid patter, all as circular grain trains that decay to silence; the glass layer redone the same way. The title's exterior low-pass 20 kHz → 6.5 kHz. | `analyze.py` new CLICKY gate: onsets/s 5.2 → 0.0 (roof), 40 → 0.3 (glass). Centroid 5.0 → 2.3 kHz. Listening files `renders/last_light/rq3_listen_{before,after}.wav`. | Implemented — Awaiting Verification (listening) |
| 13 | Thunder is a pop | High | 87 % of title strikes used the far variants, nearly all below 150 Hz (inaudible on small speakers: only the onset thump survived). No fade (files ended at −22 to −33 dB), no echo, no pitch variation. | 8 layered variants: near ×3 with crack and crackle, mid ×3, far ×2. Each has a body of 30–250 Hz bursts, a rolling 80–900 Hz layer with flutter, a 9–14.5 s tail, a synthetic sky/sea reverb and a fade to silence. Picked by distance (<700, <1500, beyond), ±6 % pitch. | TAIL gate: all old files flagged, all new pass. Energy above 200 Hz in the far variants −7.4 → −4.5 dB. g5 test: 700 / 1500 m classes. | Implemented — Awaiting Verification (listening) |
| 14 | Environmental audio audit | High | Audited: buses (Exterior low-pass, sends to Ambient), loops (`_looped` forces whole-file loops; seams pass the SEAM gate), levels at storm 0.75 (rain −9.5, wind −7.5, sea −8.5 dB), thunder delay = distance / 343, glass layer 3D at the windows. | Fixes as in 12 and 13; reverb is baked into the thunder (a bus reverb would have smeared the rain and wind as well). The synth stays deterministic. | `analyze.py --strict`: 50 files, 0 flagged. `test_last_light_audio.py`: byte-identical regenerate, 8 thunder variants. | Implemented — Awaiting Verification (listening) |
| 15 | Desktop-only optimisation | High | No defect found. Keyboard/mouse with one mouse owner (R8), FSR render scale, Medium the 60 fps default. | No code change for this item beyond the shadow budget (19, 20). | Title at the Retina default and at 1280×720 (`rq2b_720_tmenu_t3.png`): layout holds. **Windowed regress** (real `Input.mouse_mode`, no skips): 369/0 twice. A first run had 2 R6 radio-panel timing failures, untouched code with a known load sensitivity (`74994a2`). | Verified Fixed. Bench NOT TESTED (Mac not confirmed free). |
| 16 | Opening not pitch-black | High | **The reflection probe's `blend_distance` defaulted to 1.0 m.** The walls (r 3.25) sat 0.25 m inside its 7 m box and the floor 0.1 m above its bottom, so the room took the dusk SKY's ambient: the "dark" walls were evenly lit cream. Also: window spill unshadowed at 0.17 (range 7.5 m), SSIL bouncing the dusk sky, catch-lights at ~14 at 5 cm. | Probe blend 0.05 and a box past floor, ceiling and the reveals. Blackout factor (`station.dark`): spill ×0.3, range 4.6 m, SSIL 0.35, room fog cut 0.97, catch-lights 0.035 (glints, attenuation 1.0). Probe reflections ×0.15 in the dark. **No albedo changed.** Lit-room ambient 0.45 → 0.8 replaces the lost sky fill. | `rq4b_sheet_dark1.png` (rq0 vs rq4b): walls black, windows readable, the torch's glint on the shelf. | Verified Fixed |
| 17 | Black wall / coat / hat by the door | High | Not a normals problem (the GLB was checked). In the old opening the window side was lit by the sky ambient (16) and the door side was not, so the door corner read as pure black against it. The coat's storm-flap seam was Bakelite (0.004 linear albedo); the oilskin was 0.06 at roughness 0.3 (black plastic). When lit, no Medium shadows reached the coat. | 16, plus: the seam is now oilskin, the oilskin albedo 0.42/0.36/0.17 at roughness 0.42, and wall lamp 2 (over the coat and door) takes the Medium shadow slot. | `rq6_sheet_c.png` / `rq7d_sheet.png` (coat, door, lit). Torch views `rq4c_sheet.png`. | Verified Fixed |
| 18 | Red lines round the doorway | High | (a) A 6.6 cm crescent between the bulkhead's straight top plate and the curved wall, and 6 mm chamfer slits. (b) The leaf meeting the trim flush (a V-groove). (c) **The main one:** the red emergency light behind the door leaked through its soft shadow round the door edges and rivets (default bias; thin overlaps). | build.py: plates 3 cm into the wall, a filler following the wall's curve, the leaf 15 mm into the trim. The stair light: shadow bias 0.01, normal bias 0.3, hard shadow; attenuation 1.6 → 1.2. | Red pixels in the dark door view: 878 (peak R 130) → **0** (`rq6e_red_compare.png`). | Verified Fixed |
| 19 | Torch realism | High | A flat disc (no projector, angle attenuation 0.85). The light was aimed once from an old position, so the pool sat low and right of the crosshair. | A procedural reflector pattern (`Player.torch_projector`: hot core with the filament's shadow, halo, a faint reflector ring, slight asymmetry). Re-aimed at the crosshair every frame; energy 3.4, cone 27°. | `rq4c_sheet.png`, `rq7_sheet2.png`. | Verified Fixed |
| 20 | Torch shadows when pointing down | High | Looking down, the light sat on the chest (the lens comes back to the body) and the shadow-casting body sliced the beam. Default biases, a ≤1024 atlas slot. | Below −0.55 rad pitch the origin blends to just under the eye. The body is on render layer 13 and excluded by `shadow_caster_mask`. Bias 0.04, normal 1.6, blur 1.4. Atlas quadrant 0 = one 2048 slot (the torch). | `rq0_t030` vs `rq7_t030_player-look_down-torch`: a soft, unsliced pool. | Verified Fixed |
| 21 | Vapour burner | Medium | A brass cylinder and a paper ball; all brass was one flat roughness. | A turned brass fount (foot ring, belly, shoulder, burner collar), pump plunger with knob, filler cap, a mantle sock. Room brass is now worn: a noise gives roughness 0.22–0.62, a slight tarnish and a faint normal, in object space. | `rq7_sheet1.png` (cu_shelf). | Verified Fixed |
| 22 | Admiralty Tide Tables | Medium | Three plain blue boxes, no title. | Three bound volumes (1969–71): buckram boards, gilt spines "ADMIRALTY / TIDE TABLES / VOL. I / year" (generic lettering, no crest), the page block at the head, the 1969 front board with a damp tide-mark. Inspect unchanged. | `rq5_spines.png`, `rq7_sheet1.png`. | Verified Fixed |
| 23 | Box left of the Old Station Logs | Medium | A blank paper block (the spare-lamp box). | A printed buff carton ("LAMPS · SPARE / 1000 W · 240 V", a pencilled "x2", scuffed corners), bevelled; clearance to the log box kept. | `rq7_sheet1.png`. | Verified Fixed |
| 24 | Door handle | Medium | A brass handwheel at one flat roughness. | The worn brass of 21, in object-space triplanar, so its wear moves with the door when it swings (ch4). Animation, collision and IA untouched. | `rq7d_sheet.png` (cu_door). | Verified Fixed (the handwheel is small in the captures) |
| 25 | Sweater on the chair | Medium | A single-sided sheet with no thickness; the knit was a flat stripe. | A second skin 7 mm under it, rolled edges all round, deeper folds; a knit-two-purl-two rib with lit and shadowed stitches, fuzz and a darn (canon: repaired cuffs). | `rq6_sheet_b.png` (cu_chair). | Verified Fixed |
| 26 | Compass position | Medium | On the chart; its card reused the dark floor rose, so the dark needle vanished. | On the east window's sill, just right of the desk, in the open. A trial behind the radio was out of sight, so it moved. A new cream card (black and red printing). Refusal, duty line and hint text updated; regress R15 updated. | `rq7f_t062_pp_compass.png` ("[E] Take the hand compass"). R15 pick test in the suite run. | Verified Fixed |
| 27 | Floating window reflection | High | Wall lamp 0 at −48° hung 0.4 m in front of the west window's glass: that bay's wall opening runs −52.5…−22.5 (it follows the 96 wall segments), so the lamp floated in the opening with its reflection beside it. The probe also captured torch pools and catch-lights. | Lamp 0 moved to −62° on solid wall. Its shadow slot went to lamp 2 (its conduit shadow crossed the pier). The probe dims to 0.15 in a blackout. | `rq7d_sheet.png` (cu_window), `rq7b_sheet.png`. | Verified Fixed |
| 28 | Glowing orb behind the bulb | High | The globe glass was double-sided, so the inside of its far half, 7 cm from the light (falloff d^-1.6 ≈ 57×), drew as a lit orb. The wall 15 cm behind was ≈ 17×. | The globe gets its own front-faces-only glass (`lamp_globe`) and stays out of the probe capture. Lamp attenuation 1.6 → 1.2, energy 0.85 → 0.72 (same at 1.5 m). | `rq4c_sheet.png` (cu_lamp: no orb; the glass and guard read). | Verified Fixed |
| 29 | White seams under the window | High | (a) The sill board's top was coplanar with the wall top (z-fighting). (b) A wedge of bare concrete between the curved sill and the straight frame (up to 9 cm). (c) On the bays' outer sides the opening ran past the frame (16.5° vs 14.7°), a slit to the exterior (1.8 cm even on bay 0). (d) The tower skin's top was level with the sill. | The sill board 4 mm proud and run under the frame; stile extensions from the frame to the real jamb (only where the jamb is outside the frame); the skin top 2 cm below the sill. | `rq7d_sheet.png` / `rq7b_sheet.png` cu_window, cu_sill_w: no white lines or slits. | Verified Fixed |

## Testing evidence
- **Suites (final tree),** headless with `taskpolicy -b`, against the G6d baseline:

  | Suite | Result | G6d baseline |
  |---|---|---|
  | opening_test (new) | **31/31** | — |
  | story_test | 0 failures | 0 |
  | regress_test | **362/0** (headless skips as before) | 354/0 |
  | interaction_test | 159 checks, 0 failed (12 sound warnings, unchanged) | 159/0 |
  | qa_sweep_test | 1,924/1,924 | 1,924 |
  | g5_weather_audio_test | **50/0** (new far-thunder class) | 48 |
  | run_tests | 95/95 | 95 |
  | sim_v2 (seeds 1–5) | no gate failures, identical summary | identical |
  | pytest (workspace) | 23 passed (audio regenerates byte-identical and passes the gates; hooks test at 33 materials) | 23 |

  The g5 far-thunder check failed at first because the test advanced only 4 s, and thunder from 2,200 m arrives after 6.4 s. The test now waits out the delay.
- **Gameplay paths run:** `opening_test` O1–O6 (human mode, real game nodes):
  - the usual order;
  - everything during the dusk lines;
  - CHARGE off plus an overheat;
  - CHARGE first with the valve last;
  - save at the light beat and load;
  - radio lines still on Space, with a real key event.
- **Asset pipeline:** `pipeline.sh` v057 → v061, every run validation FAIL = 0 and reimport OK. The hooks test holds 33 materials and ≤ 220 mesh nodes.
- **Captures:** `rq0_*`, `rq0b_*` (before, worktree of `0704193`); `rq2a/b_*` (title); `rq4a–c_*` (dark opening, torch); `rq6*_*`, `rq7*_*` (geometry, props, windows, door). Sheets: `rq4b_sheet_dark1.png`, `rq4c_sheet.png`, `rq6_sheet_*.png`, `rq7_sheet1/2.png`, `rq7b_sheet.png`, `rq7d_sheet.png`, `rq6e_red_compare.png`.
- **Audio:** `analyze.py` with three new gates (CLICKY, TAIL, DULL); `rq3_listen_{before,after}.wav` (60 s title mix).

## Performance
- **Bench NOT TESTED:** Daniel did not confirm the Mac was free.
- **Indicative only:** the title's hidden-window frame rate was 105.4 fps before and 104.6 after (`--beam_pace`), so no visible regression.
- **Likely cost changes:**
  - **Torch:** one 2048 shadow slot instead of ≤ 1024. It's one light, and the room lights are unchanged.
  - **Shadowed lights on High:** 7 instead of 8.
  - **Torch projector:** one 256² texture.
  - **Brass:** two 256² noise textures.

## Remaining concerns
- **Audio** (12–14) needs Daniel's listening pass.
- **The lit room is a little lower-key by the windows** than before. The old brightness came from the dusk sky's ambient bleeding into the whole room (the same fault as 16). The fill is now a warm ambient (0.8).
- **The keeper's body** reads lighter from an external capture camera. The player never sees it from there; looking down in a blackout, the legs are now dark, as they should be.
- **Menu beam response (10)** is subtle by design.
- **R6 radio-panel checks** ("click across a list refresh", "Space after an order") failed once in three windowed runs. They are the known load-sensitive pair, and the panel code was not changed in this pass. Watch them; if they recur, that pair needs the same load-proofing as `74994a2`.

## Recommended next playthrough (about 10 minutes)
1. **Title:** watch the beam for a full turn, sweeping behind the title. Hover Instagram and Contact. Check the spacing with and without a save.
2. **New Game:** let the six dusk thoughts run without pressing anything; they should advance by themselves. Look at the door wall: it should be black, with no red lines.
3. **Torch:** take it from the top shelf (F), point it at the door, the coat and the floor (looking down), and walk with it on.
4. **Power and light:** valve, START, CHARGE. Then switch CHARGE off again and back on. Then MODE AUTO and LAMP NORMAL. The radio check should start, and its line should wait for Space with the cue.
5. **Lit room:** look at the wall lamps (no orb), the west and centre windows (no white lines, no floating lamp), the shelf (Tide Tables, burner, carton) and the chair.
6. **Kittiwake:** take the compass from the east window sill (G), then save, quit to the menu, and Continue.
