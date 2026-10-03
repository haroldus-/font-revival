# Baltimore Ornaments 1832

This family contains 396 observed historical impressions from the 1832 Baltimore
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
and tertiary ink respectively. Except for the title-page corner described below, local normalization is disabled: a short-radius
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
python collection/baltimore-cuts-1832/source/prepare.py baltimore-ornaments-1832 \
  --output workspace/BaltimoreOrnaments1832-Regular.otf --potrace /path/to/potrace \
  --jobs 2 --cache workspace/baltimore-trace-cache
python collection/baltimore-cuts-1832/source/prepare_truetype.py baltimore-ornaments-1832 \
  workspace/BaltimoreOrnaments1832-Regular.otf --potrace /path/to/potrace
python collection/baltimore-cuts-1832/source/stage_master.py baltimore-ornaments-1832 \
  workspace/BaltimoreOrnaments1832-Regular.otf workspace/ornaments-baseline.otf
python scripts/fontrevival.py import baltimore-ornaments-1832 workspace/ornaments-baseline.otf --binary-charstrings
python collection/baltimore-cuts-1832/source/review_sizing.py baltimore-ornaments-1832 workspace/BaltimoreOrnaments1832-Regular.otf
python scripts/fontrevival.py sizecheck baltimore-ornaments-1832
python scripts/fontrevival.py build baltimore-ornaments-1832
python scripts/fontrevival.py check baltimore-ornaments-1832
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

The user approved format-specific simplification for drawings exceeding CFF or TrueType renderer limits. The canonical CFF master, SVG and tonal PNG retain full-detail outlines. `source/truetype-glyphs/` records each affected drawing, master-outline SHA256, original and reduced quadratic point counts, contour counts, raster em resolution and measured bounds allowance. `../../baltimore-cuts-1832/source/prepare_truetype.py` renders the canonical glyph and fits a compact outline in the same coordinate frame with the same advance; no source scans or canonical outlines are replaced. OTF, TTF and both webfont formats use these reviewed drawings, as approved by the user. `otf_uses_truetype_approximations` applies them only to the exported CFF font; it preserves their exact 1/64-unit coordinates and leaves the artwork master unchanged. The preparation checks both cubic and quadratic point counts and the TrueType contour count. Additional OTF-only failures exposed the reference renderer’s 65,535-point cubic outline limit: repeated closing endpoints do not add points. Current reductions target at most 32,000 points in each curve representation and 4,000 contours; the compatibility review below explains the stricter limit. All encoded exported outlines are checked against the compatible renderer limits. Approximation coordinates use a binary-exact 1/64-font-unit grid, far below the 0.5-unit quadratic conversion tolerance. Full-detail OTF outlines also exceeded renderer limits, so the OTF uses the same reviewed drawings. SVG is the full-detail vector delivery. The source hash makes an approximation stale after a master edit.

## Editable master size

The complete imported artwork is stored as a compact static CFF baseline plus standard `source/glyphs/<glyph>.json` edits. Most encoded icons have complete baseline outlines. Oversized icons use compact baseline stand-ins, with their full original outlines restored by JSON edits. Private tone layers have named empty baseline slots whose full drawings also live in the JSON edits. `stage_master.py` preserves every original tonal contour and each oversized monochrome original before preparing this baseline for the ordinary import command. The normal source loader applies those edits first. All artwork outputs therefore use the complete original tracing. The `preserve_commands` override flag also retains degenerate contour commands produced by native tracing and integer rounding; CFF command optimization would otherwise remove these invisible fragments and invalidate exact master fingerprints. This keeps individual editable files manageable without discarding detail.

Desktop and webfonts contain the encoded monochrome icons and blank space. Private tone layers remain in the artwork master and SVG/PNG delivery. This avoids carrying hundreds of large, inaccessible tonal glyphs in a monochrome font. The full glyph names and region definitions remain stable in the master and metadata.

Generated SVGs use lossless relative/absolute path notation chosen for shorter files. No curve fitting or coordinate rounding occurs in that serialization. Sprite files are divided at approximately 48 MB; each manifest entry and HTML example names the file containing its icon. The full artwork is available through individual SVGs as well.

