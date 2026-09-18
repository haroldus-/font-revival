# Gretchen 1888

Ornamental mixed-case letters with looping terminals and long descending strokes.

![Gretchen 1888 specimen](specimens/preview.png)

**1888 · Regular · Version 1.000 · 104 characters · MIT**

[OTF](fonts/Gretchen1888-Regular.otf) · [TTF](fonts/Gretchen1888-Regular.ttf) · [WOFF2](web/Gretchen1888-Regular.woff2) · [PDF specimen](specimens/specimen.pdf) · [Changes](CHANGELOG.md)

## Use

Install either desktop format. For websites, copy `web/`, include `font.css`,
and use `font-family: "Gretchen 1888"`. Designed for display sizes.

## Design

**Designer:** Unidentified in the consulted primary specimens

**Foundry:** Lindsay Type Foundry, New York

**Observed:** Directly sampled alphabet and figures: ABCDEFGHILMNOPRSTUVWYabcdefghiklmnoprstuvxy1345678. Additional observed symbols and exact crop/cleanup settings are enumerated in source/tracing.json.

**Reconstructed:** Inferred alphabet/figures: JKQXZjqwz029. Unobserved punctuation and symbols are newly drawn MIT project companions. Spacing, kerning and optical-size harmonisation are new. Uppercase and lowercase are distinct. The year identifies the specimen, not a claimed first release.

## Sources

1. [The Inland Printer, vol. 6, no. 2 (November 1888), printed p. 140](https://archive.org/details/sim_american-printer_1888-11_6_2/page/n51/mode/1up) — 1888 US journal, public domain under the maximum 95-year term. Faithful microfilm scan; issue and provenance retained in reference/printer-metadata.json. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
2. [Lindsay Type Foundry, Specimen of Printing Types (1890), Gretchen sheet; JP2 member 0185, rotated clockwise 90 degrees](https://archive.org/details/specimenofprinti00lind) — Nineteenth-century US publication, beyond the maximum 95-year term. Library of Congress scan; institutional metadata retained with the reference. [Rights basis](https://archive.org/metadata/specimenofprinti00lind).

Source images are in `reference/`; the source record is [font.json](font.json).
Historical reference material retains the rights status recorded there.
The digital revival is released under the included [MIT License](LICENSE).

## Build or improve

From the repository root:

```sh
python scripts/fontrevival.py build gretchen-1888
python scripts/fontrevival.py check gretchen-1888
```

Edit `source/font.ttx` or export an individual glyph with
`python scripts/fontrevival.py glyph gretchen-1888 j`.
Follow the shared [revival workflow](../../docs/WORKFLOW.md) for additions and revisions.
