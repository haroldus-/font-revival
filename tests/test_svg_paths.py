"""Ensure compact serialization preserves contours, winding and coordinates."""
import sys
import unittest
from pathlib import Path
from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import parse_path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from svg_paths import compact

class CompactSVGTests(unittest.TestCase):
    def test_multiple_contours_and_fractional_curves_keep_exact_geometry(self):
        drawing = 'M1000 1000C1001 1002 1003 1004 1005 1006H1010V1015L1000 1000Z M1002 1002V1004H1004V1002Z M.1 .2C.3 .4 .5 .6 .7 .8Z'
        original = RecordingPen(); parse_path(drawing, original)
        shortened = compact(drawing)
        result = RecordingPen(); parse_path(shortened, result)
        self.assertEqual(original.value, result.value)
        self.assertLess(len(shortened), len(drawing))
