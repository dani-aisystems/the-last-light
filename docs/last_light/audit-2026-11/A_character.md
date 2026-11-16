# THE LAST LIGHT: Addendum A: character visual refinement

> Audit of 2026-11-15 at commit `2b5d3ee`. Paths are relative to `projects/games/last_light/` unless they start with `docs/`, `assets/`, `renders/` or `tools/`; `g/` means `godot/`. Section numbers are those of the approved plan. Index: [README](README.md).

## 4. Character visual refinement (Addendum A)

### 4.1 Clothing
**Found.** `blender/body.py` colours body faces by height and pushes them out 7 to 12 mm. There is no shirt, collar, hem or cuff on the body; arms and head are shadow-only. The first-person sleeve (`hands.py`) is a rigid tube weighted to the hand bone, in a different navy (#272B33) from the body (#343A46) and from the knitted gansey on the chair (#323C58). No texture maps exist on either mesh. A good procedural 2x2 rib knit already exists in `documents.py` but is used only on the chair prop.

**Plan.**
1. Guernsey as its own garment mesh over the torso and arms: cloth-draped once in Blender (the `coat_cloth.py` method), 6 mm thickness, ribbed hem, cuffs and neckband, shoulder seams.
2. Shirt: collar points and 1.5 cm of cuff showing, pale worn cotton with a fine weave normal.
3. Trousers as a garment with volume and a break over the boot; boots given real UVs.
4. One tileable knit set (albedo, normal, roughness, 1k) generated from the existing rib code, shared by body, sleeves and chair gansey, so there is one navy.
5. First-person sleeves: add forearm and elbow bones so the sleeve bends and bunches with each grip; keep the darn.
6. Check whether Godot keeps the glTF sheen; if not, a small fabric shader with a rim term.

**Evidence to capture (before and after):** neutral arms, an interaction, movement, the sit transition, warm cabin light.

### 4.2 Sitting glimpse
**Cause (Code).** On the frame E is pressed, `player._process` runs first and leaves the camera at standing height; `PlayerBody._process` then seats the body on the chair and shows it. For about 0.1 to 0.2 s the camera looks at a body it has not reached, blending from standing to sitting, with no head or arms.

**Fix.** Position the body from the camera's current blended eye every frame, not from the target seat, and drive the sit pose by the same blend value, so the body is always under the camera. Stand-up runs the same in reverse. No fade.

**Tests.** regress: across the whole blend the body's head bone stays within 5 cm of the camera horizontally; repeated sit/stand, rapid E during the blend, sit after a document, sit after a radio call, load while seated, stepped at 30, 60 and 120 fps.
