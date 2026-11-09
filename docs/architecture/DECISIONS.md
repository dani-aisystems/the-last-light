# Confirmed decisions

These came from the requirements grilling on 2026-11-03. They are binding until Daniel changes them.

| # | Decision |
|---|---|
| Q1 | Serve both game assets and films. **Game-asset pipeline first.** Include the playbook's film workflow, but defer Puppeteer and synthesized sound until a film needs them. |
| Q2 | Targets: **Roblox (FBX)**, **Web (GLB)**, **Unity/Unreal (FBX presets only, no engine installs)**. |
| Q3 | Claude builds freely and saves versioned files. It **asks first** before overwrites, deletes, writes outside the workspace, downloads, or installs. |
| Q4 | The workspace stays standalone. Exports go to the Roblox project only with approval. A decision draft for that project is kept privately. |
| Q5 | Run on the host, hardened (localhost bind, local-scope MCP, manual start, rules, versioned saves). No VM for now. |
| Q6 | **CC0 assets only** (Poly Haven, ambientCG), fetched after an explicit OK, with the licence logged. No paid or AI-generation APIs. |
| Q7 | Default style: **stylized realism**. |
| Q8 | **EEVEE** for iteration previews. **Cycles (Metal)** for hero stills and finals, rendered in chunks. |
| Q9 | 2026-11-03 (THE LAST LIGHT): **Godot 4.7.2 installed** (`brew reinstall --cask godot`) with the official 4.7.2 macOS export template (SHA-512 verified), amending Q2's "no engine installs" for Godot only. Wrapper: `tools/godot`. |
| Q10 | 2026-11-03: standing OK to **overwrite generated build outputs** in `projects/games/last_light/godot/assets/` (GLB, audio, layout JSON); they are reproducible from `spec.py`/`build.py`/`synth.py`. `.blend` files stay versioned; everything else still asks. Local git commits at verified milestones, no pushes. |
| Q11 | 2026-11-09 (THE LAST LIGHT G6): **exception to the "no AI-generated images" rule for the item 34 ending panels only.** Daniel supplies those images himself (AI-built); the game shows them through the shared panel grade. The credits drop the old "no AI-generated images or voices" line and say nothing about AI. The P3 log pages are rendered by `blender/ending_pages.py`. **Extended the same day by Daniel to:** the item 22 radio-card portraits (his ChatGPT prints from one template, `blender/portraits_prepare.py`), the Mary Ellen's radio card (a print of the boat, `character-refs/ellen.png`), and the May 1952 photograph on the watch-room wall (`character-refs/Picture-wall/Vintage Maritime Portrait by the Sea.png`, aged by `documents.silver_print`). Everything else keeps the no-AI rule. |
| Q12 | 2026-11-09 (G6): credits read **"A game by Daniel Yanchev"**; credits music is the synthesised `music_menu` pad (`CreditsRoll.CREDITS_MUSIC`) until item 33 is picked; the credits state that the in-game documents and labels were rendered with macOS system fonts (an OFL re-render is a separate ROADMAP task); item 1's link strip reads `godot/data/links.json` and stays hidden until Daniel supplies the links. **G6c (2026-11-09):** the title's bottom-right corner always shows "A game by Daniel Yanchev"; the links join it when the file has entries. |
| Q13 | 2026-11-09 (THE LAST LIGHT G6, item 22): **the radio-card portraits are a second exception to the "no AI-generated images" rule.** Daniel makes them himself in ChatGPT from one shared template (framing, lighting, backdrop, grade) and drops them into `character-refs/<id>/`; `blender/portraits_prepare.py` crops them to 512x640 prints in `godot/assets/portraits/`. A missing expression shows the neutral print. Ross stays a silhouette (F12). The Blender bust probe (`blender/portraits.py`) is shelved. Every other image rule stands, and Claude never calls a generation API. |
