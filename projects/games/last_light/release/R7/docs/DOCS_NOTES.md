# R7 docs: notes for the author (Worker D)

Everything here is in `release/R7/docs/`. Nothing outside it was touched. Godot was not run, so no number below was re-measured. Every figure comes from the sources named in section 2.

## 1. Decisions only the author can make

1. **"Програмният код е мое дело" (Appendix 4).** Left unchecked with `[[Решение на автора]]`. The workspace docs show the game was built with an AI coding assistant (Claude Code). The documentation therefore does **not** say who wrote the code. The roles table (1.2) is a placeholder for the author.
2. **Naming the AI-assisted material.** R0 and Q12 say no AI line in the game README or credits, and I added none. The Appendix 4 draft names Suno and ElevenLabs Free, as requested. It does **not** name ChatGPT (portraits, Q13; nine ending panels, Q11) or the coding assistant. Each place carries a `[[Решение на автора ...]]` note: Appendix 4 ("Други средства") and doc section 4.2. The documentation calls portraits and panels "изображения, подготвени от автора".
3. **The school header block.** I kept the template's header (ПГЕЕ, Пловдив, with logo, address and phone) as instructed. I do not know whether it is the author's school or only the template author's. Replace or remove it if it is not. The template's pre-filled supervisor line (name, phone, e-mail) was replaced by placeholders, and the file's author metadata was blanked.
4. **Authors.** The cover has two author lines (the rules allow at most two). Delete the second if there is only one.
5. **Instagram and e-mail links on the title screen (Q14).** The README says only that "two links open your browser or mail client". The rules exclude company advertising. A personal link is probably fine, but decide whether you want it visible to judges. I put no personal contact in the leaflet.
6. **Page limit.** I read "до пет листа А4" as at most 5 pages. The print version is 4 pages with placeholders (about 1,340 words). The screenshots will add roughly one page, so recheck the count after inserting them. If a sheet means a two-sided leaf, you have more room.
7. **Table font.** Tables use 11 pt at single spacing and the code block uses Courier New 10 pt. The body is Times New Roman 12 pt at 1.5 spacing. The rules say 12 pt and 1.5 throughout; the tables are my own choice.
8. **Print-version margins.** Left 2.5 cm and the others 1.8 cm, to fit the page limit. The full version keeps the template's margins (left 3.5 cm).
9. **Windows zip name and layout.** The README assumes `TheLastLight.exe` and a zip named `[[WIN_ZIP_NAME]]`. I did not see the Windows export.
10. **Leaflet fold.** I assumed a letter fold, with the right panel as the front cover and the left outside panel as the inner flap. Print double-sided, flipping on the short edge. The PDF was made with Brave (headless), because Chrome is not installed.

## 2. Claims I could not verify, or checked only against documents

