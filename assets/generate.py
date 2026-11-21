#!/usr/bin/env python3
"""Render the passport spread for the Republic of Talvar.

Draws a 1024x1024 open-passport spread: a visa/stamp page on the left and
the data page on the right, for a fictional North Atlantic island republic
whose whole economy runs on its harbour and its lighthouse. Everything is
drawn in code with Pillow; the one document fact the picture must never
break is its own timeline (issue 14 MAR 2023, every stamp after it).
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "entry.png")
SIZE = 1024

PALETTE = {
    "desk": (34, 34, 42),
    "desk_edge": (26, 26, 32),
    "paper": (245, 240, 225),
    "paper_shade": (232, 223, 200),
    "paper_line": (214, 201, 170),
    "ink": (26, 42, 74),
    "ink_soft": (70, 84, 112),
    "gold": (176, 138, 46),
    "gold_pale": (212, 186, 110),
    "red": (142, 43, 37),
    "blue": (31, 78, 121),
    "green": (46, 107, 58),
    "skin": (226, 188, 158),
    "skin_shade": (206, 164, 132),
    "hair": (58, 40, 30),
    "jacket": (38, 54, 84),
    "photo_bg": (199, 211, 222),
}

FONT_DIR = "/usr/share/fonts/truetype"
FONTS = {
    "serif": os.path.join(FONT_DIR, "liberation", "LiberationSerif-Regular.ttf"),
    "serif_b": os.path.join(FONT_DIR, "liberation", "LiberationSerif-Bold.ttf"),
    "serif_i": os.path.join(FONT_DIR, "liberation", "LiberationSerif-Italic.ttf"),
    "sans": os.path.join(FONT_DIR, "liberation", "LiberationSans-Regular.ttf"),
    "sans_b": os.path.join(FONT_DIR, "liberation", "LiberationSans-Bold.ttf"),
    "mono": os.path.join(FONT_DIR, "liberation", "LiberationMono-Regular.ttf"),
    "mono_b": os.path.join(FONT_DIR, "liberation", "LiberationMono-Bold.ttf"),
}

_cache = {}


def font(name, size):
    """Load a TrueType font, cached so repeated draws stay cheap."""
    key = (name, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(FONTS[name], size)
    return _cache[key]


def text_size(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def centred(draw, cx, y, text, fnt, fill):
    w, _ = text_size(draw, text, fnt)
    draw.text((cx - w / 2, y), text, font=fnt, fill=fill)


def right_aligned(draw, x, y, text, fnt, fill):
    w, _ = text_size(draw, text, fnt)
    draw.text((x - w, y), text, font=fnt, fill=fill)


def wrap(draw, text, fnt, max_width):
    """Greedy word wrap returning a list of lines that fit max_width."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if text_size(draw, trial, fnt)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def mrz_check(text):
    """ICAO 9303 check digit: weights 7, 3, 1; A=10 .. Z=35, '<'=0."""
    weights = (7, 3, 1)
    total = 0
    for i, ch in enumerate(text):
        if ch.isdigit():
            value = int(ch)
        elif ch == "<":
            value = 0
        else:
            value = ord(ch) - ord("A") + 10
        total += value * weights[i % 3]
    return str(total % 10)


def mrz_lines():
    """Build the two MRZ lines for Elena Maris Voss, passport TV2304821.
    The MRZ document-number field is 9 characters, so the passport number
    itself is 9 characters long and matches the printed number exactly."""
    line1 = "P<TVAVOSS<<ELENA<MARIS"
    line1 = line1 + "<" * (44 - len(line1))
    doc = "TV2304821"
    doc_c = mrz_check(doc)
    birth = "870602"
    birth_c = mrz_check(birth)
    expiry = "330314"
    expiry_c = mrz_check(expiry)
    personal = "<" * 14
    personal_c = mrz_check(personal)
    body = doc + doc_c + "TVA" + birth + birth_c + "F" + expiry + expiry_c + personal + personal_c
    line2 = body + mrz_check(body)
    return line1, line2


