# THE LAST LIGHT: the music (score system and cues), 2026-11-19

> F_soundtrack.md section 23 (23.2 the cue sheet, 23.8 the integration); DECISIONS Q12 and Q16. Plan: `~/.claude/plans/pasted-content-id-4c59-continue-the-temporal-thompson.md`. Paths are relative to `projects/games/last_light/` unless they start with `docs/`, `assets/`, `renders/` or `tools/`; `g/` means `godot/`.

## 1. The score system (`g/scripts/audio_director.gd`)

| 23.8 item | Built |
|---|---|
| Two music players for crossfades | Two bed players on Music crossfade over each cue's fade (per-player dB fades). A **layer** player carries M04's restless layer. A **stinger** player plays M08 over the bed without stopping it. |
| `play_cue(id, fade)`, `stop_cue(fade)`, `set_layer(id, on, fade)` | As named. `play_cue` refuses an unknown id or anything during the silence hold, and the same bed again is a no-op. Also `current_cue()`, `cue_state()`, `restore_cue()` and `hold()`. A new bed takes its old layers out. |
| Ducking: Music −8 dB, 0.4 s down, 1.2 s back, while any message is on screen | An `AudioEffectAmplify` at the head of the Music bus, so the player's Music volume setting is untouched. Driven by Stage D's `game_fp.message_on_screen()`: any story line, a short thought, a sound caption or a radio subtitle. |
| `["music", id, fade]` and `["music_stop", fade]` beat actions | Both work from `chapters.json` and from a `.dlg` `!` line. `music_stop` was added to the director's presentation and instant actions (story_test validates against those lists). `["music_stop", fade, "hold"]` starts the silence. The old `["music", "tension"]` id maps to M04 (`legacy` in the cue table). |
| Loop points at import; OGG Vorbis | The placeholders are WAV (LFS) and loop through the existing `_looped()` (loop points set on the stream). A real track would be cut and mastered the same way; 128 kbps OGG is possible with the local ffmpeg's native Vorbis encoder, if wanted. |
| Levels as in 23.2 | Each file is mastered to its cue's integrated loudness and played at unity. The new BS.1770 meter `analyze.lufs()` reads a 997 Hz sine at −20 dBFS as −23.0 LUFS. The pytest checks every cue within 1 LU of its target; they are all within 0.05. |
| Save the current cue; on load restart it from the top with a 2 s fade | `game_fp.save_dict()` adds `"music": {"cue", "layers", "hold"}`. A stinger is never saved. `_apply_save` calls `restore_cue`. Older saves have no key and load silent. `SaveSystem.VERSION` is unchanged (the field is additive), and save_compat stays green. |
| A new cue always crossfades; a stinger plays over the bed | As above. |
| **The silence: from "docked" to the first footstep on the stair** | ch4 `hail` (docked) runs `["music_stop", 3, "hold"]`: the bed fades out over 3 s and `play_cue` is refused until the stair-steps action (`footsteps stair`) clears the hold. It is saved too. The old `tension` drone used to play straight through this stretch. |
| The cue table | New `g/data/music_cues.json`. For each cue: its file, its kind (bed / layer / stinger), whether it loops, its level, and `max_s` (M03 and M09 go out after 2 min). It also names the title cue, the credits cue, and which cue each ending gets. |

