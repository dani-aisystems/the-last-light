# THE LAST LIGHT: Document 3: full issue register

> Audit of 2026-11-15 at commit `2b5d3ee`. Paths are relative to `projects/games/last_light/` unless they start with `docs/`, `assets/`, `renders/` or `tools/`; `g/` means `godot/`. Section numbers are those of the approved plan. Index: [README](README.md).

## 3. Issue register

Priority: P0 broken progression or mechanic; P1 major readability, rendering or narrative fault; P2 visual or usability; P3 enhancement.

### 3.1 Dialogue, UI, documents, guidance

| ID | Issue | Evidence and cause | Pri | Fix | Acceptance test |
|---|---|---|---|---|---|
| D1 | Dialogue skippable | Code: `dialogue_ui._unhandled_input` advances any line on Space / pad RT after 0.5 s | P1 | Remove the advance path for all line types; all lines advance on reading time; replies still wait for the player | regress: real Space, held Space, clicks and every mapped action sent during each line type never change the line index |
| D2 | Radio lines wait forever; E dropped meanwhile | Code: radio `auto_advance` off; `play_aside` returns false while a line is up | P0 | D1 plus a queue for examine thoughts (as device thoughts already have) | opening_test without any Space; E on every examinable during a radio line produces its line within 6 s of the line ending |
| D3 | No three-line limit; panel and card grow | Code: `fit_content` label, panel grows upward; 26 of 177 radio lines exceed three lines, 9 reach five | P1 | Fixed panel height per text size; a runtime paginator in `dialogue_ui.gd` that measures the real layout and breaks at sentence, then clause, boundaries (the only way the limit holds at text size 1.5, where a line holds about 28 characters); hand edits in `.dlg` wherever a lint reports an awkward break | qa_sweep: every radio message measures 3 lines or fewer at text 0.8, 1.0, 1.5; panel rect identical before and after every line |
| D4 | Portrait border | Code: the 8/10 px cream margin is drawn deliberately; the band under the photo grows with the panel. Image files are clean 512x640 | P2 | Fixed card; photo cover-cropped to fill its window edge to edge inside a thin dark keyline; no variable band | portrait_test: photo rect equals card rect minus keyline for every speaker at three text sizes |
| D5 | VHF panel covers the radar | Code + Capture `g22_t100`: covers 21 px at 16:9, about a quarter of the scope at 16:10 | P1 | Draggable by its title bar, clamped to the viewport, position saved in Settings; new default clear of the radar; compact mode | regress: scope's projected rect and panel rect do not intersect at 16:9, 16:10, 1280x720; drag never fires a room interaction |
| D6 | Tide Tables do nothing | Code: no document id; thought dropped while any line is up | P1 | New `tide_tables` document through the existing viewer; the Grant's thought becomes its after-read line in chapter 4 | interaction_test: E opens and closes the document in every chapter, with and without a line showing |
| D7 | Keeper's Orders and the supply diagram are not inspectable full-screen | Code: `orders` is kind `info`; the diagram has no interaction box | P2 | Standalone renders of both as documents | interaction_test open/close for each |
| D8 | Hints vanish | Code: hint shows 14 s, duty line 6 s | P2 | The current duty and its latest hint stay on the journal page until done (section 8) | story_test: for every required step the journal lists it from discovery until completion, across save/load |
| D9 | Dev flags ship in release | Code: no debug-build check; export keeps capture scripts | P2 | Gate all `--capture/--autotest/--bot/--load` flags behind a debug feature tag; exclude the scripts from export | exported app ignores the flags |

### 3.2 Ross sequence, door and stairwell

| ID | Issue | Evidence and cause | Pri | Fix |
|---|---|---|---|---|
| R1 | No cough audio | Code: caption only; no file | P1 | Recorded CC0 coughs, positioned and muffled (section 7) |
| R2 | Generator can run during the encounter | Code: nothing in chapter 4 sets generator state | P1 | Explicit story lock (section 6.3) |
| R3 | Ross is a black, static primitive | Code + Capture `g25_t076`: albedo 0.05, lamps behind, 6 mm bob only | P1 | New figure and staging (section 6) |
| R4 | Ross pops in after the line describing him and stays to dawn | Code: `visitor_enter` after narration; never removed | P1 | Enter on cue; blocked positions per beat; exit at dawn on the lie endings |
| R5 | Door opens onto a wall | Code: room shell continues behind a 0.62 m housing, with dado rail and skirting | P1 | Stairwell rebuild (section 5) |
| R6 | "Wooden stick" | Code: oak handrail rises through uncut floor and ends in mid-air (likely the object; capture to confirm) | P2 | Rail on stanchions with a newel, starting on the landing |
| R7 | White floor patch | Three candidates in code (cream-painted shaft tops outside the probe box; uncut slab strips under the stair light; the photo prop). Unconfirmed | P2 | Capture first, then correct material and probe coverage |
| R8 | Door collider stays shut-shaped; leaf has none | Code | P1 | Collider follows the leaf |
| R9 | Photograph is the right concept but small and procedural | Code: 12.5 x 9.5 cm prop; canon text defines it | P2 | Daniel's image via the document pipeline (section 11.1); slide animation |

