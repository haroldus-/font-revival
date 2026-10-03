# Changes

## 1.003

- Repair 60 downloadable cut drawings that exceed signed 16-bit renderer point counts, including the missing eagle and shield at No. 103.
- Keep downloadable CFF outlines within 32,767 points and TrueType outlines within 32,763 points, allowing for four renderer metric points. Reviewed reductions target at most 32,000 points in both formats.
- Preserve the full-detail master, SVGs, tonal PNGs, icon identities, advances and historical proportions. Retain a [before/after font review](specimens/font-compatibility-review.pdf), a [focused example](specimens/font-compatibility-example.pdf), and measured preparation settings.
- Extend coverage screening to Nos. 133, 232, 239, 244, 359 and 367 to preserve their shading within the compatible point limit. Record the compact-font bounds in individual sizing rules.

## 1.002

- Restore the complete observed upper boundaries of all 24 small New England Primer panels, Nos. 357-01–357-24, from the original scan on PDF page 209.
- Recover clipped frame rules and illustration detail, including the lion's tail and the standing figure's head in No. 357-24. Preserve gaps and irregularities in the historical impression.
- Keep the original scan-to-font scale, position, advance widths, character assignments and reviewed rotations. Apply the same crop correction to monochrome and all three tone layers.
- Record the old recipes, revised boundaries and outline hashes in `source/primer-top-review.json`; retain a repeatable preparation helper, [source and size comparison](specimens/primer-top-review.pdf), and [font comparison](specimens/primer-font-comparison.pdf).

## 1.001

- Visually survey all 381 cuts and straighten 167 using measured frame edges, ground lines or outer oval axes, including Nos. 65, 70 and Primer 357-16.
- Apply the same rigid rotation to monochrome, three-tone and compact font drawings, retaining every illustration contour and advance. Record all decisions and matrices in `source/straightening.json`; store rotated coordinates to 1/64 unit.
- Retain before/after display-size proofs and regenerate all artwork, fonts and gallery assets.
- Remove one detached price-numeral fragment beside No. 70 in its pale tone layer.
- Correct the subject labels for No. 49 (traveller) and No. 292 (paddle steamboat).

## 1.000

- Initial revival of 381 cuts from the 1832 Baltimore specimen.
- Preserve source crops, public-domain evidence, stable Private Use assignments, and the canonical CFF master.
- Generate monochrome and three-tone SVGs, icon fonts, PNGs, comparison proofs and web bundles.
- Split long downloadable CFF programs into lossless subroutines for browser compatibility.
