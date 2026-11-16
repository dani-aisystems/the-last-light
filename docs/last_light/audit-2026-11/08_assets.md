# THE LAST LIGHT: Document 8: asset requirements

> Audit of 2026-11-15 at commit `2b5d3ee`. Paths are relative to `projects/games/last_light/` unless they start with `docs/`, `assets/`, `renders/` or `tools/`; `g/` means `godot/`. Section numbers are those of the approved plan. Index: [README](README.md).

## 11. Asset packs for Daniel

### 11.1 Ross photograph brief
- **Canon:** "Eight men on a deck at Leverburgh pier. The one at the wheel is laughing." Back, in pencil: "Mary Ellen, July 1953. A. Ross, master." and below, in another hand, "Kenny B. on the hatch."
- **Deliver:** front only, 4:3 landscape, 2400 x 1824 px or larger, PNG, to `projects/games/last_light/character-refs/Picture-mary-ellen/mary_ellen_crew_1953.png`. The back, the creases and the silver-print ageing are made by `blender/documents.py` as for the wall photograph; output `godot/assets/docs/photo_1953.png`.
- **Prompt:** "A black-and-white amateur snapshot from July 1953, taken from a stone pier looking slightly down onto the deck of a wooden Scottish motor fishing boat tied alongside at Leverburgh, Isle of Harris. Eight working fishermen aged from about eighteen to sixty pose loosely on deck in wool jerseys, flat caps, braces and sea boots; one sits on the fish-hold hatch; one stands at the wheel inside the open wheelhouse door, head thrown back laughing, his face partly shaded by the wheelhouse roof. Nets, fish boxes and a coiled rope on deck; a low treeless Hebridean shore and still water behind. Bright overcast summer light, soft contrast, slight motion blur on one figure, shallow box-camera sharpness, natural grain, slightly tilted horizon. No text, no lettering, no boat name or numbers visible, no border, no modern objects."
- **Exclude:** colour, visible registration, uniforms, staged studio look, more or fewer than eight men.
- A grey placeholder card labelled "PLACEHOLDER" is used in tests until the file arrives.

### 11.2 Ending image pack
**Verified endings:** four, chosen only by `told_truth` and whether the *Iona Star* was saved. Each plays four panels then a title card. Three log-page panels exist; eight panels are stand-in plates. One new panel is needed to fix the wheel mismatch. **Nine images in total.**

**Common spec for every image:** 16:9 landscape, 3840 x 2160 px, PNG, no text or lettering of any kind, saved to `projects/games/last_light/godot/assets/ending/<id>.png`. Godot draws no text over the images; the last panel is shown smaller beside its lines, so keep the subject in the central 70%. Ross's face is never shown clearly, by standing decision.

**Common style line (append to every prompt):** "Photorealistic still from a restrained historical film drama, Outer Hebrides, Scotland, November 1971. 35 mm film look, natural grain, muted cold palette with warm tungsten or oil-lamp accents, soft contrast, no lens flare, no teal-and-orange grade. Authentic period clothing and equipment, nothing modern. No text, captions, logos or watermarks."

| ID | Shown in | Prompt (scene) |
|---|---|---|
| `p1_wheel` | Any ending where Ross took the wheel | "Close view inside a small round lighthouse watch room at night. Two pairs of hands grip one brass handwheel on a grey-green control console: an old man's large, scarred, wet hands in the cuffs of a black oilskin, and a younger man's hands in dark navy knitted cuffs with a darned repair. Rain-streaked window behind, a warm instrument lamp on the brass, shallow focus on the hands, faces out of frame. 50 mm lens, eye level." |
| `p1_alone` (new) | Any ending where he did not | "Close view inside a small round lighthouse watch room at night. One man's hands in dark navy knitted cuffs grip a brass handwheel on a grey-green control console, knuckles white; a radio handset on a long cord lies beside it. Rain-streaked window behind, one warm instrument lamp, shallow focus, face out of frame. 50 mm lens." |
| `p2_gut` | *Iona Star* saved | "Seen from a high lighthouse gallery before dawn in a storm: a 1950s British coaster about forty metres long, bridge aft, a few deck lights, passing through a narrow gap between black reefs in heavy seas, caught in the white beam of the lighthouse. Spray, low cloud, the first slate-grey light on the horizon. 85 mm lens, high angle." |
| `p2_ledge` | *Iona Star* aground | "Seen from a high lighthouse gallery at first light after a storm: a 1950s British coaster sitting upright and still on a pale sand ledge at the edge of a rocky channel, bow slightly raised, lights on, a small group of figures gathered on the bridge wing, surf breaking round her but the hull intact. Slate sea, mist, no flames, no wreckage. 85 mm lens." |
| `p4_correction` | CORRECTION | "A plain Scottish inquiry room in spring 1972: a long table, a clerk, three men in dark suits. In the foreground a woman in her mid-forties with dark brown hair, in a navy cardigan, reads aloud from a small worn pencil notebook held in both hands. Behind her, out of focus, a lean man of forty-one with greying temples sits upright, looking at the table. Grey window light, wood panelling, 50 mm lens." |
| `p4_heard_together` | HEARD TOGETHER | "The same plain inquiry room. Close view at chair height: an old man's large weathered hand rests on the arm of a wooden chair, a young woman's hand in a dark reefer sleeve holding it firmly. His flat cap lies on his knee. Faces out of frame; behind, out of focus, a table and the backs of listening people. Grey window light, 85 mm lens, shallow focus on the hands." |
| `p4_nothing_tide` | NOTHING TO REPORT, no reunion | "Dawn after a storm, seen from a small stone jetty beneath a white lighthouse: a black-hulled wooden fishing boat with her wheelhouse aft, carrying no lights, heading out on a calm grey tide, one figure in an oilskin at the wheel seen from behind. Long swell, thin mist, pale cold sky, wet stone in the foreground. 50 mm lens." |
| `p4_nothing_pier` | NOTHING TO REPORT, with reunion | "Stornoway harbour pier at night, November 1971, wet cobbles under two sodium lamps, fishing boats moored in darkness. Two small figures stand a pace apart halfway down the pier: a tall stooped old man in a black oilskin and flat cap seen from behind, and a young woman in a dark reefer jacket facing him, her face too distant to read. Wide shot, 35 mm lens, deep shadow." |
| `p4_light_exhibited` | LIGHT EXHIBITED THROUGHOUT | "A plain Scottish inquiry room in 1972. On the table in the foreground lies an open lighthouse station logbook with ruled columns and small neat handwriting, a clerk's finger resting on one line. Behind, out of focus, a lean man of forty-one in a dark jacket sits alone on a bench against the wall, hands on his knees, looking at nothing. Flat grey light, 50 mm lens. The handwriting must be illegible." |

