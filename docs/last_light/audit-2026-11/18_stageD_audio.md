# THE LAST LIGHT: Stage D evidence (audio), 2026-11-19

> Audit Stage D: [04_narrative.md](04_narrative.md) section 7.8 and the action column of the table in [05_visual_audio.md](05_visual_audio.md) section 18.4. DECISIONS Q16 allows recorded CC0 audio for Ross's cough and the handling sounds, after Daniel approves the list. Plan: `~/.claude/plans/pasted-content-id-4c59-continue-the-temporal-thompson.md`. Paths are relative to `projects/games/last_light/` unless they start with `docs/`, `assets/`, `renders/` or `tools/`; `g/` means `godot/`.

## 1. The 18.4 actions

| 18.4 action | Before | Built | Where |
|---|---|---|---|
| Static dips 6 dB under a message | Static rose for about 3.5 s after each radio line (`_static_t`); nothing dipped it | While a radio message is on screen (a radio-look story line, or a sim radio subtitle), the static sits 6 dB below its envelope, eased over 0.3 s, and returns after. Squelch and typing blips are unchanged. | `audio_director.gd` `static_db()`, `_static_dip`; `game_fp.gd` `radio_message_on_screen()` |
| Door-muffle low-pass | None; the stair steps came through an open SFX bus | New **Stair** bus into SFX: a stairwell reverb (room 0.75, damping 0.5, wet 0.3, 30 ms predelay), then the door's 12 dB low-pass. Its cutoff follows the door's swing (`station.door_phase().y`): 700 Hz shut, 8 kHz open (√ swing), eased. The stair steps and the base door play through it. | `audio_director.gd` `_ensure_stair_bus()`, `door_cutoff()` |
| Stairwell reverb send | None | As above (the reverb is on the Stair bus, ahead of the door) | — |
| Room reverb send on SFX (7.8 "Mix") | None | A light reverb on SFX (room 0.32, wet 0.10, 12 ms predelay), added once even when two directors exist (the title game has its own) | `_ensure_room_reverb()` |
| `paper_slide` on open, softer on close | Documents opened and closed silently (`interaction_test`'s 12 standing warnings) | New presenter signal `document_opened`, also fired on a page turn. `game_fp` plays `paper_slide` (−8 dB) on open and the new synthesised `paper_close` (0.6 s, 6 dB lower: a duller slide and a light tap on the desk) on `document_closed`. | `story_presenter.gd`, `game_fp.gd`, `audio/synth.py` `paper_close()` |
| Defect: `set_menu(false)` never called | The title game was freed when the loading screen opened, cutting the pad dead | `main_fp._transition_in` calls `set_menu(false, 2.6)` on the title game's director as New Game / Continue begins, so the pad fades over the camera move. `set_menu` fades from its current level over `fade_s` (it used to restart at −8 dB). | `main_fp.gd`, `audio_director.gd` |
| Defect: `horn_fishing` mastered hot | Cached report (2026-11-04): LOUD | **Already fixed in the tree** (`synth.py`: peak −4, "was −3"): RMS −10.3 dB, peak −4.0, under the LOUD gate. Re-measured, no change. | `audio/synth.py` |
| Defect: `click_button` DC offset | Cached report: DC | **Already fixed in the tree** (`save()` runs `dc_free()` on one-shots): DC 0.0000. Re-measured, no change. | `audio/synth.py` |

`game_fp.message_on_screen()` is also new: true for any story line, a short thought, a sound caption or a radio subtitle. The music duck (F 23.8) uses it.

## 2. Section 7.8: what is heard, and from what source (built)

| 7.8 item | Source | In the game |
|---|---|---|
| Ross's cough, 6 to 8 takes, one older male voice; never the same take twice | Recorded CC0: 6 takes from georgisound #369295 and 2 from husky70 #157296 (`ross_cough_0..7`) | `cough_take()` never repeats the last take (test: 200 draws, all 8 used). `cough_fit(n, pos, bus)`. On the stair: a new `["sfx", "ross_cough"]` action in ch4 `steps`, just before the cough caption, plays 4 coughs low in the stairwell through the Stair bus. In the room: a stage direction with "He coughs" (ch4.dlg:95, ch5.dlg:27) plays 3 coughs at his figure, or through the door while it is shut. No `.dlg` change. |
| Breaths between Ross's lines | Recorded CC0: sickfin #711359, 4 takes (`ross_breath_0..3`) | On about half of his lines, never two within 6 s, at his figure (or through the door) |
| Boots on concrete | Recorded CC0: SoftDistortionFX #465299, 6 takes (`step_concrete_*`) | **The keeper's own footsteps** (new; he had none): one per 0.72 m walked in free walk (not seated, not in a device view, not paused, no document open); a jump of 1 m or more (a load) is not a step |
| Boots on chequer plate | The iron-stair takes (the same steel underfoot) | Within 1.3 m of the stair door, the keeper's step is steel. gristi #562195 (approved, logged) is **not used**: it is one reverberant hit, then rumble, with no separable footfalls. |
| Boots on iron treads (the stair) | Recorded CC0: RFCaldas #749713, 8 takes (`step_stair_*`) | Ross's climb now uses them, through the Stair bus (it used the synth `step_metal`) |
| Door wheel, dogs and hinge | Hinge: recorded CC0, kyles #637583 (`door_hinge`). Dogs and leaf: synth, as before | The hinge creaks 0.1 s after the latch as the door swings (`game_fp` `door_open`) |
| Paper slide, document open and close | Synth (`paper_slide`, new `paper_close`) | Section 1 |
| Telephone lift and dead line | Lift: recorded CC0, TRP #616840 (`phone_lift`). Dead line: synth (`phone_dead`: a faint hiss, a click) | `audio.phone()` on every use of the phone |
| Switch and breaker | Synth (unchanged) | — |
| Hand pump | Recorded CC0: Garuda1982 #580670 (`hand_pump`, 7 s) | **Not wired**: no pump exists in the game yet. Ready for Stage F's fuel run. |
| Kettle | Recorded CC0: wlabarron #507937 (`kettle_boil`, 18 s: comes to the boil and whistles) | `audio.kettle()` when the Primus is lit in ch5's cup beat |
| Sediment-bowl drain | Synth (`bowl_drain`: the cock's squeak, a trickle into a tin, last drips) | On the sim's `bowl_drained` event |
| Teleprinter | Recorded CC0: craigsmith #483336 (`teleprinter`, 10 s). **Provenance risk** (a digitised 1930s to 60s film effect); Daniel chose to include it | A new `["sfx", "teleprinter"]` action in ch1's `teleprinter` beat, at the machine |
| Desk drawer (found by `interaction_test`) | Synth (`drawer_slide`) | `audio.drawer()` on every use of the drawer |

## 3. The recorded files

**Download (Daniel's OK, 2026-11-19, all four groups).**
- Freesound's high-quality preview MP3s (128 kbps): the originals need a login, and no credentials are used. Each page was re-read just before fetching, to confirm its CC0 1.0 deed link.
- Each file has its own folder `assets/audio_cc0/<item>_<id>/` with a `SOURCE.txt`: title, author, page, licence, the preview URL, the date, its sha256 and the approval.
- All 11 are logged in `assets/ASSET_LICENSES.md`.
- If Daniel downloads the originals while logged in, the same pipeline can be re-run on them.

**Cutting (`audio/recorded.py`, new; host Python).** Nothing was listened to; the cuts come from the signal itself:
- Takes are found by level events (coughs, breaths) or by impact onsets ranked by sharpness (footfalls: the peak in the first 30 ms over the RMS of the 100 ms before). On the stair recording, ranking by sharpness instead of level jump rejected railing scrapes and swells. All eight chosen takes show an impact and the metal's ring-out (checked on waveform plots).
- Each take gets a 60 Hz high-pass and short fades, then `synth.save()`'s DC removal and peak target: coughs −4 dBFS, breaths −14, footsteps −5 / −6, objects −6 to −8.
- `audio/RECORDED.json` lists every output with its cut, its source page, licence and sha256, and its own sha256.
- `tests/test_last_light_audio.py` gains `test_recorded_audio_matches_its_manifest`: each recorded file matches its hash and is CC0 and licence-logged. Recorded files are exempt from the synth byte-identity check.

**Result:** 31 recorded files. With the 52 synthesised (now 55: `paper_close`, `drawer_slide`, `phone_dead`, `bowl_drain` are new, and the old set is unchanged), `analyze.py --strict` reports 86 files, 0 flagged. `phone_dead` was first flagged QUIET; it was re-mastered to −12 dBFS and is played at −10 dB in the room.

## 4. Listening files (for Daniel; never played by Claude)

- **Where:** `renders/last_light/stageD/listen/01_*.wav` to `15_*.wav`, with `INDEX.md` saying what to listen for.
- **How:** recorded silently from the game's own mixer by the new `tests/listen_d.gd` (headless, the Dummy driver, an `AudioEffectRecord` on Master, one recording per section, the storm ambience muted).
- **Two capture issues found and handled:**
  - Godot's Movie Maker cannot run headless (no frame to capture), and the disk had 7 GB free, so the recorder replaced it.
  - The dummy mixer runs about 8 % slower than real time (recorded 0.92 × wall time in every section), so the gaps between events are about 8 % tighter than in the game; pitch is correct. Under `taskpolicy -b` it ran at 57 %, so this script runs at normal priority.

**Measured on the files:**

| Check | Result |
|---|---|
| Static under a radio message (above 1 kHz) | About 34 dB before, 24 to 27 dB under, 33 to 34 dB after |
| Stair climb, door shut against open | Energy above 2 kHz −45.9 dB against −22.9 dB |
| Title pad fade | −37 dB playing, −63 dB half way through the fade, silent at the end (it used to cut dead) |
| Peak levels | The objects at the keeper's position −12 to −16 dBFS; the door −5.9; the breaths −31 (soft by design) |

## 5. Verification

- **`tests/audio_d_test.gd`** (new, `AUDIOD_RESULT`): 37 / 37. It covers section 1's checks, plus:
  - the cough never repeats a take and uses all 8;
  - the stair fit on the Stair bus, and the stage-direction cough;
  - the phone, its dead line, the drawer and the kettle;
  - the teleprinter at the machine; the bowl drain;
  - the keeper's steps: concrete at one per stride, steel on the landing, none on a teleport, none out of free walk.
- **`interaction_test`:** document sound warnings 12 → 0; the drawer and phone rows now play too.
- **pytest:** `test_last_light_audio` 4 / 4, including the recorded manifest.
- **Full suites:** see the checkpoint entry below.

**Not touched:** the `.dlg` files (only two `sfx` actions were added to `chapters.json`), the sim, `save_system`, the music (the next stage).

## 6. Appendix: the CC0 shortlist as shown to Daniel (2026-11-19, before his OK)

**How it was checked.** A research agent opened each sound's own page on freesound.org. Every row is marked "Creative Commons 0" with the sentence beginning "You can copy, modify, distribute and perform the sound, even for commercial purposes" (the fetch tool truncates at about 125 characters, so that part is quoted). A free Freesound login is needed to download originals. OpenGameArt refused automated fetches (HTTP 403), so nothing from it is listed; the Internet Archive and Wikimedia Commons were not searched.

| Item | First choice | Alternatives | Notes |
|---|---|---|---|
| Ross's cough | *Coughing.wav*, georgisound, <https://freesound.org/people/georgisound/sounds/369295/>, 10.9 s, WAV 44.1/16 mono: "various coughs from a very sickly man", dry | *Man clearing throat, coughing.aif*, jasonLON, /125403/ (13.2 s, 48/24 stereo); *Coughing Cough.wav*, husky70, /157296/ (6.8 s, "emphysema", "smoker") | No CC0 page says "older man, several coughs". georgisound's take gives several coughs from one voice. Cut 6 to 8 takes from it, topped up from husky70 if needed. |
| Breaths | *Old Man or Middle-aged Man's Struggled Breathing*, sickfin, /711359/, 25.3 s, 44.1/24 mono, voice booth | *Sigh - man - voice…*, ValentinPetiteau, /569568/ (7.7 s) | Trim to tired exhales; drop the laboured parts. |
| Boots, concrete | *Concrete Footsteps*, SoftDistortionFX, /465299/, 59.9 s, FLAC 44.1/24 mono: big boots, garage floor | *footsteps on surfaced road in boots*, Frigus_XIII, /456428/ | Faint traffic and breathing in places: pick clean steps. |
| Boots, chequer plate | *snd_footsteps_metal_floor_inside.wav*, gristi, /562195/, 3.1 s, 48/32 stereo | *Footsteps Metallic Muffled Louder.wav*, RutgerMuller, /50724/ | No CC0 file is labelled chequer or diamond plate; these are boots on a steel floor. |
| Iron stair treads | *Steps on metal stair Up and Down 2*, RFCaldas, /749713/, 35.0 s, 48/24 stereo: boots on a metal **spiral** stair | *FOLEY_Footsteps_Metal_001.wav*, conleec, /148462/ (60.6 s, concrete stairwell) | The only true spiral stair; railing scrapes can be kept or cut. |
| Heavy door hinge | *gate big rusty metal door garage open heavy creak rattle.flac*, kyles, /637583/, 6.3 s, 48/24 mono | *door iron.wav*, gecop, /525019/ (a cellar's iron door; an electric lock clunk to trim) | No watertight door; the heavy gate is closest. |
| Telephone lift | *Phone, old wired handset, pick up hang up…*, TRP, /616840/, 19.1 s, 48/24 stereo, rotary handset | *Phone Handset Slam*, dwswords, /832762/ (a Western Electric 500 hang-up) | Clean prop recording. |
| Hand pump | *old manual pump pumping water sound effect*, Garuda1982, /580670/, 41.4 s, 192/24 stereo | *Old hand pump*, AudioPapkin, /815126/; *HandWaterPump.wav*, Bent.B.C., /588629/ | A water pump; it stands in for the fuel hand pump. |
| Kettle | *Whistling gas kettle coming to the boil*, wlabarron, /507937/, 40.2 s, 48/24 mono: gas lit, boil, whistle, off the heat | *TeaKettleBoilThenWhistle.wav*, shelbyshark, /476441/ | **Excluded:** newlocknew's kettle (/798203/) is shown CC0, but its page adds requests (credit, no stock use) beyond CC0. |
| Teleprinter | none recommended | craigsmith's *R20-17-Teletype Machine.wav* (/483336/) and two siblings | **Provenance risk:** the uploader describes them as digitised 1930s to 1960s Hollywood film effects. The CC0 dedication may not be theirs to give. Recommended synthesising instead; **Daniel chose to include it.** |
| Door wheel / ratchet | none | — | No CC0 match; the existing synth dogs. |

## Checkpoint (Daniel, 2026-11-19; DECISIONS Q26)

**Approved; committed locally.**

**Final suites** (headless, `taskpolicy -b`), all with 0 SCRIPT ERRORs:

| Suite | Result |
|---|---|
| story | 0 failed |
| run_tests / opening | 95 / 31 |
| interaction | 164 checks, 0 failed |
| qa_sweep / g5 / save_compat / ross | 7,703 / 50 / 305 / 42 |
| ship_view | PASS |
| regress | 501 |
| audio_d | 37 |
| `sim_v2` seeds 1 to 5 | identical to Stage M's M0 JSON |
| pytest | green |
| `analyze.py --strict` | 86 files, 0 flagged |

**The one interaction warning left** is the vapour burner, a look-only object. Using it only plays a thought, so silence is right. That test's sound heuristic counted the thought's typing blips as a sound in one run and not in the next.

**Moved to the music stage:** the LUFS meter for `analyze.py` (the plan's D3 item). It is first needed to master the cues to the 23.2 levels.
