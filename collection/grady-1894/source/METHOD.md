# Grady 1894: source and method

The larger ATF letters anchor the narrow weight; Ryan supplies smaller missing forms. True lowercase is retained, including the square detached i dot. G and b were selected individually from the Ryan Grasping/Laboriously line. The different ornamental M, H and C forms are size supplements, not a complete suite of alternates.

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
python scripts/trace_specimen.py grady-1894 --output workspace/Grady1894-Regular.otf
python scripts/fontrevival.py import grady-1894 workspace/Grady1894-Regular.otf
python scripts/fontrevival.py build grady-1894
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