- **References to attach when generating:** Daniel's own character sheets for Callum, Morag and Elspeth; the title-screen lighthouse capture for the tower.
- **Negative list where supported:** text, modern clothing, plastic, radar domes, life jackets in orange, lens flare, fantasy lighting, extra fingers, readable writing.
- **Integration:** files replace the stand-in plates by name; `story_director` picks `p1_alone` when `ross_wheel` is unset. I recommend lowering the print-grade shader from 0.75 to about 0.3 for photographs; judged on captures.
- **Presentation polish:** 1.8 s crossfades; lines appear one at a time at reading pace; music cue per ending (11.3) starting on the first panel and resolving on the title card; room ambience fades out under panel 1 and wind returns under the title; the ending reached is recorded so the menu can show it; credits follow after a 3 s hold on black; no skipping.

### 11.3 Soundtrack
**Route chosen: AI-assisted.** Recorded as a new exception in `docs/architecture/DECISIONS.md` (next Q number), parallel to the image exceptions: Daniel generates and downloads the tracks himself on a paid tier; I supply the cue sheet and prompts, then cut, loop, level and integrate the files he provides.

**Licence facts checked on the service's own pages this session:**
- Suno paid tiers (Pro about $10 a month, Premier about $30): commercial-use rights; ownership of output assigned to the subscriber; output must be downloaded through the service while subscribed. The terms give no warranty that the music is copyrightable and do not mention games.
- Udio: terms could not be read; treat as unusable.
- AIVA Pro (about EUR 33 a month, billed yearly): "copyright owned by you"; the mapping to games is not explicit.
- Keep the subscription receipt and a dated copy of the terms with the files.

**Identity.** One five-note falling motif (D minor, the shape of the existing menu pad), carried by felt piano and a single cello, over low strings and air. Silence is the default state in the watch room.

| Cue | Where | Length, form | Generation prompt core |
|---|---|---|---|
| M01 Title | Main menu | 3:00, loop | Sparse felt piano stating a slow five-note falling motif in D minor, long silences, one sustained cello note entering late, room tone, no percussion, about 50 bpm |
| M02 Arrival | Dusk opening | 1:30, plays once | Low strings swelling very slowly from nothing, a single piano note of the motif every few bars, cold and wide |
| M03 Watch | Chapters 1 and 2, rare | 2:00, loop | Almost-static low string drone with faint harmonics, no melody |
| M04 Weather | Chapter 3 | 2:30, loop, two intensity layers | The drone with slow cello swells and a restless viola tremolo underneath, never loud |
| M05 Mechanism | Jams and blackouts | 1:30, loop | Quiet ticking pizzicato cello and muted low piano strings, mechanical, unresolved |
| M06 The stair | Chapter 4 approach | 2:00, plays once | A single high held string note and distant low piano, mostly silence; uneasy, not horror |
| M07 Ross | Door and chapter 5 | 3:00, loop | Solo cello playing the motif slowly and plainly, tired and warm, a few piano chords beneath |
| M08 The letter | Reveals | 1:00, stinger | Three piano chords and a breath of strings, ending open |
| M09 Decision | Dawn report | 2:00, plays once | Piano alone, the motif unfinished, waiting |
| M10 to M13 Endings | One per ending | 2:30 each | Correction: motif completes in D major, piano and cello together. Heard Together: same, slower, cello alone to the end. Nothing to Report: motif stops one note short over a cold drone. Light Exhibited: low strings only, motif never appears |
| M14 Credits | Credits | 4:00 | The full theme once, piano and cello, then the drone thinning to wind |

