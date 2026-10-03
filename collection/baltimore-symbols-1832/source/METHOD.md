# Baltimore Symbols 1832

This family contains 4 observed historical impressions from the 1832 Baltimore
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

Normal releases use `font.ttx`, the canonical static CFF master, and need only
`requirements.txt`. For intentional retracing, install pinned
`collection/baltimore-cuts-1832/source/requirements.txt` and Potrace 1.16, then run from the repository root:

```sh
python collection/baltimore-cuts-1832/source/prepare.py baltimore-symbols-1832 \
  --output workspace/BaltimoreSymbols1832-Regular.otf --potrace /path/to/potrace \
  --jobs 2 --cache workspace/baltimore-trace-cache
python scripts/fontrevival.py import baltimore-symbols-1832 workspace/BaltimoreSymbols1832-Regular.otf
python scripts/fontrevival.py sizecheck baltimore-symbols-1832
python scripts/fontrevival.py build baltimore-symbols-1832
python scripts/fontrevival.py check baltimore-symbols-1832
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

## CFF program length

Downloadable CFF programs longer than 60,000 bytes are losslessly split at complete drawing instructions into global subroutines. Each subroutine is below the 65,535-byte Type 2 charstring limit enforced by browser sanitizers. This changes only the instruction packaging: the original encoded operands, curves, widths and contour order are preserved. Calls are one level deep. The editable master keeps its original programs. See the [OpenType Sanitizer Type 2 parser](https://github.com/khaledhosny/ots/blob/main/src/cff_charstring.cc).
