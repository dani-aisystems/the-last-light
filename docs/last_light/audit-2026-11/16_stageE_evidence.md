# THE LAST LIGHT: Stage E evidence (sea and vessels), part E1: the vessel models, 2026-11-17

**Daniel (2026-11-17, after the checkpoint):** "You determine, then E2." Claude's calls are in DECISIONS Q21: mapping and wiring as proposed, colours kept, textures and `.blend` versions not committed, SY 214 PARTIAL until the in-game check, and E2 on its own branch until Stage M's M4.

Stage E of the audit plan (section 9.1, [05_visual_audio.md](05_visual_audio.md)), **part E1 only**: the vessel models, built, validated, exported and reviewed in Blender. It addresses M1 ("boats distorted or partly missing": stand-in hulls with inward winding and sliding textures). Index: [README](README.md). Plan: `~/.claude/plans/pasted-content-id-0830-start-the-agile-raven.md`. Decision: DECISIONS Q21.

**Not done in E1, on purpose:**
- Nothing is synced into `godot/assets/models/`: the game loads `ship_<kind>.glb` at once, and that would change Stage M's before/after captures.
- No Godot file is touched.
- E2 covers the Godot side: per-ship models, motion, wakes, spray, whitecaps, foam, depth tint and the in-game binocular QA. It waits until Stage M has finished M4 and Daniel says go.

**Daniel (2026-11-17):** build to today's DIMS (Q21).

**Build:**

| Item | Path |
|---|---|
| Generator (new) | `projects/games/last_light/blender/vessels.py` |
| Review renders (new) | `projects/games/last_light/blender/vessel_review.py` |
| `.blend` | `blender/last_light_vessels_v003.blend` (v001 and v002 are earlier passes) |
| Textures (generated) | `blender/textures/vessels/T_Vessel_<Id>_{base,rough,metal,normal,emit,albedo,orm}.png`, 10 MB, packed into the `.blend` and embedded in the GLBs |
| Exports (gitignored) | `exports/last_light/gltf/ship_*_v003.glb`, 1.0 to 1.4 MB each |
| Test (new) | `tests/test_last_light_vessels.py` |
| Renders and logs (gitignored) | `renders/last_light/stageE/` (`sheet_<vessel>.png`, `<vessel>/*.png`, `build.json`, `validation_*`, `reimport_*`, `glb_check_v003.json`) |

## 1. The contract the models fit (`ship_view2.gd`, read only)

- **Placement:** the model is added at the ship node's origin, and the node sits at wave height − 0.4 m. The design waterline is therefore +0.40 m in the model.
- **Axes:** the bow is Godot −Z (Blender +Y); port is −X.
- **Size:** within `DIMS` for the kind the file serves:
  - beam ≤ x;
  - length overall, bowsprit included, ≤ z;
  - rail top ≤ y.
- **Lights:** today the nav lights come from DIMS, not from the model.
- **Material names:** `_swap()` replaces any material whose name `LLMaterials` knows. `get_mat` returns null for an unknown name, so the vessels' `M_Vessel_<Id>` materials are kept.
- **Node names:** no Godot import-hint suffixes.

## 2. The vessels

