# THE LAST LIGHT: Document 5: visual and audio improvement plan

> Audit of 2026-11-15 at commit `2b5d3ee`. Paths are relative to `projects/games/last_light/` unless they start with `docs/`, `assets/`, `renders/` or `tools/`; `g/` means `godot/`. Section numbers are those of the approved plan. Index: [README](README.md).

## 9. Boats and ocean

### 9.1 Vessels (new `blender/vessels.py`, exported as `ship_<kind>.glb`, which `ship_view2.gd` already looks for)
| Model | Used by | Character |
|---|---|---|
| Ring-netter MFV, about 15 m | *Kittiwake*, *Corrie May* | Varnished wheelhouse aft, mizzen, net on the stern, registration on the bow |
| The black boat | *Mary Ellen* / *Catriona* | Same yard lines, black hull, older wheelhouse, no lights |
| Schooner, about 19 m | *Gannet* | Two masts, furled sails, deckhouse for passengers |
| East-coast drifter, about 25 m | *Lowestoft Star* | Tall funnel, steadying mizzen, LT number |
| Coaster, about 40 m | *Iona Star*, *Hendrika* | Bridge aft, hatches and derricks; *Hendrika* carries a timber deck cargo and a different hull colour |

- 4 to 6k triangles each, object-space UVs, one material and one 1k set per vessel, navigation and deck lights, registration numbers, weathering.
- Motion per type: heave, pitch and roll periods scaled by length and mass; limited turn rate with bank; hull placed on the same displaced surface the GPU draws; a wake ribbon and bow spray.
- Dedicated binocular QA: every vessel captured at near, middle and far range, outside the glass and through it.

### 9.2 Ocean
- Fix M2 (mask clamp, underlay depth) and M4 (radial mesh density).
- Then, measured one at a time against the bench: storm-driven whitecaps, shore and reef foam from the existing distance field, depth tint near the island, a darker night palette, horizon blend into the fog.
- Larger extent for the far radar range (section 10).
- **Performance rule:** last clean bench was Medium 18.0 / 18.6 / 16.6 ms (desk / window / generator). Re-baseline in Stage 0; no stage may add more than 5% median on Medium without a setting to scale it back.

## 18. Document 5 in full: visual and audio improvement plan

### 18.1 Cabin audit table
| Object | State found | Evidence | Recommendation | Tier |
|---|---|---|---|---|
| Stair door and wheel | Unrotated spokes form a brass square; dogs are painted boxes; nothing animates | `rq7d_t066_cu_door.png` | Section 5 and C4 | P0 |
| Lamp over the door | Overlaps the door top; glare on the leaf | `rq7d_t060*` | Remove (C1) | P0 |
| Supply diagram | Cut by lamp 0's backplate | Code | Move left (C2); make inspectable | P1 |
| Charger cabinet | Right end over the window opening | `rq7_t068_cu_battery.png` | Move left (C3) | P0 |
| Oilskin on the stand | Jagged edges, thin shell | `rq7d_t064_cu_coat.png` | C5 | P2 |
| Telephone | Sound base, little detail | to capture | C6 | P1 |
| Mug and ashtray | Intersect | `rq7f_t062_pp_compass.png` | C7 | P1 |
| Chart dial | Unusable decoy | `g22_cards_crop.png` (old position) | Remove (C8) | P1 |
| Radio-check card | Overlaps the bezel | `rq7_t072_cu_radio.png` | C9 | P1 |
| Binoculars | Clip the phone | Code | C10 | P1 |
| Coat collar | Reads slightly as a cap (known) | handoff note | Fold fixed with the C5 pass | P2 |
| Generator START tag | Partly hidden by the knob rim (known) | handoff note | Lower the tag 8 mm | P2 |
| Conduit-clip shadow near lamp 0 | Streak on the wall (known) | handoff note | Lamp moved in R6; recheck | P3 |
| Everything else | 45 explained contact flags from the last float scan | ROADMAP cabin pass | Re-run the BVH contact scan after Stage B | P2 |

A fresh systematic pass (floating, intersecting, scale, texture resolution, seams) is run as a Blender BVH scan plus a 24-view capture sheet in Stage 0, and its results are appended to this table before Stage B starts.

### 18.2 Materials and textures
- Room stays at its 33-material cap. New garments, Ross and vessels are separate assets with their own budgets.
- One shared knit set; one waxed-cotton set shared by Callum's coat on the stand and Ross's oilskin (different tint and wetness).
- Brass keeps the object-space wear introduced in R5.
- No new 4k textures; 2k for hero items (Ross, the door), 1k elsewhere.

### 18.3 Expected visible gains
Boats that read as specific vessels through binoculars; a sea without artefacts; a stairwell with depth; a Ross who moves and is lit; cloth that reads as cloth; a desk with no intersections.

### 18.4 Audio audit (as built)
| Area | Found | Action |
|---|---|---|
| Sources | 52 WAVs, all synthesised, deterministic; storm audio approved by Daniel on 2026-11-15 | Keep; add recorded CC0 where a human or handled object is heard |
| Radio | No voice, no filter; static, squelch, typing blips | Static dips 6 dB under a message |
| Positional | Loops at devices; one-shots via `sfx_at`; stair footsteps follow the door bearing | Add door-muffle low-pass and a stairwell reverb send |
| Documents | Open and close silently (12 standing test warnings) | `paper_slide` on open, a softer variant on close |
| Music | Section 3.5 | Section 23 |
| Defects on record | `set_menu(false)` never called; `horn_fishing` mastered hot; `click_button` DC offset | Fix in Stage D |

### 18.5 Performance trade-offs
| Change | Expected cost | Control |
|---|---|---|
| Ross figure (25k triangles, skinned, one 2k set) | Small; one skinned mesh in two chapters | Shadow casting only from the two nearest lamps |
| Stairwell lower level | Extra geometry visible only through the door | Hidden when the door is shut |
| Five vessels at 4 to 6k triangles | Below today's fleet cost at range | No shadows beyond 150 m |
| Denser near-field ocean, larger extent | The main risk | Radial density; quality presets scale it |
| Garments | Slight (body visible only looking down) | None needed |
| Two music players, reverb send | Negligible | None |

**Targets (to be confirmed against a fresh Stage 0 bench on Daniel's M3, Auto resolution):** Medium median at or below 16.7 ms and p95 at or below 20 ms at desk, window and generator views; High median at or below 25 ms; no stage adds more than 5% median on Medium; VRAM at or below 1.4 GB (last recorded 1.25 GB); room at or below 125k triangles.
