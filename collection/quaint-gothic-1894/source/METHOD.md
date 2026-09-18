# Quaint Gothic 1894: evidence and method

The sole drawing source is the page headed **QUAINT GOTHIC**, printed p. 148 of
the John Ryan Foundry's September 1894 catalogue. The year in the revival name
dates this source; it is not a claim about the design's first appearance.
The catalogue does not identify the designer or original maker. Ryan is credited
as specimen seller, without inventing an attribution. Modern search results using
"Quaint Gothic" often refer to the different face named "Quaint" on Ryan p. 74;
those results were not used as drawing or attribution evidence.

## Scope and observed forms

The 24–48-point impressions establish the master. Thin horizontals contrast with
heavy upright strokes. The A has a long right stroke; H has an extended right
stem; R a descending leg; and T a long stem. These are designed extensions below
the baseline, not scanning or alignment errors. The font retains them.

The source supplies A–P, R–Y, 1, 2, 4, 5, 6, 9 and $. Smaller impressions supply
B, J, K, M, P and X. Their proportions are harmonised with the larger letters;
this is a single display master, not an optical-size family. Q and Z and figures
0, 3, 7 and 8 are inferred. Q follows O and the long R leg; 0 is a smaller O;
the remaining forms use the observed stroke contrast. All other punctuation and
symbols are new companions.

This is a capitals-only face. Lowercase input maps to the capitals. The 104 encoded
characters include aliases and new punctuation, not 104 historical designs.
There are no accent extensions.

## Measurements and cleanup

`tracing.json` records exact source crop boxes and choices. The master is 1000 units
per em, with nominal cap height 700, curved overshoots of 10 units, and descending
A/H/J/K/M/P/R/T strokes to -140. Figures are harmonised to 650 units. Sidebearings
are normally 42 units and 65 for I; word space is 300. These are new digital metrics.
Conservative kerning is recorded in `features.fea`, including extra clearance in RA.

The common tracing process removes isolated dirt, fills tiny ink holes, and fits
cubic curves. H has a larger, explicitly recorded 65-pixel speck threshold to repair
the white flaw near its right stem's foot. This preserves the open counter and the
two different stem lengths. Missing forms and modern symbols are explicit paths
or named transforms in `companions.json`.

Use [the shared tracing instructions](../../../docs/TRACING.md) to repeat the
preparation, substituting `quaint-gothic-1894` and
`workspace/QuaintGothic1894-Regular.otf`. `font.ttx` remains the canonical master.
Review `specimens/source-review.pdf` for every selected capital and figure and
word settings at several sizes.

## Acquisition and rights

Retrieved 18 September 2026 from
https://archive.org/download/lateststandardfa00ryan/lateststandardfa00ryan_jp2.zip.
`reference/ryan-1894-p148.png` is a lossless Pillow decode of
`lateststandardfa00ryan_jp2/lateststandardfa00ryan_0154.jp2` (2413 × 3816 pixels).
The Archive viewer index is n153; the printed page is 148. The complete incoming
archive remains in `workspace/`.

The edition is dated 1894 in the institution's metadata. The Library of Congress
states that it is unaware of copyright restrictions for this item; that statement
and its URL are preserved in `reference/ryan-rights.json`. This nineteenth-century
US publication is also beyond the maximum 95-year copyright term described in
US Copyright Office Circular 15A. `font.json` records the source and rights links.
No modern digital font or later commercial specimen supplied outlines.
