# Changes

## 1.002

- Replace the continuous grayscale experiment with three disjoint tone regions:
  primary ink (100%), secondary engraving (55%) and pale strokes (25%).
- Expose per-region colour and opacity variables in multi-tone SVGs. Retain the
  unchanged solid icon, character assignment and spacing.
- Replace grayscale downloads and layers with multi-tone SVG, sprite and PNG.
- Embed SVG paths directly in gallery previews so local file:// viewing works.
  Check actual geometry and rendered screenshots on disk as well as over HTTP.
- Supply complete HTML examples for tritone images, independently coloured sprite
  regions, local inline SVG, and monochrome icon fonts. Add familiar theme and
  subject tags for gallery search.
- Include a downloadable web bundle with matching example paths, extraction
  instructions and the license. Remove collection-wide Victorian/vintage tags.

## 1.001

- Add a grayscale version using 13 nonempty layers from a 16-step tonal trace.
  Retain the measured scan darkness with transparent paper; do not invent shading.
- Keep the tone outlines in the same CFF master, registered with the unchanged
  monochrome icon. Tonal glyphs are unencoded; U+E000 and its spacing are unchanged.
- Generate grayscale SVGs, a tonal sprite and transparent PNGs. The standard
  icon fonts remain monochrome. Add three-way source/gray/solid comparisons.

## 1.000

- Initial single-icon pilot: Father Christmas, Central Type Foundry cut No. 4202,
  printed p. 273 of the Boston Type Foundry specimen (1889).
- Preserve the detailed historical impression and aspect ratio, with transparent
  SVG, sprite, desktop/web fonts, named CSS and source-comparison proofs.
- Retain provenance, tracing parameters, CFF master and stable U+E000 mapping.
- Record missing Boston pages 217–218 and the remaining scope as pending.
