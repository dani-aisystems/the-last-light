# THE LAST LIGHT: script revision, November 2026 (audit Stage C, part 1)

> **Status (2026-11-17): APPROVED by Daniel ("Approved").** All six chapters, the Ross cue points, the canon check, reading time, page risks and open questions are written. Daniel approved the voice sample (chapters 1 and 2) without changes, then the whole document. **Section 14's open questions are decided as recommended** (Daniel, 2026-11-17: "I will go with recommendations on open questions"). **Stage C part 2 (the data) is built and verified headless: section 15.** In-game captures wait for Daniel's OK.
> - This is the single document Daniel approves before any change to `.dlg` or `chapters.json`. **Nothing in the game has been changed:** no `.dlg`, `chapters.json`, `speakers.gd`, test, Blender or Godot file.
> - The Stage P session, running in parallel, owns `docs/SESSION_HANDOFF.md`, the audit README and `DECISIONS.md`. This status block stands in for them until this document is approved.
> - Sources: the approved plan, sections 7.1 to 7.6, 10.4, 14 and 17.1 to 17.7 (`docs/last_light/audit-2026-11/04_narrative.md`); the drafts in `PROPOSAL_35_RADIO_CAST.md`; DECISIONS Q15 to Q18; the Stage S canon note; the story as shipped (`godot/data/story/`).
> - Paths are relative to `projects/games/last_light/` unless they start with `docs/`. Line numbers (`ch2:102`) refer to the shipped `.dlg` files at commit `9969b89`.

## Contents
1. How to read this document
2. Chapter 1, The Watch
3. Chapter 2, Strange Signals
4. Chapter 3, The Storm
5. Chapter 4, The Visitor (the steel door)
6. Chapter 5, The Truth (three movements and the cup)
7. Chapter 6, The Last Light
8. Ross cue points for Stage R
9. Canon check
10. Period claims (checked 2026-11-17)
11. Reading time
12. Three-line page risks
13. Notes for Stage C part 2 (data)
14. Open questions for Daniel
15. As built: Stage C part 2

---

## 1. How to read this document

| Mark | Meaning |
|---|---|
| **NEW** | A conversation or line that is not in the game. New conversations are printed in full in `.dlg` syntax, ready to transcribe once approved |
| **CHANGED** | Words changed. Shown as *before → after*, with the reason |
| **SPLIT** | The same words, broken into two or more messages so that none runs past three lines (D3). The words do not change |
| **CANON** | Changed to agree with the documents or the timeline |
| **▶ CUE** | A Stage R staging point for Ross (position, clip, trigger). Not dialogue and never written as `.dlg` |

**Channels:**
- **radio:** the radio panel, with a card;
- **in-room:** a person subtitle;
- **thought:** Callum, italic;
- **caption:** a sound in `[brackets]`.

**Beat and trigger:**
- each new conversation names the beat in `chapters.json` that plays it, where that beat sits among the shipped beats, and what starts it;
- a new beat id is in bold;
- `timeskip` is the existing fade with a clock change.

**Voice rules kept** (`STAGE3_NARRATIVE_MASTER.md` §4.9; `character-refs/CANON_INDEX.md` §8):
- 1971 Hebridean English with a light touch of Scots, British spelling, no modern idiom;
- "over" when a reply is wanted and "out" to finish, never "over and out";
- Callum is plain, understated and procedural on air;
- no character explains what the listener already knows.

**Every new routine call earns its place** (plan 17.7). Each one teaches a control or plants something that a later scene pays off; the "Teaches / plants" row of each table says what.

**How the numbers were made:**
- reading times and page counts come from a scratch script (section 11);
- every new and changed message measures three lines or fewer at text size x1.0.

---

## 2. Chapter 1, The Watch

### 2.1 What changes
The evening from 18:50 to 23:25, a skip in the shipped game, becomes a working watch:
1. Callum places his first call (to the *Sula*).
2. He reads the glass for the keepers' schedule with Sgeir Mhòr.
3. Morag makes the 21:00 check that the bezel card has always promised.
4. Hector is heard before he is met.
5. The teleprinter brings the 22:00 sheet.

The ending of the chapter (23:25 Morag, the log, the *Mary Ellen*) is unchanged except for the clock (23:58) and one line of the log thought.

**Beat order, revised** (new beats in bold; the shipped beats keep their ids):

| # | Beat | Clock | Trigger (`when`) and actions | Conversation | Duty |
|---|---|---|---|---|---|
| 1 to 8 | `dusk` … `kittiwake_home` | 16:20 to 18:50 | As shipped | As shipped (three Rory lines SPLIT, one Callum line CHANGED; section 2.3) | As shipped |
| 9 | **`sula`** | ≈19:10, clock running | after `kittiwake_home`: `wait 6`, `talk ch1_sula_prompt`, then `until has_flag("called_sula")` | `ch1_sula_prompt`; `ch1_sula` is placed by the player | **`sula`**: "Call the Sula about Thursday." |
| 10 | **`round`** | 20:00 | `timeskip 1200 "20:00"`, `talk ch1_round` | `ch1_round`; examine lines `look_barometer_ch1`, `look_clockwork`, `look_kettle_a` | **`round`**: "Read the glass." The clockwork and the kettle are optional subs |
| 11 | **`sked`** | ≈20:05 | `has_flag("read_glass")`: `wait 3`, `sfx static_burst`, `talk ch1_sked` | `ch1_sked` | none |
| 12 | **`check`** | 21:00 | `timeskip 1260 "21:00"`, `talk ch1_check_2100`, `log log_2100`, then `clock 1260, 0.4` (the evening passes faster until the 23:25 fade) | `ch1_check_2100` | none |
| 13 | **`hector_heard`** | ≈21:40 | `until sim.clock >= 1300`, `talk ch1_hector_heard` | `ch1_hector_heard` | none |
| 14 | **`teleprinter`** | ≈22:00 | `until sim.clock >= 1320`, `sfx teleprinter`, `talk ch1_teleprinter`; the 22:00 sheet becomes readable | `ch1_teleprinter`; after-read `after_forecast_2200` | none (optional read) |
| 15 to 17 | `late`, `log`, `mary_ellen` | 23:25 to 23:58 | As shipped, except `mary_ellen` sets `clock 1438` (was 1437; CANON 7.5) | As shipped (`ch1_log_after` CHANGED) | As shipped |

**Fades:** four (18:30, 20:00, 21:00, 23:25) where the game has two. Between 21:00 and 23:25 the clock runs at 0.4 (24 game minutes to a real minute), so Hector and the teleprinter arrive without more fades.

### 2.2 New conversations

#### `ch1_sula_prompt` and `ch1_sula` (NEW): Neil Gillies, NLB tender *Sula*
| | |
|---|---|
| Beat · trigger | **`sula`**, after `kittiwake_home`. The prompt plays after `wait 6`; the call plays when the player picks **Call a station → Sula** in the radio panel |
| Channels | thought; then radio (Callum opens the call) |
| Duty | **`sula`**, caption "The Sula", line "Call the Sula about Thursday.", done `has_flag("called_sula")`. Nudge at 25 s: "The Sula's at Stornoway. The radio." Hint at 60 s: "Sit at the radio, choose Call a station, then Sula." |
| Flags | sets `called_sula`; `clue board_noted` (tooth branch) |
| Teaches / plants | The player's **first self-placed call**, with no pressure. Thursday's relief and the linesman (the dead phone, `look_phone`). The tooth "noted" pays off in `ch2_046`. One kindly mention of Iain |

```
== ch1_sula_prompt mode=thought
~ Kittiwake's in, and the set's quiet.
~ The Sula's lying at Stornoway for the weather. I'll ask Gillies about Thursday while I can.

== ch1_sula mode=radio
! set called_sula=1
CALLUM: Sula, Sula, this is North Point. Over.
! static
GILLIES: North Point, Sula. Good evening, Principal Keeper. Go ahead. Over.
CALLUM: Evening, Mr Gillies. Is Thursday's relief still on? Over.
GILLIES: Thursday, weather allowing. Your relief keeper, stores, and the linesman for your telephone. Over.
GILLIES: Anything else for the Board while I have you? Over.
* The tooth at oh-four-six is sticking again. Over. -> tooth
* A pane for the west window. Over. -> glass
* Nothing more. Thank you, Sula. North Point out. -> end
= tooth
! clue board_noted
GILLIES: The Board will note it, Mr Mackay. It's down for the next refit.
GILLIES: Your father reported that tooth when I was a mate on the old tender. A good keeper, God rest him. Sula out.
-> END
= glass
GILLIES: A pane, west, cracked. Noted. It'll come Thursday if the glazier's sober. Sula out.
-> END
= end
GILLIES: Sula out.
```
*Canon checks:*
- Gillies at about 55 was 33 in 1949, when Iain first reported the tooth, so a mate then;
- the cracked west pane is from the September gale (CANON_INDEX §3.3);
- he adds nothing about 1953 (PROPOSAL_35 §3.2).

#### `ch1_round` and the three examine lines (NEW): the evening round
| | |
|---|---|
| Beat · trigger | **`round`**, `timeskip 1200 "20:00"`. The barometer, clockwork and kettle lines play when the player examines those objects |
| Channels | thought; one caption |
| Duty | **`round`**, caption "The evening round", line "Read the glass.", done `has_flag("read_glass")`. Optional subs: "Wind the standby clockwork" (done `has_flag("sang")`) and "Put the kettle on" (done `has_flag("kettle_ch1")`). Nudge at 25 s: "The glass. On the wall by the chart." |
| Flags | `read_glass`; `sang` (the crank, any time in chapters 1 to 3, once); `kettle_ch1` |
| Teaches / plants | Reading the glass for a report (MacAskill asks for it next). The Primus, ready for the cup in chapter 5. **`sang`**: Ross says in `ch4_door` that the boy "used to sing to the clockwork"; a new line there pays it off (chapter 4). The two mugs plant chapter 5's second cup |

```
== ch1_round mode=thought
~ Twenty hundred. The evening round: the glass, the clockwork, the kettle.

== look_barometer_ch1 mode=thought
! set read_glass=1
~ Nine-eight-one. Twenty-three down since yesterday afternoon.

== look_clockwork mode=thought
! set sang=1
~ The standby clockwork, for the day the motor fails. Twenty turns of the crank, every watch, needed or not.
> [Callum hums under his breath as he winds: a few bars of an old tune]
~ Twenty turns. Some tune always comes with them.

== look_kettle_a mode=thought
! set kettle_ch1=1
~ The Primus. Pump her up, a match to the spirit cup, and wait for the roar.
~ Two mugs on the hook. I've only ever used the one.
```
*Notes:*
- **"Twenty-three down":** yesterday's log reads "14.00 Barometer 1004 mb, falling", and 1004 − 981 = 23. The dial prop (`documents.barometer_dial`) must read 981 in chapter 1, and lower later (section 13).
- **The song** is not named here, so Ross's line in chapter 4 ("Fear a' bhàta. Your father hated that song.") still lands as a revelation.
- **The Primus** is open question 4. The room has no kettle yet; it has the two enamel mugs (desk and sill).
- **The crank** is "outside the glazing" in `build.py`. If the player cannot reach it from the watch room, this sub needs the crank brought within reach, or it is dropped (section 13).

#### `ch1_sked` (NEW): Murdo MacAskill, Sgeir Mhòr, evening schedule
| | |
|---|---|
| Beat · trigger | **`sked`**, when `has_flag("read_glass")`: `wait 3`, `sfx static_burst` |
| Channels | radio |
| Flags | none |
| Teaches / plants | **The weather report:** Callum gives the figure he has just read. The keepers' network. Iain's first sideways mention ("About weather, aye"; MacAskill knew him, and says no more). "Same time at midnight" sets up chapter 2; the missed schedule in chapter 3 depends on it |