The baseline TTX uses FontTools’ standard raw CFF `CharString` XML representation, selected with `import --binary-charstrings`. It preserves the complete encoded baseline and accelerates loading; individual full-detail drawings remain readable SVG commands in the standard glyph JSON files.

## Release build and PDF rendering

The build applies encoded edits before compiling fonts, then applies private tonal edits one icon at a time for artwork export. This reproduces the complete master without holding every large tonal CFF program in memory simultaneously. PDF proofs draw the actual TrueType curves in reusable vector forms: some PDF viewers reject large embedded glyphs that render successfully in the desktop/web fonts. No proof outline is simplified beyond its documented TTF drawing.

## Title-page paper

The title-border corner on PDF page 7 has substantially darker paper than the later ornament leaves. It uses the same broad 256-pixel paper normalization reviewed for the initials, before the unchanged 135/170/200 thresholds. The source comparison confirms that the corrected tracing retains the trefoils, rules, Greek key and dots while excluding the gray paper field. Other ornament crops retain direct grayscale thresholds.

Final font proofs also exposed isolated catalogue-number remnants above the composed Four Line Pica strips 2 and 3. Their native crop rectangles and font rectangles are recorded in `caption-cleanup.json`, and the tracing recipe removes only wholly contained disconnected contours. The same fragments were removed from the compact font drawings. Retained illustration commands were verified identical.

## CFF program length

Downloadable CFF programs longer than 60,000 bytes are losslessly split at complete drawing instructions into global subroutines. Each subroutine is below the 65,535-byte Type 2 charstring limit enforced by browser sanitizers. This changes only the instruction packaging: the original encoded operands, curves, widths and contour order are preserved. Calls are one level deep. The editable master keeps its original programs. See the [OpenType Sanitizer Type 2 parser](https://github.com/khaledhosny/ots/blob/main/src/cff_charstring.cc).

## Horizontal alignment revision (1.001)

All 396 icons were surveyed; 230 receive reviewed rigid rotations. `straightening.json` retains each decision, measured references, matrices and before/after contour counts and hashes. Clear local baselines and frame edges take precedence over containing-strip measurements; opposite tips establish the axis of rules and dashes. Pieces cropped from the same printed strip can share its axis where they lack a clear local horizontal. Uneven edges and intentional letter slants remain. Every contour and original advance is retained. The same matrix applies to all three tones and any compact font drawing, on a 1/64-unit coordinate grid.

The reusable authoring helpers are `../../baltimore-cuts-1832/source/straighten.py` (`--family collection/baltimore-ornaments-1832`) and `compare_straightening.py` (`--family collection/baltimore-ornaments-1832 --workspace workspace/baltimore-extraction/straighten-ornaments`). Backups retain the prior fonts and canonical drawings. Normal builds apply the standard glyph overrides; retracing applies `post_trace_transform` after caption cleanup. The comparison PDF shows all changed full-detail drawings at 48, 96, 192 and 384 pixels.

After the alignment revision, the ornament web bundle uses numbered ordinary ZIP parts below 90 MB. Extract every part into the same folder; complete assets are never split between archives. The generated bundle manifest lists the complete set.

## Font renderer compatibility

FreeType 2.13 uses signed 16-bit outline counts, so drawings that fit the
TrueType file format can still disappear in Firefox and other applications.
The compatibility review checks both cubic and quadratic point counts against
32,767, reserving four additional metric points for TrueType. The optional
`prepare_truetype.py` helper targets at most 32,000 points in each representation
using the same recorded raster and fitting method. Full-detail artwork, spacing
and character assignments remain unchanged. `specimens/font-compatibility-review.pdf`
compares the previous and compatible font drawings at normal display sizes.

References: [FreeType 2.13 outline limits](https://github.com/freetype/freetype/blob/VER-2-13-2/include/freetype/ftimage.h)
and [TrueType phantom points](https://github.com/freetype/freetype/blob/VER-2-13-2/src/truetype/ttgload.c).
