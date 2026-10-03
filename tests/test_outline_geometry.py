"""Optional preparation geometry; release-only environments may omit PathOps."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from outline_geometry import simplify, shadow, _path, _svg, boolean_op, _Contains


@unittest.skipUnless(importlib.util.find_spec('pathops'), 'optional source-preparation dependency')
class OutlineGeometryTests(unittest.TestCase):
    def test_indexed_membership_preserves_holes_overlaps_and_boundary_points(self):
        import pathops
        import random
        path = _path('M-20 -20H820V820H-20Z M0 0V800H800V0Z')
        for row in range(8):
            for col in range(8):
                contour = _path('M0 0C0 80 80 80 80 0L40 20Z')
                path.addPath(contour.transform(1, 0, 0, 1, col * 95, row * 95))
        rng = random.Random(1832)
        points = [(rng.uniform(-50, 850), rng.uniform(-50, 850)) for _ in range(3000)]
        points += [(x, y) for x in range(-20, 821, 20) for y in range(-20, 821, 20)]
        for fill in (pathops.FillType.WINDING, pathops.FillType.EVEN_ODD):
            path.fillType = fill
            indexed = _Contains(path)
            for point in points:
                self.assertEqual(path.contains(point), indexed(point), (fill, point))

    def test_dense_engraving_succeeds_without_flattening_its_curves(self):
        import pathops
        fixture = json.loads((Path(__file__).parent / 'fixtures/boston-mortar-tone.json').read_text())
        first, second = _path(fixture['first']), _path(fixture['second'])
        result = boolean_op(first, second, pathops.PathOp.DIFFERENCE)
        self.assertAlmostEqual(169372.7074, result.area, delta=1)
        self.assertTrue(any(verb in (pathops.PathVerb.CUBIC, pathops.PathVerb.QUAD)
                            for verb in result.verbs))

    def test_tone_subtraction_rejects_silent_triangle_from_degenerate_sweep(self):
        import pathops
        fixture = json.loads((Path(__file__).parent / 'fixtures/boston-corner-tone.json').read_text())
        first, second = _path(fixture['first']), _path(fixture['second'])
        result = boolean_op(first, second, pathops.PathOp.DIFFERENCE)
        # The unchecked 0.9.0 sweep returns area 727824 with a large diagonal
        # across unprinted paper. A rotated sweep preserves the real contours.
        self.assertAlmostEqual(211342.0773, result.area, delta=1)
        for x in range(100, 1500, 100):
            for y in range(100, 1700, 100):
                self.assertEqual(first.contains((x, y)) and not second.contains((x, y)),
                                 result.contains((x, y)), (x, y))

    def test_closed_quadratic_without_explicit_on_curve_points(self):
        import pathops
        contour = pathops.Path()
        pen = contour.getPen()
        pen.qCurveTo((0, 0), (100, 0), (100, 100), (0, 100), None)
        pen.closePath()
        result = _svg(contour)
        bounds = BoundsPen(None); parse_path(result, bounds)
        area = AreaPen(None); parse_path(result, area)
        self.assertEqual((0, 0, 100, 100), bounds.bounds)
        self.assertAlmostEqual(25000 / 3, abs(area.value))

    def test_overlapping_strokes_form_one_solid_shape(self):
        result = simplify('M0 0H100V100H0Z M50 0H150V100H50Z')
        area = AreaPen(None);parse_path(result, area)
        self.assertAlmostEqual(15000, abs(area.value))

    def test_shadow_is_only_the_exposed_translated_edge(self):
        result = shadow('M0 0H100V200H0Z', -20, -20)
        area = AreaPen(None);parse_path(result, area)
        bounds = BoundsPen(None);parse_path(result, bounds)
        self.assertAlmostEqual(5600, abs(area.value))
        self.assertEqual((-20, -20, 80, 180), bounds.bounds)
        self.assertEqual('', shadow('', -20, -20))
