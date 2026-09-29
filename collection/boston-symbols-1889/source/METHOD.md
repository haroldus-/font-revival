# Boston Symbols 1889

Original native JP2 leaves, source URLs, hashes and rights evidence are retained under reference/. Crop coordinates, masks and tracing parameters are in tracing.json; coverage is recorded in inventory.json and the central Boston Cuts inventory.

Symbols are separated using ink-row whitespace and individually reviewed against the native scan. The technical table has unequal column spacing. Catalogue numbers, fractions, ordinary letters and numeral samples are excluded. Separately printed size variants retain their observed differences. The map plate contributes the isolated construction types; labelled map and building demonstrations are retained in the source as compositions of those types.

Local paper correction uses a 25-pixel maximum filter with a radius-4 Gaussian estimate, then divides the scanned gray values by the paper estimate. Three thresholds and exact PathOps differences produce disjoint primary, secondary and tertiary vector regions at opacities 1, 0.55 and 0.25. The tones interpret scanned ink strength and are not claims of separately coloured printing inks. No missing strokes are invented.

The longest ink dimension fits 1800 units in the 2048-unit em, with 64-unit bearings and uniform scaling. Potrace 1.16 fits cubic curves for the canonical CFF master. Normal builds use source/font.ttx without the network or tracing tools. Original project work is copyright Harold Lehmann and uses the repository MIT license.

The 460 exports include 417 technical-table symbols, 17 crochet patterns, 10 small commercial symbols and 16 map types. Monochrome thresholds start from per-crop Otsu separation on locally corrected paper, then receive reviewed overrides for sun faces (180), fine map rules (200), faint at signs (230), crochet frames and counters (160–225), pale hairlines and astronomical signs (230), and the tiny 6-point percentage mark (200). Final thresholds, not a fresh automatic estimate, are committed in tracing.json. Small scans retain their printed gaps; faint lines are not reconstructed.

`measure_thresholds.py` prints candidate values for comparison without editing the authoritative recipe. Review the source and both tonal and monochrome proofs before adopting any candidate; global thresholding cannot faithfully resolve every pale hairline and tiny white counter at once.
