# Marine 1894

Rounded mixed-case display letters with crossed bowls and detached square and diamond details.

![Marine 1894 specimen](specimens/preview.png)

**1894 · Regular · Version 1.000 · 104 characters · MIT**

[OTF](fonts/Marine1894-Regular.otf) · [TTF](fonts/Marine1894-Regular.ttf) · [WOFF2](web/Marine1894-Regular.woff2) · [PDF specimen](specimens/specimen.pdf) · [Changes](CHANGELOG.md)

## Use

Install either desktop format. For websites, copy `web/`, include `font.css`,
and use `font-family: "Marine 1894"`. Designed for display sizes.

## Design

**Designer:** Unidentified in the consulted primary specimens

**Foundry:** Marder, Luse & Co., Chicago

**Observed:** Directly sampled alphabet and figures: ABCDEFGHIJKLMNOPQRSTUWabcdefghilmnoprstuvwyz1234567. Additional observed symbols and exact crop/cleanup settings are enumerated in source/tracing.json.

**Reconstructed:** Inferred alphabet/figures: VXYZjkqx089. Unobserved punctuation and symbols are newly drawn MIT project companions. Spacing, kerning and optical-size harmonisation are new. Uppercase and lowercase are distinct. The year identifies the specimen, not a claimed first release.

## Sources

1. [John Ryan Foundry, Latest and Standard Faces in Type (September 1894), printed p. 100](https://archive.org/details/lateststandardfa00ryan/page/100/mode/1up) — 1894 US publication, beyond the maximum 95-year term. Library of Congress scan; institutional rights statement retained in reference/ryan-rights.json. [Rights basis](https://archive.org/metadata/lateststandardfa00ryan).
2. [American Type Founders, Collective Specimen Book (1895/96), printed p. 428](https://www.galleyrack.com/images/artifice/letters/press/noncomptype/typography/atf/atf-collective-specimen-garland-badscan/atf-1896-specimens-of-type-garland-1981-smallpart-292-marine-series-and-mansfield-series-marder-luse-foundry-publicdomain.pdf) — Historical 1895/96 US specimen page, public domain under the maximum 95-year term; scanned from the 1981 Garland facsimile. This reference contains only the nineteenth-century page, not the modern introduction. Rendered at 400 dpi in grayscale from the linked PDF. [Rights basis](https://www.circuitousroot.com/artifice/letters/press/noncomptype/typography/atf/atf-collective-specimen-garland-badscan/index.html).

Source images are in `reference/`; the source record is [font.json](font.json).
Historical reference material retains the rights status recorded there.
The digital revival is released under the included [MIT License](LICENSE).

## Build or improve

From the repository root:

```sh
python scripts/fontrevival.py build marine-1894
python scripts/fontrevival.py check marine-1894
```

Edit `source/font.ttx` or export an individual glyph with
`python scripts/fontrevival.py glyph marine-1894 j`.
Follow the shared [revival workflow](../../docs/WORKFLOW.md) for additions and revisions.