### 3.3 Cabin

| ID | Issue | Evidence and cause | Pri | Fix |
|---|---|---|---|---|
| C1 | Lamp over the stair door | Code: backplate overlaps the door top by 2.5 cm; light 16 cm from the leaf | P2 | Remove `LMP_wall_4` and `LIGHT_wall_4`; rebalance with lamps 2 and 3 |
| C2 | Left lamp through the supply diagram | Code: backplate cuts the frame's top-right corner (3.8 x 13 cm) | P2 | Move the diagram left (about bearing -67 to -75) |
| C3 | Charger cabinet hangs over the window opening | Code: right 0.30 m stands in front of the west bay; Capture `rq7_t068` | P2 | Move the cabinet about 0.37 m left onto solid wall; re-route its conduit |
| C4 | Door handwheel | Code: diagonal spokes are unrotated boxes forming a brass square; dogs are plain boxes | P2 | Rotated spokes and hub; separate dog levers with pivot bolts; worn paint; wheel and dogs animate |
| C5 | Coat looks unnatural | Capture `rq7d_t064`; 2 mm shell, recalculated normals, back-face culling (plausible causes) | P2 | 4 to 5 mm shell, per-object normals, waxed-cotton normal and roughness maps, fix the non-manifold edge |
| C6 | Telephone | Good base | P3 | Finger wheel with holes, number ring, cradle prongs, coiled cord, gloss/chrome separation, dead-line handset sound |
| C7 | Mug against the pipe's ashtray | Code: overlap 0.9 to 1.9 cm | P2 | Move the mug about 8 cm left; reprint its ring |
| C8 | Decorative compass on the chart | Code: brass dial at desk (0.45, -2.40), no interaction | P2 | Remove it; the working compass on the east sill is untouched |
| C9 | "Sternway G.G." note | It is the "STORNOWAY C.G." radio-check card in the radio bezel | P2 | Lower it clear of the dial; make it a small inspectable document |
| C10 | Binoculars clip the phone base | Code: about 1.2 cm | P2 | Nudge the binoculars 3 cm |
| C11 | Seated body glimpse | Code: frame order (section 4.2) | P1 | Section 4.2 |
| C12 | Callum's clothing | Code + Capture `g3c/preview/sheet_v3` | P1 | Section 4.1 |

### 3.4 Sea, boats, radar

| ID | Issue | Evidence and cause | Pri | Fix |
|---|---|---|---|---|
| M1 | Boats distorted or partly missing | Code: stand-in hull winding inward with back-face culling; world-space textures slide on the hull | P1 | Five Blender vessel models (section 9); fix the fallback winding |
| M2 | Blue patches | Code: shore mask repeats every 520 m; flat underlay at -0.6 m inside the troughs | P1 | Clamp the mask; lower the underlay below the deepest trough |
| M3 | Activity crowded near the light | Code: radar 250 m, spawn 230 m, farthest reef 112 m | P3 | Range switch and outer hazards (section 10) |
| M4 | Wave grid too coarse for the short waves | Code: 3.33 m cells vs 5.3 m and 8 m waves | P2 | Radially denser mesh near the tower |

### 3.5 Other findings (not in the brief)

- **Ending panel mismatch (P1, Code):** "Two men to one wheel" shows in every ending, including when Ross never took the wheel.
- **Music not saved (P2, Code):** loading a chapter 5 or 6 save has no music; continuous play does.
- **Canon conflicts to settle:** Tide Tables are "1953" in dialogue but 1969 to 1971 on the shelf; the radio card says "Radio check 2100" but tonight's check is at 18:30; the Inquiry sits in Stornoway in one text and Inverness in the documents; the Mary Ellen call is 23:57 in data and 23:58 in text. Proposed resolutions are in section 7.5.
- **Licence log gap (P3):** the Daniel-supplied AI images are not listed in `assets/ASSET_LICENSES.md`.

## 16. Document 3 in full: evidence appendix to the issue register

Status: **C** confirmed in code; **P** plausible, needs a capture; **U** unknown until run.

