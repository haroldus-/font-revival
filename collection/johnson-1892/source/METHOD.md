# Johnson 1892: the 1.002 source revision

The 1892 Ihlenburg patent plate supplies H, L, P, R, b, f, p and q. The much
larger 60-point J in Grand Jaunts, MSJ 1892 p. 274, supplies J. Exact crops are
recorded in `tracing.json`; the source images already accompanied the master.
The source URLs and historical public-domain rights basis are in `font.json`.
`reference/patent-rights.json` and `reference/msj-rights.json` retain publication
and institutional evidence. MSJ p. 274 was checked against OCR page index 241.

The original font preserves small scan marks under L and R and beside b, along
with edge steps on vertical stems. The revision retains only the principal ink
component for each selected glyph. Patent crops use 1.4-pixel blur and threshold
145; J's larger impression needs only 0.8-pixel blur. Cubic fitting uses tolerance
0.5. P uses threshold 125 to keep the channel between its curl and stem open.
The b also retains its historically open curl. Small white specks are filled,
while actual counters and apertures remain open.

Advances and existing visible outline bounds are retained to whole font units.
L's target bounds use its actual letter contour, excluding the stray triangle
below the baseline; the letter itself keeps its previous position. The curl,
serifs, descending strokes and irregular historical baselines remain deliberate
features. Punctuation and symbols remain the original modern companions.

The consulted Ryan 1894 p. 145 confirms the larger Grand Jaunts J. Its impression
adds no necessary geometry beyond the retained MSJ page. The patent and MSJ
sources suffice for this revision; no modern digital typeface is used.

## Repeat the preparation

Use Python 3.12, the repository's pinned `requirements.txt`, and Potrace 1.16.
The [shared tracing notes](../../../docs/TRACING.md) describe installation.

```sh
python scripts/trace_revisions.py johnson-1892 --output workspace/johnson-edits
```

The helper writes nine reviewable glyph JSON files into the workspace. Compare
them with `source/glyphs/` before installing a revision. It reads the original
`font.ttx`, excluding installed overrides. The master, cmap, advances and kerning
are preserved. Release builds need only committed sources, not Potrace.

The source-review PDF pairs each raw crop with its correction and shows words
at four sizes. `specimens/source-revision-review.pdf` compares versions 1.001
and 1.002. Inspect the complete 95-character specimen and browser gallery as well,
especially P/b apertures and the balance of the revised J with adjacent letters.
