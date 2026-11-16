# THE LAST LIGHT: Document 2: technical architecture audit

> Audit of 2026-11-15 at commit `2b5d3ee`. Paths are relative to `projects/games/last_light/` unless they start with `docs/`, `assets/`, `renders/` or `tools/`; `g/` means `godot/`. Section numbers are those of the approved plan. Index: [README](README.md).

## 2. Technical architecture (as built)

| Area | Implementation | Key files (under `projects/games/last_light/godot/`) |
|---|---|---|
| Engine | Godot 4.7.2, Forward+, 60 Hz physics, macOS only, everything built in code from `scenes/main_fp.tscn` | `project.godot`, `scripts/main_fp.gd` |
| Autoloads | `GameState`, `Settings`, `SaveSystem` | `scripts/game_state.gd`, `settings.gd`, `save_system.gd` |
| Input | Actions registered in code. Space = `dialogue_next`, E interact, J duty recall, L logbook, H history, G compass, B binoculars, F torch | `scripts/core/input_setup.gd` |
| Story | Beats in `chapters.json` (11/8/7/5/5/7), conversations in six `.dlg` files, flags and clues in `StoryState`, actions run by `StoryDirector` | `scripts/story/*`, `data/story/*` |
| Dialogue UI | Radio panel (portrait card, grows upward), subtitles, replies; thoughts auto-advance, radio waits for Space | `scripts/ui/dialogue_ui.gd`, `scripts/story/speakers.gd` |
| Objectives | Duties with per-step nudge (25 s) and hint (60 s); duty HUD; J recalls; L logbook has a Duties page. **No journal exists** | `scripts/ui/duty_hud.gd`, `story_director.gd`, `logbook_pages.gd` |
| Interaction | Raycast on layer 2 against `IA_<id>` boxes from the GLB; `DEVICES` table gives each a kind (toggle, hold, focus, info, doc, pickup, door) | `scripts/fp/player.gd`, `station.gd` |
| Documents | Full-screen viewer on its own layer: zoom 1 to 4x, pan, transcription, guarded close | `scripts/story/story_presenter.gd`, `assets/docs/docs.json` |
| Station sim | Generator, battery, breakers, lamp, jams, fleet, channels; story faults via `trigger_fault` | `scripts/core/keeper_sim.gd`, `keeper_config.gd` |
| Radar | 512 px SubViewport on the desk CRT, fixed 250 m range, north up | `scripts/fp/radar.gd` |
| Sea and ships | Six Gerstner waves (GPU and CPU copies), one 1100 m plane; ships are procedural stand-ins | `scripts/fp/outside.gd`, `ship_view2.gd`, `ocean_waves.gd`, `shaders/ocean.gdshader` |
| Audio | Buses made at runtime; 52 synthesised WAVs; no voice, no radio filter; one music player with no crossfade | `scripts/audio_director.gd`, `../audio/synth.py` |
| Saves | Autosave only, JSON, `VERSION 1` with no migration between versions; beat-index remap table exists | `scripts/save_system.gd`, `story_state.gd` |
| Tooling | Capture and bench flags are read from the command line and are **not gated out of release builds** | `scripts/capture_fp.gd`, `autotest.gd` |
| Assets | Room, lighthouse, island, hands, body from Blender scripts; CC0 textures and OFL fonts logged; Daniel-supplied AI images are not in the licence log | `../blender/*`, `assets/ASSET_LICENSES.md` |

## 15. Document 2 in full: architecture evidence

### 15.1 Systems and how they connect
```
main_fp.gd  (menu, loading, credits)
   └─ game_fp.gd  (owns one play session; routes every event)
        ├─ player.gd ── equipment.gd (torch, compass, binoculars, hands.glb)
        │      └─ player_body.gd (body.glb; sit pose)
        ├─ station.gd  (watch_room.glb hooks: IA_, PT_, NDL_, LMP_, LIGHT_, FOCUS_)
        │      └─ keeper_sim.gd + keeper_config.gd  (power, generator, light, fleet)
        ├─ outside.gd  (ocean, sky, rain, lightning, island, ship_view2.gd)
        ├─ radar.gd    (SubViewport drawn onto SCR_radar)
        ├─ fp_ui.gd    (crosshair, prompts, VHF panel, notices)
        ├─ story_director.gd ── story_state.gd, dialogue_db.gd, dialogue_runner.gd
        │      └─ story_presenter.gd ── dialogue_ui.gd, duty_hud.gd, logbook_pages.gd,
        │                               ending_sequence.gd, backlog_ui.gd
        └─ audio_director.gd
Autoloads: GameState, Settings (also creates audio buses), SaveSystem
```

