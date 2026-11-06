# Review flags: resolution log

On **2026-11-06** Daniel asked for every conflict to be resolved, with the profiles based on the AI-generated dossiers as reference. Each flag below records:
- the competing sources;
- the **resolution**;
- whether a game or asset change follows (listed in §D, **not applied yet**).

**Source shorthand:**
- `M:n` = STAGE3_NARRATIVE_MASTER.md line n;
- `chN:n` = `godot/data/story/chN.dlg` line n;
- `docs:id` = `godot/assets/docs/docs.json`;
- `B01` = `sources/batch-01.md`;
- `IMG` = the character's dossier image.

## Resolution rules (applied to every flag)
1. **Daniel's explicit rules come first.** For example, Ross appears only in silhouette.
2. **Text already shipped in the game decides plot facts.** That means `.dlg` dialogue, `docs.json` documents and speaker cards. Changing them would rewrite the story, which the brief rules out unless Daniel says otherwise, and another session is currently editing game files.
3. **The dossier and bible decide appearance, wardrobe, props, personality and voice.** They also decide any backstory the shipped game doesn't contradict. Details that exist only in the master script, never shipped, yield to the dossier wherever Daniel's newer material differs.
4. **Reconcile where possible.** If both versions can be true, both are kept and the profile says how they fit. A conflict counts as resolved by rejecting one side only when they cannot both stand.
5. Text printed inside the dossier images (logs, letters, timelines) is illustrative. It is adopted only when it agrees with rules 1–2.

Any ruling can be reversed by Daniel. Change the line and its change-log entry, then follow §D.

---

## A. New bible and dossiers against existing canon

### F01: Morag's career start, and who logged the Mayday
- **Sources:**
  - B01 and IMG: began late 1940s / c. 1950; "receives and logs" the Mayday.
  - Shipped ch2:26: "I took the call. I was twenty-six and it was my first winter on the set."
  - M:123: her senior logged it; she pencilled privately.
- **Resolution:** **joined the Stornoway radio room in 1953** (shipped line). She *took* the call, her senior *logged* it, and she pencilled her own notes. By 1971 she has eighteen years' service, not twenty-plus. The bible's points (clear voice, an ear for weak signals, "one wrong figure sends help to the wrong place") are kept.
- **Game change:** none.

### F02: The wording of Morag's 1953 notebook
- **Sources:**
  - B01 proposed page;
  - IMG page;
  - ch3:67-68 (spoken: "…oh-one-fifty-two… 'No light at North Point. Repeat. No light'");
  - M:230 (she answered "Roger, *Mary Ellen*", then nothing more came).
- **Problem:** the page's "01.58 Report of grounding" would mean Stornoway knew the grounding time that night. In canon, nothing came after 01:52, and wreckage was reported at 02:30.
- **Resolution:** the page is adopted as the **prop text** (CANON_INDEX §6, P01, now *adopted*) with one line changed: "01.58  Report of grounding — East Gut." becomes **"02.30  Wreckage reported — East Gut."**
  - "Light not seen before impact?" stays: it is her own question, written that night or later.
  - The quotation stays as pencilled, "no light at North Point". When she reads it aloud in ch3, the "Repeat. No light" is her remembering the voice. Both stand.
- **Game change:** none now. If the notebook later becomes a readable prop (3C/3D), use P01 exactly.

### F03: Log text printed in Callum's dossier
- **Sources:** IMG §11 "1953 (False entry)" and "1971 (Current log)" against docs:log_1953 and docs:log_1971.
- **Resolution:** the shipped documents are canon. The image's entries are **rejected as text** (its "false entry" actually admits the truth). Its **handwriting look** (upright, slight right slant, careful capitals) is adopted as the style target (F15).
- **Game change:** none.

### F04: Iain's unsent letter, two versions
- **Sources:**
  - IMG §7: a long letter dated "3 March 1958";
  - docs:letter_1957 and ch5:83-85 ("Christmas, nineteen fifty-seven. He died in the March."), shipped;
  - Ross's ch5:76 relies on the Christmas timing (the Harris Hotel, Kenny).
- **Resolution:** **the Christmas 1957 letter is canon, word for word.** The dossier letter is filed in Iain's profile as a non-canon *voice study*. It is useful for how Iain thinks ("a light is of no use if it does not show the truth"), but it is never quoted as a document.
- **Game change:** none.

### F05: Iain's service record and photographs
- **Sources:**
  - IMG: NLB service from the c. 1920s; principal keeper by the 1930s; a solo photo from the 1940s;
  - M:176 and M:215: principal keeper *of North Point* 1946–58;
  - docs:photo_keepers: "Iain & Callum Mackay, North Point, May 1952".