| Vessel | Design | Export | Tris | Beam / length / rail top (m) | DIMS (kind) | Marks |
|---|---|---|---|---|---|---|
| *Kittiwake* | ring-netter | `ship_fishing` | 4,348 | 4.15 / 13.00 / 2.33 | 4.2 / 13 / 2.4 (fishing) | SY 37, KITTIWAKE |
| *Corrie May* | ring-netter, green, painted house, no radar | `ship_corrie_may` | 4,316 | 4.15 / 13.00 / 2.33 | same (fishing) | BRD 9, CORRIE MAY |
| *Mary Ellen* (the *Catriona* rebuilt) | the ring-netter's lines at 10 m, tarred, older house, bare mast, unlit | `ship_launch` | 4,152 | 3.14 / 10.00 / 1.89 | 3.4 / 10 / 1.9 (launch) | SY 214 (0.46 m figures), MARY ELLEN |
| *Gannet* | gaff schooner, sails furled, passenger deckhouse, dinghy | `ship_schooner` | 4,548 | 4.89 / 19.00 / 2.55 | 5.0 / 19 / 2.6 (schooner) | SY 112; GANNET and STORNOWAY on the counter |
| *Lowestoft Star* | steam drifter, tall funnel, steadying mizzen set, boat on the casing | `ship_lowestoft_star` | 4,352 | 6.12 / 25.00 / 3.35 | none of its own yet (schooner today) | LT 401; name on the quarter and the counter |
| *Iona Star* | coaster: raised forecastle and poop, two tarpaulined hatches, mast and derricks, bridge aft, star funnel, two lifeboats | `ship_steamer` | 5,162 | 7.16 / 30.00 / 4.15 | 7.5 / 30 / 4.2 (steamer) | IONA STAR on the bows; IONA STAR and GLASGOW aft |
| *Hendrika* | the same coaster, grey hull, timber deck cargo with lashings, derricks topped | `ship_hendrika` | 5,378 | 7.16 / 30.00 / 4.15 | same (steamer) | HENDRIKA; HENDRIKA and GRONINGEN aft |

Each GLB holds:
- **mesh:** one mesh object `SM_Vessel_<Id>`;
- **material and textures:** one material `M_Vessel_<Id>`, with these 1024 maps:
  - albedo with the AO folded in at 38 %;
  - ORM, with the baked AO in R so it is exported as glTF occlusion;
  - OpenGL normal;
  - emission for the windows and lenses. The black boat has none.
- **empties:** `NAV_masthead`, `NAV_port`, `NAV_starboard`, `NAV_stern` and `DECK_work`, plus `DECK_aft` on the coasters. Each sits at its modelled lantern: a black body with the lens on the side that shows.

Canon used:
- `character-refs/CANON_INDEX.md`;
- `ross/PROFILE.md`: the *Catriona*, black hull, wheelhouse aft, SY 214 on the bow;
- `SCRIPT_REVISION_2026-11.md` §9: the call signs; *Hendrika* is a Dutch coaster carrying timber;
- `speakers.gd`.

## 3. Kind mapping (proposal, for Daniel)

| File | Serves today (unchanged kinds) | Wired in E2 |
|---|---|---|
| `ship_fishing.glb` (*Kittiwake*) | *Kittiwake*, *Corrie May* | |
| `ship_schooner.glb` (*Gannet*) | *Gannet*, *Lowestoft Star* | |
| `ship_steamer.glb` (*Iona Star*) | *Iona Star*, *Hendrika* | |
| `ship_launch.glb` (the black boat) | the Visitor (`unlit`) | |
| `ship_corrie_may.glb`, `ship_lowestoft_star.glb`, `ship_hendrika.glb` | nothing | by name |

**E2 wiring proposed** (no new kinds, no `chapters.json` or sim change):
- `ship_view2` tries `ship_<slug(name)>.glb` before `ship_<kind>.glb`;
- it places the lights from the model's `NAV_*` / `DECK_*` empties when they exist, with DIMS as the fallback.

The table below shows why the second change matters: today's DIMS positions are far from where these vessels carry their lights.

**Light empties against today's DIMS positions** (model − DIMS, Blender metres x / y / z; +y is forward):

| Vessel | Masthead | Port / starboard | Stern | Deck |
|---|---|---|---|---|
| ring-netters | 0 / +0.13 / 0 | ±1.07 / −3.84 / −0.04 (on the wheelhouse, aft) | 0 / −0.04 / −0.48 | 0 / +2.44 / +0.80 |
| black boat | 0 / +0.03 / −0.10 | ±0.95 / −3.12 / +0.13 | 0 / −0.05 / −0.30 | 0 / +1.79 / +0.55 (all dark) |
| *Gannet* | 0 / +0.03 / 0 | ±0.45 / +0.40 / +0.26 (in the fore shrouds) | 0 / −0.21 / −0.60 | 0 / +0.40 / +0.14 |
| coasters | 0 / −4.25 / −0.70 (on the mast) | ±0.38 / −12.75 / +1.02 (bridge wings) | 0 / −0.42 / −0.55 | 0 / +1.78 / +2.20 |

