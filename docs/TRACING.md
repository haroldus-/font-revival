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
**This cleanup is for connected letters.** Detached dots or accents require
separate treatment; do not use it blindly on arbitrary glyphs.

Potrace fits cubic outlines with `alphamax=1`, `opttolerance=0.35`, `turdsize=0`
and `unit=10`. The script reads its y-up paths, scales uniformly to the documented
height, moves them to the recorded baseline and sidebearing, and rounds to font
units. No modern font is used to supply missing characters. Missing companions
must be drawn explicitly and described honestly in `font.json`.

`build` also generates `specimens/source-review.pdf` for these families. It pairs
each capital and figure with its historical crop (or labels an inferred drawing),
then shows words at four sizes. The normal specimen includes the full encoded
inventory. Review both, including punctuation and spacing, before accepting a
master. Lowercase aliases are permitted for documented capitals-only designs;
they must be visible in the metadata, README and gallery.