- **Resolution:** reconciled.
  - Iain joined the NLB in the 1920s and was a principal keeper at other stations from the 1930s. He was posted to North Point as principal keeper in 1946.
  - **The wall photograph is the May 1952 one of Iain and Callum** (shipped).
  - The dossier's solo picture is adopted as **Iain's likeness reference** (and could serve as a period studio portrait he owned), not as the wall photo.
- **Game change:** none. The likeness informs any future re-render of the 1952 photo (`blender/photo_render.py`).

### F06: Callum's wardrobe and shave
- **Sources:**
  - B01 and IMG: guernsey over a collared shirt, no insignia, a faint late-watch shadow;
  - M:117: NLB tunic with brass buttons, clean-shaven.
- **Resolution:** **dossier.** At collar level: a dark navy or charcoal wool guernsey over a pale, worn collared shirt, no insignia. Clean-shaven, with a faint shadow late in the watch. Hair brown greying at the temples; eyes grey-blue.
- **Game change:** `blender/portraits.py` Callum entry (3C): drop the tunic and buttons, add the guernsey and shirt collar, keep stubble low (§D).

### F07: Two endings in the bible, four in the game
- **Resolution:** reconciled. The bible's "Ending A, truth" and "Ending B, the protective lie" are the **choice axis**. The four shipped endings are that choice × the *Iona Star* saved or aground.
- **Game change:** none.

### F08: Rory's grandfather
- **Sources:**
  - IMG §6 and §10: "a crewman on the *Mary Ellen* … lost that night", "never came back";
  - shipped ch1:90-91 ("Below, in the engine. Only one of them that came home… He died at Easter"), ch2:113-117, ch5:69-77 (Ross's visit to Kenny, and Kenny relaying the drawer);
  - docs:clipping_1954 ("The sole survivor of the crew").
- **Resolution:** **canon.** Kenneth "Kenny" Bain survived, lived in Scalpay, and died at Easter 1971. The plot depends on him: he is how Ross learned of the letter.
  - The rest of the dossier's legend is kept, retold so that the grandfather *came home* and told the story (Rory profile §H).
- **Game change:** none.

### F09: Rory's boat registration, looks and father
- **Sources:**
  - IMG: *Kittiwake* "SY 76", a wooden boat of about 30 ft, creel and line; born c. 1949 in Harris; home Leverburgh; father died at sea in 1968; short curly brown hair, freckles, blue-grey eyes, wool cap, guernsey with an oilskin jacket;
  - shipped: "Sierra Yankee three-seven" (ch1:63), log_1971 "Kittiwake (SY 37)", speaker card;
  - M:140: red-brown hair, bunnet, gap tooth.
- **Resolution:**
  - **SY 37** (shipped). The illustration's "SY 76" is an image error.
  - **Looks come from the dossier:** short, curly, untidy brown hair; fair freckled wind-reddened skin; blue-grey eyes; a wool cap; a thick guernsey under a scuffed oilskin jacket. The gap-toothed grin is kept as a small extra: it isn't visible in the dossier and doesn't contradict it.
  - **Backstory from the dossier:** born c. 1949 in Harris, home Leverburgh, father lost at sea in 1968 (not in the 1953 wreck), inherited *Kittiwake*. His mother is alive (ch1:66).
- **Game change:** `portraits.py` Rory entry (3C): hair colour and shape, cap instead of bunnet, oilskin collar (§D).

### F10: Elspeth's home, chapters, voice and rank
- **Sources:**
  - IMG: home Leverburgh; on the radio ch1–2 and ch4; "Was it, Callum?"; went to sea c. 1960, deckhand 1962–66, second then first mate 1967–70; letter posted in Glasgow in a blocky hand, kept in a locked drawer in her cabin;
  - B01 Callum §7: "a skipper";
  - shipped: ch3, ch5 and ch6 only; "Mr Mackay"; "First mate" (ch3:38); "Master's injured. This is the mate." (ch5:118);
  - M:155: Glasgow from 1955, to sea at seventeen (1959).
- **Resolution:**
  - **Rank:** first mate (chief officer), not skipper (shipped).
  - **Home:** *born* in Leverburgh; *lives* in Glasgow since 1955 (both kept).
  - **Chapters:** ch3, ch5 and ch6 (shipped). The dossier's ch1–2 "distance" and ch4 "opening" are read as her off-screen state.
  - **Voice:** "Mr Mackay" on air; in extremity, "Callum Mackay" (ch6:7). Never a bare "Callum" (shipped pattern). The dossier's "Was it, Callum?" is rejected as wording; its intent is covered by ch6:9-11.
  - **Career:** reconciled. She went to sea at seventeen in 1959 as a junior on the Clyde coasters, sat her tickets through the early 1960s, then was second mate and **first mate of the *Iona Star* from about 1967–70**.
  - **Letter:** posted in Glasgow, blocky hand, kept a month in a locked drawer in her cabin. All adopted; none contradicts canon.
- **Game change:** none.

### F11: Ross's injury, his time on Pabbay, and what he wears
- **Sources:**
  - IMG: "broken rib and a bad cut"; hid on Pabbay while the Inquiry proceeded; left c. 1954 and took the name Sandy Morrison; a soft flat cap and a heavy coat or oilskin; short grey stubble;
  - shipped ch5:12 ("my hip broken"), ch5:16 (nine days, a crofter, "Sandy");
  - ch4:106: "An old man in an oilskin … rain running off the brim of his sou'wester";
  - M:174: black oilskin, white stubble;
  - `visitor_figure.gd`: olive oilskin, sou'wester.
- **Resolution:**
  - **Injury:** a broken hip (shipped). The dossier's rib and cut can be *additional* injuries; kept as minor.
  - **Pabbay:** reconciled. Nine days alone on shellfish and rainwater, then the crofter found him and kept him out of sight through the winter while the Inquiry did its work. He left the islands in 1954 and became Sandy Morrison in Govan.
  - **Headwear:** **sou'wester** tonight (shipped in ch4:106, and the silhouette's key shape). The dossier's **flat cap** is adopted as his *everyday* Govan cap, which he may carry or wear ashore, but tonight it's the sou'wester.
  - **Oilskin:** **black**, heavy and old, wet. The olive colour in `visitor_figure.gd` is to be corrected (§D).
  - **Stubble:** short, grey-white.
