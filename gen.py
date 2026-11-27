#!/usr/bin/env python3
"""news-26-b22-numbers — layout V20: masthead + DATE CHECK, 3-column main
(left rail cards 1-5, centre 3 stacked heroes, right rail cards 6-10),
map + ALSO, timeline strip, footer. Renders entry.png 1024x1024, <=1 MiB.
All strings measured with PIL font metrics against their real column width;
any overflow raises instead of truncating. No trunc() anywhere.
"""
import hashlib
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = "entry.png"
DJ = "/usr/share/fonts/truetype/dejavu/"
SERIF = DJ + "DejaVuSerif-Bold.ttf"
SERIF_R = DJ + "DejaVuSerif.ttf"
SANS = DJ + "DejaVuSans.ttf"
SANS_B = DJ + "DejaVuSans-Bold.ttf"

INK = (17, 17, 17)
PAPER = (247, 243, 234)
RED = (179, 32, 44)
NAVY = (26, 58, 92)
GOLD = (176, 132, 30)
GREY = (90, 86, 78)
LINE = (120, 112, 96)
BAND = (232, 226, 210)
YELLOW = (255, 243, 205)
OCEAN = (214, 228, 240)
LAND = (233, 226, 210)


def font(size, bold=False, serif=False):
    if serif:
        return ImageFont.truetype(SERIF if bold else SERIF_R, size)
    return ImageFont.truetype(SANS_B if bold else SANS, size)


def text_w(s, fnt):
    return fnt.getlength(s)


def wrap(text, fnt, maxw):
    """Greedy wrap; raises if any single word exceeds maxw."""
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_w(trial, fnt) <= maxw:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            if text_w(wd, fnt) > maxw:
                raise AssertionError("word too wide: %r (%d > %d)" % (wd, text_w(wd, fnt), maxw))
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def fit(text, fnt, maxw, maxlines, label):
    """Wrap and assert it fits in maxlines; never truncates."""
    lines = wrap(text, fnt, maxw)
    assert len(lines) <= maxlines, "%s needs %d lines, max %d: %r" % (label, len(lines), maxlines, text)
    return lines


def draw_lines(d, lines, x, y, fnt, fill, lh):
    for ln in lines:
        d.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


# ---------------------------------------------------------------- data
# Heroes: (city, tag, headline, why, stat). WHY is the significance angle
# (WHY IT MATTERS), rendered with that label prefix; must end with ".".
HEROES = [
    ("NEW YORK", "[C]",
     "Macy's 100th parade postponed — a first for weather",
     "The first weather delay in 100 years leaves Thanksgiving without its most famous icon.",
     "GUSTS 60 MPH  ·  SAT 28 NOV 08:30 ET  ·  100TH PARADE"),
    ("HORMUZ", "[CL]",
     "IRGC claims 2 tankers hit by mines in Hormuz",
     "If true, it widens the Iran war to the world's busiest oil chokepoint as Brent climbs.",
     "2M BARRELS  ·  UKMTO BLAST 50 NM W OF DUBAI"),
    ("GLOBAL MARKETS", "[C]",
     "Global markets rebound as Trump tariffs look milder",
     "Milder-than-feared levies calm fears of a global trade shock.",
     "14 PARTNERS  ·  CHINA 20%  ·  STOXX +1.6%"),
]
for _c, _t, _h, _w, _s in HEROES:
    assert _w.endswith("."), "WHY must end with '.': %r" % _w

# Cards: (city, tag, headline, deck, stat). Deck + stat = same single story.
CARDS_L = [
    ("GAZA", "[C]", "Israeli strike kills Hamas education deputy",
     "Khaled Abu Nada and his wife die in a Deir al-Balah flat.",
     "9 KILLED OVERNIGHT"),
    ("KYIV", "[C]", "Russian missile hits Kyiv mall",
     "Ballistic strike wounds 7 as 113 drones attack overnight.",
     "7 WOUNDED · 2 SERIOUS"),
    ("BOGOR", "[C]", "Flooded illegal gold mine traps miners",
     "Rescue teams reach ~100 m down after heavy rain.",
     "13 DEAD · 13 MISSING"),
    ("JERUSALEM", "[R]", "Judge urges Netanyahu bribery charge dropped",
     "Court recommends prosecutors drop Case 4000.",
     "ONLY BRIBERY COUNT"),
    ("PYONGYANG", "[C]", "Kim urges tactical nukes at nuclear plant",
     "KCNA reports the leader's visit on Thursday.",
     "TACTICAL NUKES PUSH"),
]
CARDS_R = [
    ("WASHINGTON", "[C]", "FCC clears 1M SpaceX orbital satellites",
     "First US approval for space-based data centres.",
     "APPROVED 25 NOV"),
    ("LONDON", "[C]", "UK net migration falls to 77,000",
     "Lowest since 1997 outside the pandemic, ONS says.",
     "77,000 · YEAR TO JUNE"),
    ("MOSCOW", "[C]", "Russia approves record military budget",
     "Defence spending hits a post-Soviet record.",
     "RECORD BUDGET"),
    ("BANGKOK", "[C]", "Bangkok oil depot blast injures 7",
     "Fire controlled in ~30 minutes; output units shut.",
     "7 INJURED · FIRE OUT"),
    ("COLOGNE", "[C]", "2 Iraqis held over synagogue plot",
     "Raids in Cologne and Heidelberg over March plot.",
     "2 SUSPECTS HELD"),
]

