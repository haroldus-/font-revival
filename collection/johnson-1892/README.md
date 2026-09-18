# Johnson 1892

An ornamental display face with rounded strokes, knob-ended curls, and an irregular rhythm.

![Johnson 1892 specimen](specimens/preview.png)

**1892 · Regular · Version 1.002 · 95 characters · MIT**

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

1. [Herman Ihlenburg, US design patent D21,607 (1892), alphabet and figures](https://patents.google.com/patent/USD21607S/en) — Historical US patent plate published 7 June 1892, beyond the maximum 95-year copyright term. The specification records a seven-year design-patent term. Evidence retained in reference/patent-rights.json. [Rights basis](https://patents.google.com/patent/USD21607S/en).
2. [MacKellar, Smiths & Jordan, Specimens of Printing Types (1892), p. 274](https://archive.org/details/specimensofprint00mackrich/page/n241/mode/2up) — Internet Archive records this 1892 edition as NOT_IN_COPYRIGHT; metadata and copyright evidence retained in reference/msj-rights.json. [Rights basis](https://archive.org/metadata/specimensofprint00mackrich).
3. [H. Berthold specimen catalogue (1909), Zierschrift Skandia, p. 428](https://resolver.staatsbibliothek-berlin.de/SBB000308EA00000263) — 1909 historical printing, treated as public domain in the supplied source record; publication predates the maximum US term [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
4. [John Ryan Foundry, Latest and Standard Faces in Type (1894), printed p. 145; JP2 member 0151, corroborating the 60-point J](https://archive.org/details/lateststandardfa00ryan/page/145/mode/1up) — US publication from 1894, beyond the maximum 95-year term. Library of Congress metadata retained in reference/ryan-rights.json. Lossless PNG conversion of the historical JP2 page; used for comparison, not as a new tracing source. [Rights basis](https://archive.org/metadata/lateststandardfa00ryan).

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
