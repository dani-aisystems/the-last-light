# THE LAST LIGHT R7: trailer QA (rc6, final)

- **File:** `TheLastLight_Trailer_narration-elevenlabs.io.mp4`. H.264 High, CRF 18, 1920×1080, 30 fps, yuv420p BT.709; AAC 256k at 48 kHz stereo. **77.3 s**, 59.0 MB.
- **Master:** H.264, CRF 10, AAC 320k, 125 MB. It stays in `renders/last_light/r7/trailer/final/`, not in the package.
- **Mix:** WAV, 48 kHz, 24-bit.
- **Narration stem:** each line at its final level and position.
- **Title metadata:** "The Last Light - Trailer (narration voice: elevenlabs.io)". The end card's fine print carries the same credit.

**How it was built:** `release/R7/trailer/build_trailer.py edit.json`, a reproducible EDL. See `SHOT_LIST.md` (17 shots with source in-points) and `CUE_SHEET.md`.

**Sources:**
- **Pictures:** Godot Movie Maker recordings of the shipping game (the High preset; capture tooling only, no game change), the game's own ending panels and log page, and three text cards in the game's typefaces and colours.
- **Not used:** generated footage, retouching, or a grade beyond the game's own look. The two in-engine shots (r08 and the door) are dark exactly as the game draws them.
- **Every frame was gated:** Movie Maker's drawn-frame count equals the written count, so no stale frames are repeated. The fault and its proof are in `ENDINGS_QA.md`.

**Checks** (`qa/video_qa.py inspect`; 1 fps contact sheets **viewed**):

| Check | Result |
|---|---|
| Frame pacing | 2,319 frames, every interval 33.333 ms |
| A/V length | equal (difference 0.000 s) |
| Black | only the intended beats: 7.9–10.1 (place card), 26.5–28.5 ("I wrote it." on black), 49.8–51.0 (the dark stair before the door opens), 57.8–59.0 (silence), 69.5–77.3 (the title on warm black) |
| Freezes | only stills (text cards, the log page, the ending panel) |
| Silence | one intended gap, 58.3–59.7 s (the cut to black after the door) |
| Loudness | −16.0 LUFS integrated, LRA 8.7 LU, true peak −1.0 dBTP, 0 clipped samples, 0 click candidates |
| Narration over its real (ducked) bed, RMS over 2.5 s per line | +18.9 / +11.2 / +9.6 / +9.0 / **+4.4** / +6.2 / +13.3 / +14.4 dB. Line 5 sits on the game's own radio sound and its RMS includes its own pauses. |
| Sync | each sound is anchored to its clip (`"clip"` and `"offset"`), so dissolves cannot drift it. The thunder follows the on-screen bolts by 0.6 s (hook), 0.4 s (landing) and 0.2 s (window): light before sound. The door audio is the game's own recording of that moment. |

**History:**
- **Draft 1:** found the dissolve drift, which led to clip-anchored audio.
- **rc1:** found the storm quieter than the radio, so the storm was lifted.
- **rc1 to rc3:** the Hector take measured 877 sample spikes, so the narrator was switched to Adam.
- **rc4 to rc6:** ducking and bed levels tuned by measurement.

**Not done:** listening. Claude cannot hear. Voice accent and warmth, music phrasing at the cuts, and the overall feel are Daniel's check.