```
== ch1_sked mode=radio
! static
MACASKILL: North Point, North Point, this is Sgeir Mhor. Evening schedule. Over.
* Sgeir Mhor, North Point. Go ahead, Murdo. Over. -> wx
= wx
MACASKILL: Glass nine-eight-four here, and dropping like a stone. South-west six. Sea rough. What have you? Over.
* Nine-eight-one and falling. South-west seven. Heavy rain. Over. -> same
* Nine-eight-one. It's coming for both of us, Murdo. Over. -> same
= same
MACASKILL: Aye. It'll be a long one.
MACASKILL: Your father used to say you could smell a November gale in the paint. Over.
* He'd a saying for every weather. Over. -> short
* He was usually right about weather. Over. -> warm
= short
MACASKILL: He had. Same time at midnight, Callum. Sgeir Mhor out.
-> END
= warm
MACASKILL: About weather, aye. Same time at midnight. Sgeir Mhor out.
```
*Changed from the 17.4 draft:*
- Callum's replies follow the glass he has just read.
- "He said a lot of things" became "He'd a saying for every weather": Callum already answers Rory with "Your grandfather said a lot of things", and the echo would sound recycled.
- The station name is written "Sgeir Mhor" in `.dlg` text (the in-game font has the accent if wanted: "Sgeir Mhòr").

#### `ch1_check_2100` (NEW): the 21:00 radio check
| | |
|---|---|
| Beat · trigger | **`check`**, `timeskip 1260 "21:00"`; then `log log_2100` |
| Channels | radio |
| Flags | none |
| Teaches / plants | CANON 7.5: the radio card's "Radio check 2100" now happens, and the 18:30 call was Morag being early, as she said. The new log row is section 2.4 |

```
== ch1_check_2100 mode=radio
! static
MORAG: North Point, Stornoway. Twenty-one hundred radio check. Over.
* Stornoway, North Point. Loud and clear. Nothing to report. Over. -> plain
* You're on time, Morag. -> ontime
= ontime
MORAG: Don't get used to it. Stornoway out.
-> END
= plain
MORAG: Loud and clear. Stornoway out.
```

#### `ch1_hector_heard` (NEW): Hector overheard on 16
| | |
|---|---|
| Beat · trigger | **`hector_heard`**, at ≈21:40 (`until sim.clock >= 1300`) |
| Channels | radio (Hector to Stornoway; the player overhears), then thought |
| Flags | none |
| Teaches / plants | Hector's voice is known before chapter 2 (plan 7.2: "Hector arrives cold"). His two passengers and "after midnight" match `ch2_gannet` |

```
== ch1_hector_heard mode=radio
! static
HECTOR: Stornoway Coastguard, Stornoway Coastguard, this is the schooner Gannet. Over.
MORAG: Gannet, Stornoway. Go ahead, Hector. Over.
HECTOR: Late away, with two passengers aboard and the glass falling. I'll be off North Point some time after midnight. Over.
MORAG: Gannet, Stornoway. Roger. Call North Point when you raise the light. Stornoway out.
~ Hector Macleod. He's run that schooner round Harris since before I could tie my boots.
```
*Changed from the 17.4 draft:* the thought read "when I was a boy on these stairs". Callum was 20 to 25 at North Point (1950 to 1955), so not a boy; Hector's forty years on the coast go back to Callum's infancy.

#### `ch1_teleprinter` and `after_forecast_2200` (NEW): the 22:00 sheet
| | |
|---|---|
| Beat · trigger | **`teleprinter`**, at ≈22:00 (`until sim.clock >= 1320`), `sfx teleprinter`. The after-read line plays once, on closing the new document `forecast_2200` (chapter 1 only) |
| Channels | caption, thought |
| Teaches / plants | Documents arrive during the night (plan section 8, "newly relevant" shown by a sheet curling out of the machine). Storm ten keeps coming, and chapter 3 opens with it |

```
== ch1_teleprinter mode=thought
> [The teleprinter by the radar starts up, chatters, and stops]
~ The twenty-two hundred. Let her finish before I tear it off.

== after_forecast_2200 mode=thought
~ Storm ten, still imminent. Imminent's had six hours of it already.
```
**Document text proposed** (`forecast_2200`, rendered later in the style of `forecast`):
> GALE WARNING ISSUED 2200 GMT 14 NOV 1971. HEBRIDES MINCHES. SOUTHWESTERLY SEVERE GALE 9 NOW IN FORCE. INCREASING STORM 10 IMMINENT.

In a British gale warning "imminent" means within six hours of issue (to verify, section 10). Callum's line plays on the 1600 warning, which said "imminent" six hours ago. The room has the 1600 sheet but no teleprinter machine, so the arriving sheet needs a prop (section 13).

### 2.3 Changed lines in shipped conversations

| Line | Speaker · channel | Beat | Before → after | Reason |
|---|---|---|---|---|
| `ch1:45` | Morag · radio | `radio_check` | "Roger. Gale warning for Hebrides and Minches. South-westerly seven, rising severe gale nine before dawn. Visibility poor in rain. Over." → "Roger. Gale warning for Hebrides and Minches." / "South-westerly seven, rising severe gale nine before dawn. Visibility poor in rain. Over." | SPLIT: it paged at x1.0 (135 characters, 4 lines) |
| `ch1:66` | Rory · radio | `kittiwake` | "Callum, is that you? Thank God. Sorry, eh, North Point. I'm coming in from the Flannans, and the rain's that thick I can't see my own bow. I was meant to pick up the Sound an hour ago. Over." → "Callum, is that you? Thank God. Sorry, eh, North Point." / "I'm coming in from the Flannans, and the rain's that thick I can't see my own bow." / "I was meant to pick up the Sound an hour ago. Over." | SPLIT: 190 characters, 3 pages. Rory's run-on reads better as three breaths |
| `ch1:83` | Callum · radio | `vector` | "Keep it fine on your starboard bow and come in slow. North Point. Over." → "Keep that green light just to the right of your bow, and come in slow. North Point. Over." | CHANGED (7.6). The plan's draft had "Keep my light", but "it" is the Sound's green Rory has just sighted, not the lighthouse. "Come in slow" stays: that's Callum's idiom |
| `ch1:84` | Rory · radio | `vector` | "Aye. Aye, I see it. Here, Callum, you'll laugh, … No lights. Just waiting. Over." → "Aye. Aye, I see it." / "Here, Callum, you'll laugh, but my grandfather used to say there's a boat out in the East Gut on nights like this." / "No lights. Just waiting. Over." | SPLIT: 165 characters. "No lights. Just waiting." gets its own message |
| `ch1:91` | Rory · radio | `vector` | "The Mary Ellen. Ross's boat. My grandfather was on her …" → "The Mary Ellen. Ross's boat." / "My grandfather was on her the night she went down. Below, in the engine. Only one of them that came home." | SPLIT: 134 characters |
| `ch1:137` | Callum · thought | `log` | "Eighteen-thirty, radio check, gale warning. Ten to seven, Kittiwake in by the North Sound. Twenty-three-twenty-five, Stornoway on sixteen. All well." → "Eighteen-thirty, radio check, gale warning. Ten to seven, Kittiwake in by the North Sound." / "Twenty-one hundred, radio check, the glass at nine-eight-one. Twenty-three-twenty-five, Stornoway on sixteen. All well." | CHANGED: the page now carries the 21:00 row |
| `chapters.json:32` | — | `mary_ellen` | `["clock", 1437, 0.0]` → `["clock", 1438, 0.0]` | CANON 7.5: the call is 23:58 everywhere in the text |

### 2.4 Data that follows from chapter 1 (no dialogue)
- **New station-log row** `log_2100` (`chapters.json` `station_log`, `documents.py` `rows71`, and the `log_1971` document text): `21.00 · SW 7 · Heavy rain · Radio check Stornoway CG. Barometer 981 mb, falling.`
- **New speakers** (`speakers.gd`), both known on first contact:
  - `GILLIES`: name "Neil Gillies", call "SULA · NLB TENDER", sub "Northern Lighthouse Board · master N. Gillies";
  - `MACASKILL`: name "Murdo MacAskill", call "SGEIR MHÒR LIGHT", sub "Principal keeper M. MacAskill".
- **The radio panel's call list** gains the *Sula* during the `sula` beat only.

---

## 3. Chapter 2, Strange Signals

### 3.1 What changes
- Elspeth's ship is overheard before her name is known.
- MacAskill keeps his midnight schedule and mentions "your father's books", the archive's first nudge.
- Dr Marsh asks for an observation, and asks whether keepers will soon be automatic.
- Two canon fixes (the tooth date; a wooden boat sold "for razor blades").

**Beat order, revised:**

| # | Beat | Trigger and actions | Conversation | Notes |
|---|---|---|---|---|
| 1, 2 | `trace`, `radar` | As shipped | As shipped | |
| 3 | **`iona_heard`** | after `radar`: `wait 6`, `sfx static_burst`, `talk ch2_iona_heard` | `ch2_iona_heard` | Before Hector's call |
| 4, 5 | `gannet`, `gannet_in` | As shipped | As shipped | The optional calls `opt_ch2_rory` and `opt_ch2_morag` open here as now |
| 6 | **`sked`** | after `gannet_in`: `wait 10`, `talk ch2_sked` (deferred while an optional call runs, like `second_call`) | `ch2_sked` | ≈00:25 |
| 7 | **`marsh`** | `wait 8`, `talk ch2_marsh` (deferred likewise) | `ch2_marsh` | |
| 8 to 11 | `second_call`, `archive`, `jam`, `clear` | As shipped | As shipped (`ch2_046` gains one line) | |

### 3.2 New conversations

#### `ch2_iona_heard` (NEW): the *Iona Star*, overheard
| | |
|---|---|
| Beat · trigger | **`iona_heard`**, after `radar` (`wait 6`) |
| Channels | radio (to Stornoway; overheard), then thought |
| Speaker card | **Shows "Iona Star · the mate", not "Elspeth Ross"** (open question 5). Today `speakers.gd` names her on the card from her first line in chapter 3, before she says who she is |
| Teaches / plants | Elspeth is heard as a professional first and a daughter second (plan 17.5). "Twelve souls aboard" comes back in her chapter 3 report and in the Mayday |

```
== ch2_iona_heard mode=radio
! static
ELSPETH: Stornoway Coastguard, Stornoway Coastguard, this is Iona Star, Golf Mike X-ray Quebec. Over.
MORAG: Iona Star, Stornoway. Go ahead. Over.
ELSPETH: Passage report. Abeam of Neist Point, northbound for Stornoway. Twelve souls aboard. Over.
MORAG: Iona Star, Stornoway. Received. Gale warning is in force for the Minches. Stornoway out.
~ A careful voice. Whoever she is, she's done this in worse.
```
*Changed from the 17.4 draft:*
- **"Passing Barra Head" became "Abeam of Neist Point".** Barra Head is on the Atlantic side, off the Glasgow to Stornoway route through the Little Minch. Neist Point (Skye) is on that route, and about the right distance for her to be "abeam of your light at oh-five-hundred" in chapter 3 at a gale-slowed speed. The geography is to check (section 10), since North Point itself is fictional.
- Elspeth is flawless on procedure and never says "please" (master §4.9).

#### `ch2_sked` (NEW): MacAskill's midnight schedule
| | |
|---|---|
| Beat · trigger | **`sked`**, after `gannet_in` (`wait 10`) |
| Channels | radio |
| Flags | none |
| Teaches / plants | **"Your father's books"** is the first nudge toward the old-log box, before "tell Iain" sends Callum there. "Tidiest books on the coast" sits against what is in them, and against Ross's "Iain was a tidy man" (chapter 5). It ties Gillies to MacAskill (one tender serves both lights). "Two o'clock, if my aerial's still standing" sets up chapter 3's silence |

