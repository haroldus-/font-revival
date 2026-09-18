# Jagged 1888: source and method

Only No. 39 is used. Ryan supplies the lighter core alphabet; the ATF No. 39 rows supply Q, U, W, dollar, 6 and 8. Two pixels of ink erosion compensate for spread in that facsimile. The 1898 Desk Book No. 39 supplies B and 4. Nos. 40, 41 and the adjacent Outing and Moxon designs are excluded. Weight and spacing have been harmonised across these impressions.

## Evidence and rights

The precise source URLs, printed pages, scan derivation and rights basis are in
`../font.json`. The source pages and institutional/rightsholder metadata extracts
are retained in `../reference/`. The historical US publications date from
1888–1898 and are beyond the maximum 95-year copyright term. ATF references
contain the historical pages reproduced in a 1981 facsimile; the modern introduction
is excluded. No modern digital typeface was used as source material.

## Preparation

Use Python 3.12, `requirements-tracing.txt` and Potrace 1.16 as described in
[the shared tracing documentation](../../../docs/TRACING.md). The release build
needs only `requirements.txt` and the committed CFF master.

```sh
python scripts/trace_specimen.py jagged-1888 --output workspace/Jagged1888-Regular.otf
python scripts/fontrevival.py import jagged-1888 workspace/Jagged1888-Regular.otf
python scripts/fontrevival.py build jagged-1888
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
