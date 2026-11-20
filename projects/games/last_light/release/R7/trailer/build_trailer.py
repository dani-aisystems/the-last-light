#!/usr/bin/env python3
"""THE LAST LIGHT release R7: build the trailer from its edit decision list (edit.json).

  build_trailer.py edit.json --out OUT_DIR [--draft]

edit.json is the single source of truth (the "timeline"):
  {"fps": 30, "size": [1920, 1080], "title": "...",
   "video": [ {"src": "...mp4|png", "in": s, "dur": s, "into": "cut" | "dissolve:D" | "dip:D",
               "fade_in": s, "fade_out": s, "note": "..."} ... ],
   "audio": [ {"src": "...", "at": s, "in": s, "dur": s, "gain_db": dB, "fade_in": s, "fade_out": s,
               "bus": "music" | "vo" | "fx"} ... ],
   "duck": {"threshold": 0.03, "ratio": 6, "attack": 80, "release": 600},
   "loudness": {"I": -16, "TP": -1.0, "LRA": 11}}
Clips sit back to back on the video track; "into" says how a clip joins the previous one ("dissolve" a
cross-dissolve, "dip" through black, both of D seconds, eating D from the shared length). Audio items are
placed at absolute timeline seconds. The music bus is ducked by the VO bus (sidechain), then everything is
mixed and loudness-normalised in two passes (EBU R128). Writes OUT_DIR/<stem>_master.mp4 (CRF 10, AAC
320k), OUT_DIR/<stem>.mp4 (CRF 18, AAC 256k), OUT_DIR/<stem>_mix.wav (the final mix, 48 kHz 24-bit) and
OUT_DIR/<stem>_timeline.json (every clip's start on the timeline).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def sh(cmd: list[str]) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-4000:])
        raise SystemExit(f"command failed ({r.returncode}): {' '.join(cmd[:6])} ...")
    return r


def build(edl_path: Path, out: Path, draft: bool) -> None:
    edl = json.loads(edl_path.read_text())
    base = edl_path.parent
    fps = edl.get("fps", 30)
    W, H = edl.get("size", [1920, 1080])
    stem = edl.get("stem", "TheLastLight_Trailer")
    out.mkdir(parents=True, exist_ok=True)

    def src(p: str) -> str:
        q = Path(os.path.expandvars(p))         # $R7 (renders/last_light/r7), $GAME (the Godot project)
        return str(q if q.is_absolute() else (base / q).resolve())

    # ---------------- video
    inputs: list[str] = []
    vf: list[str] = []
    timeline = []
    acc = None
    acc_len = 0.0
    for i, c in enumerate(edl["video"]):
        p = src(c["src"])
        if p.lower().endswith(".png"):
            inputs += ["-loop", "1", "-framerate", str(fps), "-t", f"{c['dur']:.3f}", "-i", p]
            trim = f"trim=duration={c['dur']:.3f}"
        else:
            inputs += ["-i", p]
            trim = f"trim=start={c.get('in', 0):.3f}:duration={c['dur']:.3f}"
        n = len(inputs) and (sum(1 for x in inputs if x == "-i") - 1)
        chain = [trim, "setpts=PTS-STARTPTS", f"fps={fps}",
                 f"scale={W}:{H}:force_original_aspect_ratio=decrease", f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black",
                 "setsar=1", "format=yuv420p", f"settb=1/{fps}"]
        if c.get("fade_in"):
            chain.append(f"fade=t=in:st=0:d={c['fade_in']}")
        if c.get("fade_out"):
            chain.append(f"fade=t=out:st={c['dur'] - c['fade_out']:.3f}:d={c['fade_out']}")
        vf.append(f"[{n}:v]{','.join(chain)}[v{i}]")
        into = c.get("into", "cut")
        if acc is None:
            acc, acc_len = f"v{i}", c["dur"]
            timeline.append({"i": i, "id": c.get("id", str(i)), "start": 0.0, "dur": c["dur"], "src": c["src"], "note": c.get("note", "")})
            continue
        if into == "cut":
            vf.append(f"[{acc}][v{i}]concat=n=2:v=1:a=0,settb=1/{fps}[a{i}]")
            start = acc_len
            acc_len += c["dur"]
        else:
            kind, d = into.split(":")
            d = float(d)
            tr = "fade" if kind == "dissolve" else "fadeblack"
            start = acc_len - d
            vf.append(f"[{acc}][v{i}]xfade=transition={tr}:duration={d}:offset={start:.3f},settb=1/{fps}[a{i}]")
            acc_len = start + c["dur"]
        acc = f"a{i}"
        timeline.append({"i": i, "id": c.get("id", str(i)), "start": round(start, 3), "dur": c["dur"], "src": c["src"], "note": c.get("note", "")})
    total = acc_len

    # ---------------- audio
    buses: dict[str, list[str]] = {"music": [], "vo": [], "fx": []}
    af: list[str] = []
    n_in = sum(1 for x in inputs if x == "-i")
    for j, a in enumerate(edl.get("audio", [])):
        if not Path(src(a["src"])).exists():
            print(f"WARN audio item {j} missing, skipped (draft): {a['src']}")
            continue
        inputs += ["-i", src(a["src"])]
        k = n_in
        n_in += 1
        d = a.get("dur")
        ch = [f"atrim=start={a.get('in', 0):.3f}" + (f":duration={d:.3f}" if d else ""), "asetpts=PTS-STARTPTS",
              "aresample=48000", "aformat=sample_fmts=fltp:channel_layouts=stereo"]
        if a.get("gain_db"):
            ch.append(f"volume={a['gain_db']}dB")
        if a.get("fade_in"):
            ch.append(f"afade=t=in:st=0:d={a['fade_in']}")
        if a.get("fade_out") and d:
            ch.append(f"afade=t=out:st={d - a['fade_out']:.3f}:d={a['fade_out']}")
        at = a["at"] if "clip" not in a else [t for t in timeline if t["id"] == str(a["clip"])][0]["start"] + a.get("offset", 0.0)
        a["_at"] = round(at, 3)
        ms = int(round(at * 1000))
        ch.append(f"adelay={ms}|{ms}")
        af.append(f"[{k}:a]{','.join(ch)}[s{j}]")
        buses[a.get("bus", "fx")].append(f"[s{j}]")

    def mix(labels: list[str], name: str) -> str:
        if not labels:
            af.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={total:.3f}[{name}]")
        elif len(labels) == 1:
            af.append(f"{labels[0]}apad=whole_dur={total:.3f}[{name}]")
        else:
            af.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=longest,"
                      f"apad=whole_dur={total:.3f}[{name}]")
        return name

    m = mix(buses["music"], "mus")
    v = mix(buses["vo"], "vo")
    f = mix(buses["fx"], "fx")
    dk = edl.get("duck", {"threshold": 0.03, "ratio": 6, "attack": 80, "release": 600})
    af.append(f"[{v}]asplit=2[vo1][vo2]")
    af.append(f"[{m}][vo1]sidechaincompress=threshold={dk['threshold']}:ratio={dk['ratio']}:"
              f"attack={dk['attack']}:release={dk['release']}:makeup=1[mduck]")
    if edl.get("vo_in_mix", True):
        af.append(f"[mduck][vo2][{f}]amix=inputs=3:normalize=0:duration=first,atrim=duration={total:.3f}[mixraw]")
    else:   # QA only: the VO still ducks the music, but is left out of the mix (to measure the real bed)
        af.append(f"[vo2]anullsink")
        af.append(f"[mduck][{f}]amix=inputs=2:normalize=0:duration=first,atrim=duration={total:.3f}[mixraw]")

    graph = ";".join(vf + af)
    raw_wav = out / f"{stem}_mixraw.wav"
    # pass 1: render the raw mix (to measure) and the picture
    vid_tmp = out / f"{stem}_picture.mp4"
    sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", os.environ.get("BT_LOG", "error")] + inputs +
       ["-filter_complex", graph, "-map", f"[{acc}]", "-c:v", "libx264", "-preset", "ultrafast" if draft else "slow",
        "-crf", "18" if draft else "10", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
        "-color_trc", "bt709", "-color_range", "tv", str(vid_tmp),
        "-map", "[mixraw]", "-c:a", "pcm_s24le", "-ar", "48000", str(raw_wav)])
    # loudness: two-pass loudnorm (linear where possible)
    L = edl.get("loudness", {"I": -16, "TP": -1.0, "LRA": 11})
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw_wav), "-af",
                           f"loudnorm=I={L['I']}:TP={L['TP']}:LRA={L['LRA']}:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    js = json.loads(meas[meas.rfind("{"):meas.rfind("}") + 1])
    mix_wav = out / f"{stem}_mix.wav"
    sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw_wav), "-af",
        f"loudnorm=I={L['I']}:TP={L['TP']}:LRA={L['LRA']}:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
        f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:"
        f"linear=true,aresample=48000", "-c:a", "pcm_s24le", str(mix_wav)])
    meta = ["-metadata", f"title={edl.get('title', stem)}", "-metadata", f"comment={edl.get('comment', '')}"]
    master = out / f"{stem}_master.mp4"
    deliv = out / f"{stem}.mp4"
    sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(vid_tmp), "-i", str(mix_wav),
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest",
        "-movflags", "+faststart"] + meta + [str(master)])
    sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(vid_tmp), "-i", str(mix_wav),
        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-profile:v", "high", "-crf", "18", "-preset", "slow",
        "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-color_range", "tv", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart"] + meta + [str(deliv)])
    vid_tmp.unlink()
    raw_wav.unlink()
    (out / f"{stem}_timeline.json").write_text(json.dumps({"total": round(total, 3), "loudnorm_in": js, "clips": timeline,
        "audio": [{"src": a["src"], "at": a.get("_at"), "bus": a.get("bus", "fx"), "note": a.get("note", "")} for a in edl.get("audio", [])]}, indent=1))
    print("TRAILER_RESULT " + json.dumps({"total": round(total, 3), "master": str(master), "delivery": str(deliv),
                                          "input_lufs": js["input_i"], "input_tp": js["input_tp"]}))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("edl", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--draft", action="store_true")
    a = ap.parse_args()
    build(a.edl, a.out, a.draft)


if __name__ == "__main__":
    main()
