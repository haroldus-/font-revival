"""Preserve existing font contracts when preparing local historical corrections."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import trace_revisions as revisions


def master(family):
    font = TTFont()
    font.importXML(family / 'source/font.ttx')
    return font


class RevisionTests(unittest.TestCase):
    def test_revisions_preserve_coverage_advances_and_layout_in_every_format(self):
        for slug, name in [('nero-1888', 'Nero1888'), ('johnson-1892', 'Johnson1892')]:
            family = ROOT / 'collection' / slug
            with master(family) as before:
                for folder, ext in [('fonts', 'otf'), ('fonts', 'ttf'), ('web', 'woff'), ('web', 'woff2')]:
                    with self.subTest(family=slug, format=ext), TTFont(family / folder / f'{name}-Regular.{ext}') as after:
                        self.assertEqual(before.getBestCmap(), after.getBestCmap())
                        self.assertEqual({n: w for n, (w, _) in before['hmtx'].metrics.items()},
                                         {n: w for n, (w, _) in after['hmtx'].metrics.items()})
                        for tag in ('GPOS', 'GSUB'):
                            self.assertEqual(tag in before, tag in after)
                            if tag in before:
                                self.assertEqual(before[tag].compile(before), after[tag].compile(after))

    def test_c_accents_share_revised_body_and_keep_their_original_marks(self):
        family = ROOT / 'collection/nero-1888'
        recipe = json.loads((family / 'source/tracing.json').read_text())
        with master(family) as before, TTFont(family / 'fonts/Nero1888-Regular.otf') as after:
            old, new = before.getGlyphSet(), after.getGlyphSet()
            for name in recipe['replace_bases']['C']:
                with self.subTest(glyph=name):
                    old_marks, new_marks = revisions.contours(old[name]), revisions.contours(new[name])
                    for contour in revisions.contours(old['C']):
                        old_marks.remove(contour)
                    for contour in revisions.contours(new['C']):
                        new_marks.remove(contour)
                    self.assertEqual(old_marks, new_marks)

    def test_scan_debris_is_removed_without_filling_real_counters(self):
        with TTFont(ROOT / 'collection/nero-1888/fonts/Nero1888-Regular.otf') as font:
            glyphs = font.getGlyphSet()
            for name, count in [('0', 2), ('2', 1), ('3', 1), ('6', 2), ('8', 3), ('9', 2)]:
                with self.subTest(glyph=name):
                    self.assertEqual(count, len(revisions.contours(glyphs[name])))
        with TTFont(ROOT / 'collection/johnson-1892/fonts/Johnson1892-Regular.otf') as font:
            glyphs = font.getGlyphSet()
            # The patent b has an open curl; scan spread had closed its aperture.
            for name, count in [('L', 1), ('P', 1), ('R', 1), ('b', 1)]:
                self.assertEqual(count, len(revisions.contours(glyphs[name])))
            bounds = BoundsPen(glyphs)
            glyphs['L'].draw(bounds)
            self.assertGreaterEqual(bounds.bounds[1], 0)

    def test_accent_replacement_rejects_an_unrelated_base(self):
        with master(ROOT / 'collection/nero-1888') as font:
            glyphs = font.getGlyphSet()
            with self.assertRaisesRegex(ValueError, 'exact base contours'):
                revisions.replace_base(glyphs['A'], glyphs['C'], 'M0 0H100V100H0Z')

    def test_preparation_ignores_installed_edits_and_preserves_master(self):
        source = ROOT / 'collection/nero-1888'
        with tempfile.TemporaryDirectory() as tmp:
            family = Path(tmp) / 'family'
            (family / 'source/glyphs').mkdir(parents=True)
            shutil.copyfile(source / 'source/font.ttx', family / 'source/font.ttx')
            recipe = json.loads((source / 'source/tracing.json').read_text())
            recipe['glyphs'] = {'C': recipe['glyphs']['C']}
            reference = Path(recipe['glyphs']['C']['file'])
            (family / reference.parent).mkdir()
            shutil.copyfile(source / reference, family / reference)
            (family / 'source/tracing.json').write_text(json.dumps(recipe))
            baseline = (family / 'source/font.ttx').read_bytes()
            output = Path(tmp) / 'edits'
            def fake_trace(image, entry, potrace):
                return {'path': 'M24 0H280V700H24Z', 'advance_width': entry['advance_width']}
            with patch.object(revisions, 'require_potrace'), patch.object(revisions, 'trace', side_effect=fake_trace):
                revisions.prepare(family, output, 'potrace')
                first = {p.name: p.read_bytes() for p in output.glob('*.json')}
                shutil.copytree(output, family / 'source/glyphs', dirs_exist_ok=True)
                revisions.prepare(family, output, 'potrace')
                self.assertEqual(first, {p.name: p.read_bytes() for p in output.glob('*.json')})
                self.assertEqual(6, len(first))
                self.assertEqual(baseline, (family / 'source/font.ttx').read_bytes())
                recipe['glyphs']['C']['advance_width'] += 1
                (family / 'source/tracing.json').write_text(json.dumps(recipe))
                with self.assertRaisesRegex(ValueError, 'preserve the advance width'):
                    revisions.prepare(family, output, 'potrace')