## 4. Verification

| Check | Result | Evidence |
|---|---|---|
| Closed, consistently wound, outward (generator) | **PASS**, all 7: 0 non-manifold edges, 0 inconsistent edges, 0 inward shells, 0 zero-area faces | `vessels.py --report`; `build.json` |
| Triangle budget 4 to 6k | **PASS**: 4,152 to 5,378 | same |
| Within DIMS | **PASS** for all 6 files that serve a kind. The drifter has no kind of its own (25.0 m). | same |
| UVs | **PASS**: one set, inside 0 to 1, 0 island overlaps outside the uniform "shared" kinds (rope, lenses, rubber, soot) | same |
| Blender mesh | **PASS**: the triangle counts match, bmesh non-manifold 0, one material, one UV layer | `build.json` (`bl_*`) |
| `validate_asset.py --target gltf` | **PASS with 1 WARN** each: `origin_at_base_centre`. Explained: the contract puts the origin 0.4 m below the waterline, not at the keel. | `validation_ship_*_v003.json` |
| Export (`export_asset.py`, gltf) | **PASS**, 7 files | `exports/last_light/gltf/ship_*_v003.glb` |
| Reimport (`reimport_check.py`, fresh Blender) | **PASS**, 7 of 7: loaded, mesh count, triangles, materials, size | `reimport_ship_*_v003.json` |
| GLB as Godot reads it (`vessels.py --check-glb`) | **PASS**, 7 of 7 | `glb_check_v003.json` |
| GLB: vertex normals agree with the winding | 100 % of triangles | same |
| GLB: inward shells (after welding) | 0 | same |
| GLB: material, UVs and textures | 1 material, 1 UV set, textures 1024² | same |
| GLB: axes | bow −Z, port −X | same |
| GLB: node names | clean | same |
| pytest | **PASS**: the whole suite, including the 29 new vessel tests | `tools/py -m pytest -q` |
| Renders: five distinct silhouettes, viewed with Read | **PASS** | `renders/last_light/stageE/sheet_<vessel>.png` |
| Renders: registrations and names | **PASS** at the close views and at 120 m | same |
| Renders: sidelights on the correct sides | **PASS**: red to port, green to starboard | same |
| Renders: the black boat at night | **PASS**: dark, no emission | same |
| SY 214 in the beam at 230 m (7x, 720p) | **PARTIAL** | `mary_ellen/bino_230_beam.png` |
| In-game binocular QA, through the glass and outside | **NOT TESTED** | E2 |
| Motion | **NOT TESTED** | E2 |
| Bench | **NOT TESTED** | E2 |

About the SY 214 row: the figures read clearly as white registration numbers, but they are about 8 px tall. "214" is at the edge of legibility at 230 m and clean at 120 m. The figures are already the largest the 10 m bow can carry inside the launch DIMS (0.46 m, between the boot-top and the strake). E2's game captures at the real resolution decide it.

**Renders** (`vessel_review.py`):
- **Source:** each exported GLB re-imported into an empty scene, waterline at sea level, EEVEE 1280×720.
- **Close views:**
  - three-quarter and side, at dusk and at night;
  - at night the lamps are point lights at the empties.
