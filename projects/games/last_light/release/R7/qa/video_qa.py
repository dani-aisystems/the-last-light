#!/usr/bin/env python3
"""THE LAST LIGHT release R7: transcode a Movie Maker AVI and inspect a video with measurements.

  video_qa.py transcode IN.avi --master OUT_master.mp4 --delivery OUT.mp4
  video_qa.py inspect VIDEO.mp4 --out DIR [--every 2] [--sheet-cols 6]

`inspect` writes DIR/<stem>_qa.json, contact sheets (DIR/<stem>_sheet_NN.png, a frame every N s with its
timestamp), a spectrogram (DIR/<stem>_spectrum.png) and per-second loudness. Nothing here judges how a
frame looks: the sheets are for a person (or Claude, with Read) to look at.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = Path(__file__).resolve().parents[3] / "godot/assets/fonts"


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def probe(path: Path) -> dict:
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "format=duration,size,bit_rate:stream=index,codec_type,codec_name,profile,width,height,pix_fmt,"
             "r_frame_rate,avg_frame_rate,nb_frames,duration,sample_rate,channels,bit_rate",
             "-of", "json", str(path)], check=True)
    return json.loads(r.stdout)


WARM_BLACK = "0x090705"   # ending_sequence.gd WARM_BLACK Color(0.035, 0.026, 0.02)


def transcode(src: Path, master: Path, delivery: Path, ss: float = 0.0, black_until: float = 0.0) -> dict:
    """ss: start in the source (s). black_until: cover the output's first N s with the ending's own warm black
    (used where the capture harness's start-up frames show under the in-game fade)."""
    for out in (master, delivery):
        if out.exists():
            raise SystemExit(f"refusing to overwrite {out}")
    # Movie Maker's MJPEG is full range (yuvj420p): convert to TV range first, so a drawn colour lands exactly
    # (drawing before the conversion lifted the warm black from 6 to 21 levels).
    pix = [s for s in probe(src)["streams"] if s["codec_type"] == "video"][0].get("pix_fmt", "")
    chain = [f"scale=in_range={'full' if pix.startswith('yuvj') else 'tv'}:out_range=tv", "format=yuv420p"]
    if black_until > 0:
        chain.append(f"drawbox=x=0:y=0:w=iw:h=ih:color={WARM_BLACK}:t=fill:enable='lt(t,{black_until})'")
    vf = ["-vf", ",".join(chain)]
    af = ["-af", "afade=t=in:st=0:d=0.05"] if ss > 0 else []
    base = ["ffmpeg", "-hide_banner", "-loglevel", "error"] + (["-ss", f"{ss:.3f}"] if ss > 0 else []) + \
           ["-i", str(src), "-map", "0:v:0", "-map", "0:a:0"] + vf + af + \
           ["-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-color_range", "tv",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
    run(base + ["-crf", "12", "-preset", "slow", "-c:a", "aac", "-b:a", "320k",
                "-movflags", "+faststart", str(master)], check=True)
    run(base + ["-crf", "18", "-preset", "slow", "-c:a", "aac", "-b:a", "256k",
                "-movflags", "+faststart", str(delivery)], check=True)
    return {"master": probe(master), "delivery": probe(delivery)}


def _font(size: int):
    for p in [FONT / "SourceSans3/SourceSans3-VariableFont_wght.ttf", FONT / "source_sans_3/SourceSans3-VariableFont_wght.ttf"]:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    hits = list(FONT.rglob("SourceSans3*.ttf"))
    return ImageFont.truetype(str(hits[0]), size) if hits else ImageFont.load_default()


def frame_pts(path: Path) -> np.ndarray:
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time",
             "-of", "csv=p=0", str(path)], check=True)
    vals = [float(x) for x in r.stdout.split() if x.strip() and x.strip() != "N/A"]
    return np.sort(np.array(vals))


def audio_samples(path: Path, rate: int = 48000) -> np.ndarray:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0", "-ac", "2", "-ar", str(rate),
                        "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.float32).reshape(-1, 2)


def detect(path: Path, filt: str, audio: bool = False) -> str:
    kind = ["-af", filt, "-vn"] if audio else ["-vf", filt, "-an"]
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path)] + kind + ["-f", "null", "-"])
    return r.stderr


def spans(log: str, start_key: str, end_key: str) -> list[list[float]]:
    out, cur = [], None
    for line in log.splitlines():
        m = re.search(start_key + r":\s*([-\d.]+)", line)
        if m:
            cur = float(m.group(1))
        m = re.search(end_key + r":\s*([-\d.]+)", line)
        if m and cur is not None:
            out.append([round(cur, 2), round(float(m.group(1)), 2)])
            cur = None
    return out


