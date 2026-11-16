# THE LAST LIGHT: Addendum F: music supervision and soundtrack proposal

> Audit of 2026-11-15 at commit `2b5d3ee`. Paths are relative to `projects/games/last_light/` unless they start with `docs/`, `assets/`, `renders/` or `tools/`; `g/` means `godot/`. Section numbers are those of the approved plan. Index: [README](README.md).

## 23. Addendum F in full: soundtrack proposal

### 23.1 Creative direction
- **Three layers, kept separate:** diegetic sound (machinery, radio, footsteps); ambience (wind, rain, sea, on the Ambient and Exterior buses); score (Music bus).
- **Default is no music.** Chapters 1 and 2 are mostly machinery and weather. Music enters as short cues at beats, not as a bed.
- **One motif:** five notes falling in D minor (D, C, A, G, F), the shape of the existing menu pad. It is incomplete everywhere until the truth is told.
- **Palette:** felt piano, one solo cello, low strings, air. No percussion, no choir, no synth leads.
- **Ross's music is the warmest in the game,** because he is the most human thing in the room.

### 23.2 Cue sheet
| # | Cue | Trigger | Ends | Level | Under dialogue |
|---|---|---|---|---|---|
| M01 | Title | menu shown | fades 3 s on New Game | -16 LUFS | n/a |
| M02 | Arrival | first dusk thought | plays out | -20 | yes, thoughts only |
| M03 | Watch | once each in chapters 1 and 2, after the log and after the archive | 2 min then out | -24 | ducked 8 dB |
| M04 | Weather (two layers) | chapter 3 forecast; second layer at the blackout | chapter end | -22 | ducked |
| M05 | Mechanism | each jam; each blackout | when cleared | -22 | ducked |
| — | Silence | from "docked" to the first footstep | | | |
| M06 | The stair | first footstep on the stair | cuts on the first knock | -24 | none playing |
| M07 | Ross | his first line at the door; again through chapter 5 movement 1 and 3 | fades under the Mayday | -22 | ducked |
| M08 | The letter | letter opened | plays out | -20 | none |
| M05/M04 | Rescue | chapter 6 jam and vectoring | on outcome | -20 | ducked |
| M09 | Decision | Morag's dawn question | on the choice | -22 | ducked |
| M10 to M13 | Endings | first ending panel | title card | -18 | none |
| M14 | Credits | credits start | end | -16 | n/a |

### 23.3 Generation prompts (for Daniel to use on a paid tier; instrumental mode)
Common suffix for every prompt: "Instrumental only, no vocals, no percussion, no synthesiser leads. Close, dry, intimate recording of felt piano and solo cello with soft low strings. Very slow, around 50 bpm, D minor. Sparse, restrained, melancholic, cold but human. Film score for a quiet 1971 drama set in a Scottish lighthouse. Not horror, not epic, no build to a climax."

| Cue | Prompt, before the suffix | Notes for the edit |
|---|---|---|
| M01 | "A lonely title theme. Felt piano alone states a slow five-note falling phrase, D C A G F, leaving long silences between phrases. After a minute one sustained low cello note joins and stays." | Cut a 3:00 loop at a silence |
| M02 | "Low strings swell very slowly from silence into a wide, cold chord. A single piano note sounds every eight seconds. No melody. Dusk over the sea." | 1:30, plays once |
| M03 | "An almost motionless low string drone with faint high harmonics drifting in and out. No melody, no piano." | 2:00 loop |
| M04 | "A low string drone with slow, uneasy cello swells rising and falling like a heavy sea. A quiet viola tremolo underneath. Never loud." | Generate twice: calm and restless, same key, for layering |
| M05 | "Quiet, irregular pizzicato cello like a slipping gear, over muted low piano strings struck softly. Mechanical, unresolved, tense but small." | 1:30 loop |
| M06 | "One very high, thin, held violin note. Far beneath it, a single low piano note every twelve seconds. Mostly silence. Waiting, not frightening." | 2:00 once |
| M07 | "Solo cello plays a slow, plain, tired melody based on a five-note falling phrase, D C A G F, warmly and close. A few soft piano chords beneath. An old man who has come a long way." | 3:00 loop |
| M08 | "Three slow felt-piano chords, then a single breath of strings, ending unresolved." | 0:40 stinger |
| M09 | "Felt piano alone plays the first four notes of a five-note falling phrase, D C A G, and stops. Repeats, each time stopping before the last note. Waiting for an answer." | 2:00 |
| M10 | "Felt piano and solo cello together play a slow five-note falling phrase and, for the first time, complete it and resolve gently to D major. Quiet relief, not triumph." | 2:30 |
| M11 | "Solo cello alone plays a slow five-note falling phrase to its end, very slowly, with long bows. A few piano notes at the start, then the cello is alone. Grief with dignity." | 2:30 |
| M12 | "A cold, still string drone. Felt piano plays four notes of a falling phrase, D C A G, and never plays the fifth. Hollow, unfinished." | 2:30 |
| M13 | "Low strings only, a dark sustained chord that slowly thins out. No melody, no piano. Nothing is resolved." | 2:30 |
| M14 | "The complete theme: felt piano and solo cello play a slow five-note falling phrase in full, twice, then the music thins to a single held cello note and fades into silence." | 4:00 |

