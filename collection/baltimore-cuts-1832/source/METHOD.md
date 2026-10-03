# Baltimore Cuts 1832

This family contains 381 observed historical impressions from the 1832 Baltimore
Type Foundry specimen, held by Columbia University Libraries. The four Baltimore
families share the Boston classification: Cuts, Ornaments, Initials and Symbols.
The complete 238-page audit is in `../../baltimore-cuts-1832/source/book-inventory.json`.

## Evidence and citations

The supplied `ldpd_12198261_000.pdf` was already present in
`workspace/icon-pilot/` and was verified identical to the Downloads copy.
The Internet Archive original JP2 leaves supply full-resolution scan detail.
`../reference/acquisition.json` records original and prepared-image SHA256 hashes,
archive ZIP members, source URLs, native dimensions and exact quarter turns.
Original JP2s are retained beside upright grayscale PNGs; no image is resampled.
The PDF has unnumbered leaves. `printed_page: null` means genuinely unpaginated;
`pdf_page` is one-based, and Internet Archive leaf numbers are zero-based.

The title and archive metadata date the book to 1832. It is a US publication in
the public domain by age; DPLA also marks this item Public domain. Sources and
rights links appear in font.json and `../reference/rights.json`. Copyright in
original project work belongs to Harold Lehmann under the repository MIT license;
this does not claim ownership of historical designs or the library's scan.

## Extraction

All recorded shapes are observed. Ordinary body type, captions, prices, page
furniture and blank versos are excluded. Numbered cut 357 is a set of 25 distinct
Primer panels, each retained separately. Distinct catalogue numbers remain
separate even when subjects recur. Repeated impressions under one number and
repeated letters are recorded without manufacturing extra icons. Complete border
strips preserve composed arrangements; distinguishable repeat pieces and corners
are also retained. Connected patterns retain their observed boundary cuts; no
missing corner, alphabet letter or engraved stroke is invented. Card-border
sample text is erased in documented rectangles, preserving the historical frame.
Embedded lettering belonging to a cut and visible engraver signatures remain.

`tracing.json` is the exact source recipe: native pixel crops, extra quarter turns,
and explicit erasures. Direct grayscale thresholds 135/170/200 produce primary, monochrome/secondary
and tertiary ink respectively. Local normalization is disabled: a short-radius
paper estimate incorrectly hollows broad solid strokes in this volume. Source
proofs retain the original paper for direct comparison; a 0.3-pixel blur and minimum
three-pixel component area suppress tiny scan flecks. The large fluted initials use an 8000-pixel minimum to remove disconnected fragments of neighbouring letters while retaining their complete outlined forms. No holes are filled.
Potrace 1.16 fits cubic curves with tolerance 0.15. Baltimore selects the existing
unrounded-curve separation first (`multitone.round_inputs: false`) to avoid
artificial tangencies from rounding nested threshold outlines before subtraction.
The completed regions still round to integer font units. skia-pathops 0.9.0 subtracts
darker regions to make disjoint vector tones. Existing checked boolean fallbacks
are described in `../../../docs/TRACING.md`. These three levels interpret scan
strength; they are not evidence of three inks in the original printing.

Each impression is uniformly scaled into an 1800-unit maximum dimension within
a 2048-unit em, centred vertically, with 64-unit sidebearings. Wide strips stay
wide; letters keep their source proportions. Private Use assignments are local
to each family and permanent. No alphabet completion or text-font inference is
made. Reviewed bounds are recorded in sizing.json after the visual proof review.

## Reproduce

Normal releases use `font.ttx` with standard `source/glyphs/` edits, pinned
`requirements.txt`, and system Cairo 1.18.0 for the full-detail tonal PNGs. For intentional retracing, install pinned
`collection/baltimore-cuts-1832/source/requirements.txt` and Potrace 1.16, then run from the repository root:

```sh
python collection/baltimore-cuts-1832/source/prepare.py baltimore-cuts-1832 \
  --output workspace/BaltimoreCuts1832-Regular.otf --potrace /path/to/potrace \
  --jobs 2 --cache workspace/baltimore-trace-cache
python collection/baltimore-cuts-1832/source/prepare_truetype.py baltimore-cuts-1832 \
  workspace/BaltimoreCuts1832-Regular.otf --potrace /path/to/potrace
python collection/baltimore-cuts-1832/source/stage_master.py baltimore-cuts-1832 \
  workspace/BaltimoreCuts1832-Regular.otf workspace/cuts-baseline.otf
python scripts/fontrevival.py import baltimore-cuts-1832 workspace/cuts-baseline.otf --binary-charstrings
python collection/baltimore-cuts-1832/source/review_sizing.py baltimore-cuts-1832 workspace/BaltimoreCuts1832-Regular.otf
python scripts/fontrevival.py sizecheck baltimore-cuts-1832
python scripts/fontrevival.py build baltimore-cuts-1832
python scripts/fontrevival.py check baltimore-cuts-1832
```

