# THE LAST LIGHT: trailer narration (R7)

The narrator is **Callum Mackay**, the keeper, speaking after the night, quietly and in the first person. Every claim is canon (`STAGE3_NARRATIVE_MASTER.md` §5.2–5.3, `ch1`–`ch6.dlg`). Nothing is said that the player does not learn by chapter 2, so the truth/lie choice and the endings stay unspoiled.

Voice: ElevenLabs Free, a generally available model (not Beta), under DECISIONS Q28 (trailer only). Credit: "Narration voice: elevenlabs.io".

Pace: about 2 words per second, with long silences between lines. The silences are made in the edit, not by regenerating.

---

## A. The Keeper (duty, isolation, responsibility): about 38 s of speech

1. Sixteen-twenty. The sun goes behind Pabbay, and the light is mine till morning.
2. Wind. Oil. The clockwork turning. Every hour of it written in the book.
3. Out there, seven boats and one lamp between them and the rocks.
4. A keeper doesn't sleep. A keeper doesn't guess. A keeper writes down what is true.
5. My father taught me that.
6. He taught me the other thing as well.
7. *(title)* The light is burning.

## B. The Storm (urgency, uncertainty, consequences): about 35 s

1. November, nineteen seventy-one. A gale coming in off the Atlantic.
2. The batteries are flat, the engine won't catch, and the radio won't stop.
3. Somebody out there is calling as a boat that sank eighteen years ago.
4. Keep it turning. Keep it lit. Keep talking.
5. Then, at a quarter past two, three knocks at the door.
6. *(title)* Every light has a record.

## C. The Human Cost (memory, relationships, difficult choices): about 42 s. **CHOSEN**

1. Eighteen years ago tonight, a boat called the *Mary Ellen* went onto the rocks below this light.
2. The inquiry said her master was to blame.
3. The station log said the light was burning.
4. I know what the log said. I wrote it.
5. *(pause; world and radio)* Tonight, the same gale. The same channel.
6. And someone out there is calling as the *Mary Ellen*.
7. *(storm; no narration)*
8. *(release)* By dawn, Stornoway will want my report.
9. One line in a book. That's all it ever was.
10. *(title card: THE LAST LIGHT)*

### Why C
- It opens on a fact that sets up a mystery: a wreck, a blamed man, a log.
- Line 4 turns it into a confession, the strongest hook in the material, and true to chapter 2.
- It then hands over to the game's own sound (the radio, the storm, the knock) instead of narrating over it.
- It ends on the game's real choice (the dawn report, the log line) without saying which way it goes.
- A explains duty, which the visuals already show. B narrates events the footage shows better on its own.

### Delivery notes (for the generation)
- Low, close, unhurried: a man in his forties, tired, not theatrical. A slight Scottish or Highland colour if the voice has it naturally; no put-on accent.
- Lines 3 and 4 are almost flat. The weight is in the pause before "I wrote it."
- Lines 8 and 9 are quieter still, close to the microphone.

---

## Generation record (2026-11-20/21, ElevenLabs Free; terms saved in `elevenlabs_terms_2026-11-20.txt`)

Model: **Eleven Multilingual v2**, which is not Beta. The settings each take actually used are encoded in its filename:
- speed 0.90;
- stability 0.50;
- similarity 0.86 (David 0.75);
- style 0.17 to 0.26 (David 0);
- speaker boost on.

The full script C was generated once per candidate. The originals are untouched in `renders/last_light/r7/trailer/VO_original/` (with SHA256SUMS). About 1,400 credits were used of the Free plan's 10,000 a month.

| Voice (Voice Library) | Take | Median F0 | Loudness | Defects measured | Verdict |
|---|---|---|---|---|---|
| Adam - Classic Scottish Storyteller | 31.1 s | 120 Hz | −20.4 LUFS | none (peak 0.73, no sample spikes) | **used (provisional)** |
| Hector - Poetic and Engaging Narrator | 29.6 s | 104 Hz | −13.8 LUFS | **877 up/down sample spikes near full scale** (peak 0.974): likely distortion or crackle | alternate (cut lines kept in `vo_hector/`) |
| David - Calm and Relaxed Narrator | 33.3 s | 76 Hz | −32.1 LUFS | no energy above 8 kHz (band-limited or muffled) | rejected |

**Lines.** Adam's take was cut into the eight lines at its pauses. The cut points were checked by aligning syllable counts with the speech segments (about 0.23 s per syllable). The match also holds inside the lines: "I know what the log said" is 1.35 s against 1.40 s expected, and "I wrote it" is 0.68 s against 0.70. Each line is normalised to −16 LUFS before the mix. A second Hector take with 2.5 s break tags exists in the account history; it was not used.

**Daniel's ear is the remaining check.** Claude cannot listen. Accent, warmth and naturalness are not verified. To swap the voice, cut the other take the same way into `vo/` and rebuild with `build_trailer.py`.
