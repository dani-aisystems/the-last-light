# THE LAST LIGHT: soundtrack prompts (for Daniel; DECISIONS Q16, Q27)

You generate the tracks; Claude never calls a service. Keep the subscription receipt and a dated copy of the service's terms with the files: Suno's paid plans grant ownership of songs made while subscribed, and the free plan does not.

## Where the finished files go

Download each track as WAV if your plan offers it (or the best MP3), and drop it into `projects/games/last_light/audio/score_in/`, named by cue, e.g. `M01.wav` or `M04b.wav`. Several takes are welcome (`M07_a.wav`, `M07_b.wav`); Claude will then pick, cut, loop and master each to its level in `godot/data/music_cues.json` and swap it in. The game, the tests and the cue table stay as they are.

## The whole soundtrack, in one brief (for any generator or a composer)

> A sparse, intimate film score for a quiet 1971 drama: one night in a Scottish lighthouse during a storm, a keeper alone with a lie he wrote eighteen years ago. Instrumental only. Palette: felt piano, one solo cello, soft low strings, and a little air; no percussion, no choir, no synthesiser leads, no vocals. Very slow, about 50 bpm, D minor. Cold but human, restrained, melancholic; not horror, not epic, never building to a climax. One motif holds it together: five notes falling in D minor, D C A G F, the shape of a question. Everywhere until the very end it stays incomplete, stopping before its last note or never resolving. Only when the truth is told does it complete and, once, resolve to D major. The warmest music belongs to Ross, the old fisherman at the door, because he is the most human thing in the room. Most of the night is no music at all: machinery, wind, rain and sea. Music enters as short cues at moments, then leaves.

## Suno, step by step

1. **Create** → **Custom**, and switch **Instrumental** on, so no lyrics are sung.
2. **Title:** the cue name below (it only labels your library).
3. **Style of Music:** paste the cue's *Style* line. It is kept short so it fits every version of the field.
4. If your version shows **Exclude styles** (advanced options), paste: `vocals, choir, drums, percussion, synth lead, electronic, epic, trailer, orchestral hit, hip hop beat`.
5. Generate. Keep the takes that stay sparse and slow and do not swell into a climax. If a take is too short, use **Extend** from a quiet moment.
6. Download as WAV and name it as above.

Common to every cue (already folded into each Style line): instrumental, felt piano, solo cello, soft low strings, slow 50 bpm, D minor, sparse, intimate, cold but human.

## The cues

| Cue | Title | Style (paste into Suno) | Length you need | Notes for the edit |
|---|---|---|---|---|
| M01 | Title | `instrumental film score, felt piano alone, slow falling five-note phrase D C A G F, long silences, one low cello note joins later, 50 bpm, D minor, sparse, lonely, cold` | 3:00 | The title screen; looped at a silence. Prefer the take where the cello enters late and stays. |
| M02 | Arrival | `instrumental, low strings swelling slowly from silence into a wide cold chord, single soft piano note every eight seconds, no melody, dusk at sea, D minor, 50 bpm, sparse` | 1:30 | Plays once, under the first dusk thoughts. |
| M03 | The watch | `instrumental ambient film score, almost motionless low string drone, faint high harmonics drifting in and out, no melody, no piano, D minor, very slow, cold, still` | 2:00 | Loops; goes out after two minutes. Ducks under dialogue. |
| M04 | Weather (calm) | `instrumental film score, low string drone, slow uneasy cello swells rising and falling like a heavy sea, quiet, never loud, D minor, 50 bpm, restrained` | 2:00 | The storm forecast. Make **two versions** in the same key: this calm one ... |
| M04b | Weather (restless) | `instrumental, quiet viola tremolo over a low string drone, restless and uneasy, heavy sea, D minor, 50 bpm, no melody, never loud, sparse` | 2:00 | ... and this restless layer, laid over the calm one at the blackout. They play together, so match the key. |
| M05 | Mechanism | `instrumental, quiet irregular pizzicato cello like a slipping gear, muted low piano strings struck softly, mechanical, unresolved, tense but small, D minor, slow` | 1:30 | Each jam of the optic drive; loops until it is cleared. |
| M06 | The stair | `instrumental, one very high thin held violin note, far beneath it a single low piano note every twelve seconds, mostly silence, waiting not frightening, D minor` | 2:00 | Footsteps on the stair; it is cut dead on the first knock, so a sustained middle is best. |
| M07 | Ross | `instrumental, solo cello plays a slow plain tired melody on a falling five-note phrase D C A G F, warm and close, a few soft piano chords beneath, D minor, 50 bpm, tender` | 3:00 | Ross at the door and through his story. The warmest cue. Loops. |
| M08 | The letter | `instrumental, three slow felt piano chords, then a single breath of soft strings, ending unresolved, D minor, very slow, intimate, quiet` | 0:40 | A sting when the 1957 letter is opened; plays over whatever is playing. |
| M09 | Decision | `instrumental, felt piano alone plays four notes of a falling phrase D C A G and stops, repeats, each time stopping before the last note, waiting for an answer, D minor, slow, sparse` | 2:00 | Morag's question at dawn. It must never play the fifth note (F). |
| M10 | Ending: Correction | `instrumental, felt piano and solo cello together play a slow falling five-note phrase and complete it, resolving gently to D major, quiet relief not triumph, 50 bpm, intimate` | 2:30 | The truth told and the *Iona Star* through: the only time the phrase completes and resolves. |
| M11 | Ending: Heard Together | `instrumental, solo cello alone plays a slow falling five-note phrase to its end, very slow long bows, a few piano notes at the start then cello alone, grief with dignity, D minor` | 2:30 | The truth told, the ship lost. |
| M12 | Ending: Nothing to Report | `instrumental, cold still string drone, felt piano plays four notes of a falling phrase D C A G and never plays the fifth, hollow, unfinished, D minor, very slow, sparse` | 2:30 | The lie kept, the ship through. Never the fifth note. |
| M13 | Ending: Light Exhibited Throughout | `instrumental, low strings only, dark sustained chord slowly thinning out, no melody, no piano, nothing resolved, D minor, very slow, cold, minimal` | 2:30 | The lie kept, the ship lost. |
| M14 | Credits | `instrumental film score finale, felt piano and solo cello play a slow falling five-note phrase in full twice, then thins to a single held cello note fading into silence, D minor, 50 bpm` | 4:00 | The credits after an ending. |

## Choosing takes (what to listen for)

- **Slow and sparse beats pretty.** Under wind, rain and machinery, anything busy masks the room.
- **No hidden climax.** Suno often swells in the last third; trim or reject it.
- **The motif's shape matters more than exact notes:** five falling notes, incomplete except in M10 and M14.
- **Key:** D minor everywhere (M10 ends in D major). M04 and M04b must match each other.
- **Loops (M01, M03, M04, M04b, M05, M07, M09)** need a quiet spot to cut at; Claude finds it.