- **Game change:** the oilskin colour in `visitor_figure.gd` (§D).

### F12: Ross is never shown in a full portrait
- **Resolution:** **Daniel's rule.**
  - Ross appears only as a silhouette: at the door, in the stair light, and on any radio or identity card, **even after `knows_name`**. The reveal changes his name and identity line, never his face.
  - This replaces the 2026-11-05 3C plan ("Ross in person after the reveal").
  - The faces of Ross in the other dossiers' relationship panels are not reference.
- **Game change:** 3C portrait set, so Ross gets silhouette cards; `portraits.py` Ross entry (§D).

### F13: The six principals are now Iain, not Hector
- **Resolution:**
  - Full profiles for the six Daniel listed: Callum, Morag, Rory, Elspeth, Ross and Iain.
  - Hector keeps a **secondary profile** built from canon only, because he still has ch2–3 radio scenes.
  - Iain has no radio portrait; his likeness serves the 1952 photograph.
  - Hector's portrait uses the canon description (white beard, reefer jacket, peaked cap, pipe) until Daniel supplies a reference.
- **Game change:** none.

### F14: "MRSC" in 1971
- **Resolution:** **not used.** The references say "HM Coastguard, Stornoway", matching the speaker card. Unverified period terms stay out of game text.
- **Game change:** none.

### F15: Callum's handwriting specification
- **Resolution:** **the bible's specification is the target**:
  - 1953: upright, slight right slant, careful capitals, an open-topped 4, a straight 1, a narrow 7, firm pressure;
  - 1971: smaller and more angular, with the same 4, the same low t-bar, and the same wider gap before a recorded time.

  Canon "small square letters, a clerk's hand" describes the same hand. Applied at the 3C document re-render; test the chosen font or glyph set against the specification.
- **Game change:** document renders (3C) (§D).

### F16: Morag's look
- **Sources:** IMG and B01 (dark brown hair greying at the temples, grey-green eyes, dark cardigan over a collared blouse, no glasses shown); M:129 (auburn waves, glasses on a chain, a Stornoway pin).
- **Resolution:** **dossier.**
  - Dark brown hair with early grey at the temples, in a practical 1971 set.
  - Grey-green eyes.
  - A dark (navy) cardigan over a pale collared blouse.
  - **No glasses in the portrait.** Reading glasses become a desk prop, which suits the pencil notebook.
  - The Stornoway pin is dropped. It isn't in the dossier and isn't shipped.
- **Game change:** `portraits.py` Morag entry (3C) (§D).

