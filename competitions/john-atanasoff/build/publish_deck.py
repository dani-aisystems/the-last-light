#!/usr/bin/env python3
"""Copy the verified jury deck to the existing GitHub Pages source, preserving its bytes."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "presentation"
DEST = ROOT.parents[1] / "docs/presentation"
manifest = json.loads((SOURCE / "MANIFEST.json").read_text())
files = {name: digest for name, digest in manifest["sha256"].items()
         if name in ("index.html", "VERSION.json", "The_Last_Light_zashtita.pdf")
         or name.startswith(("assets/", "css/", "js/"))}
for name, digest in files.items():
    source = SOURCE / name
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest, name
    target = DEST / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
(DEST / "MANIFEST.json").write_text(json.dumps({"deck_version": manifest["deck_version"], "sha256": files},
                                             ensure_ascii=False, indent=2) + "\n")
print(f"Published {len(files)} unchanged files to docs/presentation; deck {manifest['deck_version']}")