- **7x views:**
  - FOV: `equipment.gd` `BINO_FOV`, 10° vertical;
  - eye height: 21.65 m (`spec.py` floor 20.0 + eye 1.65);
  - range: 120, 230 and 400 m at dusk, and 230 m at night;
  - fog: fogged copies at 230 and 400 m for a 1 km visibility (σ = 3.912 / V, Stage M's recommended range), mixed toward the horizon colour from a probe render;
  - beam: the black boat also gets a night view with a spot as the light's beam.

**Fixed on viewing (with numbers):**
- **Lanterns:** they rendered as glowing cubes, so each became a black body with a lens 0.8 × 0.72 of the body on the side that shows.
- **Locker box:** a stray 0.5 × 0.2 × 1.0 m box in front of the Kittiwake's wheelhouse was removed.
- **SY 214:** it was 0.36 m high at z 1.12, about 6 px at 230 m. It is now 0.46 m at z 0.87.
- **Black boat's wheelhouse:** it read pale at night; #6C6962 → #575349.
- **Render setup only:** the first dusk was too bright, washing out the fogged views, so the horizon went (0.42, 0.30, 0.26) → (0.16, 0.13, 0.13). The fog colour had been forced at night and left a band, so it now comes from a horizon probe. The sun flared on the sea at the edge of the three-quarter views, so its azimuth went 205° → 115°.

## 5. Notes

- **Reuse:**
  - `scene_utils` (collection, versioned save);
  - `export_asset.export_one` (via `vessels.py --export`, which strips the `.<vid>` suffix Blender needs for unique empty names);
  - `validate_asset.py`, `reimport_check.py`, `contact_sheet.build`.

  `build.py`'s primitives were **not** imported, a deviation from the plan. Its `box()` adds chamfer triangles that can't be budgeted, and it is the room builder other sessions edit. `vessels.py` has small closed primitives of its own.
- **The geometry is plain Python.** Painting, checks and pytest see exactly the mesh and the UV islands Blender gets. The painter places the waterline, boot-top, scupper streaks, plank and plate seams and the lettering by metric coordinates. Fonts are macOS system fonts, as `documents.py` uses: DIN Condensed Bold for registrations, Arial Narrow Bold for names.
- **Depth EXRs:** `vessel_review.py` writes the fog's depth EXRs to `renders/last_light/stageE/<vessel>/depth/` and keeps them. The workspace rules forbid deleting files from bpy code.
- **Generated textures:** `blender/textures/vessels/` (10 MB) is reproducible with `vessels.py --paint` plus the Blender build. Whether to commit it is Daniel's call; the cloth textures were committed in Q19.
- **For Daniel's eye:**
  - the colour schemes: *Kittiwake* navy, *Corrie May* green, black boat tarred, *Gannet* black with a white cove line, drifter black with a buff funnel, *Iona Star* black with red boot-top and a star funnel, *Hendrika* grey;
  - the invented funnel colours of *Iona Star* and *Hendrika*.

---

# Part E2 (branch `stage-e2`, worktree `exports/worktrees/last_light_e2`): the vessels in the game

Daniel, 2026-11-17: "You determine, then E2."

E2 runs on its own branch. Stage M has recorded no milestone yet, so the main tree stays as its baseline expects. The branch merges after Stage M's M4. The ocean-shader items (whitecaps, shore and reef foam, depth tint) wait for Stage M's `ocean.gdshader` work.

## E2a to E2c: what changed

| Item | Change | Where |
|---|---|---|
| Models | The seven v003 GLBs are synced as `godot/assets/models/ship_*.glb`, together with the textures Godot extracts from them (`ship_*_T_Vessel_*`, committed with the GLBs, since the import needs them). | `assets/models/` |
| Lookup | `model_for()` tries `ship_<name>.glb` first (e.g. `ship_corrie_may`), then `ship_<kind>.glb`. If neither exists, the stand-in and DIMS are used. | `ship_view2.gd` |
| Lights | Placed at the model's `NAV_*` / `DECK_*` empties, with each lamp's colour, energy and range as before. The glow sphere on a model is the size of the lens (0.09 m instead of 0.22); a deck lamp on a model gets no sphere. An unlit ship gets no lights, as before. | `ship_view2.gd` `LAMPS`, `_nav` |
| Size | Length and beam come from the model's bounds. They drive the motion, the wake and the spray. | `ship_view2.gd` |
| Motion | Heave, pitch and roll come from five points on the sea at 80 % of length and beam. The sea is the one the GPU draws: the horizontal Gerstner displacement is inverted (two fixed-point steps) before the height is read. Damping uses τ = 0.32·√L (1.0 s at 10 m, 1.75 s at 30 m). Bank into turns is capped at 0.18 rad × min(1, 15/L). | `surface_y`, `motion_targets`, `tick` |
| Stand-in (M1) | The fallback hull is wound outward, so it is no longer culled from outside. | `_hull_mesh` |
| Wake | A ribbon of the stern's track, one sample per 0.25 s, kept 16 s. It is in world space, widens with age, and fades with age and speed. A new `wake.gdshader` displaces it with the ocean's own Gerstner set, so it lies on the drawn sea. It is lit, not unshaded, so it doesn't glow at night. | `ship_view2.gd` `_wake_*`; `shaders/wake.gdshader` |
| Bow spray | 48 GPU particles at the stem. They are driven by how fast the bow drops into a sea, times the storm and the speed; there is none on the spawn frame and none from a sinking ship. | `ship_view2.gd` `_make_spray`, `_spray_tick` |
| Test | New file (`regress_test.gd` is Stage M's). | `tests/ship_view_test.gd` |

## Verification (headless, `taskpolicy -b`, in the worktree)

| Check | Result |
|---|---|
| `ship_view_test` | **PASS**, 75 checks:<br>• every name and kind loads the right file;<br>• one vessel mesh, its material kept;<br>• 5 lights (6 on the coasters), 0 on the Visitor;<br>• red to port, green to starboard, the port light at its empty;<br>• within DIMS;<br>• `surface_y` within **1.4 cm** of the GPU surface (reading the height at the rest point was up to 42 cm off);<br>• motion SD in a full storm, pitch / roll: launch 3.35° / 3.30°, coaster 1.67° / 2.15°;<br>• stand-in normals out 309 / 309;<br>• the wake's newest sample 0.5 m from the stern, 37 samples;<br>• spray only under way, never on spawn or when sinking. |
| `regress_test` | **PASS** 449 / 449 (4 headless skips), the same as Stage P |
| `story`, `opening`, `run_tests`, `interaction`, `qa_sweep`, `g5`, `save_compat` | **PASS**: 0 failed; 31 / 95 / 164 / 7,703 / 50 / 305 checks |
| `sim_v2`, seeds 1 to 5 | **PASS**, no gate failures |
| In-game look (Daniel's OK, 2026-11-17) | **PASS** for the four kind files. Binoculars from `pp_radio`, facing north at 120 / 230 / 400 m (pitch −10 / −5 / −3°), dawn and night, with the glass and with `--noglass`: 8 windowed runs, 48 frames, viewed. Every hull is closed and upright on the water; no inward faces, no sliding texture (M1 fixed on screen). Sidelights show on the correct side (the coaster heading west shows red); windows glow at night. Sheets: `exports/worktrees/last_light_e2/renders/last_light/sheet_e2_<kind>_<glass\|noglass>.png`. The capture ship `Capture launch` is spawned lit, so its lamps show; the story's Visitor is spawned unlit (0 lights, covered by `ship_view_test`). |
| In-game look: the three name variants, wake and spray | **NOT TESTED in a window**: they need a named, moving capture ship in `capture_fp.gd` (Stage M's file), which comes after the merge. Headless coverage only. |
| Bench | **NOT TESTED**: deferred. Load average was 3.5 to 4.6 with other sessions running; Stage P showed that a loaded bench is noise. Run on a quiet Mac. |

**Found on the way (not E2's):** Stage P's extracted body and hands textures (`assets/models/body_T_LL_*`, `hands_T_LL_*`, 24 files with their `.import`) were never committed. A clean checkout cannot load `body.glb` or `hands.glb`, and regress fails 8 checks there. They were copied into the worktree only; committing them in main is Daniel's call.