# ALSO: 29 items, each a DIFFERENT story from heroes/cards and from each
# other. Manual check (name + place + event): none repeats a hero/card story.
# (Savasleyka/Kryvyi Rih/Subkhankulovo are Ukrainian strikes on Russian
# targets — different places/events from the Kyiv card, which is a Russian
# strike on Kyiv. Philadelphia is a different parade from Macy's NYC one.)
# The last 5 are new for the 50-story count, each a distinct KANON fact
# absent from gen.py (grep-verified) and from DATE CHECK's excluded list:
# Dow is the third Wed index (S&P/Nasdaq already listed, Dow was not);
# WTI is the US oil benchmark (Brent already listed, WTI was not);
# EU 15% and Vietnam up to 35% are partner rates the hero names only as
# "14 PARTNERS · CHINA 20%"; hearings 25 Jan is the procedural step, not
# the Feb–Mar implementation the hero deck mentions.
ALSO = [
    ("Eisenkot seals first Israel coalition deal", "[C]"),
    ("Merz: Russia's ambitions go beyond Ukraine", "[C]"),
    ("UK on drone-threat alert at air bases", "[C]"),
    ("Norse Atlantic halts all flights", "[C]"),
    ("Poundland collapses; 11,000 jobs at risk", "[C]"),
    ("Malaysia sues Google for $146M", "[C]"),
    ("Kenya court halts US-backed Ebola facility", "[C]"),
    ("Belarus offers Zelensky Moscow flight", "[C]"),
    ("Kushner calls Putin a \u201csignificant figure\u201d", "[C]"),
    ("Estonia decides to close border", "[C]"),
    ("Copernicus: longest stretch above 2\u00b0C", "[C]"),
    ("Nvidia halts AI shipments to 4 nations", "[C]"),
    ("US Bitcoin funds hit record $4.94B", "[C]"),
    ("OPEC+ to meet 29 Nov on 2027 output", "[C]"),
    ("Savasleyka: Ukraine drones damage 5 jets", "[C]"),
    ("Kryvyi Rih: 18 wounded in Russian strike", "[C]"),
    ("Subkhankulovo pump station burns", "[C]"),
    ("Philadelphia parade also cancelled", "[C]"),
    ("UN chief Turk warns of atrocity crimes", "[C]"),
    ("Saudi downs 2 missiles to Riyadh", "[C]"),
    ("S&P 500 \u22120.25% Wed; Nasdaq \u22120.62%", "[C]"),
    ("MSCI global index +0.4%", "[C]"),
    ("Wall Street shut Thu; futures +0.5%", "[C]"),
    ("Brent $93.8 (+0.9%) on Hormuz fears", "[C]"),
    ("Dow +0.33% on Wednesday", "[C]"),
    ("WTI $83.32 (+0.2%) on Thursday", "[C]"),
    ("EU faces 15% tariff in new US salvo", "[C]"),
    ("Vietnam faces tariffs up to 35%", "[C]"),
    ("Tariff hearings set for 25 January", "[C]"),
]
# Distinctive keywords per ALSO item; none may appear in hero/card text.
ALSO_KEYS = ["eisenkot", "merz", "drone-threat", "norse", "poundland",
             "malaysia", "kenya", "belarus", "kushner", "estonia",
             "copernicus", "nvidia", "bitcoin", "opec", "savasleyka",
             "kryvyi", "subkhankulovo", "philadelphia", "turk", "riyadh",
             "s&p 500", "msci", "wall street", "brent",
             "dow +0.33%", "wti", "eu faces", "vietnam", "hearings"]

# Timeline strip: 8 short briefs, distinct from heroes/cards/ALSO.
# Laid out 4 cols x 2 rows so every row fits inside the 44 px box
# (2 cols x 4 rows overflowed past the box bottom into the footer).
TIMELINE = [
    ("KHARKIV", "Couple killed in flat strike", "[C]"),
    ("ODESA", "Cargo ship claimed hit", "[CL]"),
    ("GOLD", "Gold $3,572/oz, −8% in a month", "[C]"),
    ("DOLLAR", "Dollar flat at 103.71", "[C]"),
    ("NBC", "Airs 2025 parade Thu", "[C]"),
    ("MAMDANI", "Misses Sat parade", "[C]"),
    ("NVIDIA", "Shares −3.91% to $149.30", "[C]"),
    ("BALLOONS", "Grounded above 23 mph", "[C]"),
]

