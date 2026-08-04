# How the hero assets are built

Technical notes for `scripts/prep_photo.py`, `scripts/make_ascii_svg.py`,
`scripts/make_wordmark_svg.py`, and `scripts/make_contrib_graph.py` — the
pipeline behind the README's hero and contribution graph.

## Constraints that shaped every decision here

GitHub does not execute embedded HTML or JavaScript inside `README.md` — a
README can only reference *images*. So all of the animation (typing
reveal, binary decode, bar growth) has to live inside the SVG files
themselves, using SVG-native animation only: CSS `@keyframes` declared in
an embedded `<style>` block. No `<script>` tags anywhere — even inside an
SVG loaded via `<img>`, embedded scripts don't execute.

The generated SVGs are published to the repo's `output` branch (same
mechanism `.github/workflows/snake.yml` uses for `snake.svg`) and embedded
via `raw.githubusercontent.com` URLs, rather than committed to `main`.
This keeps `main`'s history free of binary SVG diffs every time the photo
or wordmark text gets retuned.

## Wordmark: binary decode, not fake 3D

`make_wordmark_svg.py` renders the name as flat, bold monospace text —
deliberately not isometric block letters or a layered-shadow 3D effect.
Each character position gets a short stack of `<tspan>` elements at the
exact same `x`/`y`: a couple of random `0`/`1` digits that flash briefly
(CSS `opacity` keyframes, `steps(1, end)` for an instant on/off rather
than a fade), followed by the real character locking in and staying.
Positions are staggered left to right (`STAGGER_MS` per character) so it
reads as a left-to-right decode, not a simultaneous flicker. Once the
last character locks in, a blinking terminal cursor (`_`) appears and
loops indefinitely.

This needed one non-obvious fix: CSS/SVG has no way to change an
element's *text content* over time — only presentation properties
(position, color, opacity). So "cycling" a character means stacking
multiple real characters at the same spot and toggling their opacity in
sequence, not animating one element's text.

## Portrait: ASCII art from a real photo

`prep_photo.py` crops/sharpens/downsamples a source photo to a character
grid (aspect-corrected — monospace cells are taller than wide, so
`FONT_ASPECT` in `scripts/_svg_common.py` derives row count from column
count rather than using a naive square grid). `make_ascii_svg.py` maps
luminance to Paul Bourke's standard 10-level ramp (`" .:-=+*#%@"`,
sparse-to-dense) and renders one `<text>` per row (SVG text does not
line-break on `\n`, unlike HTML, so each row needs its own element).
Reveals character-by-character via the same opacity-keyframe technique as
the wordmark, in reading order, so it looks like a terminal printing the
image row by row.

Two whitespace gotchas: SVG's default `xml:space` collapses whitespace
runs, which would break column alignment since the ramp's lightest
character is a literal space — fixed by setting `xml:space="preserve"` on
the root `<svg>` *and* emitting spaces as `&#160;` (NBSP) defensively.

## Contribution graph: a terminal sparkline, not a calendar clone

`fetch_contributions.py` scrapes real daily counts from GitHub's own
public, unauthenticated contributions endpoint (`/users/{user}/
contributions` — the same fragment github.com's own profile page uses,
no token or GraphQL needed) and writes `data/contributions.json`.

`make_contrib_graph.py` deliberately does **not** reproduce GitHub's own
53-week × 7-day calendar grid with a Less→More legend — that's what
GitHub already shows on your profile natively, and this is a personal
piece of the README, not a duplicate. Instead it buckets days into
weekly totals and renders a single row of bars (a sparkline), framed like
a shell command and its output (`$ git log --since=1.year ...`, `$ echo
"N contributions, M-day streak"`) — bars grow from zero height on load
(CSS `transform: scaleY()`, staggered per bar).

## Regenerating

```
python scripts/prep_photo.py assets/photo.jpg
python scripts/make_ascii_svg.py                        # -> dist/kuldeep-ascii.svg
python scripts/make_wordmark_svg.py --mode decode        # -> dist/wordmark.svg
python scripts/fetch_contributions.py                    # -> data/contributions.json
python scripts/make_contrib_graph.py                     # -> dist/contrib-heatmap.svg
open dist/wordmark.svg                                   # local file:// preview
```

Useful knobs: `--text`, `--mode {decode,static}` on the wordmark script;
`--cols`, `--aspect`, `--crop {top,center}` on `prep_photo.py`.

## Known limitations

- No `prefers-reduced-motion` support yet for the always-looping cursor
  blink.
- The portrait crop framing is tuned for the current source photo; a
  different photo may need a manual `--crop`/`--aspect` adjustment.
- Weekly bucketing in the sparkline assumes `days` starts on a
  consistent weekday boundary from the fetch; a partial first/last week
  is included as-is rather than padded.