**Old call sites, now cues:**
- `set_menu(true)` plays the title cue (M01); `set_menu(false, fade)` stops it with that fade (Stage D's fix kept).
- The credits roll plays cue M14's file (`CREDITS_MUSIC`) once, at unity: it was the looped menu pad at −9 dB. R19's "plays on Music" still holds.
- The ending card (`game_fp`, `ending_card`) plays the ending's own cue.
- `music_menu.wav` and `music_tension.wav` are no longer used. **They are kept until Daniel OKs removing them.**

## 2. The cue sheet in the data (`chapters.json`: 21 actions, no new beats, no `.dlg` change)

| Cue (23.2) | Where |
|---|---|
| M01 Title | The title (attract) game: `set_menu(true)` |
| M02 Arrival | ch1 `dusk` (the first dusk thought) |
| M03 Watch | ch1 `log`, ch2 `archive`; out after 2 min |
| M04 Weather + layer | ch3 `forecast` (M04); `notes`, the blackout (M04b, the restless layer). The bed carries on into ch4 `approach`, which used to play the "tension" drone. |
| M05 Mechanism | ch2 `jam` (then `clear` stops it); ch6 `jam` |
| Silence | ch4 `hail` (docked): `music_stop` with the hold |
| M06 The stair | ch4 `steps`: right after `footsteps stair`; `music_stop 0` just before `knock` (it cuts on the first knock) |
| M07 Ross | ch4 `door` (his first line); ch5 `story` and `story3`; `mayday` stops it |
| M08 The letter | ch5 `drawer` (the stinger) |
| M05 / M04 Rescue | ch6 `jam` (M05), `free` and `standby` (M04); `rescue` (the outcome) stops it |
| M09 Decision | ch6 `dawn` (Morag's dawn question) |
| M10 to M13 Endings | The ending card. `correction` (truth, *Iona Star* through): M10, it resolves. `heard_together` (truth, lost): M11, grief. `nothing_to_report` (the lie, through): M12, hollow. `light_exhibited` (the lie, lost): M13, dark. |
| M14 Credits | The credits roll after an ending |

## 3. Placeholder cues (`audio/synth.py`)

**Fifteen sketches** (M01 to M14, plus M04's layer), all of the one motif: five notes falling in D minor, D C A G F.
- **Voices:** felt piano (soft hammer, partials decaying faster the higher they are), cello (bowed, with vibrato and a body resonance, or pizzicato), low strings (detuned, swelling) and air.
- **Shaped to their briefs:** M09 and M12 never play the fifth note; M10 resolves to D major; M06 is a high held note with a low note every 12 s.
- **Sizes:** 21 to 42 s, mono 44.1 kHz WAV (LFS), about 37 MB together.
- **Determinism:** synth.py is deterministic, so pytest's byte-identity covers them.
- **Mastering:** `save_lufs` sets the gain to the target. A soft knee is applied only above 0.7, keeping 1 dB of headroom, and the result is re-measured. A first version normalised after limiting and came out up to 2 LU loud; fixed.

`analyze.py --strict`: every music file passes CLIP, DC, SEAM, QUIET, LOUD and SHORT (loops ≥ 20 s).

## 4. Verification

- **`tests/music_test.gd`** (new, `MUSIC_RESULT`): 25 / 25.
  - **The data:** every cue id used by the data, the endings, the title and the credits exists, and its file loads. All 15 table cues have files.
  - **Players:** the crossfade (both play half way; the old one stops); the stinger over the bed; the layer, taken out by a new bed; the legacy id; M03 out after 2 min.
  - **The duck:** −8.00 dB at 0.4 s; −4.0 at 0.6 s after the message; 0.00 at 1.2 s.
  - **Saves:** a save keeps the cue. A JSON round trip restarts it from the top (position 0.00 s), from −60 to 0 dB over 2 s. A save taken in the silence keeps it.
  - **The silence rule, in a real headless ch4 run** from `hail` to the knock (half-speed waits): 11.4 s of silence from "docked" to the first stair footstep, 0 audible frames after the 3 s fade, and a cue asked for in the silence refused. M06 plays on the stair and is cut by the first knock.
  - **Test setup:** jumping into ch4 straight after game start first left ch1's beat pending, so `hail` was skipped. The test clears that (a setup fix, not a game one).
- **pytest:** `test_lufs_meter_matches_bs1770_reference` and `test_music_cues_are_mastered_to_the_cue_sheet` (new); `test_last_light_audio` 6 / 6.
- **Listening:** `renders/last_light/music/listen/` (`INDEX.md`).
  - The five scenes: a crossfade, the stinger, the duck, the title into a new game, and ch4 from docked to the knock.
  - The duck measured −26.4 / −32.2 / −23.5 dB before, under and after (the cue's own level moves; the engine's duck is exactly −8.0).
  - The title fades from −17.6 dB to silence.
- **Full suites:** the checkpoint entry below.

## 5. Open: the real tracks (Daniel's route, asked at this checkpoint)

1. **His own tracks under Q16.** He generates and supplies the files; Claude cuts, loops, masters them to the cue table's levels and integrates them, and never calls a generation service. Keep the receipt and a dated copy of the service's terms with the files.
2. **The verified fallback in 23.5.** Scott Buckley (CC BY 4.0) plus Musopen public domain. This needs his download OK, every licence logged in `assets/ASSET_LICENSES.md`, and the credits wording agreed with him (Q12) before the credits change.

Either way, swapping a cue is a file and its `music_cues.json` entry; the system and the tests stay as they are.

## Suites at the checkpoint (2026-11-19 to 20)

Headless, under `taskpolicy -b`. The Mac slept or was busy overnight, so some suites took hours of wall time.

| Suite | Result |
|---|---|
| story | 0 failed |
| run_tests / opening | 95 / 31 |
| interaction | 164, 0 failed (1 warning: the vapour burner, Stage D's note) |
| qa_sweep / g5 / save_compat / ross | 7,703 / 50 / 305 / 42 |
| regress | 501 |
| audio_d / music | 37 / 25 |
| `sim_v2` seeds 1 to 5 | **identical to Stage M's M0 JSON** |
| pytest | green |
| `analyze.py --strict` | 101 files, 0 flagged |
| ship_view | Failed only its "four ships under 0.4 ms" timing check under `taskpolicy -b` (162 µs a ship), the known throttling artefact; **PASS at normal priority** (2026-11-20, load 8) |

All with 0 SCRIPT ERRORs.

## Checkpoint (Daniel, 2026-11-20; DECISIONS Q27)
- **Approved; committed locally.**
- **Route: his own tracks (Q16).** The prompts he asked for, a general brief and per-cue Suno prompts, are in `projects/games/last_light/audio/SOUNDTRACK_PROMPTS.md`.
- **The old `music_menu` and `music_tension` files are kept** for now.
