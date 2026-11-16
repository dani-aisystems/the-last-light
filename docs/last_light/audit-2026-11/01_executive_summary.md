# THE LAST LIGHT: Document 1: executive audit summary

> Audit of 2026-11-15 at commit `2b5d3ee`. Paths are relative to `projects/games/last_light/` unless they start with `docs/`, `assets/`, `renders/` or `tools/`; `g/` means `godot/`. Section numbers are those of the approved plan. Index: [README](README.md).

## Context

Daniel sent a 19-phase brief and an addendum asking for a full audit of THE LAST LIGHT and a plan to raise its narrative, presentation, interactions, environment and technical quality, without rebuilding it. Nothing may be implemented before he approves the plan. This file is that plan. It was produced read-only: code, data, Blender sources, the project record and existing captures were read; no game file was changed.

**What this audit is and is not.**
- Causes below marked **Code** were traced to a mechanism in the source. **Capture** means an existing screenshot shows it. **Unconfirmed** means it still needs a windowed run.
- **No windowed playthrough was run in this session** (plan mode is read-only). Boats through binoculars, the sea patches, the open door, the sitting glimpse and all audio are therefore not yet verified on screen or by ear. Stage 0 does that first, before any fix.
- Runtime has never been measured. The design estimate on record is 85 to 105 minutes.

**Decisions Daniel has already made in this session (2026-11-15):**

| Topic | Decision |
|---|---|
| Ross encounter | Hybrid: polished through-the-door scene if the door stays shut; if opened, a modelled and animated Ross enters, face kept in shadow by the sou'wester |
| Story expansion | Balanced (about +150 to 200 lines, +20 to 30 minutes) |
| New voices | All four: Visser (*Hendrika*), Gillies (*Sula*), Dr Marsh (*Western Venture*), a neighbouring keeper |
| Beyond the cabin | A scripted stairwell fuel run, one flight down, indoors |
| Soundtrack | AI-assisted score |
| Cough and handling sounds | CC0 recordings, downloaded only after he approves the list |
| Radar | Three-position range switch |

**How this file is organised.** Part I (sections 1 to 14) is the plan. Part II (sections 15 onward) holds the full deliverables Daniel asked to read before any work: the evidence appendix with file references, the complete narrative proposal, the Ross storyboards for all three variants, the ending image pack, the soundtrack proposal, the per-stage roadmap detail, the asset list and the test matrix. On approval, Stage 0 copies Part II into `docs/last_light/audit-2026-11/` as separate documents and adds the captures.

**Rules that stay in force:** generated files only via `blender/pipeline.sh`; no pushes; ask before deleting, overwriting, downloading or opening a Godot window (silent `tools/godot_bg` runs need his OK per batch); benches only when the Mac is free; I do not call AI-generation services myself.

## 1. Executive summary

**Strengths.** A coherent, grounded story with four earned endings; a data-driven story system (`.dlg` files, `chapters.json`, `StoryDirector`) with strong headless coverage (story, regress 362 checks, opening, interaction, qa sweep); a detailed, period-correct watch room; a working station simulation; a document viewer with zoom and pan; a dialogue history screen.

**Most serious problems found.**
1. Every boat at sea is a code-built stand-in whose hull faces point inward, so the near side and deck vanish (Code; binocular capture still needed).
2. Ross is cylinders and a sphere with a 5% black coat and all lamps behind him; he appears instantly, never moves and stands on one spot through chapters 5 and 6 while the script has him lean on the chair, take the wheel and set down a cup (Code + Capture).
3. The open stair door shows the room's own cream wall 0.65 m behind it; the handrail rises out of solid floor and ends in mid-air; the door's collider stays in the doorway after it opens (Code).
4. Dialogue can be skipped with Space; radio lines wait for Space forever, and while one waits, pressing E on some objects silently does nothing (Code).
5. The Tide Tables were never a document; E plays a thought that is dropped whenever any conversation is open (Code).
6. No cough sound exists, only a caption. Nothing stops the generator being started during the Ross sequence (Code).
7. The sea shows island-shaped teal patches about every 520 m (the shore mask repeats) and a flat plane showing through wave troughs (Code; capture needed).
8. Callum's "clothing" is the body mesh pushed out 10 mm and coloured: no shirt, no collar, no garment volume, three different navies on screen (Code + Capture).
9. Sitting at the radio shows a headless, armless torso on the chair for 0.1 to 0.2 s, because the body is seated one frame before the camera starts moving (Code).
10. Music: one tension loop starts in chapter 4 and never stops, is not saved, and is cut dead at the credits (Code).

**Recommended direction.** Fix the reliability and readability defects first (dialogue, documents, generator state, UI), then rebuild the three weak set-pieces as complete sequences (stairwell and door, Ross, boats and sea), then widen the night (story, voices, radar, fuel run), then finish with endings, score and a full QA pass. Estimated total: 75 to 90 working days, in 12 approval-gated stages (section 12).

## 14. Still open for Daniel
1. Whether the endings' print-grade look is reduced for photographic panels (recommended).
2. Portraits or line cards for the four new voices.
3. The neighbouring keeper's name and station (proposed: Murdo MacAskill, a fictional light to the south).
4. Automatic journal "Notes" in Callum's voice (Proposal 37), now or later.
5. Generator lock length: through Ross's account and the letter (planned), or the stair and door scene only.
6. The Grant's bottle thought: on first look at the Tide Tables in any chapter (today's behaviour) or only from chapter 4.
