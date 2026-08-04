# How the hero assets are built

Technical notes for `scripts/prep_photo.py`, `scripts/make_ascii_svg.py`, and
`scripts/make_wordmark_svg.py` — the pipeline behind the README's hero
section (ASCII portrait + 3D wordmark).

## Constraints that shaped every decision here

GitHub does not execute embedded HTML or JavaScript inside `README.md` — a
README can only reference *images*. So all of the animation (typing reveal,
extrusion, wipe-in, rocking) has to live inside the SVG files themselves,
using SVG-native animation only: SMIL (`<animate>`, `<animateTransform>`) or
CSS `@keyframes` declared in an embedded `<style>` block. No `<script>` tags
anywhere — even inside an SVG loaded via `<img>`, embedded scripts don't
execute.

The generated SVGs are published to the repo's `output` branch (same
mechanism `.github/workflows/snake.yml` already uses for `snake.svg`) and
embedded via `raw.githubusercontent.com` URLs, rather than committed to
`main`. This keeps `main`'s history free of binary SVG diffs every time the
photo or wordmark text/font gets retuned.

## Glyph shapes: pyfiglet + isometric1

`make_wordmark_svg.py` renders block letters with `pyfiglet` (pure Python,
no network calls) using the `isometric1` font, with a fallback chain
(`isometric1` → `3-d` → `block` → `banner3-D`) in case a given install is
missing one.

Two gotchas found while building this:
- `pyfiglet.Figlet()` defaults to an 80-column wrap width. Long text
  auto-wraps into unwanted stacked blocks unless you pass `width=500`
  explicitly.
- A single-line render of "KULDEEP SINGH" measures ~171×11 characters — an
  unusable ~15:1 banner. Rendering each space-separated word on its own
  figlet line instead ("KULDEEP" / "SINGH") measures ~94×22 — a much
  cleaner two-line name lockup, and the default behavior in the script.

## Extrusion: 6 layered copies

There's no native 3D projection in flat SVG, so the "extruded" look is
faked with 6 stacked copies of the same glyph grid (defined once in
`<defs>` and reused via `<use>` + `fill="currentColor"`, not duplicated 6
times in the markup):

- 5 "depth" layers, each offset `2px * layer_index` diagonally down-right,
  colored by linearly interpolating RGB from `FACE (#58a6ff)` to
  `DEPTH (#0a1428)`.
- 1 "face" layer at zero offset, pure `FACE` color, painted last (on top).

`feDropShadow`/CSS `text-shadow` were deliberately not used — both read as
soft blur, not a solid bevel.

## Wipe-in: SMIL, not CSS

The whole extrusion group sits behind a `<clipPath>` containing a `<rect>`
whose `width` animates `0 → full` via SMIL `<animate>`
(`calcMode="spline"` for an ease-out, `fill="freeze"` to hold revealed).
SMIL is the reliable technique for animating clip-path geometry; CSS
animating a referenced clipPath's child has patchier support.

## Rock loop: pivot-around-center via nested groups

`--mode rock` adds a continuous loop after the wipe finishes
(`begin="wipeAnim.end"`, SMIL event syntax referencing the wipe
animation's id): a synced `skewX` (`0 → 6 → 0 → -6 → 0`) and `scale`
(`1 → 0.94 → 1 → 0.94 → 1`, X-only) via two `additive="sum"`
`animateTransform` elements.

SMIL's `animateTransform` pivots around the local `(0,0)` origin, not
around CSS `transform-origin` (that's a CSS Transforms concept that
doesn't apply to SMIL). To pivot around the wordmark's actual center, the
content is nested three levels deep:

```
<g transform="translate(cx,cy)">        <!-- move origin to center -->
  <g>                                    <!-- receives the two additive
                                              animateTransform elements,
                                              starting from identity -->
    <g transform="translate(-cx,-cy)">  <!-- shift content back -->
      ...6 depth layers...
    </g>
  </g>
</g>
```

This composes to the standard `T(cx,cy) · R · T(-cx,-cy)` pivot formula.

Negative `scaleX` was deliberately avoided (it would mirror-flip the text
at the animation's extreme, reading as broken glyphs) in favor of this
skew + subtle-narrow combination, which never crosses zero.

## Regenerating

```
python scripts/prep_photo.py assets/photo.jpg
python scripts/make_ascii_svg.py                  # -> dist/kuldeep-ascii.svg
python scripts/make_wordmark_svg.py --mode rock    # -> dist/wordmark.svg
open dist/wordmark.svg                             # local file:// preview
```

Useful knobs: `--text`, `--font`, `--mode {rock,static}` on the wordmark
script; `--cols`, `--aspect`, `--crop {top,center}` on `prep_photo.py`.

## Known limitations

- No `prefers-reduced-motion` support yet — SMIL animations aren't
  controlled by CSS media queries at all, so respecting that preference
  would mean switching the rock loop to CSS `@keyframes`/`animation`
  instead of SMIL.
- Height-matching between the two hero panels (portrait ~1:1, wordmark
  ~2:1) is an empirical last-mile step — they won't land at exactly the
  same rendered height without one of them overflowing the README column,
  so the README uses `valign="middle"` rather than forcing equal heights.
- The portrait crop framing (`--crop top`, `--aspect 1:1`) is tuned for
  the current source photo; a different photo may need a manual
  `--crop`/`--aspect` adjustment to frame the face well.
