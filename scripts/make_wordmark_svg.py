#!/usr/bin/env python3
"""Render the name as a terminal "glitch decode" wordmark: each character
flickers on/off a couple of times before settling solid, left to right,
then a blinking cursor holds at the end. Flat, single color, monospace --
no fake 3D, no isometric blocks.

One element per character (not stacked candidate glyphs) -- an earlier
version stacked multiple tspans (flashing digits + the real character) at
identical coordinates, and a real headless-Chrome render showed that
approach getting stuck on the wrong stacked element for the first
character of a line, regardless of its delay. This version reuses the
exact single-element opacity-stagger technique already proven reliable
across 2000+ cells in make_ascii_svg.py.

Usage:
    python scripts/make_wordmark_svg.py --mode decode
                                         [--text "KULDEEP AHLAWAT"]
                                         [--out dist/wordmark.svg]
                                         [--color #58a6ff]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _svg_common import FACE_COLOR, MONOSPACE_STACK, xml_escape  # noqa: E402

FONT_SIZE = 56
CHAR_ADV = 34  # monospace bold advance width at FONT_SIZE
LINE_H = 68
PAD = 18

STAGGER_MS = 45  # delay added per character position (left -> right)
INITIAL_DELAY_MS = 60  # small head start before the first character flickers
FLICKER_DUR_MS = 260  # each character's own on/off/on/off/settle duration


def build_lines(text):
    """One line per space-separated word (short names stay readable at a
    large font size, and a ragged left edge reads more like a terminal
    dump than a centered logo).
    """
    return text.split()


def build_svg(lines, color):
    max_len = max(len(line) for line in lines)
    canvas_w = PAD * 2 + max_len * CHAR_ADV
    canvas_h = PAD * 2 + len(lines) * LINE_H

    layers = []
    last_char_end_delay = 0
    cursor_x = PAD
    cursor_y = PAD + len(lines) * LINE_H - LINE_H * 0.3

    col = 0
    for row, line in enumerate(lines):
        y = PAD + (row + 1) * LINE_H - LINE_H * 0.35
        line_col = 0
        for ch in line:
            x = PAD + line_col * CHAR_ADV
            delay = INITIAL_DELAY_MS + col * STAGGER_MS
            layers.append(
                f'<tspan class="ch" x="{x}" y="{y}" '
                f'style="animation-delay:{delay}ms">{xml_escape(ch)}</tspan>'
            )
            last_char_end_delay = max(last_char_end_delay, delay + FLICKER_DUR_MS)
            line_col += 1
            col += 1
        if row == len(lines) - 1:
            cursor_x = PAD + line_col * CHAR_ADV + 4
            cursor_y = y

    cursor_delay = last_char_end_delay + 150

    css = f"""
    text {{ font-family: {MONOSPACE_STACK}; font-size: {FONT_SIZE}px; font-weight: 700; fill: {color}; }}
    .ch {{ opacity: 0; animation: flicker {FLICKER_DUR_MS}ms linear forwards; }}
    @keyframes flicker {{
      0%   {{ opacity: 0; }}
      12%  {{ opacity: 1; }}
      24%  {{ opacity: 0; }}
      36%  {{ opacity: 1; }}
      48%  {{ opacity: 0.3; }}
      60%  {{ opacity: 1; }}
      100% {{ opacity: 1; }}
    }}
    .cursor {{
      opacity: 0;
      animation: blink 1s steps(1, end) {cursor_delay}ms infinite;
    }}
    @keyframes blink {{ 0%, 49% {{ opacity: 1; }} 50%, 100% {{ opacity: 0; }} }}
    """.strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" '
        f'width="{canvas_w}" height="{canvas_h}">',
        f"<style>{css}</style>",
        "<text>",
        *layers,
        f'<tspan class="cursor" x="{cursor_x}" y="{cursor_y}">_</tspan>',
        "</text>",
        "</svg>",
    ]
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["decode", "static"], default="decode")
    parser.add_argument("--text", default="KULDEEP AHLAWAT")
    parser.add_argument("--out", default="dist/wordmark.svg")
    parser.add_argument("--color", default=FACE_COLOR)
    args = parser.parse_args()

    lines = build_lines(args.text)
    global STAGGER_MS
    if args.mode == "static":
        STAGGER_MS = 0

    svg = build_svg(lines, args.color)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {args.out} (mode={args.mode})", file=sys.stderr)


if __name__ == "__main__":
    main()