Use `import --replace` only for an intentional master replacement. The shared
preparation driver uses pinned NumPy 1.26.4 and SciPy 1.11.4 for the identical
maximum filter, nearest-even normalization and four-connected component cleanup.
It caches paper correction within each glyph. The retained verify_preparation.py
checks 51 masks byte for byte against the Boston implementation, including all
quarter turns, four paper radii, erasures and three source thresholds. This changes no
threshold, outline, spacing or tone operation. All thresholds, crops and sources
remain independently inspectable in the family. `specimens/specimen.pdf` compares
every historical crop with the revival and demonstrates multiple display sizes.

## Boundary review

The Primer panels share printed rules. `baltimore-cuts-1832/source/primer-rule-measurements.json` records the measured rule centres; rectangular erasure masks separate the neighbouring illustrations without drawing new rules. Joined ornament pieces have inferred crop boundaries; the complete printed strips are retained alongside them. `baltimore-ornaments-1832/source/repeat-measurements.json` records period estimates and the reviewed native crop boxes. The estimate script is an authoring aid, not an automatic approval of motif boundaries.

## TrueType delivery

The user approved format-specific simplification for drawings exceeding CFF or TrueType renderer limits. The canonical CFF master, SVG and tonal PNG retain full-detail outlines. `source/truetype-glyphs/` records each affected drawing, master-outline SHA256, original and reduced quadratic point counts, contour counts, raster em resolution and measured bounds allowance. `../../baltimore-cuts-1832/source/prepare_truetype.py` renders the canonical glyph and fits a compact outline in the same coordinate frame with the same advance; no source scans or canonical outlines are replaced. OTF, TTF and both webfont formats use these reviewed drawings, as approved by the user. `otf_uses_truetype_approximations` applies them only to the exported CFF font; it preserves their exact 1/64-unit coordinates and leaves the artwork master unchanged. The preparation checks both cubic and quadratic point counts and the TrueType contour count. Additional OTF-only failures exposed the reference renderer’s 65,535-point cubic outline limit: repeated closing endpoints do not add points. New reductions target at most 60,000 points in each curve representation and 4,000 contours; all exported outlines are checked against the renderer limits. Approximation coordinates use a binary-exact 1/64-font-unit grid, far below the 0.5-unit quadratic conversion tolerance. Full-detail OTF outlines also exceeded renderer limits, so the OTF uses the same reviewed drawings. SVG is the full-detail vector delivery. The source hash makes an approximation stale after a master edit.

No. 363 uses `separation: native-mask-bands`: nested threshold masks are separated before Potrace fitting at the original scan resolution. Whole-outline boolean sweeps stalled on this engraving. All native pixels are retained, with the same fitted-curve tolerance and final coordinate rounding; the bands are disjoint in the source masks, while fitted edges can meet within rounding precision. Other engravings retain checked vector subtraction.

## Editable master size

The complete imported artwork is stored as a compact static CFF baseline plus standard `source/glyphs/<glyph>.json` edits. Most encoded icons have complete baseline outlines. Oversized icons use compact baseline stand-ins, with their full original outlines restored by JSON edits. Private tone layers have named empty baseline slots whose full drawings also live in the JSON edits. `stage_master.py` preserves every original tonal contour and each oversized monochrome original before preparing this baseline for the ordinary import command. The normal source loader applies those edits first. All artwork outputs therefore use the complete original tracing. The `preserve_commands` override flag also retains degenerate contour commands produced by native tracing and integer rounding; CFF command optimization would otherwise remove these invisible fragments and invalidate exact master fingerprints. This keeps individual editable files manageable without discarding detail.

Desktop and webfonts contain the encoded monochrome icons and blank space. Private tone layers remain in the artwork master and SVG/PNG delivery. This avoids carrying hundreds of large, inaccessible tonal glyphs in a monochrome font. The full glyph names and region definitions remain stable in the master and metadata.

Generated SVGs use lossless relative/absolute path notation chosen for shorter files. No curve fitting or coordinate rounding occurs in that serialization. Sprite files are divided at approximately 48 MB; each manifest entry and HTML example names the file containing its icon. The full artwork is available through individual SVGs as well.

The baseline TTX uses FontTools’ standard raw CFF `CharString` XML representation, selected with `import --binary-charstrings`. It preserves the complete encoded baseline and accelerates loading; individual full-detail drawings remain readable SVG commands in the standard glyph JSON files.

## Dense-font coverage review

Seven very dense cuts (242, 360, 361, 363, 364, 365 and 368) use fine diagonal coverage screening in their downloadable-font approximations. Ordinary bilevel downsampling made the detailed hatching too dark. The optional preparation script records the raster resolution, Gaussian coverage blur and diagonal screen period in each approximation. This preserves local shading at normal display sizes. The screening is a modern format-specific interpretation; it does not alter the full original linework in the master, SVG or tonal PNG. `truetype-settings.json` records which glyphs use it. The comparison proof shows both drawings at 48, 96, 192 and 384 pixels; choose SVG for enlarged historical detail.

## Catalogue caption cleanup