| Claim | Where | Source and caveat |
|---|---|---|
| Test counts: story_test, run_tests 95/95, opening_test 31/31, interaction_test 164, regress_test 502/502, qa_sweep_test 7,703, save_compat_test 305, ross_test 42/42, sim_v2 identical, pytest PASS | README, doc 5.4, print | `20_release_plan.md` R1 to R3 tables. Not re-run. Re-run before submission. |
| "No SCRIPT ERROR", clean-checkout import, exported-app boots | doc 5.4 | R1 and R5 sections of the plan. The in-game click-through of the exported app is **NOT TESTED** and waits for R6. |
| 105/105 windowed regress after `_settle_focus()` | doc 2.2 | `docs/PROJECT_STATE.md` item 11. An older count. R30 is still flaky (backlog). |
| Performance (Low 16.7 ms; Medium 16.6 to 18.0; High 25.5 to 27.7; p95 up to 19.6; VRAM 1.08 to 1.32 GB) | README, doc 5.4 | R4 benches on the author's M3 only. The exported build's frame time is NOT TESTED. |
| Perf-bisect component costs (volumetric fog 2.5 to 4.5 ms, SSIL about 2.0, glow about 2, ocean about 2.2, shadows about 2.3) and "27 to 30 ms at the start" | doc 2.2 | `12_perf_bisect.md`. Single-run deltas are good to about ±1 ms (the bisect says so). The "faulty reflection probe" is paraphrased from it. |
| Horizon step 24 to 51 → 1.0 to 3.2 (binoculars 0.4 to 3.9) | doc 2.2, print | `14_stageM...md`, H1 table. |
| Panel shader numbers (30.5 → 5.3, predicted 5.7; 0.3 of a level; grade 0.3) | doc 2.2, print | R3 section. |
| Code size: 18,844 lines of GDScript in 57 files (includes capture, autotest and film tools that are not shipped); 8,279 lines of tests; 14,292 lines of Python in `blender/`; 1,172 lines of `.dlg` | doc 2.1, print | My `wc -l`. Text says "about". The `.dlg` figure includes comments. |
| "About 110 reply options", "about 60 beats", "24 duties" | README, doc | Counts of `*` lines in `.dlg` (109) and of beats and duties in `chapters.json` (60 and 24). |
| "15 documents" | README | Keys of `assets/docs/docs.json` (15). |
| About 90 commits, about 30 audit reports, `.blend` versions v001 to v038 | doc 1.3 | `git log -- .` on this branch (90 commits); 27 files in `audit-2026-11/`; file names. |
| Gerstner waves "5.3 to 60 m", 1100 m plane, far plane 1200 m | doc 2.2, 4.3 | `02_architecture.md` and `14_stageM`, as of 15 to 16 Nov. Not re-read in the current `outside.gd`. |
| Fog density formula and the visibility numbers (0.6 km at storm 1.0; 2.8 km at dawn) | doc 4.3 | Checked against `atmosphere.gd` (`fog_density`, `visibility_m`); the numbers are from the Stage M table. |
| Radar 250 m, 2.4 s; channel capture 55 to 150 m and 12° | doc 3.2, 4.3 | `radar.gd` and `keeper_config.gd` defaults. A beat may override the ranges. |
| 12 custom shaders | doc 4.1 | Count of `godot/shaders/*.gdshader`. |
| Windows needs Windows 10 or 11 and Vulkan 1.2 or D3D12 | README, doc 5.1 | From Godot's Forward+ requirements, not from the export. Not tested. |
| macOS 11 / 10.15 minimums | README | `export_presets.cfg`. |
| "Almost vanished profession of lighthouse keeper" | doc, Introduction | General knowledge. Check against a citable source if you keep it. |
| Firewatch (Campo Santo, 2016), Dear Esther (The Chinese Room, 2012, a Hebridean island), Papers, Please (Lucas Pope, 2013); "to our knowledge none puts the player in charge of the technical system" | doc, Introduction | From memory. The rules' template warns against "no such work exists" without a check, so the text hedges. Do a real check. |
| References: GPU Gems ch. 1 (Finch) and the other URLs | doc, Sources | Not opened online. Verify the links. The Beaufort scale entry is generic. |
| Macs: "tested on one Apple M3 only" | README | The release plan only ever mentions the M3. |
| `THIRD_PARTY_LICENSES.txt`: 102 components, 19 texts, 4 OFL texts | README, doc | R3 and R5 sections. |
| Source zip contents (godot, blender, audio, branding, story documents, licences) | README | `make_source_archive.sh`. The story documents go in only with `--with-docs`. |
| Mac zip 261.0 MB, app 378 MB | doc 5.1, README ("about 400 MB free") | R5 values. The README uses the `[[MAC_ZIP_SIZE]]` placeholder. The doc gives 261.0 MB as the "last export". Update after the R7 re-export. |
| Gamepad torch on the left trigger | README | `input_setup.gd`. It is missing from the in-game controls table in Options. |
| Bulgarian quality | all | I checked mixed Latin and Cyrillic words and the standard spelling "наративна". It has **not** been proofread by a native editor. Have it proofread. |