### 23.4 Licensing position
| Item | Status | Requirement |
|---|---|---|
| Suno Pro or Premier | Checked on its terms and pricing pages this session | Generate and download while subscribed; ownership assigned to the subscriber; no warranty of copyright; games not mentioned. Keep the receipt and a dated copy of the terms |
| Udio | Could not be verified | Do not use |
| AIVA Pro | Partly verified | "Copyright owned by you" on the Pro plan; game use not spelled out |
| Project rule | "No AI-generated images or voices"; "never paid or AI-generation APIs" | New exception recorded in `docs/architecture/DECISIONS.md`: Daniel generates and supplies the tracks; I do not call the service |
| Credits | Today: "Music: synthesised for this game" | Reworded to Daniel's choice; the image exceptions say nothing about AI in the credits, and I will ask which wording he wants |

### 23.5 Fallback: verified usable tracks (no AI)
Licences confirmed on the source pages this session; nothing downloaded or heard.

| Cue | Track | Composer or performer | Source | Licence and credit |
|---|---|---|---|---|
| Title | The Long Dark | Scott Buckley | scottbuckley.com.au/library/the-long-dark/ | CC BY 4.0; "'The Long Dark' by Scott Buckley - released under CC-BY 4.0. www.scottbuckley.com.au" |
| Watch | Static | Scott Buckley | scottbuckley.com.au/library/static | CC BY 4.0, same credit form |
| Weather | Echoes (the 3:10 to 4:30 build) | Scott Buckley | scottbuckley.com.au/library/echoes | CC BY 4.0 |
| Mechanism | Long Note Three | Kevin MacLeod | incompetech.com (ISRC USUAN1100424) | CC BY 4.0; credit "Long Note Three, Kevin MacLeod (incompetech.com), Licensed under Creative Commons: By Attribution 4.0" |
| The stair | Long Note Two | Kevin MacLeod | incompetech.com (ISRC USUAN1100420) | CC BY 4.0 |
| Ross | Cello Sonata in G minor, Op. 65, III. Largo | Chopin; Christopher Harding, Yeonjin Kim | Wikimedia Commons (Musopen) | Public domain dedication; no credit required |
| Reveals | Signal to Noise ("No Piano Melody" mix) | Scott Buckley | scottbuckley.com.au/library/signal-to-noise/ | CC BY 4.0 |
| Decision | Despair and Triumph | Kevin MacLeod | incompetech.com (ISRC USUAN1400012) | CC BY 4.0 |
| Ending 1 | At The End Of All Things | Scott Buckley | scottbuckley.com.au/library/at-the-end-of-all-things/ | CC BY 4.0 |
| Ending 2 | Peer Gynt, The Death of Ase | Grieg; Musopen Symphony | Wikimedia Commons | Public domain dedication |
| Ending 3 | The Long Dark (reprise) | Scott Buckley | as above | CC BY 4.0 |
| Ending 4 | Lost Time | Kevin MacLeod | incompetech.com (ISRC USUAN1500032) | CC BY 4.0 |
| Credits | Nocturne in E minor, Op. 72 No. 1 | Chopin; Luke Faulkner | Wikimedia Commons (Musopen) | Public domain dedication |

Any edited track's credit adds "(edited)". Excluded during research: one NonCommercial track, several AI-labelled uploads, two ccMixter pieces with unclear sample rights, Pixabay tracks flagged for content-ID.

### 23.6 Original-score brief (if a composer is ever commissioned)
20 to 25 minutes; the cue sheet in 23.2; the motif and palette in 23.1; delivery as 48 kHz WAV with separate piano, cello and strings stems and marked loop points; a buy-out or perpetual game licence. Surveyed indie rates: about $400 to $620 per finished minute, so roughly $8,000 to $15,000.

### 23.7 Budget
| Route | Cost |
|---|---|
| AI-assisted (chosen) | $10 to $30 for one to two months |
| Fallback set | $0 with credits; AUD 75 per Buckley track to drop the credit |
| Commission | about $8,000 to $15,000 |

### 23.8 Integration in Godot
- `g/scripts/audio_director.gd`: two music players for crossfades; `play_cue(id, fade)`, `stop_cue(fade)`, `set_layer(id, on, fade)`; ducking by lowering the Music bus 8 dB while any message is on screen, 0.4 s down and 1.2 s back.
- `g/data/story/chapters.json`: `["music", id, fade]` and `["music_stop", fade]` beat actions (the existing `music` action gains a fade argument).
- Loop points set at import; files as OGG Vorbis; levels as in 23.2.
- Save the current cue id; on load, restart it from the top with a 2 s fade.
- Interruption rule: a new cue always crossfades; a stinger (M08) plays over the bed without stopping it.
- Tests: every cue id in the data exists as a file; a cue is restored after load; nothing is playing between "docked" and the first stair footstep.
