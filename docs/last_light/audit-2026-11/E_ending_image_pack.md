# THE LAST LIGHT: Addendum E: ending image production pack

> Audit of 2026-11-15 at commit `2b5d3ee`. Paths are relative to `projects/games/last_light/` unless they start with `docs/`, `assets/`, `renders/` or `tools/`; `g/` means `godot/`. Section numbers are those of the approved plan. Index: [README](README.md).

## 21. Addendum E in full: ending image production pack

### 21.1 Audit of the endings as implemented
| | 1 CORRECTION | 2 HEARD TOGETHER | 3 NOTHING TO REPORT | 4 LIGHT EXHIBITED THROUGHOUT |
|---|---|---|---|---|
| Condition | truth told, *Iona Star* saved | truth told, aground | lie kept, saved | lie kept, aground |
| Outcome | New inquiry; Ross dies in August, buried under his own name | Both inquiries heard together; Ross gives evidence from a chair | Ross leaves on the morning tide; the finding stands | A second inquiry believes the log |
| Variants | letter given or kept; confessed to Ross or blamed father (log page wording) | same log variants | reunion or not; letter given | letter given |
| Reachable | yes (story_test campaign) | yes | yes | yes |
| Existing art | log page only | log page only | log page only | log page only |
| Card title | C O R R E C T I O N | H E A R D   T O G E T H E R | N O T H I N G   T O   R E P O R T | L I G H T   E X H I B I T E D   T H R O U G H O U T |
| Closing lines (all) | "North Point Light. Fifteenth of November, nineteen seventy-one." / "The light was kept." | | | |
| Audio now | whatever loop was playing | same | same | same |
| Length now | about 60 to 80 s (estimate from timings) | | | |
| Faults | wheel panel shown regardless; longest title may overflow its column (to capture) | | | |

Timings in code: fade to warm black 2.4 s; panels crossfade 1.2 s; panels 1 and 2 hold 9 s, the log page 12 s, panel 4 holds 6 s plus its lines; title card fades in over 1.4 s. No text is ever drawn over an image.

### 21.2 Shared specification
- **Aspect and size:** 16:9 landscape, 3840 x 2160 px (the game scales down). The panel slot is 1536 x 907 px at 1080p, so 16:9 fits with thin margins; panel 4 is shown at about 1056 px wide beside its lines.
- **Typography:** none in the image. Godot renders every title and line outside the picture, so no text safe area is needed; keep the subject within the central 70% so the smaller panel-4 display still reads.
- **Continuity:** the same grey-green console, brass handwheel and rain-streaked windows as the game; the same coaster; attach Daniel's character sheets for Callum, Morag and Elspeth and a title-screen capture of the tower as references.
- **Ross:** never a readable face. Hands, back, or distance only.
- **Style block, appended to every prompt:** "Photorealistic still frame from a restrained historical film drama set in the Outer Hebrides, Scotland, in November 1971. Shot on 35 mm film with natural grain, muted cold palette with small warm tungsten accents, soft contrast, gentle halation, no lens flare, no teal-and-orange grading. Period-accurate clothing, materials and equipment; nothing modern. Natural, unposed, emotionally restrained. 16:9 landscape, very high detail. No text, captions, lettering, logos, borders or watermarks anywhere in the image."
- **Negative list (where the tool supports one):** text, letters, numbers, watermark, modern clothing, plastic, hi-vis, radar dome, satellite dish, LED light, lens flare, fantasy, ghost, glowing, dramatic god rays, oversaturated, cartoon, extra fingers, deformed hands, duplicate people.

### 21.3 Shared panels
**S1. `p1_wheel.png`** (panel 1 of any ending in which Ross took the wheel)
- *Concept:* two generations of hands on the wheel that failed in 1953.
- *Prompt:* "Close view inside the small round watch room of a Scottish lighthouse at night during a storm. Two pairs of hands grip one brass handwheel, about forty centimetres across, mounted on a grey-green enamelled steel control console with round brass-rimmed gauges. The nearer hands are an old seaman's: large, scarred, wet, knuckles swollen, emerging from the cuffs of a soaked black oilskin coat. Beside them a younger man's hands in dark navy knitted wool cuffs, one cuff neatly darned, hold the same wheel. Both men are cropped at the forearm; no faces are in frame. Behind the console a rain-streaked window is black with night, faintly swept by a pale beam. One small warm instrument lamp lights the brass and the wet skin from the left; the rest falls into shadow. Eye-level, 50 mm lens, shallow depth of field with focus on the hands and wheel rim, the wheel slightly left of centre." + style block.
- *Integration:* shown when `ross_wheel` is set.

