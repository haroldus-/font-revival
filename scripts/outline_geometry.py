"""Optional vector operations for source preparation, never release builds.

Install requirements-tracing.txt. Inputs and outputs are SVG paths in font units.
"""

from fontTools.misc.bezierTools import splitCubicAtT, splitQuadraticAtT
from fontTools.pens.basePen import BasePen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.svgLib.path import parse_path


class _ContourRoundingPen(RoundingPen):
    def qCurveTo(self, *points):
        # Boolean operations can return a closed quadratic contour containing
        # only off-curve points. None closes it through the implied midpoint.
        self._outPen.qCurveTo(*(None if point is None else
                              tuple(self.roundFunc(v) for v in point) for point in points))


def _path(svg):
    import pathops

    if pathops.__version__ != "0.9.0":
        raise ValueError("Source geometry requires skia-pathops 0.9.0.")
    path = pathops.Path()
    parse_path(svg, path.getPen())
    return path


def _svg(path):
    pen = SVGPathPen(None)
    path.draw(_ContourRoundingPen(pen))
    return pen.getCommands()


def _subdivide(path, pieces):
    """Split Beziers at exact parameter fractions without flattening them."""
    import pathops

    result = pathops.Path()
    result.fillType = path.fillType
    out = result.getPen()
    cuts = [i / pieces for i in range(1, pieces)]

    class SplitPen(BasePen):
        def _moveTo(self, p): out.moveTo(p)
        def _lineTo(self, p): out.lineTo(p)
        def _closePath(self): out.closePath()
        def _endPath(self): out.endPath()

        def _curveToOne(self, p1, p2, p3):
            for curve in splitCubicAtT(self._getCurrentPoint(), p1, p2, p3, *cuts):
                out.curveTo(*curve[1:])

        def _qCurveToOne(self, p1, p2):
            for curve in splitQuadraticAtT(self._getCurrentPoint(), p1, p2, *cuts):
                out.qCurveTo(*curve[1:])

    path.draw(SplitPen(None))
    return result


def boolean_op(first, second, operation):
    """Check the fill, then retry a degenerate sweep in equivalent frames.

    Quarter turns and reflections change the sweep direction without simplifying
    or perturbing the artwork. The exact inverse restores the original frame.
    PathOps can also return a malformed contour without raising an exception.
    Check its point membership against the operands, not merely its bounds.
    """
    import pathops

    predicates = {
        pathops.PathOp.DIFFERENCE: lambda a, b: a and not b,
        pathops.PathOp.UNION: lambda a, b: a or b,
        pathops.PathOp.INTERSECTION: lambda a, b: a and b,
        pathops.PathOp.XOR: lambda a, b: a != b,
        pathops.PathOp.REVERSE_DIFFERENCE: lambda a, b: b and not a,
    }
    predicate = predicates[operation]
    bounds = [path.bounds for path in (first, second) if len(path)]
    samples = []
    if bounds:
        x0, y0 = min(b[0] for b in bounds), min(b[1] for b in bounds)
        x1, y1 = max(b[2] for b in bounds), max(b[3] for b in bounds)
        for row in range(64):
            for col in range(64):
                point = (x0 + (col + .5) * (x1 - x0) / 64,
                         y0 + (row + .5) * (y1 - y0) / 64)
                expected = predicate(first.contains(point), second.contains(point))
                samples.append((point, expected))

    def matches(result, tolerance=.05):
        for (x, y), expected in samples:
            if result.contains((x, y)) == expected:
                continue
            # Ignore float-level uncertainty directly on a split curve. This
            # tolerance is well below the final half-unit coordinate rounding.
            nearby = [(x + dx, y + dy) for dx, dy in
                      ((-tolerance, 0), (tolerance, 0), (0, -tolerance), (0, tolerance))]
            if all(predicate(first.contains(p), second.contains(p)) == expected
                   and result.contains(p) != expected for p in nearby):
                return False
        return True

    for pieces in (1, 2, 4):
        left = first if pieces == 1 else _subdivide(first, pieces)
        right = second if pieces == 1 else _subdivide(second, pieces)
        candidates = []
        for a, b, c, d in ((1, 0, 0, 1), (0, 1, -1, 0), (1, 0, 0, -1),
                           (-1, 0, 0, -1), (0, -1, 1, 0),
                           (-1, 0, 0, 1), (0, 1, 1, 0), (0, -1, -1, 0)):
            try:
                result = pathops.op(left.transform(a, b, c, d, 0, 0),
                                    right.transform(a, b, c, d, 0, 0), operation)
                result = result.transform(a, c, b, d, 0, 0)
                if matches(result):
                    return result
                candidates.append(result)
            except pathops.PathOpsError:
                continue
        # Curve reduction around almost coincident intersections can differ by
        # a fraction of a unit in every frame. Prefer a strictly matching sweep;
        # accept boundary-only differences at final integer drawing precision.
        for result in candidates:
            if matches(result, tolerance=1):
                return result
    raise ValueError('No boolean sweep passed the independent fill check.')


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