def inspect(path: Path, out: Path, every: float, cols: int) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    stem = path.stem
    info = probe(path)
    dur = float(info["format"]["duration"])
    rep: dict = {"file": str(path), "duration": round(dur, 3), "size_mb": round(int(info["format"]["size"]) / 1e6, 2),
                 "streams": info["streams"]}
    v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
    a = [s for s in info["streams"] if s["codec_type"] == "audio"]
    rep["av_duration_diff_s"] = round(abs(float(v.get("duration", dur)) - float(a[0].get("duration", dur))), 3) if a else None

    pts = frame_pts(path)
    d = np.diff(pts)
    fps = eval(v["r_frame_rate"])
    rep["frames"] = int(len(pts))
    rep["frame_interval_ms"] = {"median": round(float(np.median(d)) * 1000, 3), "min": round(float(d.min()) * 1000, 3),
                                "max": round(float(d.max()) * 1000, 3)}
    rep["frame_pacing_irregular"] = int(np.sum(np.abs(d - 1.0 / fps) > 0.25 / fps))

    blk = detect(path, "blackdetect=d=0.4:pix_th=0.06:pic_th=0.98")
    rep["black"] = spans(blk, "black_start", "black_end")
    frz = detect(path, "freezedetect=n=0.0015:d=2")
    rep["freeze"] = spans(frz, "freeze_start", "freeze_end")
    sc = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf", "select='gt(scene,0.25)',showinfo",
              "-an", "-f", "null", "-"]).stderr
    rep["cuts"] = [round(float(m), 2) for m in re.findall(r"pts_time:([\d.]+)", sc)]

    if a:
        sil = detect(path, "silencedetect=n=-55dB:d=1.0", audio=True)
        rep["silence"] = spans(sil, "silence_start", "silence_end")
        eb = detect(path, "ebur128=peak=true", audio=True)
        summ = eb[eb.rfind("Summary:"):]
        def grab(k):
            m = re.search(k + r":\s*([-\d.]+)", summ)
            return float(m.group(1)) if m else None
        rep["loudness"] = {"integrated_lufs": grab("I"), "lra_lu": grab("LRA"), "true_peak_dbfs": grab("Peak")}
        x = audio_samples(path)
        sr = 48000
        n = len(x) // sr
        per = []
        for i in range(n):
            seg = x[i * sr:(i + 1) * sr]
            rms = float(np.sqrt(np.mean(seg ** 2)) + 1e-12)
            per.append(round(20 * math.log10(rms), 1))
        rep["rms_dbfs_per_s"] = per
        rep["sample_peak_dbfs"] = round(20 * math.log10(float(np.abs(x).max()) + 1e-12), 2)
        rep["clipped_samples"] = int(np.sum(np.abs(x) >= 0.999))
        jumps = np.abs(np.diff(x[:, 0]))
        rep["click_candidates"] = [round(float(i) / sr, 3) for i in np.where(jumps > 0.6)[0][:20]]
        run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-lavfi",
             "showspectrumpic=s=1600x500:legend=1:scale=log", str(out / f"{stem}_spectrum.png")], check=True)

    # contact sheets
    times = list(np.arange(0.5, dur, every))
    tw, th = 384, 216
    per_sheet = cols * 6
    font = _font(18)
    sheets = []
    for si in range(0, len(times), per_sheet):
        chunk = times[si:si + per_sheet]
        rows = math.ceil(len(chunk) / cols)
        sheet = Image.new("RGB", (cols * tw, rows * (th + 24)), (12, 12, 14))
        dr = ImageDraw.Draw(sheet)
        for k, t in enumerate(chunk):
            r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1",
                                "-vf", f"scale={tw}:{th}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                               capture_output=True, check=True)
            if len(r.stdout) == tw * th * 3:
                im = Image.frombytes("RGB", (tw, th), r.stdout)
                x0, y0 = (k % cols) * tw, (k // cols) * (th + 24)
                sheet.paste(im, (x0, y0))
                dr.text((x0 + 6, y0 + th + 2), f"{t:6.1f} s", fill=(230, 200, 140), font=font)
        p = out / f"{stem}_sheet_{si // per_sheet:02d}.png"
        sheet.save(p)
        sheets.append(str(p))
    rep["sheets"] = sheets
    (out / f"{stem}_qa.json").write_text(json.dumps(rep, indent=1))
    return rep


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("transcode")
    t.add_argument("src", type=Path)
    t.add_argument("--master", type=Path, required=True)
    t.add_argument("--delivery", type=Path, required=True)
    t.add_argument("--ss", type=float, default=0.0)
    t.add_argument("--black-until", type=float, default=0.0)
    i = sub.add_parser("inspect")
    i.add_argument("video", type=Path)
    i.add_argument("--out", type=Path, required=True)
    i.add_argument("--every", type=float, default=2.0)
    i.add_argument("--sheet-cols", type=int, default=6)
    a = ap.parse_args(argv)
    if a.cmd == "transcode":
        print("TRANSCODE_RESULT " + json.dumps(transcode(a.src, a.master, a.delivery, a.ss, a.black_until)))
    else:
        rep = inspect(a.video, a.out, a.every, a.sheet_cols)
        short = {k: v for k, v in rep.items() if k not in ("streams", "rms_dbfs_per_s", "sheets")}
        print("QA_RESULT " + json.dumps(short))


if __name__ == "__main__":
    sys.exit(main())
