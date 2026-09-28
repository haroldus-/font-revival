# Remington 1888: source and method

Only the lower 12-point Remington No. 2 showing on Inland Printer p. 137 is used. The 10-point cut above it is excluded. Every encoded character, punctuation, space and .notdef uses a 600-unit advance with fixed-pitch metadata. There is no kerning. Capitals/figures are harmonised to 700 units, lowercase to 480 with 700-unit ascenders and 200-unit descenders. Sparse capitals and j require explicitly new square-serif constructions.

## Version 1.002 sizing revision

The retained source is *The Inland Printer*, November 1888, printed p. 137,
[12-point Remington No. 2](https://archive.org/details/sim_american-printer_1888-11_6_2/page/n48/mode/1up).
The existing public-domain evidence and retained scan apply to this revision.
No new source or digital typeface was introduced.

The original preparation mistakenly assigned `t` a 480-unit height. Its selected
impression in “6th” occupies the crop `[2179, 2361, 2201, 2399]`, the same 38-pixel
height as neighbouring `h` at `[2211, 2361, 2240, 2399]`. The revised outline is
700 units high and 390 wide, centred in its existing 600-unit cell. This restores
both height and stroke presence; a vertical stretch alone would leave it too thin.

The selected `e` in “Spindler” at `[1221, 2429, 1247, 2458]` already reached the
480-unit body height, with an approximately 430-unit ink width. Its open bowl
looked small beside the surrounding forms. The new optical adjustment makes it
460 units wide and 492 high, from -6 to 486. These modest width and overshoot
changes are a revival decision, not dimensions claimed for the original metal
type. Its contour structure and traced character remain intact.

The full alphabet, figures and punctuation were reviewed. Narrow `c` and `z`
agree with their source crops and are retained. The deliberately narrow inferred
`j`, dotted `i`, Q tail and lowercase descenders have separate validation limits.
There are no encoded accented derivatives or OpenType substitutions depending
on `e` or `t`. Character coverage, names, every advance, and fixed-pitch metadata
remain unchanged. No kerning is added.

The unchanged `font.ttx` and original tracing measurements retain the initial
drawings. Current builds apply `glyphs/e.json` and `glyphs/t.json` over that master.
To repeat the 1.002 edits exactly, run:

```sh
python collection/remington-1888/source/resize.py
python scripts/fontrevival.py sizecheck remington-1888 --strict
python scripts/fontrevival.py build remington-1888
```

`resize.py` always reads the original master, so repeated runs do not accumulate
scaling. `sizing.json` records reviewed top/bottom, ink-width and advance limits;
the shared `check` enforces them in OTF, TTF, WOFF and WOFF2. The before/after
proofs are `specimens/sizing-review.pdf` and `specimens/sizing-words-review.pdf`.

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
