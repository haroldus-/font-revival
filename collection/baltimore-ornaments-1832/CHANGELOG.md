# Changes

## 1.002

- Repair 20 downloadable ornament drawings that exceed signed 16-bit renderer point counts.
- Keep downloadable CFF outlines within 32,767 points and TrueType outlines within 32,763 points, allowing for four renderer metric points. Reviewed reductions target at most 32,000 points in both formats.
- Preserve the full-detail master, SVGs, tonal PNGs, icon identities, advances and historical proportions. Retain a [before/after font review](specimens/font-compatibility-review.pdf), a [focused example](specimens/font-compatibility-example.pdf), and measured preparation settings.
- Record the reviewed compact-font bounds in individual sizing rules while retaining the historical master ranges and exact advances.

## 1.001

- Review the complete family and straighten 230 icons using measured baselines, frames, opposing tips or containing strip axes.
- Preserve all contours, tone registration, proportions and advances; retain matrices and before/after proofs.
- Regenerate fonts, full-detail SVG/PNG artwork, specimens and downloads.

## 1.000

- Initial revival of 396 ornaments from the 1832 Baltimore specimen.
- Preserve source crops, public-domain evidence, stable Private Use assignments, and the canonical CFF master.
- Generate monochrome and three-tone SVGs, icon fonts, PNGs, comparison proofs and web bundles.
- Split long downloadable CFF programs into lossless subroutines for browser compatibility.
