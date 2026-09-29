"""Source-preparation invariants, without requiring Potrace in release CI."""

import json
import io
import string
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import trace_specimen as tracing


class TracingTests(unittest.TestCase):
    def test_local_paper_correction_recovers_faint_ink_without_paper(self):
        image = Image.new('L', (60, 30))
        for x in range(60):
            paper = 195 + x // 2
            for y in range(30):
                image.putpixel((x, y), paper - 40 if 8 <= y <= 10 else paper)
        cleaned = tracing.clean_crop(image, {
            'box': [0, 0, 60, 30], 'blur': 0,
            'threshold': 225, 'paper_normalization_radius': 6,
            'component_min_area': 2, 'fill_holes': 0})
        for x in (5, 30, 55):
            self.assertEqual(0, cleaned.getpixel((x + 4, 13)))
            self.assertEqual(255, cleaned.getpixel((x + 4, 24)))

    def test_wide_icon_fits_without_stretching_and_centres_vertically(self):
        drawing = RecordingPen()
        parse_path('M20 30H220V80H20Z', drawing)
        transform, advance = tracing.trace_transform(drawing, {
            'height': 1800, 'max_ink_dimension': 1800,
            'center_vertical': True, 'bearings': [64, 64]})
        bounds = BoundsPen(None)
        drawing.replay(TransformPen(bounds, transform))
        self.assertEqual((64, 675, 1864, 1125), bounds.bounds)
        self.assertEqual(1928, advance)

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

    def test_detached_dot_survives_explicit_component_cleanup(self):
        image = Image.new('L', (30, 40), 255)
        draw = ImageDraw.Draw(image)
        draw.rectangle((10, 16, 16, 36), fill=0)
        draw.rectangle((10, 3, 16, 9), fill=0)
        draw.point((26, 2), fill=0)
        entry = {'box': [0, 0, 30, 40], 'blur': 0, 'component_min_area': 5}
        cleaned = tracing.clean_crop(image, entry)
        self.assertEqual(0, cleaned.getpixel((17, 9)))
        self.assertEqual(0, cleaned.getpixel((17, 25)))
        self.assertEqual(255, cleaned.getpixel((30, 6)))
        with self.assertRaisesRegex(ValueError, 'No components survive'):
            tracing.clean_crop(image, entry | {'component_min_area': 1000})

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
        with patch.object(tracing.subprocess, 'run', side_effect=fake_potrace):
            glyph = tracing.trace(Image.new('L', (20, 20), 0), {
                'box': [0, 0, 20, 20], 'height': 700, 'y_min': -10,
                'advance_width': 600, 'center': True}, 'potrace')
        bounds = BoundsPen(None)
        parse_path(glyph['path'], bounds)
        self.assertEqual((125, -10, 475, 690), bounds.bounds)
        self.assertEqual(600, glyph['advance_width'])
        with patch.object(tracing.subprocess, 'run', side_effect=fake_potrace):
            glyph = tracing.trace(Image.new('L', (20, 20), 0), {
                'box': [0, 0, 20, 20], 'height': 700, 'y_min': -10,
                'ink_width': 280, 'bearings': [24, 24], 'advance_width': 328}, 'potrace')
        bounds = BoundsPen(None)
        parse_path(glyph['path'], bounds)
        self.assertEqual((24, -10, 304, 690), bounds.bounds)
        self.assertEqual(328, glyph['advance_width'])

    def test_mixed_case_monospaced_master_and_ttf_preserve_cells(self):
        glyphs = {chr(cp): {'advance_width': 720, 'path': 'M40 0H540V700H40Z'}
                  for cp in range(32, 127)}
        glyphs[' ']['path'] = ''
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'mono.otf'
            tracing.assemble(REPO / 'collection/remington-1888', glyphs, {}, output,
                             metrics={'monospaced': True, 'x_height': 480})
            with TTFont(output) as font:
                cmap = font.getBestCmap()
                self.assertNotEqual(cmap[ord('a')], cmap[ord('A')])
                self.assertEqual(480, font['OS/2'].sxHeight)
                self.assertEqual({720}, {w for w, lsb in font['hmtx'].metrics.values()})
                self.assertTrue(font['CFF '].cff.topDictIndex[0].isFixedPitch)
                self.assertTrue(tracing.fontrevival.to_truetype(font)['post'].isFixedPitch)
            glyphs['i']['advance_width'] = 200
            with self.assertRaisesRegex(ValueError, 'one advance width'):
                tracing.assemble(REPO / 'collection/remington-1888', glyphs, {}, output,
                                 metrics={'monospaced': True})

    def test_quadratic_conversion_covers_control_point_extents(self):
        family = REPO / 'collection/marine-1894'
        original = tracing.fontrevival.load_source(family, tracing.fontrevival.metadata(family))
        converted = tracing.fontrevival.to_truetype(original)
        stream = io.BytesIO()
        converted.save(stream)
        stream.seek(0)
        with TTFont(stream) as font:
            self.assertGreaterEqual(font['OS/2'].usWinAscent, font['head'].yMax)
            self.assertGreaterEqual(font['OS/2'].usWinDescent, -font['head'].yMin)

    def test_registered_icon_layers_keep_their_origin_after_conversion(self):
        family = REPO / 'collection/boston-cuts-1889'
        original = tracing.fontrevival.load_source(family, tracing.fontrevival.metadata(family))
        name = original.getBestCmap()[0xE000]
        # A curved edge whose control box extends well beyond its ink bound.
        from fontTools.pens.t2CharStringPen import T2CharStringPen
        pen = T2CharStringPen(1200, None)
        parse_path('M300 0C-100 500 700 500 300 1000H900V0Z', pen)
        top = original['CFF '].cff.topDictIndex[0]
        top.CharStrings[name] = pen.getCharString(private=top.Private, globalSubrs=top.GlobalSubrs)
        bounds = BoundsPen(None)
        parse_path('M300 0C-100 500 700 500 300 1000H900V0Z', bounds)
        original['hmtx'][name] = (1200, round(bounds.bounds[0]))
        converted = tracing.fontrevival.to_truetype(original, preserve_origins=True)
        stream = io.BytesIO(); converted.save(stream); stream.seek(0)
        with TTFont(stream) as font:
            glyphs = font.getGlyphSet(); actual = BoundsPen(glyphs)
            glyphs[name].draw(actual)
            for before, after in zip(bounds.bounds, actual.bounds):
                self.assertAlmostEqual(before, after, delta=1)
            self.assertEqual(font['hmtx'][name], (1200, font['glyf'][name].xMin))

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
        for recipe in (REPO / 'collection').glob('*/source/tracing.json'):
            family = recipe.parents[1]
            slug = family.name
            manifest = json.loads((family / 'source/tracing.json').read_text())
            for character, entry in manifest['glyphs'].items():
                with self.subTest(family=slug, character=character), Image.open(family / entry['file']) as image:
                    left, top, right, bottom = entry['box']
                    self.assertTrue(0 <= left < right <= image.width)
                    self.assertTrue(0 <= top < bottom <= image.height)


if __name__ == '__main__':
    unittest.main()
