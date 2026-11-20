# THE LAST LIGHT: R7 submission checklist

Branch `release-r7` (worktree `exports/worktrees/last_light_r7`, from main `eff547c`). Intermediates go to `renders/last_light/r7/`; the package goes to `projects/games/last_light/build/R7/`. Competition: National Autumn IT Tournament "Джон Атанасов" 2026/27. **Registration (in Bulgarian) closes 29.11.2026**; the defence is in Sofia, 4–6.12.2026.

Statuses: DONE · IN PROGRESS · BLOCKED (owner) · NOT TESTED. *(Live document: updated during R7.)*

| # | Item | Status | Output | Evidence / note |
|---|---|---|---|---|
| A1 | `film_fp.gd --film_credits` (endings run on into the credits through the shipping path) | DONE | `godot/scripts/film_fp.gd` | 4 endings reached `credits at_end=true` |
| A2 | Ending: Heard Together | DONE | `Endings/TheLastLight_Ending_HeardTogether.mp4` | 141.8 s; 4254/4254 frames; sheets viewed |
| A3 | Ending: Nothing to Report | DONE | `Endings/TheLastLight_Ending_NothingToReport.mp4` | 153.3 s; 4750/4750 frames recorded; sheets viewed |
| A4 | Ending: Light Exhibited | IN PROGRESS | | first take rejected: the window was covered, 2332 of 4356 frames drawn |
| A5 | Ending: Correction (re-take with credits) | IN PROGRESS | | first take rejected: covered window, 2584 of 4459 frames drawn |
| B | Screenshots (6–8 + contact sheet) | TODO | `Screenshots/` | |
| C | Source archive + clean room | IN PROGRESS (Worker C) | `02_Source/` | |
| D | README EN/BG, BG documentation, print digest, leaflet, Appendix 4 draft | DRAFTED (Worker D), fact-check IN PROGRESS | `03_Документация/` | premise corrected (no "eight men", no 11-minute spoiler) |
| E1 | Trailer footage reel (13 in-engine shots, Movie Maker, High preset) | TODO | `renders/last_light/r7/reel/` | `release/R7/trailer/reel_shots.txt` |
| E2 | Trailer edit (EDL + build script) | TOOLS READY | `release/R7/trailer/{edit.json,build_trailer.py}` | |
| E3 | Title and place cards | DONE | `renders/last_light/r7/trailer/cards/` | viewed |
| F | ElevenLabs narration (Q28) | IN PROGRESS | `release/R7/trailer/VO_SCRIPT.md` | Free plan; terms saved; 1 Hector sample made; downloads fixed by Daniel |
| G | R30 deterministic | IN PROGRESS (Worker F) | `godot/tests/` | |
| H | Windows export | IN PROGRESS | `01_Build/Windows/` | official 4.7.2 templates downloading; preset added in branch |
| I | Integration + final gate | TODO | `build/R7/TheLastLight_R7/` | |
| R6 | Daniel's timed playthrough | BLOCKED (Daniel) | | play time placeholder `[[R6_PLAY_TIME]]` |

## Rules facts (from `John Atanasov/Регламент 2026-2027.pdf`)
- Upload everything online and share the link: source code (mandatory), executable, documentation, presentation, other files.
- The physical folder holds: a labelled flash drive or CD; documentation of up to 5 A4 sheets (Appendix 1 structure, Times New Roman 12, spacing 1.5); one advertising leaflet; the Appendix 4 declaration.
- The defence is 15 minutes, presented from a flash drive or your own laptop. Windows is not required.
