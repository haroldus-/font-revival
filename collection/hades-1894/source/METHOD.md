# Hades 1894: source and method

Hades is a registered geometric reconstruction, not an independent autotrace. Its historical page establishes the open lower-left contours; Erebus supplies the underlying traced forms. A vector difference subtracts the original Erebus silhouette from a copy shifted (-28, -28) font units. This is an optical interpretation of the edge weight. Both fonts use identical advances, cmap aliases, line metrics and kerning. No raster conversion is involved in deriving the contours.

## Evidence and rights

The precise source URLs, printed pages, scan derivation and rights basis are in
`../font.json`. The source pages and institutional/rightsholder metadata extracts
are retained in `../reference/`. The historical US publications date from
1894–1896 and are beyond the maximum 95-year copyright term. ATF references
contain the historical pages reproduced in a 1981 facsimile; the modern introduction
is excluded. No modern digital typeface was used as source material.

## Preparation

Use Python 3.12, `requirements-tracing.txt` and Potrace 1.16 as described in
[the shared tracing documentation](../../../docs/TRACING.md). The release build
needs only `requirements.txt` and the committed CFF master.

```sh
python collection/hades-1894/source/derive.py --output workspace/Hades1894-Regular.otf
python scripts/fontrevival.py import hades-1894 workspace/Hades1894-Regular.otf
python scripts/fontrevival.py build hades-1894
```

For an existing master, prepare into `workspace/`, inspect the audit paths and
proofs, then deliberately use `import --replace` only when installing the revision.
The initial master is already imported as `font.ttx`; normal builds do not retrace.

`tracing.json` records historical comparison crops for the source-review PDF.
`registration.json` and `derive.py` define the geometry; `companions.json` retains
the resulting cubic SVG paths. All Hades outlines are classified as reconstructed
in `font.json`, including the observed historical characters. Erebus supplies the
underlying letter shapes and the project's newly drawn punctuation.

## Review

Review the raw crops against `specimens/source-review.pdf`, including the full
alphabet/figures and words at four sizes. `specimens/specimen.pdf` includes every
encoded character. Check `preview.png` and the desktop/mobile gallery for clipping
and spacing. The source year is a specimen date, not a claim of first release.

## Pair regeneration

`derive.py` reads the canonical Erebus master, checks its recorded version and
kerning, and writes the prepared OTF plus an adjacent `.companions.json` audit.
Copy the reviewed companion paths into `source/companions.json` when installing a
new pair. If Erebus changes, review and version both families together.

After building both fonts, run `python collection/hades-1894/source/proof.py`, then
build Hades again to include `specimens/pairing.pdf` in its checksums. The proof
shows each layer separately and overprinted at the same origin, size and spacing.
Keep tracking, shaping, line height and alignment identical in applications.
