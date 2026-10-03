# Baltimore Initials 1832

Historical initials from A specimen of printing types and ornaments from the Baltimore Type Foundry (1832).

![Historical scan beside the vector revival](specimens/preview.png)

**38 icon(s) · Version 1.001 · MIT**

[SVG files](svg/) · [SVG sprite](web/icons.svg) · [OTF](fonts/BaltimoreInitials1832-Regular.otf) · [TTF](fonts/BaltimoreInitials1832-Regular.ttf) · [WOFF2](web/BaltimoreInitials1832-Regular.woff2) · [Comparison and size proof](specimens/specimen.pdf) · [Icon manifest](icons.json) · [Changes](CHANGELOG.md)

[Three-tone SVGs](svg/multitone/) · [Three-tone sprite](web/icons-multitone.svg) · [Transparent three-tone PNGs](png/multitone/)

## Use in HTML

[Download the web bundle (ZIP)](downloads/baltimore-initials-1832-web.zip), unzip it, and place
the extracted `collection` folder beside your HTML file. Keep its subfolders
together. The examples below then work as written; adjust the paths if you move
the folder elsewhere. The bundle contains SVGs, PNGs, fonts, CSS, instructions
and the license. No JavaScript or font installation is needed for SVG use.

### Three-tone image — works from disk too

The individual SVG displays all three tones at their default strengths, with a
transparent background. Change `height` to resize it; the proportions are retained.

```html
<img src="collection/baltimore-initials-1832/svg/multitone/baltimore-1832-p59-six-line-pica-ornamented-m.svg"
     alt="Six Line Pica Ornamented letter M" height="96">
```

An `<img>` has its own colour context: page CSS cannot recolour its internal
regions. For a decorative image beside a text label, use `alt=""` instead.

### Three-tone sprite — customise every tone

Copy `web/icons-multitone.svg` and use the following complete example on an
HTTP(S) page served from the same origin as the sprite. It draws dark primary ink
and two strengths of red. Each colour and opacity can be changed independently.

```html
<style>
  .revival-cut {
    display: inline-block;
    font-size: 96px;
    height: 1em;
    width: 0.941406em;
    vertical-align: middle;
    --fr-primary-color: #24251f;
    --fr-secondary-color: #a5422c;
    --fr-tertiary-color: #a5422c;
    --fr-primary-opacity: 1;
    --fr-secondary-opacity: 0.55;
    --fr-tertiary-opacity: 0.25;
  }
</style>
<svg class="revival-cut" role="img" aria-label="Six Line Pica Ornamented letter M">
  <use href="collection/baltimore-initials-1832/web/icons-multitone.svg#baltimore-1832-p59-six-line-pica-ornamented-m"></use>
</svg>
```

Use the same secondary and tertiary colour and opacity for a two-tone appearance.
The defaults are primary 100%, secondary 55% and tertiary 25%; these are separate
vector regions, not a gradient. The tone assignments interpret the historical
impression. A transparent PNG of the default tones is also provided.

External SVG sprites can be blocked on `file://` pages. To customise tones on a
page opened from disk, open the individual SVG in a text editor, copy its complete
`<svg>…</svg>` markup into your HTML, and add `class="revival-cut"` to that SVG.
The same CSS above then applies to its inline paths. Keep its `viewBox` and paths.
The gallery itself uses inline SVG so its previews work directly from disk.

### Monochrome icon font

Copy the whole `web/` folder, including CSS and webfonts. Standard icon fonts show
the solid artwork; use the SVG examples above for three-tone artwork.

```html
<link rel="stylesheet" href="collection/baltimore-initials-1832/web/icons.css">
<span class="fr-icon fr-baltimore-1832-p59-six-line-pica-ornamented-m" aria-hidden="true"
      style="font-size:96px;color:#a5422c"></span>
<span>Six Line Pica Ornamented letter M</span>
```

The example hides a decorative icon from screen readers and supplies visible
text. For an icon that conveys meaning on its own, use `role="img"` and an
`aria-label` instead of `aria-hidden`. Font size and colour use ordinary CSS.

