THE LAST LIGHT
==============

A first-person narrative game by Daniel Yanchev. Version 1.0. Submitted to the National Autumn
IT Tournament "John Atanasov" 2026/27, Sofia, 4-6 December 2026.

1. OVERVIEW
-----------

Genre. First-person narrative game with a station simulation. Single player, offline, one night
of play in six chapters. The interface and all text are in English. There is no voice acting:
dialogue is shown as text, with synthesised radio sound.

Premise. North Point Light is a fictional lighthouse in the Outer Hebrides. It is the night
of 14-15 November 1971, and a severe gale is blowing. You are Callum Mackay, the principal
keeper. You keep the lamp turning, the generator running and the batteries charged, and you talk
the fishing boats home through the reefs by radio, using the radar on your desk.

Then, just before midnight, a voice on Channel 16 gives the name of a trawler that went down
on the rocks below this light eighteen years ago tonight. Before dawn, someone will climb the
stair.

The experience.
- You run the station by hand: open the fuel valve, crank and run the generator, charge the
  batteries, light the lamp and keep its clockwork turning, reset breakers, free a jammed gear.
- You work the radio and radar: confirm a vessel's position, give turn, speed and hold orders,
  and bring each boat through the safe channel.
- You read what the room holds: the station log, a 1957 letter, a 1954 inquiry extract,
  photographs, tide tables, a forecast (15 documents).
- You talk, and you choose what to say. There are about 110 reply options across the six
  chapters.
- Four endings. Estimated time for one playthrough: about 65–110 minutes (typically about 80), excluding the credits (about 1–2 minutes more; Esc skips them).

What is distinctive.
- The story and the simulation depend on each other. With no power there is no radio and no
  light, so a failing generator is a story problem as well as a technical one.
- The ending is decided by a duty, not a menu: what you write in the station log at dawn, and
  whether you bring the last ship through. The rule is in section 5.
- The 1971 watch room, the lighthouse, the documents and the dials were built for the game from
  Python scripts driving Blender, then imported into Godot. The keeper's hands and body are
  built on a CC0 base mesh.
- Accessibility is part of the options, not an add-on (section 6).

