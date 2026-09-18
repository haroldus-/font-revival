# Trinal 1888

Curled Victorian capitals with fine serifs, open bowls, and looping terminals, based on Trinal’s larger sizes.

![Trinal 1888 specimen](specimens/preview.png)

**1888 · Regular · Version 1.000 · 104 characters · Capitals only · MIT**

[OTF](fonts/Trinal1888-Regular.otf) · [TTF](fonts/Trinal1888-Regular.ttf) · [WOFF2](web/Trinal1888-Regular.woff2) · [PDF specimen](specimens/specimen.pdf) · [Changes](CHANGELOG.md)

## Use

Install either desktop format. For websites, copy `web/`, include `font.css`,
and use `font-family: "Trinal 1888"`. Designed for display sizes.

## Design

**Designer:** William F. Capitain

**Foundry:** Marder, Luse & Co.

**Observed:** A–Z, 0–9 and ampersand, from the 1888 patent and named 1888/1894 specimens. The 24-point letters anchor the revival; documented 18- and 36-point impressions and the patent supply missing forms. K, Q, W, Z, 0, 6 and 7 are redrawn to repair damaged or rough patent impressions.

**Reconstructed:** Modern punctuation and symbols are newly drawn companions. Lowercase input aliases the capitals; this is a capitals-only display face. Spacing, kerning and harmonisation between optical sizes are new. The separate swash initial alphabet and small-size variants are not included.

## Sources

1. [John Ryan Foundry, Latest and Standard Faces in Type (September 1894), p. 130](https://archive.org/details/lateststandardfa00ryan/page/130/mode/1up) — 1894 US publication, beyond the 95-year maximum term. Library of Congress scan; Archive metadata states that the Library of Congress is unaware of copyright restrictions. Metadata evidence retained in reference/ryan-rights.json. [Rights basis](https://archive.org/metadata/lateststandardfa00ryan).
2. [John Ryan Foundry, Latest and Standard Faces in Type (September 1894), p. 131](https://archive.org/details/lateststandardfa00ryan/page/131/mode/1up) — 1894 US publication, beyond the 95-year maximum term. Library of Congress scan; Archive metadata states that the Library of Congress is unaware of copyright restrictions. Metadata evidence retained in reference/ryan-rights.json. [Rights basis](https://archive.org/metadata/lateststandardfa00ryan).
3. [The Inland Printer, vol. 6, no. 2 (November 1888), pp. 138–139, Trinal advertisements](https://archive.org/details/sim_american-printer_1888-11_6_2/page/n49/mode/1up) — US journal published in 1888; public domain under the maximum 95-year term. Internet Archive microfilm scan, a faithful reproduction of the historical page. Publication date and scan source retained in reference/printer-metadata.json. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
4. [William F. Capitain, US design patent D18,671, plate and specification (9 October 1888)](https://patents.google.com/patent/USD18671S/en) — 1888 US patent publication, beyond the maximum copyright term; its specification grants a seven-year design patent term. Plate reproduced from the historical patent, not a later digital font. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).

Source images are in `reference/`; the source record is [font.json](font.json).
Historical reference material retains the rights status recorded there.
The digital revival is released under the included [MIT License](LICENSE).

## Build or improve

From the repository root:

```sh
python scripts/fontrevival.py build trinal-1888
python scripts/fontrevival.py check trinal-1888
```

Edit `source/font.ttx` or export an individual glyph with
`python scripts/fontrevival.py glyph trinal-1888 j`.
Follow the shared [revival workflow](../../docs/WORKFLOW.md) for additions and revisions.