| ID | Location | How to reproduce | Cause, with status | Acceptance test |
|---|---|---|---|---|
| D1 | `g/scripts/ui/dialogue_ui.gd:437-469` | Press Space twice on any line | C: first press completes the typewriter, second advances after 0.5 s | No input changes the shown line (regress R11b rewritten) |
| D2 | `dialogue_ui.gd:410-411`; `g/scripts/story/story_director.gd:950-956`; `g/scripts/fp/game_fp.gd:292-299` | Leave a radio line up; press E on the Tide Tables | C: radio never auto-advances; `play_aside` returns false while `_talking` | Queued aside plays within 6 s of the conversation ending |
| D3 | `g/scripts/ui/style.gd:155-172`; `dialogue_ui.gd:89-93`; e.g. `g/data/story/ch3.dlg:6` (192 chars) | Play Morag's chapter 3 gale warning | C: fit-content label, 606 px column, about 43 characters per line | 3 lines or fewer at four text sizes; pages rejoin to the source text |
| D4 | `dialogue_ui.gd:73-74, 99-102, 472-483` | Any portrait line longer than three lines | C: cream fill then photo at `Rect2(8,10,136,170)`; card stretches with the row | Photo fills the card inside a fixed keyline at all sizes |
| D5 | `g/scripts/fp/fp_ui.gd:122-170`; `blender/build.py:906-926, 966-967` | Enter the radio view at 16:10 | C by projection; capture `g22_t100_focus_radio-say_radio.png` | Projected scope rect and panel rect disjoint at 16:9, 16:10, 720p |
| D6 | `game_fp.gd:292-299`; `g/assets/docs/docs.json` (no entry) | E on the Tide Tables | C: no document id is ever set | Viewer opens in all chapters |
| D7 | `g/scripts/fp/station.gd:93`; `build.py:2196-2205` | E on Keeper's Orders; look at the diagram | C: `orders` is `info`; diagram has no IA box | Both open in the viewer |
| D8 | `g/scripts/story/story_presenter.gd:58, 332-340` | Wait past a hint | C: 14 s timer | Journal lists the step until done |
| D9 | `g/export_presets.cfg:11`; `g/scripts/main_fp.gd:39-66` | Run the exported app with `-- --autotest=10` | C: flags read with no build check | Exported app ignores them |
| R1 | `g/data/story/chapters.json:88`; `story_presenter.gd:438-445`; `g/assets/audio/` | Play the chapter 4 `steps` beat with sound | C: caption only, no file | A cough is heard from the stair; Daniel approves by ear |
| R2 | `chapters.json:75, 85-89`; `g/scripts/core/keeper_sim.gd:196-210`; `station.gd:646-658` | Hold START during the stair sequence | C: nothing blocks it | START never reaches RUNNING in the interval |
| R3 | `g/scripts/fp/visitor_figure.gd:9-62`; `game_fp.gd:241-251`; `station.gd:268-298, 448, 522` | Open the door in chapter 4 | C: albedo 0.05, primitives, lamps behind; captures `g25_t076_cu_door-visitor.png`, `g2b_t066_*` | Section 21 capture set |
| R4 | `g/data/story/ch4.dlg:101-107`; `game_fp.gd:225-226, 388, 416-417` | Open the door; play on to dawn | C: spawned after narration; never freed | Present on cue; blocked per beat; gone at dawn on lie endings |
| R5 | `build.py:174, 713-718, 1635-1732` | Open the door and look in | C: shell ring continues behind a 0.62 m housing | Open-door captures show a stairwell |
| R6 | `build.py:1712` (oak `seg_cyl`, 44 mm) | As R5 | C geometry; P that it is the object seen | Rail starts from a newel on the landing |
| R7 | `build.py:801-817, 1716-1722, 2667-2671`; `g/shaders/room_pbr.gdshader:117-131`; `station.gd:441-452` | As R5, lit and in blackout | U: three candidates | No cream or unlit-white surfaces inside the housing |
| R8 | `build.py:368-375, 1698`; `station.gd:843, 912-923` | Walk at the opened door and at the leaf | C: static closed-position collider; leaf has none | Doorway passable when open; leaf solid |
| R9 | `build.py:2667-2671`; `g/assets/docs/docs.json:39-40`; `blender/documents.py:413-418` | Keep the door shut in chapter 4 | C: 12.5 x 9.5 cm prop appears in place | Slide animation; pickup; viewer shows front and back |
| C1 | `build.py:1694, 2123-2141`; door leaf `build.py:1672-1676` | View `cu_door`; capture `rq7d_t060*face_b170.png` | C: backplate z 2.035 to 2.205 vs leaf top 2.06 | Lamp gone; door area reads at 0.10 to 0.14 mean luminance in `cu_door` |
| C2 | `spec.py:74-77`; `build.py:2196-2205` | Look at the diagram | C: 0.2815 m centre distance, backplate radius 0.085 m | 10 cm clear gap; top-right screw visible |
| C3 | `build.py:1412-1440`; west bay -52.5 to -22.5 degrees | View `cu_battery`; capture `rq7_t068_cu_battery.png` | C: right 0.29 to 0.30 m is in front of the opening | Whole cabinet backed by wall in a top-down render |
| C4 | `build.py:1666-1692` | View `cu_door`; capture `rq7d_t066_cu_door.png` | C: spoke boxes never rotated | Five spokes and hub read in `cu_door` |
| C5 | `blender/coat_cloth.py`; `build.py:2353-2520`; `g/scripts/fp/materials.gd:46` | View `cu_coat`; capture `rq7d_t064_cu_coat.png` | P: 2 mm shell, bucket-wide normal recalculation, culling | No jagged edges in three views |
| C6 | `build.py:2626-2657` | View the desk corner | C: plain geometry | Close-up capture reads as a GPO desk set |
| C7 | `build.py:1210, 1391-1402` | Capture `rq7f_t062_pp_compass.png` | C: centres 7.5 cm apart, radii 4.2 and 5.5 cm | Clear gap of 3 cm or more in a top-down render |
| C8 | `build.py:954-956` | Look at the chart | C: brass dial, no IA box | Dial absent; R15 compass test still passes |
| C9 | `build.py:1306-1307`; `documents.py:600-610` | View `cu_radio`; capture `rq7_t072_cu_radio.png` | C: card overlaps the bezel | Card clear of the dial; opens as a document |
| C10 | `build.py:1353-1371, 2626-2657` | Close view of phone and binoculars | C: 1.2 cm intersection | No intersection in the Blender BVH check |
| C11 | `g/scripts/fp/player.gd:246-265, 302-309`; `g/scripts/fp/player_body.gd:60-110`; `game_fp.gd:109-120` | Stand facing the chair, press E on the radio | C: process order and 0.45 s blend | Frame series shows no body ahead of the camera |
| C12 | `blender/body.py:146-171, 287-310`; `blender/hands.py:33, 139-189, 265-270` | Look down; hold the compass | C: displaced skin, no garment; rigid cuff | Section 4 capture set |
| M1 | `g/scripts/fp/ship_view2.gd:50-136, 186`; `g/shaders/tri_pbr.gdshader` | Binoculars on any vessel | C by winding rule; needs a capture | Every hull closed from all sides at three ranges |
| M2 | `g/scripts/fp/outside.gd:322-356`; `g/shaders/ocean.gdshader:16, 62, 79` | Binoculars toward bearing 000 at about 520 m; storm 1.0 | C if default repeat applies; needs a capture | No tinted patches away from the real island and reefs |
| M3 | `g/scripts/fp/radar.gd:6`; `g/scripts/core/keeper_config.gd` `spawn_radius` 230 | Watch any vessel arrive | C | Section 24 tests |
| M4 | `outside.gd:304-321` | Low view of short waves | C: 3.33 m cells | No faceting in a near-shore capture |
| E1 | `story_director.gd:767-778` | Reach any ending without giving Ross the wheel | C: `p1_wheel` is unconditional | `p1_alone` shown when `ross_wheel` is unset |
| E2 | `game_fp.gd:380-420`; `audio_director.gd:279-283` | Save in chapter 5, quit, continue | C: no audio state saved | Same music state after load as in continuous play |

**Existing captures that serve as "before" evidence** (all in `renders/last_light/`): `g22_t100_focus_radio-say_radio.png`, `g22_cards_crop.png`, `g25_t076_cu_door-visitor.png`, `g2b_t066_*`, `g3c/preview/sheet_v3.png`, `g3c2_t032_body_3p-in_radio.png`, `rq7_t068_cu_battery.png`, `rq7_t072_cu_radio.png`, `rq7d_t060*`, `rq7d_t064_cu_coat.png`, `rq7d_t066_cu_door.png`, `rq7f_t062_pp_compass.png`, `s3b_after_t064_pp_tide_tables-say_grants.png`.

**Captures still to take in Stage 0:** binoculars on a near vessel outside and through the glass; the sea at bearing 000 and at storm 1.0; the door open, lit and in blackout; lamp 0 against the diagram; phone and binoculars close-up; the chart dial; the longest radio line at text 1.0 and 1.5; the radio view at 1920x1080; a 60 fps frame series of sitting down; each ending's title card.
