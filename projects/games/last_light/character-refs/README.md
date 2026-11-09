# THE LAST LIGHT: character references

These are the persistent character references for *THE LAST LIGHT* (North Point Light, Outer Hebrides, 14–15 November 1971). Each character has two things:

- **a written profile** (`<id>/PROFILE.md`), which is the authority for facts;
- **a visual dossier** (the `.png` in the same folder), which guides visual interpretation only.

**Status (2026-11-06):** consolidation is in progress. Daniel is supplying material in batches. Profiles marked **DRAFT** are not final until he sends "ALL CHARACTER INFORMATION PROVIDED".

## Contents

| File | What it is |
|---|---|
| [CANON_INDEX.md](CANON_INDEX.md) | The single source of truth. It holds the timeline (1953 and 1971), ages, identities, family links, who knows what and when, the order of discoveries, the in-game documents word for word, the endings and their dependencies, the period rules and the visual-consistency rules |
| [REVIEW_FLAGS.md](REVIEW_FLAGS.md) | Contradictions and missing information. Each flag has an ID, its sources, the current position (status quo) and a field for Daniel's ruling |
| [sources/](sources/) | Daniel's material exactly as received, one file per batch, for provenance |
| `callum/` `morag/` `rory/` `elspeth/` `ross/` `iain/` | The six principal characters: profile plus dossier image |
| `hector/` | Hector Macleod: a secondary profile, built from existing canon only |

| Character | Profile | Visual reference | Status |
|---|---|---|---|
| Callum Mackay | [callum/PROFILE.md](callum/PROFILE.md) | [dossier](<callum/Callum Mackay_ Lighthouse Keeper Profile.png>) | DRAFT: bible (batch 01) + dossier + canon |
| Morag Fraser | [morag/PROFILE.md](morag/PROFILE.md) | [dossier](<morag/Morag Fraser_ The Last Light Character Bible.png>) | DRAFT: bible cut off at §10 ch4 (G01) + dossier + canon |
| Ruaridh "Rory" Bain | [rory/PROFILE.md](rory/PROFILE.md) | [dossier](<rory/The Last Light_ Rory Bain Character Bible.png>) | DRAFT: dossier + canon |
| Elspeth Ross | [elspeth/PROFILE.md](elspeth/PROFILE.md) | [dossier](<elspeth/Elspeth Ross Character Bible Dossier.png>) | DRAFT: dossier + canon |
| Alasdair Ross / "Sandy Morrison", the Visitor | [ross/PROFILE.md](ross/PROFILE.md) | [dossier](<ross/The Visitor_ Alasdair Ross Character Bible.png>) (silhouette panels only) | DRAFT: dossier + canon |
| Iain Mackay | [iain/PROFILE.md](iain/PROFILE.md) | [dossier](<iain/The Last Light_ Iain Mackay Dossier.png>) | DRAFT: dossier + canon |
| Hector Macleod (secondary) | [hector/PROFILE.md](hector/PROFILE.md) | none supplied (G03) | DRAFT: canon only |

**Conflicts:** all were resolved on 2026-11-06 at Daniel's instruction ("resolve any conflicting information … based off the AI generated as reference"):
- the dossiers decide looks, personality, voice and backstory the game doesn't contradict;
- text already shipped in the game decides plot facts.

Rules and per-item rulings are in REVIEW_FLAGS. Follow-up asset and game-text changes are listed in REVIEW_FLAGS §D and are **not applied** yet.

**The dossier images are local-only (untracked in git).** They total about 19 MB, aren't under Git LFS, and the repository has been pushed publicly once. The text references are committed; the links resolve on this machine. Ask Daniel before tracking or publishing the images.

## Precedence: which source wins

1. **Daniel's explicit rules and decisions.** This includes the rules in his consolidation brief, for example *"Alasdair Ross is never shown in a full portrait and appears only as a silhouette."*
2. **Approved, implemented canon:**
   - `../STAGE3_NARRATIVE_MASTER.md` (APPROVED, including §21);
   - the shipped dialogue in `../godot/data/story/*.dlg`;
   - the in-game documents in `../godot/assets/docs/docs.json`.

   Exact in-game wording lives here.
3. **Daniel's character bible text** (`sources/`) **and the dossier images.** By Daniel's instruction of 2026-11-06, the dossiers are the primary reference for:
   - appearance, wardrobe, personality and voice;
   - any backstory the shipped game doesn't contradict.

   This overrides look details that exist only in the master. Text printed inside the images (logs, letters, timelines, sample lines) is used only where it agrees with 1–2. Other characters' small faces in the relationship panels are not reference, and Ross's least of all.

   The images appear to be AI-generated. Use them as reference only, and never ship them or trace them into game assets (CLAUDE.md: no AI-generated images in the game). The shipped radio portraits are a separate, later set Daniel made from one template (DECISIONS Q13), not these dossiers.
4. `../NARRATIVE.md`: the earlier draft. It is superseded wherever the master differs.

## Tags used in the profiles

| Tag | Meaning |
|---|---|
| `[CANON]` | Approved master or in-game text. The source is given as `file:line` |
| `[BIBLE]` | Daniel's bible text that is consistent with canon. Treat as established |
| `[COND]` | True only on some player paths. The condition is given |
| `[PROPOSAL]` | Suggested but not accepted. Never use it in game text without Daniel's approval |
| `[FLAG-Fnn]` | Disputed. See REVIEW_FLAGS before using it |

Source shorthand:
- `M:123` = `STAGE3_NARRATIVE_MASTER.md` line 123;
- `ch3:66` = `godot/data/story/ch3.dlg` line 66;
- `docs:log_1953` = the `docs.json` entry;
- `B01 Callum §8` = `sources/batch-01.md`, Callum section 8.

## Keeping it in sync

Run `tools/py projects/games/last_light/character-refs/tools/refs_check.py --sync` after any change to `docs.json`, a `.dlg` line quoted here, or these files. It refreshes the document texts in CANON_INDEX §6 and checks links, flags, sections, quotes and ages.

## How future sessions should use this

- **Before writing dialogue:**
  - read the speaker's PROFILE §D (voice) and §I (knowledge);
  - read the CANON_INDEX knowledge matrix for the chapter;
  - check that the line doesn't let the character know something before they could.
- **Before modelling or rendering a character** (3C portraits and busts):
  - read PROFILE §G and the dossier;
  - read the CANON_INDEX visual rules;
  - check REVIEW_FLAGS for open visual flags.
- **Before touching a document prop** (logs, letters, notes): copy its wording from the CANON_INDEX documents section. Never paraphrase a document.
- **When canon changes:**
  - update CANON_INDEX first, then the profiles;
  - add a dated line to each file's change log;
  - close or open the matching flag.
- **Never promote a `[PROPOSAL]` or a `[FLAG]` item to `[CANON]` without Daniel's ruling.**
