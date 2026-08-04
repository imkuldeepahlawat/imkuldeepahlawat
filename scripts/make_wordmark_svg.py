#!/usr/bin/env python3
"""Render the name as a terminal "binary decode" wordmark: each character
flickers through a couple of random 0/1 digits before locking into place
(left to right), then a blinking cursor settles at the end. Flat, single
color, monospace -- no fake 3D, no isometric blocks.

Usage:
    python scripts/make_wordmark_svg.py --mode decode
                                         [--text "KULDEEP AHLAWAT"]
                                         [--out dist/wordmark.svg]
                                         [--color #58a6ff]
"""

import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _svg_common import FACE_COLOR, MONOSPACE_STACK, xml_escape  # noqa: E402

FONT_SIZE = 56
CHAR_ADV = 34  # monospace bold advance width at FONT_SIZE
LINE_H = 68
PAD = 18

FLASH_WINDOW_MS = 55  # how long each binary digit flashes before the next
FLASHES_PER_CHAR = 2  # how many random digits flicker before the real one
STAGGER_MS = 70  # delay added per character position (left -> right)
INITIAL_DELAY_MS = 30  # first character must not start at exactly 0ms --
# an animation-delay of 0 on the very first paint leaves some renderers
# (confirmed via a real headless-Chrome render, not just a static check)
# stuck showing the last flash digit instead of resolving to the final
# character, while every other (nonzero-delay) character resolves fine.

BINARY_DIGITS = "01"


def build_lines(text):
    """One line per space-separated word (short names stay readable at a
    large font size, and a ragged left edge reads more like a terminal
    dump than a centered logo).
    """
    return text.split()


def char_layer(x, y, delay, char, css_class):
    return (
        f'<tspan class="{css_class}" x="{x}" y="{y}" '
        f'style="animation-delay:{delay}ms">{xml_escape(char)}</tspan>'
    )


def build_svg(lines, color):
    rng = random.Random(42)  # deterministic output across regenerations
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
            base_delay = INITIAL_DELAY_MS + col * STAGGER_MS
            for flash_i in range(FLASHES_PER_CHAR):
                digit = rng.choice(BINARY_DIGITS)
                delay = base_delay + flash_i * FLASH_WINDOW_MS
                layers.append(char_layer(x, y, delay, digit, "flash"))
            final_delay = base_delay + FLASHES_PER_CHAR * FLASH_WINDOW_MS
            layers.append(char_layer(x, y, final_delay, ch, "final"))
            last_char_end_delay = max(last_char_end_delay, final_delay)
            line_col += 1
            col += 1
        if row == len(lines) - 1:
            cursor_x = PAD + line_col * CHAR_ADV + 4
            cursor_y = y

    cursor_delay = last_char_end_delay + 150

    css = f"""
    text {{ font-family: {MONOSPACE_STACK}; font-size: {FONT_SIZE}px; font-weight: 700; fill: {color}; }}
    .flash {{ opacity: 0; animation: flash {FLASH_WINDOW_MS}ms steps(1, end) forwards; fill-opacity: 0.55; }}
    @keyframes flash {{ 0% {{ opacity: 0; }} 15% {{ opacity: 1; }} 85% {{ opacity: 1; }} 100% {{ opacity: 0; }} }}
    .final {{ opacity: 0; animation: lock 10ms steps(1, end) forwards; }}
    @keyframes lock {{ to {{ opacity: 1; }} }}
    .cursor {{
      opacity: 0;
      animation: appear 10ms steps(1, end) {cursor_delay}ms forwards,
                 blink 1s steps(1, end) {cursor_delay}ms infinite;
    }}
    @keyframes appear {{ to {{ opacity: 1; }} }}
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
    global FLASHES_PER_CHAR, STAGGER_MS
    if args.mode == "static":
        FLASHES_PER_CHAR = 0
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
