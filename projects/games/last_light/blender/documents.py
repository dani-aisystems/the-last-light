"""Readable story documents for THE LAST LIGHT (host Python + Pillow, macOS system fonts).

  tools/py projects/games/last_light/blender/documents.py

Writes godot/assets/docs/<id>.png plus docs.json (id -> title + plain transcription for accessibility).
Hands: Callum = Bradley Hand (small square "clerk's hand"), Iain = Snell Roundhand (copperplate),
Morag = Noteworthy (pencil), official = American Typewriter / Courier New.
The 1953 log entry and the 1971 log are deliberately in the SAME hand: that is the chapter-2 clue.
"""

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "godot" / "assets" / "docs"
SUP = Path("/System/Library/Fonts/Supplemental")
SYS = Path("/System/Library/Fonts")


def F(name, size):
    for d in (SUP, SYS):
        p = d / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    raise FileNotFoundError(name)


CALLUM = lambda s: F("Bradley Hand Bold.ttf", s)
IAIN = lambda s: F("SnellRoundhand.ttc", s)
MORAG = lambda s: F("Noteworthy.ttc", s)
TYPE = lambda s: F("AmericanTypewriter.ttc", s)
PRINT = lambda s: F("Georgia.ttf", s)
PRINTB = lambda s: F("Georgia Bold.ttf", s)
INK = (34, 36, 58)
PENCIL = (70, 70, 72)
PAPER = (232, 222, 196)


