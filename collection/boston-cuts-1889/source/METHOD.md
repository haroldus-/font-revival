# Father Christmas, No. 4202

This is the first pilot for Boston Cuts 1889, not a completed inventory of the
book. It follows printed p. 273 (PDF page 281, one-based; Internet Archive leaf
281). The section heading credits the cuts to Central Type Foundry. The title
page establishes Boston, 1889; an individual engraver is not identified.

The supplied PDF was copied from Downloads to `workspace/icon-pilot/`. Its
segmented image layers discard tonal detail, so the corresponding original
Internet Archive JP2 page was obtained and converted losslessly to PNG with
Pillow 12.3.0. The page is 2827 × 3969 native pixels. `reference/acquisition.json`
records the exact URLs, hashes, conversion and PDF identity. The full page and
title image, archive metadata and page map are retained. This is the same
historical impression, not a modern reproduction or digital redrawing.

## Measured preparation

`tracing.json` records the crop `[682, 785, 943, 1034]`, using native image pixels
with y down and exclusive right/bottom edges. It excludes the catalogue number
and neighbouring cuts. The 261 × 249 crop has no added pictorial elements.

Inspect the historical page before changing this recipe. We compared thresholds
135, 150, 165, 175, 180, 185 and 190. Lower values discard the pale swept-hat
strokes and face details; 190 begins closing fine white spaces. The selected
185 threshold, 0.3-pixel blur, two-pixel minimum ink component and no hole filling
preserve detached marks and the tiny open areas. One isolated background speck
at crop pixels x=19–20, y=165 is erased by the documented `[18,164,21,167]`
rectangle. It is detached from the engraving. Other surviving details are kept.

Potrace 1.16 uses turdsize 0, alphamax 1, opttolerance 0.15 and unit 10. Cubic
outlines are uniformly scaled to 1800 units high and rounded to integer units.
The em is 2048 units, the ascent/descent 1900/−148, and the sidebearings 64 units.
There is no horizontal stretching, added engraving, kerning, hinting or simplified
small-size variant. Font-unit rounding explains sub-unit differences in extrema.

The curve fitting and threshold choice are interpretations of the impression;
the SVG cannot recover detail absent from the scan. Paper, background specks,
catalogue number and price are not part of the icon. Labels, tags, spacing and
the Private Use codepoint U+E000 are new project work.

## Limited multi-tone edition (1.002)

The multi-tone companion has exactly three disjoint vector regions, following
observed strengths of ink in the scan. The primary region keeps the darkest hat,
eye, pipe and lower beard marks at full opacity. The secondary region carries
medium engraving and face/beard strokes at 55%. The tertiary region keeps pale
hat and facial strokes at 25%. These assignments are a new interpretation of
the impression, not a claim that the printer used three separate inks.

The recipe traces thresholds 130, 185 and 210, with the same crop, blur, cleanup
and transform as the solid icon. The 130 trace defines primary ink. The primary
region is subtracted from the 185 trace to produce the secondary region; their
union is subtracted from the 210 trace to produce the tertiary region. Boolean
operations use the already pinned skia-pathops 0.9.0. This yields three separate
regions rather than a stack of semi-transparent contours that accumulates shades.
The regions may be coloured independently through the SVG's primary, secondary
and tertiary CSS custom properties. Giving the lighter two regions the same
colour and opacity produces a two-tone appearance.

The monochrome transform is reused for all regions, keeping the portrait aligned
across formats. The CFF master contains unencoded `uniE000.primary`,
`uniE000.secondary` and `uniE000.tertiary` glyphs. Their roles and default opacities
live in `font.json`. They can be exported and revised through the usual `glyph`
command and `source/glyphs/` overrides. They add no user-facing codepoints;
standard icon fonts still show the unchanged solid form at U+E000.

In addition to the shared one-speck erasure, the multi-tone recipe removes an
isolated background smudge to the right of the face with crop rectangle
`[236,114,258,131]`. It does not intersect the portrait or pipe. No engraving is
invented. Threshold choice and curve fitting interpret the scan's limited detail.
The superseded 13-layer grayscale assets are removed from this release.

The build derives a multi-tone SVG, sprite and transparent 1024-pixel-high PNG
from the committed regions. The PNG renderer temporarily maps the unencoded
layers to supplementary Private Use characters in memory for Pillow; these
mappings are never saved in released fonts. PNG pixels use black plus alpha so
the default three ink strengths work against any background. Intermediate edge
pixels are antialiasing, not additional designed tones. Normal builds use only
`requirements.txt`; preparing regions additionally uses `requirements-tracing.txt`.

The gallery places actual SVG paths inline. No external sprite reference or
network request is needed for the previews, so `icons.html` also works when
opened directly as a file. The downloadable sprite remains available for HTTP(S)
use. Individual SVG files can be opened directly or embedded with `<img>`.

## Reproduce the initial master

Use Python 3.12, `requirements-tracing.txt`, and the documented Potrace 1.16
source-preparation dependency in [TRACING.md](../../../docs/TRACING.md).
The pinned skia-pathops 0.9.0 is used only during multi-tone source preparation.

```sh
python scripts/trace_specimen.py boston-cuts-1889 \
  --output workspace/icon-pilot/BostonCuts1889-Regular.otf
python scripts/fontrevival.py import boston-cuts-1889 \
  workspace/icon-pilot/BostonCuts1889-Regular.otf
python scripts/fontrevival.py build boston-cuts-1889
```

The import intentionally refuses to overwrite an existing master. To repeat the
preparation for an audit, use a different workspace output and compare it with
the existing OTF; do not replace the canonical master automatically. A deliberate
replacement uses `import --replace` after reviewing edits in `source/glyphs/`.

Normal offline builds use `source/font.ttx`, applying any individual glyph JSON
edits before deriving all font and SVG outputs. `companions.json` adds only a
blank space glyph; no companion illustration was drawn. The font has `.notdef`,
space, the single encoded icon and three unencoded tone regions. All illustrated
coverage and the multi-tone compositor are declared in `font.json`.

## Review

`specimens/specimen.pdf` and `source-review.pdf` compare the source, multi-tone and
monochrome versions, and show 16, 24, 32, 48, 64, 96 and 192 pt sizes plus an inline
text example. Multi-tone proof sizes measure the ink height; font sizes measure the
em. The PNG proof also compares all three. Inspect the multi-tone SVG, solid SVG
sprite and WOFF2 side by side in `icons.html`, including at 64 px and on
mobile. The glyph is detailed display artwork; 64 px is a reviewed recommendation,
not a restriction. Smaller representations are provided in the proof so users
can judge their intended output.

`sizing.json` protects the reviewed source proportions, baseline, height and
advance through CFF-to-quadratic conversion. These are icon-specific bounds;
alphabetic proportion heuristics are not applicable to Private Use characters.

## Rights and credits

The 1889 US publication is public domain under the maximum 95-year term; see the
source record and the U.S. Copyright Office's Circular 15A. The retained archive
metadata credits the Library of Congress and records that it is unaware of
copyright restrictions. The original engraving remains public-domain material.
Original digital project work is Copyright (c) 2026 Harold Lehmann, MIT licensed.
