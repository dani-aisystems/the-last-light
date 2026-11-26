#!/usr/bin/env python3
"""Package the rendered jury deck with a per-file SHA-256 manifest; no workstation files."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "presentation"
names = ["index.html", "index.template.html", "README_START.txt", "SPEAKER_NOTES.md",
         "RUN_OF_SHOW.md", "VERSION.json", "The_Last_Light_zashtita.pdf"]
files = [DECK / n for n in names]
files += sorted(p for d in ("assets", "css", "js") for p in (DECK / d).rglob("*") if p.is_file())
assert all(p.is_file() for p in files)
manifest = {"deck_version": json.loads((DECK / "VERSION.json").read_text())["deck_version"],
            "sha256": {str(p.relative_to(DECK)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(DECK / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
files.append(DECK / "MANIFEST.json")
out = ROOT / "The_Last_Light_zashtita_offline.zip"
with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in sorted(files):
        info = zipfile.ZipInfo(str(p.relative_to(DECK)), date_time=(2026, 11, 26, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        z.writestr(info, p.read_bytes())
checks = "\n".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT)}" for p in (out, DECK / "The_Last_Light_zashtita.pdf")) + "\n"
(ROOT / "SHA256SUMS_PRESENTATION.txt").write_text(checks)
print(checks)
print("ZIP bytes:", out.stat().st_size, "files:", len(files), "version:", manifest["deck_version"])
