"""Optional vector operations for source preparation, never release builds.

Install requirements-tracing.txt. Inputs and outputs are SVG paths in font units.
"""

from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.svgLib.path import parse_path


def _path(svg):
    import pathops

    if pathops.__version__ != "0.9.0":
        raise ValueError("Source geometry requires skia-pathops 0.9.0.")
    path = pathops.Path()
    parse_path(svg, path.getPen())
    return path


def _svg(path):
    pen = SVGPathPen(None)
    path.draw(RoundingPen(pen))
    return pen.getCommands()


def simplify(svg):
    """Resolve overlapping contours while preserving their nonzero fill."""
    import pathops

    return _svg(pathops.simplify(_path(svg))) if svg else ""


def shadow(svg, dx, dy):
    """Return the translated silhouette minus the original, with no raster step."""
    import pathops

    if not svg:
        return ""
    original = _path(svg)
    shifted = original.transform(1, 0, 0, 1, dx, dy)
    return _svg(pathops.op(shifted, original, pathops.PathOp.DIFFERENCE))