### 15.2 Evidence table
| System | Fact | Where |
|---|---|---|
| Engine | Godot 4.7, Forward+, MSAA 3D x2 in project, 1920x1080 fullscreen, `canvas_items` / `expand`, physics 60 Hz | `g/project.godot:10-41` |
| Launch wrappers | `tools/godot` (headless and direct), `tools/godot_bg` (background window, Dummy audio, exits 0 only on a `*_RESULT` line) | workspace `tools/` |
| Input | Actions created in code; Space is both `boost` (legacy) and `dialogue_next`; mouse buttons read directly | `g/scripts/core/input_setup.gd:7-77`; `g/scripts/fp/player.gd:125-158` |
| Scene flow | Menu is a live game in attract mode; 2.6 s push-in; threaded GLB preload; `campaign_over` leads to credits | `g/scripts/main_fp.gd:39-66, 417-528` |
| Story state | chapter, beat, flags, clues, relations (-3..3), rescues, history (last 300 saved), duties, `in_beat` / `resume` | `g/scripts/story/story_state.gd:6-40, 172-217` |
| Beats | `{id, when, duty, hint, needs_power, do}`; `talk` and `wait` block; `until` holds; radio talk waits for power | `g/scripts/story/story_director.gd:36-52, 530-685` |
| Dialogue format | `== id mode=`, `SPEAKER(expr)@room:`, `~` thought, `>` caption, `*` choice, `!` action, `[if]` | `g/scripts/story/dialogue_db.gd:3-57` |
| Line advance | Radio waits for Space with a cue; others auto-advance at 1.0 s + 0.06 s per character, 2.8 to 9 s | `g/scripts/ui/dialogue_ui.gd:63-71, 410-469` |
| Radio panel | Bottom-left, 820 px wide, grows upward; text is a fit-content RichTextLabel at 25 px; card 152x190 drawn by hand | `dialogue_ui.gd:73-102, 472-509`; `g/scripts/ui/style.gd:155-184` |
| VHF panel | Centre-right anchor, x 1450 to 1880, y 240 to 840 at 1080p, shown only in the radio view | `g/scripts/fp/fp_ui.gd:122-170, 226-229` |
| History | Every line and choice logged; H or pause menu opens it | `g/scripts/ui/backlog_ui.gd`; `game_fp.gd:520-549` |
| Duties | Per-chapter `duties` with steps, nudge 25 s, hint 60 s; HUD line held 6 s; J recalls | `story_director.gd:256-475`; `g/scripts/ui/duty_hud.gd:12-127` |
| Hints | 14 s on screen, 2.5 s minimum before replacement | `g/scripts/story/story_presenter.gd:57-58, 332-340, 778-798` |
| Interaction | Ray on layer 2, reach 1.9 m; specific control beats its cabinet; walls, floor, ceiling, stair occlude | `player.gd:375-455`; `g/scripts/fp/station.gd:52-95, 249-263, 641-703` |
| Document viewer | Layer 30, zoom 1 to 4x, pan, T transcription, closes on E / Esc / B / right click after 3 frames | `story_presenter.gd:138-181, 643-774` |
| Generator | OFF, CRANKING, RUNNING, STOPPING; crank 1.5 s; overheat at 100 C, restart below 60 C | `g/scripts/core/keeper_sim.gd:9, 196-210, 466-505` |
| Story faults | `overheat`, `trip`, `jam`; chapter start sets clock, storm, battery, fuel only | `keeper_sim.gd:360-373`; `story_director.gd:186-216` |
| Radar | 250 m, sweep 2.4 s, rings every 50 m, north up | `g/scripts/fp/radar.gd:6-96` |
| Fleet | Spawn at 230 m or a beat's `range`; channel capture 55 to 150 m within 12 degrees; edge at 310 m | `keeper_sim.gd:636-742`; `g/scripts/core/keeper_config.gd:6-95` |
| Layout | Island radius 21 m, 31 reefs out to about 112 m, three channels at -46, 0, +46 degrees | `g/assets/data/layout.json` from `blender/layout.py` |
| Ocean | 1100 m plane, 330x330 cells, 6000 m skirt at -0.6 m; six Gerstner waves; CPU copy for ships | `g/scripts/fp/outside.gd:304-356`; `g/shaders/ocean.gdshader`; `ocean_waves.gd` |
| Ships | Looks for `ship_<kind>.glb`, none exist, builds stand-ins | `g/scripts/fp/ship_view2.gd:6-136` |
| Audio buses | Music, SFX, Dialogue, Ambient to Master; Exterior to Ambient through a low-pass (2.4 kHz in game) | `g/scripts/settings.gd:8, 52-58`; `g/scripts/audio_director.gd:21-25, 73-90` |
| Music | One player; menu pad -8 dB; `music` cue swaps with no fade at -12 dB; used once (ch4 `approach`); never stopped or saved | `audio_director.gd:60, 156-167, 279-283, 331-335`; `g/data/story/chapters.json:85` |
| Saves | `user://saves/slot_<slot>.json`; `VERSION 1`; any other version is corrupt; autosave at beat entry, the `autosave` action, chapter change, quit | `g/scripts/save_system.gd:9-63`; `game_fp.gd:381-420` |
| Tests | `run_tests`, `regress_test` (R1 to R23), `story_test`, `opening_test`, `interaction_test`, `portrait_test` (stale, 2 failing checks), `qa_sweep_test`, `g5_weather_audio_test`, `sim`, `sim_v2`; workspace pytest | `g/tests/`; workspace `tests/` |
| Release gating | No `OS.is_debug_build` or feature check; export excludes only `tests/*` | `g/export_presets.cfg:11` |
| Licences | 14 Poly Haven CC0 textures, Blender Studio base meshes (CC0), four OFL fonts | workspace `assets/ASSET_LICENSES.md` |

### 15.3 Reusable code for the planned work
| Need | Reuse |
|---|---|
| Auto-advance for radio lines | `dialogue_ui.auto_advance_s()` and its hold checks |
| Minimum dwell with auto timer | `EndingSequence._wait` |
| Full-screen documents | `story_presenter.open_document`, `docs.json`, `BUILTIN_DOCS`, `after_read` |
| Story-gated objects | `station.availability`, `set_story_prop`, `game_fp._update_story_props` |
| Refusal with a reason | `station.availability` plus `fp_ui.show_notice_once` |
| Non-blocking thought | `story_presenter.show_thought` / `queue_thought` (the valve-shut path) |
| Battery floor | the title screen's floor in `game_fp._title_events` |
| Drag gesture | the viewer's left-drag pan (`story_presenter.gd:761-767`) |
| Cloth garments | `blender/coat_cloth.py` |
| Knit texture | `blender/documents.py:679-704` |
| Rig and clips | `blender/body.py` |
| Silver-print ageing of a supplied photo | `blender/documents.py` `silver_print` |