```
== ch2_sked mode=radio
! static
MACASKILL: North Point, Sgeir Mhor. Midnight schedule, and late for it. Over.
* Sgeir Mhor, North Point. Go ahead, Murdo. Over. -> wx
= wx
MACASKILL: Nine-seven-six here and still going. South-west eight. Spray over the gallery rail. What have you? Over.
* Nine-seven-three. South-west eight, and the rain going sideways. Over. -> books
* Lower than yours, Murdo. Nine-seven-three. Over. -> books
= books
MACASKILL: Neil Gillies was at me last month about my returns. Said I should see how North Point kept its books.
MACASKILL: Your father's time, he meant. Tidiest books on the coast. You'll have them all yet. Over.
* Every one. In the box on the shelf. Over. -> box
* (Say nothing.) -> quiet
= box
MACASKILL: Aye. A keeper's books outlast the keeper. Two o'clock, Callum, if my aerial's still standing. Sgeir Mhor out.
-> END
= quiet
MACASKILL: ...Two o'clock, then. If my aerial's still standing. Sgeir Mhor out.
```
*Notes:*
- **Not in the 17.4 draft;** written to its outline ("a remark about 'your father's books'").
- **MacAskill does not mention the *Mary Ellen* call:** he is too far south to have heard Ross's low-power set (CANON_INDEX §3.4).
- **"Midnight schedule, and late for it":** the schedule falls at about 00:25, after Hector is in.
- **The glass:** 981 at 20:00, 973 at about 00:25, falling to storm force by 01:05. Steep, but in keeping with a storm-ten depression.

