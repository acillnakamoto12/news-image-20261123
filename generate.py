#!/usr/bin/env python3
"""Render the front page for Monday 23 November 2026 from news.json.

news.json beside this file holds the six verified stories of the day.
This script paints them as a 1024x1024 newspaper front page (entry.png)
using Pillow only -- no network, no randomness, so two runs produce
identical bytes.

The page is composed before it is painted. `compose_page` turns the
stories into a flat list of rows -- paragraphs, rules and one lead
block -- each row already wrapped with the real fonts, so its height is
exact. `fit_page` shrinks the body type a point at a time until the
rows fit the height budget; only then does `Renderer` walk the rows and
paint them. Measuring first and painting second is what guarantees no
text overlaps and nothing runs off the bottom edge.

Run from anywhere: `python3 generate.py` writes entry.png beside it.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent

# Canvas geometry.
CANVAS = 1024
EDGE = 46
SPAN = CANVAS - 2 * EDGE
PAD_TOP = 20
PAD_BOTTOM = 20
HEIGHT_BUDGET = 1000  # rows plus pads must stay under this

# Palette.
PAPER_RGB = (253, 251, 245)
INK_RGB = (18, 18, 18)
MUTED_RGB = (112, 110, 106)
HAIRLINE_RGB = (205, 200, 188)

TYPEFACES = {
    "serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "sans_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
}

BASE_SIZES = {
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
FLOOR_SUMMARY = 16
STORY_GAP = 26
LEAD_INDENT = 22
BAR_WIDTH = 6


def typeface(face, points):
    """Load one DejaVu face at the requested point size."""
    return ImageFont.truetype(TYPEFACES[face], points)


def fold_lines(draw, text, face, limit):
    """Greedy word wrap: fill each line up to `limit` pixels wide."""
    words = text.split()
    lines = []
    line = ""
    for word in words:
        joined = f"{line} {word}".strip()
        if draw.textlength(joined, font=face) <= limit:
            line = joined
            continue
        if line:
            lines.append(line)
        line = word
    if line:
        lines.append(line)
    return lines


def trim(lines, count):
    """Keep at most `count` lines of a wrapped block."""
    return lines[:count]


def line_pitch(face, extra):
    """Vertical advance of one line: font height plus extra leading."""
    top, bottom = face.getmetrics()
    return top + bottom + extra


def para_height(lines, face, extra):
    """Height of a wrapped block: line pitches minus the last leading."""
    if not lines:
        return 0
    return len(lines) * line_pitch(face, extra) - extra


def part_height(part):
    return para_height(part["lines"], part["face"], part["extra"])


def lead_height(lead):
    """Height of the lead block's text and internal gaps (no bar yet)."""
    total = 0
    for part in lead["parts"][:-1]:
        total += part_height(part) + part["gap_after"]
    return total + part_height(lead["parts"][-1])


def row_height(row):
    """Full height of a row, including the blank space after it."""
    kind = row["kind"]
    if kind == "para":
        return para_height(row["lines"], row["face"], row["extra"]) + row["gap_after"]
    if kind == "rule":
        return row["weight"] + row["gap_after"]
    if kind == "lead":
        return lead_height(row) + row["gap_after"]
    raise ValueError(f"unknown row kind: {kind}")


def para_row(lines, face, rgb, extra, gap_after, centred=False, indent=0):
    return {
        "kind": "para",
        "lines": lines,
        "face": face,
        "rgb": rgb,
        "extra": extra,
        "gap_after": gap_after,
        "centred": centred,
        "indent": indent,
    }


def lead_part(lines, face, rgb, extra, gap_after, indent=LEAD_INDENT):
    return {
        "lines": lines,
        "face": face,
        "rgb": rgb,
        "extra": extra,
        "gap_after": gap_after,
        "indent": indent,
    }