Install the OTF or TTF for desktop use. The manifest lists Private Use codepoints
(pilot: U+E000); these are not ordinary text characters. IDs and
codepoints are permanent within this collection. Keep the included LICENSE with
redistributed assets. Detailed cuts need display sizes: the pilot is recommended
from 64 px, with 16–192 pt proofs supplied for review.

## Evidence and editing

**Foundry:** Baltimore Type Foundry; F. Lucas, Jr., agent

**Designer:** Baltimore Type Foundry; individual engravers generally unidentified (signed large cuts credited in the source inventory)

**Observed:** Observed impressions from the supplied 1832 Baltimore specimen. Every crop is mapped to a one-based PDF page of this unpaginated book; original JP2 leaves and exact preparation records are retained.

**Interpreted or new:** No new pictorial content. Thresholding, documented crop cleanup, cubic curve fitting and font-unit rounding interpret the scanned impressions. Names, search tags, Private Use assignments, scale and bearings are new project work. Paper, catalogue numbers and prices are excluded. Multi-tone companions separate observed ink strengths into three disjoint vector regions at default opacities 1, 0.55 and 0.25; these are modern interpretations, not evidence of separately printed inks. Version 1.001 applies reviewed rigid rotations to 22 icons to level measured horizontal references, preserving every contour, original scale and advance; source/straightening.json records the evidence and matrices.

- [A specimen of printing types and ornaments from the Baltimore Type Foundry (1832), unnumbered leaf; PDF page 59, Internet Archive leaf 58](https://archive.org/details/ldpd_12198261_000/page/n58/mode/1up) — 1832 US publication, public domain by age; Columbia University Libraries historical scan, distributed through Internet Archive. DPLA item c773fb687c8cc1c610a04becf6baf8e2 records Public domain. No modern digital font or redrawing was used. The MIT license applies to original project work, not ownership of the historical design. [Rights basis](https://dp.la/item/c773fb687c8cc1c610a04becf6baf8e2).
- [A specimen of printing types and ornaments from the Baltimore Type Foundry (1832), unnumbered leaf; PDF page 65, Internet Archive leaf 64](https://archive.org/details/ldpd_12198261_000/page/n64/mode/1up) — 1832 US publication, public domain by age; Columbia University Libraries historical scan, distributed through Internet Archive. DPLA item c773fb687c8cc1c610a04becf6baf8e2 records Public domain. No modern digital font or redrawing was used. The MIT license applies to original project work, not ownership of the historical design. [Rights basis](https://dp.la/item/c773fb687c8cc1c610a04becf6baf8e2).
- [A specimen of printing types and ornaments from the Baltimore Type Foundry (1832), unnumbered leaf; PDF page 67, Internet Archive leaf 66](https://archive.org/details/ldpd_12198261_000/page/n66/mode/1up) — 1832 US publication, public domain by age; Columbia University Libraries historical scan, distributed through Internet Archive. DPLA item c773fb687c8cc1c610a04becf6baf8e2 records Public domain. No modern digital font or redrawing was used. The MIT license applies to original project work, not ownership of the historical design. [Rights basis](https://dp.la/item/c773fb687c8cc1c610a04becf6baf8e2).
- [A specimen of printing types and ornaments from the Baltimore Type Foundry (1832), unnumbered leaf; PDF page 69, Internet Archive leaf 68](https://archive.org/details/ldpd_12198261_000/page/n68/mode/1up) — 1832 US publication, public domain by age; Columbia University Libraries historical scan, distributed through Internet Archive. DPLA item c773fb687c8cc1c610a04becf6baf8e2 records Public domain. No modern digital font or redrawing was used. The MIT license applies to original project work, not ownership of the historical design. [Rights basis](https://dp.la/item/c773fb687c8cc1c610a04becf6baf8e2).

Copyright (c) 2026 Harold Lehmann. Historical public-domain material retains its status.
Read [the method](source/METHOD.md), [inventory](source/inventory.json) and
[icon workflow](../../docs/ICONS.md). The canonical master is `source/font.ttx`;
SVGs, sprite, fonts and manifests are generated from it with glyph edits applied.

```sh
python scripts/fontrevival.py build baltimore-initials-1832
python scripts/fontrevival.py sizecheck baltimore-initials-1832
python scripts/fontrevival.py check baltimore-initials-1832
python scripts/fontrevival.py glyph baltimore-initials-1832 uniE000
```
