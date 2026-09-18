# Johnson 1892

An ornamental display face with rounded strokes, knob-ended curls, and an irregular rhythm.

![Johnson 1892 specimen](specimens/preview.png)

**1892 · Regular · Version 1.001 · 95 characters · MIT**

[OTF](fonts/Johnson1892-Regular.otf) · [TTF](fonts/Johnson1892-Regular.ttf) · [WOFF2](web/Johnson1892-Regular.woff2) · [PDF specimen](specimens/specimen.pdf) · [Changes](CHANGELOG.md)

## Use

Install either desktop format. For websites, copy `web/`, include `font.css`,
and use `font-family: "Johnson 1892"`. Designed for display sizes.

## Design

**Designer:** Herman Ihlenburg

**Foundry:** MacKellar, Smiths & Jordan

**Observed:** A–Z, a–z and 0–9 from the 1892 patent and period foundry specimens. Larger impressions inform title-critical forms.

**Reconstructed:** Punctuation and symbols are newly drawn companions. Spacing is adapted for digital use.

## Sources

1. [Herman Ihlenburg, US design patent D21,607 (1892), alphabet and figures](https://patents.google.com/patent/USD21607S/en) — Historical US patent plate; the patent states a seven-year term beginning 7 June 1892 [Rights basis](https://patents.google.com/patent/USD21607S/en).
2. [MacKellar, Smiths & Jordan, Specimens of Printing Types (1892), p. 274](https://archive.org/details/specimensofprint00mackrich/page/n241/mode/2up) — Internet Archive records this 1892 edition as NOT_IN_COPYRIGHT [Rights basis](https://archive.org/details/specimensofprint00mackrich).
3. [H. Berthold specimen catalogue (1909), Zierschrift Skandia, p. 428](https://resolver.staatsbibliothek-berlin.de/SBB000308EA00000263) — 1909 historical printing, treated as public domain in the supplied source record; publication predates the maximum US term [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).

Source images are in `reference/`; the source record is [font.json](font.json).
Historical reference material retains the rights status recorded there.
The digital revival is released under the included [MIT License](LICENSE).

## Build or improve

From the repository root:

```sh
python scripts/fontrevival.py build johnson-1892
python scripts/fontrevival.py check johnson-1892
```

Edit `source/font.ttx` or export an individual glyph with
`python scripts/fontrevival.py glyph johnson-1892 j`.
Follow the shared [revival workflow](../../docs/WORKFLOW.md) for additions and revisions.