**S2. `p1_alone.png`** (new; panel 1 when he did not)
- *Concept:* the same wheel, one man.
- *Prompt:* "Close view inside the small round watch room of a Scottish lighthouse at night during a storm. One man's hands in dark navy knitted wool cuffs, one cuff neatly darned, grip a brass handwheel about forty centimetres across on a grey-green enamelled steel control console with round brass-rimmed gauges; the knuckles are white with effort. A black Bakelite radio handset on a long coiled cord lies on the console beside the wheel. The man is cropped at the forearm; no face is in frame. Behind, a rain-streaked window black with night, faintly swept by a pale beam. One small warm instrument lamp lights the brass and the hands from the left. Eye-level, 50 mm lens, shallow depth of field, focus on the hands, wheel slightly left of centre, empty shadow to the right." + style block.
- *Integration:* new entry in `g/data/ending/panels.json`; chosen in `story_director.gd` when `ross_wheel` is unset.

**S3. `p2_gut.png`** (panel 2 when the *Iona Star* is saved)
- *Prompt:* "High view from the gallery of a lighthouse just before dawn in a full Atlantic storm. Below, a 1950s British motor coaster about forty metres long, black hull with a rust-streaked white superstructure and bridge at the stern, two derricks and closed cargo hatches, a few yellow deck lights burning, is passing through a narrow channel between two lines of black, wave-washed reef. The white beam of the lighthouse lies across the water and holds on the ship. Heavy grey-green seas, spindrift, low torn cloud, the first slate-grey light along the horizon. A strip of wet iron gallery railing in the bottom foreground. 85 mm lens, looking down at about thirty degrees, the ship in the centre third heading left to right, safely clear of the rocks." + style block.

**S4. `p2_ledge.png`** (panel 2 when she grounds)
- *Prompt:* "High view from the gallery of a lighthouse at first light after a storm. Below, a 1950s British motor coaster about forty metres long, black hull, white superstructure and bridge at the stern, sits upright and motionless on a pale sand ledge at the edge of a rocky channel, her bow slightly raised, deck lights still burning. About a dozen small figures in dark coats stand together on the bridge wing. Surf breaks white around the hull but the ship is whole: no fire, no smoke, no wreckage, no listing. Slate-coloured sea, thinning rain, mist over the water, a strip of wet iron gallery railing in the bottom foreground. 85 mm lens, looking down at about thirty degrees, the ship in the centre of frame." + style block.

### 21.4 ENDING 1 — CORRECTION
- **Story significance:** Callum corrects the 1953 entry on the air and the ship is saved. The record is put right while Ross is alive to hear it.
- **Panels:** S1 or S2; S3; the existing correction log page; `p4_correction.png`.
- **Visual concept:** Morag reading her eighteen-year-old notebook into the record. The truth belongs to her as much as to him.
- **Why this frame:** the epilogue's first line is "It took eleven minutes to read Morag's notebook into the record."
- **Prompt (`p4_correction.png`):** "A plain wood-panelled public inquiry room in a Scottish town in the spring of 1972. In the foreground, slightly left of centre, a woman of forty-four with dark brown hair pinned back, grey-green eyes, no glasses, wearing a navy cardigan over a cream blouse, stands at a long table reading aloud from a small, worn, pencil-written notebook held open in both hands; her expression is steady and controlled. Across the table three men in dark suits listen, one writing. Behind her and out of focus, a lean, clean-shaven man of forty-one with short brown hair greying at the temples sits upright on a wooden chair in a dark jacket, white shirt and plain tie, looking down at his own hands. Tall windows on the right give flat grey daylight; a brass desk lamp is unlit. Eye-level, 50 mm lens, medium shot, focus on the woman and the notebook, the handwriting too small to read." + style block.
- **References:** Morag and Callum character sheets.
- **File:** `g/assets/ending/p4_correction.png`, 3840 x 2160.
- **Audio:** cue M10: the five-note motif completes for the first time and resolves in D major, piano and cello together; starts under panel 1, final chord on the title card.
- **Timing:** panels 1 and 2 hold 10 s each; log page 14 s; panel 4 holds through its three or four lines at reading pace; 1.8 s crossfades; title card after 2 s of black.

### 21.5 ENDING 2 — HEARD TOGETHER
- **Story significance:** the truth is told but the ship grounds; nobody is lost. The old inquiry and the new are heard as one, and Ross lives to hear it.
- **Panels:** S1 or S2; S4; the correction log page; `p4_heard_together.png`.
- **Visual concept:** a daughter holding her father's hand through a day of evidence.
- **Why this frame:** "Ross gave his evidence from a chair. Elspeth sat beside him and held his hand the whole day."
- **Prompt (`p4_heard_together.png`):** "Close view at chair height in a plain wood-panelled public inquiry room in Scotland in 1972. An old man's large, weathered, liver-spotted hand rests on the arm of a plain wooden chair; a young woman's hand, emerging from the sleeve of a dark navy reefer jacket, is closed firmly over it. A worn tweed flat cap lies on the old man's knee, on dark serge trousers. Both figures are cropped at the chest: no faces are in frame. Behind them, far out of focus, the edge of a long table and the dark backs of seated people. Flat grey window light from the left, a faint warm reflection on the chair's worn varnish. 85 mm lens, very shallow depth of field, focus on the two hands, placed just right of centre." + style block.
- **References:** Elspeth's character sheet for the jacket.
- **File:** `g/assets/ending/p4_heard_together.png`.
- **Audio:** cue M11: the motif, slower, cello alone carrying it to the end; no piano in the last phrase.
- **Timing:** as ending 1; panel 2 (the ledge) held 12 s.

