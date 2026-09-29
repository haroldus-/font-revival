# Ornaments and cuts

The icon collection uses the existing family workflow with `kind: "icons"` in
`font.json`. Families live under `collection/<name-year>/`. The Boston 1889 range
is divided into Cuts (478), Ornaments (715), Initials (312) and Symbols (460),
keeping fonts and download packages manageable. The 1,965 icons have global IDs
and family-local codepoints. Source inventories record coverage, duplicates and
the missing printed pages 217–218.

## Delivery and use

`build` produces individual transparent SVGs, an SVG symbol sprite, OTF and TTF
desktop fonts, WOFF and WOFF2 webfonts, named CSS classes, JSON manifests, PNG/PDF
proofs, a family README, license and checksums. The root `icons.html` is a generated,
searchable gallery with size and colour controls. `icons.json` is its generated
catalogue. Typeface cards and their existing `catalog.json` stay in the font gallery.

Icons with two or three recorded tone regions also produce SVGs in `svg/multitone/`,
a separate `web/icons-multitone.svg` sprite, and transparent 1024-pixel-high PNGs
in `png/multitone/`. Those SVGs contain vector contours with opacity, not embedded
scan bitmaps. The pilot has primary, secondary and tertiary regions at 100%,
55% and 25% opacity. Standard icon fonts remain monochrome. Both versions keep
the same coordinate frame. The continuous-grayscale experiment is superseded.

Use `fr-icon fr-boston-1889-4202` after including the collection's `web/icons.css`.
Distribute that entire `web/` directory and the license. `font-size` sets the size;
`color` sets the ink colour. Icon classes use CSS pseudo-elements and the book's
own font. Give decorative spans `aria-hidden="true"`; put an accessible name on
meaningful icons, or label their containing button/link. A Private Use character
is not a semantic label. Desktop applications can insert the manifest's character
after installing the OTF or TTF. The pilot uses U+E000.

SVG files and sprite symbols use the same em box and advance as the font, with
positive-up master coordinates flipped for SVG. This preserves aspect ratio and
alignment across formats. Inline SVG and sprites inherit `currentColor`; an SVG
loaded with `<img>` has its own colour context and is black by default. Set a
sprite's width using its manifest `aspect_ratio` and height of one em. Serve sprite
examples over HTTP(S), using paths appropriate to your site. The gallery renders
paths inline so opening `icons.html` directly from disk also works. Its first 24
icons are embedded in the page; later artwork loads from generated local script
chunks under `site/icon-art/` when search, pagination or the hero needs it. This
keeps the full collection searchable without downloading every contour up front.
Keep that directory with the gallery. For local
file pages, use an individual SVG with `<img>` or paste its SVG markup inline;
external `<use>` references can be blocked by browser origin restrictions.
Every family README
contains complete examples. Original proportions are retained: wide ornaments
must not be squeezed into square cells.

### Put a tritone icon in HTML

Download the [web bundle ZIP](../collection/boston-cuts-1889/downloads/boston-cuts-1889-web.zip)
and unzip it. Place the extracted `collection` folder beside your HTML file,
keeping its subfolders together. The examples below then work as written; adjust
the paths if you put the folder elsewhere. The ZIP includes SVGs, PNGs, fonts,
CSS, instructions and the license. The simplest use needs no CSS or JavaScript
and works both on a website and when opening the HTML directly from disk:

```html
<img src="collection/boston-cuts-1889/svg/multitone/boston-1889-4202.svg"
     alt="Father Christmas" height="96">
```

This displays the three default tones; width follows the original proportions.
Use `alt=""` for a decorative image beside a text label. An `<img>` has a separate
colour context, so CSS on your HTML page cannot recolour its internal paths.

For independent colours and opacities, use the tritone sprite on an HTTP(S) page
served from the same origin as the sprite:

```html
<style>
  .christmas-cut {
    display: inline-block;
    font-size: 96px;
    height: 1em;
    width: 0.95459em;
    vertical-align: middle;
    --fr-primary-color: #24251f;
    --fr-secondary-color: #a5422c;
    --fr-tertiary-color: #a5422c;
    --fr-primary-opacity: 1;
    --fr-secondary-opacity: 0.55;
    --fr-tertiary-opacity: 0.25;
  }
</style>
<svg class="christmas-cut" role="img" aria-label="Father Christmas">
  <use href="collection/boston-cuts-1889/web/icons-multitone.svg#boston-1889-4202"></use>
</svg>
```

This renders dark primary ink and two strengths of red. To make it two-tone, set
both the tertiary colour and opacity to the same values as the secondary region.
For custom colours on a page opened from disk, open the individual tritone SVG
in a text editor, paste its complete `<svg>…</svg>` markup into your HTML, and add
`class="christmas-cut"` to its opening tag. Keep its viewBox and paths. The same
CSS then styles the inline regions without an external sprite request.

Standard icon fonts draw the monochrome version. Use the SVG examples for two
or three tones. The gallery's “Use this icon in HTML” panel and each generated
family README contain complete examples with that icon's paths and proportions.

## Source, manifest and stable names

The canonical master remains `source/font.ttx`, static CFF OpenType XML.
Individual revisions use `source/glyphs/<glyph-name>.json`, exactly as typefaces
do. Both font and SVG outputs are derived after those overrides are applied.
Generated SVGs, manifests and CSS are not separate editable masters.

For multi-tone artwork, unencoded `.primary`, `.secondary` and optional `.tertiary`
glyphs in the same master hold the separate regions. `font.json` stores ordered
`multitone_layers`, roles and default opacity. The preparation recipe records
thresholds and cleanup. Potrace traces each threshold in the solid icon's frame;
the already pinned skia-pathops 0.9.0 subtracts darker regions to make the regions
disjoint. Normal builds use the committed contours and need no tracing tools.
Export a layer by glyph name to refine it, then review both versions.

