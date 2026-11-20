"""List the files inside a Godot 4 .pck (release R5 checks).

  tools/py projects/games/last_light/release/pck_list.py "<path>/The Last Light.pck" [--json] [--cat=<path>]

Reads the pack header (formats 2 to 4) and its file directory; prints one path (no res:// prefix) and size per
line, then a count. --cat=<path> prints that one file's bytes instead (plain-text data such as panels.json).
The directory must not be encrypted (the export does not encrypt).
"""

import json
import struct
import sys


def read_pck(path: str) -> list[tuple[str, int, int]]:
    """[(path, size, absolute offset)]"""
    with open(path, "rb") as f:
        if f.read(4) != b"GDPC":
            raise SystemExit(f"{path}: not a Godot pck (no GDPC magic)")
        fmt, major, minor, patch = struct.unpack("<4I", f.read(16))
        flags = 0
        file_base = 0
        if fmt >= 2:
            flags, file_base = struct.unpack("<IQ", f.read(12))   # a standalone pck: file_base is absolute
        dir_offset = None
        if fmt >= 3:
            (dir_offset,) = struct.unpack("<Q", f.read(8))
        f.read(16 * 4)                                   # reserved
        if flags & 1:
            raise SystemExit("the pck directory is encrypted")
        if dir_offset is not None:
            f.seek(dir_offset)
        (count,) = struct.unpack("<I", f.read(4))
        out = []
        for _ in range(count):
            (n,) = struct.unpack("<I", f.read(4))
            name = f.read(n).rstrip(b"\0").decode("utf-8")
            offset, size = struct.unpack("<QQ", f.read(16))
            f.read(16)                                   # md5
            if fmt >= 2:
                f.read(4)                                # per-file flags
            out.append((name, size, file_base + offset))
        print(f"# pck format {fmt}, Godot {major}.{minor}.{patch}, {count} files", file=sys.stderr)
        return out


def main() -> None:
    files = read_pck(sys.argv[1])
    cat = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--cat=")), None)
    if cat is not None:
        hit = [x for x in files if x[0] == cat]
        if not hit:
            raise SystemExit(f"{cat}: not in the pck")
        with open(sys.argv[1], "rb") as f:
            f.seek(hit[0][2])
            sys.stdout.write(f.read(hit[0][1]).decode("utf-8", "replace"))
        return
    if "--json" in sys.argv:
        print(json.dumps([{"path": p, "size": s} for p, s, _ in files]))
        return
    for p, s, _ in files:
        print(f"{s:>12}  {p}")
    print(f"{len(files)} files")


if __name__ == "__main__":
    main()
