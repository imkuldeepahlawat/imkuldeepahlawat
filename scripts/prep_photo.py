#!/usr/bin/env python3
"""Prepare a source photo for ASCII-art conversion.

Crops/resizes a photo down to the exact character grid that
make_ascii_svg.py will render, with the sharpening/contrast steps
ASCII legibility depends on.

Usage:
    python scripts/prep_photo.py <photo> [--cols 64] [--aspect 1:1]
                                  [--crop top] [--out assets/.cache/photo_prepped.png]
                                  [--no-preview]
"""

import argparse
import os
import sys

from PIL import Image, ImageFilter, ImageOps

sys.path.insert(0, os.path.dirname(__file__))
from _svg_common import RAMP, rows_for  # noqa: E402


def parse_aspect(spec):
    w, h = spec.split(":")
    return float(w), float(h)


def crop_to_aspect(img, aspect_w, aspect_h, crop="top"):
    """Crop img to the target aspect ratio before any resizing."""
    target_ratio = aspect_w / aspect_h
    w, h = img.size
    current_ratio = w / h

    if current_ratio > target_ratio:
        # image is wider than target -> crop width, keep full height, center horizontally
        new_w = round(h * target_ratio)
        left = (w - new_w) // 2
        box = (left, 0, left + new_w, h)
    else:
        # image is taller than target -> crop height
        new_h = round(w / target_ratio)
        if crop == "top":
            top = 0
        else:
            top = (h - new_h) // 2
        box = (0, top, w, top + new_h)

    return img.crop(box)


def terminal_preview(img):
    """Print a quick ASCII rendering of img (already at grid resolution) to stdout."""
    cols, rows = img.size
    pixels = img.load()
    lines = []
    for y in range(rows):
        row_chars = []
        for x in range(cols):
            lum = pixels[x, y]
            char = RAMP[min(9, lum * 10 // 256)]
            row_chars.append(char)
        lines.append("".join(row_chars))
    print("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("photo", help="path to the source photo")
    parser.add_argument("--cols", type=int, default=64, help="character grid width")
    parser.add_argument("--aspect", default="1:1", help="target crop aspect, e.g. 1:1")
    parser.add_argument("--crop", choices=["top", "center"], default="top",
                         help="crop bias when trimming height (default: top, biases "
                              "toward keeping headroom for head-and-shoulders portraits)")
    parser.add_argument("--out", default="assets/.cache/photo_prepped.png",
                         help="where to write the prepped grayscale grid PNG")
    parser.add_argument("--no-preview", action="store_true",
                         help="skip printing the terminal ASCII preview")
    args = parser.parse_args()

    aspect_w, aspect_h = parse_aspect(args.aspect)
    cols = args.cols
    rows = rows_for(cols, aspect_w, aspect_h)

    img = Image.open(args.photo)
    img = ImageOps.exif_transpose(img)  # phone photos carry EXIF orientation
    img = img.convert("L")  # grayscale

    img = crop_to_aspect(img, aspect_w, aspect_h, crop=args.crop)

    # Sharpen BEFORE downsampling — LANCZOS resize to a small grid blurs away
    # exactly the edge contrast that makes ASCII art legible.
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    # Resize to the actual character grid — one pixel per character cell.
    img = img.resize((cols, rows), Image.Resampling.LANCZOS)

    # Stretch the luminance histogram after downsampling, for max contrast
    # in the small grid the ramp mapping will read from.
    img = ImageOps.autocontrast(img, cutoff=2)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    img.save(args.out)
    print(f"wrote {args.out} ({cols}x{rows} grid)", file=sys.stderr)

    if not args.no_preview:
        terminal_preview(img)


if __name__ == "__main__":
    main()
