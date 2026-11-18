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

**Decisions for Daniel** (answers in DECISIONS Q22: 1 yes; 2 keep; 3 build and judge on captures; 4 open until M5; 5 in M4; 6 paired bench at M6):
1. Stage M takes M2, M4 and the horizon blend from Stage E and runs before it (recommended), or folds into E.
2. Fog density: keep today's visibility (0.6 to 1.3 km, recommended; the fix is geometry and colour), or make it thicker or thinner.
3. The loom of the light on the fog bank: yes or no.
4. M5, near-field drifting scud on High: try it and measure, or skip.
5. The vessel fade-in and fade-out (fixing today's pop) here (recommended) or in Stage E.
6. The bench and window captures in M0: when the Mac is free.
