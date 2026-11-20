# THE LAST LIGHT trailer: music and sound cue sheet (rc6)

Every sound is the game's own: Daniel Yanchev's score (Suno, his subscription, DECISIONS Q16/Q27), the game's synthesised and CC0 effects (`assets/ASSET_LICENSES.md`), the game's own mix recorded in-engine, and the narration (ElevenLabs Free, voice 'Adam - Classic Scottish Storyteller', Eleven Multilingual v2; DECISIONS Q28; credit: elevenlabs.io). Levels were set by measurement; **not auditioned by ear** (Claude cannot listen).

| At | Bus | Source | Source in / dur | Gain dB | Note |
|---|---|---|---|---|---|
| 0:00.00 | music | `m01.mp3` | 0.0 / 20.0 | -8 | M01 title: the falling motif |
| 0:15.50 | music | `m02.mp3` | 24.0 / 24.0 | -14 | M02 arrival: its swell (cue 40-52 s) under the radio and the boats |
| 0:38.50 | music | `m04b.mp3` | 28.0 / 19.8 | 1 | M04b restless: the storm; cut dead on the black |
| 0:42.50 | music | `m05.mp3` | 40.0 / 14.0 | -4 | M05 mechanism: the slipping gear |
| 0:59.80 | music | `m09.mp3` | 0.0 / 18.0 | -3 | M09 decision: the motif that never reaches its fifth note |
| 0:00.00 | fx | `amb_wind.wav` | 0.0 / 40.0 | -15 | wind bed (loops in the game) |
| 0:38.50 | fx | `amb_wind.wav` | 2.0 / 19.8 | -6 |  |
| 0:15.00 | fx | `amb_rain_glass.wav` | 0.0 / 30.0 | -21 |  |
| 0:06.10 | fx | `thunder_2.wav` | 0 / full | -4 | after the bolt in r01 (5.5 s) |
| 0:10.00 | fx | `TheLastLight_Gameplay_Ch1_master.mp4` | 39.0 / 5.0 | -3 | the game's own sound: the charge switch, the engine, the lamps |
| 0:29.00 | fx | `r06_radio_morag.wav` | 1.0 / 6.5 | -12 | the game's own radio sound under Morag's card |
| 0:35.50 | fx | `r07_bino_storm.wav` | 6.0 / 3.5 | -14 |  |
| 0:41.40 | fx | `thunder_5.wav` | 0 / full | 1 | after the landing bolt (5 s in the shot) |
| 0:43.30 | fx | `thunder_1.wav` | 0 / full | 0 |  |
| 0:47.30 | fx | `clockwork.wav` | 0.0 / 3.0 | -8 | the lens clockwork under the lantern |
| 0:50.30 | fx | `r13_door_ross.wav` | 24.5 / 8.0 | 3 | the game's own door, stair and storm |
| 0:59.30 | fx | `amb_sea.wav` | 0.0 / 18.0 | -18 | the calm sea at dawn |
| 0:01.80 | vo | `line_01.wav` | 0 / full | 5.2 | Eighteen years ago tonight, a boat called the Mary Ellen went onto the rocks below this light. |
| 0:20.00 | vo | `line_02.wav` | 0 / full | 4.3 | The inquiry said her master was to blame. |
| 0:23.10 | vo | `line_03.wav` | 0 / full | 2.7 | The station log said the light was burning. |
| 0:25.60 | vo | `line_04.wav` | 0 / full | 2.3 | I know what the log said... I wrote it. |
| 0:30.80 | vo | `line_05.wav` | 0 / full | 4.6 | Tonight, the same gale. The same channel. |
| 0:35.80 | vo | `line_06.wav` | 0 / full | 4.6 | And someone out there is calling as the Mary Ellen. |
| 1:01.10 | vo | `line_07.wav` | 0 / full | 4.7 | By dawn, Stornoway will want my report. |
| 1:05.40 | vo | `line_08.wav` | 0 / full | 5.3 | One line in a book. That's all it ever was. |

Mix: music ducked by the narration (sidechain, threshold 0.015, ratio 8, attack 50 ms, release 700 ms); two-pass EBU R128 loudness normalisation to -16 LUFS integrated, -1 dBTP; measured result -16.0 LUFS, true peak -1.0 dBTP, 0 clipped samples.

Narration over its real (ducked) bed, RMS over 2.5 s from each line's start: +18.9, +11.2, +9.6, +9.0, +4.4 (line 5 sits on the game's own radio sound and includes its own pauses), +6.2, +13.3, +14.4 dB.
