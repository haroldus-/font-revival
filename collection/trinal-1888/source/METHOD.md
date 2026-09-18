# Trinal 1888: evidence and method

The primary named showing is Marder, Luse & Co.'s advertisement in *The Inland
Printer*, November 1888, printed pp. 138–139. Page 138 explicitly says "Patented
October 9, 1888". Ryan's September 1894 catalogue shows the same face on pp.
130–131. The patent plate and specification identify William F. Capitain and
his assignment to Marder, Luse & Co. The number is **D18,671**, not D18,516:
the latter number in the Roberts/Saxe index belongs to a different patent.
Identification was checked against the primary documents, not copied from that
index. The full patent is retained in `reference/USD18671.pdf`.

## Scope

This is one harmonised display master based principally on the 24-point design.
The source changes with size: the 12-point A has a projecting cross-stroke; the
24-point A curls inward. The 18-point R turns inward; the 24-point R curls at the
foot. The revival deliberately follows the latter forms. It is not a complete
release of every optical size, initial, ornament or variant advertised as Trinal.

Both uppercase and lowercase Unicode inputs use the same capitals. There is no
historical lowercase alphabet in these sources. The 104 encoded characters include
these aliases; they do not represent 104 distinct historical designs. Basic Latin
and useful typographic punctuation are supplied. There are no accent extensions.

## Measurements and drawing

`tracing.json` records every selected crop at full scan resolution. Ryan's 24-point
UNEXCELLED and STANDARD FACES supply the large A, C, D, E, L, N, R, S, U and X;
the Inland Printer 24-point lines supply B, F, P, T, V and figures 1–4. Ryan's
36-point showing supplies G, I, M, O and 5; its 18-point figures supply 8 and 9.
The patent supplies H, J, Q, W, Y, Z, 0, 6 and 7. The ampersand comes from Ryan's
20-point line on p. 131.

The font uses 1000 units per em and a nominal 700-unit cap height. Curved forms
have eight-unit overshoots. N, U, V and Y retain rising curls up to approximately
772 units. Sidebearings are generally 42–45 units (60 for I), with a 300-unit word
space. These are new digital spacing decisions. `features.fea` supplies conservative
kerning for diagonal and overhanging pairs.

The damaged patent K was redrawn with its characteristic loop joining the stem
and split arms. The patent 0 has a scan dropout at the lower right; the repaired
oval is closed. Q, W, Z, 6 and 7 also use explicit curves and straight segments to
remove scan-edge stair steps while preserving their observed construction.
These repairs are SVG paths in `companions.json`, overriding
the initial traces without hiding their historical crops in the review proof.
The remaining punctuation and symbols are new companion drawings.

See [the shared tracing instructions](../../../docs/TRACING.md) for pinned tools,
cleanup and the exact preparation command. The canonical source is `font.ttx`;
the tracing recipe recreates this initial release, not future unrecorded TTX edits.

## Acquisition

Retrieved 18 September 2026. The complete incoming archives remain in `workspace/`.
The committed PNGs are lossless Pillow decodes of these JPEG2000 members:

- `lateststandardfa00ryan_jp2.zip`: `lateststandardfa00ryan_0136.jp2` (printed 130)
  and `_0137.jp2` (printed 131). Archive viewer indices are n135 and n136.
- `sim_american-printer_1888-11_6_2_jp2.zip`: members ending `_0049.jp2` and
  `_0050.jp2` (printed 138–139). Viewer indices are n49 and n50.
- `patent-plate.png`: lossless first image extracted from `USD18671.pdf` using
  `pdfimages -f 1 -l 1 -png`. It is 2320 × 3408 pixels. The PDF download URL is
  https://patentimages.storage.googleapis.com/c5/95/20/60c216cf09fc92/USD18671.pdf.

Archive item URLs, page links and rights evidence are in `font.json`. The Library
of Congress metadata and the journal's publication metadata are retained locally.
The patent's specification grants seven years. All underlying publications are
nineteenth-century US material; Circular 15A supplies the public-domain term basis.
The MIT license covers the project's digital contributions, not a claim to ownership
of the historical pages.
