# Remington 1888: source and method

Only the lower 12-point Remington No. 2 showing on Inland Printer p. 137 is used. The 10-point cut above it is excluded. Every encoded character, punctuation, space and .notdef uses a 600-unit advance with fixed-pitch metadata. There is no kerning. Capitals/figures are harmonised to 700 units, lowercase to 480 with 700-unit ascenders and 200-unit descenders. Sparse capitals and j require explicitly new square-serif constructions.

## Evidence and rights

The precise source URLs, printed pages, scan derivation and rights basis are in
`../font.json`. The source pages and institutional/rightsholder metadata extracts
are retained in `../reference/`. The US journal was published in 1888,
beyond the maximum 95-year copyright term. The retained microfilm page is a
faithful scan of that historical issue. No modern digital typeface was used
as source material.

## Preparation

Use Python 3.12, `requirements-tracing.txt` and Potrace 1.16 as described in
[the shared tracing documentation](../../../docs/TRACING.md). The release build
needs only `requirements.txt` and the committed CFF master.

```sh
python scripts/trace_specimen.py remington-1888 --output workspace/Remington1888-Regular.otf
python scripts/fontrevival.py import remington-1888 workspace/Remington1888-Regular.otf
python scripts/fontrevival.py build remington-1888
```

For an existing master, prepare into `workspace/`, inspect the audit paths and
proofs, then deliberately use `import --replace` only when installing the revision.
The initial master is already imported as `font.ttx`; normal builds do not retrace.

`tracing.json` records exact pixel crops, cleanup, target outline heights, baseline
offsets and bearings. Impressions from the 12-point No. 2 showing are normalised into a
single static master. The source comparison preserves raw scan damage; the master repairs dirt
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
