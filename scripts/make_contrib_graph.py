#!/usr/bin/env python3
"""Render data/contributions.json (see fetch_contributions.py) as a
GitHub-style contribution heatmap: the classic 53-week x 7-day grid, boxes
revealed once via a diagonal cascade, monochrome-blue to match the rest of
the hero pipeline (portrait/wordmark use the same #58a6ff accent).

Usage:
    python scripts/make_contrib_graph.py [--in data/contributions.json]
                                          [--out dist/contrib-heatmap.svg]
"""

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _svg_common import FACE_COLOR, MONOSPACE_STACK  # noqa: E402

# Dark -> bright single-hue ramp (blue, not GitHub's green) for 5 activity levels.
PALETTE = ["#0d1117", "#122b4a", "#1c4d80", "#2f7fd6", FACE_COLOR]

CELL = 11
GAP = 3
STEP = CELL + GAP
PAD = 16
LEFT_LABEL_W = 26
TOP_LABEL_H = 16

MUTED = "#7d8590"
TEXT = "#c9d1d9"

COL_DELAY = 0.015  # per-column stagger (left -> right)
ROW_DELAY = 0.04  # per-row stagger (top -> bottom), diagonal cascade
CELL_DUR = 0.4


def level_for(count):
    if count == 0:
        return 0
    if count <= 3:
        return 1
    if count <= 8:
        return 2
    if count <= 15:
        return 3
    return 4


def build_grid(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    lead_pad = (first.weekday() + 1) % 7  # week starts Sunday
    grid, col = [], [None] * lead_pad
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        weekday = (date.weekday() + 1) % 7
        while len(col) < weekday:
            col.append(None)
        col.append((d["date"], d["count"], level_for(d["count"])))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        col += [None] * (7 - len(col))
        grid.append(col)
    return grid


def render(data):
    days = data["days"]
    grid = build_grid(days)
    art_w = len(grid) * STEP
    art_h = 7 * STEP

    month_labels, seen = [], set()
    for ci, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            date = datetime.date.fromisoformat(cell[0])
            key = (date.year, date.month)
            if key not in seen and date.day <= 7:
                seen.add(key)
                month_labels.append((ci, date.strftime("%b")))
            break

    canvas_w = PAD + LEFT_LABEL_W + art_w + PAD
    footer_h = 34
    canvas_h = TOP_LABEL_H + art_h + footer_h + PAD

    css = f"""
    @keyframes reveal {{ to {{ opacity: 1; }} }}
    .cell {{ opacity: 0; animation: reveal {CELL_DUR:.2f}s ease-out forwards; }}
    """.strip()

    grid_top = TOP_LABEL_H
    grid_left = PAD + LEFT_LABEL_W

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" '
        f'width="{canvas_w}" height="{canvas_h}" font-family="{MONOSPACE_STACK}">',
        f"<style>{css}</style>",
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="8" fill="#0d1117"/>',
    ]

    for ci, label in month_labels:
        x = grid_left + ci * STEP
        parts.append(f'<text x="{x}" y="{TOP_LABEL_H - 4}" fill="{MUTED}" font-size="9">{label}</text>')

    for wi, wname in [(1, "M"), (3, "W"), (5, "F")]:
        y = grid_top + wi * STEP + CELL * 0.78
        parts.append(f'<text x="{PAD}" y="{y:.1f}" fill="{MUTED}" font-size="8">{wname}</text>')

    for ci, column in enumerate(grid):
        gx = grid_left + ci * STEP
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            gy = grid_top + ri * STEP
            delay = ci * COL_DELAY + ri * ROW_DELAY
            plural = "" if count == 1 else "s"
            parts.append(
                f'<rect class="cell" x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{PALETTE[lvl]}" style="animation-delay:{delay:.3f}s">'
                f"<title>{date_s}: {count} contribution{plural}</title></rect>"
            )

    leg_y = grid_top + art_h + 8
    leg_x = canvas_w - PAD - (len(PALETTE) * CELL + 60)
    parts.append(f'<text x="{leg_x}" y="{leg_y + CELL * 0.8:.1f}" fill="{MUTED}" font-size="9" text-anchor="end">Less</text>')
    lx = leg_x + 6
    for color in PALETTE:
        parts.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL - 1}" height="{CELL - 1}" rx="2" fill="{color}"/>')
        lx += CELL
    parts.append(f'<text x="{lx + 4}" y="{leg_y + CELL * 0.8:.1f}" fill="{MUTED}" font-size="9">More</text>')

    stats_y = leg_y + CELL + 20
    total = data["total_contributions"]
    streak = data["current_streak"]
    parts.append(
        f'<text x="{PAD}" y="{stats_y}" font-size="12" fill="{TEXT}">'
        f'<tspan font-weight="700" fill="{FACE_COLOR}">{total:,}</tspan>'
        f'<tspan fill="{MUTED}"> contributions in the last year'
        f'   &#183;   current streak </tspan>'
        f'<tspan font-weight="700" fill="{FACE_COLOR}">{streak} day{"" if streak == 1 else "s"}</tspan></text>'
    )

    parts.append("</svg>")
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="in_path", default="data/contributions.json")
    parser.add_argument("--out", default="dist/contrib-heatmap.svg")
    args = parser.parse_args()

    data = json.load(open(args.in_path))
    svg = render(data)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w") as f:
        f.write(svg)
    print(f"wrote {args.out} ({len(svg)} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