def paper(w, h, seed, tone=PAPER, stains=3):
    rnd = random.Random(seed)
    img = Image.new("RGB", (w, h), tone)
    noise = Image.effect_noise((w // 4, h // 4), 18).resize((w, h), Image.BICUBIC).convert("RGB")
    img = Image.blend(img, noise, 0.06)
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(stains):
        x, y, r = rnd.randint(0, w), rnd.randint(0, h), rnd.randint(40, 160)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(150, 120, 80, 40), width=rnd.randint(2, 6))
    for _ in range(4):   # fold shadows
        if rnd.random() < 0.5:
            y = rnd.randint(h // 4, 3 * h // 4)
            d.line([0, y, w, y + rnd.randint(-6, 6)], fill=(0, 0, 0, 18), width=3)
    return img


def jitter_text(d, xy, text, font, fill, seed=0, slope=0.0):
    """Hand-written look: per-word tiny baseline/rotation jitter. Callum's hand gets the F15 glyphs."""
    rnd = random.Random(seed + len(text))
    x, y = xy
    callum = _is_callum(font)
    for word in text.split(" "):
        dy = rnd.uniform(-1.6, 1.6) + slope * x
        if callum:
            x += _callum_word(d, (x, y + dy), word, font, fill) + d.textlength(" ", font=font)
        else:
            d.text((x, y + dy), word, font=font, fill=fill)
            x += d.textlength(word + " ", font=font)


# ---- Callum's hand to the F15 specification (character-refs/REVIEW_FLAGS.md): upright with a slight
# right slant, careful capitals, an open-topped 4 (Bradley Hand's own), a straight 1, a narrow 7 and a low
# t-bar. Bradley Hand's 1 has a flag and foot, its 7 is wide and crossed, its t-bar is high, and it is
# upright: those three glyphs are drawn as pen strokes and each word is sheared 6 degrees.
CALLUM_SLANT = math.tan(math.radians(6.0))


def _is_callum(font):
    return str(getattr(font, "path", "")).endswith("Bradley Hand Bold.ttf")


def _callum_word(d, xy, word, font, fill):
    """Draw one word in Callum's hand onto d's image; returns its advance in pixels."""
    size = font.size
    sw = max(2, round(size * 0.085))                       # Bradley Hand Bold's stroke weight
    asc = font.getbbox("4")[1]                             # digit top (from the text origin)
    base = font.getbbox("4")[3]                            # baseline (digits sit on it)
    xh = font.getbbox("x")[1]                              # x-height top
    pad = int(size * 0.4)
    h = int(size * 1.6)
    w = int(font.getlength(word) + size + h * CALLUM_SLANT) + 2 * pad
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    col = tuple(fill[:3]) + ((fill[3],) if len(fill) > 3 else (255,))

    def stroke(a, b):
        ld.line([a, b], fill=col, width=sw)
        for p in (a, b):
            ld.ellipse([p[0] - sw / 2, p[1] - sw / 2, p[0] + sw / 2, p[1] + sw / 2], fill=col)
    cx = pad
    for ch in word:
        if ch == "1":                                      # a straight 1: one stroke, a hair of lean
            adv = font.getlength("1") * 0.7
            stroke((cx + adv * 0.55, asc + sw * 0.5), (cx + adv * 0.45, base - sw * 0.5))
        elif ch == "7":                                    # a narrow 7, no crossbar
            adv = font.getlength("7") * 0.72
            stroke((cx + adv * 0.08, asc + sw * 0.6), (cx + adv * 0.88, asc + sw * 0.4))
            stroke((cx + adv * 0.88, asc + sw * 0.4), (cx + adv * 0.36, base - sw * 0.5))
        elif ch == "t":                                    # the low t-bar
            adv = font.getlength("t")
            ttop = font.getbbox("t")[1]
            sx = cx + adv * 0.42
            stroke((sx, ttop + sw * 0.5), (sx, base - sw * 1.2))
            stroke((sx, base - sw * 1.2), (sx + adv * 0.35, base - sw * 0.6))
            yb = xh + (base - xh) * 0.22
            stroke((cx + adv * 0.08, yb), (cx + adv * 0.82, yb))
        else:
            ld.text((cx, 0), ch, font=font, fill=col)
            adv = font.getlength(ch)
        cx += adv
    k = CALLUM_SLANT                                       # shear: the top of the word leans right
    sheared = layer.transform(layer.size, Image.AFFINE, (1, k, -k * base, 0, 1, 0), resample=Image.BICUBIC)
    img = d._image
    x, y = int(round(xy[0])) - pad, int(round(xy[1]))
    if img.mode == "RGBA":
        img.alpha_composite(sheared, (max(0, x), max(0, y)))
    else:
        img.paste(sheared.convert("RGB"), (max(0, x), max(0, y)), sheared)
    return cx - pad


def log_page(year, rows, seed, title_month, size=27):
    W, H = 1500, 1050
    img = paper(W, H, seed)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 46), "NORTHERN LIGHTHOUSE BOARD", font=PRINTB(30), fill=(60, 50, 40), anchor="mm")
    d.text((W // 2, 86), f"NORTH POINT LIGHT  ·  STATION LOG  ·  {title_month} {year}", font=PRINT(24), fill=(60, 50, 40), anchor="mm")
    cols = [(60, "Date"), (170, "Time"), (270, "Wind"), (430, "Weather"), (620, "Remarks")]
    y0 = 130
    d.line([40, y0, W - 40, y0], fill=(120, 90, 70), width=2)
    for x, t in cols:
        d.text((x, y0 + 10), t, font=PRINTB(20), fill=(90, 70, 55))
        d.line([x - 10, y0, x - 10, H - 50], fill=(170, 130, 110), width=1)
    for k in range(18):
        y = y0 + 46 + k * 47
        d.line([40, y, W - 40, y], fill=(170, 150, 140), width=1)
    y = y0 + 52
    for r in rows:
        hand, date, time, wind, wx, remark = r
        f = hand(size)
        jitter_text(d, (60, y), date, f, INK, seed)
        jitter_text(d, (170, y), time, f, INK, seed + 1)
        jitter_text(d, (270, y), wind, f, INK, seed + 2)
        jitter_text(d, (430, y), wx, f, INK, seed + 3)
        lines = wrap(d, remark, f, W - 680)
        for i, line in enumerate(lines):
            jitter_text(d, (620, y + i * 47), line, f, INK, seed + 4 + i)
        y += 47 * max(1, len(lines))
    return img.filter(ImageFilter.GaussianBlur(0.4))


def wrap(d, text, font, width):
    out, cur = [], ""
    for w in text.split(" "):
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) > width and cur:
            out.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        out.append(cur)
    return out


def letter(lines, hand, size, seed, w=1100, h=1500, color=INK, line_h=None):
    img = paper(w, h, seed, (236, 228, 205), 4)
    d = ImageDraw.Draw(img)
    f = hand(size)
    y = 110
    lh = line_h or int(size * 1.55)
    for para in lines:
        if para == "":
            y += lh // 2
            continue
        for line in wrap(d, para, f, w - 200):
            jitter_text(d, (100, y), line, f, color, seed + y)
            y += lh
    return img.filter(ImageFilter.GaussianBlur(0.35))


def clipping():
    W, H = 1000, 1300
    img = paper(W, H, 77, (214, 205, 180), 2)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 70), "STORNOWAY GAZETTE", font=PRINTB(48), fill=(30, 30, 30), anchor="mm")
    d.text((W // 2, 120), "Thursday, 18th March 1954", font=PRINT(22), fill=(50, 50, 50), anchor="mm")
    d.line([60, 145, W - 60, 145], fill=(40, 40, 40), width=3)
    d.text((W // 2, 200), "MARY ELLEN INQUIRY:", font=PRINTB(44), fill=(20, 20, 20), anchor="mm")
    d.text((W // 2, 252), "MASTER TO BLAME", font=PRINTB(44), fill=(20, 20, 20), anchor="mm")
    body = ("The formal inquiry into the loss of the Stornoway trawler Mary Ellen (SY 214) on the East Gut rocks off "
            "North Point on the morning of 15th November last, with the loss of seven lives, concluded at Inverness "
            "yesterday. The court found that the master, Alasdair Ross of Leverburgh, who is presumed drowned, \"failed "
            "to keep a proper lookout and stood into danger despite the light being exhibited.\" Evidence from the "
            "station log of North Point Light, kept by Principal Keeper Iain Mackay, showed that the light was "
            "extinguished for approximately two minutes only, at 2.10 a.m., some twelve minutes after the vessel struck. "
            "A wireless message received at Stornoway shortly before the stranding was described by the court as "
            "\"confused and unreliable.\" The sole survivor of the crew, deckhand Kenneth Bain, was below at the time "
            "and could give no evidence as to the light.")
    y = 310
    for line in wrap(d, body, PRINT(25), W - 140):
        d.text((70, y), line, font=PRINT(25), fill=(30, 30, 30))
        y += 37
    return img.filter(ImageFilter.GaussianBlur(0.5))


def note_046():
    # Stage 3B: dated entries, and the procedure the ch2 jam teaches and ch6 needs. Iain's 1949 line is
    # era-neutral ("take the drive off": the clockwork then, MODE OFF on the electric drive now)
    W, H = 900, 640
    img = paper(W, H, 46, (238, 230, 200), 1)
    d = ImageDraw.Draw(img)
    jitter_text(d, (60, 56), "GEAR RACE - worn tooth at 046°.", IAIN(44), INK, 1)
    jitter_text(d, (60, 122), "Sticks in heavy weather.", IAIN(36), INK, 2)
    jitter_text(d, (60, 174), "FREE BY HAND: take the drive off, back her", IAIN(34), INK, 7)
    jitter_text(d, (60, 220), "past the tooth, then put the drive in again.", IAIN(34), INK, 8)
    jitter_text(d, (60, 272), "Reported to Board 4.3.49.   I.M.", IAIN(36), INK, 3)
    d.line([50, 334, W - 50, 334], fill=(150, 120, 100), width=2)
    jitter_text(d, (60, 360), "Reported again 9.12.53.  C.M.", CALLUM(36), INK, 4)
    jitter_text(d, (60, 420), "Reported again 2.2.63.  Engineer says", CALLUM(36), INK, 5)
    jitter_text(d, (60, 470), "\"next refit\".  C.M.", CALLUM(36), INK, 6)
    d.rectangle([W // 2 - 70, 0, W // 2 + 70, 30], fill=(200, 190, 150))   # tape
    return img


def inquiry_extract(photostat):
    """Stage 3B: the Inquiry's findings on the 01.52 Mayday and the log, with the photostat Ross read in
    the Mitchell Library (Appendix C: a grey copy of the real 1953 log page, same hand)."""
    W, H = 1000, 1400
    img = paper(W, H, 54, (226, 222, 208), 1)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 64), "REPORT OF FORMAL INVESTIGATION", font=PRINTB(34), fill=(30, 30, 30), anchor="mm")
    d.text((W // 2, 106), "m.f.v. MARY ELLEN (SY 214)  ·  Inverness, March 1954", font=PRINT(23), fill=(50, 50, 50), anchor="mm")
    d.text((W // 2, 140), "Extract and Appendix C", font=PRINT(21), fill=(70, 70, 70), anchor="mm")
    d.line([70, 166, W - 70, 166], fill=(60, 60, 60), width=2)
    y = 196
    for para in INQUIRY:
        for line in wrap(d, para, TYPE(23), W - 150):
            d.text((75, y), line, font=TYPE(23), fill=(35, 35, 40))
            y += 33
        y += 18
    d.text((75, y + 6), "APPENDIX C.  Photostat of the station log, North Point Light, 14-15 November 1953.",
           font=TYPE(20), fill=(35, 35, 40))
    g = photostat.convert("L").resize((W - 180, int((W - 180) * photostat.height / photostat.width)))
    g = Image.merge("RGB", [g.point(lambda v: int(v * 0.72 + 30))] * 3)          # a dull grey copy
    top = y + 48
    if top + g.height > H - 40:
        g = g.crop((0, 0, g.width, H - 40 - top))
    img.paste(g, (90, top))
    d.rectangle([88, top - 2, 92 + g.width, top + g.height + 2], outline=(90, 90, 90), width=2)
    return img.filter(ImageFilter.GaussianBlur(0.45))


INQUIRY = [
    "22. The Court has considered a wireless message logged by Stornoway Coastguard at 01.52, which was said to report "
    "that no light was visible from North Point. The message was received in conditions of severe interference. The "
    "Court finds it confused and unreliable.",
    "23. The Court prefers the evidence of the station log of North Point Light, kept by a principal keeper of long and "
    "unblemished service, which records that the light was exhibited throughout save for approximately two minutes at 02.10.",
    "24. The Court finds that the master, Alasdair Ross, failed to keep a proper lookout and stood into danger despite the "
    "light being exhibited.",
]


def forecast():
    W, H = 1000, 900
    img = paper(W, H, 9, (240, 238, 228), 0)
    d = ImageDraw.Draw(img)
    lines = ["GALE WARNING  ISSUED 1600 GMT 14 NOV 1971", "",
             "HEBRIDES MINCHES  SOUTHWESTERLY SEVERE GALE 9",
             "INCREASING STORM 10 IMMINENT  VEERING WESTERLY LATER", "",
             "MALIN  SOUTHWESTERLY GALE 8 TO SEVERE GALE 9", "",
             "SEA AREA FORECASTS  RAIN  VISIBILITY POOR", "",
             "STORNOWAY COASTGUARD  CH 16  CH 67", "",
             "-- TELEPRINTER NORTH POINT LT --"]
    y = 80
    for l in lines:
        d.text((60, y), l, font=TYPE(28), fill=(40, 40, 70))
        y += 50
    return img


RAW_KEEPERS = HERE / "tex" / "src" / "photo_keepers_raw.png"   # blender/photo_render.py (CC0 base meshes)
# Daniel 2026-11-09: the wall photograph is his print of Iain and Callum (character-refs/Picture-wall; the
# bare print of the two, chosen over the copy with a mount and caption baked in, so the canon caption below
# stays exact). It replaces the Blender render above, which is kept as the fallback.
SRC_KEEPERS = HERE.parent / "character-refs" / "Picture-wall" / "Vintage Maritime Portrait by the Sea.png"


def silver_print(raw, seed, creases=3):
    """Raw Cycles render -> 1950s silver gelatin snapshot: grey tone, soft lens, compressed and lifted
    tonal range, warm-grey toning, vignette, film grain, a few soft creases."""
    rnd = random.Random(seed)
    W, H = raw.size
    g = raw.convert("L").filter(ImageFilter.GaussianBlur(1.1))
    # S-curve, then lift the blacks / dull the whites (faded print)
    g = g.point(lambda v: int(14 + 222 * (0.5 - 0.5 * math.cos(math.pi * (v / 255.0) ** 1.05))))
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    for k in range(40):
        t = k / 40
        vd.ellipse([-W * 0.25 + t * W * 0.2, -H * 0.3 + t * H * 0.22, W * 1.25 - t * W * 0.2, H * 1.3 - t * H * 0.22],
                   fill=int(255 * t))
    vig = vig.filter(ImageFilter.GaussianBlur(60))
    g = Image.composite(g, g.point(lambda v: int(v * 0.72)), vig)
    grain = Image.effect_noise((W, H), 34).filter(ImageFilter.GaussianBlur(0.6))
    g = Image.blend(g, grain, 0.12)
    img = Image.merge("RGB", (g, g.point(lambda v: int(v * 0.965)), g.point(lambda v: int(v * 0.885))))
    d2 = ImageDraw.Draw(img, "RGBA")
    for _ in range(creases):
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        pts = [(x, y)]
        for _ in range(10):
            x += rnd.randint(10, 60)
            y += rnd.randint(-14, 14)
            pts.append((x, y))
        d2.line(pts, fill=(240, 232, 214, 70), width=1)
    return img


def note_on_hood(img):
    """The in-world copy of note_046 (the viewer's page is unchanged): a soft fold across the middle, a pin
    hole under the tape, the faint ring of a mug set down on it once. Seeded, so the build is reproducible."""
    out = img.copy().convert("RGB")
    W, H = out.size
    d = ImageDraw.Draw(out, "RGBA")
    d.line([(0, H * 0.52), (W, H * 0.49)], fill=(120, 105, 80, 46), width=3)          # the fold's shadow
    d.line([(0, H * 0.52 - 3), (W, H * 0.49 - 3)], fill=(255, 250, 235, 40), width=2)  # and its lit edge
    d.ellipse([W // 2 - 5, 34, W // 2 + 5, 44], fill=(70, 60, 45, 150))                 # pin hole below the tape
    cx, cy, r = int(W * 0.8), int(H * 0.74), 92
    for k in range(5):                                                                 # a faint tea ring
        d.ellipse([cx - r - k, cy - r - k, cx + r + k, cy + r + k], outline=(150, 110, 70, 26 - k * 4), width=3)
    return out


def photo(kind):
    W, H = 1100, 800
    rnd = random.Random(5 if kind == "keepers" else 8)
    if kind == "keepers" and (SRC_KEEPERS.exists() or RAW_KEEPERS.exists()):
        raw = Image.open(SRC_KEEPERS if SRC_KEEPERS.exists() else RAW_KEEPERS).convert("RGB")
        pw = min(W, round(H * raw.width / raw.height))   # the print at full height, never stretched: a
        # framed behind glass on the wall: no creases (one ran across Callum's face); the G4c glass smudge
        # carries the wear. A narrower print gets wider side margins.
        img = silver_print(raw.resize((pw, H), Image.LANCZOS), 5, creases=0)
        framed = Image.new("RGB", (W + 80, H + 160), (236, 229, 212))   # the mount stays 1180 x 960 (build.py)
        framed.paste(img, ((W + 80 - pw) // 2, 40))
        fd = ImageDraw.Draw(framed)
        fd.text((W // 2 + 40, H + 80), "Iain & Callum Mackay, North Point, May 1952", font=PRINT(30),
                fill=(88, 80, 70), anchor="mm")              # D8 / I09: a printed mount caption, nobody's hand
        return framed
    img = Image.new("RGB", (W, H), (120, 100, 75))
    d = ImageDraw.Draw(img)
    # sky / sea gradient in sepia
    for y in range(H):
        t = y / H
        c = int(200 - 90 * t)
        d.line([0, y, W, y], fill=(c, int(c * 0.86), int(c * 0.66)))
    if kind == "keepers":
        d.polygon([(560, 120), (640, 120), (680, 700), (520, 700)], fill=(200, 188, 160))   # tower
        d.rectangle([555, 90, 645, 125], fill=(70, 60, 50))
        d.rectangle([590, 560, 625, 700], fill=(70, 60, 50))                                   # door
        figs = [(470, 1.0), (735, 0.88)]
        caption = "Iain & Callum Mackay, North Point, May 1952"
    else:
        d.rectangle([0, 560, W, H], fill=(105, 90, 70))                                        # pier
        d.polygon([(80, 470), (1020, 470), (960, 560), (140, 560)], fill=(60, 52, 44))        # hull
        d.rectangle([620, 360, 760, 470], fill=(80, 70, 58))                                   # wheelhouse
        d.line([400, 470, 400, 180], fill=(60, 52, 44), width=8)
        figs = [(180 + i * 100, 0.62 + rnd.uniform(-0.05, 0.05)) for i in range(8)]
        caption = "Mary Ellen, Leverburgh, July 1953"
    for x, s in figs:
        # head, shoulders, coat, legs: a person, not a pillar
        hgt = (300 if kind == "keepers" else 150) * s
        base = 700 if kind == "keepers" else 470
        u = hgt / 7.0
        col = (48, 40, 33)
        d.ellipse([x - 0.55 * u, base - hgt, x + 0.55 * u, base - hgt + 1.1 * u], fill=col)                       # head
        if kind != "keepers":
            d.rectangle([x - 0.75 * u, base - hgt - 0.1 * u, x + 0.75 * u, base - hgt + 0.35 * u], fill=col)       # cap
        d.polygon([(x - 1.25 * u, base - hgt + 1.4 * u), (x + 1.25 * u, base - hgt + 1.4 * u),
                   (x + 1.05 * u, base - 2.6 * u), (x - 1.05 * u, base - 2.6 * u)], fill=col)                      # coat
        d.rectangle([x - 0.85 * u, base - 2.7 * u, x - 0.15 * u, base], fill=col)                                   # legs
        d.rectangle([x + 0.15 * u, base - 2.7 * u, x + 0.85 * u, base], fill=col)
        d.line([x + 1.2 * u, base - hgt + 1.6 * u, x + 1.6 * u, base - 3.2 * u], fill=col, width=max(2, int(0.4 * u)))
    img = img.filter(ImageFilter.GaussianBlur(2.2))
    noise = Image.effect_noise((W, H), 40).convert("RGB")
    img = Image.blend(img, noise, 0.12)
    d = ImageDraw.Draw(img)
    d2 = ImageDraw.Draw(img, "RGBA")
    for _ in range(3):   # a few soft creases
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        pts = [(x, y)]
        for _ in range(10):
            x += rnd.randint(10, 60)
            y += rnd.randint(-14, 14)
            pts.append((x, y))
        d2.line(pts, fill=(240, 230, 205, 90), width=1)
    framed = Image.new("RGB", (W + 80, H + 160), (238, 230, 210))
    framed.paste(img, (40, 40))
    fd = ImageDraw.Draw(framed)
    if kind == "keepers":
        fd.text((W // 2 + 40, H + 80), caption, font=PRINT(30), fill=(88, 80, 70), anchor="mm")   # D8 / I09
    else:
        # D8 / I08: the canon back-of-print pencilling (docs text), in two hands that are not Callum's or
        # Morag's: "Mary Ellen, July 1953. A. Ross, master." and beneath "Kenny B. on the hatch."
        fd.text((60, H + 50), "On the back, in pencil:", font=PRINT(20), fill=(130, 120, 105))
        jitter_text(fd, (60, H + 78), "Mary Ellen, July 1953.  A. Ross, master.", F("Apple Chancery.ttf", 32), PENCIL, 3)
        jitter_text(fd, (90, H + 124), "Kenny B. on the hatch.", F("Chalkboard.ttc", 24), PENCIL, 9)   # clear of "July"
    return framed


TEX = HERE / "tex"


def logbook_spread(left, right):
    """The open station log on the desk: a wide NLB ledger, two landscape pages side by side
    (2048 x 716, each page 1024 x 716 = the 1500 x 1050 log page; left page = u 0..0.5).
    Left = 13 Nov, right = 14 Nov (the readable log_1971 document). A darker gutter marks the binding."""
    W, H = 2048, 716
    out = Image.new("RGB", (W, H), PAPER)
    for k, pg in enumerate((left, right)):
        out.paste(pg.resize((W // 2, H), Image.LANCZOS), (k * W // 2, 0))
    # aged ledger stock is darker than the reading copy: at the full cream (albedo ~0.9) the desk lamp
    # blew the pages out to white (iA_after cu_logbook); x0.78 keeps the hot spot below clipping
    out = out.point(lambda v: int(v * 0.78))
    d = ImageDraw.Draw(out, "RGBA")
    for i in range(60):   # gutter shading into the binding
        a = int(110 * (1 - i / 60) ** 2)
        d.line([W // 2 - i, 0, W // 2 - i, H], fill=(60, 45, 30, a))
        d.line([W // 2 + i, 0, W // 2 + i, H], fill=(60, 45, 30, a))
    # Stage 1 iteration 5: an old tea ring in the left page's lower margin (the mug, 80 mm = ~290 px across;
    # a broken arc, darker at the rim where the tea dried)
    cx, cy, r = 190, 610, 145
    for k in range(3):
        d.arc([cx - r - k, cy - r - k, cx + r + k, cy + r + k], 200, 520, fill=(120, 80, 45, 70 - 20 * k), width=3)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(150, 110, 70, 10))
    return out


DOCS = {}


def add(doc_id, title, img, text):
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / f"{doc_id}.png", optimize=True)
    DOCS[doc_id] = {"title": title, "text": text}


# ------------------------------------------------------------------ in-world prop faces (Stage 1 iteration 4)

def calendar():
    """Northern Lighthouse Board wall calendar, November 1971, Sunday-first grid; the 14th ringed in red pencil."""
    W, H = 700, 1000
    img = paper(W, H, 1971, tone=(236, 228, 206), stains=1)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, W, 210], fill=(38, 62, 52))
    d.text((W // 2, 70), "NORTHERN LIGHTHOUSE BOARD", font=PRINTB(34), fill=(226, 214, 180), anchor="mm")
    d.text((W // 2, 140), "84 George Street, Edinburgh", font=PRINT(24), fill=(200, 190, 160), anchor="mm")
    d.text((W // 2, 280), "NOVEMBER  1971", font=PRINTB(58), fill=(30, 30, 34), anchor="mm")
    cols = ["S", "M", "T", "W", "T", "F", "S"]
    x0, y0, cw, rh = 40, 360, (W - 80) / 7, 105
    for i, c in enumerate(cols):
        d.text((x0 + cw * (i + 0.5), y0), c, font=PRINTB(30), fill=(150, 40, 30) if i == 0 else (40, 40, 44), anchor="mm")
    day, col = 1, 1               # 1 November 1971 was a Monday
    row = 0
    while day <= 30:
        cx, cy = x0 + cw * (col + 0.5), y0 + 70 + row * rh
        d.text((cx, cy), str(day), font=PRINT(40), fill=(150, 40, 30) if col == 0 else (34, 34, 38), anchor="mm")
        if day == 14:
            for k in range(3):    # red pencil ring, drawn twice like a hand would
                d.ellipse([cx - 44 + k, cy - 36 - k, cx + 46 - k, cy + 38 + k], outline=(176, 40, 32, 200), width=4)
        day += 1
        col += 1
        if col == 7:
            col, row = 0, row + 1
    for r in range(7):
        y = y0 + 25 + r * rh
        d.line([x0, y, W - x0, y], fill=(0, 0, 0, 40), width=2)
    return img


def wiring_diagram():
    """Station power-chain diagram (as the room is built): generator -> charger -> batteries -> distribution."""
    W, H = 1100, 800
    img = paper(W, H, 49, tone=(222, 226, 222), stains=2)
    d = ImageDraw.Draw(img, "RGBA")
    ink = (32, 46, 86)
    d.text((W // 2, 60), "NORTH POINT LIGHT  -  STATION ELECTRICAL SUPPLY", font=TYPE(34), fill=ink, anchor="mm")
    d.text((W // 2, 105), "Watch room.  Drg. No. NP/E/7   (revised 1962)", font=TYPE(24), fill=ink, anchor="mm")
    boxes = {"AUX. SET No.2\n(diesel)": (150, 300, 110), "CHARGER": (420, 300, 110), "BATTERY\n12 cells": (690, 300, 110),
             "DISTRIBUTION": (950, 300, 110), "LAMP": (590, 600, 95), "ROOM LIGHTS": (800, 600, 95), "RADAR / W.T.": (1000, 600, 95)}
    for name, (x, y, hw) in boxes.items():
        d.rectangle([x - hw, y - 55, x + hw, y + 55], outline=ink, width=4)
        d.multiline_text((x, y), name, font=TYPE(24), fill=ink, anchor="mm", align="center")
    for a, b in (((260, 300), (310, 300)), ((530, 300), (580, 300)), ((800, 300), (840, 300))):
        d.line([a, b], fill=ink, width=5)
        d.polygon([(b[0], b[1]), (b[0] - 18, b[1] - 10), (b[0] - 18, b[1] + 10)], fill=ink)
    d.line([(950, 355), (950, 450)], fill=ink, width=4)
    d.line([(590, 450), (1000, 450)], fill=ink, width=4)              # the three circuits off the board
    for x in (590, 800, 1000):
        d.line([(x, 450), (x, 545)], fill=ink, width=4)
    d.text((150, 420), "MAIN ENGINES\n(engine room)\nDISCONNECTED", font=TYPE(22), fill=(150, 40, 30), anchor="mm", align="center")
    d.line([(150, 355), (150, 380)], fill=(150, 40, 30), width=3)
    d.text((60, H - 60), "Initialled  C.M.  4.6.62", font=CALLUM(30), fill=INK)
    return img


def barometer_dial():
    """Aneroid barometer face in millibars (the station log reads the barometer in mb)."""
    S = 1024
    img = Image.new("RGB", (S, S), (234, 226, 204))
    d = ImageDraw.Draw(img, "RGBA")
    c, R = S / 2, S / 2 - 30
    d.ellipse([c - R, c - R, c + R, c + R], outline=(60, 50, 40), width=6)
    ink = (36, 32, 30)
    for mb in range(950, 1051, 5):            # 950..1050 mb over 270 degrees, 1000 mb at the top
        a = math.radians(-135 + (mb - 950) / 100 * 270)
        L = 60 if mb % 10 == 0 else 32
        x0, y0 = c + (R - 20) * math.sin(a), c - (R - 20) * math.cos(a)
        x1, y1 = c + (R - 20 - L) * math.sin(a), c - (R - 20 - L) * math.cos(a)
        d.line([x0, y0, x1, y1], fill=ink, width=5 if mb % 10 == 0 else 3)
        if mb % 20 == 10 or mb in (950, 1050):
            d.text((c + (R - 130) * math.sin(a), c - (R - 130) * math.cos(a)), str(mb), font=PRINT(40), fill=ink, anchor="mm")
    for word, mb in (("STORMY", 960), ("RAIN", 985), ("CHANGE", 1000), ("FAIR", 1015), ("VERY DRY", 1040)):
        a = math.radians(-135 + (mb - 950) / 100 * 270)
        d.text((c + (R - 250) * math.sin(a), c - (R - 250) * math.cos(a)), word, font=PRINTB(44), fill=ink, anchor="mm")
    d.text((c, c + 200), "MILLIBARS", font=PRINT(36), fill=ink, anchor="mm")
    d.text((c, c + 260), "NEGRETTI & ZAMBRA", font=PRINT(30), fill=(90, 80, 70), anchor="mm")
    return img


# ------------------------------------------------------------------ small-prop atlas (Stage 1 iteration 5)

def load_props_atlas():
    import importlib.util
    s = importlib.util.spec_from_file_location("ll_spec", HERE / "spec.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m.SPEC["props_atlas"]


def _chip(d, rd, cx, cy, r, seed):
    """Enamel chip: an irregular patch of dark iron with a faint rust halo (albedo d, roughness rd)."""
    rnd = random.Random(seed)
    pts = []
    for i in range(11):
        a = 2 * math.pi * i / 11
        rr = r * (0.55 + 0.6 * rnd.random())
        pts.append((cx + rr * math.cos(a) * 1.3, cy + rr * math.sin(a)))
    halo = [(cx + (x - cx) * 1.35, cy + (y - cy) * 1.35) for x, y in pts]
    d.polygon(halo, fill=(130, 84, 52, 70))
    d.polygon(pts, fill=(38, 34, 32, 255))
    rd.polygon(pts, fill=180)


def mug_wrap(w, h, mv, seed=31):
    """White enamel mug with a blue rolled rim (UK camp/works mug, Falcon-type 8 x 8 cm). Rows follow
    build.py's lathe profile: v = 0 (outer base) at the bottom row, v = 1 (inside the bottom) at the top."""
    img = Image.new("RGB", (w, h), (236, 234, 226))
    noise = Image.effect_noise((w // 2, h // 2), 10).resize((w, h), Image.BICUBIC).convert("RGB")
    img = Image.blend(img, noise, 0.03)
    rough = Image.new("L", (w, h), int(0.16 * 255))
    d = ImageDraw.Draw(img, "RGBA")
    rd = ImageDraw.Draw(rough)
    row = lambda v: h - v * h
    d.rectangle([0, row(mv["rim_v1"]), w, row(mv["rim_v0"])], fill=(30, 54, 104, 255))
    rd.rectangle([0, row(mv["rim_v1"]), w, row(mv["rim_v0"])], fill=int(0.18 * 255))
    for i in range(14):                                   # handling grime toward the base
        v = 0.12 * (1 - i / 14)
        d.line([0, row(v), w, row(v)], fill=(120, 112, 98, 4 + i), width=int(h * 0.01) + 1)
    z0, z1 = mv["inner_z"]
    it, ib = mv["inner_top"], mv["inner_bottom"]
    vz = lambda z: it + (z0 - z) / (z0 - z1) * (ib - it)  # inner-wall z -> v
    d.rectangle([0, row(1.0), w, row(ib)], fill=(110, 70, 40, 255))   # stained inside bottom
    rd.rectangle([0, row(1.0), w, row(ib)], fill=int(0.3 * 255))
    newest = mv["tide_z"][-1]
    d.rectangle([0, row(ib), w, row(vz(newest))], fill=(150, 110, 75, 170))
    for k, z in enumerate(mv["tide_z"]):                  # tide lines from earlier, fuller mugs
        y = row(vz(z))
        a = 90 if z == newest else 50 - 12 * k
        d.line([0, y, w, y], fill=(120, 80, 48, a), width=2)
        d.rectangle([0, y, w, y + 3], fill=(150, 112, 78, a // 3))
    for k, (u, v, r) in enumerate(((0.70, 0.78, 9), (0.79, 0.46, 7), (0.56, 0.05, 6), (0.33, 0.60, 4), (0.90, 0.80, 5))):
        _chip(d, rd, u * w, row(v), r, seed + k)
    return img, rough


SKED = (("STORNOWAY C.G.", 30), ("Ch 16  /  2182 kc/s", 26), ("Radio check 2100", 26), ("& as required.", 26))


def sked_card(w, h, k=1):
    """The radio-check card in the radio's bezel. k scales the writing (k=3: the readable card, audit D7)."""
    img = paper(w, h, 44, (226, 218, 196), 0)
    d = ImageDraw.Draw(img, "RGBA")
    y = 14 * k
    for line, size in SKED:
        jitter_text(d, (16 * k, y), line, CALLUM(size * k), INK, seed=y // k)
        y += (size + 14) * k
    d.rectangle([0, 0, w - 1, h - 1], outline=(150, 135, 110), width=2 * k)
    for x in range(0, w, 3):                              # thumb-grime along the bottom edge
        d.point((x, h - 4 * k - (x * 7) % (5 * k)), fill=(90, 70, 50, 60))
    return img


def tin_lid(w, h):
    """A made-up tobacco brand (no real trade dress)."""
    img = Image.new("RGB", (w, h), (118, 30, 28))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([6, 6, w - 7, h - 7], radius=18, outline=(164, 124, 54), width=5)
    d.rounded_rectangle([16, 16, w - 17, h - 17], radius=12, outline=(164, 124, 54), width=2)
    d.text((w / 2, h * 0.38), "SKERRY", font=PRINTB(44), fill=(196, 160, 84), anchor="mm")
    d.text((w / 2, h * 0.62), "FLAKE", font=PRINTB(34), fill=(196, 160, 84), anchor="mm")
    d.text((w / 2, h * 0.82), "ready rubbed  ·  1 oz", font=PRINT(16), fill=(196, 160, 84), anchor="mm")
    rnd = random.Random(8)
    for _ in range(60):                                   # worn edges show the tinplate
        x, y = rnd.choice([(rnd.randint(0, w), rnd.choice([rnd.randint(0, 10), h - rnd.randint(1, 10)])),
                           (rnd.choice([rnd.randint(0, 10), w - rnd.randint(1, 10)]), rnd.randint(0, h))])
        d.line([x, y, x + rnd.randint(-8, 8), y + rnd.randint(-3, 3)], fill=(190, 186, 176, 160), width=1)
    return img


def spines(w, h):
    """Four 60 px spines: Admiralty List of Lights, the West Coast pilot, the NLB keepers' instructions,
    and a 1971 almanac (generic titles; no publisher's trade dress)."""
    img = Image.new("RGB", (w, h), (30, 30, 30))
    books = (((30, 40, 70), "ADMIRALTY LIST OF LIGHTS  VOL. A"), ((38, 58, 44), "WEST COAST OF SCOTLAND PILOT"),
             ((104, 30, 26), "N.L.B.  INSTRUCTIONS TO LIGHTKEEPERS"), ((26, 25, 24), "NAUTICAL ALMANAC  1971"))
    for k, (col, title) in enumerate(books):
        sp = Image.new("RGB", (h, 60), col)
        sd = ImageDraw.Draw(sp, "RGBA")
        sd.text((h / 2, 30), title, font=PRINTB(19), fill=(196, 164, 92), anchor="mm")
        for x in (14, 20, h - 20, h - 14):
            sd.line([x, 6, x, 54], fill=(196, 164, 92, 200), width=2)
        noise = Image.effect_noise((h // 2, 30), 22).resize((h, 60)).convert("RGB")
        sp = Image.blend(sp, noise, 0.08)
        sd = ImageDraw.Draw(sp, "RGBA")
        for x in range(0, 12):                            # rubbed head and tail
            sd.line([x, 0, x, 60], fill=(200, 190, 170, 70 - 5 * x))
            sd.line([h - 1 - x, 0, h - 1 - x, 60], fill=(200, 190, 170, 70 - 5 * x))
        img.paste(sp.rotate(-90, expand=True), (k * 60, 0))   # English spines read top to bottom
    return img


def stores_note(w, h):
    img = paper(w, h, 46, (226, 220, 202), 1)
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(70, h, 26):                            # ruled foolscap
        d.line([0, y, w, y], fill=(120, 140, 170, 90), width=1)
    d.line([34, 0, 34, h], fill=(170, 80, 80, 90), width=1)
    lines = ["Stores - wk 46", "Gas oil  2 drums", "Bulbs 1000W  x 2", "Mantles (spare) x 6", "Paraffin  5 gal",
             "Batts - S.G. low", "  cells 7, 9", "Wick trimmer"]
    y = 44
    for i, line in enumerate(lines):
        jitter_text(d, (42, y), line, CALLUM(24), PENCIL if i else INK, seed=i)
        y += 26 * (2 if i == 0 else 1) - (0 if i else 0)
    return img


def page_edge(w, h):
    img = Image.new("RGB", (w, h), (222, 210, 182))
    d = ImageDraw.Draw(img, "RGBA")
    rnd = random.Random(12)
    for y in range(h):
        if rnd.random() < 0.45:
            d.line([0, y, w, y], fill=(150, 135, 105, rnd.randint(30, 90)))
    for x in range(0, w, 7):                              # thumbed fore-edge
        d.line([x, 0, x + 2, h], fill=(120, 100, 70, rnd.randint(0, 25)))
    return img


def knit(w, h):
    """Navy wool gansey: knit-two-purl-two ribs (R5: the old texture was a flat stripe pattern). Each stitch is a
    little V with a lit upper edge and a shadowed lower edge, the purl columns sit deeper and darker, the wool
    carries a faint fuzz and a darned patch near one edge (canon: cuffs repaired)."""
    rnd = random.Random(31)
    img = Image.new("RGB", (w, h), (50, 60, 88))       # iteration 5: (30, 36, 54) read as black under one lamp
    d = ImageDraw.Draw(img, "RGBA")
    col_w, row_h = 10, 8
    for cx in range(0, w + col_w, col_w):
        purl = (cx // col_w) % 4 in (2, 3)
        if purl:
            d.rectangle([cx, 0, cx + col_w - 1, h], fill=(36, 44, 66, 200))
            continue
        for y in range(0, h, row_h):
            j = rnd.randint(-1, 1)
            d.line([cx, y + j, cx + 5, y + 7 + j], fill=(92, 104, 138, 220), width=2)       # lit upper strand
            d.line([cx + 10, y + j, cx + 5, y + 7 + j], fill=(78, 90, 122, 220), width=2)
            d.line([cx + 1, y + 2 + j, cx + 5, y + 8 + j], fill=(30, 36, 54, 120), width=1)  # its shadow
    for _ in range(int(w * h / 90)):                    # fuzz
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        d.line([x, y, x + rnd.uniform(-3, 3), y + rnd.uniform(-3, 3)], fill=(120, 130, 160, rnd.randint(15, 45)))
    px0, py0 = int(w * 0.08), int(h * 0.82)             # a darn in slightly bluer, newer wool
    for y in range(py0, min(h, py0 + 40), 3):
        d.line([px0, y, px0 + 46, y + rnd.randint(-1, 1)], fill=(62, 76, 116, 200), width=2)
    noise = Image.effect_noise((w, h), 30).convert("RGB")
    return Image.blend(img, noise, 0.05)


TIDE_YEARS = ("1969", "1970", "1971", "1953")


def tide_spines(w, h):
    """R5: volumes of the Admiralty Tide Tables (1969, 1970, 1971), dark blue buckram, gilt titles, the
    oldest the most rubbed. Generic lettering, no crest (no publisher's trade dress).
    Audit canon 7.5 (2026-11-16): a fourth, the 1953 volume the dialogue names, at the end of the row:
    sun-faded cloth, the gilt nearly gone (nobody has opened it in eighteen years)."""
    img = Image.new("RGB", (w, h), (24, 30, 52))
    n = len(TIDE_YEARS)
    sw = w // n
    for k, year in enumerate(TIDE_YEARS):
        rnd = random.Random(70 + k)
        wear = 1.6 if year == "1953" else (2 - k) / 2.0    # 1969 most handled of the three; 1953 faded and dusty
        col = (26 + int(10 * wear), 36 + int(8 * wear), 66 - int(6 * wear))
        if year == "1953":
            col = (58, 62, 74)                             # the blue gone grey on the sunny end of the shelf
        sp = Image.new("RGB", (h, sw), col)
        sd = ImageDraw.Draw(sp, "RGBA")
        gilt = (190, 160, 92, 235 - int(70 * wear))
        sd.text((h * 0.38, sw * 0.33), "ADMIRALTY", font=PRINTB(14), fill=gilt, anchor="mm")
        sd.text((h * 0.38, sw * 0.68), "TIDE TABLES", font=PRINTB(14), fill=gilt, anchor="mm")
        sd.text((h * 0.78, sw / 2), year, font=PRINTB(16), fill=gilt, anchor="mm")
        sd.text((h * 0.11, sw / 2), "VOL. I", font=PRINT(12), fill=gilt, anchor="mm")
        for x in (int(h * 0.04), int(h * 0.05), int(h * 0.95), int(h * 0.96)):      # gilt rules at head and tail
            sd.line([x, 5, x, sw - 5], fill=gilt, width=1)
        weave = Image.effect_noise((h // 2, sw // 2), 30).resize((h, sw)).convert("RGB")
        sp = Image.blend(sp, weave, 0.07)
        sd = ImageDraw.Draw(sp, "RGBA")
        for x in range(0, 14):                             # rubbed head and tail, frayed corners
            a = int((80 - 5 * x) * (0.5 + wear))
            sd.line([x, 0, x, sw], fill=(150, 150, 160, max(a, 0)))
            sd.line([h - 1 - x, 0, h - 1 - x, sw], fill=(150, 150, 160, max(a, 0)))
        for _ in range(int(40 + 80 * wear)):               # thumb grime where the spine is pulled from the shelf
            x = rnd.gauss(h * 0.5, h * 0.18)
            y = rnd.uniform(0, sw)
            sd.ellipse([x - 2, y - 1, x + 2, y + 1], fill=(10, 10, 14, rnd.randint(10, 35)))
        img.paste(sp.rotate(-90, expand=True), (k * sw, 0))
    return img


def tide_rows_1953():
    """Audit D6: Stornoway, November 1953, high and low waters (GMT, feet). The FIGURES ARE INVENTED for
    the game (not taken from any real table): a plain semi-diurnal sequence, each tide about 50 minutes
    later than the day before, springs about the 7th and 21st, a 15 ft spring range and 8 ft neaps."""
    days = {d: [] for d in range(1, 31)}
    t = 4 * 60 + 12.0                                    # minutes from 1 Nov 00:00: first high water 04:12
    high = True
    while t < 30 * 1440:
        day = int(t // 1440) + 1
        spring = 0.5 + 0.5 * math.cos((t / 1440.0 + 1 - 7) * 2 * math.pi / 14.0)   # 1 at springs, 0 at neaps
        ht = 11.4 + 4.0 * spring if high else 2.6 - 1.9 * spring
        m = int(round(t)) % 1440
        days[day].append(("%02d%02d" % (m // 60, m % 60), "%.1f" % ht))
        t += 372.5                                       # high to low: 6 h 12.5 min (12 h 25 min a cycle)
        high = not high
    return [(d, days[d]) for d in range(1, 31)]


def tide_page_1953():
    """Audit D6 (2026-11-16): the 1953 Admiralty Tide Tables open at Stornoway, November. Printed, foxed,
    nobody's pencil on it."""
    W, H = 1100, 1500
    img = paper(W, H, 53, (226, 218, 194), 2)
    d = ImageDraw.Draw(img, "RGBA")
    ink = (40, 38, 44)
    d.text((W / 2, 70), "STORNOWAY", font=PRINTB(44), fill=ink, anchor="mm")
    d.text((W / 2, 122), "LAT. 58° 12′ N.   LONG. 6° 23′ W.", font=PRINT(22), fill=ink, anchor="mm")
    d.text((W / 2, 160), "TIMES AND HEIGHTS OF HIGH AND LOW WATERS", font=PRINT(22), fill=ink, anchor="mm")
    d.text((W / 2, 196), "TIME ZONE  G.M.T.        HEIGHTS IN FEET", font=PRINT(19), fill=ink, anchor="mm")
    d.text((W / 2, 250), "NOVEMBER  1953", font=PRINTB(30), fill=ink, anchor="mm")
    d.line([60, 280, W - 60, 280], fill=ink, width=2)
    days = ("SU", "MO", "TU", "WE", "TH", "FR", "SA")    # 1 Nov 1953 was a Sunday
    rows = tide_rows_1953()
    col_x = (70, 590)
    y0 = 300
    lh = 74
    for i, (day, tides) in enumerate(rows):
        c = 0 if i < 15 else 1
        y = y0 + (i % 15) * lh
        x = col_x[c]
        d.text((x, y + 6), "%2d" % day, font=PRINTB(26), fill=ink)
        d.text((x + 42, y + 12), days[(day - 1) % 7], font=PRINT(16), fill=ink)
        for k, (tm, ht) in enumerate(tides):
            yy = y + (k // 2) * 34
            xx = x + 90 + (k % 2) * 210
            d.text((xx, yy), tm, font=PRINT(24), fill=ink)
            d.text((xx + 80, yy), ht, font=PRINT(24), fill=ink)
        d.line([x, y + lh - 6, x + 440, y + lh - 6], fill=(40, 38, 44, 60), width=1)
    d.line([W / 2, 290, W / 2, y0 + 15 * lh], fill=(40, 38, 44, 120), width=1)
    d.text((W / 2, H - 34), "— 112 —", font=PRINT(20), fill=ink, anchor="mm")
    rnd = random.Random(1953)
    for _ in range(90):                                  # foxing
        x, y, r = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(1.5, 5)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(150, 110, 60, rnd.randint(25, 70)))
    for y in range(H - 40, H):                           # the damp tide-mark the cover shows, through to the page
        d.line([0, y, W, y], fill=(120, 110, 90, 22))
    return img


def tide_text_1953():
    lines = ["ADMIRALTY TIDE TABLES 1953. STORNOWAY. Times and heights of high and low waters, November 1953 (G.M.T., feet)."]
    for day, tides in tide_rows_1953():
        if day in (14, 15):
            lines.append("%d Nov: " % day + ",  ".join("%s  %s ft" % t for t in tides))
    return "\n".join(lines)


def tide_cover(w, h):
    """R5: the front board of the 1969 volume (the one that shows on the shelf end): blind-blocked title,
    a damp tide-mark along the foot, rubbed corners."""
    rnd = random.Random(73)
    img = Image.new("RGB", (w, h), (30, 40, 68))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([6, 6, w - 7, h - 7], outline=(18, 24, 42, 200), width=2)       # blind-stamped border
    d.text((w / 2, h * 0.3), "ADMIRALTY", font=PRINTB(13), fill=(16, 22, 38, 210), anchor="mm")
    d.text((w / 2, h * 0.42), "TIDE TABLES", font=PRINTB(13), fill=(16, 22, 38, 210), anchor="mm")
    d.text((w / 2, h * 0.56), "1969", font=PRINTB(12), fill=(16, 22, 38, 190), anchor="mm")
    weave = Image.effect_noise((w // 2, h // 2), 32).resize((w, h)).convert("RGB")
    img = Image.blend(img, weave, 0.07)
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(int(h * 0.86), h):                       # a tide-mark of old damp along the foot
        d.line([0, y, w, y + rnd.randint(-2, 2)], fill=(120, 120, 110, 30))
    for cx, cy in ((0, 0), (w, 0), (0, h), (w, h)):        # rubbed board corners show the grey millboard
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(110, 108, 104, 150))
    return img


def bulb_carton(w, h):
    """R5: the spare-lamp carton beside the old logs: buff board, a printed panel (generic maker, no brand),
    the rating, a pencilled count, scuffed corners and a creased flap."""
    rnd = random.Random(74)
    img = Image.new("RGB", (w, h), (196, 170, 120))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([10, 12, w - 11, h - 13], outline=(120, 40, 30, 230), width=3)
    d.text((w / 2, h * 0.3), "LAMPS  ·  SPARE", font=PRINTB(18), fill=(120, 40, 30), anchor="mm")
    d.text((w / 2, h * 0.52), "1000 W  ·  240 V", font=PRINTB(16), fill=(40, 34, 30), anchor="mm")
    d.text((w / 2, h * 0.7), "HANDLE WITH CARE", font=PRINT(12), fill=(40, 34, 30), anchor="mm")
    jitter_text(d, (w * 0.66, h * 0.8), "x2", CALLUM(18), PENCIL, seed=5)
    board = Image.effect_noise((w // 2, h // 2), 26).resize((w, h)).convert("RGB")
    img = Image.blend(img, board, 0.09)
    d = ImageDraw.Draw(img, "RGBA")
    for cx, cy in ((0, 0), (w, 0), (0, h), (w, h)):
        d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=(120, 100, 70, 120))
    d.line([0, 6, w, 4], fill=(90, 70, 40, 120), width=2)     # the flap's crease
    for _ in range(30):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        d.line([x, y, x + rnd.uniform(-10, 10), y + rnd.uniform(-2, 2)], fill=(80, 60, 40, 40))
    return img


def compass_card(w, h):
    """R5: the hand compass's card, cream with black and red printing (it used the floor rose, dark: the dark
    needle disappeared on it). 32 points, the north point red, degrees round the rim."""
    s = 4                                                     # draw large, then downsample (clean small print)
    W = w * s
    img = Image.new("RGB", (W, W), (232, 222, 196))
    d = ImageDraw.Draw(img)
    c = W / 2
    R_ = W / 2 - 2 * s
    d.ellipse([c - R_, c - R_, c + R_, c + R_], outline=(30, 28, 26), width=2 * s)
    for k in range(72):                                       # 5-degree ticks, longer every 10 and 30
        a = math.radians(k * 5)
        L = R_ * (0.16 if k % 6 == 0 else (0.1 if k % 2 == 0 else 0.06))
        x0, y0 = c + math.sin(a) * R_, c - math.cos(a) * R_
        x1, y1 = c + math.sin(a) * (R_ - L), c - math.cos(a) * (R_ - L)
        d.line([x0, y0, x1, y1], fill=(30, 28, 26), width=max(1, s if k % 2 == 0 else s // 2))
    for k in range(32):                                       # the rose: long cardinals, shorter intercardinals
        a = math.radians(k * 11.25)
        L = R_ * (0.74 if k % 8 == 0 else (0.56 if k % 4 == 0 else (0.42 if k % 2 == 0 else 0.32)))
        wdt = R_ * (0.07 if k % 8 == 0 else 0.045)
        tip = (c + math.sin(a) * L, c - math.cos(a) * L)
        l_ = (c + math.sin(a - math.pi / 2) * wdt, c - math.cos(a - math.pi / 2) * wdt)
        r_ = (c + math.sin(a + math.pi / 2) * wdt, c - math.cos(a + math.pi / 2) * wdt)
        fill = (168, 34, 28) if k == 0 else (30, 28, 26)
        d.polygon([tip, l_, (c, c)], fill=fill)
        d.polygon([tip, r_, (c, c)], fill=(232, 222, 196) if k != 0 else (200, 60, 50), outline=fill)
    for txt, a in (("N", 0), ("E", 90), ("S", 180), ("W", 270)):
        x, y = c + math.sin(math.radians(a)) * R_ * 0.83, c - math.cos(math.radians(a)) * R_ * 0.83
        d.text((x, y), txt, font=PRINTB(int(R_ * 0.13)), fill=(168, 34, 28) if txt == "N" else (30, 28, 26), anchor="mm")
    img = img.resize((w, h), Image.LANCZOS)
    return img


def props_extras(props, pa):
    """Paint the iteration-5 regions into the props atlas and return its roughness map (same layout)."""
    rg = pa["regions"]
    rough = Image.new("L", props.size, int(0.8 * 255))
    rdr = ImageDraw.Draw(rough)
    for name, r in (("calendar", 0.85), ("diagram", 0.85), ("barometer", 0.45), ("forecast", 0.85), ("sked", 0.82),
                    ("tin", 0.32), ("spines", 0.75), ("note", 0.86), ("page_edge", 0.9), ("knit", 1.0),
                    ("ext_label", 0.55), ("note_fold", 0.88), ("tin_band", 0.3),
                    ("tide_spines", 0.82), ("bulb_carton", 0.9), ("tide_cover", 0.84), ("compass_card", 0.7)):
        rdr.rectangle(rg[name], fill=int(r * 255))
    box = lambda n: rg[n]
    size = lambda n: (rg[n][2] - rg[n][0], rg[n][3] - rg[n][1])
    mug, mug_r = mug_wrap(*size("mug"), pa["mug_v"])
    props.paste(mug, box("mug")[:2])
    rough.paste(mug_r, box("mug")[:2])
    props.paste(forecast().resize(size("forecast"), Image.LANCZOS), box("forecast")[:2])
    props.paste(sked_card(*size("sked")), box("sked")[:2])
    props.paste(tin_lid(*size("tin")), box("tin")[:2])
    props.paste(spines(*size("spines")), box("spines")[:2])
    props.paste(stores_note(*size("note")), box("note")[:2])
    props.paste(page_edge(*size("page_edge")), box("page_edge")[:2])
    props.paste(knit(*size("knit")), box("knit")[:2])
    props.paste(ext_label(*size("ext_label")), box("ext_label")[:2])
    props.paste(note_fold(*size("note_fold")), box("note_fold")[:2])
    props.paste(tin_band(*size("tin_band")), box("tin_band")[:2])
    props.paste(tide_spines(*size("tide_spines")), box("tide_spines")[:2])        # R5
    props.paste(bulb_carton(*size("bulb_carton")), box("bulb_carton")[:2])
    props.paste(tide_cover(*size("tide_cover")), box("tide_cover")[:2])
    props.paste(compass_card(*size("compass_card")), box("compass_card")[:2])
    sw = pa["swatch"]
    for i, (name, (rgb, r)) in enumerate(pa["swatches"].items()):
        x = sw["x0"] + (i % sw["cols"]) * sw["px"]
        y = sw["y0"] + (i // sw["cols"]) * sw["px"]
        ImageDraw.Draw(props).rectangle([x, y, x + sw["px"] - 1, y + sw["px"] - 1], fill=tuple(rgb))
        rdr.rectangle([x, y, x + sw["px"] - 1, y + sw["px"] - 1], fill=int(r * 255))
    return rough


# ------------------------------------------------------------------ cabin pass (2026-11-05)

def ext_label(w, h):
    """Extinguisher wrap label: cream enamel band, red border, period lettering and instructions."""
    img = Image.new("RGB", (w, h), (226, 214, 184))
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, w - 5, h - 5], outline=(140, 30, 24), width=6)
    d.text((w // 2, 34), "FIRE", font=F("Georgia Bold.ttf", 46), fill=(140, 30, 24), anchor="mm")
    d.text((w // 2, 76), "EXTINGUISHER", font=F("Georgia Bold.ttf", 26), fill=(40, 30, 24), anchor="mm")
    d.text((w // 2, 108), "WATER  (SODA-ACID)  2 GALL.", font=F("Georgia.ttf", 17), fill=(40, 30, 24), anchor="mm")
    d.line([30, 128, w - 30, 128], fill=(140, 30, 24), width=2)
    for i, line in enumerate(("1. PULL OUT SAFETY PIN", "2. DIRECT AT BASE OF FIRE", "3. SQUEEZE LEVER",
                              "NOT FOR USE ON ELECTRICAL FIRES")):
        d.text((w // 2, 148 + i * 22), line, font=F("Georgia.ttf", 15), fill=(40, 30, 24) if i < 3 else (140, 30, 24), anchor="mm")
    noise = Image.effect_noise((w // 2, h // 2), 14).resize((w, h), Image.BICUBIC).convert("RGB")
    return Image.blend(img, noise, 0.06)                   # a little enamel grime


def note_fold(w, h):
    """The folded stores note seen in the pocket: a slip of cream paper with a few pencil lines showing."""
    img = paper(w, h, 77, (230, 222, 196), 1)
    d = ImageDraw.Draw(img)
    for i, line in enumerate(("Stores - relief", "paraffin x2", "No.8 cells", "tea, milk")):
        jitter_text(d, (12, 14 + i * 40), line, CALLUM(24), (90, 90, 96), i)
    d.line([w * 0.52, 0, w * 0.52, h], fill=(200, 190, 165), width=2)       # the fold
    return img


def tin_band(w, h):
    """Shortbread tin band: a red tartan (one third of the way round; build.py repeats it 3x)."""
    img = Image.new("RGB", (w, h), (130, 24, 26))
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, w, 32):
        d.rectangle([x, 0, x + 10, h], fill=(20, 50, 34, 150))
        d.rectangle([x + 18, 0, x + 20, h], fill=(220, 190, 90, 170))
    for y in range(0, h, 32):
        d.rectangle([0, y, w, y + 10], fill=(20, 50, 34, 130))
        d.rectangle([0, y + 18, w, y + 20], fill=(220, 190, 90, 150))
    d.rectangle([0, 0, w, 10], fill=(180, 140, 60, 255))
    d.rectangle([0, h - 10, w, h], fill=(180, 140, 60, 255))
    return img


COAT_NOTE = ["Stores for the relief boat,", "Thurs. if the sea allows", "",
             "- paraffin for the stove (2 drums)", "- No. 8 cells for the torch, a dozen",
             "- tea, condensed milk, Skerry Flake", "- glass for the west window, 2nd pane",
             "   (cracked in the Sept. gale)", "", "Tell Stornoway the No. 2 set still",
             "smokes on starting.", "", "C.M."]


def coat_note():
    """The note in the oilskin pocket (text approved by Daniel, 2026-11-05): a pencilled stores list in
    Callum's hand on a notebook leaf, folded twice."""
    W, H = 900, 1180
    img = paper(W, H, 78, (232, 225, 200), 2)
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(150, H - 60, 70):                       # notebook rules
        d.line([40, y, W - 40, y], fill=(150, 170, 190, 90), width=2)
    for fx in (W // 2,):
        d.line([fx, 0, fx, H], fill=(190, 178, 150, 120), width=3)    # the folds
    d.line([0, H // 2, W, H // 2], fill=(190, 178, 150, 120), width=3)
    y = 110
    for i, line in enumerate(COAT_NOTE):
        if line:
            jitter_text(d, (70, y), line, CALLUM(40), (70, 70, 80), 80 + i, slope=-0.004)
        y += 70
    return img


def props_atlas():
    """The props atlas alone (T_LL_Props + its roughness map). R5: `documents.py --props` rebuilds just this,
    so a prop change doesn't regrain every document PNG (their paper grain is unseeded)."""
    props = Image.new("RGB", (2048, 2048), (230, 226, 214))
    props.paste(calendar(), (0, 0))
    props.paste(wiring_diagram(), (720, 0))
    props.paste(barometer_dial(), (0, 1024))
    rough = props_extras(props, load_props_atlas())       # Stage 1 iteration 5: small-prop regions + swatches
    TEX.mkdir(exist_ok=True)
    props.save(TEX / "T_LL_Props.png", optimize=True)
    rough.save(TEX / "T_LL_Props_rough.png", optimize=True)


def extra_docs():
    """Audit D7 (2026-11-16): the room's notices as readable documents, drawn by the same code that paints
    them into the atlases (one source): KEEPER'S ORDERS (textures.notice at 2x), the supply diagram and the
    radio-check card (3x)."""
    import textures
    add("orders", "Keeper's Orders", textures.notice(12, 2),
        "KEEPER'S ORDERS\n" + "\n".join(textures.ORDERS).replace("\n    ", " "))
    add("diagram", "Station electrical supply (Drg. NP/E/7)", wiring_diagram(),
        "NORTH POINT LIGHT - STATION ELECTRICAL SUPPLY. Watch room. Drg. No. NP/E/7 (revised 1962).\n"
        "AUX. SET No.2 (diesel) -> CHARGER -> BATTERY, 12 cells -> DISTRIBUTION.\n"
        "From the distribution board: LAMP, ROOM LIGHTS, RADAR / W.T.\n"
        "MAIN ENGINES (engine room): DISCONNECTED.\nInitialled C.M. 4.6.62")
    sw, sh = PA_SIZE("sked")
    add("radio_card", "Card in the radio's bezel", sked_card(sw * 3, sh * 3, 3), "\n".join(t for t, _s in SKED))
    # audit D6: the 1953 volume, open at Stornoway, November (invented figures; see tide_rows_1953)
    add("tide_tables", "Admiralty Tide Tables, 1953", tide_page_1953(), tide_text_1953())


def PA_SIZE(name):
    x0, y0, x1, y1 = load_props_spec()["regions"][name]
    return x1 - x0, y1 - y0


def load_props_spec():
    import importlib.util
    s = importlib.util.spec_from_file_location("ll_spec", HERE / "spec.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m.SPEC["props_atlas"]


def main():
    import sys
    if "--props" in sys.argv:
        props_atlas()
        print("DOCS_RESULT props_only")
        return
    extra = [a for a in sys.argv if a == "--extra" or a.startswith("--extra=")]
    if extra:                            # audit D7: only the notice documents, merged into the existing docs.json
        only = extra[0].split("=", 1)[1].split(",") if "=" in extra[0] else None   # --extra=tide_tables: just that one
        old = json.loads((OUT / "docs.json").read_text())
        DOCS.update(old)
        new = {}
        global add
        keep_add = add
        def add(doc_id, title, img, text):   # noqa: E306 (collect, then write only the ids asked for)
            new[doc_id] = (title, img, text)
        extra_docs()
        add = keep_add
        for doc_id, (title, img, text) in new.items():
            if only is None or doc_id in only:
                add(doc_id, title, img, text)
        (OUT / "docs.json").write_text(json.dumps(DOCS, indent=1))
        print("DOCS_RESULT extra", json.dumps([k for k in new if only is None or k in only]))
        return
    C = CALLUM
    rows71 = [
        # brief 2026-11-06 (D8-a, Daniel): the evening starts with flat cells; the light comes after the engine
        (C, "14.11", "16.22", "SW 6", "Overcast, rain", "Batteries flat. Engine started, on charge."),
        (C, "", "16.40", "SW 6", "Rain", "Light exhibited. Lamp normal."),
        (C, "", "18.30", "SW 7", "Heavy rain", "Radio check Stornoway CG. Gale warning, severe gale 9."),
        (C, "", "18.50", "SW 7", "Heavy rain", "Kittiwake (SY 37) brought in by North Sound on radio bearings."),
        (C, "", "23.25", "SW 7", "Heavy rain", "Stornoway CG on Ch. 16. All well."),
    ]
    # Stage 3B (C10): the entries follow tonight's order (radio check 18.30, Kittiwake 18.50, Morag 23.25)
    add("log_1971", "Station log, Sunday 14 November 1971", log_page(1971, rows71, 71, "NOVEMBER", 26),
        "14.11.71 Sun. 16.22 SW 6, overcast, rain. Batteries flat. Engine started, on charge. / 16.40 Light exhibited. Lamp normal. / "
        "18.30 Radio check Stornoway CG. Gale warning, severe gale 9. / 18.50 Kittiwake (SY 37) brought in by North Sound "
        "on radio bearings. / 23.25 Stornoway CG on Ch. 16. All well.  (Hand: C. Mackay)")
    rows53 = [
        (C, "14.11", "23.30", "SW 8", "Heavy rain", "I. Mackay on watch. Light good."),
        (C, "15.11", "01.30", "SW 9", "Rain, poor vis.", "Trawler observed standing in too close to East Gut. No response to light."),
        (C, "", "02.10", "SW 9", "Rain", "Light extinguished approx. 2 min (mantle failure). Relit 02.12."),
        (C, "", "02.30", "SW 9", "Rain", "Wreckage reported East Gut by Stornoway W/T. Mary Ellen (SY 214) believed lost."),
        (C, "", "", "", "", "Signed I. Mackay, P.K."),     # D8 / I02: Callum wrote the signature too
    ]
    page53 = log_page(1953, rows53, 53, "NOVEMBER", 29)   # F15: the 1953 hand a little larger than 1971's
    add("log_1953", "Station log, 14-15 November 1953", page53,
        "14.11 23.30: I. Mackay on watch. Light good. / 15.11 01.30: Trawler observed standing in too close to East Gut. No response to light. / "
        "02.10: Light extinguished approx. 2 min (mantle failure). Relit 02.12. / 02.30: Wreckage reported East Gut by Stornoway W/T. "
        "Mary Ellen (SY 214) believed lost. / Signed I. Mackay, P.K.  (The entries are in the same small square hand as tonight's log.)")
    letter_text = ["Christmas 1957", "", "Callum,", "",
                   "I made you write it. I made a boy of twenty-three put his hand to my lie, because I was asleep in this chair with the bottle, and the clockwork stuck on the bad tooth, and the light was out, and I could not face it.",
                   "",
                   "The girl at Stornoway had it right. Ten minutes to two. I heard the wireless in my sleep and thought I was dreaming.",
                   "",
                   "Ross was a better man than me, and he was my friend. If you ever have the courage I did not, put it right.",
                   "", "Your father,", "Iain Mackay"]
    add("letter_1957", "Unsent letter, Christmas 1957", letter(letter_text, IAIN, 42, 57), "\n".join(letter_text))
    n46 = note_046()
    note_on_hood(n46).save(TEX / "T_LL_Note046.png", optimize=True)    # G4a (item 11): the note on the console
    add("note_046", "Maintenance note, light console", n46,
        "GEAR RACE - worn tooth at 046°. Sticks in heavy weather. FREE BY HAND: take the drive off, back her past the tooth, "
        "then put the drive in again. Reported to Board 4.3.49. I.M. / Reported again 9.12.53. C.M. / "
        "Reported again 2.2.63. Engineer says \"next refit\". C.M.")
    add("inquiry_extract", "Report of Formal Investigation, Mary Ellen (SY 214): extract", inquiry_extract(page53),
        " ".join(INQUIRY) + " APPENDIX C. Photostat of the station log, North Point Light, 14-15 November 1953. "
        "(The page shown is in a small square hand.)")
    add("clipping_1954", "Stornoway Gazette, 18 March 1954", clipping(),
        "MARY ELLEN INQUIRY: MASTER TO BLAME. ... the master, Alasdair Ross of Leverburgh, who is presumed drowned, \"failed to keep a "
        "proper lookout and stood into danger despite the light being exhibited.\" Evidence from the station log of North Point Light "
        "... showed that the light was extinguished for approximately two minutes only, at 2.10 a.m. ... A wireless message received at "
        "Stornoway shortly before the stranding was described by the court as \"confused and unreliable.\" The sole survivor of the crew, "
        "deckhand Kenneth Bain, was below at the time ...")
    add("forecast", "Teleprinter, 1600 GMT", forecast(),
        "GALE WARNING ISSUED 1600 GMT 14 NOV 1971. HEBRIDES MINCHES SOUTHWESTERLY SEVERE GALE 9 INCREASING STORM 10 IMMINENT.")
    keepers = photo("keepers")
    add("photo_keepers", "Photograph on the wall", keepers, "Iain & Callum Mackay, North Point, May 1952.")
    # in-world textures (build.py TEXTURED): the framed print on the wall and the open logbook on the desk
    TEX.mkdir(exist_ok=True)
    keepers.save(TEX / "T_LL_Photo.png", optimize=True)
    rows13 = [   # routine entries the day before (no story facts beyond NARRATIVE.md: same hand, same station)
        (C, "13.11", "07.58", "W 4", "Fair", "Light extinguished. Lamp and lens cleaned."),
        (C, "", "10.15", "W 4", "Fair", "Engine run 1 hr. Batteries 92%. Fuel day tank topped up."),
        (C, "", "14.00", "SW 5", "Cloudy", "Barometer 1004 mb, falling."),
        (C, "", "16.24", "SW 5", "Cloudy", "Light exhibited. Lamp normal."),
        (C, "", "21.00", "SW 6", "Showers", "Radio check Stornoway CG. All well."),
    ]
    logbook_spread(log_page(1971, rows13, 70, "NOVEMBER", 26), log_page(1971, rows71, 71, "NOVEMBER", 26)).save(
        TEX / "T_LL_Logbook.png", optimize=True)
    add("coat_note", "Note in the oilskin pocket", coat_note(), "\n".join(COAT_NOTE))
    add("photo_1953", "Photograph: the Mary Ellen's crew, July 1953", photo("crew"),
        "Eight men on a deck at Leverburgh pier. The one at the wheel is laughing. On the back, in pencil: \"Mary Ellen, "
        "July 1953. A. Ross, master.\" Beneath, in another hand: \"Kenny B. on the hatch.\"")
    # one 2048 atlas for the three prop faces (one material, not three): calendar top-left (700x1000),
    # wiring diagram top-right (1100x800 at x 720), barometer dial bottom-left (1024x1024 at y 1024)
    props_atlas()
    extra_docs()
    (OUT / "docs.json").write_text(json.dumps(DOCS, indent=1))
    print("DOCS_RESULT", json.dumps(sorted(DOCS)))


if __name__ == "__main__":
    main()
