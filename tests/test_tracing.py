"""Source-preparation invariants, without requiring Potrace in release CI."""

import json
import string
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import trace_specimen as tracing


class TracingTests(unittest.TestCase):
    def test_cleanup_removes_dirt_and_repairs_speck_without_filling_counter(self):
        image = Image.new('L', (40, 40), 255)
        draw = ImageDraw.Draw(image)
        draw.rectangle((5, 5, 28, 35), fill=0)
        draw.rectangle((11, 12, 21, 26), fill=255)
        draw.point((7, 7), fill=255)
        draw.point((33, 3), fill=0)
        cleaned = tracing.clean_crop(image, {'box': [0, 0, 40, 40], 'blur': 0})
        self.assertEqual(0, cleaned.getpixel((11, 11)))
        self.assertEqual(255, cleaned.getpixel((37, 7)))
        self.assertEqual(255, cleaned.getpixel((20, 24)))

    def test_empty_crop_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'No ink'):
            tracing.clean_crop(Image.new('L', (20, 20), 255), {'box': [0, 0, 20, 20]})

    def test_potrace_y_up_geometry_keeps_baseline_and_bearings(self):
        # Potrace's display group flips y; font outlines must not inherit it.
        def fake_potrace(command, **kwargs):
            Path(command[command.index('--output')+1]).write_text(
                '<svg xmlns="http://www.w3.org/2000/svg">'
                '<g transform="translate(0,200) scale(.1,-.1)">'
                '<path d="M0 0H1000V2000H0Z"/></g></svg>')
        with patch.object(tracing.subprocess, 'run', side_effect=fake_potrace):
            glyph = tracing.trace(Image.new('L', (20, 20), 0), {
                'box': [0, 0, 20, 20], 'height': 700, 'y_min': -10,
                'bearings': [40, 50]}, 'potrace')
        bounds = BoundsPen(None)
        parse_path(glyph['path'], bounds)
        self.assertEqual((40, -10, 390, 690), bounds.bounds)
        self.assertEqual(440, glyph['advance_width'])

    def test_master_encodes_capital_aliases_and_kerning(self):
        characters = string.ascii_uppercase + string.digits + string.punctuation + ' '
        glyphs = {ch: {'advance_width': 600, 'path': 'M40 0H540V700H40Z'} for ch in characters}
        glyphs[' ']['path'] = ''
        aliases = {ch: ch.upper() for ch in string.ascii_lowercase}
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'test.otf'
            tracing.assemble(REPO / 'collection/trinal-1888', glyphs, aliases, output,
                             'feature kern { pos A V -35; } kern;')
            with TTFont(output) as font:
                cmap = font.getBestCmap()
                self.assertTrue(set(range(32, 127)).issubset(cmap))
                self.assertEqual(cmap[ord('A')], cmap[ord('a')])
                self.assertIn('CFF ', font)
                self.assertIn('GPOS', font)
                self.assertEqual(0, font['OS/2'].fsType)
            del glyphs['?']
            with self.assertRaisesRegex(ValueError, 'Missing Basic Latin'):
                tracing.assemble(REPO / 'collection/trinal-1888', glyphs, aliases, output)

    def test_committed_crop_boxes_are_inside_the_references(self):
        for slug in ('trinal-1888', 'quaint-gothic-1894'):
            family = REPO / 'collection' / slug
            manifest = json.loads((family / 'source/tracing.json').read_text())
            for character, entry in manifest['glyphs'].items():
                with self.subTest(family=slug, character=character), Image.open(family / entry['file']) as image:
                    left, top, right, bottom = entry['box']
                    self.assertTrue(0 <= left < right <= image.width)
                    self.assertTrue(0 <= top < bottom <= image.height)


if __name__ == '__main__':
    unittest.main()