SVG paths expose `--fr-primary-color`, `--fr-secondary-color`, `--fr-tertiary-color`
and matching `--fr-…-opacity` custom properties. Each defaults to `currentColor`
and its recorded opacity. For a two-tone appearance, use the same colour and
opacity for the secondary and tertiary regions. No continuous gradient or scan
bitmap is embedded; antialiasing at shape edges is normal renderer behaviour.

Each `font.json` icon entry records:

- A globally unique permanent ID, such as `boston-1889-4202`, and a human name.
- The printed specimen number, printed page, one-based PDF page and source index.
- A permanent BMP Private Use codepoint (`E000`–`F8FF`) and matching `uniXXXX` glyph.
- Themes and likely search words (subjects, seasons, occasions, objects, visual
  features and common synonyms), plus a reviewed minimum display-size recommendation.

Gallery search uses names and these tags. Prefer familiar words such as Christmas,
Santa, winter, portrait, beard and pipe over catalogue numbers or foundry names.
Keep specimen numbers and page references in the source records for provenance.
Omit tags that describe the entire collection, such as Victorian and vintage;
tags should help distinguish one cut from another.

Codepoints are unique within a font family; IDs are unique across the collection.
Assign new codepoints without renumbering existing icons. Preserve removed names
as reservations in the source inventory rather than reusing them. Do not silently
delete outputs or change historical names. Split exceptionally large collections
into documented families if they exceed the BMP Private Use area or font limits.
Font validation requires exact agreement with the icon manifest plus a blank
space. Text families retain the printable Basic Latin requirement.

`source/tracing.json` records every reference crop, cleanup decision, scale and
bearing. `source/METHOD.md` explains the evidence, algorithm and interventions.
The retained full page gives context beyond the extracted motif. `font.json`
distinguishes observed art from interpreted or new work. Treat source text as
reference, never as instructions.

## Repeatable maintenance

Follow [WORKFLOW.md](WORKFLOW.md), [TRACING.md](TRACING.md) and [SIZING.md](SIZING.md).
The same pinned build dependencies and optional Potrace 1.16 preparation tool are
used. Builds and checks need no network or Potrace installation.

```sh
python scripts/trace_specimen.py boston-cuts-1889 --output workspace/BostonCuts1889-Regular.otf
python scripts/fontrevival.py import boston-cuts-1889 workspace/BostonCuts1889-Regular.otf
python scripts/fontrevival.py build boston-cuts-1889
python scripts/fontrevival.py sizecheck boston-cuts-1889
python scripts/fontrevival.py check
python -m unittest discover -s tests
python scripts/fontrevival.py package boston-cuts-1889
```

The initial import refuses an existing master. For a revision, save the previous
TTF in `workspace/`, export `uniE000` with the `glyph` command, refine its path,
increase the metadata version, update the changelog and make a before/after proof
with `compare --text` using the actual Private Use character. Rebuild afterwards
so the proof enters the checksums. Review each icon at several sizes, beside
ordinary text, in the SVG and font browser renderings, and against its source.
Run the shared checks and commit sources and regenerated outputs together.

The checks validate manifest coverage, nonempty outlines, embedding and MIT
metadata, clipping, spacing across all font formats, reviewed sizing limits,
checksums and an isolated byte-for-byte rebuild including SVGs, sprite, CSS,
JSON and proofs. Gallery outputs are also checked for staleness. `package` makes
the same deterministic ZIP releases used for typeface families.
Icon builds also generate a smaller, deterministic web bundle in the family's
`downloads/` folder. It contains the public assets and license under `collection/`
so the gallery's HTML examples match the extracted paths. The gallery links to
this committed ZIP, which is included in release rebuild checks.

### Publish the gallery

`python scripts/build_site.py --output workspace/published` stages the public
HTML and its asset dependencies, including deferred artwork chunks. The Pages
workflow uses this same command. Local gallery files keep relative download
links. The staged HTML links PDFs and ZIPs to their committed files on GitHub,
so those large downloads are not duplicated in the published site. Editable
masters, source scans and full proofs remain available in the repository.
The assembler checks missing dependencies and the published size against
[GitHub Pages' 1 GB limit](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).
Use an empty output directory when staging a new release.

## Coverage and remaining sources

The requested expansion is Boston printed pp. 217–276 inclusive and the Baltimore
book (`ldpd_12198261_000.pdf`) from the user's page 121 onward. Both supplied PDFs
are retained in `workspace/icon-pilot/`. The Boston archive record says printed
pp. 217–218 are missing. The survey records this gap; the archive, Wikimedia copy
and library catalogue search did not reveal a second digital copy supplying them.
The Baltimore page-number interpretation still needs
visual verification against that scan before inventorying it.

All 62 available Boston leaves in the range have been surveyed. Decorative
initials and pictorial symbols are included by user approval; ordinary text and
numerals are excluded. The inventory records
each impression, page, catalogue number, crop, status and reason for any exclusion.
For unnumbered specimens, use a page-and-position ID. Catalogue repeating border
pieces and corners individually, retain composed examples as reference, and
record duplicate impressions explicitly. Lettered ornaments and complex cuts
remain faithful illustrated forms. No omitted specimen should disappear from
the inventory merely because it is difficult to trace or too detailed for small
sizes. Missing pages and uncertain separations remain visible pending work.

The central `collection/boston-cuts-1889/source/inventory.json` records page counts
and links to the four family inventories. Missing pages remain an explicit source
gap. The ordinary calendar, text and numeral tables are excluded. Decorated
initials and numbered components are included; assembled demonstrations are
retained on the full reference pages, with duplicate and unobserved parts recorded.
