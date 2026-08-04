#!/usr/bin/env python3
"""Render a prepped grayscale photo grid (see prep_photo.py) as a
monochrome, "types in" animated ASCII-art SVG.

Usage:
    python scripts/make_ascii_svg.py [--in assets/.cache/photo_prepped.png]
                                      [--out dist/kuldeep-ascii.svg]
                                      [--color #58a6ff]
"""

import argparse
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from _svg_common import (  # noqa: E402
    CHAR_H,
    CHAR_W,
    FACE_COLOR,
    MONOSPACE_STACK,
    NBSP,
    RAMP,
    xml_escape,
)

# Row-major stagger: reveal reads top-to-bottom, left-to-right, like a
# terminal printing an image row by row. Kept short (~1.8s total for a
# 64x35 grid) so it settles quickly rather than still being mid-reveal on
# a quick glance.
DELAY_MS_PER_CELL = 0.8


def image_to_grid(img):
    """Return the image as a list of rows of ramp characters."""
    cols, rows = img.size
    pixels = img.load()
    grid = []
    for y in range(rows):
        row = []
        for x in range(cols):
            lum = pixels[x, y]
            row.append(RAMP[min(9, lum * 10 // 256)])
        grid.append(row)
    return grid


def build_row_markup(row_chars, row_index, cols):
    """Build the mixed text/tspan content for one row.

    Space characters are emitted as plain adjacent NBSP text (no wrapper,
    no animation delay — they're invisible regardless of opacity and this
    keeps the tspan count down). Every other character gets its own
    animated tspan with a stagger delay based on reading position.
    """
    parts = []
    for col_index, ch in enumerate(row_chars):
        if ch == " ":
            parts.append(NBSP)
        else:
            delay = round((row_index * cols + col_index) * DELAY_MS_PER_CELL)
            parts.append(
                f'<tspan class="ch" style="animation-delay:{delay}ms">'
                f"{xml_escape(ch)}</tspan>"
            )
    return "".join(parts)


def build_svg(grid, color):
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    width = cols * CHAR_W
    height = rows * CHAR_H

    text_rows = []
    for row_index, row_chars in enumerate(grid):
        y = row_index * CHAR_H + CHAR_H
        markup = build_row_markup(row_chars, row_index, cols)
        text_rows.append(f'<text x="0" y="{y}">{markup}</text>')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve"
     viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <style>
    text {{
      font-family: {MONOSPACE_STACK};
      font-size: {CHAR_H}px;
      fill: {color};
      white-space: pre;
    }}
    .ch {{
      opacity: 0;
      animation: typeIn 10ms steps(1, end) forwards;
    }}
    @keyframes typeIn {{
      to {{ opacity: 1; }}
    }}
  </style>
{chr(10).join(text_rows)}
</svg>
"""
    return svg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="in_path", default="assets/.cache/photo_prepped.png",
                         help="prepped grayscale grid PNG from prep_photo.py")
    parser.add_argument("--out", default="dist/kuldeep-ascii.svg")
    parser.add_argument("--color", default=FACE_COLOR)
    args = parser.parse_args()

    img = Image.open(args.in_path).convert("L")
    grid = image_to_grid(img)
    svg = build_svg(grid, args.color)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