## 3. Placeholders (all highlighted yellow in the .docx and .html)

- **Sizes and hash:** `[[MAC_ZIP_SIZE]]`, `[[WIN_ZIP_SIZE]]`, `[[SOURCE_ZIP_SIZE]]`, `[[SOURCE_SHA256]]` (README_EN, README_BG, doc 5.1).
- **R6 and trailer:** `[[R6_PLAY_TIME]]` (README, doc 1.1), `[[TRAILER_LENGTH]]`, `[[TRAILER_FILE]]`, `[[WIN_ZIP_NAME]]` (README, leaflet), `[[QR код към трейлъра]]` (leaflet).
- **Authors and supervisor (cover of both .docx files, leaflet back, declaration):** names, phone, e-mail, school, class, supervisor name, phone, e-mail and position.
- **Doc 1.2:** the roles table.
- **Doc, Introduction:** `[[резултат от пробна игра с външен играч]]`, the fifth success criterion. The doc and the print version have the same slot.
- **Doc 4.2:** `[[Решение на автора ...]]` about tools.
- **Doc 5.4:** `[[R6: пробната игра на автора]]`.
- **Doc, Conclusion:** `[[Приложения до момента]]`. Rule 4.7 asks whether there are applications so far.
- **Declaration:** name, class, school, city, date, signature, "Други средства", "Trial версии", "Програмният код е мое дело", "лично мои".
- **Credits line "Narration voice: elevenlabs.io":** present in README section 8 and in the declaration. Per Q28 it must stay.

## 4. Screenshot slots (full .docx; each is a dashed box with a caption)

| Fig. | Slot | Suggested source (R1 captures in `renders/last_light/`, to be redone for R7) |
|---|---|---|
| 1 | screenshot 11, horizon before and after (2.2) | the `m0h_*` and M6 pair from Stage M |
| 2 | screenshot 09, architecture diagram (3.1) | to be drawn: `main_fp → game_fp → ...` |
| 3 | screenshot 02, radio and radar (3.3) | `r1_judge_t066_focus_radio-say_radio.png` |
| 4 | screenshot 03, generator panel (3.3) | `fp_gen` capture |
| 5 | screenshot 07, ending panel and card (3.4) | `r1_judge_t100_player-ending_correction.png` |
| 6 | screenshot 01, title menu (5.2) | `r1_judge_tmenu.png` |
| 7 | screenshot 08, Options > Accessibility (5.2) | a new capture |
| 8 | screenshot 10, test output (5.4) | a terminal capture of `run_tests` and `story_test` |

The **print version** has two slots: screenshot 02 (4.4) and screenshot 01 (4.6). The **leaflet** images (`Листовка_img/`, 4 captures plus the key art and logo) are **provisional** and must be swapped for the R7 set. The `radio` and `stair` images are cropped by CSS (`object-fit: cover`), so check the framing with the new images. `r1_judge_t090_..._binoculars` was too empty to use.

## 5. Production notes

- The template was used as the base. The cover and header were kept; the sample body text, unused media and its hyperlinks were removed. The table of contents is **static** (built from the LibreOffice layout). After final edits, in Word use right-click > Update field, or Ctrl+A then F9.
- The `.docx` files could not be run through the skill's XSD validator (`defusedxml` is not installed, and nothing was installed). They were checked by parsing every XML part, by an rId check, and by rendering in LibreOffice. Open them once in Word.
- The leaflet uses Source Sans 3 and Libre Baskerville from `godot/assets/fonts/` (relative `@font-face` paths, so keep the folder layout). **Libre Baskerville has no Cyrillic**, so it is used only for digits and Latin text; Bulgarian headings are in Source Sans 3.
- The README text twins (`README_EN.md` and `.txt`) come from one source, so they match.
- The only extra files besides the deliverables are the `Листовка_img/` folder (about 0.6 MB: provisional captures, key art and logo) and the rendered `Листовка.pdf`.