#### `ch2_marsh` (NEW): Dr Helen Marsh, survey vessel *Western Venture*
| | |
|---|---|
| Beat · trigger | **`marsh`**, after `sked` (`wait 8`) |
| Channels | radio, then thought |
| Flags | none |
| Teaches / plants | Theme: "the last light". The keepers' era is ending ("automatic inside ten years"), which gives the title a second meaning without touching the plot. Callum's reply keeps the radio rule ("keep it short on sixteen", as Morag's "not supposed to chat on sixteen"). His last thought is evasive, not ignorant, as the archive is about to show |

```
== ch2_marsh mode=radio
! static
MARSH: North Point Light, this is Western Venture. Um. Over.
CALLUM: Western Venture, North Point. Go ahead. Over.
MARSH: This is Dr Marsh, survey party. Our master's asleep and I've the weather log. Could I have your observation? Over.
* South-west eight. Glass nine-seven-three, falling. Heavy rain. Over. -> obs
= obs
MARSH: Nine-seven-three. Thank you. Can I ask, is it awfully rude? What's it like, being the only one out there? Over.
* It's a job. Over. -> job
* Quiet. Mostly. Over. -> quiet
= job
MARSH: Of course. Sorry. Over.
-> auto
= quiet
MARSH: I'd go mad. I'd be talking to the lamp. Over.
= auto
MARSH: They say the Board will make you all automatic inside ten years. A light that keeps itself. Over.
CALLUM: Keep it short on sixteen, Western Venture. North Point out.
~ A light that keeps itself. Then nobody would have had to write anything down.
```
*Notes:* re-cut from PROPOSAL_35 §3.3. Her procedure is loose ("Um", no call sign, a question on 16), which is what she is there to show; she is the only new voice allowed one "Sorry". The new speaker `MARSH` is known on first contact: name "Dr Helen Marsh", call "WESTERN VENTURE", sub "Survey vessel · Dr H. Marsh, survey party".

### 3.3 Changed lines in shipped conversations

| Line | Speaker · channel | Beat | Before → after | Reason |
|---|---|---|---|---|
| `ch2:102` | Callum · thought | `clear` | "… Forty-nine. December fifty-three. Sixty-one." → "… Forty-nine. December fifty-three. Sixty-three." | CANON: `note_046` was corrected to "2.2.63" (REVIEW_FLAGS I01: Callum was posted elsewhere from 1955 to 1962), but the line still said sixty-one |
| `ch2:104` (new line before it) | Callum · thought | `clear` | (none) → `[if clue("board_noted")] ~ "The Board will note it." They've been noting it since forty-nine.` | NEW: pays off the *Sula* call |
| `ch2:113` | Rory · radio | optional `opt_ch2_rory` | one message → "My grandfather'd have had his coat on and been out the door." / "He'd never go past the Gut after dark, not once in eighteen years. Said he'd no wish to meet her. Over." | SPLIT: 164 characters |
| `ch2:129` | Morag · radio | optional `opt_ch2_morag` | one message → "Mary Ellen had a sister off the same yard in Fraserburgh. The Catriona." / "Sold for breaking in nineteen sixty-nine, to a Mr Morrison. Govan." | SPLIT: 138 characters |
| `ch2:130` | Morag · radio | optional `opt_ch2_morag` | "Govan's a long road from razor blades to the Minch. Stornoway out." → "Sold for breaking, Callum. That doesn't mean she was broken. Stornoway out." | CHANGED (7.6) and CANON. The *Catriona* is a wooden motor-fisher ("old wooden boat", `ch3:109`), and wood is not made into razor blades. The plan's draft ("Sold to Govan for scrap, the register says. Scrap doesn't sail back to the Minch") repeated the line before it and had Morag already sure the boat came back. The new line keeps her one step short of that |

**One chapter 3 line follows from 3.2:** the hidden card is revealed when she names herself. A `! set elspeth_named=1` goes just before `ch3:38` ("This is Elspeth Ross. First mate."), and also before Ross's "That's Elspeth" (`ch5:127`) for players who never hear her name. Chapter 3 lists it.

---

## 4. Chapter 3, The Storm

### 4.1 What changes
- **Chapter opening:** the chapter opens with the fuel run (plan 10.4). It teaches the stair before Ross climbs it, and its pumping is the cause of the fouled fuel in chapter 4.
- **Missed schedule:** the 02:00 schedule with Sgeir Mhòr goes unanswered. It is the storm's first cost before it reaches North Point.
- **Visser:** Visser and the *Hendrika* are the third navigation job, once both rescues are settled. He is the one person tonight who sees Callum simply as a good keeper.
- **Line fixes:** one wind contradiction is fixed, and the gale warning and the long Morag, Rory and Hector messages are split.

**Beat order, revised:**

| # | Beat | Trigger and actions | Conversation | Duty |
|---|---|---|---|---|
| 1 | **`fuel`** | chapter start: `wait 2`, `talk ch3_fuel`. The pump plays `ch3_pump` once it is drawing (after about 40 strokes). `ch3_fuel_done` plays when the stair door is shut again with the day tank full | `ch3_fuel`, `ch3_pump`, `ch3_fuel_done` | **`fuel`**: "Top up the day tank from the drums below." Subs: the torch (optional), "Open the stair door", "Work the hand pump" (hold), "Back up, and shut the door". Done `has_flag("fuel_done")` |
| 2 | `forecast` | **when `has_flag("fuel_done")`** (was: chapter start), so the broadcast is not missed below | `ch3_forecast` (CHANGED) | |
| 3 | `two_ships` | As shipped, but the wait between the two calls is 16 s (was 10: plan 7.3, more air) | `ch3_corrie`, `ch3_lowestoft` (CHANGED) | as shipped |
| 4 | `both` | As shipped; `opt_ch3_hector` opens here as now | `ch3_after_two` (unchanged: "Coming up on two o'clock…") | |
| 5 | **`sked3`** | after `both`: `wait 10`, `clock 1560` (02:00, no fade), `talk ch3_sked_missed` | `ch3_sked_missed` | |
| 6 | **`hendrika`** | `wait 12`, `sfx static_burst`, `talk ch3_hendrika` (deferred while `opt_ch3_hector` runs). On `help` the ship spawns | `ch3_hendrika` | **`hendrika`** (only if `helped_hendrika`): "Bring Hendrika in by the West Gut." Subs as `gannet` (confirm, 314° line, shelter) |
| 7 | **`hendrika_in`** | when `saved("Hendrika") or lost("Hendrika") or not has_flag("helped_hendrika")`: `wait 3`, `talk ch3_hendrika_in` | `ch3_hendrika_in` | |
| 8 to 11 | `elspeth`, `notes`, `restore`, `dark_boat` | As shipped, with the waits before `elspeth` and `notes` raised from 6 and 8 s to 12 and 14 s (more air); `opt_ch3_hector` now closes at `notes` as before | `ch3_elspeth` (one flag line added; one SPLIT), `ch3_notes_a/b` (SPLIT), `ch3_rory_dark` (SPLIT) | as shipped |

**Clock:** the start stays at 01:05. Rate 0.1 → 0.06, and after `sked3` sets 02:00, 0.04, so the chapter ends near 02:20 as chapter 4's start (02:21) expects. To confirm in the sim in part 2.

### 4.2 New conversations

#### `ch3_fuel`, `ch3_pump`, `ch3_fuel_done` (NEW): the fuel run
| | |
|---|---|
| Beat · trigger | **`fuel`**, chapter start; the pump line when the pump draws; the last line when the stair door is shut again |
| Channels | thought; one caption |
| Flags | `fuel_done` |
| Teaches / plants | The stair, the ladder, the door wheel ("dogged", the word chapter 4 uses). "I'll have stirred up every drop of water in it" is the cause behind `ch4_gen_out` ("Water in the sediment bowl: all tonight's pumping has stirred the tank", Q17, unchanged). "Nobody on them but me" sets up the footsteps in chapter 4 |

```
== ch3_fuel mode=thought
~ Five past one. The day-tank glass is down on the red line.
~ She's run since four this afternoon. Down to the drums, then, and pump her up by hand.
~ The torch, and the stair door. Mind the ladder: it'll be wet in this.

== ch3_pump mode=thought
> [The hand pump: a dry rasp, then the suck and knock of diesel coming up]
~ Forty strokes and she's drawing. Twenty more.
~ That's near the bottom of the drum. I'll have stirred up every drop of water in it.

== ch3_fuel_done mode=thought
~ Day tank full. The door shut and dogged behind me.
~ A hundred and nine steps down to the base door, and nobody on them but me.
```
*Notes:*
- **`sys_daytank`** ("The day-tank's run dry. I'll pump it up from the main tank below.") stays as it is. It is the system line for a day tank run dry at any other time; the silent automatic top-up stays as the safety net (plan 10.4).
- **The hint** `_use_door` gives before chapter 4 ("Nobody on it till the relief comes on Thursday") must let the door open during this beat (section 13).

#### `ch3_sked_missed` (NEW): Sgeir Mhòr off the air
| | |
|---|---|
| Beat · trigger | **`sked3`**, after `both`; Callum calls by himself (no choice) |
| Channels | radio, caption, thought |
| Teaches / plants | Pays off "two o'clock, if my aerial's still standing" (chapter 2). The storm's first casualty is another keeper; "If it can do that to Sgeir Mhor, it can do it here" sets up the blackout that follows Morag's notebook |

```
== ch3_sked_missed mode=radio
CALLUM: Sgeir Mhor, Sgeir Mhor, this is North Point. Two o'clock schedule. Over.
! wait 4
CALLUM: Sgeir Mhor, North Point. Murdo, do you hear me? Over.
! static
> [A carrier. No voice. Then nothing.]
~ Sgeir Mhor's off the air. Murdo will be at his batteries with a torch in his teeth.
~ If it can do that to Sgeir Mhor, it can do it here.
```
*Changed from the 17.4 draft:* "Sgeir Mhor's dark" became "off the air". To a keeper, a station "dark" means its light is out, which would be a bigger event than the storm can carry here.

#### `ch3_hendrika` and `ch3_hendrika_in` (NEW): Captain Jan Visser, MV *Hendrika*
| | |
|---|---|
| Beat · trigger | **`hendrika`**, after `sked3`; **`hendrika_in`** when she is in, lost, or never came in |
| Channels | radio; a closing thought |
| Flags | `helped_hendrika`; ship `Hendrika` (`steamer`, bearing −38, aim `reef`, speed 0.7, as PROPOSAL_35 §3.1) |
| Teaches / plants | A third navigation job (West Gut, 314°), with the two lessons already learned. The only voice tonight that knows nothing of 1953: "A good keeper." His careful "please" and "thank you" sit just before Elspeth's ice (master §4.9: she never says "please" on the radio). He returns at dawn if saved (chapter 6) |

```
== ch3_hendrika mode=radio
! static
VISSER: North Point Light, North Point Light, this is Hendrika, Hendrika, Papa Echo Juliett X-ray. Over.
* Hendrika, North Point. Go ahead. Over. -> go
* Hendrika, North Point. Say your position. Over. -> pos
= go
VISSER: Good morning, North Point Light. I did not expect a voice at this hour. On my chart you are a light and nothing more. Over.
-> ask
= pos
VISSER: Five miles west of you, North Point Light, and not liking it. Over.
= ask
VISSER: I am timber for Stornoway, and late. My chart is the old edition.
VISSER: I would like the West Gut, please, if you will tell me it is still where my chart says. Over.
* She's where your chart says. Steer for the light, and I'll put you on the line. Over. -> help
* Stay outside, Hendrika. Heave to till morning. Over. -> outside
= help
! set helped_hendrika=1
VISSER: Thank you, North Point Light. My wife says you have a kind voice for such a bad night. Over.
! ship {"name": "Hendrika", "kind": "steamer", "bearing": -38, "aim": "reef", "speed_mul": 0.7}
-> END
= outside
VISSER: Understood. We will heave to and drink coffee. Hendrika out.

== ch3_hendrika_in mode=radio
[if saved("Hendrika")] VISSER: North Point Light, Hendrika. Anchored in the West Gut lee. Thank you. Over.
[if saved("Hendrika") and saved("Gannet")] VISSER: There is a schooner here also. Her master is waving a lamp at us. Over.
[if saved("Hendrika")] VISSER: My wife says to tell you, North Point. A good keeper. Hendrika out.
[if saved("Hendrika")] ~ A good keeper. He's no way of knowing any different.
[if lost("Hendrika")] ~ The Hendrika's echo goes into the broken water at the edge of the Gut, and doesn't come out.
[if lost("Hendrika")] ~ Morag's voice, calling the lifeboat. Then the lifeboat's, answering.
```
*Changed from the PROPOSAL_35 draft:*
- "Good evening" became "Good morning … at this hour" (it is after two).
- "Late after engine trouble at Kyle" was dropped: a coaster from Kyle to Stornoway would not come up five miles west of North Point. His route is left unsaid.
- The call sign is spelled with the ITU "Juliett".
- The thank-you call (PROPOSAL_35's "payoff") is written; Hector waves his lamp only if the *Gannet* was saved.

### 4.3 Changed lines in shipped conversations

| Line | Speaker · channel | Beat | Before → after | Reason |
|---|---|---|---|---|
| `ch3:6` | Morag · radio | `forecast` | "All stations, all stations, this is Stornoway Coastguard. Gale warning. Hebrides, Minches: south-westerly severe gale nine, increasing storm ten, imminent. Visibility very poor. Stornoway out." → "All stations, all stations. This is Stornoway Coastguard. Gale warning." / "Hebrides, Minches. South-westerly severe gale nine, increasing storm ten, imminent." / "Visibility very poor. Stornoway out." | SPLIT (7.6), keeping "imminent". The plan's draft had "rising to storm force ten within the hour", but in a gale warning "imminent" means within six hours (section 10). `after_forecast_b` and the 1600 sheet both rest on the word |
| `ch3:16` | *Lowestoft Star* · radio | `two_ships` | "North Point Light, Lowestoft Star, Lowestoft Star. Running before it from the north. Can't hold her head up. Advise, over." → "North Point Light, Lowestoft Star, Lowestoft Star. Coming down from the north with it on the bow." / "She won't hold her head up to it. Tell me where to steer, North Point. Over." | CANON and 7.6. A boat running before a south-westerly gale is heading north-east, but she comes in from the north to the 000° Sound. "Can't hold her head up" already described a boat heading into it. The plan's draft ("the gale's behind us, driving us south") repeated the error. "Advise" became plain words, as 7.6 asked |
| `ch3:29` | Elspeth · radio | `elspeth` | one message → "Glasgow for Stornoway, twelve souls aboard." / "We expect to pass abeam of your light at oh-five-hundred. Request local conditions, over." | SPLIT: 133 characters |
| before `ch3:38` | — | `elspeth` | (none) → `! set elspeth_named=1` | Reveals her card as "Elspeth Ross" at the moment she says it (section 3.2; open question 5) |
| `ch3:66` | Morag · radio | `notes` | one message → "I've something I should have said a long time ago." / "I've got it in front of me. My notebook from that night. Pencil. I kept it in my handbag for eighteen years like a fool." | SPLIT: 171 characters. The first sentence alone lets the silence land |
| `ch3:80` | Morag · radio | `restore` | one message → "Thank God. Callum, did you hear what I said?" / "Oh-one-fifty-two. No light. Your father's log says the light failed at oh-two-ten. After she struck." | SPLIT: 145 characters |
| `ch3:109` | Rory · radio | `dark_boat` | one message → "I'm tied up in the Sound, and I've been watching." / "There's a boat came out from the lee of Pabbay. Old wooden boat, a wee motor-fisher. No lights. Not a single light, Callum." | SPLIT: 173 characters |
| `ch3:118` | Hector · radio | optional `opt_ch3_hector` | "Snug as a dog in a basket, North Point. Lying to two anchors in the West Gut lee, and the passengers asleep at last. Over." → "Snug as a dog in a basket, North Point. Two anchors down in the shelter of the West Gut." / "And the passengers asleep at last. Over." | CHANGED (7.6, as drafted) |
| `ch3:119` | Hector · radio | optional `opt_ch3_hector` | one message → "I was thinking of your father." / "On a night like this he'd have had the kettle on and the tide tables open, and Sandy Ross up from the boat telling lies about herring." | SPLIT: 165 characters |

---

## 5. Chapter 4, The Visitor

### 5.1 What changes
The story is unchanged (plan 7.3). The lines are made true to the steel bulkhead door that Stage S built and that Daniel kept (canon note, 2026-11-16), and the clockwork song from chapter 1 is paid off. The two long MF lines are split. The Ross cues are in section 8; the beat order and the generator lock (`ch4_gen_out`, Q17) are as shipped.

### 5.2 The steel door

**Decided:** the door stays steel. Its handwheel turns 1.5 turns while two lever dogs lift, and then the leaf swings in (Stage S, `13_stageS_evidence.md`). The flag `bolted` keeps its name in data, meaning "dogged hard", so no save or test changes.

| Line | Speaker · channel | Beat | Before → after |
|---|---|---|---|
| `ch4:128` | caption | aside `look_bolt` (the door, chapter 4 from `hail` to the door scene) | "[The bolt goes home]" → **"[The wheel goes hard over. The dogs bite home.]"** |
| `ch4:129` | Callum · thought | aside `look_bolt` | "Two inches of oak and a bolt my father fitted. It'll have to do." → **"A steel door, and two dogs my father kept greased. It'll have to do."** |
| `ch4:94`, `ch4:103` | reply | `door` | "(Draw the bolt and open the door.)" → "(Turn the wheel and open the door.)" |
| `ch4:109` | Callum · thought | `door` (`open`, after dogging) | "The bolt is stiff with salt. The door comes in with the storm behind it." → "The wheel's stiff with salt. The dogs come up one at a time, and the door swings in with the cold of the whole stair behind it." |
| `ch4:110` | Callum · thought | `door` (`open`, not dogged hard) | "It was never even bolted. The door comes in with the storm behind it." → "I never dogged it hard. One turn of the wheel, and the door swings in with the cold of the whole stair behind it." |
| `ch5:8` | Callum · thought | ch5 `story` (door shut) | "…I can hear him breathing on the other side of two inches of oak." → "…I can hear him breathing on the other side of the steel." |
| `game_fp.gd:699` (prompt, not dialogue) | — | ch4 | "The stair door · bolted" → "The stair door · dogged hard" |

*Why these words:*
- **The door line** keeps the old line's rhythm and its father, and "kept greased" is a keeper's care, true of Iain sober.
- **"The storm behind it"** became "the cold of the whole stair". The stair is inside the tower; what comes in with the door is the draught from the base door Ross left open below. That fits the soaked man on the landing.

### 5.3 Other changed lines

| Line | Speaker · channel | Beat | Before → after | Reason |
|---|---|---|---|---|
| after `ch4:68` | Callum · thought | `door` (`name` branch) | (none) → `[if has_flag("sang")] ~ I was humming it tonight, at the crank. I never even noticed.` | NEW: pays off `look_clockwork` (chapter 1). Restrained on purpose: Ross has just named the song |
| `ch4:35` | Callum · radio | optional `ch4_mf_morag` | one message → "Stornoway, Stornoway, North Point on two-one-eight-two." / "There's a boat tied up at my landing. No lights, and somebody's sitting on sixteen. Over." | SPLIT: 145 characters |
| `ch4:80` | Morag · radio | `door` (`radio` branch) | one message → "…North Point, Stornoway. Callum, the lifeboat's out on a shout at the Shiants. Two hours at least." / "Do not open that door. Do you hear me? Over." | SPLIT: 145 characters. The warning gets its own message |

`ch4_stairs` ("Nobody comes up those stairs but the relief keeper and the engineer") stays. After the fuel run it reads truer, not less true: Callum goes *down* them.

---

## 6. Chapter 5, The Truth

### 6.1 What changes: three movements (plan 7.3)
The content is the same; the conversation is broken where the player does something.
1. **Movement 1, at the door:** the wreck, Pabbay, why he stayed dead. `ch5_ross`, ending on his cough.
2. **The cup:** Callum makes tea on the Primus. With the door open he gives Ross the other mug; with the door shut he pours two from habit and sets one by the door. This is the cup Ross sets down at dawn (`ch6:120`, now true).
3. **Movement 2:** the library, the Board, and the choice "My father wrote that entry" / "I wrote that entry" / "What do you want" (`ch5_ross_2`).
4. **Movement 3:** the calls, Kenny Bain, the drawer (`ch5_ross_3`), after a silence.
5. **Then as shipped:** the letter, the sediment bowl (Q17), Morag, the Mayday.

**Beat order, revised:**

| # | Beat | Trigger and actions | Conversation | Duty |
|---|---|---|---|---|
| 1 | `story` | As shipped | `ch5_ross` (movement 1; now ends at `ch5:27`, the cough) | |
| 2 | **`cup`** | `wait 3`, `talk ch5_kettle`. The Primus interaction plays `ch5_cup` | `ch5_kettle`, `ch5_cup` | **`kettle_ch5`**: door open, "Make him tea."; door shut, "Make tea." Done `has_flag("kettle_ch5")`. Nudge at 25 s: "The Primus, on the west sill." |
| 3 | **`story2`** | when `has_flag("kettle_ch5")`: `wait 3`, `talk ch5_ross_2` | `ch5_ross_2` (shipped `ch5:28` to `ch5:49`) | |
| 4 | **`story3`** | `wait 6`, `talk ch5_ross_3` | `ch5_ross_3` (shipped `ch5:50` to `ch5:78`, plus one opening thought) | |
| 5 to 9 | `drawer`, `bowl`, `morag`, `mayday`, `power` | As shipped | as shipped (Mayday SPLIT, one flag line) | as shipped |

### 6.2 New and restructured conversations

#### `ch5_kettle` and `ch5_cup` (NEW): the cup
| | |
|---|---|
| Beat · trigger | **`cup`**, after movement 1 |
| Channels | thought; caption; Ross in-room (door open) |
| Flags | `kettle_ch5`; `gave_cup` (door open only) |
| Teaches / plants | The player's act in the long conversation (plan 7.3). "The other mug, the one I've never used" pays off "Two mugs on the hook. I've only ever used the one" (chapter 1). "The way Father always did, summers" implies the two mugs were Iain's and his guest's (Hector's "kettle on … and Sandy Ross up from the boat", `ch3:119`) without saying so. It makes `ch6:120` true |

```
== ch5_kettle mode=thought
[if has_flag("door_open")] ~ He's shaking. Not with the cold, or not only with it.
[if has_flag("door_shut")] ~ He's coughing his lungs up on the top step, and I'm sitting here.
~ The Primus. It's something to do with my hands.

== ch5_cup mode=person
! set kettle_ch5=1
> [The Primus roars. The kettle ticks, and then it sings.]
[if has_flag("door_open")] ! set gave_cup=1
[if has_flag("door_open")] ~ I take down the other mug, the one I've never used, and fill it, and hold it out.
[if has_flag("door_open")] ROSS: ...Thank you.
[if has_flag("door_open")] ~ He holds it in both hands and doesn't drink. Just holds it.
[if has_flag("door_shut")] ~ I've poured two. I never thought about it. Two mugs, the way Father always did, summers.
[if has_flag("door_shut")] ~ I set his on the floor by the door, as if he could reach it.
```
*Note:* the Primus keeps working with the engine dead (the generator lock runs from the stair to the sediment bowl, Q17). An electric kettle would not, which is open question 4. "He's coughing his lungs up on the top step" also places him for the door-shut staging (section 8).

#### `ch5_ross`, `ch5_ross_2`, `ch5_ross_3` (RESTRUCTURED from `ch5_ross`)
- **No words change** except `ch5:8` (section 5.2) and one new opening thought for movement 3.
- **The split points:**
  - `ch5_ross` ends after `ch5:27` (`> [He coughs. It goes on too long.]`);
  - `ch5_ross_2` runs from `ch5:28` ("Two years ago I'm in the Mitchell Library…") to the three replies and their answers, and its `= calls` label now ends the conversation (`-> END`);
  - `ch5_ross_3` begins with the new thought, then the shipped `ch5:51` choice ("And the calls on sixteen…") through `ch5:78` ("…Look in the bottom drawer of that desk.").

```
== ch5_ross_3 mode=person
~ The wind's got into the stair. Neither of us says anything for a while.
* And the calls on sixteen. That was you. -> calls_ask
* (Say nothing.) -> calls_quiet
… (shipped text from ch5:53 to ch5:78, unchanged)
```
*Why the opening thought:* a conversation should not open on a bare reply, and the silence between movements is the point. The line works on both door paths.

### 6.3 Changed lines

| Line | Speaker · channel | Beat | Before → after | Reason |
|---|---|---|---|---|
| `ch5:8` | Callum · thought | `story` | "two inches of oak" → "the steel" | Steel door (5.2) |
| `ch5:123` | Elspeth · radio | `mayday` | "The flood tide's setting us down onto North Point faster than we can steer. Twelve souls aboard. Position one point two miles north-east of North Point Light. Over." → "The flood tide's setting us down onto North Point faster than we can steer." / "Twelve souls aboard. Position one point two miles north-east of North Point Light. Over." | SPLIT (7.6), keeping her words. The plan's draft changed "setting us down" to "carrying us", "souls" to "people" and "Position" to "We are". Those three are her bridge terms (master §4.9), and the 7.6 rule keeps a sea term when the next words explain it ("…faster than we can steer"). "Position" is the procedure word in a Mayday. Daniel may still prefer the plainer version |
| `ch5:124` | Morag · radio | `mayday` | one message → "Iona Star, Stornoway. Mayday received. Lifeboat is engaged at the Shiants, two hours." / "North Point Light is your nearest station. Over." | SPLIT: 134 characters |
| before `ch5:127` | — | `mayday` | (none) → `! set elspeth_named=1` | Her card shows her name from here on, even if she never gave it (the `curt` branch in chapter 3) |

---

## 7. Chapter 6, The Last Light

### 7.1 What changes
- **The story** is unchanged (plan 7.3).
- **Dawn:** two voices are heard at dawn. Visser, if the *Hendrika* was saved, thanks North Point through Stornoway. On the truth endings, MacAskill comes back on the air.
- **Canon fixes:** the cup, and Elspeth calling Callum by a name she was never told.

**Dawn beat, revised:** `timeskip 1830 "06:30"` … `talk ch6_hendrika_dawn`, `talk ch6_morag_dawn`, `talk ch6_sked_dawn`, `talk ch6_final_log` (the two new talks are self-gating: every line has its condition, so on other paths they show nothing).

### 7.2 New conversations

#### `ch6_hendrika_dawn` (NEW)
| | |
|---|---|
| Beat · trigger | `dawn`, before `ch6_morag_dawn`; plays only if `saved("Hendrika")` |
| Channels | radio (Visser to Stornoway; overheard) |
| Teaches / plants | The night had other ships in it, and the player kept one. Visser never speaks after chapter 3 except here, in the background (plan 17.7) |

```
== ch6_hendrika_dawn mode=radio
[if saved("Hendrika")] ! static
[if saved("Hendrika")] VISSER: Stornoway Coastguard, Hendrika. We weigh at seven for Stornoway. All well aboard. Over.
[if saved("Hendrika")] MORAG: Hendrika, Stornoway. Roger. Stornoway out.
[if saved("Hendrika")] VISSER: And Stornoway. Please thank North Point Light for us. Hendrika out.
```

#### `ch6_sked_dawn` (NEW): Sgeir Mhòr back on the air (truth endings)
| | |
|---|---|
| Beat · trigger | `dawn`, after `ch6_morag_dawn`; plays only if `told_truth` |
| Channels | radio |
| Teaches / plants | Closes MacAskill's thread: the silence of chapter 3 ends. The one outside keeper's view of what Callum has done, in four words ("That took doing"), with no speech and no forgiveness. On the lie endings the set stays quiet, which matches the epilogue's carrier "and I don't answer it" |

```
== ch6_sked_dawn mode=radio
[if has_flag("told_truth")] ! static
[if has_flag("told_truth")] MACASKILL: North Point, Sgeir Mhor. Back on the air. The aerial came down at two, and I've been up the mast with a torch since. Over.
[if has_flag("told_truth")] MACASKILL: I heard some of what you sent Stornoway. That took doing, Callum. Over.
* [if has_flag("told_truth")] It was in the book long enough, Murdo. Over. -> done
* [if has_flag("told_truth")] Good to hear you, Murdo. Over. -> done
-> END
= done
MACASKILL: Aye. Morning schedule at eight. Sgeir Mhor out.
```
*Knowledge check:* MacAskill hears only the end of Callum's report, once his aerial is back up. He knows Iain, and the Inquiry's public finding. "That took doing" is all he needs to understand.

### 7.3 Changed lines

| Line | Speaker · channel | Beat | Before → after | Reason |
|---|---|---|---|---|
| `ch6:7` | Elspeth · radio | `iona` | "North Point, Iona Star. I see your light. I see it. Callum Mackay, I need you to put me through the East Gut. I can't make the open sea against this. Over." → "North Point, Iona Star. I see your light. I see it." / `[if has_flag("elspeth_letter_told")]` "Callum Mackay, I need you to put me through the East Gut. I can't make the open sea against this. Over." / `[if not has_flag("elspeth_letter_told")]` "North Point, I need you to put me through the East Gut. …" | SPLIT and CANON. On the `curt` branch in chapter 3 ("North Point Light. That's all you need.") she never learns his name. `elspeth_letter_told` is set exactly on the branch where she does |
| `ch6:9` | Elspeth · radio | `iona` | "And Mr Mackay. A month ago someone wrote…" → "And North Point. A month ago someone wrote…" | CANON: this line plays only on that same `curt` path |
| `ch6:54` | Rory · radio | `standby` | one message → "North Point, Kittiwake. I heard the Mayday." / "I'm at the mouth of the Sound with every light I own switched on. If she wants a mark on the far side of the Gut, she's got one. Over." | SPLIT: 178 characters |
| `ch6:68` | Elspeth · radio | `rescue` (aground) | one message → "…Iona Star aground, North Point. We're holed forward." / "She's sitting upright. All twelve on the bridge. We'll hold till the lifeboat. Over." | SPLIT: 140 characters (borderline) |
| `ch6:99` | Callum · radio | `dawn` (truth) | "The light at North Point stopped turning at approximately oh-one-forty, and was extinguished from approximately oh-one-fifty until oh-two-oh-one." → "The light at North Point stopped turning at approximately oh-one-forty." / "It was extinguished from approximately oh-one-fifty until oh-two-oh-one." | CHANGED: one sentence becomes two (same facts), so the report reads as two plain statements on air |
| `ch6:120` | Callum · thought | `dawn` (lie, door open) | `[if has_flag("door_open")]` "Behind me Ross sets down the cup I gave him…" → `[if has_flag("door_open") and has_flag("gave_cup")]` (same words) / `[if has_flag("door_open") and not has_flag("gave_cup")]` "Behind me Ross lets go of the back of the chair, slowly, one finger at a time." | CANON: no cup was ever given in the shipped game, and on the `open_now` path (door opened only in chapter 6) none could be |

---

## 8. Ross cue points for Stage R
These are staging cues for Stage R (Addendum B, sections 6.4, 6.5 and 20.4). They are **not** `.dlg` text; Stage R turns them into actions. Positions: A, landing, hand on the rail; B, 0.6 m inside the door, hand on the frame; C, behind the desk chair, hand on its back; D, at the console handwheel; E, by the desk.

### 8.1 Door opened
| Cue | Where in the script | Position · clip | Light and sound |
|---|---|---|---|
| ▶ R-1 | `ch4_door` `= open`, the `! door_open` action (`ch4:108`) | A · breathe-idle, head down; waits until the player stands aside | Stair pendant behind as a rim; wall lamp 2 as a side key; rain off the brim |
| ▶ R-2 | "Thank you." (`ch4:113`) | A → B · two-step walk, hand to the door frame; water pools at his boots | Brim keeps eyes and upper face in shadow |
| ▶ R-3 | `ch5_ross` first line (`ch5:7`, "He won't take the chair") | B · weight shift, drip loop | Warm room on battery (the generator is locked: check the light level at the Stage R capture) |
| ▶ R-4 | every cough caption: `ch4:92`, `ch5:27` | where he stands · cough, turned away (two variants, never the same twice) | Cough take from the stair or room position |
| ▶ R-5 | `ch5_cup` "…and hold it out." / "…Thank you." | B · **new clip: takes the mug, holds it in both hands** (not in the B §6.6 clip list) | Mug prop handed over |
| ▶ R-6 | after `ch5_cup`, before `ch5_ross_2` (B: "after the kettle step") | B → C · walk, hand to the chair back, mug in the other hand | |
| ▶ R-7 | `ch5_ross_3` "Your father and I sat in this room…" (`ch5:67`) | C · looks once at the 1952 photograph on the wall | |
| ▶ R-8 | `ch5_mayday` "That's Elspeth." (`ch5:127`; `ch5:125` has his hand on the chair) | C · head up, half a step toward the radio | |
| ▶ R-9 | `ch6_jam` `= together` (`ross_wheel`) | C → E → D · sets the mug down at E on the way; wheel grip | Console instrument light on his hands |
| ▶ R-10 | `ch6_freed` "I have her." | D · wheel grip, holding | |
| ▶ R-11 | `ch6_outcome` `= father` (`reunion`) | D · reaches for the handset | |
| ▶ R-12 | `ch6_morag_dawn` `= silence` (lie), `ch6:120` | with `gave_cup`: to E, picks up the mug, sets it down (the line), turns, A, descends. Without it: lets go of the chair at C, turns, A, descends | Dawn through the windows; footsteps descending |
| ▶ R-13 | `ch6_morag_dawn` `= truth` | to E · sets the mug down (if `gave_cup`) and stands; he stays | Dawn |
| ▶ R-14 | `ch6_jam` `= open_now` (the door is opened only in chapter 6) | rises from the top step at A, then A → B on "There's the boy."; C if he is not given the wheel | Stair pendant rim, as R-1 |

### 8.2 Door kept shut
| Cue | Where in the script | What is seen | Sound |
|---|---|---|---|
| ▶ S-1 | ch4 `steps`, from "[Footsteps on the stair…]" | Warm light grows in the 20 mm gap under the door as he climbs | Steps one at a time; breath |
| ▶ S-2 | ch4 `steps`, "[Three slow knocks]" | A shadow breaks the light in the gap | Three knocks |
| ▶ S-3 | `ch4_door` `= shut`, before "…Aye. I'd have done the same" | The wheel is tried once from outside, a quarter turn, and released | Wheel rasp, close and dry; the second cough at the door |
| ▶ S-4 | `! sfx paper_slide` (`ch4:118`) | A corner of card in the gap; a pause; it slides 30 cm onto the floor, face down. Turning it over is the pickup | Paper on concrete |
| ▶ S-5 | `ch5_ross` (`ch5:8`) | Callum sits against the door (camera low). **Ross stays standing, leaning on the door:** the boots' shadow stays in the gap | Through-door voice bed |
| ▶ S-6 | `ch5_cup` (door shut) | The second mug set on the floor by the door, steaming | |
| ▶ S-7 | `ch5_mayday`, "Behind the door, something heavy slides down to the floor" (`ch5:126`) | **The shadow drops: he sits on the top step here** | A heavy slide against steel |
| ▶ S-8 | `ch6_morag_dawn` `= silence`, "[Footsteps going down the stair…]" (`ch6:122`) | The gap light dims as he goes down; the mug by the door untouched | Footsteps descending |
| ▶ S-9 | truth endings with the door shut | The shadow stays in the gap | Breathing |

**Change to Addendum B §6.4.** The storyboard had Ross sit on the top step at the start of chapter 5. `ch5:126` ("something heavy slides down to the floor") happens at the Mayday, so he stands until then (S-5, S-7). The alternative is to cut `ch5:126`, but it is the door-shut path's best moment.

---

## 9. Canon check
NARRATIVE.md is the superseded 2026-11-04 draft ("Superseded (2026-11-06)" at its head); canon is `STAGE3_NARRATIVE_MASTER.md`, `character-refs/CANON_INDEX.md` and the shipped text (CANON_INDEX's precedence). Weekdays were checked with Python's calendar.

### 9.1 Names, ages, dates, call signs

| Item | NARRATIVE.md | Canon now | This script | Status |
|---|---|---|---|---|
| Callum Mackay | 41, principal keeper; 23 in 1953 | Born 1930, Tarbert; assistant here 1950 to 1955; principal keeper from 1962 | Unchanged. Hector's thought no longer calls him "a boy on these stairs" | ✓ |
| Morag Fraser | Coastguard radio officer, oldest friend | 44 (26 in 1953); HM Coastguard Stornoway, not "MRSC" (CANON_INDEX §8) | Says "Stornoway Coastguard" only | ✓ |
| Rory Bain | 22, *Kittiwake* | 22, SY 37; grandson of Kenny Bain (died Easter 1971) | Unchanged | ✓ |
| Hector Macleod | not in NARRATIVE | About 68, schooner *Gannet*, SY 112, forty years on the Harris coast | Overheard in ch1; "since before I could tie my boots" (Callum was about one in 1931) | ✓ |
| Elspeth Ross | "ferry mate" | 29, mate of the coaster MV *Iona Star*, GMXQ, twelve souls | Coaster; "Twelve souls aboard" in ch2, ch3, ch5; card hidden until named | NARRATIVE superseded; ✓ |
| Alasdair Ross | 64; "broken pelvis" | 64, born 1907, Leverburgh; broken hip (`ch5:12`) | Unchanged | NARRATIVE superseded; ✓ |
| Iain Mackay | 49 in 1953 | 1904 to March 1958; principal keeper 1946 to 1958 | Gillies: reported the tooth "when I was a mate" (1949: Gillies about 33) | ✓ |
| Mrs Ross; Callum's mother | not named | Unnamed by decision (REVIEW_FLAGS G06, I11) | Not mentioned | ✓ |
| Death count | seven of eight lost | Eight aboard; officially seven lost; six died | Unchanged (Morag, `ch2:9`) | ✓ |
| Night of the wreck | 14 to 15 Nov 1953 | Saturday 14 to Sunday 15 Nov 1953 | — | ✓ (14 Nov 1953 was a Saturday) |
| Tonight | 14 to 15 Nov 1971 | Sunday 14 to Monday 15 Nov 1971 | "Thursday" relief (Gillies) = 18 Nov 1971 | ✓ (Sunday; 18 Nov a Thursday) |
| The Inquiry | "1954" | Concluded at **Inverness**, 17 March 1954; *Gazette* Thursday 18 March (both documents print Inverness) | Not mentioned in any line | Master §12.2's `inquiry_extract` title still says "Stornoway". Correct that note in part 2 (CANON 7.5); no `.dlg` change |
| 1953 times | Mayday 01:52, struck 01:58 | Stalled 01:40; dark 01:50 to 02:01; Mayday 01:52; struck 01:58; false entry 02:10 | Unchanged; `ch6:99` split keeps every figure | ✓ |
| Tonight's call | 23:58 | 23:58 in all text; **23:57 in `chapters.json`** (clock 1437) | Clock 1438 | Fixed (CANON 7.5) |
| The 046 reports | — | 4.3.49 I.M.; 9.12.53 C.M.; **2.2.63** C.M. (note_046) | `ch2:102` "Sixty-one" → "Sixty-three" | Fixed |
| Radio check | — | Card: "Radio check 2100"; tonight's first call 18:30 | 21:00 check added; Morag "always early" | Fixed (CANON 7.5) |
| Tide Tables 1953 | — | The 1953 volume was added in Stage A | Unchanged | ✓ (done) |
| Barometer | — | 13.11, 14.00: 1004 mb, falling (the day-before log) | 981 at 20:00; 976 at Sgeir Mhòr / 973 at North Point about 00:25 | New; consistent |
| Wind | south-westerly gale | South-west throughout | *Lowestoft Star* no longer "running before it from the north" | Fixed |
| The gale warning | — | 1600 sheet: "severe gale 9 increasing storm 10 imminent" | 18:30 Morag: "gale nine before dawn" kept as her near-term figure; 22:00 sheet "storm 10 imminent" | Noted; no change |
| *Catriona* | — | Wooden, the *Mary Ellen*'s sister, Fraserburgh yard; sold for breaking 1969 to "a Mr Morrison, Govan" | "Razor blades" line replaced | Fixed |
| The stair door | — | Steel bulkhead, handwheel, two dogs (Stage S; Daniel 2026-11-16) | Four lines and one prompt; "oak" gone from `ch4:129` and `ch5:8` | Fixed |
| The cup | — | `ch6:120` "the cup I gave him"; no cup in the shipped game | `gave_cup`, given in ch5 | Fixed |
| Elspeth knows his name | — | `ch6:7`, `ch6:9` use "Callum Mackay" and "Mr Mackay" on every path | Gated on `elspeth_letter_told` | Fixed |
| Call signs | — | *Kittiwake* SY 37 · *Gannet* SY 112 · *Corrie May* BRD 9 · *Lowestoft Star* LT 401 · *Mary Ellen* SY 214 · *Iona Star* GMXQ | New: *Hendrika* PEJX (Dutch series, invented); *Sula*, *Western Venture* and Sgeir Mhòr give none (station names on the radio) | ✓ (new ones are invention) |
| Spoken phonetics | — | "Sierra Yankee three-seven" (`ch1:64`) | "Golf Mike X-ray Quebec", "Papa Echo Juliett X-ray" | ✓ |
| Places | Pabbay, Leverburgh, Tarbert | adds Scalpay, Stornoway, the Shiants, the Flannans, Fraserburgh, Govan, the Mitchell Library | New: Neist Point (real, Skye); Sgeir Mhòr (fictional, like North Point) | ✓; Neist Point to check (section 10) |
| Language | English only | One Gaelic song title; no Gaelic for atmosphere (CANON_INDEX §8) | "Fear a' bhàta" unchanged; "Sgeir Mhòr" is a place name | ✓ |
| Radio procedure | — | "over" / "out", never "over and out"; Channel 16 for calling | Marsh is told "Keep it short on sixteen" | ✓ |

### 9.2 New voices (for `character-refs/` in part 2; none is stated in dialogue)
| Voice | Age | Where | Knows of 1953 | Appears |
|---|---|---|---|---|
| Capt. Jan Visser | about 50 | MV *Hendrika*, Dutch coaster, timber for Stornoway; his wife sails as cook | Nothing | ch3; ch6 dawn if saved |
| Neil Gillies | about 55 | NLB tender *Sula*, lying at Stornoway | The official version only; says nothing of it | ch1 |
| Dr Helen Marsh | about 35 | survey vessel *Western Venture*, sheltering | Nothing | ch2 |
| Murdo MacAskill | about 58 | principal keeper, Sgeir Mhòr, a fictional rock light to the south, relieved by the *Sula* | Knew Iain; the public finding only | ch1, ch2, (ch3 silent), ch6 dawn on truth endings |

---

## 10. Period claims: checked 2026-11-17
Open question 6 was decided as recommended, and the check was run the same day. It used web searches of public sources only, with generic queries that mention nothing about Daniel or the project. Each claim below is **Confirmed** (a source supports it), **Plausible** (a source supports the background but not the detail), **Invention** (stays fiction, and nothing found contradicts it) or **Open** (nothing found). Not every search was exhaustive; the sources are listed under the table.

| Claim | Where | Result | Script change |
|---|---|---|---|
| "Imminent" in a gale warning means within six hours of issue | `ch3:6`, `after_forecast_2200` | **Confirmed** by the Met Office marine glossary [1] ("imminent" within 6 h; "soon" 6 to 12 h; "later" more than 12 h). The glossary is current; the same terms in 1971 is likely but not shown | None; the plan's "within the hour" stays out |
| GMT on 14 November 1971 | teleprinter sheets ("1600 GMT", "2200 GMT") | **Confirmed**: the British Standard Time experiment (GMT+1 all year) ran from 27 October 1968 to 31 October 1971, then the UK went back to GMT [2] | None |
| Dutch merchant call signs | Visser, "PEJX" | **Confirmed**: the Netherlands' ITU series is PAA to PIZ [3]. A check that PEJX was not a real 1971 ship is **Open** | None |
| "Automatic inside ten years" | Marsh | **Plausible as her hearsay**: the NLB's first conversion to an unattended light was in 1970, and a big push of automation ran from 1960 to 1980, finishing in 1998 [4] | None |
| Keepers kept weather records | MacAskill's glass; the barometer duty | **Confirmed**: Scottish keepers had to keep meteorological records twice a day from 1868 [5] | None |
| Keepers gave observations to ships and to other lights by radio, on a nightly "schedule" | MacAskill (ch1 to ch3, ch6); Marsh (ch2) | **Open**: nothing found on NLB inter-station radio schedules [6]. Treat as **invention** in the game's credits or notes if asked; it fits the record-keeping duty above | None |
| NLB tender relief "weather allowing", with stores and tradesmen | Gillies | **Plausible**: the NLB fleet carried relief and supplies [7]; the details are invention | None |
| *Sula* as an NLB tender | Gillies | **Invention**: no NLB vessel of that name found in the fleet index or in searches [7][8] | None |
| *Western Venture*, *Hendrika*, Sgeir Mhòr | — | **Invention**; nothing found that clashes (not searched exhaustively) | None |
| A seismic survey party sheltering in the Minch in 1971 | Marsh | **Plausible as a research survey**: 1971 seismic and geophysical research cruises worked west of the Hebrides and Shetland (RRS *Surveyor*, RRS *Researcher*). Oil-industry seismic work in the Minches is recorded only later (a 1977 parliamentary answer) [9] | None. Her lines never mention oil; the notes for part 2 make her party a research survey (section 13) |
| The Glasgow to Stornoway route passes Neist Point | `ch2_iona_heard` | **Open**: the old Clyde to Stornoway service ran by the Mull of Kintyre [10], which is consistent with going north past Skye's west coast (Neist Point) into the Little Minch. No source names the waypoint | None. Check on a chart in part 2, or change it to "south of Skye" |
| A teleprinter forecast in a lighthouse watch room in 1971 | `forecast` (in the game since Stage B), `forecast_2200` | **Open**: not searched to a result. Treat as invention | None |
| Fear a' Bhàta | `look_clockwork` (hum), `ch4:68` | **Confirmed traditional**: late 18th century, author unknown (the Jean Finlayson story is a legend) [11]. The melody is long out of copyright; any recording (Stage D) must be new or properly licensed | None |
| The Primus is lit by pre-heating with methylated spirit in its cup | `look_kettle_a` | Standard practice; not searched | None |

**Sources:**
1. Met Office, [Marine forecasts glossary](https://weather.metoffice.gov.uk/guides/coast-and-sea/glossary) and [Guide to marine forecasts](https://weather.metoffice.gov.uk/guides/coast-and-sea).
2. [tz database mailing list, Europe/London 1968 to 1971](https://mm.icann.org/pipermail/tz/2014-September/021596.html); [Hansard, British Standard Time debate, 2 December 1970](https://api.parliament.uk/historic-hansard/commons/1970/dec/02/british-standard-time); [British Summer Time (Wikipedia)](https://www.wikipedia.org/wiki/BDST).
3. [ITU prefix (Wikipedia)](https://Www.Wikipedia.org/wiki/ITU_prefix); [International call sign prefix allocations (ARRL table)](https://www.qsl.net/ve3xap/$alloc.htm).
4. [Canmore event record (first NLB light converted to unattended automatic operation, 1970)](https://canmore.org.uk/event/575706); [The Scotsman, "When Scotland's last lighthouse keeper turned off the lights"](https://www.scotsman.com/arts-and-culture/when-scotlands-last-lighthouse-keeper-turned-off-the-lights-336136).
5. [National Records of Scotland, "A place of threat"](https://nrscotland.gov.uk/learning-and-events/for-the-safety-of-all-scotlands-lighthouses/a-place-of-threat/); [Met Office, ship, light vessel and lighthouse logs](https://www.metoffice.gov.uk/research/library-and-archive/archive/ship-logs).
6. [National Records of Scotland, lighthouses research guide](https://nrscotland.gov.uk/learning-and-events/research-guides/lighthouses/) (NLB correspondence 1901 to 1987, a lead for a deeper check).
7. [Granton history, Northern Lighthouse Board fleet](https://grantonhistory.org/harbour/lighthouse_vessels_index.htm).
8. [Find a Tender, NLB vessel notices](https://www.find-tender.service.gov.uk/Notice/011111-2021) (recent fleet only).
9. [BODC cruise summary report 9426](https://www.bodc.ac.uk/resources/inventories/cruise_inventory/report/9426/); [BODC cruise summary report 8252](https://www.bodc.ac.uk/resources/inventories/cruise_inventory/report/8252/); [Hansard, oil exploration, Minches and Western Isles, 28 November 1977](https://api.parliament.uk/historic-hansard/written-answers/1977/nov/28/oil-exploration-minches-and-western-isles).
10. [Dalmadan, "All the way to Stornoway"](https://www.dalmadan.com/?p=6638).
11. [Fear a' Bhàta (Wikipedia)](https://en.wikipedia.org/wiki/Fear_a%27_Bh%C3%A0ta); [Mainly Norfolk, Fhír a Bhata](https://www.mainlynorfolk.info/sandy.denny/songs/fhirabhata.html).

---

## 11. Reading time

**Formula** (`11_stageA_evidence.md`, D1):
- 1.0 s + 0.06 s per character, clamped 2.8 to 12 s;
- +0.7 s on a change of speaker, +0.4 s for a message ending in a full stop;
- counted per page.

**Method:** a scratch interpreter of the `.dlg` files.
- It walks the beats in order, following labels and `[if]` conditions with each path's flags.
- Choices are not timed, since they wait for the player; the number per path is given.
- Pages come from the calibrated measure (section 12).
- Waits inside conversations (`! wait`) are counted separately: under 10 s per chapter.

**Calibration:** run on the shipped files with Stage 0's formula (clamp 9 s, no extras, every branch summed), it gives **38.5 min** against Stage 0's **38.3 min**. The 0.1 min of `system.dlg` explains most of the difference.

**Paths:** each ending with the door opened and with it shut, taking the optional calls. The other choices take the first reply offered.

| Ending | Door | Ch1 | Ch2 | Ch3 | Ch4 | Ch5 | Ch6 | **Total, shipped → revised** | Replies |
|---|---|---|---|---|---|---|---|---|---|
| Correction (truth, saved) | open | 5.9 → 9.0 | 4.8 → 6.8 | 5.1 → 7.3 | 3.2 → 3.4 | 6.2 → 6.8 | 4.3 → 4.9 | **29.5 → 38.2** | 33 → 46 |
| Correction | shut | 5.9 → 9.0 | 4.8 → 6.8 | 5.1 → 7.3 | 3.4 → 3.5 | 6.2 → 6.8 | 3.9 → 4.5 | **29.3 → 37.9** | 33 → 46 |
| Heard Together (truth, aground) | open | 5.9 → 9.0 | 4.8 → 6.8 | 5.1 → 7.3 | 3.2 → 3.4 | 6.2 → 6.8 | 4.1 → 4.8 | **29.4 → 38.1** | 32 → 45 |
| Heard Together | shut | 5.9 → 9.0 | 4.8 → 6.8 | 5.1 → 7.3 | 3.4 → 3.5 | 6.2 → 6.8 | 4.2 → 4.8 | **29.6 → 38.2** | 32 → 45 |
| Nothing to Report (lie, saved) | open | 5.9 → 9.0 | 4.8 → 6.8 | 5.1 → 7.3 | 3.2 → 3.4 | 6.2 → 6.8 | 3.7 → 4.0 | **29.0 → 37.4** | 33 → 45 |
| Nothing to Report | shut | 5.9 → 9.0 | 4.8 → 6.8 | 5.1 → 7.3 | 3.4 → 3.5 | 6.2 → 6.8 | 3.1 → 3.4 | **28.6 → 36.8** | 33 → 45 |
| Light Exhibited Throughout (lie, aground) | open | 5.9 → 9.0 | 4.8 → 6.8 | 5.1 → 7.3 | 3.2 → 3.4 | 6.2 → 6.8 | 3.4 → 3.7 | **28.7 → 37.1** | 32 → 44 |
| Light Exhibited Throughout | shut | 5.9 → 9.0 | 4.8 → 6.8 | 5.1 → 7.3 | 3.4 → 3.5 | 6.2 → 6.8 | 3.3 → 3.6 | **28.7 → 37.0** | 32 → 44 |

All times are minutes.

**Without the optional calls** (and the optional clockwork, kettle and sheet in chapter 1): shipped 25.9 to 26.9 min, revised 33.5 to 34.9 min.

**Every branch summed:**

| Formula | Shipped | Revised |
|---|---|---|
| Stage 0's (clamp 9 s, no extras) | 38.5 min (Stage 0 measured 38.3) | 48.4 min |
| Today's (above) | 43.6 min | 53.5 min |

**What this means:**
- **Dialogue added per path:** about +8.5 min.
- **Play time added (an estimate, not measured):** the plan's +25 min also counts play time. The new duties carry it: the call, the glass, the crank and kettle, the fuel run (about 3 min, plan 10.4), the *Hendrika* job (about as long as the *Gannet*'s, 4 to 5 min), and the cup. A rough total for dialogue plus play is +20 to 25 min.
- **Measured runtime:** only Daniel's timed playthrough in Stage G gives a real figure; this is NOT TESTED.

---

## 12. Three-line page risks
**Measure:** the game's LibreBaskerville at weight 500, in the radio column (606 px at size 25) or the subtitle column (1280 px at 28, italic for thoughts), less the 3 px margin, with greedy word wrap as `TextParagraph` does.
- **Strict measure:** Pillow's layout has no kerning and reads slightly wide, so the unscaled measure is strict.
- **Calibrated measure:** widened 4 %, it reproduces Stage A's 16 paged messages at x1.0.
- **"Border" lines** are those that page only on the strict measure.

**Shipped, at text x1.0 (20 strict, 16 calibrated). Every one is resolved by a change above:**

| Line | Characters | Lines (strict / calibrated) | Pages | Resolved by |
|---|---|---|---|---|
| `ch1:45` Morag | 135 | 4 / 3 (border) | 2 | SPLIT, 2.3 |
| `ch1:66` Rory | 190 | 5 / 5 | 3 | SPLIT into three, 2.3 |
| `ch1:84` Rory | 165 | 4 / 4 | 2 | SPLIT into three, 2.3 |
| `ch1:91` Rory | 134 | 4 / 3 (border) | 2 | SPLIT, 2.3 |
| `ch2:113` Rory | 164 | 4 / 4 | 2 | SPLIT, 3.3 |
| `ch2:129` Morag | 138 | 4 / 4 | 2 | SPLIT, 3.3 |
| `ch3:6` Morag | 192 | 5 / 5 | 2 | SPLIT into three (7.6), 4.3 |
| `ch3:29` Elspeth | 133 | 4 / 4 | 2 | SPLIT, 4.3 |
| `ch3:66` Morag | 171 | 4 / 4 | 2 | SPLIT, 4.3 |
| `ch3:80` Morag | 145 | 4 / 4 | 2 | SPLIT, 4.3 |
| `ch3:109` Rory | 173 | 5 / 5 | 2 | SPLIT, 4.3 |
| `ch3:119` Hector | 165 | 4 / 4 | 2 | SPLIT, 4.3 |
| `ch4:35` Callum | 145 | 4 / 4 | 2 | SPLIT, 5.3 |
| `ch4:80` Morag | 145 | 4 / 4 | 2 | SPLIT, 5.3 |
| `ch5:123` Elspeth | 164 | 4 / 4 | 2 | SPLIT (7.6), 6.3 |
| `ch5:124` Morag | 134 | 4 / 3 (border) | 2 | SPLIT, 6.3 |
| `ch6:7` Elspeth | 155 | 4 / 4 | 2 | SPLIT and CANON, 7.3 |
| `ch6:54` Rory | 178 | 4 / 4 | 2 | SPLIT, 7.3 |
| `ch6:68` Elspeth | 140 | 4 / 3 (border) | 2 | SPLIT, 7.3 |
| `ch6:99` Callum | 145 | 4 / 4 | 2 | Two sentences, 7.3 |

**Revised, at text x1.0:** **0** messages page on either measure, and every new message passes the strict one. No line in the revised script is a three-line-page risk at x1.0.

**For information, at x1.5:** the paginator still pages long messages, as it must at the largest text size (about 28 characters to a line). There are 65 paged messages in the shipped files on the calibrated measure (Stage A measured 72) and 76 in the revised script. Those are handled at run time, not by the script.

---

## 13. Notes for Stage C part 2 (data), once this script is approved
These are not dialogue. They list what part 2 has to build, so nothing above is approved without its cost being visible.

- **Beats** (`chapters.json`):
  - ch1 `sula`, `round`, `sked`, `check`, `hector_heard`, `teleprinter` between `kittiwake_home` and `late`;
  - ch2 `iona_heard`, `sked`, `marsh`;
  - ch3 `fuel` first, `sked3`, `hendrika`, `hendrika_in`;
  - ch5 `cup`, `story2`, `story3`;
  - ch6 `dawn` gains two talks.
  - Shipped ids are kept, so saves resolve by id (save v2). No `beat_aliases` are needed, since nothing is renamed; `story` stays movement 1.
  - Clock changes: ch1 (timeskips 1200 and 1260, rate 0.4 after 21:00, `mary_ellen` 1438) and ch3 (rates 0.06 and 0.04, `clock 1560`). The new waits are given in each chapter's table.
- **Duties:** `sula`, `round` (optional subs), `fuel`, `hendrika`, `kettle_ch5`, each with nudge and hint text in Callum's register. `forecast` waits on `fuel_done`.
- **Backfill** for saves made before the change (save v2 `backfill`):
  - `elspeth_named` for any save at or after ch3 `notes` if `elspeth_letter_told`, and for any save at or after ch5 `mayday`;
  - everything else defaults safely: no `sang` means no ch4 line; no `gave_cup` means the chair line; no `board_noted` means no ch2 line.
- **Speakers** (`speakers.gd`):
  - `GILLIES`, `MACASKILL`, `MARSH`, `VISSER` (known on first contact);
  - `ELSPETH` gets `hidden_as` a new `IONA` entry ("Iona Star", "IONA STAR · GMXQ", "Coaster · the mate") with `reveal: "elspeth_named"`;
  - `fix_heights()` already reserves the tallest identity block, so check the panel at three text sizes.
- **Radio panel:** the *Sula* as a callable station during `sula`. The `sked` calls are incoming, so nothing new is needed for them.
- **Ship:** `Hendrika` (the `steamer` kind until Stage E's coaster model); the bot taught to run the job; `sim_v2` gates rerun.
- **Documents and props:**
  - `forecast_2200` (new teleprinter sheet), `log_1971` with the 21.00 row;
  - a teleprinter machine (there is only a sheet today);
  - the Primus and kettle on the west sill (none today; the two enamel mugs exist);
  - the barometer needle reading 981 in chapter 1 (`documents.barometer_dial`);
  - the standby clockwork crank, which `build.py` places "outside the glazing": either reachable from the watch room or the sub is dropped;
  - the inquiry title in master §12.2 corrected to Inverness.
- **Sounds:** `teleprinter`, Primus roar and kettle, hand pump, wheel and dogs (exists). The hummed bar (Daniel or CC0, Stage D).
- **Code text:** `game_fp.gd:699` "· dogged hard"; `_use_door` must allow the door to open in the ch3 `fuel` beat.
- **Tests:**
  - story_test campaigns must cover the new duties on both door paths, every new conversation, and all four endings;
  - the canon lint (plan 13) should check the names, ages and dates of section 9;
  - `qa_sweep` must stay at three lines or fewer on every page;
  - `save_compat_test`: all 70 fixtures must still load onto the right beats.
- **Dr Marsh's party** is a research survey (section 10), not an oil company's; her character profile says so.
- **Character refs:** add profiles for the four new voices to `character-refs/`, and CANON_INDEX rows for them.

---

## 14. Open questions for Daniel
**Decided 2026-11-17: all seven as recommended** (Daniel: "I will go with recommendations on open questions"):
1. MacAskill at Sgeir Mhòr (fictional).
2. Line cards now; a portrait later only if Daniel makes one (Visser first).
3. Journal notes later, after the Stage G playthrough.
4. The Primus.
5. Elspeth's card hidden until she is named.
6. A short web check of the period claims: **done 2026-11-17** (section 10). Nothing found needs a line changed; three items stay open for a chart or archive check.
7. Elspeth's own Mayday terms, split only.

The questions as put, with their reasoning, follow.

1. **The neighbouring keeper's name and station.** **Recommended: Murdo MacAskill, principal keeper of Sgeir Mhòr**, a fictional rock light to the south, relieved by the same tender *Sula*.
   - A fictional station keeps the game free of real-world history claims, as North Point does. A real light, such as Eilean Glas on Scalpay (Kenny Bain's island), would bring dates to get right.
   - MacAskill is a Harris and Skye name and sits well beside Mackay and Macleod. Say if you want a different name or station; it changes about twenty lines mechanically.
2. **Portraits or line cards for the new voices.** **Recommended: line cards now**, from the card drawings the game already has (`speakers.gd` `art`): the `steamer` drawing, as the *Iona Star*'s, for the *Hendrika*, the *Western Venture* and the *Sula*; the `station` drawing for Sgeir Mhòr. Portraits come later only if you make them (Q13 template).
   - Each voice has one or two short scenes, and plan 17.7 caps them so they don't crowd the cast.
   - If you make one portrait, make it Visser: the only one with a navigation job and a second appearance.
3. **Automatic journal notes in Callum's voice** (plan 14.4, PROPOSAL_37 §4). **Recommended: later**, after your timed playthrough in Stage G.
   - The Tonight page and Kept papers (Stage B) already cover duties and documents.
   - Notes would add about a dozen lines that repeat his thoughts. They only earn their place if a real playthrough shows players losing the thread.
4. **The kettle: a paraffin Primus or an electric kettle.** **Recommended: the Primus.** It works with the engine dead (the generator lock covers chapter 5), it is period for a 1971 rock station, and "pump her up" echoes the vapour burner that starved in 1953 (`look_vapour_b`). An electric kettle would need its lines rewritten and would fail during the lock.
5. **Hide Elspeth's name on her card until she gives it.** **Recommended: yes.**
   - Today the card names her ("Elspeth Ross · 1st mate E. Ross") from her first line in chapter 3, which spoils "This is Elspeth Ross" and the overheard report in chapter 2.
   - If no: drop the two `elspeth_named` lines, and the chapter 2 thought "Whoever she is" should go.
6. **Checking the period claims (section 10).** **Recommended:** allow a short web check in a later session, before part 2 ships. It means public sources only, nothing about you or the project sent, and each result recorded as verified or as invention. Today they are all marked.
7. **The Mayday wording (`ch5:123`).** **Recommended: keep Elspeth's own terms** ("setting us down", "souls", "Position") and only split the message. If you prefer the plan's plainer draft, it is a direct swap.

---

## 15. As built: Stage C part 2 (2026-11-17)
Part 2 was built on a local branch (`stage-c-data`, in a git worktree) so that the Stage P session's test runs never saw half-finished story files. It was then merged into `main` locally. Nothing was pushed.

### 15.1 What is in the game
- **Dialogue:** every line in sections 2 to 7, transcribed from this document into `ch1.dlg` to `ch6.dlg`. A script compared all 25 printed conversations with the files: 0 differences.
- **Beats** (`chapters.json`, layout 5):
  - ch1 17 beats (`sula`, `round`, `sked`, `check`, `hector_heard`, `teleprinter` after `kittiwake_home`), with the *Sula* as an optional call in the radio panel during `sula`; `mary_ellen` at clock 1438;
  - ch2 11 (`iona_heard`, `sked`, `marsh`);
  - ch3 11 (`sked3`, `hendrika`, `hendrika_go`, `hendrika_in`), the slower clock and the longer waits;
  - ch5 9 (`cup`, `story2`, `story3`);
  - ch6's dawn plays `ch6_hendrika_dawn` and `ch6_sked_dawn`.
  - New duties: `sula`, `round` (glass, plus the optional crank and kettle), `hendrika`, `kettle_ch5`.
  - New log row: `log_2100`.
  - Backfill: `elspeth_named` for saves at or past ch3 `notes`.
- **Saves:** `StoryState.LAYOUT` 4 → 5, with remap rows for chapters 1, 2, 3 and 5. Version-2 saves resolve by beat id as before.
- **Speakers:** `GILLIES`, `MACASKILL`, `MARSH`, `VISSER` (line cards, no portraits). `ELSPETH` shows as `IONA` ("Iona Star · the mate") until `elspeth_named`; her photograph appears on her card at the moment she names herself.
- **Room** (`build.py`, `last_light_v078.blend`, `watch_room.glb`):
  - `IA_barometer`, and the needle as its own part `NDL_barometer`, turned by `station.gd` from the story clock (988 mb at 16:20, 981 at 20:00, 973 at 00:25, 960 before four, 970 at dawn);
  - `IA_clockwork` on the standby crank;
  - a Primus under the kettle, with `IA_primus`;
  - a teleprinter on its own stand under the east bay's sill;
  - room triangles 128,090 → 128,802, materials still 33.
- **Code:**
  - `station.gd` has the three new devices and the barometer table;
  - in `game_fp.gd`:
    - the barometer, crank and Primus lines;
    - the 22:00 sheet opened from the forecast sheet once `teleprinter_2200` is set;
    - the door prompts "Dog the stair door hard" and "The stair door · dogged hard".
- **Documents:**
  - `forecast_2200` (new) and `log_1971` (the 21.00 row) via `documents.py --extra=forecast_2200,log_1971` (refactored: the rows live in `rows_1971()`);
  - `log_strips.py` (new log row and duty strips);
  - `ending_pages.py` (the three P3 log panels now carry the 21.00 row).

### 15.2 Where the build differs from the approved text, and why
| Item | Approved text | As built | Why |
|---|---|---|---|
| The fuel run (4.1) | Chapter 3 opens with `fuel`; the forecast waits for `fuel_done` | `ch3_fuel`, `ch3_pump`, `ch3_fuel_done` are in `ch3.dlg` but no beat plays them yet; the forecast still opens the chapter | The lower level has no colliders and the ladder can't be climbed (Stage S, section 4 of its record). The roadmap puts the fuel run in Stage F, which wires this beat |
| The *Hendrika*'s spawn (4.2) | `! ship {...}` inside `ch3_hendrika` | The beat `hendrika_go` (skipped unless `helped_hendrika`) spawns her and gives the duty | A `!` line is split on spaces, so it cannot carry JSON. The dialogue is unchanged |
| The kettle (2.2, 6.2, question 4) | "The room has no kettle yet" | **Wrong:** the room already had a green enamel kettle on an electric ring at bearing −42 on the west sill (cabin pass). As built, that kettle now stands on a Primus, in place of the ring | It keeps the decided Primus and the room's own kettle; no second kettle. **If Daniel prefers the electric ring back, say so:** the Primus lines (`look_kettle_a`, `ch5_kettle`, `ch5_cup`, two hints) would then need rewording, and the cup would fail during the generator lock |
| The teleprinter (2.2) | "The room has the 1600 sheet but no teleprinter machine" | A teleprinter on a steel stand at bearing 30, under the east bay's sill (top 0.86 m), between the desk's right end and the optic drive | Placed by a top-down and an eye-level check in Blender. Not yet seen in the game (section 15.4) |
| The crank (2.2) | "If the player cannot reach it, the sub is dropped" | Reachable: "outside the glazing" means the optic drive's glazed case, and the crank is 0.42 m above the watch-room floor on its pedestal | — |
| Bots and tests | — | A beat may name, for bot mode only, the player steps it waits on (`"bot_player": {"set": [...], "calls": [...]}`): `sula` places the *Sula* call, `sked` reads the glass, `cup` lights the Primus. Real play never reads it | One mechanism instead of teaching six test drivers the same three steps |
| `story_test` flag audit | — | Searches `chapters.json` with its escaped quotes undone | A flag read only in `chapters.json` (`has_flag(\"x\")`) was invisible to it |

### 15.3 Verification (worktree, final state, headless under taskpolicy -b)
| Check | Result |
|---|---|
| story_test | PASS (0 failed): all four endings, the reunion and the door-shut campaign; the *Hendrika* brought in on policy 0 and the scenarios, declined on policies 1 and 2; generator lock unchanged; 15 autosaves resume on a new conversation; flag audit 45 set, 0 unread |
| save_compat_test | PASS (305): every v1 fixture lands on its beat id under layout 5 |
| opening_test | PASS (31 / 31) |
| regress_test | PASS (417 / 417). Three checks that hard-coded chapter 2 beat indexes now look the beat up by id; the two door-prompt checks expect the steel-door wording |
| qa_sweep_test | PASS (7,703): every page of every line, new voices included, three lines or fewer at x0.8 / x1.0 / x1.5; the panel rect is unchanged |
| interaction_test | PASS (164 checks, 11 warnings: the standing "no sound when a document opens", Stage D) |
| run_tests | PASS (95) |
| sim_v2, seeds 1 to 5 | PASS, no gate failures |
| g5_weather_audio_test | PASS (50) |
| pytest | PASS (the ending P3 panels re-rendered for the 21.00 row) |
| Pipeline (v078) | validation FAIL = 0 for watch_room, lighthouse and stairwell; reimport ok; synced |
| New props, by eye in Blender | PASS: the barometer needle at about 981 mb; the kettle on the Primus beside the mug and tin; the teleprinter between the desk and the optic drive, clear of both, with the compass sill free above it; the crank handle on the drive pedestal (renders `renders/last_light/c2_v076/`, `c2_v077/`; gitignored, reproducible with `review_views.py --views cu_primus,cu_teleprinter,cu_baro,cu_crank`) |
| In the game | NOT TESTED (window batch needs Daniel's OK) |

### 15.4 Not done, and why
- **In-game captures of the new props and lines: NOT TESTED.** They need a window batch with Daniel's OK (`tools/godot_bg`). Suggested shots:
  - `cu_desk_r` with the teleprinter;
  - the barometer at 20:00 and at 02:00;
  - the Primus on the sill;
  - the radio panel with Visser's and MacAskill's cards and Elspeth's hidden card, at text x1.0 and x1.5;
  - the dogged-door prompt.
- **Sounds:** `teleprinter`, the Primus roar, the kettle and the hummed bar are not made (Stage D). The lines' captions carry them meanwhile.
- **The fuel run:** Stage F (above).
- **Character profiles** for the four new voices in `character-refs/`, with CANON_INDEX rows: not written yet.
- **The three period claims still open** (section 10): the keepers' schedules, Neist Point, the teleprinter.
