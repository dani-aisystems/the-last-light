# THE LAST LIGHT: Stage R evidence (Ross), part 1: the staging marks, the figure, the three lit stills, 2026-11-17

**Status (2026-11-18): finalized and committed locally** (Daniel: "Finalize this stage"; DECISIONS Q24). Part 1 below is the checkpoint; part 2 (sections 7 to 14) is the upgrade and the game integration.

Stage R of the audit plan (sections 6.4 to 6.6 and 20.4, [B_ross_storyboards.md](B_ross_storyboards.md); cue points in [SCRIPT_REVISION_2026-11.md](../../../projects/games/last_light/SCRIPT_REVISION_2026-11.md) section 8), **part 1 only**, up to the checkpoint B 20.4 asks for: one lit still at A, B and C, for Daniel to judge whether Ross reads as a man and not a shape. Index: [README](README.md). Plan: `~/.claude/plans/pasted-content-id-4bbf-continue-the-scalable-patterson.md`.

**Not in this part, on purpose:** clips, `visitor_figure.gd`, the cue actions in ch4 to ch6, the door-shut gap light and shadow, the photograph slide, tests and window captures (later Stage R sessions, after Daniel's OK on the stills); the cough (Stage D). Nothing under `godot/` was touched; no `.dlg` or `chapters.json`.

**File number:** the brief named this record `16_stageR_evidence.md`; a parallel session had already written `16_stageE_evidence.md`, so this is 17.

**Licence:** the base mesh is `GEO-body_male_realistic` from Blender Studio's Human Base Meshes v1.4.1, logged CC0 1.0 in `assets/ASSET_LICENSES.md:12` (2026-11-04); the hands are the same bundle's `Hand - Realistic`, as `hands.py` uses it. No download, no AI or paid service.

## 1. The staging marks (B 20.4), verified in Blender

New `blender/ross.py --marks` opens the built room (`last_light_v078.blend`, which holds the `ASSET_stairwell` collection that `stairwell.glb` is exported from), poses the stair door open as Godot does (`review_views.pose_stair_door`, reused), and stands a body-sized proxy on each mark: boots, sea-boot shafts, the oilskin skirt, chest, shoulders, neck, head, the sou'wester's brim and crown, each banded to the figure's real widths. Checks: a ray down under each boot (floor within 2 cm), BVH overlap against every room and stairwell mesh (a designed contact passes only if a proxy inset by 2 cm clears it), and shoulder-to-hand reach (0.30 to 0.70 m, the shoulder moved by any lean or sway). Recorded in `spec.py` as `ross_marks` (room polar coordinates, like the device bearings). Nothing reads them yet; the Godot session turns them into anchors.

Final check (`renders/last_light/stageR/marks/marks.json`, 2026-11-17, against v078 with the door open):

| Mark | Feet (bearing, dist, z) | Faces | Floor under both boots | Contacts | Reach | Result |
|---|---|---|---|---|---|---|
| A landing, left hand on the oak rail by the newel | 160.70, 2.878, 0.006 | 345 | chequer plate | side plate (chest, skirt), drop chain (skirt): designed, clear when inset 2 cm | 0.523 m | PASS |
| B 0.6 m inside the door (his toes), left hand on the latch-side jamb at 1.05 m | 176.74, 2.129 | 330 | room floor | the door-shut path's slid photograph under his boots (designed, see below) | 0.548 m | PASS |
| C behind the desk chair, right hand on its top rail (0.88 to 0.95 m) | 0.00, 1.160 | 0 | rug | none | 0.649 m | PASS |
| D at the console handwheel, right hand on the rim | 76.91, 1.766 | 60 | room floor | none | 0.690 m bent 42 degrees | PASS |
| E by the desk, the mug on bare desk at 0.78 m | 17.64, 2.046 | 0 | rug | none (6.2 cm from the radio) | 0.662 m bent 25 degrees | PASS |
| Door head on the A to B walk | crown 1.93 m | | | trim underside 2.00 m | | PASS (7 cm) |

Renders (viewed): `renders/last_light/stageR/marks/plan_room.png`, `plan_door.png` (orthographic, from under the ceiling), `eye_A..E.png` (player's eye, 72 degrees; B's eye view predates B's final placement, which the B still shows with the figure itself).

**What the check found:**
- **A is a squeeze.** The landing between the housing's side plate and the hatch coaming is 0.365 m clear; a man's oilskin is 0.36 to 0.44 m. Square to the door his shoulders went 6 cm into the side plate. He now fills it: right side against the side plate, coat against the drop chain (both designed contacts, under 2 cm), upper body swayed 9 cm left over the newel his left hand rests on, turned 5 degrees toward the latch side where the player stands aside.
- **B: 0.6 m inside the door is his toes.** With his feet 0.6 m in, the latch-side jamb was 0.6 m behind his shoulders: the IK missed by 13 cm and the sleeve tore. Feet 0.45 m in (toes 0.6 m), the hand rests on the jamb at hip height.
- **D: the console stool** (0.64 m high, x 1.43 to 1.82, y 0.67 to 1.04) stands in front of the handwheel, whose centre is only 0.5 m up. He stands beside the stool, bent 42 degrees; whether he sits on it instead is the clip session's choice.
- **B's photograph:** his boots stand where `PROP_photo53door` lies. It is hidden on the door-open path (`game_fp._update_story_props`: shown only with the `photo_1953` clue from the slide); if the door is shut in chapter 4 and opened only in chapter 6 (R-14), the photograph is on the floor there, under him. For the Godot session.
- **The door head:** the crown's top at 1.93 m (stooped, the proxy's) against the trim's underside at 2.00 m: 7 cm on the A to B walk.

## 2. The figure: `blender/ross.py` → `ASSET_ross` → `last_light_ross_vNNN.blend`

| Item | Value | Budget | Result |
|---|---|---|---|
| Final build | `last_light_ross_v009.blend` (v001 to v008 are this session's iterations) | | |
| Triangles (`SK_ross`, one mesh) | 20,909 | 25,000 | PASS |
| Materials | 2: `M_LL_Ross_Oilskin`, `M_LL_Ross_Skin` | 2 | PASS |
| Texture set | 1 at 2048: `T_LL_Ross_albedo` (RGBA), `T_LL_Ross_normal`, `T_LL_Ross_orm` | one 2k set | PASS |
| Bones (`ARM_ross`) | 49: `body.py`'s 19 plus 15 finger bones a hand | | |
| Height | 1.857 m to the hat's crown, stooped (1.88 m upright) | tall | |
| `validate_asset.py --target gltf` | FAIL 0, WARN 3, PASS 13 | FAIL 0 | PASS, WARNs explained below |
| Export | `exports/last_light/gltf/ross_v001.glb` (9.0 MB, textures embedded); not synced to `godot/` | | |
| `reimport_check.py` | ok: loads; mesh count, triangles, materials, size all match | | PASS |

**The three WARNs:** 17 n-gons (from the turned-in rims; glTF triangulates on export); 789 non-manifold edges (the figure is assembled from open garment shells, the coat single-sided with turned-in edges; watertightness is a Roblox rule, not a glTF one); the bounds' centre sits 12 cm forward of the origin (the stoop and the hat carry his mass forward; the origin stays between his feet, where the rig and the marks put it).

**Not checked yet:** no posed poke-through measure (the `body.py --check` method) was run on the coat; the stills are the only evidence of fit, and they show the sleeve tearing at hard-bent wrists (section 4). Godot's glTF import of the clearcoat, the alpha-tested stubble and the double-sided coat is NOT TESTED (no Godot work this session).

Preview renders (neutral light, viewed): `renders/last_light/stageR/fig/t10_front.png`, `_side`, `_back`, `_q34`, `_face`, `_glance` (160 px).

**How it is built (reuse first):**
- **Body and rig:** the CC0 male at multires level 0 is the cloth collider and weight source (never exported); the visible head is level 1, decimated to 4.6k triangles. Scaled to 1.88 m upright. `body.py`'s 19-bone rig and its region-limited weights are reused by importing `body.py` with its scale set to Ross's (`body.S`; `body.py` itself is not edited).
- **Aged and stooped:** cheeks and temples hollowed, a brow that throws shadow, mouth corners turned down and lips thinned, a thinner neck, a thinner chest, broader shoulders (a seaman's frame, thinned). The stoop (chest 12, neck 10, head back 12 degrees; shoulders rounded, arms 5 degrees forward) is applied as the rest pose, so the coat drapes on it and every clip will start from it.
- **Hands:** `hands.py`'s CC0 realistic hand with its traced 16-bone rig (and its Stage P grip poses), 1.12x for a big man's hand, grafted under the sleeve with the palm to the thigh; the oilskin cuff hides the wrist. 15 finger bones a hand join `ARM_ross` under `hand.L` / `hand.R` (49 bones in all).
- **Oilskin:** the body's torso and arms eased out (3 cm, sleeves 2.5 cm, the waist filled so it hangs straight from the shoulders, the chest smoothed flat), cut by planes at the neck, wrists and hips (arm and hip told apart by the rig's weights, not by distance: the forearms hang beside the hips), a skirt extruded from the hip loop to 0.40 m with godet folds widening to the hem, a 5 cm collar open at the throat. Draped by Blender cloth (fixed settings, 36 frames, the yoke, collar and waist pinned, the body as collider), smoothed, edges turned in 9 mm (`body.turn_in`), weights transferred from the body and smoothed so the sleeves cannot tear, the skirt following the pelvis with a little of each thigh.
- **Sou'wester:** a four-panel crown fitted over the skull (1 cm clear), a real brim: 6.5 cm and nearly flat at the front, 9 cm at 20 degrees at the sides, 16 cm at 34 degrees at the back (it sheds water off the neck), 4 mm thick with a rolled edge, a slight soft wave; chin ties to a knot under the chin.
- **Scarf:** undyed dark grey wool, a roll round the neck inside the collar, thickening at the throat into the knot, two short tails into the coat.
- **Sea boots:** `body.boot`'s foot loft (scaled, 7 % shorter) with a rubber shaft to the knee and the top turned down.
- **Stubble and hair:** a shell 1.6 mm (hair 3 mm) over the jaw, cheeks, lip, sideburns and nape, alpha-tested dots whose density fades to nothing before the region's edge.
- **One texture set, baked in Cycles from procedural shaders** (`blender/textures/ross/`, 2048 px): albedo with alpha (the stubble), tangent normal, and an ORM-style map (R clearcoat, G roughness). Oilskin #1C1B18 with lighter worn wax on the edges, rain runs, a crumple in the normal, beads on up-facing surfaces (roughness 0.05, clearcoat 1), clearcoat lower in the creases; rubber boots; grey wool knit; weathered skin, ruddier at the nose and cheeks, darker thin lips, greyer under the stubble, redder knuckles.
- **Two materials:** `M_LL_Ross_Oilskin` (double-sided; coat, hat, boots, scarf) and `M_LL_Ross_Skin` (alpha-tested; head, hands, eyes, stubble, hair).

## 3. The game's lighting in Blender, calibrated

The stills use **only the game's lights**, translated from `station.gd`: a point at each `LIGHT_*` empty (walls 0.72, stair pendant 0.26, the desk spot 2.6 at 55 degrees aimed as `_make_light` does), the four instrument spots, the generator cage bulb, the door's bounce fill (energy 1.6, 19 degrees, aimed at the *shut* leaf's centre, as Godot computes it at load), the window spill (0.14, cold), the probe's warm ambient, Godot's colours linearised (Godot treats light colours as sRGB), AgX with exposure x1.35, vertical FOV 72 degrees, eye 1.65 m. The room's materials take `materials.gd`'s palette (cream walls above a green dado, etc.) in the render scene only; the room `.blend` is not saved.

**Calibration** (`ross.py --calibrate`, the `cu_door` view against the game's `s5r2_t060_cu_door.png`, Rec. 709 luma as `measure_luma.py`):

| Crop | Game | Blender (k 40, door fill 30, ambient 1.6) |
|---|---|---|
| Door leaf (`measure_luma` crop) | 0.1208 | 0.1233 |
| Left wall, lamp side | 0.3390 | 0.3498 |
| Frame (top 75 %) | 0.1603 | 0.1663 |

Two things had to be found first: the bulbs sat inside their own globes and guards (EEVEE let the fixtures shadow them; Godot's lamp meshes cast no shadows), and Godot's light colours are sRGB. **Limits:** Blender's lights fall off as 1/d², Godot's as d^-1.2, so lamps and the door fill needed separate factors and nothing is exact away from the calibration distances; the room shader's scan detail is absent. The stills are Blender approximations of the game's light: the Godot captures in the later session are the real test.

## 4. The checkpoint: three lit stills

**For Daniel:** `renders/last_light/stageR/stageR_checkpoint_sheet.png` (the game's figure today at the top, then A, B, C) and `stageR_checkpoint_crops.png` (his upper body from each still, 1.6x). The stills themselves: `renders/last_light/stageR/stills/rA_s10.png`, `rB_s10.png`, `rC_s10.png` (1920 x 1080, figure `v009`), with their figure masks and `metrics_s10.json`. Camera: the player's eye at 1.65 m, vertical FOV 72 degrees, aimed at his upper chest; A from 1.6 m on the latch side (where the player stands aside), B from the room's south-west, C from the front-right three-quarter by the desk's east end.

**Measured on each still** (Rec. 709 luma of the sRGB pixels inside the figure's mask; the eye and jaw boxes are his posed landmarks projected into the frame). The targets were set by Claude before the first render, in the plan:

| Measure | Target | A | B | C |
|---|---|---|---|---|
| Eye box, mean | at most 0.035 | 0.015 | 0.014 | 0.020 |
| Eye box, brightest pixel | at most 0.08 | 0.046 | 0.046 | 0.070 |
| Brim ratio (eye box mean / jaw box mean) | at most 0.35 | 0.344 | 0.292 | 0.203 |
| Silhouette edge contrast | at least 0.08 | **0.069** | 0.117 | 0.108 |
| Jaw and cheek edge, 95th percentile (B: "catching light") | at least 0.25 | 0.101 | **0.098** | 0.116 |
| Rim on the upper body's outline (A: "pendant as rim") | at least 25 % | **0.03 %** | 6.9 % | 3.3 % |
| Hand IK error | | 0 | 0 | 0 |

**The brim sweep** (`ross.py --stills --sweep`, ray tests, not pixels; `renders/last_light/stageR/stills/sweep_s9.json`, same brim and pose as v009): from 37 standing viewpoints round A, B and C (eye 1.65 m, 1.3 and 2.2 m away, 0 to 90 degrees off his face), **no part of either eye is both seen and lit** (at most 4.2 % seen, from 90 degrees at B, and that part unlit). **Seated at the radio** (eye 1.2 m), looking back at C: 18.3 % of the eyes' surface is seen from below, 0.8 % seen and lit.

**Results:**

| Check | Result | Evidence |
|---|---|---|
| He reads as a man (Daniel's judgement) | **For Daniel** | the sheets above |
| Eyes and upper face dark in every lit view | PASS in the three stills (all eye boxes under target) and from every standing viewpoint in the sweep; **PARTIAL** for the seated radio view at C | metrics, sweep |
| A: stair pendant as rim | **FAIL as specified**: the pendant hangs beside him (0.43 m to his left, level with him), never behind him from any place the player can stand; it lights the limewash behind him instead, so he reads as a dark silhouette against a lit wall (edge contrast 0.069) | `rA_s10.png`, the geometry in section 1 |
| A and B: wall lamp 2 as side key | **FAIL as specified**: lamp 2 (bearing 148) is outside the housing and behind the door plane, so the side plate hides the landing from it entirely; at B the open leaf stands between it and most of him (worked out from the coordinates: lamp at (1.64, -2.62, 22.25), side plate at x 1.04 to 1.24 from the door plane to the wall, the leaf 2.04 m tall; not separately ray-tested) | `plan_door.png`, `rA_s10.png`, `rB_s10.png` |
| B: brim shadow; stubble and cheek edge catching light | PARTIAL: brim shadow PASS; the cheek edge stays dark (jaw 95th percentile 0.098), and under the brim a pale curve of lip and stubble catches the door fill and can still read as a grin | `rB_s10.png`, the crops |
| C: the warm room on battery during the lock | PASS: the room at full warm light, the generator's run lamp dark, the desk lamp on the radio; he stands behind the chair, hand on it | `rC_s10.png` |
| Coat fit | PARTIAL: the sleeve tears where the wrist bends hard (B's hand on the jamb, A's on the rail: skin shows through the cuff); B's coat front folds into two rounded bulges under the light that can read as a bust | the crops |

**Not done, and why:**
- **The extra light the storyboard wanted** (pendant rim at A, lamp 2 key at A and B) is not faked into the stills: the game's lights cannot give it. It is a Godot decision, see section 5.
- **Room light sag during the lock** (B 6.3, "room lights sag slightly"): not in `station.gd` (lights stay at full while the battery is at least 10 %), so C shows the room as the game has it.
- **No mug in his other hand at C** (R-6): the grip was not built this session.

## 5. For Daniel, and for the next Stage R sessions

**Daniel's judgement:** whether he reads as a man at A, B and C. Claude's own reading: A and C do (a stooped tall man in a wet oilskin and a sou'wester, face lost under the brim, one hand on the rail or the chair); B is the weakest (the lit lip and stubble under the brim, the coat's chest).

**Proposed fixes before any animation, if Daniel agrees:**
1. **B's face:** darken the lip region further and pull the stubble shell's lower edge below the lip line, or tip his head 4 degrees further down at B.
2. **The coat front:** flatten the chest band a second time after the drape (the cloth sim re-forms the pecs), and keep the closure groove off the centre line.
3. **The cuffs:** weight the last 6 cm of each sleeve to the hand bone (as `hands.py` does for Callum's cuff), so the cuff turns with the wrist.
4. **Light in Godot (a decision):** Ross on his own render layer with one light only he receives (a warm, low-energy side key from lamp 2's direction, and a rim from the stair side), so the storyboard's look is possible without changing the room. The alternative is the stills as they are: a silhouette against the lit stair.
5. **Seated at the radio with Ross behind the chair:** the seated view sees under the brim; either C moves half a metre to the side while the player sits, or the seated look limits keep him out of a below-view.

**Calls Claude made (overrule freely):** height 1.88 m upright; the scarf undyed dark grey wool; EEVEE, not Cycles, for the stills (closest to Godot); the marks as recorded in `spec.py` (A as a squeeze, B's 0.6 m as his toes, D beside the stool).

## 6. Files

| File | Status |
|---|---|
| `projects/games/last_light/blender/ross.py` | new: marks, build, calibrate, stills, sweep |
| `projects/games/last_light/blender/spec.py` | `ross_marks` added (nothing reads it yet) |
| `projects/games/last_light/blender/textures/ross/T_LL_Ross_{albedo,normal,orm}.png` | new, generated by `ross.py` |
| `projects/games/last_light/blender/last_light_ross_v001..v009.blend` | new (v009 is the figure) |
| `exports/last_light/gltf/ross_v001.glb` | generated, gitignored, not synced |
| `renders/last_light/stageR/` | marks, figure previews, calibration, stills, sweep, sheets (gitignored) |

`tools/py -m pytest -q`: PASS (exit 0) after the `spec.py` change. The Godot suites were not run: no Godot file changed.

**Commands:**
- the marks: `tools/bl <room.blend> -P projects/games/last_light/blender/ross.py -- --marks renders/last_light/stageR/marks [--norender]`
- the figure: `tools/bl -P …/ross.py -- --new --save --preview DIR`
- the calibration: `tools/bl <room.blend> -P …/ross.py -- --calibrate DIR`
- the stills: `tools/bl <room.blend> -P …/ross.py -- --stills DIR --figure …/last_light_ross_v009.blend --tag T [--sweep]`


---

# Part 2 (2026-11-18): Daniel left the call to Claude ("You determine"), then asked for the full upgrade

**What happened:** asked whether Ross reads as a man, Daniel replied "You determine". Claude's call, after a close look at full resolution: **not yet**. A and C read as a figure at game distance, but in close-up and in neutral light the coat read as glossy latex: no folds, one even shine all over, sleeves showing the arm's muscles, a bust in front, a pear-shaped waist. B also had a grin: the lips were slightly open, so a lit lower lip under a dark parting read as a smile. At A, the grafted hand's wrist stub poked out through a torn cuff. Daniel then sent a broad brief: audit Ross, choose the tools, improve the model, integrate him in Godot, fix the door and ending staging, and capture before and after. This part does that, inside the project's standing rules.

## 7. Tools and workflow (brief phase 2)

| Option | Verdict |
|---|---|
| Meshy, Higgsfield `generate_3d`, any text- or image-to-3D, AI concept images | **Not used.** CLAUDE.md ("Never: paid or AI-generation APIs") and DECISIONS Q11 (no AI-generated images; the only exceptions are prints Daniel supplies). Lifting that is Daniel's call, not a brief's. |
| Mixamo | **Not used.** It needs an Adobe login and an upload of the character, the result is not CC0, and the game's rig is `body.py`'s (Ross shares it with the keeper), so its clips would need retargeting anyway. |
| Sketchfab, Fab, Poly Haven downloads | **Not needed, not fetched.** Any download needs Daniel's OK (CC0 only). The CC0 base mesh and hands already logged in `assets/ASSET_LICENSES.md` cover the figure. |
| **Blender (`ross.py`) → glTF → Godot** | **Chosen.** Fully procedural and reproducible, reuses the keeper's rig, validation, export and reimport tools (`scripts/`), and the `body.glb` pattern Godot already plays. |

## 8. The figure, v012 (`ross.py`, build changes)

Each item was found by looking (stills, a neutral-light preview sheet, full-resolution crops), fixed with a measured change, and looked at again.

| Defect (where seen) | Fix in `ross.py` | Result (seen) |
|---|---|---|
| Latex look: roughness 0.36 plus a clear coat everywhere (`t10_sheet`, all stills) | Waxed cotton is satin: base roughness 0.55. **Wet** (roughness −0.30, clear coat 0.45) only where rain sits (up-facing) and in the rain runs; beads stay on the shoulders and hat. Albedo #1C1B18 → #161513 (it read grey in neutral light). | `t14`: reads as cloth with wet shoulders |
| Bust (B, neutral front) | `fill_torso`: every 2 cm slice of the torso pushed out to its convex hull (no sternum valley, no under-pec shadow), then the front hangs from the chest (at most 20 cm back per metre down). Run before and after the drape (the drape pulled the chest back in). Only moves vertices outward. | gone in `t15` front and `rB_s12` |
| Ledge where the filled torso met the skirt (`t11g`) | the fill fades out over the skirt's top 25 cm | gone |
| Pannier at the waist (`rB_s11`): elbows beside the waist were counted as torso | hull points only where the arm weight is ≤ 0.15 and within 0.22 m of the centre line | gone (`rB_s12`) |
| Sleeves showing biceps and deltoids (`t10`, `t11g`) | the sleeve smoothed (8 passes), then made a tube round the bone: at every point as wide as the widest part below it, at most 30 mm of new room, 12 mm bell at the cuff, the shoulder cap left out | straight sleeves (`t14`) |
| Nothing said "coat" from the front | two hip pocket flaps and four horn buttons down the off-centre closure, laid onto the draped shell by rays (`coat_details`) | `t15` front, `rB_s12` |
| Grin (B): open lips, lit lower lip | lower lip set back 3 mm and up 1.6 mm (closed mouth), lips darker (#5A4038, 85 %) | `rB_s12`: no grin |
| Wrist stub through the cuff (A) | the hand graft's 7 cm forearm stub weighted to the forearm (it swung out with the hand); the last 8 cm of each sleeve follows the hand by up to 35 % | `rA_s12`: clean (zoom checked) |
| Stubble too white in neutral light | #9C978E → #8A857C | `t14_face` |
| Weights up to 1.037 made the mesh "invalid" for the glTF exporter | `clamp_weights` (46 clamped) | export clean |

**Budget (v012):** 21,169 triangles (≤ 25,000), 2 materials, one 2k set, 49 bones. **Validation** (`validate_asset.py`, gltf): FAIL 0, WARN 3 (as part 1). **Reimport:** ok.

**Stills, s12** (same cameras and calibrated game lights as s10; `renders/last_light/stageR/stills/`; before and after sheet: `renders/last_light/stageR/stageR_before_after_stills.png`):

| Measure | A | B | C | s10 → s12 |
|---|---|---|---|---|
| Eye box mean | 0.011 | 0.013 | 0.015 | all lower or equal |
| Eye box max | 0.032 | 0.036 | 0.057 | all within 0.08 |
| Brim ratio | 0.288 | 0.295 | 0.154 | all better |
| Edge contrast | **0.084** | 0.125 | 0.111 | A now passes 0.08 (was 0.069) |
| Jaw p95 (B) | | 0.088 | | still below 0.25: the stubble does not catch light at B (unchanged finding) |

An intermediate run (s11, v011) gave C an eye-box max of 0.31. The zoom showed both eye boxes on the brim: the eyes are behind it, and the peak was the wet brim's new highlight. With v012's pose it is 0.057.

## 9. The game: `ross.glb` and `visitor_figure.gd`

**Actions** (`ross.py --actions`, on the figure, saved as v017):
- `idle`: a slow breath, 3 s.
- `walk`: an old man's walk (body.py's leg cycle at 0.72 / 0.80 / 0.70 of its swing, 1.2 s a stride, little arm swing, eyes on his feet). Measured ground speed **0.953 m/s** (the planted foot's slide); the game moves the root at exactly that, so the boots do not skate.
- `door`, `chair`, `wheel`: the held poses at B, C and D, solved by IK at the mark exactly as the stills are, with the breath, baked to plain keys.

Two bake bugs were found by the Godot test and fixed:
1. `finger_pose` works in Euler and the keys are quaternions, so the grips were lost.
2. The actions already baked sat on live NLA tracks that overrode the next pose being solved. The wheel lost its lean, so the hand was 27 cm off.

D also needed a hip hinge (24 degrees, legs kept upright): a spine curl alone left the wrist 13.6 cm short of the wheel's rim.

**Export:** `exports/last_light/gltf/ross_v006.glb` (validation FAIL 0, reimport ok), synced to `godot/assets/models/ross.glb` (generated, DECISIONS Q10).

**`visitor_figure.gd`** (rewritten; its node contract with `game_fp.gd` unchanged: `_spawn_visitor`, the save's `visitor`, the capture's `queue_free`). No `.dlg`, `chapters.json` or `game_fp.gd` change.
- Loads `ross.glb` and loops its clips. It gives the oilskin back what Godot's glTF import drops: the clear coat (from the ORM texture's red channel, the wet mask) and a cloth rim (0.18, as `player_body.gd` does for wool).
- Stages him from the story state (see its header):
  - **live** (a conversation running when he is spawned): hidden until the leaf is 80 % through its swing, then he walks in from the landing (A) through the doorway to B. Before, he appeared at once, possibly while the door was still moving.
  - **B:** hand on the jamb, breathing (ch4, ch5).
  - **D:** walks to the wheel when `ross_wheel` is set ("Two men to one wheel").
  - **C:** walks to the back of the desk chair at the `rescue` beat ("Hand Ross the handset"), and stays there through the dawn ("lets go of the back of the chair") and under the ending card.
  - **A loaded save or a capture:** straight to his mark.
  - **A move during a black fade:** no walk.
- **Routes:** checked on the plan (`renders/last_light/stageR/marks/plan_room.png`).
  - B to D passes the open leaf's free edge by about 0.5 m.
  - D to C goes via a point toward the centre, 0.8 m clear of the console stool.
- The old procedural sway (a transform written every frame) is gone. The skeleton animates instead, as the keeper's body does.

**Test:** new `godot/tests/ross_test.gd`, **35/35 PASS**:
- the import: 1 mesh, triangles, 2 materials, 5 actions, ORM, double-sided coat, alpha-scissor stubble, the figure's clear coat and rim;
- the hands on their contacts **in Godot**: B 0.0 mm, C 0.0 mm, D 17.7 mm;
- the staging with a stand-in game: entrance, the walk speed (0.953 m/s), the B → D route (within 2 cm of its line), the rescue to C, the load, and a fade hiding a move.

## 10. In-game check (one batched background capture, silent)

`tools/godot_bg … -- --capture=r1 --shots=60@cu_door!visitor,60@fp_stair!visitor,60@cu_door!visitor!dark,60@fp_stair!visitor!dawn --bot=expert`. The "before" is the same views and state from 2026-11-15 (`a0_*-visitor.png`, the cylinder figure). Sheets: `renders/last_light/stageR/stageR_godot_before_after.png` and `stageR/r1_dark_dawn.png`. All viewed.

| Shot | Before | After |
|---|---|---|
| `cu_door!visitor` | a stack of black cylinders under a lampshade hat | a stooped man in a buttoned oilskin just inside the door, his hand at the jamb, face under the brim, rain on the hat catching the lamps |
| `fp_stair!visitor` | the same block shape | a figure of the right size in the doorway, readable from across the room |
| `cu_door!visitor!dark` (new) | n/a | the blackout's red pendant: a clean silhouette (brim, shoulders, stoop), red glints on the wet hat |
| `fp_stair!visitor!dawn` (new) | n/a | reads in the flat dawn light |

**Performance:** 47 fps at 1x in `cu_door` with Ross in view (the capture's PERF line, a background window, so indicative only).

**Seen, not fixed:** the clear coat glints (clear coat roughness ×0.25 of the ORM's green) make small sharp sparkles over the coat in close-up; they read as rain but a little like sequins. The knob is `visitor_figure.gd` `CLEARCOAT` (0.25 → 0.5 would soften them). It needs a re-capture to judge, so it was left.

## 11. Results (part 2)

| Item | Result | Evidence |
|---|---|---|
| Figure reads as a man in a coat, not a gown, not a shape | **PASS** (Claude's judgement, the call Daniel delegated) | `stageR_before_after_stills.png`, `stageR_godot_before_after.png`, `t15_front` |
| Brim keeps the eyes dark (A, B, C) | **PASS** | s12 eye boxes ≤ 0.036 mean, ≤ 0.057 max. The ray sweep was not re-run: brim and head poses are unchanged since s9. |
| Budget, validation, export, reimport | **PASS** | 21,169 triangles; validation FAIL 0 / WARN 3; `ross_v006.glb` reimport ok |
| Held poses' hands on their contacts in Godot | **PASS** | `ross_test` R2: B 0.0 mm, C 0.0 mm, D 17.7 mm |
| Door entrance, the walks to D and C, load and fade behaviour | **PASS (logic, headless)**; **NOT TESTED visually** (no capture state stages a live entrance or ch6, and `capture_fp.gd` belongs to another session) | `ross_test` R3 and R4 |
| Game suites | **PASS**: story, sim_v2, run_tests 95, opening 31, interaction 164 checks, regress 468, save_compat 305, ross 35, pytest. `portrait_test` fails 3 on the "Mary Ellen" speaker: an untracked test from another session, untouched by this work. | test output in the session log |
| Godot integration (scale, orientation, shadows, textures, normal map, alpha, roughness) | **PASS in the door captures**: 1.88 m figure on mark B facing 330; casts shadows (default on, shadow meshes imported); textures, normals, alpha scissor and clear coat present | r1 captures, R1 |
| Ending | **PARTIAL by design**: he is behind the chair (C) from the rescue call through the dawn and under the ending card, but the ending card itself is 2D panels Daniel supplies, so nothing of the figure shows there | `visitor_figure.gd` header |

**Remaining, for Daniel or later sessions:**
- the clear-coat sparkle knob (above);
- a capture state for the live entrance and ch6 marks, so they can be seen in-game (a `capture_fp.gd` change, the other session's file);
- the Ross-only light proposal (part 1, section 5) is still open: the door captures read without it;
- the seated-at-the-radio view under the brim at C (part 1, section 5) is unchanged;
- the entrance starts with him appearing on the landing (A) in the stairwell's dim light: no clip brings him up the stairs;
- the face itself (aged features, ears, eyelids) was not reworked: it is under the brim in every standing view, so the gain would be seen only seated at C.

## 12. Files (part 2)

| File | Status |
|---|---|
| `projects/games/last_light/blender/ross.py` | changed: coat fill and hang, sleeve tubes, cuff and stub weights, coat details, mouth, materials, `--actions` (idle, walk, held poses), weight clamp |
| `projects/games/last_light/blender/textures/ross/*.png` | regenerated |
| `projects/games/last_light/blender/last_light_ross_v010..v017.blend` | new (v012 the figure, v017 the figure with its actions) |
| `projects/games/last_light/godot/assets/models/ross.glb` (+ extracted textures, `.import`) | new, generated (Q10) from `exports/last_light/gltf/ross_v006.glb` |
| `projects/games/last_light/godot/scripts/fp/visitor_figure.gd` | rewritten (the figure and its staging) |
| `projects/games/last_light/godot/tests/ross_test.gd` | new |
| `renders/last_light/stageR/…`, `renders/last_light/r1_*` | renders and sheets (gitignored) |

Not touched: `game_fp.gd`, `capture_fp.gd`, `.dlg`, `chapters.json`, CLAUDE.md, settings, ROADMAP, the Stage M files.

**Commands:**
- the actions: `tools/bl …/last_light_ross_v012.blend -P …/ross.py -- --actions --save`
- then `validate_asset.py`, `export_asset.py --name ross`, `reimport_check.py`, `sync_assets.py ross` (as `pipeline.sh` does for the room)
- the test: `tools/godot --headless --path projects/games/last_light/godot -s res://tests/ross_test.gd`

## 13. Part 2, continued: the staging seen in-game, and two Godot-side fixes

Daniel said "Continue". The gap was that the live entrance and the ch6 moves had been tested only headless. New `godot/tests/ross_shots.gd` (a windowed `SceneTree` script, silent, run with `tools/godot_bg … -s res://tests/ross_shots.gd -- --tag=rN`) closes it. It boots the real main scene and drives the real `game_fp`, station and director; only the story state is set by hand (director held), and it reuses no capture state. `capture_fp.gd` was not touched.

**Seen in-game** (`renders/last_light/stageR/r5_entrance.png`, `r5_ch6.png`, frames `renders/last_light/r5_*.png`):
- **Entrance:** hidden while the leaf swings; then on the landing, in the doorway, inside; settles; hand on the jamb.
- **ch6:** the walk across the room to the wheel and the bend over it, hand on the rim; the walk to the chair and the chair pose behind it.

The frame notes (mark, animation, position) match the plan at every frame.

**Defects found by looking, and fixed:**

| Seen | Cause | Fix | After |
|---|---|---|---|
| Close-up at B: the wet shoulders read as black plastic, mirror-sharp lamp spots (`r2_coat_close`, `r3_b_close_*`) | Godot clear coat at strength 1.0 and roughness ×0.25, over a base the bake had left at about 0.3 where wet; faint cloth normals | Godot (`visitor_figure.gd`): clear coat [0.6, 0.6], oilskin normal scale 1.6. Bake (`ross.py`): wet roughness −0.18 (was −0.30), crumple ×2.4, a new small-crease noise, bump strength 1.0 | `r4_close.png`: a broad, soft wet sheen |
| Close-up: a smooth, young, mannequin jaw (`r3_b_close_front`, `r4`) | the alpha-scissor stubble dots average away in the mipmaps; alpha to coverage (tried, kept) was not enough | the stubble also baked into the skin's albedo: a grey cast over the beard area plus the dots (#A8A399) | `r5_face.png`: a grey, unshaven jaw and cheek at 0.7 m |
| A seated look up into his face from below (`r2_chair_c_seated_look`) | not reachable in play: seated at the radio is focus mode, where mouse look is off and the camera is fixed (`player.gd` `_unhandled_input`, `_sync_camera`) | none needed. Part 1's "seated at the radio sees under the brim" finding is withdrawn for the same reason. | n/a |

**Seen, not changed:** at the wheel, from over his back (`r5_wheel_c_close`), the crown, the long back brim and the collar stack into a ribbed silhouette. It is an awkward angle more than a defect; it would go if the brim's back flap were 3 to 4 cm shorter, but the back flap is what makes it a sou'wester, so it was left.

**Final assets:**
- figure `last_light_ross_v020.blend`, with actions `v021`;
- `exports/last_light/gltf/ross_v008.glb`, synced to `godot/assets/models/ross.glb`;
- 21,169 triangles; validation FAIL 0 / WARN 3; reimport ok;
- `ross_test` 35/35.

**Stills s13** (v020; Blender, game lights):

| Still | Eye box (mean / max) | Brim ratio | Edge contrast | Jaw p95 |
|---|---|---|---|---|
| A | 0.012 / 0.037 | 0.292 | 0.084 | |
| B | 0.014 / 0.046 | 0.289 | 0.122 | 0.093 |
| C | 0.012 / 0.032 | 0.118 | 0.113 | |

All are within the eye-box targets.

**More files:**
- `godot/tests/ross_shots.gd` (new);
- `last_light_ross_v018..v021.blend` (v020 the figure, v021 with actions);
- superseded: v010, v011, v013 to v016, v018 and v019, which can be deleted on Daniel's OK.

**Godot suites:** unchanged since section 11 except `visitor_figure.gd`'s material settings; `ross_test` re-run, 35/35.

## 14. Part 2, continued again: he acknowledges the keeper

Daniel said "Continue" again (no commit or delete OK, so neither was done). The brief's "remain standing unnaturally" was half answered: he walked, held and breathed, but never reacted to the keeper. Now he does.

**`visitor_figure.gd` `HeadTurn`:** a `SkeletonModifier3D` that runs after the animation each frame.
- When he stands (not walking, not settling) and the keeper's eye is within 3.5 m and in front of him (within 110 degrees of his facing), the head turns toward it.
- It turns at most 35 degrees, split neck 40 % and head 60 %, eased (rate 2.5/s).
- It is yaw only, so the stooped head keeps its downward tilt and the brim stays over the eyes. Part 1's ray sweep covered views from face-on to 90 degrees off his face; no eye surface was both seen and lit.

**Test:** `ross_test` R5, **42/42 PASS**. With the keeper 30 degrees to his left, the head bone turns 30 degrees, measured in the final skinned pose on `skeleton_updated` (a modifier's change lives only inside the skeleton's update). For a keeper at 70 degrees it stops at 35; there is no turn for a keeper behind him or 5 m away, and none while he walks.

**Seen in-game** (`renders/last_light/stageR/r6_head.png`, frames `r6_head_*`):
- the same camera, the keeper behind him: the pose's own head;
- the keeper 2 m to his left: the head turns to him, the brim still over the eyes;
- zoomed: a stubbled cheek and jaw and a closed, set mouth (no grin).

The harness had to move the player's camera with the player: disabled, the player no longer positions its camera. That is a harness detail; in play the camera follows the player.