Final proofs revealed small remnants of catalogue numbers and prices at the top crop edges of cuts 359, 361 and 362. `caption-cleanup.json` records the crop-pixel regions, their measured font-coordinate rectangles, removed contour counts and before/after path hashes. `post_trace_remove_contours` applies that cleanup after fitting, preserving the original common frame. Only whole disconnected contours whose control bounds lie inside a rectangle are removed; the illustrations and engraver signatures remain.

## Release build and PDF rendering

The build applies encoded edits before compiling fonts, then applies private tonal edits one icon at a time for artwork export. This reproduces the complete master without holding every large tonal CFF program in memory simultaneously. PDF proofs draw the actual TrueType curves in reusable vector forms: some PDF viewers reject large embedded glyphs that render successfully in the desktop/web fonts. No proof outline is simplified beyond its documented TTF drawing.

## Distribution size

The complete web bundle is divided into ordinary ZIP parts below 90 MB. Download and extract every part into the same folder; no asset is split between archives. The generated `downloads/bundles.json` lists the parts. The Cuts PDF embeds grayscale JPEG previews: source crops at 384 pixels and quality 75, and tonal comparisons at 320 pixels and quality 80. Monochrome proof outlines remain vectors. This keeps the complete comparison downloadable. Full-resolution native scan files remain lossless in `reference/`, and all vector artwork retains its complete outlines.

The complete output review additionally removed crop-edge catalogue/page-heading fragments from 69, 70, 197, 206, 302, 324, 326 and 346, and fragments of the adjacent cuts from 250 and 251. Rectangles before each crop rotation are retained in `caption-cleanup.json`. Every retained vector command was verified identical; separate Cairo raster comparisons record at most 8/255 coverage-level edge rounding after removal of disconnected contours. No illustration contour outside the measured regions changes.

Final font proofs also exposed isolated catalogue-number remnants above cut 356. Their native crop rectangles and font rectangles are recorded in `caption-cleanup.json`, and the tracing recipe removes only wholly contained disconnected contours. The same fragments were removed from the compact font drawings. Retained illustration commands were verified identical.

## CFF program length

Downloadable CFF programs longer than 60,000 bytes are losslessly split at complete drawing instructions into global subroutines. Each subroutine is below the 65,535-byte Type 2 charstring limit enforced by browser sanitizers. This changes only the instruction packaging: the original encoded operands, curves, widths and contour order are preserved. Calls are one level deep. The editable master keeps its original programs. See the [OpenType Sanitizer Type 2 parser](https://github.com/khaledhosny/ots/blob/main/src/cff_charstring.cc).

## Horizontal alignment review (1.001)

All 381 cuts were surveyed. `straightening.json` records the measurements and
decision for each impression; 167 receive a rigid rotation. Silhouette-line fits
and the principal axis of a filled outer oval nominated candidates. Before/after
proofs determined acceptance: a tapered screw, rounded foot, irregular cloud or
sloping landscape is not automatically a horizontal reference. The original
poses, perspective and uneven printing remain. Frames whose upper and lower
rules diverge retain that historical trapezoid; no perspective warp is applied.

Positive angles rotate counterclockwise in positive-up font coordinates about
(advance/2, 900). The same matrix is applied to the monochrome drawing, all three
tone layers and any compact downloadable-font drawing. Every contour and its
order are retained, including invisible degenerate contours; advances are
unchanged. Coordinates use a binary-exact 1/64-unit grid, with at most 1/128 unit
rounding per coordinate. The `preserve_coordinates` flag prevents CFF export
from rounding them to whole units. Original scan files and imported baseline TTX
remain untouched; the canonical result uses the standard glyph JSON overrides.

`straighten.py` is the guarded one-time authoring helper. It saves previous fonts
and canonical drawings into a new workspace backup directory before applying a
reviewed plan. Normal release builds use the overrides. For tracing from scans,
`post_trace_transform` runs after crop-edge caption cleanup and after fitting,
using the identical common matrix and precision. Compact-font fingerprints and
sizing bounds are updated for the rotated master.

`specimens/straightening-review.pdf` compares all changed full-detail drawings
at 48, 96, 192 and 384 pixels. `specimens/requested-straightening-review.pdf` is
the shared workflow's font comparison for the three requested examples. The
source audit includes contour counts and before/after outline hashes for all
four drawings of each rotated cut.

The post-trace rotation first repeats the initial import's CFF line
specialization. Joining collinear segments before rotation avoids creating tiny
rounded bends at redundant intermediate vertices. Retracing Nos. 65, 70 and
357-16 reproduces all twelve canonical monochrome and tonal drawings exactly;
the comparison hashes are retained in `straightening-retrace-review.json`.

The straightening review also removed one detached pale price-numeral tip beside No. 70. Its pre-rotation control bounds are [787,248,810,303]; the narrow rectangle [780,240,820,310] removes only that contour, before the common rotation. `straightening.json` retains both original and cleaned hashes and contour counts. All illustration contours, spacing and font drawings remain unchanged by this additional cleanup.
