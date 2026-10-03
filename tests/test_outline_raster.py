"""Dense vector delivery must preserve holes, opacity and registration."""
import ctypes.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from outline_raster import rasterize


@unittest.skipUnless(ctypes.util.find_library('cairo'), 'Cairo 1.18.0 dense-outline renderer')
class OutlineRasterTests(unittest.TestCase):
    def test_nonzero_hole_and_overlapping_filled_contour(self):
        svg = 'M0 0H100V100H0Z M20 20V80H80V20Z M40 40H60V60H40Z'
        mask = rasterize(svg, 120, 120, 1, (10, 110))
        self.assertEqual(0, mask.getpixel((5, 5)))
        self.assertEqual(255, mask.getpixel((15, 15)))
        self.assertEqual(0, mask.getpixel((40, 40)))
        self.assertEqual(255, mask.getpixel((60, 60)))

    def test_curves_keep_transparent_antialiased_edges(self):
        mask = rasterize('M0 0C0 100 100 100 100 0Z', 120, 120, 1, (10, 110))
        self.assertEqual(0, mask.getpixel((0, 0)))
        self.assertEqual(255, mask.getpixel((60, 80)))
        self.assertTrue(any(0 < alpha < 255 for alpha in mask.get_flattened_data()))
