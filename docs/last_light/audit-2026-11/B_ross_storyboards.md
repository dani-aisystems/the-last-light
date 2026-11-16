# THE LAST LIGHT: Addendum B: the Ross encounter

> Audit of 2026-11-15 at commit `2b5d3ee`. Paths are relative to `projects/games/last_light/` unless they start with `docs/`, `assets/`, `renders/` or `tools/`; `g/` means `godot/`. Section numbers are those of the approved plan. Index: [README](README.md).

## 6. Ross encounter (Addendum B)

### 6.1 What the scene is for
Alasdair "Sandy" Ross, 64, is the drowned skipper come back for one page in a book and to see his daughter's ship past the Gut. The script moves him from accuser to witness to ally ("Keeper", then "the boy", then "Callum"). The player should feel dread on the stair, then recognition, then pity and obligation. He is exhausted and ill, never a threat and never supernatural. His name stays hidden until he gives it.

### 6.2 The three variants compared

| | A: stays outside | B: enters and sits, full face | C: entry only at the ending |
|---|---|---|---|
| Narrative | Keeps the mystery; breaks chapters 5 and 6 where he is in the room and at the wheel | Strongest contact; contradicts "He won't take the chair" and the silhouette ruling | Needs a new ending condition; endings today depend only on truth and the *Iona Star* |
| Emotion | Voice and sound carry it | Highest if the face convinces, lowest if it does not | Delays the relationship the last two chapters rest on |
| Character work | None | Face, expressions, walk, sit | As B |
| Effort | 3 to 4 days | 15 to 25 days | 20+ days plus story rework |
| Risk | Reads as a workaround in the open-door path | Uncanny face | Canon and softlock risk |

**Chosen: hybrid.** The script already has both paths, so both are staged properly.

### 6.3 Generator lock (both paths)
- **State:** two saved sim fields, `gen_locked` and `batt_floor`, set and cleared by new story faults `gen_out` and `gen_restore` (`keeper_sim.trigger_fault`). Old saves load unlocked.
- **Why a battery floor is required:** at lamp NORMAL the cells drain about 0.59% a second, so a full battery lasts under three minutes without the engine. While locked the battery cannot fall below 30%, so radio, lights and radar keep working and the chapter cannot soft-lock.
- **Start:** chapter 4, first action of the `steps` beat, three seconds before the first footstep on the jetty. The engine hunts, runs down and stops. Callum: water in the sediment bowl, stirred up by the night's pumping.
- **During:** START turns the starter for 2.5 s with the existing dry-crank sound, then dies, and Callum thinks one line (non-blocking, so the timed footsteps are not stretched). The generator panel reads accordingly; the hum is gone; room lights sag slightly. The test bot is taught not to crank while locked.
- **End:** chapter 5, after the letter beat: a new step, drain the sediment bowl (a small valve on the fuel line), clears the lock. The floor stays until the engine has run once. The scripted chapter 5 MAIN trip and restart follow as written; the scripted overheat applies only if the engine is running by then, and its hint is reworded for the other case.
- **Scope note:** this keeps the generator dead from the stair through Ross's whole account and the letter, which is longer than the stair alone. Ending the lock at the door would leave the cells at the floor through the longest conversation in the game.
- **Tests:** lock while running leads to stop; cranking never catches at any beat in the interval, on both door paths; 900 s at lamp HIGH never drops below the floor; save and load at each beat keeps the lock; the bot still finishes chapters 4 to 6.

### 6.4 Storyboard, door kept shut
| Beat | Screen | Sound |
|---|---|---|
| Approach | Player free in the room; warm light grows in the 20 mm gap under the door as he climbs | Jetty steps, base door far below, the first cough two floors down (muffled, long reverb), steps one at a time, breath, silence, three knocks |
| Talk | A shadow breaks the light in the gap; the wheel is tried once from outside and released | Voice lines as text; breathing between them; second cough at the door, close and dry |
| Photograph | A corner of card appears in the gap, pauses, then slides 30 cm onto the floor, face down; turning it over is the pickup | Paper on concrete |
| Chapter 5 | Callum sits against the door (camera low); the shadow in the gap shifts as Ross sits on the top step | Through-door voice bed |
| Dawn | Light in the gap dims as he goes down | Footsteps descending |

About 4 to 5 minutes for the chapter 4 scene.

### 6.5 Storyboard, door opened
| Beat | Blocking | Light |
|---|---|---|
| Open | Wheel turns, dogs lift, door swings. Ross is already there: one hand on the rail, head down, rain running off the brim. He waits until the player steps aside | Stair pendant behind as a rim; wall lamp 2 as a side key on the oilskin, hand and jaw |
| Enter | Two slow steps in, hand to the door frame, stops just inside; water pools at his boots | Brim keeps eyes and upper face in shadow; stubble and cheek edge catch the light |
| Chapter 5 | Stands, then rests a hand on the chair back, as written; coughs turned away; shifts weight; looks at the photograph on the wall once | Unchanged warm room |
| Chapter 6 | Crosses to the console and takes the handwheel if given it; otherwise stays by the chair | Console instrument light on his hands |
| Dawn | Sets down the cup on the desk; on the lie endings, turns and goes down the stair | Dawn through the windows |

