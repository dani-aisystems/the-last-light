# THE LAST LIGHT: Addendum C: stairwell and door reconstruction

> Audit of 2026-11-15 at commit `2b5d3ee`. Paths are relative to `projects/games/last_light/` unless they start with `docs/`, `assets/`, `renders/` or `tools/`; `g/` means `godot/`. Section numbers are those of the approved plan. Index: [README](README.md).

## 5. Stairwell and door reconstruction (Addendum C)

**Constraint.** The tower's inner wall is 0.65 m behind the door plane, so there is no room for a corridor. The believable space is a landing with a ship's ladder dropping through a floor hatch to the level below.

**Build (`blender/build.py::build_stair`, new `blender/stairwell.py` for the lower level):**
- Inside the housing: remove the room's dado rail, skirting and cream paint; bare whitewashed masonry with conduit and a cable clip run.
- A chequer-plate landing, a properly cut hatch with a raised coaming, and a guard rail on three sides.
- Handrail on stanchions from a newel on the landing; nothing passes through the floor.
- The ladder descends to a **service landing** one flight down: curved masonry, fuel drums on a rack, a semi-rotary hand pump with a line rising to the day tank, the clockwork weight tube passing through, the shut door of the dead main engine room, and the stair continuing down behind a closed storm door.
- Materials: worn painted steel treads, chequer plate, limewashed stone, with roughness and wear; the lower level inside reflection-probe coverage.
- Lighting: the existing pendant plus one bulkhead lamp below; red emergency light in a blackout.
- Door: handwheel turns and dogs lift before the swing; eased open and close; collider follows the leaf; hinge and latch sounds.

**Access.** The player goes through this door only in the scripted fuel run (section 10.4). At other times the prompt gives a reason in Callum's voice, and the door stays shut by story, not by an invisible wall.

**Acceptance.** Open-door captures from three angles show depth, a floor, a rail and no room-wall materials; the white patch and the stick are gone or explained; the player cannot walk through the open leaf.
