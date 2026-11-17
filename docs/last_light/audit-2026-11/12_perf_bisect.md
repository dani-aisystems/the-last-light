# THE LAST LIGHT: performance bisect, 2026-11-16

The bisect the plan put first in Stage A (Stage 0 measured Medium at 27 to 30 ms median against the 16.7 ms budget). Daniel said the Mac was free. Index: [README](README.md).

**Method.** Foreground `tools/godot --audio-driver Dummy ... --bench --quality=1 --novsync --bench_secs=20 --bench_shots=fp_desk,fp_window,fp_gen --bot=expert`, one run per flag, sequential, worst case (storm 1.0, lightning every 3 s, generator running, one ship). New debug-only flags: `--bench_body` (keep the keeper's body visible and animating in detached bench views, as in play; since Stage B those views hide it), `--nobodyshadow`, `--nomoonshadow`, `--noisland`. JSON: `renders/last_light/pb_*_bench.json`.

**Conditions.** A Playwright job in another project started at 12:28 and loaded the Mac (load average 14.5), so the bench was stopped and resumed later behind a guard (each run waits for a 1-minute load below 3 and no headless Chromium). The afternoon was never fully idle (5-minute load 3 to 7): the baseline itself moved between 17.6 and 19.3 ms. Only the desk and window views are used for deltas (the generator view drifted 10 % between baselines). Single-run deltas are good to about ±1 ms; the paired runs below are better.

## 1. Results, Medium (median ms)

| Run | Desk | Window | Gen | Note |
|---|---|---|---|---|
| base (body hidden), 12:23 | 18.36 | 18.56 | 17.30 | quiet Mac |
| base_body, 12:24 | 18.58 | 18.09 | 16.84 | body costs < 0.5 ms |
| nobodyshadow | 18.18 | 17.38 | 16.27 | |
| norain | 18.02 | 18.16 | 17.30 | rain < 0.5 ms in the room |
| base_body_r, 13:32 / base_body2, 17:12 | 19.14 / 19.33 | 19.00 / 19.06 | 17.05 / 18.85 | baselines for the flags below |
| nomoonshadow | 18.22 | 18.86 | 17.48 | ~0 |
| noisland | 17.81 | 17.84 | 17.59 | about -1, noisy |
| noglass | 18.95 | 19.11 | 18.14 | 0 |
| novolfog | 16.62 | 14.51 | 14.13 | -2.5 desk, -4.5 window |
| nossao | 18.83 | 18.99 | 17.90 | 0 (half-size, low) |
| noglow | 17.14 | 17.02 | 15.89 | about -2 |
| noocean | 16.79 | 16.79 | 15.97 | about -2.2 |
| noshadows | 16.04 | 16.71 | 16.63 | about -2.3 (draw calls 927 → 293) |
| nossil, probe=off (16:54, 17:10) | 12.94, 13.01 | 13.19, 13.15 | | about -6 each: **not reproduced**, see below |
| **probefix**, 17:16 / again 17:22 | 17.76 / 17.65 | 17.65 / 17.55 | 16.73 / 17.30 | baseline 17:14: 18.10 / 18.17 / 16.43 |
| **probefix + nossil**, 17:19 | 15.69 | 15.77 | 14.79 | paired: **SSIL ≈ 2.0 ms** |
| probefix + probe=off, 17:21 | 17.50 | 16.93 | 16.18 | the probe now costs 0.2-0.7 ms |

## 2. Findings

1. **Stage 0's 27 to 30 ms was machine load**, not the build. On a quiet Mac Medium is 17.3 to 19.3 ms: the long-standing 1 to 2 ms over 16.7 recorded on 5 November (17.4 to 18.6).
2. **Things added since 5 November are cheap:** the keeper's body under 0.5 ms (its shadows included), the moon's shadow over the island about 0, the island about 1 ms (noisy), the window-glass rain shader 0, the rain under 0.5 ms.
3. **The standing per-pixel effects are where the time goes:** SSIL about 2.0 ms (paired), volumetric fog about 2.5 ms (desk), shadows about 2.3, ocean about 2.2, glow about 2.0 (single runs).
4. **Probe writes.** `_update_probe` set the room probe's ambient energy and intensity every frame; setting a probe property can make Godot re-capture it. They are now written only when they change (`station.gd _probe_set`), which gives no visual change. Measured gain about 0.5 ms (within noise); the 6 ms readings of `--probe=off` and `--nossil` in the afternoon were not reproduced in the closely spaced set and are treated as load.

## 3. Proposals and what was done (Daniel 2026-11-17: "U determine the rest", DECISIONS Q18)

| # | Change | Expected Medium | Visual cost |
|---|---|---|---|
| P1 (**done**) | SSIL off on Medium (High keeps it) | about -2.0 ms → about 15.7 ms, inside 16.7 | less warm bounce off the cream walls; the R4 blackout tuning of SSIL then applies to High only. Before/after captures needed |
| P2 | Volumetric fog on Medium at a lower froxel size / depth (project setting `volumetric_fog_size` 64 → 48, `depth` 64 → 48), instead of off | about -1 ms (estimate) | softer beam shafts through the windows |
| P3 | Glow: fewer levels on Medium | about -1 ms (estimate) | lamp bloom slightly tighter |

**P1 is in** (`settings.gd q_ssil`: High only; `qa_sweep_test` updated). Check: Medium captures against High (`renders/last_light/p1_sheet_ssil.png`) read the same by eye, and the stair door stays at 0.121 mean luminance. Its saving was measured as `--nossil`, which is the same code path; a fresh bench was not possible (load 39 from another project's Playwright job). P2 and P3 stay proposals: only if a later stage (E: the sea) needs the room. A clean confirmation bench (quiet Mac, three repeats per setting) belongs in Stage G.
