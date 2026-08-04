#!/usr/bin/env python3
"""Render data/contributions.json (see fetch_contributions.py) as a terminal
"commit sparkline": one bar per week, growing up on reveal, framed like a
shell command and its output. Deliberately not a clone of GitHub's own
day-by-day calendar grid -- a single compact row instead.

Usage:
    python scripts/make_contrib_graph.py [--in data/contributions.json]
                                          [--out dist/contrib-heatmap.svg]
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _svg_common import FACE_COLOR, MONOSPACE_STACK  # noqa: E402

BAR_W = 6
BAR_GAP = 3
BAR_STEP = BAR_W + BAR_GAP
MAX_BAR_H = 60
PAD = 16
HEADER_H = 28
FOOTER_H = 34

DIM = "#3d5a80"  # empty/zero week
MUTED = "#7d8590"
TEXT = "#c9d1d9"

GROW_DUR = 0.35
STAGGER = 0.012


def weekly_totals(days):
    """Bucket daily counts into ISO-week totals, oldest first."""
    weeks = []
    current_week = []
    for d in days:
        current_week.append(d["count"])
        if len(current_week) == 7:
            weeks.append(sum(current_week))
            current_week = []
    if current_week:
        weeks.append(sum(current_week))
    return weeks


def render(data):
    weeks = weekly_totals(data["days"])
    peak = max(weeks) if weeks else 1
    peak = max(peak, 1)

    art_w = len(weeks) * BAR_STEP - BAR_GAP
    canvas_w = PAD * 2 + art_w
    canvas_h = HEADER_H + MAX_BAR_H + FOOTER_H + PAD

    css = f"""
    text {{ font-family: {MONOSPACE_STACK}; }}
    .bar {{ transform-box: fill-box; transform-origin: bottom; transform: scaleY(0); animation: grow {GROW_DUR}s ease-out forwards; }}
    @keyframes grow {{ to {{ transform: scaleY(1); }} }}
    """.strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" '
        f'width="{canvas_w}" height="{canvas_h}">',
        f"<style>{css}</style>",
        f'<text x="{PAD}" y="{PAD + 6}" font-size="12" fill="{MUTED}">'
        f'<tspan fill="{FACE_COLOR}">$</tspan> git log --since=1.year --format=%cd | uniq -c -w10</text>',
    ]

    baseline = HEADER_H + MAX_BAR_H
    for i, total in enumerate(weeks):
        x = PAD + i * BAR_STEP
        h = 2 if total == 0 else max(3, round((total / peak) * MAX_BAR_H))
        y = baseline - h
        color = DIM if total == 0 else FACE_COLOR
        delay = i * STAGGER
        plural = "" if total == 1 else "s"
        parts.append(
            f'<rect class="bar" x="{x}" y="{y}" width="{BAR_W}" height="{h}" rx="1" '
            f'fill="{color}" style="animation-delay:{delay:.3f}s">'
            f"<title>week of {data['days'][min(i * 7, len(data['days']) - 1)]['date']}: "
            f"{total} commit{plural}</title></rect>"
        )

    total = data["total_contributions"]
    streak = data["current_streak"]
    footer_y = baseline + 26
    parts.append(
        f'<text x="{PAD}" y="{footer_y}" font-size="12" fill="{MUTED}">'
        f'<tspan fill="{FACE_COLOR}">$</tspan> echo "'
        f'<tspan fill="{TEXT}" font-weight="700">{total:,}</tspan> contributions, '
        f'<tspan fill="{TEXT}" font-weight="700">{streak}</tspan>-day streak"</text>'
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
