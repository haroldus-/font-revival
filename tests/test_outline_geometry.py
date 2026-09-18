"""Optional preparation geometry; release-only environments may omit PathOps."""
import importlib.util
import sys
import unittest
from pathlib import Path
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from outline_geometry import simplify, shadow


@unittest.skipUnless(importlib.util.find_spec('pathops'), 'optional source-preparation dependency')
class OutlineGeometryTests(unittest.TestCase):
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
