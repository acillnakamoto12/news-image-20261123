#!/usr/bin/env python3
"""Draw the front page for Monday 23 November 2026 from news.json.

Reads the six stories (headline, summary, tag, colour) from news.json next
to this file and paints a newspaper front page, 1024x1024, with Pillow.
No network, no randomness. Run from anywhere: `python3 generate.py`
writes entry.png beside this file.

The layout is measured before it is drawn: every text block is wrapped
first, the heights are summed, and the body type shrinks a point at a
time until the whole page fits. Drawing then uses the same heights, so
nothing can overlap or run off the bottom of the page.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
PAGE = 1024
MARGIN = 46
CONTENT = PAGE - 2 * MARGIN

PAPER = (253, 251, 245)
INK = (18, 18, 18)
GREY = (112, 110, 106)
FAINT = (205, 200, 188)

SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def load(path, size):
    return ImageFont.truetype(path, size)


def wrap_text(draw, text, font, width):
    """Greedy word wrap; returns the lines that fit `width`."""
    lines = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def line_height(font, leading):
    ascent, descent = font.getmetrics()
    return ascent + descent + leading


def block_height(lines, font, leading):
    """Height of a wrapped block: line heights minus the last leading."""
    if not lines:
        return 0
    return len(lines) * line_height(font, leading) - leading


def draw_lines(draw, lines, font, x, y, fill, leading):
    """Draw wrapped lines left-aligned; return y advanced by the block."""
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height(font, leading)
    return y - leading if lines else y


def draw_centered(draw, lines, font, y, fill, leading):
    """Draw wrapped lines centred; return y advanced by the block."""
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text(((PAGE - w) / 2, y), line, font=font, fill=fill)
        y += line_height(font, leading)
    return y - leading if lines else y


def measure(draw, data, sizes):
    """Wrap every text block at `sizes`; return (total height, wrapped)."""
    kicker_f = load(SANS_BOLD, sizes["kicker"])
    mast_f = load(SERIF_BOLD, sizes["masthead"])
    date_f = load(SANS_BOLD, sizes["date"])
    lead_head_f = load(SERIF_BOLD, sizes["lead_head"])
    lead_sum_f = load(SANS, sizes["lead_sum"])
    head_f = load(SANS_BOLD, sizes["head"])
    sum_f = load(SANS, sizes["summary"])
    tag_f = load(SANS_BOLD, sizes["tag"])
    foot_f = load(SANS, sizes["footer"])

    wrapped = {}
    wrapped["kicker"] = wrap_text(draw, data["kicker"], kicker_f, CONTENT)
    wrapped["masthead"] = wrap_text(draw, data["title"], mast_f, CONTENT)
    wrapped["date"] = wrap_text(draw, data["date_line"], date_f, CONTENT)

    lead = data["stories"][0]
    lead_w = CONTENT - 22
    wrapped["lead_tag"] = [lead["tag"]]
    wrapped["lead_head"] = wrap_text(draw, lead["headline"], lead_head_f, lead_w)[:2]
    wrapped["lead_sum"] = wrap_text(draw, lead["summary"], lead_sum_f, lead_w)[:2]

    wrapped["stories"] = []
    for story in data["stories"][1:]:
        head = wrap_text(draw, story["headline"], head_f, CONTENT)[:2]
        # Two summary lines when the headline took one, one when it took two.
        max_sum = 2 if len(head) == 1 else 1
        wrapped["stories"].append(
            {
                "tag": story["tag"],
                "head": head,
                "sum": wrap_text(draw, story["summary"], sum_f, CONTENT)[:max_sum],
            }
        )
    wrapped["footer"] = wrap_text(draw, data["footer"], foot_f, CONTENT)

    total = 0
    total += 20  # top pad
    total += block_height(wrapped["kicker"], kicker_f, 4) + 8
    total += block_height(wrapped["masthead"], mast_f, 4) + 5
    total += block_height(wrapped["date"], date_f, 4) + 12
    total += 3 + 5 + 1 + 14  # thick rule, gap, thin rule, gap
    lead_h = (
        block_height(wrapped["lead_tag"], tag_f, 2)
        + 5
        + block_height(wrapped["lead_head"], lead_head_f, 6)
        + 6
        + block_height(wrapped["lead_sum"], lead_sum_f, 5)
    )
    total += lead_h + 14
    total += 1 + 12  # divider + gap
    for item in wrapped["stories"]:
        total += block_height([item["tag"]], tag_f, 2) + 4
        total += block_height(item["head"], head_f, 4) + 4
        total += block_height(item["sum"], sum_f, 4) + 26
    total += 1 + 8  # footer divider + gap
    total += block_height(wrapped["footer"], foot_f, 3) + 20  # bottom pad
    return total, wrapped, lead_h


def main():
    data = json.loads((HERE / "news.json").read_text())
    img = Image.new("RGB", (PAGE, PAGE), PAPER)
    draw = ImageDraw.Draw(img)

    sizes = {
        "kicker": 19,
        "masthead": 60,
        "date": 25,
        "lead_head": 40,
        "lead_sum": 24,
        "head": 27,
        "summary": 22,
        "tag": 20,
        "footer": 16,
    }
    # Shrink the body type until the page fits with room to spare.
    while True:
        total, wrapped, lead_h = measure(draw, data, sizes)
        if total <= 1000 or sizes["summary"] <= 16:
            break
        sizes["summary"] -= 1
        sizes["head"] -= 1
        sizes["lead_sum"] -= 1

    kicker_f = load(SANS_BOLD, sizes["kicker"])
    mast_f = load(SERIF_BOLD, sizes["masthead"])
    date_f = load(SANS_BOLD, sizes["date"])
    lead_head_f = load(SERIF_BOLD, sizes["lead_head"])
    lead_sum_f = load(SANS, sizes["lead_sum"])
    head_f = load(SANS_BOLD, sizes["head"])
    sum_f = load(SANS, sizes["summary"])
    tag_f = load(SANS_BOLD, sizes["tag"])
    foot_f = load(SANS, sizes["footer"])

    y = 20
    y = draw_centered(draw, wrapped["kicker"], kicker_f, y, GREY, 4)
    y += 8
    y = draw_centered(draw, wrapped["masthead"], mast_f, y, INK, 4)
    y += 5
    y = draw_centered(draw, wrapped["date"], date_f, y, INK, 4)
    y += 12
    draw.rectangle([MARGIN, y, PAGE - MARGIN, y + 3], fill=INK)
    y += 3 + 5
    draw.rectangle([MARGIN, y, PAGE - MARGIN, y + 1], fill=INK)
    y += 1 + 14

    lead = data["stories"][0]
    lead_top = y
    draw.rectangle([MARGIN, lead_top, MARGIN + 6, lead_top + lead_h], fill=tuple(lead["color"]))
    x = MARGIN + 22
    y = draw_lines(draw, wrapped["lead_tag"], tag_f, x, y, tuple(lead["color"]), 2)
    y += 5
    y = draw_lines(draw, wrapped["lead_head"], lead_head_f, x, y, INK, 6)
    y += 6
    y = draw_lines(draw, wrapped["lead_sum"], lead_sum_f, x, y, INK, 5)
    y = lead_top + lead_h + 14
    draw.rectangle([MARGIN, y, PAGE - MARGIN, y + 1], fill=FAINT)
    y += 1 + 12

    for story, item in zip(data["stories"][1:], wrapped["stories"]):
        y = draw_lines(draw, [item["tag"]], tag_f, MARGIN, y, tuple(story["color"]), 2)
        y += 4
        y = draw_lines(draw, item["head"], head_f, MARGIN, y, INK, 4)
        y += 4
        y = draw_lines(draw, item["sum"], sum_f, MARGIN, y, INK, 4)
        y += 26

    draw.rectangle([MARGIN, y, PAGE - MARGIN, y + 1], fill=FAINT)
    y += 1 + 8
    y = draw_centered(draw, wrapped["footer"], foot_f, y, GREY, 3)

    out = HERE / "entry.png"
    img.save(out)
    print(f"wrote {out} ({out.stat().st_size} bytes); measured total={total}, content ends y={y}")


if __name__ == "__main__":
    main()
