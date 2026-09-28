#!/usr/bin/env python3
"""Repeat the 1.002 optical sizing edits from the unchanged historical master.

Copyright (c) 2026 Harold Lehmann. MIT licensed; see ../LICENSE.
Run from any directory with the repository's pinned requirements installed.
"""

import json
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

SOURCE = Path(__file__).resolve().parent
TARGETS = {
    "t": (390, 700, 0,
          "Restore the observed ascender-height t: the 12-point No. 2 '6th' crop on "
          "Inland Printer p. 137 is 38 pixels high, like neighbouring h. The initial "
          "master incorrectly normalised it to the 480-unit body height. Resize to "
          "390 by 700 units, centred in the unchanged 600-unit cell."),
    "e": (460, 492, -6,
          "Optical adjustment of the observed e from 'Spindler' on Inland Printer "
          "p. 137: widen the 430-unit bowl to 460 and add 6 units of overshoot above "
          "and below the 480-unit body. This is a new proportion adjustment, not a "
          "claim of exact historical dimensions. Preserve its traced contours and "
          "the 600-unit advance."),
}


def main():
    with TTFont(recalcTimestamp=False) as font:
        font.importXML(SOURCE / "font.ttx")
        glyphs = font.getGlyphSet()
        for name, (width, height, bottom, notes) in TARGETS.items():
            bounds = BoundsPen(glyphs)
            glyphs[name].draw(bounds)
            x0, y0, x1, y1 = bounds.bounds
            advance = font["hmtx"][name][0]
            sx, sy = width / (x1 - x0), height / (y1 - y0)
            pen = SVGPathPen(glyphs, ntos=lambda value: f"{value:.3f}")
            glyphs[name].draw(TransformPen(pen, (
                sx, 0, 0, sy, (advance - width) / 2 - x0 * sx, bottom - y0 * sy)))
            data = {"glyph": name, "advance_width": advance,
                    "path": pen.getCommands(), "notes": notes}
            output = SOURCE / "glyphs" / f"{name}.json"
            output.parent.mkdir(exist_ok=True)
            output.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