def compose_page(data, draw, sizes):
    """Turn the stories into rows; return (rows, total height)."""
    face = {
        "kicker": typeface("sans_bold", sizes["kicker"]),
        "masthead": typeface("serif", sizes["masthead"]),
        "date": typeface("sans_bold", sizes["date"]),
        "tag": typeface("sans_bold", sizes["tag"]),
        "lead_head": typeface("serif", sizes["lead_head"]),
        "lead_sum": typeface("sans", sizes["lead_sum"]),
        "head": typeface("sans_bold", sizes["head"]),
        "summary": typeface("sans", sizes["summary"]),
        "footer": typeface("sans", sizes["footer"]),
    }

    rows = [
        para_row(
            fold_lines(draw, data["kicker"], face["kicker"], SPAN),
            face["kicker"], MUTED_RGB, 4, 8, centred=True,
        ),
        para_row(
            fold_lines(draw, data["title"], face["masthead"], SPAN),
            face["masthead"], INK_RGB, 4, 5, centred=True,
        ),
        para_row(
            fold_lines(draw, data["date_line"], face["date"], SPAN),
            face["date"], INK_RGB, 4, 12, centred=True,
        ),
        {"kind": "rule", "weight": 3, "rgb": INK_RGB, "gap_after": 5},
        {"kind": "rule", "weight": 1, "rgb": INK_RGB, "gap_after": 14},
    ]

    lead = data["stories"][0]
    lead_rgb = tuple(lead["color"])
    lead_width = SPAN - LEAD_INDENT
    rows.append(
        {
            "kind": "lead",
            "rgb": lead_rgb,
            "gap_after": 14,
            "parts": [
                lead_part([lead["tag"]], face["tag"], lead_rgb, 2, 5),
                lead_part(
                    trim(
                        fold_lines(draw, lead["headline"], face["lead_head"],
                                   lead_width),
                        2,
                    ),
                    face["lead_head"], INK_RGB, 6, 6,
                ),
                lead_part(
                    trim(
                        fold_lines(draw, lead["summary"], face["lead_sum"],
                                   lead_width),
                        2,
                    ),
                    face["lead_sum"], INK_RGB, 5, 0,
                ),
            ],
        }
    )
    rows.append({"kind": "rule", "weight": 1, "rgb": HAIRLINE_RGB, "gap_after": 12})

    for story in data["stories"][1:]:
        rgb = tuple(story["color"])
        head = trim(
            fold_lines(draw, story["headline"], face["head"], SPAN), 2
        )
        # A one-line headline leaves room for two summary lines.
        summary = trim(
            fold_lines(draw, story["summary"], face["summary"], SPAN),
            2 if len(head) == 1 else 1,
        )
        rows.append(para_row([story["tag"]], face["tag"], rgb, 2, 4))
        rows.append(para_row(head, face["head"], INK_RGB, 4, 4))
        rows.append(para_row(summary, face["summary"], INK_RGB, 4, STORY_GAP))

    rows.append({"kind": "rule", "weight": 1, "rgb": HAIRLINE_RGB, "gap_after": 8})
    rows.append(
        para_row(
            fold_lines(draw, data["footer"], face["footer"], SPAN),
            face["footer"], MUTED_RGB, 3, 0, centred=True,
        )
    )

    total = PAD_TOP + sum(row_height(row) for row in rows) + PAD_BOTTOM
    return rows, total


def fit_page(data, draw):
    """Compose the page, shrinking body type until it fits the budget."""
    sizes = dict(BASE_SIZES)
    rows, total = compose_page(data, draw, sizes)
    while total > HEIGHT_BUDGET and sizes["summary"] > FLOOR_SUMMARY:
        sizes["summary"] -= 1
        sizes["head"] -= 1
        sizes["lead_sum"] -= 1
        rows, total = compose_page(data, draw, sizes)
    if total > HEIGHT_BUDGET:
        # Never paint an overflowing page: fail loudly instead so the
        # bad image is noticed here, not at submission time.
        raise SystemExit(
            f"page still {total}px tall at minimum body size "
            f"(budget {HEIGHT_BUDGET}); refusing to overflow"
        )
    return rows, total, sizes


class Renderer:
    """Walks the composed rows and paints them onto the canvas."""

    def __init__(self, draw):
        self.draw = draw
        self.y = PAD_TOP

    def run(self, rows):
        for row in rows:
            if row["kind"] == "para":
                self.paint_para(row)
            elif row["kind"] == "rule":
                self.paint_rule(row)
            elif row["kind"] == "lead":
                self.paint_lead(row)
            else:
                raise ValueError(f"unknown row kind: {row['kind']}")
        return self.y

    def paint_lines(self, lines, face, rgb, extra, centred, indent):
        """Paint one paragraph's lines; advance past its text only."""
        for offset, line in enumerate(lines):
            if centred:
                x = (CANVAS - self.draw.textlength(line, font=face)) / 2
            else:
                x = EDGE + indent
            self.draw.text(
                (x, self.y + offset * line_pitch(face, extra)),
                line, font=face, fill=rgb,
            )
        self.y += para_height(lines, face, extra)

    def paint_para(self, row):
        self.paint_lines(
            row["lines"], row["face"], row["rgb"], row["extra"],
            row["centred"], row["indent"],
        )
        self.y += row["gap_after"]

    def paint_rule(self, row):
        self.draw.rectangle(
            [EDGE, self.y, CANVAS - EDGE, self.y + row["weight"] - 1],
            fill=row["rgb"],
        )
        self.y += row["weight"] + row["gap_after"]

    def paint_lead(self, row):
        body = lead_height(row)
        self.draw.rectangle(
            [EDGE, self.y, EDGE + BAR_WIDTH - 1, self.y + body - 1],
            fill=row["rgb"],
        )
        for part in row["parts"][:-1]:
            self.paint_lines(
                part["lines"], part["face"], part["rgb"], part["extra"],
                False, part["indent"],
            )
            self.y += part["gap_after"]
        last = row["parts"][-1]
        self.paint_lines(
            last["lines"], last["face"], last["rgb"], last["extra"],
            False, last["indent"],
        )
        self.y += row["gap_after"]


def main():
    data = json.loads((BASE / "news.json").read_text())
    img = Image.new("RGB", (CANVAS, CANVAS), PAPER_RGB)
    draw = ImageDraw.Draw(img)

    rows, total, fitted = fit_page(data, draw)
    renderer = Renderer(draw)
    end_y = renderer.run(rows)

    out = BASE / "entry.png"
    img.save(out)
    print(
        f"wrote {out} ({out.stat().st_size} bytes); "
        f"measured total={total}, content ends y={end_y}, "
        f"body sizes head={fitted['head']} summary={fitted['summary']} "
        f"lead_sum={fitted['lead_sum']}"
    )


if __name__ == "__main__":
    main()
