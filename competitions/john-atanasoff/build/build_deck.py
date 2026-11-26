#!/usr/bin/env python3
"""Събира presentation/index.html от index.template.html + build/playtime/out/deck_tokens.json + build/tests_result.json.
Стартиране: tools/py competitions/john-atanasoff/build/build_deck.py"""
import json
import hashlib
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tpl = (ROOT / "presentation/index.template.html").read_text()
tokens = json.loads((ROOT / "build/playtime/out/deck_tokens.json").read_text())
tests = json.loads((ROOT / "build/tests_result.json").read_text())
tokens["OTHER_TESTS"] = tests["slide_line"]
for k, v in tokens.items():
    tpl = tpl.replace("{{%s}}" % k, v)
assert "{{" not in tpl, [l for l in tpl.splitlines() if "{{" in l]
inputs = [ROOT / "presentation/index.template.html", ROOT / "presentation/css/deck.css",
          ROOT / "presentation/js/deck.js", ROOT / "build/playtime/out/deck_tokens.json",
          ROOT / "build/tests_result.json"]
inputs += sorted(p for p in (ROOT / "presentation/assets").rglob("*") if p.is_file())
sources = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
version = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()[:12]
tpl = tpl.replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n<meta name="deck-version" content="{version}">')
(ROOT / "presentation/VERSION.json").write_text(json.dumps({"deck_version": version, "game_build": "R7", "game_release": "v1.0.0", "sources": sources}, ensure_ascii=False, indent=2) + "\n")
(ROOT / "presentation/index.html").write_text(tpl)
print("index.html written")

# Speaker text comes from the same HTML, so the offline copy cannot drift.
class Notes(HTMLParser):
    def __init__(self):
        super().__init__(); self.active = False; self.rows = []; self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag == 'aside' and dict(attrs).get('class') == 'notes':
            self.active = True; self.parts = []
    def handle_data(self, data):
        if self.active: self.parts.append(data)
    def handle_endtag(self, tag):
        if tag == 'aside' and self.active:
            self.rows.append(''.join(self.parts).strip()); self.active = False
n = Notes(); n.feed(tpl)
text = '# Бележки за говорене — The Last Light, R7\n\nНаправление 3 „Разпределени приложения“. Клавиш N показва тези бележки върху същия екран; не го включвайте пред журито.\n\n'
text += '\n\n'.join(f'## Слайд {i}\n\n{s}' for i, s in enumerate(n.rows, 1)) + '\n'
(ROOT / 'presentation/SPEAKER_NOTES.md').write_text(text)
