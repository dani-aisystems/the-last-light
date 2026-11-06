"""Sync and check the character references (THE LAST LIGHT).

    tools/py projects/games/last_light/character-refs/tools/refs_check.py          # check only
    tools/py projects/games/last_light/character-refs/tools/refs_check.py --sync   # refresh CANON_INDEX §6 first

--sync rewrites the block between the DOCUMENTS:BEGIN/END markers in CANON_INDEX.md from
godot/assets/docs/docs.json, so the in-game document texts there are always exact. The check then confirms:
every PROFILE has sections A-J; every relative link resolves; every FLAG-xxx reference exists in REVIEW_FLAGS;
every docs.json text appears verbatim in CANON_INDEX; key quoted dialogue lines still match the .dlg files;
the birth-year arithmetic holds. Exit code 1 on any failure. Host Python only (no bpy).
"""

import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

REFS = Path(__file__).resolve().parents[1]
GAME = REFS.parent / "godot"
DOCS = GAME / "assets" / "docs" / "docs.json"
DLG = GAME / "data" / "story"
ORDER = ["log_1953", "log_1971", "note_046", "letter_1957", "inquiry_extract", "clipping_1954", "photo_1953",
         "photo_keepers", "coat_note", "forecast"]
PROFILES = ["callum", "morag", "rory", "elspeth", "ross", "iain", "hector"]
# (file, substring) pairs quoted in the references that must still be in the dialogue
DIALOGUE = [("ch3", 'MORAG: Mayday from Mary Ellen received at oh-one-fifty-two. And what he said was:'),
            ("ch3", 'MORAG: "No light at North Point. Repeat. No light"'),
            ("ch3", '"The light was out. Your father was not to blame."'),
            ("ch2", "twenty-six and it was my first winter"),
            ("ch1", "small square letters"), ("ch4", "sou'wester"), ("ch5", "hip broken"),
            ("ch1", "Donald's birthday"), ("ch1", "Only one of them that came home"),
            ("ch4", "Alasdair Ross. Master of the Mary Ellen.")]
AGES = [("Callum", 1930, 23, 41), ("Morag", 1927, 26, 44), ("Ross", 1907, 46, 64), ("Elspeth", 1942, 11, 29),
        ("Iain", 1904, 49, None), ("Rory", 1949, 4, 22)]


def sync(docs: dict) -> None:
    idx = REFS / "CANON_INDEX.md"
    s = idx.read_text(encoding="utf-8")
    keys = ORDER + [k for k in docs if k not in ORDER]
    block = "\n".join(f"**`{k}`**: {docs[k]['title']}\n\n```text\n{docs[k]['text']}\n```\n" for k in keys if k in docs)
    s2, n = re.subn(r"(<!-- DOCUMENTS:BEGIN[^>]*-->\n).*?(<!-- DOCUMENTS:END -->)",
                    lambda m: m.group(1) + "\n" + block + "\n" + m.group(2), s, flags=re.S)
    if n != 1:
        sys.exit("CANON_INDEX.md: DOCUMENTS markers not found")
    if s2 != s:
        idx.write_text(s2, encoding="utf-8")
        print("synced CANON_INDEX §6 from docs.json")


def check(docs: dict) -> int:
    fails = []
    flags = (REFS / "REVIEW_FLAGS.md").read_text(encoding="utf-8")
    defined = set(re.findall(r"^### (F\d\d)", flags, re.M)) | set(re.findall(r"^\| ([IGD]\d+) \|", flags, re.M))
    for p in REFS.rglob("*.md"):
        if "sources" in p.parts:
            continue
        s = p.read_text(encoding="utf-8")
        for ref in set(re.findall(r"FLAG-([FIG]\d\d)", s)):
            if ref not in defined:
                fails.append(f"{p.relative_to(REFS)}: FLAG-{ref} undefined")
        for a, b in re.findall(r"\]\(<([^>]+)>\)|\]\(([^)<\s]+)\)", s):
            link = a or b
            if link.startswith(("http", "#")):
                continue
            tgt = (p.parent / urllib.parse.unquote(link.split("#")[0])).resolve()
            if not tgt.exists():
                fails.append(f"{p.relative_to(REFS)}: broken link {link}")
    for cid in PROFILES:
        s = (REFS / cid / "PROFILE.md").read_text(encoding="utf-8")
        for sec in "ABCDEFGHIJ":
            if not re.search(rf"^## {sec}\. ", s, re.M):
                fails.append(f"{cid}: missing section {sec}")
    idx = (REFS / "CANON_INDEX.md").read_text(encoding="utf-8")
    for k, v in docs.items():
        if f"```text\n{v['text']}\n```" not in idx:
            fails.append(f"CANON_INDEX: document {k} not verbatim (run with --sync)")
    for ch, frag in DIALOGUE:
        if frag not in (DLG / f"{ch}.dlg").read_text(encoding="utf-8"):
            fails.append(f"{ch}.dlg no longer contains {frag!r}")
    for name, born, a53, a71 in AGES:
        if 1953 - born != a53 or (a71 and 1971 - born != a71):
            fails.append(f"age arithmetic {name}")
    for f in fails:
        print("FAIL", f)
    print("REFS_CHECK", "OK" if not fails else f"{len(fails)} failure(s)", f"| flags defined: {len(defined)}")
    return 1 if fails else 0


def main() -> None:
    docs = json.loads(DOCS.read_text(encoding="utf-8"))
    if "--sync" in sys.argv:
        sync(docs)
    sys.exit(check(docs))


if __name__ == "__main__":
    os.chdir(REFS)
    main()