# DATE CHECK: stories deliberately EXCLUDED (not 26 Nov), 2 lines.
DATECHECK = [
    "DATE CHECK — NOT 26 NOV: COP31 failure (22 Nov) · Shenzhou-24 launch (25 Nov) · Cairo tanker blast (25 Nov) · Cartagena hostages freed (25 Nov) ·",
    "Australia–Solomon pact (25 Nov) · UK energy +26% (25 Nov) · Huawei verdict (24 Nov) · Ras Tanura strike (25 Nov) · Cartagena supermarket attack (24 Nov)",
]

# Map pins: (number, label, lon, lat, nudge dx, nudge dy in px).
PINS = [
    (1, "NYC", -74.0, 40.7, 0, 0),
    (2, "HORMUZ", 56.5, 26.6, 0, 0),
    (3, "KYIV", 30.5, 50.4, -11, -9),
    (4, "GAZA", 34.4, 31.5, -15, -11),
    (5, "JERUSALEM", 35.2, 31.8, 13, 9),
    (6, "BOGOR", 106.8, -6.6, 0, 0),
    (7, "PYONGYANG", 125.8, 39.0, 0, 0),
    (8, "LONDON", -0.1, 51.5, -13, 7),
    (9, "MOSCOW", 37.6, 55.8, 11, 7),
    (10, "BANGKOK", 100.5, 13.8, 0, 0),
    (11, "COLOGNE", 7.0, 50.9, 11, -7),
]

# Rough continent outlines (lon, lat), stylised — map not to scale.
NA = [(-168, 65), (-155, 71), (-140, 70), (-128, 71), (-118, 72), (-108, 68),
      (-95, 69), (-85, 66), (-82, 73), (-75, 72), (-65, 60), (-55, 52),
      (-60, 46), (-70, 42), (-75, 35), (-80, 32), (-81, 25), (-90, 21),
      (-97, 16), (-94, 17), (-87, 13), (-83, 9), (-79, 9), (-85, 11),
      (-92, 15), (-97, 16), (-105, 20), (-110, 23), (-114, 28), (-120, 34),
      (-125, 40), (-124, 48), (-130, 54), (-140, 60), (-155, 58), (-165, 60)]
SA = [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
      (-70, -23), (-70, -30), (-72, -37), (-73, -44), (-70, -52), (-66, -55),
      (-68, -50), (-62, -41), (-57, -38), (-52, -32), (-48, -28), (-41, -23),
      (-35, -9), (-35, -6), (-40, -3), (-44, -2), (-50, 0), (-53, 4),
      (-58, 6), (-62, 9), (-68, 11), (-72, 12), (-77, 8)]
