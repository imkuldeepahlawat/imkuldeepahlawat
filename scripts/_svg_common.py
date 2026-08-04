"""Shared constants and helpers for the hero-asset generators
(prep_photo.py, make_ascii_svg.py, make_wordmark_svg.py).
"""

import xml.sax.saxutils as _saxutils

# --- character grid geometry -------------------------------------------------
# Monospace glyph cells render roughly 1.8x taller than wide, so a naive
# COLS x COLS grid looks vertically squished. FONT_ASPECT corrects for it when
# deriving ROWS from COLS and the target image aspect ratio.
FONT_ASPECT = 0.55

# Pixel size of one character cell in the output SVG (2:1 w:h, matches a
# typical monospace font metric at this point size).
CHAR_W = 7
CHAR_H = 14

# --- ASCII luminance ramp -----------------------------------------------------
# Paul Bourke's standard 10-level ramp: sparse (dark) -> dense (bright).
# None of these characters are XML-special, but we still escape defensively.
RAMP = " .:-=+*#%@"

# --- color palette -------------------------------------------------------------
# Single restrained accent, matches GitHub's dark-theme accent blue and the
# rest of the README's existing widget theme (bg_color=0D1117 everywhere else).
FACE_COLOR = "#58a6ff"
FACE_RGB = (0x58, 0xA6, 0xFF)
DEPTH_COLOR = "#0a1428"
DEPTH_RGB = (0x0A, 0x14, 0x28)

MONOSPACE_STACK = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# Non-breaking space entity — used instead of a literal space so SVG's default
# xml:space whitespace-collapsing behavior can't corrupt column alignment.
NBSP = "&#160;"


def xml_escape(text):
    """Escape text for safe inclusion inside SVG element content."""
    return _saxutils.escape(text)


def lerp_color(rgb_a, rgb_b, t):
    """Linearly interpolate between two (r, g, b) tuples at t in [0, 1]."""
    r = round(rgb_a[0] + (rgb_b[0] - rgb_a[0]) * t)
    g = round(rgb_a[1] + (rgb_b[1] - rgb_a[1]) * t)
    b = round(rgb_a[2] + (rgb_b[2] - rgb_a[2]) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def rows_for(cols, aspect_w, aspect_h):
    """Derive character-grid row count from column count + target aspect,
    correcting for monospace glyph cells being taller than they are wide.
    """
    return round(cols * (aspect_h / aspect_w) * FONT_ASPECT)
