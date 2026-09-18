# The revival workflow

## 1. Start from evidence

Put the supplied scans, images, or PDFs in `workspace/`. Identify the typeface,
date, designer, foundry, and useful specimen pages. Record a public-domain rights
basis using the [source policy](SOURCES.md). Keep the exact reference images used
in `collection/<id>/reference/` so future work does not depend on live websites.

## 2. Add a family

```sh
python scripts/fontrevival.py new example-1890 --name "Example 1890" --year 1890
```

Complete the generated `font.json`. Trace the historical forms, clean scan damage,
set consistent metrics and spacing, and draw any missing companions. Record which
forms are reconstructed. Build or export a static OpenType/CFF master with at
least printable Basic Latin, then import it:

```sh
python scripts/fontrevival.py import example-1890 workspace/Example1890-Regular.otf
python scripts/fontrevival.py build example-1890
```

The imported XML master preserves the outlines, character map, spacing, kerning,
and OpenType features. It is the common source for every release format. Additional
tracing scripts and measurements can live alongside it under `source/`.

For sources suitable for crop-based tracing, the optional [repeatable tracing
tool](TRACING.md) records measurements and explicit companion drawings, then prepares
the OTF for `import`. It also enables a generated historical-source comparison proof.
It does not replace visual review or change the canonical TTX workflow.

## 3. Improve an existing family

Save the current font before editing. For example:

```sh
cp collection/nero-1888/fonts/Nero1888-Regular.ttf workspace/nero-before.ttf
python scripts/fontrevival.py glyph nero-1888 j
```

If that glyph already has an edit file, edit the existing file. Change the SVG path
and advance width in `source/glyphs/j.json`. Coordinates use the font's units per
em, with positive y upwards. The `notes` field records the design rationale.
Check related accented forms too; a `j` change may also require `jcircumflex`.
For broader changes, edit `source/font.ttx`, or intentionally replace it with
`import ... --replace`. Existing glyph edits continue to apply over a replaced master;
review them when replacing it.

Increase `font.json`'s version (for example `1.001` → `1.002`) and describe the
change in `CHANGELOG.md`. Rebuild, then generate a focused review proof:

```sh
python scripts/fontrevival.py build nero-1888
python scripts/fontrevival.py compare nero-1888 --before workspace/nero-before.ttf \
  --text "j ij ji fj ja jo ju aj enjoyment ĵ" \
  --output collection/nero-1888/specimens/j-review.pdf
python scripts/fontrevival.py build nero-1888
```

The final build includes the review PDF in the checksums. Use a meaningful filename
and keep review proofs that explain design decisions. Git preserves previous masters
and releases; a revision should be a focused commit.

## 4. Check and share

```sh
python scripts/fontrevival.py check
python -m unittest discover -s tests
python -m http.server 8000
```

Inspect the gallery at <http://localhost:8000>, the specimen PDF (including its full
character inventory), and any review proofs. Compare against the historical sources.
Check counters, overlaps, baseline, descenders, spacing, and words containing the changed
forms. Then follow [CONTRIBUTING.md](../CONTRIBUTING.md) to submit a pull request.

## Repeatability

`build` discovers families automatically and derives OTF, TTF, WOFF, WOFF2, specimen
PDF/PNG, CSS, family README, checksums, and the gallery from committed inputs.
TTF curves are derived from the cubic master with a maximum conversion error of
0.5 font units. The build applies the MIT metadata and unrestricted embedding.

`check` verifies character coverage, nonempty outlines, spacing across formats,
license metadata, checksums, and a clean rebuild in a temporary directory.
Python 3.12 and `requirements.txt` define the reference environment used by CI.
Rendering may differ with platform font rasterizers; use the Linux CI environment
for byte-for-byte comparisons. Source files and outputs are committed together.

## A prompt to reuse

> Read AGENTS.md and docs/WORKFLOW.md. Using the samples in workspace/, add a new
> revival or improve the specified family. Research and record the historical
> sources and rights basis. Preserve the distinctive forms and mark reconstructions.
> Use the shared source format and build commands. For revisions, include a version
> bump, changelog, and before/after proof. Inspect the results and finish with passing
> checks and a focused change ready for a pull request.
