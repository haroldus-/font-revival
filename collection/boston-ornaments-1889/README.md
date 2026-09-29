# Boston Ornaments 1889

Word ornaments, floral details, border components and corners from the Boston Type Foundry specimen of 1889.

![Historical scan beside the vector revival](specimens/preview.png)

**715 icon(s) · Version 1.000 · MIT**

[SVG files](svg/) · [SVG sprite](web/icons.svg) · [OTF](fonts/BostonOrnaments1889-Regular.otf) · [TTF](fonts/BostonOrnaments1889-Regular.ttf) · [WOFF2](web/BostonOrnaments1889-Regular.woff2) · [Comparison and size proof](specimens/specimen.pdf) · [Icon manifest](icons.json) · [Changes](CHANGELOG.md)

[Three-tone SVGs](svg/multitone/) · [Three-tone sprite](web/icons-multitone.svg) · [Transparent multitone PNGs](png/multitone/)

## Use in HTML

[Download the web bundle (ZIP)](downloads/boston-ornaments-1889-web.zip), unzip it, and place
the extracted `collection` folder beside your HTML file. Keep its subfolders
together. The examples below then work as written; adjust the paths if you move
the folder elsewhere. The bundle contains SVGs, PNGs, fonts, CSS, instructions
and the license. No JavaScript or font installation is needed for SVG use.

### Tritone image — works from disk too

The individual SVG displays all three tones at their default strengths, with a
transparent background. Change `height` to resize it; the proportions are retained.

```html
<img src="collection/boston-ornaments-1889/svg/multitone/boston-1889-p258-word-1-1.svg"
     alt="Solid triangular terminal, left, 12 point" height="96">
```

An `<img>` has its own colour context: page CSS cannot recolour its internal
regions. For a decorative image beside a text label, use `alt=""` instead.

### Tritone sprite — customise every tone

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
<svg class="revival-cut" role="img" aria-label="Solid triangular terminal, left, 12 point">
  <use href="collection/boston-ornaments-1889/web/icons-multitone.svg#boston-1889-p258-word-1-1"></use>
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
the solid artwork; use the SVG examples above for tritone artwork.

```html
<link rel="stylesheet" href="collection/boston-ornaments-1889/web/icons.css">
<span class="fr-icon fr-boston-1889-p258-word-1-1" aria-hidden="true"
      style="font-size:96px;color:#a5422c"></span>
<span>Solid triangular terminal, left, 12 point</span>
```

The example hides a decorative icon from screen readers and supplies visible
text. For an icon that conveys meaning on its own, use `role="img"` and an
`aria-label` instead of `aria-hidden`. Font size and colour use ordinary CSS.

Install the OTF or TTF for desktop use. The manifest lists Private Use codepoints
(pilot: U+E000); these are not ordinary text characters. IDs and
codepoints are permanent within this collection. Keep the included LICENSE with
redistributed assets. Detailed cuts need display sizes: the pilot is recommended
from 32 px, with 16–192 pt proofs supplied for review.

## Evidence and editing

**Foundry:** Boston Type Foundry; Central Type Foundry credited on the ornament plates

**Designer:** Individual designers and engravers unidentified

**Observed:** Individually catalogued historical impressions from the 1889 Boston specimen; see each icon and source/inventory.json for subjects, pages, specimen numbers, crop evidence and review status.

**Interpreted or new:** No new pictorial content. Thresholding, documented crop cleanup, cubic curve fitting and font-unit rounding interpret the scanned impressions. Names, search tags, Private Use assignments, scale and bearings are new project work. Paper, catalogue numbers and prices are excluded. Multi-tone companions separate observed ink strengths into three disjoint vector regions at default opacities 1, 0.55 and 0.25; these are modern interpretations, not evidence of separately printed inks.