- **Fallback if the AI route disappoints or its terms change:** the verified one-composer set (Scott Buckley, CC BY 4.0, credit required) plus two Musopen public-domain recordings (Chopin Cello Sonata Largo for Ross; Nocturne in E minor for the credits). Cost: free.
- **Budget:** $10 to $30 for one or two months of a paid tier. A commissioned score would be roughly $8,000 to $15,000 at surveyed indie rates.
- **Integration (`audio_director.gd`):** two music players for real crossfades (2 to 4 s); a cue table in `chapters.json` (`["music", id, fade]`, `["music_stop", fade]`); ducking under messages; loop points set in import; current cue and position class saved and restored; OGG Vorbis, about -18 LUFS; the never-stopping tension loop retired.

### 11.4 Easter eggs
| Name | Where and trigger | What happens | Why |
|---|---|---|---|
| Fear a' bhàta | Wind the standby clockwork crank in chapter 1 or 2 | Callum hums a bar (caption and a faint hummed line). In chapter 4 Ross says "you used to sing to the clockwork" | Rewards an optional duty with the game's best recurring detail. The song is a traditional 19th-century air |
| In Salutem Omnium | With the torch in a blackout, the brass maker's plate behind the optic pedestal | Readable plate with the Board's motto, "For the safety of all", and a thought | Real NLB motto (to be re-verified); lands differently after chapter 5 |
| The Flannans | A book on the shelf, any time | Callum's line about his two winters there and the three keepers lost in December 1900 | Real event; uses his established posting; quiet dread without the supernatural |
| The second cup | Boil the kettle in chapter 5 | Ross's "the cup I gave him" line at dawn is then literally the player's doing; unused, the line is skipped | Makes a scripted detail earned |
| The bird | Chapter 3, once, high storm | A soft thud on the glass; with binoculars a small seabird is seen sheltering on the gallery rail until dawn | Lighthouses do draw birds in bad weather; a living thing shares the night |

All optional, none carries required information, all derive from saved flags.

### 11.5 Other assets
| Asset | Source | Path | Priority |
|---|---|---|---|
| Portraits for the four new voices | Daniel (or line cards drawn in code) | `character-refs/<id>/` to `godot/assets/portraits/` | Stage C |
| Cough, breath and foley recordings | CC0, shortlist for Daniel's OK | `godot/assets/audio/`, logged in `assets/ASSET_LICENSES.md` | Stage D |
| Vessel, Ross, garment and stairwell models | Built in Blender here | `blender/` to `godot/assets/models/` | Stages S, R, E |
| Document renders (Orders, diagram, tide tables, card, teleprinter sheets) | `blender/documents.py` | `godot/assets/docs/` | Stage B |

## 25. Document 8 in full: asset requirements

| Asset | Purpose | Format and spec | Made by | Scene | Depends on | Licence | Priority |
|---|---|---|---|---|---|---|---|
| *Mary Ellen* crew photograph | Slid under the door; document | PNG, 4:3, 2400 x 1824 or larger | Daniel (AI), aged by `documents.py` | Chapter 4 | none | Daniel-supplied exception (DECISIONS) | Stage R |
| Ending panels x9 | Endings | PNG, 16:9, 3840 x 2160 | Daniel (AI) | Endings | prompts in section 21 | as above | Stage H |
| Score cues x14 | Music | WAV or high-rate MP3 from the service; converted to OGG | Daniel (AI service) | All | prompts in 23.3 | new exception; keep receipt and terms | Stage H |
| Portraits x4 | Radio card | PNG, 4:5, 512 x 640 after preparation | Daniel, or line cards drawn in code | Chapters 1 to 3 | script approval | as existing portraits | Stage C |
| Cough and breath takes | Ross | WAV, mono, 44.1 kHz, 6 to 8 takes | CC0 recordings after Daniel's OK | Chapters 4, 5 | none | CC0, logged | Stage D |
| Foley set | Handling sounds | WAV, mono | CC0 or synthesised | All | none | CC0 or own | Stage D |
| Ross figure | Chapter 4 to 6 | GLB, 25k triangles, 2 materials, 2k set, 10 clips | Built here | Watch room | stairwell | CC0 base mesh | Stage R |
| Stairwell and service landing | Door view, fuel run | GLB | Built here | Stair | none | own | Stage S |
| Garments | Callum | Part of `body.glb`, `hands.glb`; 1k knit set | Built here | All | none | own | Stage P |
| Vessels x5 | Sea | GLB each, 4 to 6k triangles, 1k set | Built here | Exterior | none | own | Stage E |
| Documents | Orders, diagram, tide page, card, teleprinter sheets | PNG via `documents.py` | Built here | Watch room | script text | own; fonts as today | Stage B |
| Hummed phrase | Easter egg | WAV, 4 s | Daniel records, or CC0 | Chapter 1 to 3 | none | own or CC0 | Stage H |
