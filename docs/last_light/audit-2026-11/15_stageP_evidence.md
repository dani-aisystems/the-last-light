# THE LAST LIGHT: Stage P evidence (player body), 2026-11-17

Stage P of the audit plan (section 4, [A_character.md](A_character.md)): C11, the sitting glimpse, and C12, the clothing. It follows Stage S (`9969b89`). Index: [README](README.md). Plan: `~/.claude/plans/pasted-content-id-c83a-continue-the-gentle-lollipop.md`.

**Build:**

| Asset | Before | Now |
|---|---|---|
| Body `.blend` | v003 | `last_light_body_v007.blend` |
| Body export | `body_v003.glb` | `body_v005.glb` |
| Hands `.blend` | v007 | `last_light_hands_v009.blend` |
| Hands export | `hands_v007.glb` | `hands_v009.glb` |

The room, lighthouse and stairwell are unchanged.

**Daniel (2026-11-17):** match the chair's knit without touching the room (no edits to `build.py` or `documents.py`, no room rebuild); one navy, the chair's (DECISIONS Q19).

## 1. What changed

| ID | Change | Where |
|---|---|---|
| C11 | **Cause.** The body sat down on the chair on the frame E was pressed. The camera took 0.45 s to follow, so for that time a headless, armless torso stood in front of it (f00, f01), then an open neck (f02 to f04). **Fix.** Each frame the body is placed from the camera's *current* blended transform, and posed by `player.sit_amount()` (the camera's own ease, from wherever it was) on a new `sitdown` clip. Standing up runs the same in reverse; a second E mid-blend reverses from where it is. No fade. At the end of the blend the seated placement is G3c's exactly. | `player.gd` `sit_amount`, `_sit_from` / `_sit_to`; `player_body.gd` `_sit(s)`, `head_offset`; `body.py` `sit_at`, action `sitdown` (11 keys, a forward lean of up to 16 degrees mid-way) |
| 4.1.4 | One knit set, tileable, made from the chair's own knit. `documents.knit()` is sampled, not edited, and its mean (#363F58) is the target. Stockinette 1k (albedo, OpenGL normal, roughness), 2x2 rib, a darn in bluer wool, and the trousers' twill. | new `blender/knit_tex.py` → `blender/textures/cloth/` |
| 4.1.1 | The guernsey is its own garment, not the skin pushed out. Cut by planes, so the edges are clean (a level hem, a crew neck 2.5 cm lower at the front, cuffs square to the forearm). Edges turned in 9 mm, so none reads as paper. A snug 6 cm welt over the trousers' waistband; easy over the belly and back, with a soft blousing above the welt; fitted across the chest. Knit UVs at 12 stitches per 10 cm. | `body.py` `build_garments`, `garment`, `garment_cuts`, `turn_in`, `uv_garment`, `guernsey_offset` |
| 4.1.3 | Trousers as a garment: 12 mm of volume, cinched to 6 mm at the waistband, fuller at the knee and seat; the hem clears the boot shaft by 7 mm and breaks 12 mm lower at the front. Twill UVs. Boots get real UVs. | `body.py` `trousers_offset`, `trouser_hem`, `boot` |
| 4.1.5 | First-person sleeves bend. Each hand gets `wrist`, `forearm` and an `elbow` marker (children of the hand; 19 bones a hand). The sleeve goes from hand to forearm across 4 to 10 cm above the cuff; the hand's skin stub is trimmed inside the rigid part. Each frame the forearm is aimed at an elbow point low and outside the view, at most 70 degrees from straight, and the wrist takes half the turn. Rib cuff, knit sleeve, the darn kept, and 1.2 cm of pale shirt cuff below it. | `hands.py` `cuff`, `add_arm_bones`, `trim_skin`; `equipment.gd` `aim_sleeve`, `sleeve_turn`, `ELBOW` |
| 4.1 (fit) | **Found:** G3b's fingers went into the held items: the binoculars by 16.7 mm (palm included), the torch by 6.9, the compass by 5.0, and the two thumbs into each other over the bridge by 4.7. Fixed in the finger poses and a per-grip hand offset, fitted in Blender against the items as the game holds them. | `hands.py` `POSES` (`curl_k`); `equipment.gd` `GRIP_FIT` |
| 4.1.6 | Godot's glTF import drops the sheen, so wool and cloth get the StandardMaterial3D rim term at load. | `player_body.gd` `fabric_rim`, `RIM` |
| Tests | R27 (new); R16's bone count 32 → 38 and its near-plane bone set (the hand's bones, not the arm's), both updated in place. | `regress_test.gd` |
| Tools | `sitseq` and `standseq` run at 0.1x time and save a frame per sixteenth of the blend (at 1x a capture frame took the whole blend). `body.py --check` (posed poke-through), `hands.py --grip_check` (held-item fit, from R27's dump). | `capture_fp.gd`, `body.py`, `hands.py` |

**Not done as planned (with reasons):**

- **Cloth-simulated drape (4.1.1): PARTIAL.** The corrected look-down render shows the guernsey body is never in first-person view. It is seen only in shadow and in `body_3p`, so a simulation would buy nothing on screen. The garment has modelled ease, blousing and a welt instead.
- **Shirt collar (4.1.2): not on the body.** The body's head and neck are shadow-only, so a collar would float round an invisible neck. The shirt shows where the player sees it: the cuff below each sleeve.
- **Weave normal on the shirt cuff: dropped.** It is invisible on a 1.2 cm band, so it is not generated.

## 2. Verification

| Check | Result | Evidence |
|---|---|---|
| C11 on screen | PASS: no body in any frame sitting down or standing up | `stageP_cmp3_sitseq.png`, `stageP_cmp4_standseq.png` (p0 top, p4 below; p0 f00–f04 show the torso and the open neck) |
| R27, sit and stand | PASS (22 checks) | Stepped at 30, 60 and 120 fps; reversals at mid-blend; after a document, during a radio line; console ↔ radio; load while seated. The head is never more than 5 cm ahead of or beside the camera (worst 0.6 cm *behind*), and 0 seen vertices are in view. |
| R27 negative control | FAILS on the old `player_body.gd` (9 of 22), as it should | head 0.92 m ahead, 496 vertices in view; console → radio 1.76 m aside |
| Garment poke-through, 9 poses (idle, 4 walk, 3 sitdown, sit) | PASS: worst 1.85 mm (target < 2); boots through hems 0 | `renders/last_light/stageP/body_p2c/check4.json`. The measure was corrected twice, recorded: nearest-point signs and rim normals gave false 17 to 22 mm hits; it now casts from each inner point along its own normal. |
| Garment renders | PASS by eye | `stageP/body_p2c/*.png` (front, back, side, 3/4, walk, sit, the look-down view) |
| Cuff fit, static | PASS: skin 0.0 mm outside; shirt cuff 2.0 mm inside the guernsey's | HANDS_RESULT (the first build had skin 2.7 mm out: a box-based ellipse) |
| Held-item fit, posed in Godot | PASS: worst 1.31 mm over every pair, in torch, compass, binoculars half-raised, and compass with torch (was 16.7) | `stageP/grip_check2.json`; Blender renders `stageP/tune0` against `tune3` |
| Sleeves | PASS: every sleeve's far end out of frame (R27); bends 42 to 70 degrees; in the captures no cuff or sleeve edge enters the frame | R27, `stageP_cmp5_items.png` |
| Torch fist still closed | PASS: middle finger PIP 72 degrees (R16 wants over 70) | R16 |
| Body comparisons | PASS | `stageP_cmp1_body3p.png` (standing and seated), `stageP_cmp2_look_down.png` |
| Cost | Same surfaces (body: 3 seen, 2 shadow; hands: 4 per hand, no shadows). Body 18.0k triangles (17.6k), hands 23.0k (22.9k). GLBs 4.9 MB and 6.0 MB with embedded textures (0.7 and 2.1 MB) | material probe, BODY_RESULT, HANDS_RESULT |
| Bench (Medium, foreground, `--bench_body` against the body hidden) | PARTIAL: frame times inconclusive | **Structure, solid:** the body adds +32 to +35 draw calls (+42 in the bisect) and the same primitives. **Frame time, noisy:** 3 of 4 runs came up unfocused (the window behind another; one at 240 MB less video memory, smaller targets), and the machine was not quiet (Spotlight, load 3 to 7). The two body runs differ by up to 7 ms. The closest pair (base2 against body) gives about +0.9 ms, but the two differed in focus. A clean three-repeat bench belongs in Stage G (as the bisect proposed). `renders/last_light/sp_{base,body,base2,body2}_bench.json` |

**For Daniel's eye:**

- The look-down frame now shows the guernsey's belly at the bottom edge as knit wool. It reads fairly pale grey-blue under the lamp at that grazing angle (navy plus the rim term). If it's too pale, the guernsey rim can go from 0.35 to 0.2.
- Seated, the welt hangs a little behind the seat (`body_3p`).

**Daniel, 2026-11-17:** Stage P approved; the guernsey's rim stays 0.35; the cloth textures are committed (DECISIONS Q19).

## 3. Suites

Final state, headless under `taskpolicy -b` and `timeout`, 2026-11-17, after all of Stage P's changes.

| Suite | Result | New in Stage P |
|---|---|---|
| regress_test | PASS (449 / 449, 4 headless skips) | R27 (32 checks: 22 sit and stand, 10 grip and sleeve); R16 bone count and near-plane bone set updated in place |
| story_test | PASS (0 failed) | |
| opening_test | PASS (31 / 31) | |
| interaction_test | PASS (164 checks, the standing 12 sound warnings) | |
| qa_sweep_test | PASS (5,881) | |
| g5_weather_audio_test | PASS (50) | |
| run_tests | PASS (95) | |
| sim_v2, seeds 1 to 5 | PASS, no gate failures | |
| save_compat_test | PASS (305) | |
| pytest | PASS | |

## 4. Not done, and why

- The dialogue panel covers the compass hand in both the p0 and p4 compass frames at t064 and t072 (the radio talk). The compass fit rests on the Blender renders and the posed check.
- First-person frames still show no forearm by design: the bent sleeve runs out of view.
