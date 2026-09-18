# Nero 1888: the 1.003 source revision

This revision repairs specific scan artifacts in the existing revival. C comes
from the 72-point COMEDIES line on *The Inland Printer*, November 1888, p. 141.
All ten figures come from the 36-point line on John Ryan's 1894 p. 135. The
references already accompanied the original master; their exact crops are now
recorded in `tracing.json`, and institutional metadata is retained in `reference/`.
Source URLs and the historical public-domain rights basis are in `font.json`.

The original C contains a burr on the upper inward-facing wedge. Several figures
retain paper-grain holes and uneven edges, especially 0, 2, 3, 8 and 9. The new
traces use 0.8-pixel blur, threshold 145 and cubic fitting at tolerance 0.5.
Filling enclosed white regions up to 200 source pixels removes the paper holes;
the real counters remain substantially larger. These settings are specific to
these measured crops and should not become general defaults.

Each glyph retains its advance, left ink edge, height and baseline, with the
measured horizontal extent supplied as `ink_width`. New curves retain the
specimen's rounded corners and wedge terminals. The outlines are optical
interpretations of printed ink, not claims about the original punches.

The original C contour is also present verbatim inside Cacute, Ccaron, Ccedilla,
Ccircumflex and Cdotaccent. The revision helper replaces only that contour, after
checking an exact match, and retains the accent contours and positions. These
accents remain modern reconstructions. The earlier j, jcircumflex and quotation
mark edits remain in place. Other extensions, punctuation and ligatures are
unchanged and included in the complete character-inventory review.

## Repeat the preparation

Use Python 3.12, the repository's pinned `requirements.txt`, and Potrace 1.16.
The [shared tracing notes](../../../docs/TRACING.md) describe installation.

```sh
python scripts/trace_revisions.py nero-1888 --output workspace/nero-edits
```

The helper writes 16 reviewable glyph JSON files to the workspace. Compare them
with `source/glyphs/` before installing a revision. It reads the original
`font.ttx`, excluding installed overrides, so repeated runs have the same input.
The master, cmap, advances and OpenType tables are preserved. Normal release
builds need only the committed master and glyph edits, not Potrace.

The source-review PDF pairs raw crops with corrected glyphs and shows words at
four sizes. `specimens/source-revision-review.pdf` compares versions 1.002 and
1.003, including all five accented C forms. The normal specimen includes the
full 302-character inventory.
