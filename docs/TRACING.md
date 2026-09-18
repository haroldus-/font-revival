# Repeatable specimen tracing

The release build still uses `source/font.ttx`. The optional
`scripts/trace_specimen.py` prepares an **initial** CFF master from documented
historical crops. It never downloads images or replaces a master automatically.

Use Python 3.12, the pinned `requirements.txt`, and **Potrace 1.16**. The reference
Linux tool packages are Ubuntu 24.04 `potrace=1.16-2build1` and
`libpotrace0=1.16-2build1`. They are source-preparation dependencies only; normal
`build`, `check`, and CI do not need them. The script checks the Potrace version.

```sh
python scripts/trace_specimen.py trinal-1888 --output workspace/Trinal1888-Regular.otf
python scripts/fontrevival.py import trinal-1888 workspace/Trinal1888-Regular.otf
python scripts/fontrevival.py build trinal-1888
```

Use `--potrace /path/to/potrace` for a local installation. For an existing master,
first inspect the prepared OTF and its adjacent `.paths.json` audit export. Only
use `import --replace` deliberately: it replaces the master and its features,
while existing `source/glyphs/` edits continue to apply. Later TTX edits are not
automatically fed back into the historical tracing recipe.

Each participating family keeps:

- `source/tracing.json`: exact reference filenames and crop boxes `[left, top,
  right, bottom]` in original image pixels, with y down and right/bottom exclusive.
  It records target outline height, baseline offset, sidebearings and any cleanup
  settings. Read `source/METHOD.md` before changing them.
- `source/companions.json`: explicit SVG paths in font units with y up, or named
  transforms of earlier drawings. These supply new companions and documented
  repairs. An entry with the same character replaces its initial trace.
- `source/features.fea`: optional OpenType features for the prepared master.
- `reference/`: exact local scans plus acquisition and rights evidence.

The tracer caches each decoded image, works on small crops, blurs by 0.55 pixels,
thresholds at 135, retains the largest connected ink component, and fills enclosed
white specks of at most eight pixels. Per-glyph settings override these defaults.
For detached dots and ornaments, set `keep_components` to retain the largest N
components, or `component_min_area` to retain all components above a pixel-area
threshold. Inspect the result: pale hairlines may require a higher `threshold`
and less `blur`. `ink_erosion` shrinks ink by an integer pixel radius before
component selection; use it only to compensate for documented impression spread.

Potrace fits cubic outlines with `alphamax=1`, `opttolerance=0.35`, `turdsize=0`
and `unit=10`. The script reads its y-up paths, scales uniformly to the documented
height, moves them to the recorded baseline and sidebearing, and rounds to font
units. No modern font is used to supply missing characters. Missing companions
must be drawn explicitly and described honestly in `font.json`.

An entry may set `advance_width` and `center` for a fixed-width cell. The recipe's
`font_metrics` can set `cap_height`, `x_height`, `win_ascent`, `win_descent` and
`monospaced`; fixed-pitch masters
must give every drawing the same advance, including spaces and punctuation.
The assembler carries fixed-pitch metadata into CFF and TrueType outputs.
`ink_width` sets an explicit horizontal outline extent when preserving an
existing glyph's proportions; it takes precedence over `width_scale`.

## Revising selected glyphs

For an existing family, `scripts/trace_revisions.py` prepares individual glyph
JSON files rather than a replacement font. Set `mode` to `glyph-revision` in
`source/tracing.json`, record the selected crops and `notes`, and use
`review_characters`/`review_words` to focus the historical proof.

```sh
python scripts/trace_revisions.py nero-1888 --output workspace/nero-edits
```

This command reads the original CFF master without applying existing overrides,
preserves its glyph names and advances, and writes candidate edits only to the
specified directory. It rejects a recipe that changes an advance. Review and
copy the desired files into `source/glyphs/`, following the version, changelog,
before/after and verification steps in [WORKFLOW.md](WORKFLOW.md).

A `replace_bases` mapping may list dependent glyph names, such as Cacute for C.
The helper requires an exact match for the original base contours (apart from
equivalent explicit/implicit closing lines), replaces them with the new drawing,
and keeps all other contours in place. A mismatch fails preparation. This is
appropriate for flattened CFF accents sharing the same original body; translated
or otherwise altered bases require separate reviewed edits. Revision recipes
do not require a `companions.json`, and they do not assemble a new master.

## Vector construction and review

Optional vector construction uses `requirements-tracing.txt`, which additionally
pins skia-pathops 0.9.0. `scripts/outline_geometry.py` resolves contour overlaps and
constructs translated silhouette differences without a raster step. The Hades
family's `source/derive.py` uses it to prepare a registered companion to Erebus.
These tools are not required by normal builds or checks.

`build` also generates `specimens/source-review.pdf` for these families. It pairs
each capital and figure with its historical crop (or labels an inferred drawing),
then shows words at four sizes. Mixed-case families also compare lowercase.
Recipes may override `review_characters` and `review_words`. The normal specimen includes the full encoded
inventory. Review both, including punctuation and spacing, before accepting a
master. Lowercase aliases are permitted for documented capitals-only designs;
they must be visible in the metadata, README and gallery.
