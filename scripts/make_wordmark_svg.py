#!/usr/bin/env python3
"""Render an extruded 3D ASCII wordmark as an animated SVG: wipes in
left-to-right, then (in --mode rock) rocks gently on its vertical axis.

Usage:
    python scripts/make_wordmark_svg.py --mode rock
                                         [--text "KULDEEP SINGH"]
                                         [--font isometric1]
                                         [--out dist/wordmark.svg]
                                         [--color #58a6ff]
"""

import argparse
import os
import sys

import pyfiglet

sys.path.insert(0, os.path.dirname(__file__))
from _svg_common import (  # noqa: E402
    CHAR_H,
    CHAR_W,
    DEPTH_RGB,
    FACE_COLOR,
    FACE_RGB,
    MONOSPACE_STACK,
    NBSP,
    lerp_color,
    xml_escape,
)

# Fonts to try, in order, in case a given install is missing one.
FONT_FALLBACK_CHAIN = ["isometric1", "3-d", "block", "banner3-D"]

DEPTH_LAYERS = 5  # + 1 face layer = 6 total, per design spec
DEPTH_OFFSET_PX = 2  # per-layer diagonal offset step


def render_font(text, requested_font):
    """Render each space-separated word of `text` on its own figlet line
    (measured: a single-line "KULDEEP SINGH" via isometric1 is ~171x11, a
    ~15:1 unusable banner; stacking each word is ~94x22, ~4:1 and a much
    cleaner two-line name lockup). Returns (lines, font_used).
    """
    chain = [requested_font] + [f for f in FONT_FALLBACK_CHAIN if f != requested_font]
    last_error = None
    for font_name in chain:
        try:
            fig = pyfiglet.Figlet(font=font_name, width=500)
        except pyfiglet.FontNotFound as e:
            last_error = e
            continue

        lines = []
        for word in text.split():
            block = fig.renderText(word)
            lines.extend(block.rstrip("\n").split("\n"))

        max_width = max(len(line) for line in lines)
        lines = [line.ljust(max_width) for line in lines]
        return lines, font_name

    raise RuntimeError(f"no usable font found in {chain}: {last_error}")


def build_row_text(line):
    """Escape a figlet line for SVG text content, preserving spaces as NBSP
    so SVG's default whitespace collapsing can't corrupt alignment.
    """
    return "".join(NBSP if ch == " " else xml_escape(ch) for ch in line)


def build_svg(lines, mode, color):
    rows = len(lines)
    cols = len(lines[0]) if rows else 0
    content_w = cols * CHAR_W
    content_h = rows * CHAR_H

    max_offset = DEPTH_LAYERS * DEPTH_OFFSET_PX
    total_w = content_w + max_offset
    total_h = content_h + max_offset
    cx = total_w / 2
    cy = total_h / 2

    glyph_rows = []
    for row_index, line in enumerate(lines):
        y = row_index * CHAR_H + CHAR_H
        glyph_rows.append(f'<text x="0" y="{y}">{build_row_text(line)}</text>')
    glyph_markup = "\n    ".join(glyph_rows)

    # Depth layers: furthest/darkest first, face layer (offset 0, FACE_COLOR)
    # drawn last so it sits on top. Each layer reuses the same glyph content
    # via <use>+currentColor rather than duplicating the text markup.
    layers = []
    for d in range(DEPTH_LAYERS, 0, -1):
        offset = d * DEPTH_OFFSET_PX
        depth_color = lerp_color(FACE_RGB, DEPTH_RGB, d / DEPTH_LAYERS)
        layers.append(
            f'<g transform="translate({offset},{offset})" style="color:{depth_color}">'
            f'<use href="#glyphs" xlink:href="#glyphs" fill="currentColor"/></g>'
        )
    layers.append(
        f'<g transform="translate(0,0)" style="color:{color}">'
        f'<use href="#glyphs" xlink:href="#glyphs" fill="currentColor"/></g>'
    )
    layers_markup = "\n        ".join(layers)

    if mode == "rock":
        rock_animations = """<animateTransform attributeName="transform" type="skewX" additive="sum"
            begin="wipeAnim.end" dur="5s" repeatCount="indefinite"
            keyTimes="0;0.25;0.5;0.75;1" values="0;6;0;-6;0" />
          <animateTransform attributeName="transform" type="scale" additive="sum"
            begin="wipeAnim.end" dur="5s" repeatCount="indefinite"
            keyTimes="0;0.25;0.5;0.75;1" values="1,1;0.94,1;1,1;0.94,1;1,1" />"""
    else:
        rock_animations = ""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     xml:space="preserve" viewBox="0 0 {total_w} {total_h}" width="{total_w}" height="{total_h}">
  <style>
    text {{
      font-family: {MONOSPACE_STACK};
      font-size: {CHAR_H}px;
      white-space: pre;
    }}
  </style>
  <defs>
    <clipPath id="wipeClip">
      <rect x="0" y="0" width="0" height="{total_h}">
        <animate id="wipeAnim" attributeName="width" from="0" to="{total_w}"
          dur="1.2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.25 0.1 0.25 1" />
      </rect>
    </clipPath>
    <g id="glyphs">
    {glyph_markup}
    </g>
  </defs>
  <g clip-path="url(#wipeClip)">
    <!-- pivot-around-center: translate(cx,cy) -> skew/scale (identity origin) -> translate(-cx,-cy) -->
    <g transform="translate({cx},{cy})">
      <g>
        {rock_animations}
        <g transform="translate({-cx},{-cy})">
        {layers_markup}
        </g>
      </g>
    </g>
  </g>
</svg>
"""
    return svg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["rock", "static"], default="rock")
    parser.add_argument("--text", default="KULDEEP AHLAWAT")
    parser.add_argument("--font", default="isometric1")
    parser.add_argument("--out", default="dist/wordmark.svg")
    parser.add_argument("--color", default=FACE_COLOR)
    args = parser.parse_args()

    lines, font_used = render_font(args.text, args.font)
    if font_used != args.font:
        print(f"warning: font '{args.font}' unavailable, used '{font_used}' instead", file=sys.stderr)

    svg = build_svg(lines, args.mode, args.color)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {args.out} (font={font_used}, mode={args.mode})", file=sys.stderr)


if __name__ == "__main__":
    main()
