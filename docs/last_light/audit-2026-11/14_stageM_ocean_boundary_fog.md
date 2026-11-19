# THE LAST LIGHT: Stage M, Ocean Boundary Concealment & Atmospheric Fog

**Status: Approved 2026-11-17 — in progress (M0)** (opened 2026-11-16 from Daniel's brief "Ocean boundaries & cinematic fog system"; decisions in DECISIONS Q22 and at the end of section J).

Stage letter M (maritime boundary and mist); "O" was avoided because it reads as Stage 0. Index: [README](README.md). Related: [05_visual_audio.md](05_visual_audio.md) §9.2 (ocean), [06_gameplay.md](06_gameplay.md) §10 (radar, larger sea), [07_roadmap.md](07_roadmap.md) (stages E and F).

Paths are relative to `projects/games/last_light/godot/` unless they start with `docs/`, `renders/` or `tools/`.

Nothing in the game has been changed for this stage. This document, the ROADMAP row and the README line are the only edits.

---

## A. Current-state assessment

### A.1 How the sea is drawn today (`scripts/fp/outside.gd`)

| Layer | What it is | Where it ends |
|---|---|---|
| Wave ocean | One `PlaneMesh`, 1100 × 1100 m, 330 × 330 cells (3.33 m), centred on the tower. `shaders/ocean.gdshader`: 6 Gerstner waves (5.3 to 60 m), two scrolling detail normal maps, crest and shore foam, a fresnel emission term. No shadows. | **A square.** Its edge is 550 m away on the cardinal bearings and 778 m on the diagonals. |
| Far skirt | One flat 6000 × 6000 m `PlaneMesh` at y −0.6 with a plain `StandardMaterial3D` (albedo = the deep-water colour, roughness 0.2). No waves, no normal detail, different specular. | 3000 m, but see the far plane. |
| Camera far plane | `player.gd:81` `camera.far = 1200.0` (the binoculars use the same camera). Captures and the cinematic camera use 2000 m. | **1200 m in play.** Beyond it the sky shader is drawn, including below the true horizon. |
| Depth fog | Exponential, density `0.0025 + 0.004·storm`, × (1 − 0.6·dawn); colour (0.05, 0.065, 0.085); `fog_sky_affect` 0.6, uniform over the whole dome. | — |
| Height fog | `fog_height` 30 m, `fog_height_density` 0.02. In Godot's shader (checked in the 4.7.2 binary) this is `1 − exp((y − 30)·0.02)`, combined with `max()`. It does **not** depend on distance. | Every sea-level pixel gets at least a **45 % veil**, 20 m away or 1000 m away. |
| Volumetric fog | Global, length 180 m, density `0.006 → 0.016` with storm (× 0.3 for the title's attract shot), albedo 0.7. The beam's SpotLight scatters in it (energy 5). **Off on Low** (`Settings.q_volumetric()`). | Froxel volume stops at 180 m. |
| Sky | `shaders/sky.gdshader`: a two-colour gradient, two scrolling cloud layers, lightning through the cloud bellies, a dawn blend. Below the horizon it darkens only by `-d.y·6`, so it is still sky-coloured 1° below. | — |
| Lightning bolts | `bolt.gdshader`, unshaded, additive, **fog disabled** on purpose, struck about 650 m out, foot 1.5 m below y 0 (comment: "just under the far skirt"). | — |

Fog density, as visibility (the distance at which contrast falls to 2 %, V = 3.912 / density) and as the depth-fog transmittance T at three distances. Depth fog only, before the height-fog veil and the volumetric fog:

| Weather (story values) | Density | V | T at 230 m (spawn) | T at 550 m (wave edge) | T at 1200 m (far plane) |
|---|---|---|---|---|---|
| ch1 start, storm 0.12 | 0.0030 | 1.3 km | 0.50 | 0.19 | 0.028 |
| ch3, storm 0.55 | 0.0047 | 0.83 km | 0.34 | 0.075 | 0.004 |
| ch6, storm 1.0 | 0.0065 | 0.60 km | 0.22 | 0.028 | 0.0004 |
| ch6 dawn, storm 0.25, dawn 1 | 0.0014 | 2.8 km | 0.72 | 0.46 | **0.19** |

The density is already about right for a night gale (0.6 to 1.3 km visibility). What gives the world away is the geometry and the colours, not too little fog.

### A.2 Where the limit shows (Stage 0 captures, viewed again 2026-11-16)

| Capture | What is seen |
|---|---|
| `renders/last_light/a0b_t096_ext_far-dawn.png` | A ruler-straight horizon; under it a flat, featureless band (the skirt) above the wave field; the flat underlay patches (issue M2) all over the near sea. |
| `a0s_t096_ext_far.png` (night) | The same: the horizon is the sharpest line in the frame, a near-black band against a grey sky. |
| `a0b_t096_pp_radio-binoculars-face_north-pitch_m3-dawn.png` | Through the binoculars: a plain band about 145 px tall between the wave field and the sky, with a pale seam where the wave mesh stops (about 550 m). The band's height matches the gap between the 550 m edge and the 1200 m far-plane clip at 10° FOV, so the "horizon" seen in play is the **far-plane clip, about 1.2° below the true horizon, with sky drawn in the gap**. |
| `a0s_t098_…-storm_full.png` | At full storm the far sea is one flat dark-blue field ending in a hard line against a lighter sky. |
| `a0s_t094_…-ship_schooner_230.png` | A schooner at 230 m (the spawn radius) reads crisply: hull, masts and lights. A ship created there appears in view. |

**Measured** (row-mean luminance, 8-bit, across an object-free strip; script in the session scratchpad, to be committed as `blender/measure_horizon.py` in M0). The largest step between two adjacent rows in the horizon band:

| Capture | Step at the horizon | Largest other step in the band |
|---|---|---|
| ext_far, dawn | **40.1** (149 → 109) | 4.7 |
| ext_far, night | **49.1** (70 → 20) | 7.8 |
| binoculars, dawn | **26.7** (133 → 106) | 3.6 (the 550 m seam) |
| binoculars, full storm | **28.0** (75 → 47) | 10.7 (same edge, second row) |

### A.3 Root causes

1. **R1, the far-plane clip.** The sea ends at 1200 m in play, 2000 m in captures, and the sky below the horizon is sky-coloured, so the end of the world is a line.
2. **R2, two surfaces with different shading.** The flat skirt has no waves, no detail normals and a different specular. It shows as a band, and as the M2 patches where it pokes through wave troughs.
3. **R3, a square sea.** The seam distance swings from 550 to 778 m with bearing.
4. **R4, mismatched convergence colours.** Fog, sky and volumetric fog each pull distant pixels toward a different colour (fog_light_color; the sky at 60 % fog; the volumetric in-scatter at 40 %). Distant sea and the sky at the horizon never meet. A lightning flash brightens the sky but not the fog colour, so the seam flashes too.
5. **R5, a flat veil.** The height fog veils near and far water alike, so the sea has no depth gradient (the brief's "fog should create depth rather than flatten").
6. **R6, ships pop.** Ships are created at 230 m, where 22 to 72 % of their contrast survives. A ship that is SAVED counts a 10 s `_fade` that never changes her alpha, then disappears in one frame (`ship_view2.gd`, `visible = _fade < 1.0`). A ship that "stood out to sea" is SAVED at 310 m and pops the same way.

---

## B. Design objective

From any window, from the binoculars, from the title camera and from every capture viewpoint:

1. The near sea (0 to about 200 m) keeps full wave, foam and reflection detail, with no haze veil on it.
2. The middle sea (200 to 800 m) keeps the long swells, losing contrast steadily with distance.
3. The far sea fades into a dark, desaturated murk that is the same colour as the sky just above the horizon, so the horizon is a soft band, not a line.
4. Above the horizon, a low fog bank: its top edge uneven, slowly changing with the wind, darkest at the sea, thinning upward into the cloud deck.
5. No visible end to the water at any bearing, in any weather, with lightning, at dawn, on Low, through the binoculars.
6. The lighthouse stays the anchor. The beam scatters in the near air as it does now, and optionally lights the far murk as it sweeps (the *loom* of the light, the glow a keeper sees in haze beyond the beam's reach).
7. Ships come out of the murk as lights first, then a faint shape, then a hull. Leaving, they go back the same way, never in one frame.
8. Fog is optical only. The radar, the sim, rescue timings and saves are untouched.

---

## C. Technical alternatives

**A — Distance fog only.** Keep the square sea and the skirt; tune the depth fog (exponential or Godot 4.3+ depth mode) and fog colour.
To hide a 550 m edge in every weather, T(550 m) must be at or below about 1 %. That needs density ≥ 0.0084 (V ≤ 470 m) **at dawn too**. It would black out the ending's dawn, halve the visibility of the 230 m traffic, and still leave the 1200 m clip and the band. It does nothing for R3, R4 or R6.

**B — Volumetric fog bank.** Raise `volumetric_fog_length` to about 700 m and ring the sea with `FogVolume`s (noise density textures, height falloff, wind scroll), or use soft geometry cards or a curtain mesh.
- Godot's volumetric fog is a froxel grid (64 depth slices by default) over its length. Stretching it from 180 m to 700 m spreads those slices over four times the depth, which coarsens the beam's near-field scattering, the effect it exists for today.
- Fog volumes beyond the length are not drawn.
- It is off on Low, so Low players would see the edge.
- The froxels follow the camera frustum, so the 10° binocular view samples it seven times finer than the 72° view. A bank would look different through the glasses.
- Cards and curtains have silhouettes, sort against the water, and show their flatness in parallax through the binoculars.

**C — Hybrid: one continuous sea, fog as the authority, the bank painted at infinity.**
- One radial ocean mesh to about 6 km, dense near the tower and coarser outward, with the wave set fading out by distance. The skirt goes.
- A far plane beyond the rim.
- One atmosphere function that sets the depth-fog density and a single horizon colour for fog, sky and volumetric fog.
- Distance-free height fog removed; aerial-perspective fog, so distant water takes the sky's own colour.
- The fog bank painted into the sky shader as a low horizon band, uneven and wind-driven. It sits at infinity, so it has no silhouette and no parallax to give away, and it costs a few instructions per sky pixel.
- Volumetric fog kept for what it does well: the beam and the near air.

| Criterion | A: distance fog | B: volumetric bank | C: hybrid |
|---|---|---|---|
| Visual realism | Low: needs fog so thick the scene dies, and the clip and band stay | Medium: organic up close, but cards or a thin froxel bank show at range | High: continuous water, physically shaped fade, soft horizon |
| Atmospheric quality | Flat | Best near the camera | Good everywhere; the beam's near scatter unchanged; optional scud for near motion |
| Performance | Free | Costly: longer froxel volume, noise volumes, High-only | Neutral or cheaper: radial mesh at similar or fewer triangles, sky band and aerial perspective nearly free |
| Godot compatibility | Full | Volumetric only on Forward+, off on Low | Full: built-in fog features plus our own shaders; works on Low |
| Implementation complexity | Lowest | High, with a lot of tuning | Medium: mesh builder, wave distance fade (CPU and GPU), sky band, atmosphere function |
| Interaction with waves | None; keeps M2 | None; keeps M2 | Fixes M2 and M4; far waves fade, so no faceting through the binoculars |
| Radar and boats | Unchanged; ships still pop | Unchanged; ships still pop | Unchanged sim and radar; explicit fades for vessels |
| Lighthouse visibility | Thick fog dims the tower in exterior shots | Bank can swallow the beam | Beam unchanged; optional loom on the bank |
| Storm consistency | One knob | Many knobs | One visibility figure per weather, driving all layers |
| Potential artifacts | Clip line, band | Froxel banding, binocular mismatch, card edges | Seam if the colours disagree (measured, see H); radiance-map lag on lightning (see I) |
| Maintainability | Simple | Fragile | One atmosphere function, one mesh builder |

---

## D. Recommended solution: C, the hybrid

It is the only option that fixes all six causes, it works on every quality preset (the concealment uses no volumetrics), and it is likely to cost less than today's square mesh. A and B each survive as parts of C: A's exponential fog is the authority on visibility, and B's volumetric fog stays for the beam and, optionally, for drifting near-field scud on High.

### D.1 How the fog blends with the sea

- **One surface.** The sea is one mesh and one material from the tower to the rim. There is no second surface to meet, so there is no seam to hide.
- **Detail fades by itself.** Each Gerstner wave fades out with distance from the tower once the mesh cells grow too coarse to carry it, measured from the tower so the CPU and GPU agree. The 5.3 m chop goes first and the 60 m swell last (about 900 m). By the time displacement is gone, fog transmittance is low. Detail normal maps carry the texture further and lose contrast with distance, against shimmer.
- **The fog decides visibility.** Exponential depth fog (density from the atmosphere function, close to today's values) with **aerial perspective**: the fog takes the sky's colour along the view ray, so the farthest water converges to exactly the sky colour at the horizon, lightning included.
- **No flat veil.** The height fog is removed, or given a real falloff measured against captures, so the water close to the tower is clear and haze grows with distance.
- **The horizon is a band.** The sky shader's lowest few degrees become the fog bank: cloud contrast fades into the murk colour, with low-frequency noise breaking the top edge into uneven, slowly drifting heights. Below the horizon the sky is filled with the same murk, so even a clipped pixel reads as fogged sea.
- **The geometry ends where nothing can see it.** Rim at about 6 km; far plane at about 6.5 km (Godot 4.3+ uses reverse-Z depth, so near 0.03 m with far 6.5 km keeps room precision; verified in QA). At the clearest weather (dawn, V 2.8 km) T(6 km) ≈ 0.02 %.

### D.2 Vessels and the binoculars

- **Coming in:** a vessel's view fades in over about 3 s after spawning (instance transparency on the hull; navigation-light energy ramped). Beyond the volumetric fog's 180 m, the nav lights get a small soft halo attenuated by the same fog function, so lights read first and the hull follows as fog thins. Unlit ships (the visitor) come out of the dark as shapes only, as now.
- **Going out:** SAVED ships and ships that stood out to sea fade over the existing 10 s `_fade`, which today is counted but never shown. Ships wrecked keep the sinking animation.
- **Spawning:** today's spawns at 230 m are inside the visible range in every weather, so the fade-in is required now. When Stage F moves fast vessels out to 500 to 1000 m, the fog hides spawns by itself; the fade stays as the safety net.
- **Binoculars:** depth fog, aerial perspective and the sky band are per-pixel and do not depend on FOV, so the binoculars and the naked eye agree by construction. The volumetric part does depend on the frustum, but it only reaches 180 m. QA compares both at the same bearing. The far rings' coarse cells carry no displacement, so the 7× view cannot show facets.

### D.3 Radar and the sim

No change. `KeeperSim`, `FleetShip`, `radar.gd`, `keeper_config.gd` and the seeded outcomes are not touched; a regress check proves the outside view never writes to the sim. The situation where a ship is on the scope but lost in the murk already happens and becomes clearer. Making it a deliberate moment (a hail answered before the ship can be seen) is an idea for Stage C or F, **not part of this stage**.

### D.4 Lighthouse and weather

- The SpotLight's volumetric scatter and `beam.gdshader` stay as approved.
- **The loom (optional, for Daniel's decision):** the sky band brightens faintly along the beam's current bearing, peaking where the beam meets the bank, so the sweep is seen on the horizon murk. One uniform (beam bearing and level) plus a few instructions. Capped so the tower stays the brightest thing in the frame.
- Rain is unchanged. Visibility follows `storm`; an optional slow squall modulation (±15 % density over 20 to 60 s) is in the optional milestone, visual only.
- Lightning lights the murk consistently through aerial perspective. Bolts stay unfogged, and their foot must stay hidden under the sea surface at about 650 m (at that range the waves are partly faded, so the foot depth is rechecked).

### D.5 Three boundaries (brief section 7)

| Boundary | Today | After Stage M | After Stage F |
|---|---|---|---|
| Visible rendered sea | 1100 m square + flat skirt, clipped at 1200 m | Radial, about 6 km, far plane about 6.5 km | Same |
| Navigable sea / sim edge | Spawns at 230 m; "stood out to sea" at 310 m | Unchanged | Far spawns to about 1000 m; new world-edge setting (06 §10.3) |
| Radar | 250 m | Unchanged | 250 / 500 / 1000 m switch |

Rules this stage sets for Stage F:
- the rendered sea extends at least 4 × the clearest-weather fog distance where T falls to 1 %, beyond the world edge;
- any despawn inside that distance goes through the fade;
- the shore-foam field (`field_rect` ±260 m) must grow to cover the outer hazards (Stage F's work), with the same fade-by-distance applied to their foam.

---

## E. Technical implementation plan

Each milestone ends with suites, captures viewed, and a short checkpoint. Nothing in Blender, no `.dlg`, no saves, no sim.

| Milestone | Work | Files |
|---|---|---|
| **M0 Baseline** | Commit `blender/measure_horizon.py` (row-step and band-gradient metrics on a named strip). Before set: every view in section H. Bench Medium, High and Low, adding a binocular bench shot. Only when the Mac is free and after the other session's performance bisect; Daniel's OK, foreground `tools/godot --audio-driver Dummy`. Read the bisect's `--noocean` and `--novolfog` figures. | `blender/measure_horizon.py`, `scripts/capture_fp.gd` (bench shot only) |
| **M1 One sea** | Radial ocean `ArrayMesh` builder (segments and ring growth per quality preset; inner disc round the island). Per-wave distance fade in `ocean.gdshader` and in `OceanWaves.height_at/normal_at` from one shared table. Skirt removed (fixes M2), mesh made radial and denser near the tower (fixes M4), far planes raised (`player.gd`, `game_fp.gd` cine cam, `capture_fp.gd`). Bolt foot rechecked. Regress: CPU height equals GPU displacement at 0, 100, 300, 800 m and at the rim. | `scripts/fp/outside.gd` `_ocean()`, `scripts/fp/ocean_waves.gd`, `shaders/ocean.gdshader`, `scripts/fp/player.gd`, `tests/regress_test.gd` |
| **M2 One atmosphere** | New `scripts/fp/atmosphere.gd` (static): `visibility_m(storm, dawn, dusk, attract)`, `fog_density()`, `horizon_color()`. Applied in `_process_body`. Aerial perspective on; height fog removed (or a measured falloff); volumetric sky affect and albedo reconciled to the horizon colour by measurement. Sky shader: horizon band with noise edge and wind drift; below-horizon murk fill; flash consistency. | new `scripts/fp/atmosphere.gd`, `outside.gd`, `shaders/sky.gdshader` |
| **M3 Light in the murk** | The loom (if approved): beam bearing and level into the sky band. Spot range unchanged. | `shaders/sky.gdshader`, `outside.gd` |
| **M4 Vessels in fog** | Fade-in after spawn; real fade-out for SAVED and stood-out ships; nav-light halos beyond 180 m from the atmosphere function. Stage E's new models inherit this. | `scripts/fp/ship_view2.gd`, `tests/regress_test.gd` |
| **M5 Optional, High only, kept only if it earns its milliseconds** | Drifting near-field scud (2 to 4 `FogVolume`s within 30 to 170 m, noise density, wind scroll); squall modulation. | `outside.gd`, `settings.gd` |
| **M6 QA and checkpoint** | After set; metrics; bench; suites; the four-part checkpoint for Daniel. | this file |

A user argument `--sea=legacy` keeps the old path for A/B captures until Daniel approves. Removing the legacy code afterwards is a separate ask.

---

## F. Dependencies

| Stage | Interaction | Proposal |
|---|---|---|
| **E, sea and vessels** | Stage E listed M2, M4 and "horizon blend into the fog" (05 §9.2), plus vessel models and motion. | Stage M takes M2, M4 and the horizon blend and runs **before** E. E keeps the models, wakes, whitecaps, shore and reef foam and depth tint, and inherits M4's fades. *Daniel's call.* |
| **F, radar, larger sea, fuel run** | World edge, far spawns, outer hazards at 300 to 800 m, far range 750 or 1000 m (06 §10.3: "the final figure is set from captures"). | M's captures at 400, 750 and 1000 m become the evidence for that figure. F follows the D.5 rules. Fog never changes radar contacts. |
| **Lighthouse beam (G6d, R2)** | Beam cone, spot volumetric energy, title beam mask: all approved by Daniel. | Untouched; the loom is additive and optional. Title captures before and after; any visible change to the approved title goes to Daniel. |
| **G5 weather** | Lightning flash, bolts, rain. | Flash routed through aerial perspective; bolts stay unfogged. |
| **Performance bisect (running in another session today)** | Shares the bench harness and the Mac. | M0 waits for it and reuses its figures. |
| **Stage S (another session)** | `outside.gd` `EXTERIOR_ONLY` and `station.gd` lower-level layer. | M edits `outside.gd` only in `_environment`, `_ocean` and `_process_body`; the layer mask stays. Coordinate before touching the file. |

---

## G. Performance

**Baseline (indicative, not this session's measurement).** The other session's bisect base run, 2026-11-16 12:23, Medium, `--novsync`, window not focused (`pb_base_*`), median / p95 in ms: desk 18.4 / 19.0, window 18.6 / 19.6, generator 17.3 / 18.4. Draw calls up to 1464, primitives up to 2.5 M, VRAM 1.19 GB. Its `--noocean` and `--novolfog` runs had not finished when this was written. M0 records a clean, focused baseline with a binocular shot.

**Expected costs:**

| Change | Expected | How it scales |
|---|---|---|
| Radial mesh in place of the 1100 m grid (today 218k triangles, 6 Gerstner waves per vertex) | About equal or cheaper: 256 / 384 / 512 segments give about 0.1 / 0.24 / 0.42 M triangles out to 6 km | Segments and ring growth per preset |
| Per-wave distance fade | A few ALU per vertex; fewer waves evaluated far out | — |
| Aerial-perspective fog | Samples the existing 64 px radiance map; negligible | Sky radiance update rate is checked (I.2) |
| Sky horizon band and loom | A few instructions per sky pixel | Off on Low if it ever shows up in a bench |
| Vessel fades and halos | Instance transparency for 3 s; up to 5 small billboards per ship | — |
| Far plane 1.2 → 6.5 km | Nothing else is out there to draw | — |
| M5 scud volumes | The only real cost | High only; dropped if over the limit |

**Acceptance targets:**
- Medium: median ≤ M0 baseline + 2 % at every bench shot (the goal is ≤ baseline), p95 ≤ baseline + 5 %.
- High: ≤ 25 ms median.
- Low: no worse.
- VRAM ≤ 1.4 GB.
- The audit's limit of +5 % median per stage is the hard ceiling.

---

## H. Acceptance criteria

**Visual QA set.** The same set is used for before and after. Views:
- `ext_far` at night, `storm_full` and `dawn`;
- `pp_window` turned with `face_b000`, `face_b090`, `face_b180` and `face_b270` (one cardinal bearing to each side, plus one at a diagonal, `face_b045`, where the old square reached 778 m);
- binoculars at `face_north` with `pitch_m1` and `pitch_m3`, at storm 0.12, 0.55, 1.0 and dawn;
- `ship_<kind>_<range>` at 120, 230, 400, 750 and 1000 m;
- a new spawn and departure frame series (capture-only state);
- a forced lightning frame;
- `cu_radar`;
- the title menu.

PNGs viewed with Read.

| # | Check | Objective test | Today |
|---|---|---|---|
| H1 | No horizon line | `measure_horizon.py`: largest adjacent-row step in the band from +3° to −3° about the horizon ≤ **4/255** in every QA view (lightning frame ≤ 6) | 26.7 to 49.1 |
| H2 | No map edge | No step > 4/255 anywhere from the tower out to the horizon at all eight bearings; the rim distance × fog density gives T ≤ 0.1 % at dawn (computed and logged) | Clip and band at every bearing |
| H3 | Depth, not a veil | The row-mean contrast of the sea surface (standard deviation of luminance in 1° strips) falls steadily with distance; near sea (≤ 150 m) keeps ≥ 80 % of its no-fog contrast | 45 % floor veil |
| H4 | Not a wall | The bank's top edge varies by at least 0.5° across 90° of bearing and moves over 60 s (two frames 30 s apart differ); judged by Claude and by Daniel | No bank |
| H5 | Vessels | In the spawn and departure series, a vessel's region changes luminance by ≤ 15 % of its final value per frame at 60 fps, with no frame where it appears or vanishes; lights visible before the hull on approach | Pops at 230 m and on SAVED |
| H6 | Binoculars agree | The same bearing with and without the binoculars: horizon-band row means within 3/255 | Not measured |
| H7 | Waves consistent | The regress CPU-and-GPU height check passes; no facets or shimmer in a binocular frame series at 400 to 800 m; M2 patches gone | M2 visible |
| H8 | Beam | Beam captures match the approved look within the beam cone; the loom (if approved) is fainter than the lantern | — |
| H9 | Gameplay untouched | All suites green, including `sim_v2` seeds 1 to 5 with identical outcomes, `story_test`, `regress_test`, `opening_test`, `run_tests`, `interaction_test`, `qa_sweep_test`, `save_compat_test`, pytest | — |
| H10 | Performance | Section G targets | — |

The stage is marked complete only after the after-set has been viewed and Daniel approves it.

---

## I. Risks and rollback

**I.1 Rollback.**
- Every change is in Godot scripts and shaders.
- No save-format, sim, story or Blender asset changes.
- `--sea=legacy` restores the old sea, fog and far plane for A/B captures.
- Each milestone is its own local commit (never pushed), so `git revert` of one milestone is clean.

**I.2 Risks.**

| Risk | Mitigation |
|---|---|
| Volumetric fog (applied after depth fog) pulls distant water off the sky colour, so a seam survives on Medium and High but not on Low | Measured with H1 on all three presets; reconciled by volumetric sky affect and albedo, or by a horizon-colour term in the ocean shader as a fallback |
| The sky radiance map may not refresh every frame, so the fog lags a lightning flash | Check the sky process mode in M2; fallback as above |
| Reverse-Z precision at a 6.5 km far plane with a 0.03 m near plane | Interior close-up captures (`cu_*`) before and after; z-fighting check |
| The CPU and GPU wave fade drift apart and ships float or sink | One shared table, and the regress height check (H7) |
| The bolt foot appears above the faded far waves | Rechecked in M1 with a forced bolt capture |
| The approved title look changes | Title before and after; anything visible goes to Daniel |
| Another session is editing `outside.gd` (Stage S) and the bench harness (bisect) | Edits limited to three functions; start only after their commits land |
| Ship fades show sorting artifacts while transparent | Fade lasts 3 s against a dark sea; capture series; fallback to a dithered fade |

---

## J. Progress log

| Date | Entry |
|---|---|
| 2026-11-16 | Research and plan written. Read: `outside.gd`, `ocean.gdshader`, `ocean_waves.gd`, `sky.gdshader`, `beam.gdshader`, `bolt.gdshader`, `ship_view2.gd`, `radar.gd`, `equipment.gd`, `settings.gd`, `player.gd`, `keeper_sim.gd`, `keeper_config.gd`, `chapters.json` storm values. Godot 4.7.2 binary checked for `fog_aerial_perspective`, depth fog, `FogMaterial` density textures and the height-fog formula. Stage 0 captures re-viewed and measured (A.2). No game files changed; no Godot run (another session's performance bisect had the Mac). **Awaiting Daniel's approval and decisions (below).** |
| 2026-11-17 | **Daniel approved Stage M**: M0 to M6 as planned, before the rest of Stage E (decision 1). The first implementation session ran out of context before leaving anything: no tool, no captures, no game file touched. |
| 2026-11-18 | Resumed at M0. Decisions asked (DECISIONS Q22): 2 keep today's density; 3 build the loom, judge on captures; 5 vessel fades in M4; 6 paired bench at M6 (`--sea=legacy` against the new sea), godot_bg capture batches OK. 4 (scud) is asked at M5. Load 4.7 to 10 with a Stage R session running, so no bench. |
| 2026-11-18 | **M0 done** (results in J.1 below). New `blender/measure_horizon.py` (+ `tests/test_measure_horizon.py`, 10 tests); capture additions; the before-set (`m0h_*`, `m0b_*`, `m0c_*`, `m0s4_*`, sheets in `renders/last_light/stageM/m0_sheet_*.png`, all viewed); the suite baseline (all green). |
| 2026-11-19 | **M5 built, judged on captures, dropped (Daniel; J.6).** Decision 4 asked: "try it and measure". Built, captured on High against `--scud=off`, shown, and removed on Daniel's call. |
| 2026-11-19 | **M6 after-set, metrics and suites done (J.7); the paired bench waits for Daniel.** Stage E2 has not merged, so the after-set is main at `f24439b` (M4 plus Stage R, which does not touch the sea or fog). |

### J.1 M0 baseline (2026-11-18)

**Tooling.**
- `blender/measure_horizon.py`, subcommands `band` (H1), `contrast` (H3), `compare` (H6) and `series` (H5, with `--ref` or `--dark-pct`).
  - It finds the horizon row from the camera of each shot, which `capture_fp.gd` now writes to `<capture>_cams.json`.
  - Checked against section A.2's hand measurements: `a0b_t096_ext_far-dawn` 39.5 (A.2: 40.1), `a0s_t096_ext_far` 49.2 (49.1).
- `capture_fp.gd`, all capture-only:
  - `storm_<percent>`;
  - `far_ships` (capture ships beyond 310 m are not resolved "stood out to sea" at once, which would make M4's fade-out show in the shot);
  - `ext_b<deg>` (outward from 7 m at eye height, 2° down: all eight bearings for H2);
  - `shipseq` (a still 10° camera 6 m out on bearing 0, lamp off for the series; an empty frame, then 4 s after a spawn at 230 m, then 11 s after forcing SAVED, a frame per 1/6 s on the outside clock);
  - the `fp_bino` bench shot.
- **Correction to section H:** the watch room's windows cover only bearings −51° to +51° (bays −36, 0, 36 ± 15°). So H2 uses `ext_b000` to `ext_b315`, and the window views are `face_b000`, `face_b045` and `face_b315`.

**H1 and H2 (largest adjacent-row step, ±3° about the horizon; `m0h_*`, HUD hidden, no glass or rain):**

| View | storm 0.12 | 0.55 | 1.0 | dawn (0.25) | Where the step is |
|---|---|---|---|---|---|
| `ext_far` | 51.4 | 46.1 | 24.5 | 41.0 | −0.86°, the capture camera's 2000 m clip seen from 30 m |
| `ext_b000` … `ext_b315` (8 bearings) | 45.5 to 51.9 | 40.6 (b045) | 33.7 (b045) | 36.4 (b045) | −0.63°: the 2000 m clip from 21.65 m |
| window, naked eye, `pitch_m1` | 28.6 (b000), 24.8 (b045), 15.3 (b315) | 26.1 | 20.4 | 24.6 | −1.07°: the player camera's 1200 m clip |
| binoculars `pitch_m1` / `pitch_m3` | 20.9 / 18.6; b045 34.6 | 20.3 / 10.4 | 14.7 / 10.0 | 18.7 / 15.1 | −1.06° |
| `ext_far!flash` | 7.5 (the flash washes the frame) | | | | |

- Every step sits exactly at the far-plane clip (R1). The target is ≤ 4.
- Seen in the captures:
  - the M2 underlay patches all over the near sea at every bearing;
  - the dark band under the line;
  - at dawn, the wave mesh's pale 550 m seam through the binoculars;
  - ships at 750 and 1000 m standing as crisp black silhouettes on the clip against a lighter sky (`m0_sheet_ships_*.png`), because at T(1000 m) ≈ 5 % a ship takes the fog colour, which does not match the sky (R4).

**H5 (vessels; `m0s4`, still camera, lamp off, the darkest 2 % against the median of a window round the hull):**
- **Arrival:** the hull is complete in the first frame after the spawn: −10.3 → −22.4, about 108 % of her settled contrast (≈ 11/255) in one step.
- **Departure:** she is unchanged until 10.0 s after SAVED, then gone in one frame: −18.4 → −7.1, about 101 %.
- The target is ≤ 15 % per 60 fps frame. **FAIL**, as section A.3 R6 said.
- Lamp-on and binocular series (`m0s`, `m0s2`) were tried first: the beam's sweep and the glasses' sway swamp the measurement, hence the still camera.

**H9 reference** (suites, main at `be296c1` plus the M0 capture additions):

| Suite | Result |
|---|---|
| `story_test` | 0 failed |
| `regress_test` | 449 passed (4 headless skips) |
| `interaction_test` | 164 checks, 0 failed |
| `qa_sweep_test` | 7,703 passed |
| `g5_weather_audio_test` | 50, 0 failed |
| `save_compat_test` | 305 passed |
| `opening_test` | 31 passed |
| `run_tests` | 95 |
| `sim_v2` seeds 1 to 5 | no gate failures; the outcomes are saved in `renders/last_light/stageM/m0_sim_v2_seeds_1_5.json`, e.g. expert saved [6,6,5,6,6], score [6741,6741,5741,6741,6741] |

M6 must reproduce `sim_v2` exactly.

### J.2 M1 one sea (2026-11-18)

**Built:**
- **New `scripts/fp/sea_mesh.gd`** (`preload` only, no `class_name`):
  - one radial `ArrayMesh`, a centre fan, then rings to a 6000 m rim;
  - cells 1.4 m to 120 m, then growing 0.02 m per metre (3.6 m at 230 m, 19 m at 1 km, 119 m at the rim);
  - power-of-two segment counts, with stitch strips where they double or halve (no T-junctions);
  - cell scale 1.4 / 1.0 / 0.8 for Low / Medium / High: 108k / 203k / 357k triangles (the old square: 218k), built in about 160 ms on Medium at game start.
- **`OceanWaves`:**
  - new `FADE` table, `wave_gain(i, r)`, `calm(r)`, `shader_fade_array()`, and the static `legacy` flag;
  - `height_at` scales each wave by its gain at the rest position's distance from the tower.
- **`ocean.gdshader`:** `uniform vec2 wave_fade[6]`; each Gerstner term's steepness is multiplied by `1 - smoothstep(fade.x, fade.y, r)`, so displacement and normal fade together.
- **`outside.gd` `_ocean()`:** the radial mesh with a custom AABB; no skirt. `--sea=legacy` keeps the 1100 m square, the skirt and no fade.
- **Bolt foot:** `BOLT_FOOT_Y` −1.5 → **−2.2**. The skirt used to hide the foot; the deepest full-storm trough at 400 m is now −1.84 m. G5's test wants the strip's lowest vertex above −3, and the strip reaches about 0.5 m below the foot.
- **Far planes** 1200 / 2000 → **6500 m**: `player.gd` (the binoculars too), `game_fp.gd` cine camera, `capture_fp.gd`. Legacy keeps the old values.

**The wave fade** (gain 1 inside x, 0 beyond y, metres from the tower). It was derived from the mesh's real cell size, the larger of ring step and arc:

| λ (m) | 60 | 34 | 21 | 13 | 8 | 5.3 |
|---|---|---|---|---|---|---|
| fade | 800–980 | 460–550 | 300–380 | 210–265 | 150–185 | 110–145 |

- Vertices per wavelength wherever a wave is not zero (R28):
  - Medium ≥ 2.53;
  - High ≥ 3.00;
  - Low ≥ 1.49, the 5.3 m chop on the innermost arcs under the island's calming. The old square had 1.6 everywhere for that wave.
- At 230 m (spawns), the 5.3 m and 8 m waves are gone and the 13 m wave is fading. The surface there is the 60, 34 and 21 m swells.

**For Stage E (merge of `stage-e2`):** every CPU or GPU mirror of the sea must scale wave i by `OceanWaves.wave_gain(i, r)`, with r = the rest position's distance from the tower, inside the calming:
- `ship_view2.surface_ys()`: in both the horizontal fixed-point loop and the height sum, multiply each wave's `wc[o + 4] * amp` by the gain at `q.length()`;
- `wake.gdshader`'s copy of `gerstner()`: take `wave_fade` like `ocean.gdshader` (outside.gd passes `OceanWaves.shader_fade_array()`).

The wave set, the calming and the mesh displacement are otherwise unchanged.

**Results:**
- **R28** (19 checks; regress 468 / 468):
  - the uniforms come from `OceanWaves`;
  - the CPU height equals the shader's vertex code from 0 to 6000 m (worst 0.000000 m);
  - the mesh is closed and faces up on all presets, inside budget;
  - the far plane is 6500 m;
  - the bolt foot is under the trough.
- **Suites:** story, run_tests, opening, interaction 164, qa_sweep 7,703, g5 50 / 50 (after the foot moved to −2.2), save_compat 305, pytest all pass. **`sim_v2` seeds 1 to 5 are identical to M0.**
- **Captures `m1h_*`, `m1c_*`, `m1L_*`** (sheets `stageM/m1_sheet_*.png`, viewed):
  - the M2 underlay patches are gone at every bearing;
  - the pale 550 m seam through the binoculars at dawn is gone;
  - ships at 750 and 1000 m now sit below the horizon, in the sea's haze, not against the sky;
  - interior close-ups at a 6.5 km far plane show no z-fighting;
  - `--sea=legacy` reproduces the old look.
- **H1 is still FAIL, as expected before M2.** The step moved from the clip (−0.63° to −1.07°) to the 6 km rim (−0.17° to −0.24°): `ext_b` at storm 0.12 is 31 to 44 (M0: 45 to 52). The far sea and the sky still disagree in colour, and the sky is still drawn below the rim. Both are M2.
- **Corrected 2026-11-18 (start of M2):** the "about 2000 m" steps first listed here for `ext_far!storm_12` and `ext_b045` were a table bug: the comparison keyed files by name without their prefix, so the legacy A/B shots (`m1L_*`, which correctly show the old 2000 m clip: 52.9 and 43.7) overwrote the M1 rows. The M1 values are `ext_far` 35.6 at −0.27° and `ext_b045` 32.2 at −0.19°, both at the rim. `--sea=legacy` is confirmed to reproduce M0.

### J.3 M2 one atmosphere (2026-11-18, awaiting Daniel's choice on the sky)

**Built:**
- **New `scripts/fp/atmosphere.gd`** (`preload`, static):
  - `fog_density()` (today's formula, decision 2), `visibility_m()`, `transmittance()`;
  - `horizon_color(sky_dawn, flash)`: the murk. Night sRGB (0.12, 0.135, 0.16), dawn (0.55, 0.5, 0.48), plus `FLASH_TINT` × flash × 0.12.
- **`outside.gd`:**
  - `_process_body` sets `fog_light_color` and the sky's `murk` uniform to that one colour every frame, the flash included;
  - `_environment` sets `fog_height_density` 0 (the flat veil goes; it also gave the room a 16 % veil), `fog_aerial_perspective` 0, and `volumetric_fog_sky_affect` 1.0 (see the choice below; `--volsky=` for A/B);
  - `--sea=legacy` keeps the old fog, sky and veil.
- **`sky.gdshader`:**
  - the fog bank: the lowest 1.6° to 4° fade into the murk;
  - its top edge undulates on two low-frequency noises along the azimuth and drifts with `time_s`. A first, jagged edge read as a skyline of trees or roofs and was replaced;
  - below the horizon the sky is exactly the murk;
  - `bank = 0` gives the legacy sky.
- **Deviation from section D.1: aerial perspective is not used.** One colour sent to both the fog and the bank matches by construction, with no dependence on the 64 px radiance map lagging a flash (risk I.2). Measured: the flash frame passes H1.
- **Why `volumetric_fog_sky_affect` 1.0:** the volumetric fog lays its last froxel slice over every pixel beyond 180 m. At 0.4 the far sea got all of it but the sky only 40 %, which left a 7 to 14 / 255 line on Medium (Low, without volumetrics, matched to about 1).
- **Regress R29** (12 checks; regress 480 / 480): the fog colour equals the sky's murk equals `horizon_color` at flash 0 and 1; today's densities and visibilities; no veil; no aerial perspective; sky affect 1.0.

**Results (H1, largest step within ±3° of the horizon; M0 → M2):**
- **Medium `m2h`, the full M0 set:**
  - `ext_far` at storm 0.12 / 0.55 / 1.0 / dawn: 51.4 / 46.1 / 24.5 / 41.0 → **0.8 / 0.4 / 1.6 / 1.3**;
  - `ext_b000` to `ext_b315`: 45 to 52 → **0.6 to 0.8**;
  - the window, naked eye: 15 to 29 → **0.5 to 1.8**;
  - binoculars (strip 300:1150, clear of the mullion and latch bar): 19 to 35 → **0.4 to 3.4**, dawn included;
  - the flash: **0.5**.
- **Low `m2q0`:** 0.9 to 2.9 (binoculars 4.2, at −2.7°: the sea's texture, not the horizon).
- **High `m2q2`:** 0.3 to 2.8, and the lightning frame 4.4 (≤ 6 allowed). **H1 PASS** on all three presets.
- **H2:** no step anywhere between the tower and the horizon at the eight bearings; at dawn, T(6 km) = exp(−0.0014 × 6000) = 0.02 % (≤ 0.1 %). **PASS.**
- **H4** (the bank's top edge from per-column profiles): it varies 1.1 to 1.3° across about 85° in three frames, 0.38° in one; it moves 0.27 to 0.40° on average (up to 1.1°) in 30 s. **PARTIAL**, pending Daniel's eye.
- **H6:** through the binoculars the eyepiece vignette darkens the view by about 32 / 255 on average in M0 and M2 alike, so absolute levels cannot be compared; both views pass H1 on their own. **PARTIAL** (the method, not the fog).
- **Room** (`m1t` legacy against `m2t`, same shots): mean luminance +1 to +3 on the close views and +5.6 on `fp_window`, mostly the sea through the glass. Unchanged to the eye.
- **Look, for Daniel** (sheets `stageM/m2_sheet_*.png`):
  - the sea fades into a dark bank, darkest at the sea and thinning into the cloud deck;
  - ships at 750 to 1000 m sit in it;
  - objects fade toward the grey murk instead of near-black, so the scene reads foggier: the tower at 160 m in `ext_far` is visibly veiled;
  - with sky affect 1.0 the sky above is darker and flatter, with less cloud definition;
  - the approved title loses its lighter horizon band and sea line: sea and sky become one dark murk.
- **Option B (`--volsky=0.4`):** keeps more of today's sky, but the line comes back on Medium and High (`m2B`: 9.0 to 16.8). **H1 FAIL.**

**Daniel (2026-11-18): "A + bring the clouds back."**
- **The model:**
  - with sky affect 1.0, the sky above the bank gets (1 − a) of its light, where a is the volumetric cover;
  - under the old 0.4 it got (1 − 0.4a);
  - the fog's own light is near black at night (Low against Medium: in-scatter about 0);
  - so `Atmosphere.sky_gain() = (1 − 0.4a) / (1 − a)` gives the cloud deck its old brightness and contrast.
- **The parameters:** a = 1 − exp(−120 × volumetric density) (K calibrated on M0's sky), capped at 6, and 1 on Low.
- **Where it applies:** `sky.gdshader` multiplies only the sky above the bank (`mix(col * sky_gain, bank_col, b)`), so the horizon match holds.
- **Sky 5° to 25°, mean / std, M0 → with the gain:**
  - storm 0.12: 73.6 / 4.3 → 74.1 / 3.3;
  - 0.55: 63.7 / 3.5 → 61.3 / 2.3;
  - 1.0: 62.2 / 7.9 → 50.4 / 4.2 (a darker sky in a full gale);
  - dawn: 144.2 / 3.8 → 147.2 / 4.2.
  - H1 with the gain: 0.5 to 1.5 (metric shots), 0.6 to 2.8 as played.
- **Seen** (`stageM/m2_sheet_today_A_Aclouds.png`):
  - the cloud deck is back to about today's look;
  - the bank reads as a dark band on the sea, thinning upward;
  - the title is back to today's brightness, without the hard sea line.
- **R29** gains three checks: the uniform equals `sky_gain`; the gain is 1 on Low; it lifts only above the bank.

### J.4 M3 the loom (2026-11-18): built, judged on captures, dropped (Daniel)

**Built:**
- a `loom` uniform in `sky.gdshader`: the beam's world direction and strength;
- a lobe of cos^60 (about 18°) along the beam's bearing in the bank, rising from 0 at the horizon (so no line at the horizon) to a peak a third of the way up;
- tinted warm, `LOOM_GAIN` 0.025;
- strength from the lamp (lit, intensity, focused, less at dawn); `--loom=off`.

**Judged:**
- Sweep series of 8 outward frames at bearing 0 plus 4 window frames, on and off (`m3s_*`), and a stronger, wider variant (gain 0.08, cos^30, about 25°; `m3x_*`). Sheets: `stageM/m3_sheet_loom_on.png`, `_off.png`, `m3_sheet_off_soft_strong.png`. All viewed.
- The beam's own volumetric shaft already lights the horizon wherever the beam points, so the loom only widens that glow slightly at the bank.
- The title is unaffected. H1 with the loom on: 1.1 to 1.8.

**Daniel (2026-11-18): drop it.** The loom code was removed: `sky.gdshader` and `outside.gd` are back to the M2 commit `f88a923`. The beam is exactly as approved (H8 holds by construction). Nothing to commit for M3 beyond this record.

### J.5 M4 vessels in fog (2026-11-18)

**Built** (`scripts/fp/ship_view2.gd`, self-contained):
- `fade_alpha()` = smoothstep(`_appear`) × (1 − smoothstep(`_fade`)): in over `APPEAR_S` = 3 s after she is made, out over the existing 10 s SAVED fade. That fade was counted but never shown before; she vanished in one frame at its end.
- `_fog_fade(dt, storm)`, called at the end of `tick()`:
  - sets `GeometryInstance3D.transparency` on every mesh under the view (any material: the GLB, the stand-in, E2's wake and spray), only on change, and back to 0 when she is fully there (no lasting alpha pass);
  - scales each light from its `e0` meta;
  - dims each bulb by √T(d) × alpha. The bulbs now skip the depth fog (`disable_fog`), so at range a lamp keeps more of its light than the hull keeps of its contrast: lights read first (at 230 m, storm 0.12: 71 % against 50 %).
- `setup()` calls `_fog_fade` deferred, so she is never drawn at full strength on her first frame.
- **Deviation from section E:** no separate halo billboards. The bulbs themselves, fog-dimmed by √T and above the glow threshold, give the halo.

**Regress R30** (11 checks; regress 494 / 494):
- alpha 0.003 on her first frame; half at about 1.5 s; full at 3 s;
- the largest change in one 60 fps frame is 0.8 % in and 0.25 % out (H5 ≤ 15 %);
- opaque again when she is fully there;
- the view never writes to the sim (position, heading, state);
- the bulbs skip the fog; the lamps fade with her.

**Captures** (`m4s` series with the still camera; `m4c_*` ranges; sheets `stageM/m4_sheet_shipseq.png`, `m4_sheet_ships.png`; viewed):
- **Arrival:** nothing at f000, a ghost at f004, half at f009, complete by f013. The measured contrast steps are ≤ 2.4 per 1/6 s sample (about 0.24 % per 60 fps frame). M0 was about 108 % in one frame.
- **Departure:** a gradual fade; nearly gone at f069, gone at f074. M0 was about 101 % in one frame.
- One spike at f075 is the beam sweeping into the view: the expert bot turned the lamp back on during the series. It is not the vessel.
- **H5: PASS.**
- **Ranges:** at 1000 m a faint hint at most; at 750 m the fishing boat's lamps before her hull; at 400 m the hull and lights. Each shot is taken a few seconds after its ship spawns, so the farthest may not be fully faded in.

**Suites:** story, run_tests, opening, interaction 164, qa_sweep 7,703 (96 s), g5 50, save_compat 305, pytest all pass; **`sim_v2` seeds 1 to 5 identical to M0.**

**For the Stage E merge of `stage-e2` (after this commit):**
- **`ship_view2.gd`:**
  - keep the `# Stage M (M4)` section at the end of the file unchanged;
  - E2's `tick()` must end with `_fog_fade(dt, storm)`;
  - E2's `setup()` must start with `_fog_fade.call_deferred(0.0, 0.5)`;
  - E2's `_nav()` must set `l.set_meta("e0", energy)` on each light and, on each bulb material, `disable_fog = true` and `set_meta("c0", <its colour>)`;
  - `visible` and `done` keep their logic.
- **Surface mirrors (from M1):** `surface_ys()` (both loops) and `wake.gdshader`'s `gerstner()` must scale wave i by `OceanWaves.wave_gain(i, r)`.
- **Whitecaps, shore and reef foam, and depth tint** go into `ocean.gdshader` as Stage E's work. The shader now has the `wave_fade` uniform and the per-wave gain in `vertex()`; crest foam already fades with the displacement (`crest` uses the faded `disp`).

**Decisions for Daniel** (answers in DECISIONS Q22: 1 yes; 2 keep; 3 build and judge on captures; 4 open until M5; 5 in M4; 6 paired bench at M6):
1. Stage M takes M2, M4 and the horizon blend from Stage E and runs before it (recommended), or folds into E.
2. Fog density: keep today's visibility (0.6 to 1.3 km, recommended; the fix is geometry and colour), or make it thicker or thinner.
3. The loom of the light on the fog bank: yes or no.
4. M5, near-field drifting scud on High: try it and measure, or skip.
5. The vessel fade-in and fade-out (fixing today's pop) here (recommended) or in Stage E.
6. The bench and window captures in M0: when the Mac is free.

### J.6 M5 near-field scud (2026-11-19): built, judged on captures, dropped (Daniel)

**Decision 4** (DECISIONS Q22), asked at M5: Daniel chose **"try it and measure"**, squall included, kept only if the M6 bench shows it earns its milliseconds.

**Built** (all removed again, see below):
- `scripts/fp/scud.gd` (preload) and `shaders/scud.gdshader` (`shader_type fog`):
  - four box `FogVolume`s tiling the 30 to 170 m annulus (inner hole ±21.2 m, inscribed in the 30 m circle) from the sea to 36 m;
  - density from a seamless 64³ `NoiseTexture3D`, flattened, thresholded into patches, trimmed by a ring mask and a height mask;
  - carried by `TitleStorm.WIND` at 4 to 11 m/s, the drift integrated on the CPU;
  - a squall envelope from three slow sines (about 11 % of a gale's time, only above storm 0.25), adding density, speed and cover;
  - High only, off on the title, the legacy sea and `--scud=off`; visual only (no sim access, no random draws).
- Regress R31 (14 checks: the High-only gate, annulus coverage, the shader's masks equal to the CPU copies, the drift, the squall's smoothness and share, the title, the dawn, no sim access).

**Calibration** (`ext_b045`, beam-free half of the frame):
- At ×30 density the volumes render as an opaque wall.
- Fog-volume `EMISSION` behaves as density-weighted: an opaque patch converges to it.
- At 1× the murk (linear) the wall was 9 to 13/255 against the bank's 41 to 51, near black. At 3× it matched the bank (45, 43, 44 against 41, 43, 51), so a patch seen against the horizon cannot draw a line.
- The first density (0.010 to 0.030 1/m) was invisible; the judged set used 0.030 to 0.090.

**Judged** (`m5f` on, `m5fo` off, `m5fq` full squall; High, storm 0.55 and 1.0; sheets `stageM/m5_sheet_scud_ext.png`, `m5_sheet_scud_window.png`; viewed):
- The scud read as an uneven darkening of the middle distance, not as drifting patches: the volumetric fog's froxel grid is coarse at 30 to 170 m, so patches blur into large soft blobs.
- The beam lights it as big, soft, warm blobs.
- In a gale, and more in a squall, the window view went to flat murk: the sea, the horizon and anything beyond about 120 m disappeared. That is far below the 0.6 km gale visibility of decision 2, and it hides the vessels the player must find.
- No frame-time figure was taken: the capture fps are run-to-run noise on a loaded Mac, and the bench waits for Daniel.

**Daniel (2026-11-19): drop it.** `scud.gd`, `scud.gdshader`, R31 and the two `outside.gd` hooks were removed; a temporary `lamp_off` capture state was removed too. The game files are back to the M4 commit. Nothing to commit for M5 beyond this record and DECISIONS Q22. The M5 captures stay in `renders/last_light/` (`m5*`, gitignored); `m5n` is the scud-off set. The files that were not evidence for the look were deleted on 2026-11-19 with Daniel's OK (43 files, 35 MB): `m5o --scud=off_*` (a mis-named re-run with the scud still on, from a shell loop bug) and the calibration frames `m5x*`, `m5y*`, `m5e*` and `m5g` (dev knobs `--scud_gain` and `--scud_em`).

### J.7 M6 QA and checkpoint (2026-11-19)

**Base:** main at `f24439b` (M0 to M4 plus Stage R's commit; M3 and M5 dropped, so no game file differs from the M4 commit). `stage-e2` had not merged, so R28 to R30 were not re-run against E2's `ship_view2.gd` (to do after that merge: J.5's notes).

**After-set** (`tools/godot_bg`, Medium, `--bot=expert`; the shot lists rebuilt from the M0 file names, so the shots are the same):
- `m6h_*`, the M0 metric set (35 shots, `--noglass --norain --nohud`);
- `m6c_fishing_*` and `m6c_steamer_*` (6 each);
- `m6s_*` (`shipseq`, 93 frames);
- `m6b_*` (as played: title, window, binoculars, `fp_window`, `ext_far`);
- `m6t_*` (title and room close-ups, the `m1t` / `m2t` shots).
- Sheets, all viewed: `stageM/m6_sheet_ships_fishing.png`, `m6_sheet_ships_steamer.png`, `m6_sheet_played_title.png`, `m6_sheet_room.png`.

**Results against section H:**

| # | Result | Evidence |
|---|---|---|
| H1 | **PASS for the horizon** | Largest step within ±3° of the horizon, M0 → M6: `ext_far` 24 to 51 → **1.0 to 3.2**; `ext_b000` to `ext_b315` 46 to 52 → **1.2 to 1.4**; window 15 to 29 → **0.5 to 2.1**; binoculars (strip 300:1150) 18 to 36 → **0.4 to 3.9**; flash 7.5 → **0.7**; `fp_bolt` 10.3 → 6.8, but at +1.99° in M0, M2 and M6 alike: the window's horizontal transom, not the horizon (viewed: the horizon behind the bolt is soft). One view is over 4: the binoculars at dawn, `pitch_m3`, **5.0 at −1.38°**, 165 rows below the horizon. It is on the sea, not the horizon (see H7). |
| H2 | **PASS** | No step at any of the eight bearings (`ext_b*` 1.2 to 1.4, all on the bank's soft gradient above the horizon). |
| H3 | **PARTIAL** | `ext_b000`, the sea's luma spread per 1° strip. At 100 to 150 m it is 7.9 to 15.1, against M0's 7.5 to 14.4, so the near sea keeps at least M0's contrast now the 45 % veil is gone. The "≥ 80 % of no-fog" figure needs a no-fog capture (NOT TESTED). The spread does not fall steadily with range: 8.3 at 154 m, 10.9 at 620 m, 12.1 at 1.2 km. The long swell's foreshortened crests and the far sea's flat patches add banding with range. |
| H4 | **PARTIAL** (unchanged from J.3) | The bank's edge varies 1.1 to 1.3° across about 85° and moves 0.27 to 0.40° in 30 s; Daniel's eye still to come. |
| H5 | **PASS** | `m6s`, window x 700–1220, y 400–700, the darkest 2 % against the median. The empty sea is −11.1 and the settled vessel −21.2. In over about 9 samples (1.5 s), out over about 20 (3.3 s). The largest vessel step is 3.35 per 1/6 s sample, about 3 % of her contrast per 60 fps frame (≤ 15 %). Three one-frame spikes at samples 8, 39 and 69 (5 s apart) are the beam sweeping through the still camera: the expert bot relights the lamp that `shipseq` turns off (as at M4's f075). M0 (J.1): about 108 % in one frame. |
| H6 | **PARTIAL** (unchanged) | The eyepiece vignette (about 32/255) prevents an absolute comparison; each view passes H1 on its own. |
| H7 | **PASS with one open item** | R28 passes (regress 494). Seen: no facets or shimmer. **Open:** through the binoculars at dawn, the far sea at about 0.6 to 1 km shows pale, flat, sharp-edged patches. The faded short waves leave the surface flat there, and it mirrors the bright dawn sky between the 60 m swell's crests. Already in M2 (`m2h_t083`, step 3.4), so not new in M6; it is the 5.0 above. A candidate for Stage E's sea work (a far-sea roughness floor or a distance blend of the normal), not a horizon fault. |
| H8 | **PASS** | The loom was dropped; the beam code is as approved. Title (`m6_sheet_played_title.png`, `m6_sheet_room.png`): the layout and brightness match M0; the faint sea line is gone; the cloud deck is back (Q23). |
| H9 | **PASS** | Story 0 failed; `sim_v2` seeds 1 to 5 **identical to the M0 JSON** (exact equality); run_tests 95; opening 31; interaction 164 (0 failed); g5 50; save_compat 305; regress 494 (4 headless skips); qa_sweep 7,703 (92 s); pytest green. |
| H10 | **PARTIAL** (bench 2026-11-19, below) | **Medium PASS** on the one clean pair: median −0.1 to +0.9 %, p95 −1.5 to +2.8 % against `--sea=legacy`. **Low PASS:** both seas sit at the 60 Hz cap (16.7 ms) when focused; the new sea draws 0.11 M fewer primitives. **VRAM PASS:** 1331 MB at most. **High NOT CLEANLY TESTED:** no focused, quiet pair; 28 to 39 ms on both seas, so High misses its 25 ms target with the legacy sea too (not a Stage M regression); new against legacy is inside the run-to-run noise; +0.13 M primitives (+5 %). |

**Ships** (`m6_sheet_ships_*.png`, M0 against M6, both kinds):
- At 1000 m M0 showed a crisp black silhouette on a hard horizon; M6 has nothing readable in that frame, because the beam was in the view.
- At 750 m M0 showed a silhouette against the sky; M6 shows her lamps and a faint hull in the murk.
- At 400 m: hull and lights. At 230 m and 120 m: unchanged.
- To the naked eye: no hard line.

**Daniel (2026-11-19), at the checkpoint:**
- **Approved the look:** the after-set and M2's "A + clouds" as they stand.
- **Keep `--sea=legacy` for now**; removing it is decided after Stage E merges.
- The records were committed locally (`78c85a3`).
- He said the Mac was free for the bench, but macOS indexing ran right after the after-set wrote its PNGs (Spotlight `mdworker`, then XProtect and Siri): the load stayed at 14 to 17 for 30 minutes. **The bench was not run (H10 NOT TESTED).**
**Bench (H10), 2026-11-19 10:15 to 11:32.**

Command per run: `tools/godot --audio-driver Dummy --path projects/games/last_light/godot -- --capture=m6bench_q<Q>_<new|legacy>_r<N> --novsync --bench --bench_secs=20 --bench_shots=fp_desk,fp_window,fp_gen,fp_bino --quality=<Q> [--sea=legacy]`. Bash loops, run in the background; the load was logged before each run. Output: `renders/last_light/m6bench_*_bench.json`.

Three passes:

1. **Pass 1 (10:15, 12 runs, interleaved):** started at a load of 2.6, after Daniel closed Brave and the Playwright session.
   - Runs 1 to 5 held focus.
   - At about 10:22:40, during `q2_new_r1`, another window took the foreground (a 333 ms frame at that moment). Every run after it is unfocused: once something else is in front, macOS does not let a newly launched Godot take focus.
   - `q0_new_r1` opened at 1920×1080 at scale 0.75, against 3840×2410 at 0.355 for the others. The render size is the same, 1.17 M pixels.
2. **Re-run (`*_rerun`, 11:08):** the nine invalid runs. Focus was lost from the first frame, so it was stopped after three runs.
3. **Re-run 2 (`*_rerun2`, 11:17, nine runs):** Godot was brought to the front with AppleScript every 15 s. Focus still flickered per shot, and the load was 3.3 to 4 throughout. The same focused configuration varies by up to 17 % between runs (High `fp_desk` with the new sea: 28.45 and 33.21 ms), so these runs only give the range.

All runs exited 0, with no `SCRIPT ERROR`. The "resources still in use at exit" lines are Godot's shutdown notices.

The clean pairs are from pass 1, repeat 1 (focused, quiet). Times are medians and p95 in ms.

| Quality | Shot | New | Legacy | Δ median | Δ p95 |
|---|---|---|---|---|---|
| Medium (1) | fp_desk | 18.63 / 20.68 | 18.62 / 20.66 | +0.1 % | +0.1 % |
| Medium (1) | fp_window | 18.74 / 20.90 | 18.68 / 20.83 | +0.3 % | +0.3 % |
| Medium (1) | fp_gen | 17.49 / 19.14 | 17.51 / 19.44 | −0.1 % | −1.5 % |
| Medium (1) | fp_bino | 17.39 / 18.76 | 17.23 / 18.25 | +0.9 % | +2.8 % |
| Low (0) | all four | 16.67 to 16.70 / 17.5 to 17.8 | 16.68 to 16.71 / 17.7 to 18.0 | 0 (60 Hz cap) | −0.5 to −1.2 % |

- **Medium** is inside the +2 % median and +5 % p95 targets at every shot. Primitives fell from 1.85 M to 1.83 M at most; VRAM was 1155 against 1156 MB.
- **Low:** both seas are at the display cap when focused, so the bench cannot separate them. Unfocused (uncapped) samples put the new sea at or below legacy. Primitives: 1.36 M against 1.47 M at most.
- **High:** no focused pair from the quiet period.
  - The ranges overlap. New sea: 26.6 to 39.0 ms, focused 28.45 to 34.23 ms. Legacy: 27.7 to 37.6 ms, focused 28.79 to 33.55 ms.
  - Primitives: 3.02 M against 2.89 M at most (the 512-segment radial sea).
  - The 25 ms target is missed by both seas, so it is a High-budget item for a later stage, not a Stage M cost.
- **VRAM:** 1091 MB on Low, 1155 MB on Medium, 1331 MB on High; all ≤ 1.4 GB.
- **To make High clean**, if wanted: a quiet Mac with no other app able to take the foreground (or Daniel clicking each window), quality 2 only, about 7 minutes.

**Stage M is closed** with H10 PARTIAL as above. The handover is in `docs/SESSION_HANDOFF.md`:
- After the E2 merge: re-run R28 to R30; check `ship_view2.gd`'s `_fog_fade` and its `wave_gain` mirrors (J.2, J.5); capture an `m7c_` / `m7s` set. `stage-e2` was not merged on 2026-11-19.
- H4: still needs Daniel's eye.
- H6: a method limit.
- The pale, flat far-sea patches through the binoculars at dawn (H7): a candidate for Stage E.
- Removing `--sea=legacy`: Daniel's call after Stage E.