2. TECHNICAL INFORMATION
------------------------

  Item              Value
  ---------------   ----------------------------------------------------------------------------
  Engine            Godot Engine 4.7.2, GDScript, Forward+ renderer
  Assets            Blender 5.2, built from scripts (blender/), exported as GLB
  Platforms         macOS (tested on an Apple M3 Mac), Windows (exported, not run-tested)
  macOS             macOS 11 or later on Apple silicon; macOS 10.15 or later on Intel; a Metal-
                    capable GPU. Universal app (arm64 and x86_64)
  Windows           64-bit Windows 10 or 11 and a GPU with Vulkan 1.2 or Direct3D 12 support (a
                    requirement of Godot's Forward+ renderer)
  Disk space        about 400 MB free (the macOS app is 378 MB unpacked)
  Download size     macOS zip 261.0 MB; Windows zip 236.5 MB; source zip
                    713.2 MB
  Display           1920 x 1080 base, scaled to the window. Starts fullscreen; F11 toggles
  Quality presets   Low, Medium (default, 60 fps target), High (30 fps or more)
  Input             Keyboard and mouse; gamepad (Xbox or PlayStation layout)
  Saving            Automatic. Continue on the title screen resumes
  Network           None. Two links on the title screen open your browser or mail client, only
                    if you click them
  Source            Included: TheLastLight-source.zip (SHA-256 397dea040287f521cacba714c66ec4650b0a28af4041535b44ccdf93522c7a4d)

Measured performance (Apple M3, fullscreen Retina, focused benchmarks, frame times): Low 16.7 ms
median (the 60 Hz cap); Medium 16.6 to 18.0 ms median and at most 19.6 ms at the 95th
percentile; High 25.5 to 27.7 ms.

Automated tests (all passing at the last full run): story_test (all four endings reached by bot
campaigns), run_tests 95/95, opening_test 31/31, interaction_test 164 checks, regress_test
503/503, qa_sweep_test 7,703 checks, save_compat_test 305 checks (old save files still load),
ross_test 42/42, and the Python tests. The headless simulation gives identical results on seeds
1 to 5. The tests are in godot/tests/.

3. INSTALLATION
---------------

macOS
~~~~~

1. Unzip TheLastLight.zip. You get The Last Light.app and THIRD_PARTY_LICENSES.txt.
2. Double-click The Last Light. The app is not notarised by Apple (that needs a paid developer
   account), so macOS blocks it the first time: "Apple could not verify ... is free of malware".
   Click Done, not "Move to Bin".
3. Open System Settings > Privacy & Security, scroll down to the Security section, and click
   Open Anyway next to "The Last Light was blocked". Confirm with your password or Touch ID.
4. The game opens. From then on it opens normally.

Alternatives:
- On macOS 14 or earlier: right-click the app, choose Open, then Open again.
- In Terminal, remove the quarantine mark once: xattr -dr com.apple.quarantine "The Last
  Light.app". Then double-click as usual.

The app is signed ad hoc and its signature verifies. It is only missing Apple's notarisation.

Windows
~~~~~~~

The Windows build was exported but has not been run-tested on a Windows PC.
1. Unzip the Windows zip into a folder of your own. Keep all the files together.
2. Run TheLastLight.exe.
3. Windows SmartScreen may say "Windows protected your PC", because the program is unsigned.
   Click More info, then Run anyway.

From source (optional)
~~~~~~~~~~~~~~~~~~~~~~

Unzip TheLastLight-source.zip, open the godot/ folder in Godot Engine 4.7.2 (godot.org, free)
and press Import, then Run. To run the tests from a terminal: godot --headless --path godot -s
res://tests/run_tests.gd (and story_test.gd, opening_test.gd, and so on).

4. UNINSTALL
------------

- macOS: drag The Last Light.app to the Bin. Windows: delete the game's folder. The game writes
  nothing else to the system.
- To remove saves and settings as well, delete the data folder:
  - macOS: ~/Library/Application Support/Godot/app_userdata/The Last Light
  - Windows: %APPDATA%\Godot\app_userdata\The Last Light
  - Inside it, saves/ holds the saves and settings.cfg the options. Deleting saves/ starts the
    story afresh.

5. PLAYING
----------

Where to begin. Choose New Game. The first minutes teach the station: the duty line at the top
of the screen says what to do next, and the keeper's thoughts say why.

How choices matter. Two things decide the ending: whether, in the dawn report, you tell the
truth about the old log entry or let it stand, and whether the last ship, the Iona Star, comes
through the East Gut or is lost. Earlier choices, such as what you tell the visitor and what you
do with a letter, change the epilogue lines and some radio conversations. How well you keep the
light turning and guide her in by radio decides the ship.

  Dawn report   Iona Star saved     Iona Star lost
  -----------   -----------------   --------------------------
  The truth     Correction          Heard Together
  The lie       Nothing to Report   Light Exhibited Throughout

A full play takes one sitting. The game saves at every beat and chapter, so you can stop at any
time and use Continue.

Controls: keyboard and mouse
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Action                               Key
  ----------------------------------   ---------------------------------------------------------
  Look                                 Mouse
  Walk                                 W A S D or arrow keys
  Hurry                                Shift
  Use, pick up, answer the radio       E or left click
  Choose a reply in a conversation     1 to 4
  Radio: send an order to the          1 to 6 (confirm position, port 30, starboard 30, slow,
  selected vessel                      hold, maintain course)
  Radio: next vessel                   Tab
  Current duty (hold for the latest    J
  hint)
  Station log                          L
  Dialogue history                     H
  Transcription of a document you      T
  are reading
  Binoculars / hand compass / torch    B / G / F
  Handwheel on the console             A / D
  Selector knobs                       Mouse wheel or right click
  Step back from a view; pause         Esc or right click
  Fullscreen                           F11

Controls: gamepad
~~~~~~~~~~~~~~~~~

  Action                         Button
  ----------------------------   -------------------------
  Walk / look                    Left stick / right stick
  Use                            A (Cross)
  Step back                      B (Circle)
  Choose a reply                 D-pad, then A
  Hurry                          Left stick click
  Station log / transcription    Y (Triangle) / X (Square)
  Current duty                   Right stick click
  Dialogue history               View / Share
  Torch                          Left trigger
  Selector knobs / next vessel   LB, RB
  Handwheel                      Left stick or D-pad
  Pause                          Start

The binoculars, compass and fullscreen have no gamepad button. In device views (radio, radar,
console) the right stick moves a cursor and A clicks.

6. ACCESSIBILITY
----------------

All of these are in Options.
- Text: dialogue size 0.8x to 1.5x; text speed; reading time per line from 0.75x to 3x; ship
  radio chatter subtitles can be turned off (story dialogue always shows); sounds that matter to
  the story are captioned; a dialogue history (H) keeps every line.
- Guidance: Minimal (the room and the log), Standard (a short duty line, hints when stuck) or
  Full (the duty and its steps always shown). The duty line's time on screen is adjustable.
- Comfort: reduce flashing (lightning); reduce motion (title screen); head bob off; field of
  view 60 to 90; brightness.
- Controls: mouse and gamepad sensitivity; invert Y; the generator crank can be held or pressed
  once; full gamepad support.
- Audio: separate volume for master, music, effects, dialogue and radio, and ambience.

7. CREDITS AND LICENCES
-----------------------

- A game by Daniel Yanchev. Story, dialogue, code, models, documents, dials and charts. Music by
  Daniel Yanchev.
- Tools: Godot Engine 4.7.2 (MIT); Blender 5.2 (GPL); FFmpeg (audio and video processing);
  Python with Pillow and NumPy (asset scripts); Git and Git LFS.
- CC0 1.0 sources:
  - Textures from Poly Haven (polyhaven.com): cliff_side, coast_land_rocks_01, sparse_grass,
    painted_concrete, rusty_painted_metal, distressed_painted_planks, oak_veneer_01,
    dark_wooden_planks, green_metal_rust, metal_plate_02, plastered_wall_02,
    concrete_floor_worn_001.
  - Human Base Meshes v1.4.1 by Blender Studio (the keeper's hands and body).
  - Recordings from Freesound (freesound.org): coughs by georgisound and husky70; breathing by
    sickfin; footsteps by SoftDistortionFX; stair steps by RFCaldas; door hinge by kyles;
    telephone by TRP; kettle by wlabarron; teleprinter by craigsmith.
- Typefaces, SIL Open Font License 1.1: Libre Baskerville (Pablo Impallari, Rodrigo Fuenzalida),
  Source Sans 3 (Paul D. Hunt, Adobe), Courier Prime (Alan Dague-Greene), Cedarville Cursive
  (Kimberly Geswein).
- Licence texts: THIRD_PARTY_LICENSES.txt, next to the game (Godot's MIT licence and its 102
  components, and the four font licences). The asset log is assets/ASSET_LICENSES.md in the
  source zip.
- The characters, vessels, North Point Light and the events of 1953 are fictional.

8. TRAILER
----------

TheLastLight_Trailer_narration-elevenlabs.io.mp4, 1:17. Narration voice: elevenlabs.io.

9. PACKAGE CONTENTS
-------------------

  File                      What it is
  -----------------------   --------------------------------------------------------------------
  TheLastLight.zip          macOS build: The Last Light.app and THIRD_PARTY_LICENSES.txt
  TheLastLight-Windows.zip          Windows build (exported, not run-tested)
  TheLastLight-source.zip   Source: godot/ (project, scripts, data, tests), blender/ (asset
                            scripts and .blend files), audio/, branding/, the story documents
                            and the licence files
  README_EN, README_BG      This file in English and Bulgarian
  TheLastLight_Trailer_narration-elevenlabs.io.mp4          Trailer

Inside godot/scripts/: core/ (the station simulation and its configuration), story/ (director,
dialogue parser, presenter, saves of story state), fp/ (first-person play: player, room, radio,
radar, sea), ui/ (dialogue, duty line, log, history), and audio_director.gd. The story itself is
data: godot/data/story/chapters.json and six .dlg files.

10. KNOWN LIMITATIONS
---------------------

- The interface and story are in English only.
- The macOS app is not notarised, so the first launch needs the steps in section 3.
- The Windows build was exported but not run-tested.
- The High quality preset is heavier than Medium (about 26 to 28 ms per frame on the development
  Mac, below 60 fps). Use Medium or Low if it stutters.
- Chapters 3 and 4 are dark by design when the room lights are off. Raise Brightness in Options
  if you need to.
- It has been tested on one Apple M3 Mac only; Intel Macs and other graphics cards have not been
  tested.