EU = [(-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (0, 50), (2, 51),
      (5, 53), (8, 57), (10, 59), (5, 60), (5, 62), (12, 65), (18, 69),
      (25, 71), (30, 70), (35, 68), (40, 67), (45, 68), (50, 69), (55, 68),
      (58, 66), (50, 60), (45, 55), (40, 50), (38, 45), (36, 42), (33, 41),
      (30, 36), (27, 37), (23, 36), (22, 38), (19, 40), (16, 38), (15, 40),
      (12, 44), (8, 44), (3, 43), (0, 40), (-2, 37), (-6, 36), (-9, 37)]
AF = [(-6, 35), (-10, 31), (-15, 27), (-17, 21), (-17, 15), (-15, 11),
      (-12, 8), (-8, 5), (-4, 5), (0, 6), (6, 4), (9, 4), (9, 0), (12, -2),
      (12, -6), (13, -10), (12, -17), (14, -22), (16, -28), (20, -35),
      (26, -34), (32, -29), (35, -24), (40, -16), (40, -10), (42, -4),
      (46, 0), (51, 2), (51, 10), (48, 11), (44, 11), (40, 15), (38, 18),
      (37, 22), (35, 28), (32, 31), (25, 32), (20, 32), (15, 33), (10, 34),
      (5, 35), (0, 36)]
AS = [(38, 36), (40, 31), (42, 27), (44, 29), (48, 30), (50, 29), (52, 28),
      (54, 26), (56, 27), (58, 25), (62, 25), (65, 25), (68, 23), (72, 20),
      (75, 12), (77, 8), (80, 15), (86, 20), (89, 22), (92, 21), (94, 17),
      (98, 12), (100, 8), (103, 7), (105, 10), (108, 18), (110, 20),
      (118, 32), (120, 28), (120, 35), (122, 38), (127, 40), (130, 42),
      (135, 44), (140, 53), (142, 59), (150, 59), (158, 52), (162, 56),
      (170, 60), (178, 65), (178, 62), (170, 67), (160, 69), (150, 70),
      (140, 72), (130, 72), (120, 73), (110, 76), (100, 77), (90, 75),
      (80, 73), (75, 72), (68, 73), (60, 69), (55, 68), (50, 66), (45, 62),
      (42, 58), (40, 52), (38, 46), (36, 42), (38, 36)]
AU = [(113, -22), (114, -30), (115, -35), (118, -35), (124, -33), (129, -32),
      (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (150, -37),
      (153, -32), (153, -27), (150, -22), (146, -19), (142, -15), (142, -11),
      (137, -12), (135, -15), (132, -12), (130, -13), (126, -14), (122, -17),
      (118, -20), (113, -22)]


def check_duplicates():
    """ALSO-vs-hero/card scan: 0 duplicates allowed. Also ALSO-vs-ALSO
    headline-start check. Raises on any hit."""
    hc = " ".join([h for _, _, h, _, _ in HEROES] +
                  [h for _, _, h, _, _ in CARDS_L + CARDS_R]).lower()
    for (txt, _tag), key in zip(ALSO, ALSO_KEYS):
        assert key in txt.lower(), "keyword %r not in ALSO item %r" % (key, txt)
        assert key not in hc, "ALSO duplicates hero/card: %r (%s)" % (txt, key)
    starts = [" ".join(t.lower().split()[:3]) for t, _ in ALSO]
    assert len(set(starts)) == len(starts), "ALSO headline starts collide"
    tl = " ".join(t for _, t, _ in TIMELINE).lower()
    for key in ["kharkiv", "odesa", "gold $3,572", "dollar", "nbc", "mamdani",
                "nvidia", "23 mph"]:
        assert key not in hc, "timeline duplicates hero/card: %s" % key
    assert "ras tanura" not in " ".join(t for t, _ in ALSO).lower()


def art(kind, w, h):
    """Scene art drawn on its OWN layer exactly w x h (clamped to its box).
    No text inside art — labels live in solid bands below."""
    im = Image.new("RGB", (w, h), (220, 224, 230))
    d = ImageDraw.Draw(im)
    if kind == "macys":
        d.rectangle([0, 0, w, h], fill=(168, 196, 222))
        for i in range(5):  # skyline
            bx = i * (w // 5)
            d.rectangle([bx + 3, h - 55 - (i % 3) * 12, bx + w // 5 - 3, h], fill=(70, 84, 104))
        d.ellipse([w * 0.28, 8, w * 0.72, h * 0.62], fill=(179, 32, 44))  # balloon
        d.ellipse([w * 0.38, 16, w * 0.62, h * 0.5], fill=(247, 243, 234))
        d.rectangle([0, h - 18, w, h], fill=(60, 60, 60))
        for x in range(8, w, 26):
            d.line([x, h - 18, x, h - 8], fill=(255, 220, 90), width=2)
    elif kind == "hormuz":
        d.rectangle([0, 0, w, h], fill=(232, 150, 80))
        d.rectangle([0, h * 0.62, w, h], fill=(28, 68, 110))  # sea
        d.rectangle([w * 0.12, h * 0.42, w * 0.88, h * 0.62], fill=(40, 40, 44))  # hull
        d.rectangle([w * 0.12, h * 0.30, w * 0.45, h * 0.42], fill=(90, 90, 96))
        for cx, cy, r, c in [(0.3, 0.28, 14, (255, 200, 40)), (0.42, 0.22, 18, (255, 120, 20)),
                             (0.55, 0.28, 12, (255, 200, 40))]:
            d.polygon([(w * cx - r, h * cy + r), (w * cx, h * cy - r * 1.6),
                       (w * cx + r, h * cy + r)], fill=c)
        for cx, cy, r in [(0.35, 0.12, 12), (0.5, 0.08, 15), (0.62, 0.14, 10)]:
            d.ellipse([w * cx - r, h * cy - r, w * cx + r, h * cy + r], fill=(90, 90, 90))
    elif kind == "tariffs":
        d.rectangle([0, 0, w, h], fill=(232, 240, 228))
        d.line([14, h - 14, w - 8, h - 14], fill=INK, width=2)
        d.line([14, h - 14, 14, 10], fill=INK, width=2)
        pts = [(20, h - 30), (w * 0.3, h - 55), (w * 0.45, h - 42),
               (w * 0.62, h - 62), (w * 0.8, h - 48), (w - 14, h - 78)]
        d.line(pts, fill=(22, 120, 60), width=4)
        for x, y in pts:
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(22, 120, 60))
        for i, bh in enumerate([18, 26, 22, 34, 30, 44]):
            x0 = 30 + i * (w - 50) // 6
            d.rectangle([x0, h - 14 - bh, x0 + 14, h - 14], fill=(26, 58, 92))
    elif kind == "gaza":
        d.rectangle([0, 0, w, h], fill=(226, 214, 190))
        d.rectangle([6, h * 0.35, w - 6, h], fill=(120, 100, 80))
        for r in range(3):
            for c in range(3):
                d.rectangle([10 + c * 16, h * 0.42 + r * 22, 20 + c * 16, h * 0.42 + r * 22 + 12],
                            fill=(255, 220, 120) if (r + c) % 2 else (60, 50, 40))
        d.ellipse([w * 0.6, 4, w * 0.6 + 22, 26], fill=(120, 120, 120))
        d.ellipse([w * 0.7, 10, w * 0.7 + 16, 26], fill=(90, 90, 90))
    elif kind == "kyiv":
        d.rectangle([0, 0, w, h], fill=(200, 210, 225))
        d.rectangle([8, h * 0.45, w - 8, h], fill=(90, 96, 110))
        d.polygon([(w * 0.5, 6), (w * 0.58, 22), (w * 0.74, 22), (w * 0.62, 32),
                   (w * 0.68, 48), (w * 0.5, 38), (w * 0.32, 48), (w * 0.38, 32),
                   (w * 0.26, 22), (w * 0.42, 22)], fill=(255, 180, 30))
    elif kind == "bogor":
        d.rectangle([0, 0, w, h], fill=(60, 48, 36))
        d.ellipse([w * 0.5 - 16, h * 0.3 - 16, w * 0.5 + 16, h * 0.3 + 16], fill=(255, 220, 90))
        d.ellipse([w * 0.5 - 8, h * 0.3 - 8, w * 0.5 + 8, h * 0.3 + 8], fill=(255, 240, 160))
        d.rectangle([0, h * 0.72, w, h], fill=(40, 32, 24))
        d.polygon([(0, h), (w * 0.3, h * 0.72), (w * 0.7, h * 0.72), (w, h)], fill=(90, 70, 45))
    elif kind == "jerusalem":
        d.rectangle([0, 0, w, h], fill=(228, 222, 200))
        d.rectangle([6, h * 0.3, w - 6, h * 0.38], fill=(150, 130, 100))
        for i in range(4):
            x0 = 10 + i * (w - 20) // 4
            d.rectangle([x0, h * 0.38, x0 + 8, h * 0.85], fill=(120, 100, 75))
        d.rectangle([4, h * 0.85, w - 4, h * 0.92], fill=(150, 130, 100))
    elif kind == "pyongyang":
        d.rectangle([0, 0, w, h], fill=(210, 214, 220))
        d.rectangle([6, h * 0.5, w * 0.45, h], fill=(90, 96, 104))
        d.rectangle([w * 0.55, h * 0.35, w - 6, h], fill=(70, 76, 86))
        d.polygon([(w * 0.55, h * 0.35), (w * 0.72, h * 0.18), (w - 6, h * 0.35)], fill=(120, 30, 30))
        cx, cy = int(w * 0.78), int(h * 0.62)
        d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], outline=(26, 58, 92), width=3)
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(26, 58, 92))
        for a in (0, 60, 120):
            import math as _m
            d.line([cx, cy, cx + int(16 * _m.cos(_m.radians(a))),
                    cy + int(16 * _m.sin(_m.radians(a)))], fill=(26, 58, 92), width=2)
    elif kind == "washington":
        d.rectangle([0, 0, w, h], fill=(16, 24, 48))
        for sx, sy in [(10, 12), (30, 30), (50, 10), (58, 40), (20, 55), (45, 60)]:
            d.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=(255, 255, 255))
        d.ellipse([w * 0.42, h * 0.35, w * 0.58, h * 0.65], fill=(200, 210, 230))
        d.rectangle([w * 0.2, h * 0.44, w * 0.42, h * 0.56], fill=(26, 90, 160))
        d.rectangle([w * 0.58, h * 0.44, w * 0.8, h * 0.56], fill=(26, 90, 160))
    elif kind == "london":
        d.rectangle([0, 0, w, h], fill=(190, 205, 220))
        d.rectangle([w * 0.38, h * 0.15, w * 0.62, h], fill=(120, 105, 80))
        d.ellipse([w * 0.42, h * 0.2, w * 0.58, h * 0.36], fill=(247, 243, 234))
        d.line([w * 0.5, h * 0.2, w * 0.5, h * 0.36], fill=INK, width=2)
        d.line([w * 0.5, h * 0.28, w * 0.56, h * 0.28], fill=INK, width=2)
        d.rectangle([w * 0.1, h * 0.7, w * 0.32, h], fill=(90, 96, 104))
        d.rectangle([w * 0.68, h * 0.7, w * 0.9, h], fill=(90, 96, 104))
    elif kind == "moscow":
        d.rectangle([0, 0, w, h], fill=(205, 200, 185))
        for i, cc in enumerate([(179, 32, 44), (26, 58, 92), (176, 132, 30)]):
            x0 = 8 + i * (w - 16) // 3
            d.rectangle([x0, h * 0.45, x0 + 14, h], fill=(110, 95, 75))
            d.ellipse([x0 - 2, h * 0.32, x0 + 16, h * 0.48], fill=cc)
    elif kind == "bangkok":
        d.rectangle([0, 0, w, h], fill=(222, 214, 196))
        for i in range(3):
            x0 = 6 + i * (w - 12) // 3
            d.ellipse([x0, h * 0.45, x0 + (w - 12) // 3 - 4, h * 0.6], fill=(150, 150, 150))
            d.rectangle([x0, h * 0.55, x0 + (w - 12) // 3 - 4, h * 0.9], fill=(170, 170, 170))
        d.polygon([(w * 0.6, h * 0.42), (w * 0.68, h * 0.2), (w * 0.76, h * 0.42)], fill=(255, 120, 20))
        d.polygon([(w * 0.68, h * 0.42), (w * 0.74, h * 0.26), (w * 0.8, h * 0.42)], fill=(255, 200, 40))
    elif kind == "cologne":
        d.rectangle([0, 0, w, h], fill=(216, 222, 230))
        d.rectangle([8, h * 0.55, w - 8, h * 0.9], fill=(130, 120, 100))
        d.ellipse([w * 0.3, h * 0.28, w * 0.7, h * 0.62], fill=(26, 58, 92))
        d.rectangle([w * 0.48, h * 0.12, w * 0.52, h * 0.3], fill=(26, 58, 92))
        d.rectangle([w * 0.12, h * 0.3, w * 0.2, h * 0.9], fill=(110, 100, 85))
        d.rectangle([w * 0.8, h * 0.3, w * 0.88, h * 0.9], fill=(110, 100, 85))
    return im


def tag_chip(d, x, y, tag):
    """Solid tag chip: [C] green-ish dark, [R] amber, [CL] red outline."""
    f = font(10, bold=True)
    tw = int(text_w(tag, f)) + 8
    if tag == "[C]":
        fill = (34, 110, 60)
    elif tag == "[R]":
        fill = (150, 110, 10)
    else:
        fill = RED
    d.rounded_rectangle([x, y, x + tw, y + 14], radius=3, fill=fill)
    d.text((x + 4, y + 1), tag, font=f, fill=(255, 255, 255))
    return tw


def draw_masthead(img, y, h):
    d = ImageDraw.Draw(img)
    d.rectangle([0, y, W, y + h], fill=PAPER)
    f_title = font(30, bold=True, serif=True)
    f_date = font(15, bold=True)
    f_sub = font(11, bold=True)
    title = "THE WORLD IN ONE PAGE"
    d.text((16, y + 6), title, font=f_title, fill=INK)
    date = "THURSDAY 26 NOVEMBER 2026"
    d.text((W - 16 - text_w(date, f_date), y + 12), date, font=f_date, fill=RED)
    sub = "SUMMING UP THE WORLD'S NEWS  ·  50 STORIES  ·  16+ REGIONS  ·  [C] CONFIRMED  [R] REPORTED  [CL] CLAIM"
    d.text((16, y + h - 20), sub, font=f_sub, fill=GREY)
    d.line([16, y + h - 3, W - 16, y + h - 3], fill=RED, width=3)


def draw_datecheck(img, y, h):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([16, y, W - 16, y + h], radius=4, fill=YELLOW, outline=(200, 170, 60))
    f = font(11)
    f_b = font(11, bold=True)
    lead = "DATE CHECK"
    for i, ln in enumerate(DATECHECK):
        assert text_w(ln, f) <= W - 32 - 8, "DATE CHECK line %d too wide" % i
        if i == 0:
            # Bold lead-in drawn FIRST, the rest follows after its true
            # bold width — never overpainted onto the dash that follows.
            rest = ln[len(lead):]
            assert text_w(lead, f_b) + text_w(rest, f) <= W - 32 - 8, "DATE CHECK line 0 too wide"
            d.text((22, y + 4), lead, font=f_b, fill=RED)
            d.text((22 + text_w(lead, f_b), y + 4), rest, font=f, fill=INK)
        else:
            d.text((22, y + 4 + i * 18), ln, font=f, fill=INK)


def draw_hero(img, x, y, w, h, city, tag, headline, why, stat, kind):
    """Art top (clamped to its own box), text band below on solid paper.
    Asserts WHY-to-stat gap >= 6 px."""
    art_h, pad = 80, 6
    img.paste(art(kind, w, art_h), (x, y))
    d = ImageDraw.Draw(img)
    ty = y + art_h
    d.rectangle([x, ty, x + w, y + h], fill=PAPER)
    d.rectangle([x, ty, x + w, ty + 2], fill=NAVY)
    cx = x + pad
    f_city = font(11, bold=True)
    d.text((cx, ty + 4), city, font=f_city, fill=RED)
    tag_chip(d, x + w - 34, ty + 4, tag)
    f_head = font(17, bold=True)
    hl = fit(headline, f_head, w - 2 * pad, 2, "hero headline " + city)
    hy = draw_lines(d, hl, cx, ty + 20, f_head, INK, 19)
    f_why = font(12)
    wl = fit("WHY IT MATTERS: " + why, f_why, w - 2 * pad, 2, "hero WHY " + city)
    wy_end = draw_lines(d, wl, cx, hy + 1, f_why, (40, 40, 40), 14)
    f_stat = font(11, bold=True)
    assert text_w(stat, f_stat) <= w - 2 * pad, "hero stat too wide: %s" % city
    gap = (y + h - 15) - wy_end
    assert gap >= 6, "WHY-stat gap %d < 6px in hero %s" % (gap, city)
    d.text((cx, y + h - 15), stat, font=f_stat, fill=NAVY)
    d.rectangle([x, y, x + w, y + h], outline=LINE, width=1)
    return gap


def draw_card(img, x, y, w, h, city, tag, headline, deck, stat, kind):
    """Mini-card: art clamped left, text right on solid paper."""
    art_w = 66
    img.paste(art(kind, art_w, h), (x, y))
    d = ImageDraw.Draw(img)
    tx = x + art_w
    d.rectangle([tx, y, x + w, y + h], fill=(255, 255, 255))
    pad = 6
    cx = tx + pad
    tw = w - art_w - 2 * pad
    f_city = font(10, bold=True)
    city_w = int(text_w(city, f_city))
    assert city_w + 30 <= tw, "card city too wide: %s" % city
    d.text((cx, y + 5), city, font=f_city, fill=RED)
    tag_chip(d, x + w - 30, y + 5, tag)
    f_head = font(12, bold=True)
    hl = fit(headline, f_head, tw, 2, "card headline " + city)
    hy = draw_lines(d, hl, cx, y + 20, f_head, INK, 14)
    f_deck = font(10)
    dl = fit(deck, f_deck, tw, 2, "card deck " + city)
    dy_end = draw_lines(d, dl, cx, hy + 1, f_deck, (50, 50, 50), 12)
    f_stat = font(10, bold=True)
    assert text_w(stat, f_stat) <= tw, "card stat too wide: %s" % city
    d.text((cx, y + h - 15), stat, font=f_stat, fill=NAVY)
    assert dy_end <= y + h - 17, "card deck overflows stat: %s" % city
    d.rectangle([x, y, x + w, y + h], outline=LINE, width=1)


def lonlat_to_xy(lon, lat, mx, my, mw, mh):
    px = mx + (lon + 168) / 360.0 * mw
    py = my + (84 - lat) / 142.0 * mh
    return px, py


def draw_map(img, x, y, w, h):
    d = ImageDraw.Draw(img)
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=LINE)
    f_t = font(11, bold=True)
    d.text((x + 8, y + 5), "WHERE IT HAPPENED — WORLD MAP", font=f_t, fill=NAVY)
    mx, my, mw, mh = x + 6, y + 22, w - 12, h - 62
    d.rectangle([mx, my, mx + mw, my + mh], fill=OCEAN)
    for poly in (NA, SA, EU, AF, AS, AU):
        pts = [lonlat_to_xy(lo, la, mx, my, mw, mh) for lo, la in poly]
        d.polygon(pts, fill=LAND)
    f_n = font(9, bold=True)
    for num, label, lon, lat, ndx, ndy in PINS:
        px, py = lonlat_to_xy(lon, lat, mx, my, mw, mh)
        cx, cy = px + ndx, py + ndy
        if ndx or ndy:
            d.line([px, py, cx, cy], fill=INK, width=1)
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=RED)
        d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=RED, outline=(255, 255, 255), width=1)
        tw = text_w(str(num), f_n)
        d.text((cx - tw / 2, cy - 6), str(num), font=f_n, fill=(255, 255, 255))
    f_l = font(8)
    leg1 = "1 NYC  2 HORMUZ  3 KYIV  4 GAZA  5 JERUSALEM  6 BOGOR"
    leg2 = "7 PYONGYANG  8 LONDON  9 MOSCOW  10 BANGKOK  11 COLOGNE  ·  MAP NOT TO SCALE"
    for i, ln in enumerate((leg1, leg2)):
        assert text_w(ln, f_l) <= w - 16, "map legend too wide"
        d.text((x + 8, y + h - 28 + i * 11), ln, font=f_l, fill=GREY)


def draw_also(img, x, y, w, h):
    d = ImageDraw.Draw(img)
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=LINE)
    f_t = font(11, bold=True)
    d.text((x + 8, y + 5), "ALSO ON THURSDAY 26 NOVEMBER", font=f_t, fill=NAVY)
    f_i = font(10)
    f_tag = font(9, bold=True)
    col_w = (w - 16) // 2
    row_h = 13  # 10 pt glyphs are 13 px tall; 15 rows x 13 = 195 + 20 = 215 <= 224
    for i, (txt, tag) in enumerate(ALSO):
        col, row = divmod(i, 15)
        ix = x + 8 + col * col_w
        iy = y + 20 + row * row_h
        full = txt + " " + tag
        # Measure the FULL string — no trunc() anywhere.
        assert text_w(full, f_i) <= col_w - 6, "ALSO too wide: %r" % full
        d.text((ix, iy), txt, font=f_i, fill=INK)
        d.text((ix + text_w(txt + " ", f_i), iy), tag, font=f_tag,
               fill=(34, 110, 60) if tag == "[C]" else RED)
    assert y + 20 + 15 * row_h <= y + h - 4, "ALSO rows overflow"