### 6.6 The figure
- Built in a new `blender/ross.py` from the CC0 male base mesh already in the project, aged and stooped; black oilskin draped by cloth simulation with wet roughness and beading on the shoulders; sou'wester with a real brim; knotted scarf; large worn hands; sea boots.
- Rig reused from `body.py`. Clips: breathe-idle, weight shift, cough (two variants), two-step walk, hand-to-chair, turn, wheel grip, set-down. No facial animation; the face is modelled to hold up in shadow only.
- Budget: 25k triangles, two materials, one 2k texture set.
- The radio card stays the silhouette print. Name display rules in `speakers.gd` are unchanged.

## 20. Addendum B in full: Ross, three storyboards

### 20.1 Variant A, he stays outside (reference only; not chosen)
| # | Scene | Camera | Blocking | Dialogue and interaction | Light | Sound | Time |
|---|---|---|---|---|---|---|---|
| 1 | The climb | Player free | None visible | Thoughts as written | Warm light grows under the door | Steps, cough, breath | 40 s |
| 2 | Knocks | Player free | Shadow in the gap | Choices as written | Gap light broken by boots | Three knocks | 20 s |
| 3 | The talk | Player free | Door on a short chain, opens a hand's width if "open" is chosen | Existing door conversation | A slice of stair light across the floor | Voice through the gap | 3 to 4 min |
| 4 | Photograph | Player free | Card slides in | Pick up, turn over | Unchanged | Paper | 20 s |
| 5 | Chapters 5 and 6 | Player seated against the door | He sits on the top step | Lines rewritten: no chair, no wheel, no cup | Unchanged | Through-door bed | as chapter |

Impact: mystery kept; the "two men to one wheel" image, the cup and the reunion handset are lost or rewritten. Effort 3 to 4 days plus about two days of script changes.

### 20.2 Variant B, he enters and sits, full face (reference only; not chosen)
| # | Scene | Camera | Blocking | Light | Sound | Time |
|---|---|---|---|---|---|---|
| 1 | Open | Player free | He stands on the landing, looks up | Face lit by wall lamp 2 | Rain off the oilskin | 10 s |
| 2 | Enter | Player free | Crosses 2.5 m to the desk chair | Room light | Boots, breath | 12 s |
| 3 | Sit | Player free | Lowers himself, hand on the desk | Desk lamp on his face | Chair, cough | 6 s |
| 4 | The account | Player free | Seated, small gestures, facial expression | Unchanged | Voice | 8 to 10 min |
| 5 | The wheel | Player free | Stands, crosses to the console | Console light | | 15 s |

Impact: the closest contact, but it needs a convincing face in motion for ten minutes, breaks "He won't take the chair", and reverses the silhouette ruling. Effort 15 to 25 days.

### 20.3 Variant C, entry reserved for an ending (reference only; not chosen)
He stays outside through chapters 4 to 6; the door opens only in a closing cinematic. It requires either making "open the door" an ending condition (today the endings depend only on telling the truth and saving the *Iona Star*) or playing the same entry in all four endings, which contradicts the two lie endings where he leaves unreconciled. The chapter 6 handwheel help and the reunion call both need him in the room earlier. Effort 20+ days with story rework; not recommended on canon grounds.

### 20.4 Chosen hybrid
Sections 6.4 to 6.6 are the storyboard. Added detail:

**Positions (room bearings, to be verified in Blender):** A, landing, hand on the rail; B, 0.6 m inside the door, hand on the frame; C, behind the desk chair, hand on its back; D, at the console handwheel; E, by the desk to set down the cup.

| Beat | Position | Clip | Trigger |
|---|---|---|---|
| Door opens | A | breathe, head down | `door_open` event |
| "Thank you." | A to B | two-step walk | the line itself |
| Chapter 5 start | B | weight shift, drip loop | `ch5_ross` |
| Movement 2 | B to C | walk, hand to chair | after the kettle step |
| Cough lines | where he is | cough, turned away | the `>` caption lines |
| "That's Elspeth." | C | head up, half step toward the radio | `ch5_mayday` |
| "Take the wheel" | C to D | walk, wheel grip | `ross_wheel` set |
| Handset reunion | D | reaches for the handset | `reunion` |
| Dawn, lie endings | to E, then A, down | set-down, turn, descend | `ch6_morag_dawn` silence branch |
| Dawn, truth endings | E, stays | set-down, stands | truth branch |

**Capture checkpoint before animation is finished:** one lit still of the figure at positions A, B and C, for Daniel's judgement on whether he reads as a man and not a shape.
