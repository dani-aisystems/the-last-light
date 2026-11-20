# THE LAST LIGHT R7: ending recordings, QA

**Recording.** Godot Movie Maker, the same configuration as R3's `r3_ending_correction.mp4`: `tools/godot_bg --write-movie <abs>.avi --fixed-fps 30 --path projects/games/last_light/godot -- --capture=film --film --film_ending=<id> --film_credits=90 --audio`.
- 1920×1080 at 30 fps; MJPEG plus PCM 48 kHz.
- Default quality (Medium, the first-launch default). The ending is 2D panels, so the preset does not change it.
- The game's own mix is recorded, with no added sound.

**What a film shows.** `film_fp.gd` starts a game, sets the ending's flags and calls the director's ending card, as R3 did. New in R7: `--film_credits` then calls `director._finish_campaign()`, the same call the `end_campaign` beat makes in play. From there the shipping path runs unchanged: `game_fp._on_campaign_finished` → `main_fp._on_campaign_over` → the credits roll after 1 s. The film runs until the roll's end button shows, then 4 s more.

**Edit (identical for all four).** The deliverable starts 5.0 s into the recording, 0.1 s before the ending trigger, so the ending's music cue plays from its first note. The ending fades the room to warm black over its first ~2 s. In a film that room is the capture harness's chapter 1 start-up, not the dawn room a player would be in. Those 2.17 s are therefore covered with the ending's own warm black (`ending_sequence.gd` WARM_BLACK, drawn at 9/7/5 against the fade's measured 9/6/7). Nothing else is cut, retimed or regraded.

**Transcode.** Delivery is H.264 High CRF 18, yuv420p BT.709 TV range, AAC 256k. The master is the same at CRF 12 with AAC 320k. Panel colour measured against the source: within 2 levels.

**Automated checks (`release/R7/qa/video_qa.py inspect`).**
- ffprobe: A/V duration difference, frame count, frame intervals (pacing).
- `blackdetect`, `freezedetect` (panel holds are expected freezes), `silencedetect`, `ebur128` (integrated, LRA, true peak), per-second RMS, clipped samples, sample-jump click candidates, scene cuts.
- Contact sheets every 2 s, **all viewed**; full-resolution frames at the epilogue and the card, viewed.

**A capture fault, found, proven and fixed.**
- **Symptom:** three takes (Light Exhibited twice, Correction once) were full length, but drawing stopped exactly when the credits opened and only resumed when the roll's end button appeared. The credits were black from about 82 to 139 s. Movie Maker logged fewer drawn frames than it wrote: 2,332 of 4,356 (both Light Exhibited takes) and 2,584 of 4,459. Heard Together and Nothing to Report were complete.
- **Cause:** the Godot window was occluded. Claude in Chrome brings Daniel's browser (Brave, maximised, 1920 points wide) to the front, and the Godot window is opened behind the front app. macOS then reports the window as covered, and Godot stops drawing. The two good takes were made before the browser was first used.
- **Proof:** a controlled A/B, both runs the same command (Light Exhibited with the panels at 8× speed, then the credits).
  - Brave in front: 483 of 1,323 frames drawn, stopping at credits open.
  - Daniel's IDE in front: 1,323 of 1,323 drawn.
  - The stop lands at credits open in every bad take, which first looked like a code fault. The credits path is where the covered state shows; no game or film code was changed to fix it.
- **Ruled out:** display sleep (no display-off events after 20:33, and macOS reports "display sleep prevented by Godot").
- **Fix:**
  - all windowed recordings now run as one block (`release/R7/record_block.sh`), with no browser use during it;
  - before each run a guard brings the IDE forward if a browser is frontmost;
  - every recording must pass a gate: Movie Maker's drawn-frame count must equal the AVI's packet count, otherwise it is retried and the failure logged. `record_reel.sh` does the same for the trailer shots.
- **Records:** the bad logs are kept in `renders/last_light/r7/endings/bad_occluded/`.

## Results

| Ending | File | Length | Frames (drawn / written) | Panels (FILM_STEP) | Credits | Loudness | Verdict |
|---|---|---|---|---|---|---|---|
| Heard Together | `TheLastLight_Ending_HeardTogether.mp4` | 141.8 s | 4404 / 4404 | p1_wheel 2.5 s, p2_ledge 12.7, p3_correction 22.9, p4_heard_together 36.1, card 64.9 | open 79.3 s, end 137.7 s, "Return to the title" | −28.5 LUFS, TP −4.3 dBFS, 0 clipped | **PASS** |
| Nothing to Report | `TheLastLight_Ending_NothingToReport.mp4` | 153.3 s | 4750 / 4750 | p1_wheel, p2_gut, p3_exhibited, p4_nothing_pier (same times); card 71.6 s | open 85.8 s, end 149.3 s | −28.2 LUFS, TP −4.3, 0 clipped | **PASS** |
| Light Exhibited | `TheLastLight_Ending_LightExhibited.mp4` | 135.2 s | 4207 / 4207 | p1_alone, p2_ledge, p3_exhibited, p4_light_exhibited (same times); card 58.5 s | open 72.7 s, end 131.2 s | −28.9 LUFS, TP −4.3, 0 clipped | **PASS** |
| Correction | `TheLastLight_Ending_Correction.mp4` | 143.6 s | 4459 / 4459 | p1_wheel, p2_gut, p3_correction, p4_correction (same times); card 66.9 s | open 81.1 s, end 139.6 s | −28.4 LUFS, TP −4.1, 0 clipped | **PASS** |

Times are in the delivered file (recording time − 5.0 s).

**Findings with timestamps (Heard Together; Nothing to Report is the same structure):**
- 0.0–2.6 s: warm black, then p1 fades in. Intended.
- Frame pacing: 33.333 ms on every frame. No irregular intervals, no cuts other than the game's crossfades, A/V lengths equal.
- Panel holds register as "freezes" (for example 3.6–10.5 s). These are intended: the panels are still images with crossfades.
- Epilogue (HT 36–64 s): three paragraphs fade in one at a time beside p4. Legible at 1080p, nothing cropped (full frame at 66 s viewed).
- Card (HT 65–79 s): "HEARD TOGETHER", then the amber date line, then "The light was kept." Legible and centred.
- 79.2–80.5 s: 1.25 s of near-silence, from the card's music tail to the credits cue (M14). A natural gap, not a dropout.
- Credits (HT 80–138 s): the roll scrolls evenly and every section is readable. It ends with "Return to the title"; the film stops 4 s later.
- No clipping, no clicks found, integrated loudness about −28 LUFS. That is the game's own quiet mix, left unnormalised so the file is what a player hears.

**Not checked by ear.** Claude cannot listen. Audio was checked only by measurement: per-second RMS, spectrogram, silence and click scans. Daniel's ear is the remaining check.