### 21.6 ENDING 3 — NOTHING TO REPORT
- **Story significance:** the ship is saved and the lie is kept. Callum does his duty well and stays silent; present courage does not undo past silence.
- **Panels:** S1 or S2; S3; the "Light exhibited throughout" log page; `p4_nothing_tide.png` (no reunion) or `p4_nothing_pier.png` (reunion).
- **Visual concept, no reunion:** the black boat leaving, unlit, as she came.
- **Why:** "Ross left with the morning tide in the black boat."
- **Prompt (`p4_nothing_tide.png`):** "Dawn after a storm, seen from a small wet stone jetty at the foot of a white lighthouse on a low Hebridean island. A black-hulled wooden motor fishing boat about fifteen metres long, with a small wheelhouse at the stern and a short mizzen mast, showing no lights, is heading out to sea on a long grey swell, seen from astern and already eighty metres off. One figure in a black oilskin and sou'wester stands at the wheel, back to the camera, small in the frame. Thin mist on the water, a pale cold sky with a faint band of light at the horizon, gulls absent, the sea the colour of slate. Wet stone and an iron mooring ring in the bottom foreground. 50 mm lens, eye level, the boat just right of centre with open water to the left." + style block.
- **Visual concept, reunion:** father and daughter on the pier, seen from too far to hear.
- **Why:** "Elspeth met him on the pier at Stornoway that night. I heard it from Morag, not from either of them."
- **Prompt (`p4_nothing_pier.png`):** "Stornoway harbour pier at night in November 1971, wet granite setts shining under two widely spaced sodium lamps, wooden fishing boats moored in darkness along the left, stacked fish boxes and a bollard in the foreground. Halfway down the pier, small in the frame, two figures stand a pace apart: a tall, stooped old man in a black oilskin and tweed flat cap seen from behind, and facing him a young woman in a dark navy reefer jacket and roll-neck jumper, her face too distant and too shadowed to read. Neither is touching the other. Light rain, haloes round the lamps, black water. 35 mm lens, wide shot from low on the pier, the figures on the centre line." + style block.
- **Files:** `g/assets/ending/p4_nothing_tide.png`, `g/assets/ending/p4_nothing_pier.png`.
- **Audio:** cue M12: the motif stops one note short, over a cold string drone; a carrier click, with no voice, is the last sound before the title card (the epilogue's "a carrier with no voice on it").
- **Timing:** as ending 1; 3 s of silence before the title.

### 21.7 ENDING 4 — LIGHT EXHIBITED THROUGHOUT
- **Story significance:** the ship grounds and the lie is kept. A second inquiry reads his log and believes it. "People always believe the light."
- **Panels:** S1 or S2; S4; the "Light exhibited throughout" log page; `p4_light_exhibited.png`.
- **Visual concept:** the book believed, the man alone.
- **Why:** "They read my log into the record. Light exhibited throughout. They believed it."
- **Prompt (`p4_light_exhibited.png`):** "A plain wood-panelled public inquiry room in Scotland in 1972. In the foreground, sharp, a large lighthouse station logbook lies open on a dark table: ruled columns, small neat fountain-pen handwriting too fine to read, a clerk's forefinger resting on one line, the cuff of a dark suit. Behind, well out of focus, a lean, clean-shaven man of forty-one with greying temples, in a dark jacket and tie, sits alone on a bench against the panelled wall with his hands on his knees, looking at nothing. The benches beside him are empty. Flat, cold grey window light from the right; no lamp is lit. 50 mm lens, low angle across the table top, focus on the book in the lower left, the man small in the upper right." + style block.
- **File:** `g/assets/ending/p4_light_exhibited.png`.
- **Audio:** cue M13: low strings only; the motif never appears.
- **Timing:** as ending 1; the log page held 16 s.

### 21.8 Integration and polish
- Files replace the stand-in plates by name; no code is needed beyond the `p1_alone` selection.
- Print-grade shader: lower from 0.75 to about 0.3 for the photographs (judged on captures).
- Record the ending reached in settings so the menu can show it; today nothing is recorded.
- Fade the room ambience out under panel 1; bring wind alone back under the title card; hold 3 s of black before the credits; crossfade to the credits cue (today the audio is cut).
- No input advances or skips anything. Pause still works.
- Verify the longest title fits its column at all aspect ratios.