### F17: Where the 1953 log is kept
- **Resolution:** reconciled. It is in the archive cabinet, filed with the other station logs (shipped ch2). That *is* "where it belongs", so the bible's point stands: it isn't hidden.
- **Game change:** none.

### F18: When Morag learns the Visitor is Ross
- **Resolution:** **canon.** In ch4 she knows only "a man at the door", and only if called on MF. She learns it is Ross in **ch5** (ch5:111, Ross speaks to her on the open set). The bible's ch4 paragraph applies from that moment.
- **Game change:** none.

### F19: How many died with the *Mary Ellen*
- **Sources:**
  - Ross IMG: "Seven of my crew went down with her";
  - Callum B01: "killed seven men";
  - shipped ch2:9 ("Lost with seven of the eight aboard, the skipper among them. Presumed."), ch5:12 ("Eight of us"), docs:clipping_1954 ("the loss of seven lives");
  - M:1663 ("six widows in Leverburgh, and to his").
- **Resolution:**
  - Eight aboard.
  - **Officially: seven lost, the skipper among them** (presumed).
  - **In truth: six of the crew died.** Ross and Kenny Bain survived.

  Characters who don't know Ross lived (Callum before ch4–5, Morag, Elspeth, Rory, the town) say "seven". Ross says six of his crew died, or "seven good men on the rocks", meaning the seven he put there.
- **Game change:** none.

### F20: Did Iain hear the Mayday?
- **Sources:**
  - Iain IMG §3: "He did not hear Morag Fraser's 01:52 Mayday";
  - shipped letter: "I heard the wireless in my sleep and thought I was dreaming."
- **Resolution:** **canon wording.** He half-heard it in his sleep and took it for a dream. He did not consciously hear it in time to act.
- **Game change:** none.

### F21: Ross and the word "ghost"
- **Sources:**
  - master voice table: Ross never says "ghost" (M:196);
  - shipped ch4:112: "with a ghost at the door";
  - Ross IMG sample: "a man can … still be a ghost, if he chooses."
- **Resolution:** Ross may use "ghost" **dryly, about himself** (a man the world thinks dead). Never as a claim about the supernatural, and never about the "ghost boat" legend as true.
- **Game change:** none.

## B. Internal issues in the existing canon

| ID | Issue | Resolution | Change needed |
|---|---|---|---|
| I01 | note_046 has "Reported again 2.2.61 … C.M." but Callum was posted elsewhere 1955–62 | Callum returned in 1962, so the line's date becomes **2.2.63**. "Engineer says 'next refit'" still works | docs.json and documents.py note_046 (§D) |
| I02 | log_1953 signature is drawn in Iain's copperplate, but it was written in Callum's hand | Callum's hand writes "Signed I. Mackay, P.K." too | documents.py render (§D) |
| I03 | Kenny is an "engine-man" (dialogue) but a "deckhand" in the clipping | **Engine-man** is the truth. The Gazette got it wrong, a plausible period error. Left as it is | none |
| I04 | Inquiry dated 18 Mar 1954, but the Gazette of Thursday 18 March says it "concluded … yesterday" | **The Inquiry concluded on Wednesday 17 March 1954 at Inverness.** The Gazette reported it on the 18th | master timeline wording (§D); CANON_INDEX updated |
| I05 | "Racing home before the Sabbath", but the wreck is at 01:58 on Sunday | They were racing to be in before the Sabbath (midnight on Saturday), were late, and Ross pushed her harder (ch5:21 "the Sabbath coming"). Consistent as it stands | none |
| I06 | At 06:30 Morag says "Three hours ago you told me…", but the ch3 admission is around 01:05–02:20 | Should be "Hours ago" | ch6:116 (§D) |
| I07 | §5.3 lists Oct 1971 before Sep 1971 | Sep before Oct (CANON_INDEX is correct) | master §5.3 (§D) |
| I08 | photo_1953: the docs text has a pencilled caption, but the print is rendered with a Callum-font caption | The docs text is canon: pencilled on the back, "Mary Ellen, July 1953. A. Ross, master.", with "Kenny B. on the hatch." beneath in another hand | documents.py render (§D) |
| I09 | The keepers' photo caption is rendered in Morag's font | Use a neutral print caption or Iain's hand | documents.py render (§D) |
| I10 | Ross's arc is "Keeper → the boy → Callum", but he already says "Callum" at the door | **Accepted.** At the door he uses the name as pressure. The arc describes warmth, not vocabulary | none |
| I11 | Mrs Ross is unstated, but "I named my boat for her" | She stays **unnamed**. The implication that the *Mary Ellen* was named for her stands, unconfirmed | none |
| I12 | The *Mary Ellen* speaker card reads "Registry: LOST 15.11.1953" from her first line | Out of scope here (a 3A UI item, already logged in FINDINGS_LOG:448) | — |
| I13 | NARRATIVE.md is stale in places | A "superseded by the master and character-refs" banner at the final consolidation. The body is not edited | NARRATIVE.md header (§D) |
| I14 | Portrait details are missing | Now defined in each profile §G | portraits.py (§D) |

