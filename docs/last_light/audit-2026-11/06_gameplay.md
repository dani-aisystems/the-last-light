# THE LAST LIGHT: Document 6: gameplay expansion proposal

> Audit of 2026-11-15 at commit `2b5d3ee`. Paths are relative to `projects/games/last_light/` unless they start with `docs/`, `assets/`, `renders/` or `tools/`; `g/` means `godot/`. Section numbers are those of the approved plan. Index: [README](README.md).

## 8. Documents, journal and guidance

- **Viewer reuse:** `story_presenter.open_document` for Keeper's Orders, the supply diagram, the Tide Tables (invented but plausible November 1971 figures, marked as invention), the radio-check card, and new teleprinter sheets.
- **Progressive availability:** each document carries a state (not yet relevant, newly relevant, available, read) derived from story flags through `station.availability`. "Newly relevant" is shown by a physical change (a sheet curled out of the teleprinter, a drawer left ajar, a catch-light), not a UI marker. Nothing is ever greyed out without a spoken reason.
- **Journal:** J opens the logbook at a pencilled "Tonight" page (extends the existing Duties page): current duties, done ones struck through, the latest hint per duty, and "Kept papers" re-opening every document already read. L opens the same book at the log. This implements Proposal 37 option (b) with a J alias; automatic "Notes" entries are a later choice.
- **Hints:** state-driven as now (nudge at 25 s, hint at 60 s), but the hint is also written to the journal page and stays until the step is done.
- **Dead-end tests:** for every required step in every chapter, a headless run that does nothing proves a nudge, a hint and a journal line appear; a save loaded mid-event resumes it.

## 10. Radar, larger sea and the fuel run

### 10.1 Radar as built
Fixed 250 m range, north up, east right, rings every 50 m, reefs as static echoes, ship echoes refreshed by the sweep, labels only after a vessel confirms its position. It is a full plan-position sweep, not a sector chart.

### 10.2 Range switch
- A three-position knob on the radar cabinet (new `IA_radar_range`, wheel to turn): near 250 m, middle 500 m, far 1000 m. Rings and labels redraw per range; bearing labels do not move.
- Static hazards drawn as steady echoes; moving contacts as fading sweep echoes, as now.

### 10.3 Larger sea
- **Principle:** the inner 250 m game stays exactly as it is; an outer approach leg is added in front of it. This protects the seeded sim results and the tuned rescues.
- **Two defects to fix first (Code):** a story ship given a range beyond 310 m is resolved as "stood out to sea" on its first step; and far hazards added to the reef list would silently retarget every ship that aims at "the nearest reef".
- `blender/layout.py`: an outer line of hazards between about 300 and 800 m (three or four named skerries and one shoal), marked as a separate kind, placed so each channel has one clear outer approach; the clearance checks extended outward.
- Far spawns are placed by projecting the existing 230 m entry course backwards, so every ship still arrives at the same inner point on the same heading. Storm drift and blind steering error apply only inside the old radius, because the light does not reach beyond about 300 m and an outer leg bent by drift could not be guaranteed.
- A new world-edge setting replaces the current 310 m edge. The ocean mesh, 550 m to each side today, is extended to match the far range.
- **Pacing cost (from the code's speeds):** each extra 100 m adds 31 s for a fishing boat, 45 s for the *Gannet*, 62 s for the visitor's boat and 91 s for the *Iona Star*. So far spawns go to the fast vessels and the new *Hendrika*; the *Kittiwake*, the visitor and the *Iona Star* keep their present distances.
- Difficulty: chapter 1 uses the near range only; chapter 2 introduces the middle range; chapter 3 needs the far range to see the *Hendrika* coming.
- No random spawns in the story. Every outer leg is checked against every far hazard for seeds 1 to 50; the `sim_v2` gates must pass before and after; inner arrival times must match the old values within tolerance.
- **Far range value:** 1000 m as chosen. The design review preferred 750 m because fog leaves only about 7 to 37% visibility beyond 400 m; the final figure is set at the stage checkpoint from captures.
- **Not determinable from code, to be captured in Stage 0:** how ships and rocks look beyond 400 m, the frame cost of the larger sea, and the binocular view at range.

### 10.4 Stairwell fuel run (chapter 3 opening)
Sight glass low; Callum's line; take the torch; open the stair door; down the ladder; work the hand pump (hold) while the day-tank float is heard rising; climb back; close the door. About 3 minutes. The automatic top-up stays as a silent safety net if the player ignores it. It teaches the stair before Ross climbs it and sets up the fouled-fuel cause in chapter 4.

## 19. Document 6 in full: gameplay expansion

| Topic | Options weighed | Chosen | Scope |
|---|---|---|---|
| Radar coverage | One larger fixed range; three-range switch; chart plotting | Three-range switch | Section 10.2; 2 days |
| Distant hazards | Random field; hand-placed outer line | Hand-placed, named, validated by `layout.py` | 2 days with the chart reprint |
| Routes | Free approach; back-projected leg onto today's entry points | Back-projected | 2 days |
| Spawning | Random far spawns; fixed per beat | Fixed per beat in the story, seeded in watch mode | 1 day |
| Leaving the room | None; stairwell; full exterior | Stairwell fuel run | Section 10.4; 5 to 7 days including the lower level |
| Generator fuel | Automatic top-up only; manual run | Manual run with the automatic top-up as a silent net | In the above |
| Journal | New J system; extend the logbook | Extend the logbook, J opens the "Tonight" page | 2 days |
| Hints | Timers; state-driven with persistence | State-driven, written to the journal | 1 day |

**Fuel run and the Ross lock as explicit states (no conflicting scripted exceptions):**
| State | Set by | Cleared by | Effect |
|---|---|---|---|
| `fuel_low` | chapter 3 start | pumping | sight glass low; duty shown |
| `gen_locked` | chapter 4 `steps` | sediment bowl drained (chapter 5) | engine cannot catch; battery floored |
| overheat lockout (existing) | 100 C | below 60 C | START refused with its reason |