- [Specimen book from the Boston type foundry (1889), printed p. 258; PDF page 266, Internet Archive leaf 266](https://archive.org/details/specimenbookfrom00unse/page/258/mode/1up) — 1889 US publication; public domain in the United States under the maximum 95-year term. Library of Congress scan hosted by Internet Archive; its recorded assessment says the Library is unaware of copyright restrictions. Metadata and page map are retained locally. No modern redraw was used. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
- [Specimen book from the Boston type foundry (1889), printed p. 259; PDF page 267, Internet Archive leaf 267](https://archive.org/details/specimenbookfrom00unse/page/259/mode/1up) — 1889 US publication; public domain in the United States under the maximum 95-year term. Library of Congress scan hosted by Internet Archive; its recorded assessment says the Library is unaware of copyright restrictions. Metadata and page map are retained locally. No modern redraw was used. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
- [Specimen book from the Boston type foundry (1889), printed p. 260; PDF page 268, Internet Archive leaf 268](https://archive.org/details/specimenbookfrom00unse/page/260/mode/1up) — 1889 US publication; public domain in the United States under the maximum 95-year term. Library of Congress scan hosted by Internet Archive; its recorded assessment says the Library is unaware of copyright restrictions. Metadata and page map are retained locally. No modern redraw was used. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
- [Specimen book from the Boston type foundry (1889), printed p. 261; PDF page 269, Internet Archive leaf 269](https://archive.org/details/specimenbookfrom00unse/page/261/mode/1up) — 1889 US publication; public domain in the United States under the maximum 95-year term. Library of Congress scan hosted by Internet Archive; its recorded assessment says the Library is unaware of copyright restrictions. Metadata and page map are retained locally. No modern redraw was used. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
- [Specimen book from the Boston type foundry (1889), printed p. 262; PDF page 270, Internet Archive leaf 270](https://archive.org/details/specimenbookfrom00unse/page/262/mode/1up) — 1889 US publication; public domain in the United States under the maximum 95-year term. Library of Congress scan hosted by Internet Archive; its recorded assessment says the Library is unaware of copyright restrictions. Metadata and page map are retained locally. No modern redraw was used. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
- [Specimen book from the Boston type foundry (1889), printed p. 263; PDF page 271, Internet Archive leaf 271](https://archive.org/details/specimenbookfrom00unse/page/263/mode/1up) — 1889 US publication; public domain in the United States under the maximum 95-year term. Library of Congress scan hosted by Internet Archive; its recorded assessment says the Library is unaware of copyright restrictions. Metadata and page map are retained locally. No modern redraw was used. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
- [Specimen book from the Boston type foundry (1889), printed p. 269; PDF page 277, Internet Archive leaf 277](https://archive.org/details/specimenbookfrom00unse/page/269/mode/1up) — 1889 US publication; public domain in the United States under the maximum 95-year term. Library of Congress scan hosted by Internet Archive; its recorded assessment says the Library is unaware of copyright restrictions. Metadata and page map are retained locally. No modern redraw was used. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
- [Specimen book from the Boston type foundry (1889), printed p. 270; PDF page 278, Internet Archive leaf 278](https://archive.org/details/specimenbookfrom00unse/page/270/mode/1up) — 1889 US publication; public domain in the United States under the maximum 95-year term. Library of Congress scan hosted by Internet Archive; its recorded assessment says the Library is unaware of copyright restrictions. Metadata and page map are retained locally. No modern redraw was used. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
- [Specimen book from the Boston type foundry (1889), printed p. 264; PDF page 272, Internet Archive leaf 272](https://archive.org/details/specimenbookfrom00unse/page/264/mode/1up) — 1889 US publication; public domain in the United States under the maximum 95-year term. Library of Congress scan hosted by Internet Archive; its recorded assessment says the Library is unaware of copyright restrictions. Metadata and page map are retained locally. No modern redraw was used. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
- [Specimen book from the Boston type foundry (1889), printed p. 265; PDF page 273, Internet Archive leaf 273](https://archive.org/details/specimenbookfrom00unse/page/265/mode/1up) — 1889 US publication; public domain in the United States under the maximum 95-year term. Library of Congress scan hosted by Internet Archive; its recorded assessment says the Library is unaware of copyright restrictions. Metadata and page map are retained locally. No modern redraw was used. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
- [Specimen book from the Boston type foundry (1889), printed p. 266; PDF page 274, Internet Archive leaf 274](https://archive.org/details/specimenbookfrom00unse/page/266/mode/1up) — 1889 US publication; public domain in the United States under the maximum 95-year term. Library of Congress scan hosted by Internet Archive; its recorded assessment says the Library is unaware of copyright restrictions. Metadata and page map are retained locally. No modern redraw was used. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
- [Specimen book from the Boston type foundry (1889), printed p. 267; PDF page 275, Internet Archive leaf 275](https://archive.org/details/specimenbookfrom00unse/page/267/mode/1up) — 1889 US publication; public domain in the United States under the maximum 95-year term. Library of Congress scan hosted by Internet Archive; its recorded assessment says the Library is unaware of copyright restrictions. Metadata and page map are retained locally. No modern redraw was used. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).
- [Specimen book from the Boston type foundry (1889), printed p. 268; PDF page 276, Internet Archive leaf 276](https://archive.org/details/specimenbookfrom00unse/page/268/mode/1up) — 1889 US publication; public domain in the United States under the maximum 95-year term. Library of Congress scan hosted by Internet Archive; its recorded assessment says the Library is unaware of copyright restrictions. Metadata and page map are retained locally. No modern redraw was used. [Rights basis](https://www.copyright.gov/circs/circ15a.pdf).

Copyright (c) 2026 Harold Lehmann. Historical public-domain material retains its status.
Read [the method](source/METHOD.md), [inventory](source/inventory.json) and
[icon workflow](../../docs/ICONS.md). The canonical master is `source/font.ttx`;
SVGs, sprite, fonts and manifests are generated from it with glyph edits applied.

```sh
python scripts/fontrevival.py build boston-ornaments-1889
python scripts/fontrevival.py sizecheck boston-ornaments-1889
python scripts/fontrevival.py check boston-ornaments-1889
python scripts/fontrevival.py glyph boston-ornaments-1889 uniE000
```
