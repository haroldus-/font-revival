# Gretchen 1888: source and method

The clean Lindsay sheet is the principal tracing image; the Inland Printer advertisement confirms the name, foundry and 1888 appearance. The rotated Lindsay scan is retained at full resolution. Higher thresholds retain pale joining hairlines and curls. Small G, V, b and m impressions are individually cropped. No designer attribution is asserted without a primary source.

## Evidence and rights

The precise source URLs, printed pages, scan derivation and rights basis are in
`../font.json`. The source pages and institutional/rightsholder metadata extracts
are retained in `../reference/`. The US journal and foundry catalogue were
published in 1888 and 1890, beyond the maximum 95-year copyright term. The
Lindsay scan retains its Library of Congress metadata. No modern digital
typeface was used as source material.

## Preparation

Use Python 3.12, `requirements-tracing.txt` and Potrace 1.16 as described in
[the shared tracing documentation](../../../docs/TRACING.md). The release build
needs only `requirements.txt` and the committed CFF master.

```sh
python scripts/trace_specimen.py gretchen-1888 --output workspace/Gretchen1888-Regular.otf
python scripts/fontrevival.py import gretchen-1888 workspace/Gretchen1888-Regular.otf
python scripts/fontrevival.py build gretchen-1888
```

For an existing master, prepare into `workspace/`, inspect the audit paths and
proofs, then deliberately use `import --replace` only when installing the revision.
The initial master is already imported as `font.ttx`; normal builds do not retrace.

`tracing.json` records exact pixel crops, cleanup, target outline heights, baseline
offsets and bearings. Different optical sizes are scaled into a single static
master. The source comparison preserves raw scan damage; the master repairs dirt
and normalises spacing. `companions.json` retains explicit cubic SVG paths for
every inferred or new drawing, including the final overlap cleanup. Those paths
are sufficient to repeat preparation without the disposable drawing cache.
`font.json` separates observed letters from inferred letters. The punctuation is
new project work, adapted from the collection's existing MIT companion drawings.

## Review

Review the raw crops against `specimens/source-review.pdf`, including the full
alphabet/figures and words at four sizes. `specimens/specimen.pdf` includes every
encoded character. Check `preview.png` and the desktop/mobile gallery for clipping
and spacing. The source year is a specimen date, not a claim of first release.