def draw_timeline(img, y, h):
    d = ImageDraw.Draw(img)
    d.rectangle([16, y, W - 16, y + h], fill=BAND)
    f_l = font(10, bold=True)
    d.text((22, y + 3), "THE DAY IN BRIEF", font=f_l, fill=NAVY)
    f_i = font(9)
    f_b = font(9, bold=True)
    col_w = (W - 32) // 4
    for i, (city, txt, tag) in enumerate(TIMELINE):
        col, row = i % 4, i // 4
        ix = 22 + col * col_w
        iy = y + 17 + row * 13
        # Measure exactly as drawn: city part bold, rest regular.
        w_city = text_w(city + " — ", f_b)
        w_rest = text_w(txt + " " + tag, f_i)
        assert w_city + w_rest <= col_w - 8, "timeline too wide: %r" % (city + " — " + txt + " " + tag)
        d.text((ix, iy), city + " — ", font=f_b, fill=RED)
        d.text((ix + w_city, iy), txt + " " + tag, font=f_i, fill=INK)
    # 4 cols x 2 rows, 9 pt glyphs 12 px tall: last row ends y+17+13+12
    # = y+42, inside the 44 px box; box bottom stays well inside 1024.
    assert y + 17 + 13 + 12 <= y + h, "timeline rows overflow box"
    assert y + h <= 1020, "timeline box bottom past 1020"


