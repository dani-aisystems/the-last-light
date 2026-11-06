# THE LAST LIGHT: music shortlist (finding 33, G5), 2026-11-06

For Daniel to pick from. **Nothing has been downloaded or auditioned.** Tempo and dynamics are inferred from the piece and its title, so every pick needs a listen first.

## Criteria (FINDINGS_LOG 33)
- Sparse and slow (≤ 70 bpm or unmetred), minor or modal.
- No vocals and no percussion; at least 2 minutes long or loopable.
- Sits under the wind and rain without masking them.

## Sources
- **All candidates:** solo-piano Musopen recordings on Wikimedia Commons, of music whose composer died in 1849 or earlier.
- **Licence check:** the licence was read on each item's own page by a research agent. For the top two, I re-checked the page myself, and the quotes match.
- **Licence wording:** some pages say "CC0 1.0"; the rest say "released into the public domain by its author, Musopen. This applies worldwide." The second form is a public-domain dedication of the recording, not the literal CC0 text. **Daniel decides whether that wording is acceptable.**
- **Musopen's own terms:** the Commons pages note that Musopen's own site materials are copyrighted. That covers the website, not these files.

## Top 3
| # | Piece | Performer | Licence on the page (quoted) | Length / format | Suggested use | Risk |
|---|---|---|---|---|---|---|
| 1 | Chopin, Nocturne in E minor, Op. posth. 72 No. 1 ([page](https://commons.wikimedia.org/wiki/File:Chopin_-_Nocturne_Op._posth._72_no._1.ogg)) | Luke Faulkner | "This file is made available under the Creative Commons CC0 1.0 Universal Public Domain Dedication." *(re-checked)* | 4:33, OGG 112 kbps. A FLAC of the same recording ([page](https://commons.wikimedia.org/wiki/File:Chopin_-_Nocturne_No._19_in_E_minor,_Op._72_No._1_(Luke_Faulkner).flac)) is marked "released into the public domain … Musopen" | Credits, faded at about 3:00; or the menu | Lossy original (prefer the FLAC). Likely a modest mid-piece swell |
| 2 | Chopin, Nocturne in C-sharp minor, B. 49 ([page](https://commons.wikimedia.org/wiki/File:Chopin_-_Nocturne_No._20_in_C-sharp_minor,_B._49_(Frank_Levy).flac)) | Frank Lévy | "This work has been released into the public domain by its author, Musopen. This applies worldwide." *(re-checked)* | 3:45, FLAC 1.84 Mbps (49 MB) | Loading screen, crossfading into chapter 1 | PD wording, not CC0. It is a well-known piece (recognisable) |
| 3 | Chopin, Nocturne in F minor, Op. 55 No. 1 ([page](https://commons.wikimedia.org/wiki/File:Chopin_-_Nocturne-op-55-no-1.ogg)) | Luke Faulkner | "CC0 1.0 Universal Public Domain Dedication" | 5:17, OGG 92 kbps | Menu loop | Low bitrate. The middle section is livelier, so it needs a loop region |

## Other candidates (licence read by the agent, not re-checked)
| Piece | Performer | Licence | Length | Use | Risk |
|---|---|---|---|---|---|
| Nocturne Op. 48 No. 2, F-sharp minor ([page](https://commons.wikimedia.org/wiki/File:Chopin_-_Nocturne_No._14_in_F-sharp_minor,_Op._48_No._2_(Luke_Faulkner).flac)) | Luke Faulkner | PD (Musopen) | 8:16 | Credits (cut) | Long; loud middle |
| Nocturne Op. 37 No. 1, G minor ([page](https://commons.wikimedia.org/wiki/File:Chopin_-_Nocturne_No._11_in_G_minor,_Op._37_No._1_(Luis_Sarro).flac)) | Luis Sarro | PD (Musopen) | 7:04 | Credits | Major-key chorale in the middle |
| Nocturne Op. 9 No. 1, B-flat minor ([page](https://commons.wikimedia.org/wiki/File:Chopin_-_Nocturne_No._1_in_B-flat_minor,_Op._9_No._1_(Olga_Gurevich).flac)) | Olga Gurevich | PD (Musopen) | 5:37 | Menu | Agitated middle |
| Étude Op. 10 No. 6 "Lament", E-flat minor ([page](https://commons.wikimedia.org/wiki/File:Chopin_-_12_%C3%89tudes,_Op._10_-_No._6_in_E-Flat_minor_%27Lament%27_(Edward_Neeman).flac)) | Edward Neeman | PD (Musopen) | 4:13 | Menu or credits | Busier left hand |
| Nocturne Op. 48 No. 1, C minor ([page](https://commons.wikimedia.org/wiki/File:Chopin_-_Nocturne_No._13_in_C_minor,_Op._48_No._1_(Luke_Faulkner).flac)) | Luke Faulkner | PD (Musopen) | 6:19 | Credits (cut) | Loud, dramatic middle; poor under the storm |
| Largo in E-flat major, B. 109 ([page](https://commons.wikimedia.org/wiki/File:Chopin_-_Largo_in_E-flat_major,_B._109_(Aya_Higuchi).flac)) | Aya Higuchi | PD (Musopen) | 2:14 | Loading (loop) | Major key, which misses the criterion |
| Beethoven, String Quartet Op. 18 No. 6, II. Adagio ([page](https://commons.wikimedia.org/wiki/File:Beethoven_StringQuartetNo.6inBFlatMajorOp.18_LudwigVanBeethoven-StringQuartetNo.6InBFlatMajorOp.18No.6-02-AdagioMaNonTroppo.ogg)) | Musopen String Quartet | CC0 1.0 | 7:02 | Credits | Major key; a quartet, not solo |

## Gaps
- **Scottish air:** none qualifies. The Commons recordings checked are CC BY-SA, and one is probably vocal. No CC0 "Flowers of the Forest" or similar was found.
- **Cello or low strings:** no CC0 recording was found.
- **Not searched properly:**
  - OpenGameArt (the site refused automated fetches);
  - Free Music Archive;
  - Internet Archive (search errored).

  A second pass there is possible if none of the above suits.

## After Daniel picks
1. **Fetch it.** Use the FLAC where one exists. `tools/fetch_cc0.py` supports only Poly Haven and ambientCG, so the fetch is a manual one-off, run only with Daniel's OK, or the tool gains a `commons` source (a script change, also with his OK).
2. **Log it.** Add the file to `assets/ASSET_LICENSES.md` with the page URL and the licence sentence quoted.
3. **Fit it to the game.**
   - set loop points, or a fade for the credits;
   - mix at −18 to −14 LUFS under the ambience;
   - crossfade menu → loading → game, fading out under the first chapter card;
   - use it as the credits music for finding 34;
   - check the seams with `analyze.py`.