def guilloche(draw, box, colour, step=9):
    """Fine concentric arcs in a corner, the way security paper prints."""
    x0, y0, x1, y1 = box
    cx, cy = x0, y1
    radius = step
    while radius < (x1 - x0) * 1.6:
        draw.arc([cx - radius, cy - radius, cx + radius, cy + radius],
                 start=270, end=360, fill=colour, width=1)
        radius += step


def watermark(page, draw, text, colour):
    """A big diagonal country name, barely there, across the two pages only."""
    layer = Image.new("RGBA", page.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    big = font("serif_b", 120)
    w, h = text_size(ld, text, big)
    tile = Image.new("RGBA", (w + 80, h + 40), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    td.text((40, 20), text, font=big, fill=colour + (26,))
    tile = tile.rotate(38, expand=True, resample=Image.BICUBIC)
    for x in range(-200, SIZE, tile.width - 60):
        for y in range(-100, SIZE, tile.height - 40):
            layer.alpha_composite(tile, (x, y))
    # keep the watermark off the desk: mask it to the two page rectangles
    mask = Image.new("L", page.size, 0)
    md = ImageDraw.Draw(mask)
    md.rectangle([62, 72, 512, 952], fill=255)
    md.rectangle([512, 72, 962, 952], fill=255)
    from PIL import ImageChops
    layer.putalpha(ImageChops.multiply(layer.split()[3], mask))
    page.alpha_composite(layer)


def draw_emblem(draw, cx, top, scale=1.0):
    """The Talvar arms: a striped lighthouse over three waves, in a ring."""
    gold = PALETTE["gold"]
    ink = PALETTE["ink"]
    r = int(34 * scale)
    draw.ellipse([cx - r, top, cx + r, top + 2 * r], outline=gold, width=2)
    # tower
    tw = int(13 * scale)
    th = int(30 * scale)
    base_y = top + int(52 * scale)
    draw.polygon([(cx - tw, base_y), (cx - int(9 * scale), top + int(18 * scale)),
                  (cx + int(9 * scale), top + int(18 * scale)), (cx + tw, base_y)],
                 fill=ink)
    draw.rectangle([cx - tw, top + int(30 * scale), cx + tw, top + int(36 * scale)],
                   fill=PALETTE["paper"])
    draw.rectangle([cx - tw, top + int(42 * scale), cx + tw, top + int(48 * scale)],
                   fill=PALETTE["paper"])
    # lamp room and light
    draw.rectangle([cx - int(10 * scale), top + int(8 * scale),
                    cx + int(10 * scale), top + int(18 * scale)], fill=gold)
    draw.polygon([(cx - int(10 * scale), top + int(13 * scale)),
                  (cx - int(34 * scale), top + int(2 * scale)),
                  (cx - int(34 * scale), top + int(24 * scale))],
                 fill=PALETTE["gold_pale"])
    draw.polygon([(cx + int(10 * scale), top + int(13 * scale)),
                  (cx + int(34 * scale), top + int(2 * scale)),
                  (cx + int(34 * scale), top + int(24 * scale))],
                 fill=PALETTE["gold_pale"])
    # waves
    for i, wy in enumerate((base_y + 4, base_y + 12)):
        for k in range(-3, 4):
            x = cx + k * int(14 * scale)
            draw.arc([x, wy, x + int(14 * scale), wy + int(8 * scale)],
                     start=180, end=360, fill=ink, width=2)

def draw_portrait(size):
    """A flat passport portrait: Elena Maris Voss, dark hair in a bun,
    navy jacket, pale blue-grey backdrop. Deliberately plain — a document
    photo, not a painting."""
    w, h = size
    img = Image.new("RGB", size, PALETTE["photo_bg"])
    d = ImageDraw.Draw(img)
    # backdrop shading
    for y in range(h):
        shade = int(8 * (1 - y / h))
        d.line([(0, y), (w, y)], fill=(199 - shade, 211 - shade, 222 - shade))
    cx = w // 2
    # shoulders / jacket
    d.polygon([(cx - 78, h), (cx - 66, h - 52), (cx - 30, h - 66),
               (cx + 30, h - 66), (cx + 66, h - 52), (cx + 78, h)],
              fill=PALETTE["jacket"])
    d.polygon([(cx - 16, h - 66), (cx, h - 44), (cx + 16, h - 66),
               (cx + 26, h - 52), (cx - 26, h - 52)], fill=(240, 238, 232))
    d.polygon([(cx - 6, h - 62), (cx, h - 46), (cx + 6, h - 62),
               (cx + 10, h - 52), (cx - 10, h - 52)], fill=PALETTE["ink"])
    # neck and head
    d.rectangle([cx - 13, h - 96, cx + 13, h - 62], fill=PALETTE["skin_shade"])
    d.ellipse([cx - 34, h - 158, cx + 34, h - 78], fill=PALETTE["skin"])
    # hair: cap plus a bun
    d.pieslice([cx - 38, h - 164, cx + 38, h - 92], start=180, end=360,
               fill=PALETTE["hair"])
    d.ellipse([cx - 16, h - 176, cx + 16, h - 148], fill=PALETTE["hair"])
    d.arc([cx - 34, h - 158, cx + 34, h - 92], start=200, end=340,
          fill=PALETTE["hair"], width=10)
    # brows, eyes, nose, mouth — kept minimal and symmetrical
    for sign in (-1, 1):
        ex = cx + sign * 15
        d.line([(ex - 9, h - 128), (ex + 9, h - 130)], fill=PALETTE["hair"], width=3)
        d.ellipse([ex - 6, h - 122, ex + 6, h - 116], fill=(52, 44, 40))
        d.ellipse([ex - 2, h - 121, ex + 2, h - 118], fill=(255, 255, 255))
    d.line([(cx + 2, h - 116), (cx - 2, h - 102), (cx + 4, h - 100)],
           fill=PALETTE["skin_shade"], width=2)
    d.line([(cx - 8, h - 92), (cx + 8, h - 92)], fill=(168, 96, 92), width=3)
    d.line([(cx - 5, h - 89), (cx + 5, h - 89)], fill=(188, 128, 122), width=2)
    return img


def make_stamp(lines, colour, size=(196, 116), oval=False, angle=0):
    """One border-control stamp as its own layer, slightly rotated."""
    layer = Image.new("RGBA", (size[0] + 30, size[1] + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0 = 15, 15
    x1, y1 = x0 + size[0], y0 + size[1]
    if oval:
        d.ellipse([x0, y0, x1, y1], outline=colour, width=3)
        d.ellipse([x0 + 6, y0 + 6, x1 - 6, y1 - 6], outline=colour, width=1)
    else:
        d.rounded_rectangle([x0, y0, x1, y1], radius=8, outline=colour, width=3)
        d.rounded_rectangle([x0 + 5, y0 + 5, x1 - 5, y1 - 5], radius=5,
                            outline=colour, width=1)
    f_big = font("sans_b", 17)
    f_small = font("sans_b", 12)
    f_date = font("mono_b", 14)
    n = len(lines)
    for i, (text, kind) in enumerate(lines):
        fnt = f_big if kind == "big" else (f_date if kind == "date" else f_small)
        # lines sit at 10 / 46 / 82 so the date clears the inner border
        centred(d, (x0 + x1) / 2, y0 + 10 + i * (size[1] - 44) / max(n - 1, 1),
                text, fnt, colour)
    return layer.rotate(angle, expand=True, resample=Image.BICUBIC)


def draw_visa(d, x, y, w, h):
    """The Meridia visitor-visa sticker: issued 02 APR 2023, before the
    first Meridia entry on 28 APR 2023."""
    d.rectangle([x, y, x + w, y + h], fill=(250, 246, 232),
                outline=PALETTE["ink"], width=2)
    d.rectangle([x, y, x + w, y + 34], fill=PALETTE["ink"])
    centred(d, x + w / 2, y + 8, "MERIDIA  —  VISITOR VISA",
            font("sans_b", 15), (245, 240, 225))
    rows = [
        ("Visa No.", "MRD-2023-11844"),
        ("Issued", "02 APR 2023 — PORT OF CALDARA"),
        ("Valid for", "90 DAYS — SINGLE ENTRY"),
        ("Conditions", "TOURISM ONLY — NO EMPLOYMENT"),
    ]
    yy = y + 44
    for label, value in rows:
        d.text((x + 12, yy), label, font=font("sans_b", 11), fill=PALETTE["ink_soft"])
        d.text((x + 96, yy), value, font=font("sans", 11), fill=PALETTE["ink"])
        yy += 20
    # round visa seal
    sx, sy, sr = x + w - 52, y + h - 56, 22
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], outline=PALETTE["red"], width=2)
    centred(d, sx, sy - 12, "MERIDIA", font("sans_b", 9), PALETTE["red"])
    centred(d, sx, sy + 2, "★", font("sans_b", 12), PALETTE["red"])
    centred(d, sx, sy + 14, "CALDARA", font("sans_b", 7), PALETTE["red"])
    # signature squiggle
    d.line([(x + 14, y + h - 18), (x + 34, y + h - 26), (x + 52, y + h - 16),
            (x + 70, y + h - 24), (x + 92, y + h - 18)],
           fill=PALETTE["ink"], width=2)


def field(d, x, y, label, value, label_w=118, value_font=None, max_width=None):
    """One data-page row: small-caps label above, value below it. Long
    values wrap instead of running off the page edge."""
    d.text((x, y), label, font=font("sans_b", 10), fill=PALETTE["ink_soft"])
    fnt = value_font or font("sans", 15)
    if max_width:
        lines = wrap(d, value, fnt, max_width)
    else:
        lines = [value]
    for i, line in enumerate(lines):
        d.text((x, y + 13 + i * 15), line, font=fnt, fill=PALETTE["ink"])


def draw_data_page(page, draw):
    """The right-hand page: arms, header, portrait, personal data, the
    lighthouse-keeper endorsement, and the machine-readable zone."""
    x0, y0 = 512, 72
    x1, y1 = 962, 952
    draw.rectangle([x0, y0, x1, y1], fill=PALETTE["paper"])
    draw.rectangle([x0 + 3, y0 + 3, x1 - 3, y1 - 3], outline=PALETTE["gold"], width=1)
    guilloche(draw, (x0 + 8, y0 + 8, x0 + 150, y0 + 150), PALETTE["gold_pale"])
    watermark(page, draw, "TALVAR", PALETTE["gold"])
    draw_emblem(draw, (x0 + x1) // 2, y0 + 22, scale=0.9)
    centred(draw, (x0 + x1) // 2, y0 + 96, "REPUBLIC OF TALVAR",
            font("serif_b", 26), PALETTE["ink"])
    centred(draw, (x0 + x1) // 2, y0 + 126, "P A S S P O R T",
            font("serif", 15), PALETTE["ink_soft"])
    centred(draw, (x0 + x1) // 2, y0 + 148, "VALO MERE PÄÄL  •  LIGHT UPON THE SEA",
            font("serif_i", 11), PALETTE["gold"])
    draw.line([(x0 + 30, y0 + 172), (x1 - 30, y0 + 172)], fill=PALETTE["gold"], width=2)

    # portrait, top left
    px, py, pw, ph = x0 + 28, y0 + 192, 150, 188
    portrait = draw_portrait((pw, ph))
    page.paste(portrait, (px, py))
    draw.rectangle([px, py, px + pw, py + ph], outline=PALETTE["ink"], width=2)
    # ghost image, faint, bottom right of the portrait
    ghost = portrait.resize((64, 80)).convert("RGBA")
    ghost.putalpha(70)
    page.alpha_composite(ghost, (px + pw - 58, py + ph - 74))
    centred(draw, px + pw / 2, py + ph + 6, "PHOTO — HOLDER",
            font("sans_b", 8), PALETTE["ink_soft"])

    # personal data, right of the portrait
    dx = x0 + 196
    field(draw, dx, y0 + 192, "TYPE", "P")
    field(draw, dx + 52, y0 + 192, "CODE", "TVA")
    field(draw, dx + 118, y0 + 192, "PASSPORT No.", "TV2304821",
          value_font=font("mono_b", 15))
    field(draw, dx, y0 + 240, "SURNAME", "VOSS")
    field(draw, dx, y0 + 288, "GIVEN NAMES", "ELENA MARIS")
    field(draw, dx, y0 + 336, "NATIONALITY", "TALVARI")
    field(draw, dx + 140, y0 + 336, "SEX", "F")
    field(draw, dx + 180, y0 + 336, "HEIGHT", "172 cm")
    field(draw, dx, y0 + 384, "DATE OF BIRTH", "02 JUN 1987")
    field(draw, dx, y0 + 432, "PLACE OF BIRTH", "PORT LIORA, TALVAR")
    field(draw, dx, y0 + 480, "DATE OF ISSUE", "14 MAR 2023")
    field(draw, dx, y0 + 528, "DATE OF EXPIRY", "14 MAR 2033")
    field(draw, dx, y0 + 576, "AUTHORITY", "MINISTRY OF THE SEA",
          max_width=234)
    # signature: name above the line, caption below it
    d_sig = ImageDraw.Draw(page)
    d_sig.text((dx, y0 + 618), "E. M. Voss", font=font("serif_i", 16),
               fill=PALETTE["ink"])
    draw.line([(dx, y0 + 640), (dx + 200, y0 + 640)], fill=PALETTE["ink"], width=1)
    d_sig.text((dx, y0 + 646), "HOLDER'S SIGNATURE",
               font=font("sans_b", 8), fill=PALETTE["ink_soft"])

    # the telling detail: the lighthouse-keeper endorsement
    ex, ey, ew, eh = x0 + 28, y0 + 700, 394, 62
    draw.rectangle([ex, ey, ex + ew, ey + eh], outline=PALETTE["red"], width=2)
    draw.text((ex + 10, ey + 6), "ENDORSEMENT", font=font("sans_b", 10),
              fill=PALETTE["red"])
    for i, line in enumerate(wrap(draw,
            "Holder is a certified lighthouse keeper — exempt from port fees "
            "at all Talvari harbours. Ministry of the Sea, Port Liora.",
            font("sans", 11), ew - 20)):
        draw.text((ex + 10, ey + 22 + i * 14), line, font=font("sans", 11),
                  fill=PALETTE["ink"])

    # machine-readable zone
    line1, line2 = mrz_lines()
    my = y1 - 78
    draw.rectangle([x0 + 14, my - 8, x1 - 14, my + 52], fill=(238, 232, 214))
    draw.text((x0 + 20, my), line1, font=font("mono", 15), fill=PALETTE["ink"])
    draw.text((x0 + 20, my + 24), line2, font=font("mono", 15), fill=PALETTE["ink"])
    right_aligned(draw, x1 - 20, y1 - 22, "12", font("sans_b", 10),
                  PALETTE["ink_soft"])


def draw_stamp_page(page, draw):
    """The left-hand page: the Meridia visa, six border stamps in travel
    order, and a clerk's handwritten cross-reference."""
    x0, y0 = 62, 72
    x1, y1 = 512, 952
    draw.rectangle([x0, y0, x1, y1], fill=PALETTE["paper"])
    draw.rectangle([x0 + 3, y0 + 3, x1 - 3, y1 - 3], outline=PALETTE["gold"], width=1)
    watermark(page, draw, "TALVAR", PALETTE["gold"])
    centred(draw, (x0 + x1) // 2, y0 + 18, "V I S A S",
            font("serif_b", 16), PALETTE["ink"])
    draw.line([(x0 + 30, y0 + 44), (x1 - 30, y0 + 44)], fill=PALETTE["gold"], width=1)

    draw_visa(draw, x0 + 26, y0 + 58, 398, 168)

    stamps = [
        (make_stamp([("DEPARTED", "big"), ("PORT LIORA", "small"),
                     ("27 APR 2023", "date")], PALETTE["blue"], oval=True, angle=-9),
         x0 + 30, y0 + 250),
        (make_stamp([("ENTERED", "big"), ("PORT OF CALDARA", "small"),
                     ("28 APR 2023", "date")], PALETTE["red"], angle=7),
         x0 + 232, y0 + 258),
        (make_stamp([("DEPARTED", "big"), ("PORT OF CALDARA", "small"),
                     ("05 MAY 2023", "date")], PALETTE["red"], angle=-6),
         x0 + 34, y0 + 392),
        (make_stamp([("ARRIVED", "big"), ("PORT LIORA", "small"),
                     ("06 MAY 2023", "date")], PALETTE["blue"], oval=True, angle=10),
         x0 + 238, y0 + 400),
        (make_stamp([("ENTERED", "big"), ("BRYNN BORDER POST", "small"),
                     ("19 SEP 2023", "date")], PALETTE["green"], angle=-8),
         x0 + 30, y0 + 536),
        (make_stamp([("DEPARTED", "big"), ("KARSTOV — BRYNN", "small"),
                     ("02 OCT 2023", "date")], PALETTE["green"], angle=6),
         x0 + 232, y0 + 544),
    ]
    for layer, sx, sy in stamps:
        page.alpha_composite(layer, (sx, sy))

    # arrival home after the Karstov trip, small and neat
    home = make_stamp([("ARRIVED", "big"), ("PORT LIORA", "small"),
                       ("03 OCT 2023", "date")], PALETTE["blue"], oval=True,
                      size=(176, 104), angle=-4)
    page.alpha_composite(home, (x0 + 128, y0 + 668))

    # clerk's note, in italic serif like handwriting
    draw.text((x0 + 30, y0 + 800), "See endorsement — lighthouse keeper, p. 14.",
              font=font("serif_i", 13), fill=PALETTE["ink_soft"])
    right_aligned(draw, x1 - 20, y1 - 22, "11", font("sans_b", 10),
                  PALETTE["ink_soft"])


def compose():
    """Assemble the whole spread on a dark desk, with a gutter shadow."""
    img = Image.new("RGB", (SIZE, SIZE), PALETTE["desk"])
    draw = ImageDraw.Draw(img)
    # desk vignette
    for i in range(60):
        draw.rectangle([i, i, SIZE - i, SIZE - i],
                       outline=(PALETTE["desk_edge"][0] + i // 6,
                                PALETTE["desk_edge"][1] + i // 6,
                                PALETTE["desk_edge"][2] + i // 6))
    page = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(page)
    draw_stamp_page(page, pdraw)
    draw_data_page(page, pdraw)
    # gutter shadow between the two pages
    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    for i in range(5):
        sdraw.rectangle([512 - 5 + i, 72, 512 + 5 - i, 952],
                        fill=(0, 0, 0, 26 - i * 4))
    page.alpha_composite(shadow)
    img.paste(page, (0, 0), page)
    img.save(OUT, format="PNG", optimize=True)
    return OUT


if __name__ == "__main__":
    path = compose()
    size = os.path.getsize(path)
    print(f"wrote {path} ({size} bytes)")