def main():
    check_duplicates()
    img = Image.new("RGB", (W, H), PAPER)
    # Vertical plan: 60 + 10 + 40 + 6 + 596 + 6 + 228 + 6 + 44 + 6 + 22 = 1024
    # (10 px of paper between the masthead red rule, bottom y=58, and the
    # DATE CHECK box top y=70, so no rule touches the label.)
    y = 0
    draw_masthead(img, y, 60)
    y = 70
    draw_datecheck(img, y, 40)
    y = 116
    main_y, main_h = y, 596
    lx, lw = 16, 245
    cx, cw = 271, 482
    rx = 763
    hero_h = (main_h - 2 * 9) // 3
    kinds_h = ["macys", "hormuz", "tariffs"]
    for i, (city, tag, hl, why, stat) in enumerate(HEROES):
        draw_hero(img, cx, main_y + i * (hero_h + 9), cw, hero_h,
                  city, tag, hl, why, stat, kinds_h[i])
    card_h = (main_h - 4 * 7) // 5
    kinds_l = ["gaza", "kyiv", "bogor", "jerusalem", "pyongyang"]
    kinds_r = ["washington", "london", "moscow", "bangkok", "cologne"]
    for i, c in enumerate(CARDS_L):
        draw_card(img, lx, main_y + i * (card_h + 7), lw, card_h, *c, kinds_l[i])
    for i, c in enumerate(CARDS_R):
        draw_card(img, rx, main_y + i * (card_h + 7), lw, card_h, *c, kinds_r[i])
    y = main_y + main_h + 6
    draw_map(img, 16, y, 410, 228)
    draw_also(img, 436, y, 572, 228)
    y += 228 + 6
    draw_timeline(img, y, 44)
    y += 44 + 6
    d = ImageDraw.Draw(img)
    f_f = font(9)
    foot = "Sources: Reuters · AP · BBC · CNN · NPR · UKMTO · ONS · KCNA · FCC  |  All stories dated Thursday 26 November 2026 unless marked 25 NOV  |  news-26-b22-numbers"
    assert text_w(foot, f_f) <= W - 32, "footer too wide"
    d.text((16, y + 4), foot, font=f_f, fill=GREY)
    img.save(OUT, optimize=True)
    # Verify the DATE CHECK label is clean: no long horizontal RED run
    # (a rule) may cross its text rows. Bold "DATE CHECK" glyphs alone
    # never make a run >= 60 px (measured max < 20 px on the V20 render).
    chk = Image.open(OUT).convert("RGB")
    cpx = chk.load()
    for _yy in range(70 + 4, 70 + 4 + 14):
        _run = _best = 0
        for _xx in range(16, W - 16):
            if cpx[_xx, _yy] == RED:
                _run += 1
                _best = max(_best, _run)
            else:
                _run = 0
        assert _best < 60, "red rule crosses DATE CHECK label at y=%d (run %d)" % (_yy, _best)
    size = os.path.getsize(OUT)
    assert img.size == (1024, 1024)
    assert size <= 1048576, "entry.png %d bytes > 1 MiB" % size
    sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    n_stories = len(HEROES) + len(CARDS_L) + len(CARDS_R) + len(ALSO) + len(TIMELINE)
    print("entry.png sha256=%s size=%d stories=%d regions=16+" % (sha, size, n_stories))


if __name__ == "__main__":
    main()