## C. Missing information

| ID | Item | Status |
|---|---|---|
| G01 | The rest of Morag's bible (cut at §10 ch4) | **Open.** Profile filled from canon and IMG meanwhile; replace when resent |
| G02 | Written bibles for Rory, Elspeth, Ross and Iain | Profiles built from their dossier images plus canon (Daniel's instruction). Update if written bibles arrive |
| G03 | A visual reference for Hector | **Open.** Canon description used |
| G04 | Physical spec for Ross's letter | Resolved from IMG: plain paper, a plain blocky hand, posted in Glasgow, unsigned |
| G05 | Morag's notebook as a prop | Text fixed as P01 (F02). Building the prop is a 3C/3D decision |
| G06 | Callum's mother's name; Mrs Ross's name | Both stay unnamed |

## D. Follow-up changes and their status

**Portraits are paused (Daniel, 2026-11-06):** "I can provide images of each one I create … pause portraits for later when I am ready." D1–D4 and D6 wait for his images.
- The procedural Blender busts (`blender/portraits.py`) are kept as a working probe, uncommitted.
- In the probe test, the low-key bible lighting plus the 1971 print grade worked best.
- If Daniel's images are generated rather than drawn or photographed, CLAUDE.md's "no AI-generated images" rule needs his explicit call before they go into the game.

| # | Change | Files | From | Status |
|---|---|---|---|---|
| D1 | Callum's bust: guernsey and shirt collar instead of tunic and buttons; grey-blue eyes | `blender/portraits.py` | F06 | In the probe; portraits paused |
| D2 | Morag's bust: dark brown greying hair, grey-green eyes, no glasses, no pin | `blender/portraits.py` | F16 | In the probe; portraits paused |
| D3 | Rory's bust: curly brown hair, wool cap, freckles, blue-grey eyes, oilskin over a guernsey, gap tooth | `blender/portraits.py` | F09 | In the probe (no gap tooth yet); portraits paused |
| D4 | Ross: silhouette cards only. Remove the full-face portrait from the game set | `blender/portraits.py`, 3C card code | F12 | Probe has a silhouette mode (the face still reads; needs darker); portraits paused |
| D5 | The Visitor's oilskin to black | `godot/scripts/fp/visitor_figure.gd` | F11 | Applied; parse-checked headless; not yet seen in a capture. The coat-stand oilskin (`materials.gd` `M_LL_Oilskin`, Callum's own coat) correctly stays olive |
| D6 | Per-character eye colours: Callum grey-blue, Morag grey-green, Rory blue-grey, Elspeth and Ross grey | `blender/portraits.py` | I14 | In the probe; portraits paused |
| D7 | note_046: "2.2.61" becomes "2.2.63" | `docs.json`, `blender/documents.py` | I01 | **Done** by the G2 session, commit `7ac1175` |
| D8 | log_1953 signature row in Callum's hand; photo_1953 caption from the docs text; keepers' photo caption not in Morag's font; Callum's hand meets the F15 specification | `blender/documents.py` | I02, I08, I09, F15 | Assigned to the brief's G4 (other session) |
| D9 | "Three hours ago" becomes "Hours ago" | `ch6.dlg:116` | I06 | **Done** by the G2 session, commit `193fcf3` |
| D10 | Master: Inquiry 17 Mar 1954; §5.3 order; a pointer to character-refs | `STAGE3_NARRATIVE_MASTER.md` | I04, I07 | Applied, uncommitted |
| D11 | Banner pointing to the master and character-refs | `NARRATIVE.md` | I13 | Applied, uncommitted |

## Change log
- **2026-11-06 (a):** created from batch 01, the six dossier images and the read-only canon audit (F01–F18, I01–I14, G01–G06).
- **2026-11-06 (c):** D5, D10 and D11 applied here; D7 and D9 applied by the G2 session. Portraits paused by Daniel until he supplies images. `tools/refs_check.py` added (sync and check).
- **2026-11-06 (b):** Daniel instructed that all conflicts be resolved, using the dossiers as reference. Resolution rules and resolutions recorded. F19–F21 added from the full dossier read. §D lists the follow-up changes, none applied.
