"""Protect icon identity and the shared SVG/font maintenance contract."""

import contextlib
import copy
import importlib.util
import io
import hashlib
import json
import re
import random
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from argparse import Namespace
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont
from fontTools import subset
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'scripts'))
spec = importlib.util.spec_from_file_location("fontrevival_icons", REPO / "scripts/fontrevival.py")
revival = importlib.util.module_from_spec(spec)
spec.loader.exec_module(revival)


class IconWorkflowTests(unittest.TestCase):
    def test_font_only_revision_reuses_verified_artwork_and_matches_full_build(self):
        m = revival.metadata(self.family) | {'font_export_glyphs': 'encoded',
                                             'otf_uses_truetype_approximations': True}
        revival.write_json(self.family / 'font.json', m)
        revival.build_family(self.family)
        revival.write_json(self.root / 'icons.json', {'collections': [m]})
        master = revival.load_source(self.family, m)
        name = m['icons'][0]['glyph']
        glyphs = master.getGlyphSet()
        original = SVGPathPen(glyphs); glyphs[name].draw(original)
        bounds = revival.BoundsPen(glyphs); glyphs[name].draw(bounds)
        x0, y0, x1, y1 = bounds.bounds
        revival.write_json(self.family / 'source/truetype-glyphs' / (name + '.json'), {
            'glyph': name, 'advance_width': master['hmtx'][name][0],
            'path': f'M{x0} {y0}H{x1}V{y1}H{x0}Z', 'max_bound_delta': 2,
            'master_sha256': hashlib.sha256(original.getCommands().encode()).hexdigest(),
            'notes': 'Synthetic font-only revision; the SVG retains the original artwork.'})
        m['version'] = '1.099'
        revival.write_json(self.family / 'font.json', m)
        from unittest.mock import patch
        with patch.object(revival, 'write_icon_artwork', side_effect=AssertionError('Artwork must be reused')):
            revival.build_family(self.family, reuse_artwork=True)
        with TTFont(self.family / 'fonts' / (m['postscript_name'] + '.ttf')) as font:
            self.assertEqual(4, len(font['glyf'][name].coordinates))
        reused = {f.relative_to(self.family): revival.digest(f) for f in revival.family_files(self.family)}
        revival.build_family(self.family)
        self.assertEqual(reused, {f.relative_to(self.family): revival.digest(f)
                                  for f in revival.family_files(self.family)})
        for relative in ['source/font.ttx', 'source/glyphs/new.json',
                         'svg/' + m['icons'][0]['id'] + '.svg']:
            with self.subTest(file=relative):
                file = self.family / relative
                before = file.read_bytes() if file.exists() else None
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'full build'):
                    revival.verify_reusable_icon_artwork(self.family, m)
                if before is None:
                    file.unlink()
                else:
                    file.write_bytes(before)
        with self.assertRaisesRegex(ValueError, 'metadata changed'):
            revival.verify_reusable_icon_artwork(self.family, m | {'copyright': 'Changed'})
        with self.assertRaisesRegex(ValueError, 'metadata changed'):
            revival.verify_reusable_icon_artwork(self.family, {k: v for k, v in m.items() if k != 'description'})

    def test_delivery_rejects_outlines_that_older_renderers_cannot_load(self):
        m = revival.metadata(self.family)
        master = revival.load_source(self.family, m)
        name = m['icons'][0]['glyph']
        # A single zigzag contour avoids the separate contour-count limit.
        # Its 32,768 points fit in TrueType's unsigned count but overflow
        # FreeType 2.13's signed outline count, which used to escape our checks.
        path = 'M0 0' + ''.join(f'L{i % 1000} {100 * (i % 2)}' for i in range(1, 32768)) + 'Z'
        item = {'path': path, 'advance_width': master['hmtx'][name][0]}
        self.assertEqual(32768, revival.cff_point_count(path))
        with self.assertRaisesRegex(ValueError, 'renderer point limit'):
            revival.to_truetype(master, approximations={name: item})
        with self.assertRaisesRegex(ValueError, 'renderer point limit'):
            revival.font_delivery_master(master, m | {'otf_uses_truetype_approximations': True},
                                         {name: item})
        # TrueType renderers also reserve four phantom points for metrics.
        path = 'M0 0' + ''.join(f'L{i % 1000} {100 * (i % 2)}' for i in range(1, 32764)) + 'Z'
        with self.assertRaisesRegex(ValueError, 'renderer point limit'):
            revival.to_truetype(master, approximations={name: item | {'path': path}})

    def test_long_cff_subroutines_preserve_serialized_outlines_and_widths(self):
        m = revival.metadata(self.family)
        master = revival.load_source(self.family, m)
        expected = revival.icon_records(m, master)
        # A small chunk size exercises repeated calls throughout each outline.
        delivery = revival.font_delivery_master(master, m | {'cff_charstring_chunk_bytes': 128})
        top = delivery['CFF '].cff.topDictIndex[0]
        self.assertGreater(len(top.GlobalSubrs), 0)
        stream = io.BytesIO(); delivery.save(stream); stream.seek(0)
        with TTFont(stream, recalcTimestamp=False) as reopened:
            cff = reopened['CFF '].cff.topDictIndex[0]
            self.assertTrue(all(len(cff.CharStrings[n].bytecode) <= 65535
                                for n in reopened.getGlyphOrder()))
            self.assertTrue(all(len(subr.bytecode) <= 128 for subr in cff.GlobalSubrs))
            self.assertEqual(expected, revival.icon_records(m, reopened))
            self.assertEqual(master['hmtx'].metrics, reopened['hmtx'].metrics)
        self.assertEqual(expected, revival.icon_records(m, master))
        self.assertEqual(0, len(master['CFF '].cff.topDictIndex[0].GlobalSubrs))

    def test_release_files_exclude_python_runtime_caches(self):
        cache = self.family / 'source/__pycache__/prepare.cpython-312.pyc'
        cache.parent.mkdir(exist_ok=True)
        cache.write_bytes(b'local interpreter cache')
        self.assertNotIn(cache, revival.family_files(self.family))
        self.assertNotIn('__pycache__', revival.checksums(self.family))
        self.assertIn(self.family / 'source/font.ttx', revival.family_files(self.family))

    def test_large_download_parts_keep_complete_assets_and_zip_limits(self):
        generator = random.Random(1832)
        files = {f'icon-{i}.svg': generator.randbytes(1200) for i in range(6)}
        groups = revival.partition_zip_files(files, 3000)
        self.assertEqual(3, len(groups))
        self.assertEqual(files, {name: data for group in groups for name, data in group.items()})
        for group in groups:
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for name, data in group.items():
                    archive.writestr(name, data)
            self.assertLessEqual(len(stream.getvalue()), 3000)
        with self.assertRaisesRegex(ValueError, 'single download asset'):
            revival.partition_zip_files(files, 1000)

    def test_raw_cff_xml_import_retains_the_same_editable_master(self):
        m = revival.metadata(self.family)
        original = revival.load_source(self.family, m)
        expected = revival.icon_records(m, original)
        with contextlib.redirect_stdout(io.StringIO()):
            revival.import_font(Namespace(id=m['id'],
                font=self.family / 'fonts' / (m['postscript_name'] + '.otf'),
                replace=True, binary_charstrings=True))
        self.assertIn('raw="1"', (self.family / 'source/font.ttx').read_text())
        restored = revival.load_source(self.family, m)
        self.assertEqual(expected, revival.icon_records(m, restored))
        self.assertEqual(original.getBestCmap(), restored.getBestCmap())

    def test_native_override_preserves_even_degenerate_source_contours(self):
        m = revival.metadata(self.family)
        font = revival.load_source(self.family, m)
        name = m['icons'][0]['glyph']
        drawing = 'M100 100H200V200H100V100ZM250 250H251H250ZM500 500Z'
        revival.write_json(self.family / 'source/glyphs' / (name + '.json'),
                           {'glyph': name, 'advance_width': font['hmtx'][name][0],
                            'path': drawing, 'preserve_commands': True})
        revival.apply_glyphs(font, self.family / 'source/glyphs')
        pen = SVGPathPen(font.getGlyphSet())
        font.getGlyphSet()[name].draw(pen)
        self.assertEqual(drawing, pen.getCommands())

    def test_rotated_override_keeps_fractional_coordinates_in_cff(self):
        m = revival.metadata(self.family)
        font = revival.load_source(self.family, m)
        name = m['icons'][0]['glyph']
        drawing = 'M100.015625 100.5L200.25 102.125L198.5 202.25Z M250.125 250.5Z'
        revival.write_json(self.family / 'source/glyphs' / (name + '.json'),
                           {'glyph': name, 'advance_width': font['hmtx'][name][0],
                            'path': drawing, 'preserve_commands': True,
                            'preserve_coordinates': True})
        revival.apply_glyphs(font, self.family / 'source/glyphs')
        stream = io.BytesIO(); font.save(stream); stream.seek(0)
        restored = TTFont(stream)
        pen = SVGPathPen(restored.getGlyphSet()); restored.getGlyphSet()[name].draw(pen)
        expected = SVGPathPen(None); parse_path(drawing, expected)
        self.assertEqual(expected.getCommands(), pen.getCommands())

    def test_split_sprites_keep_each_icon_linked_to_its_own_file(self):
        m = revival.metadata(self.family)
        with revival.load_source(self.family, m) as font:
            record = revival.icon_records(m, font)[0]
        records = [copy.deepcopy(record) | {'id': 'test-' + str(i)} for i in range(3)]
        revival.assign_icon_sprites({'sprite_max_bytes': 100}, records)
        self.assertEqual(['icons.svg', 'icons-2.svg', 'icons-3.svg'], [r['_sprite_file'] for r in records])
        self.assertIn('icons-multitone-3.svg#test-2', revival.icon_html_examples(records[2], 'collection/test')['sprite'])
        self.assertNotIn('_sprite_file', revival.public_icon(records[2]))

    def test_conversion_validation_ignores_invisible_isolated_points(self):
        revival.export_glyph(Namespace(id=self.family.name, character='uniE000'))
        edit = self.family / 'source/glyphs/uniE000.json'
        data = json.loads(edit.read_text())
        # The traced drawing stays unchanged; an isolated point below it has
        # no ink and is discarded by the TrueType conversion.
        data['path'] += ' M500 50Z'
        data['preserve_commands'] = True
        revival.write_json(edit, data)
        profile = self.family / 'source/sizing.json'
        revival.write_json(profile, {'schema_version': 1, 'rules': [
            {'characters': '*', 'advance_width': [0, 3000],
             'notes': 'This fixture tests visible outline registration.'}]})
        revival.build_family(self.family)
        revival.validate_family(self.family)

    def test_encoded_delivery_preserves_full_tonal_gallery_artwork(self):
        m = revival.metadata(self.family) | {'font_export_glyphs': 'encoded'}
        master = revival.load_source(self.family, m)
        original = revival.icon_records(m, master)
        delivery = revival.font_delivery_master(master, m)
        self.assertEqual(master.getBestCmap(), delivery.getBestCmap())
        self.assertEqual({'.notdef', *master.getBestCmap().values()}, set(delivery.getGlyphOrder()))
        self.assertGreater(len(master.getGlyphOrder()), len(delivery.getGlyphOrder()))
        self.assertEqual(original, revival.gallery_icon_records(self.family, m, delivery))
        for name in delivery.getGlyphOrder():
            self.assertEqual(master['hmtx'][name], delivery['hmtx'][name])

    def test_streamed_tonal_edits_match_the_complete_source(self):
        m = revival.metadata(self.family) | {'font_export_glyphs': 'encoded'}
        name = m['icons'][0]['multitone_layers'][0]['glyph']
        revival.export_glyph(Namespace(id=self.family.name, character=name))
        file = self.family / 'source/glyphs' / (name + '.json')
        edit = json.loads(file.read_text())
        edit['path'] += ' M500 500H510V510H500Z'
        revival.write_json(file, edit)
        complete = revival.load_source(self.family, m)
        expected = revival.icon_records(m, complete)
        encoded = revival.load_source(self.family, m, encoded_only=True)
        before = revival.icon_records(m, encoded)
        self.assertNotEqual(before, expected)
        self.assertEqual(revival.source_icon_records(self.family, m, encoded), expected)
        self.assertEqual(revival.icon_records(m, encoded), before)
        revival.write_json(self.family / 'font.json', m)
        revival.build_family(self.family)
        proof = (self.family / 'specimens/specimen.pdf').read_bytes()
        self.assertIn(b'/Subtype /Form', proof)
        self.assertNotIn(b'/Subtype /TrueType', proof)

    def test_reviewed_truetype_approximation_keeps_master_and_rejects_stale_data(self):
        from fontTools.pens.boundsPen import BoundsPen
        m = revival.metadata(self.family)
        font = revival.load_source(self.family, m)
        glyphs = font.getGlyphSet(); name = m['icons'][0]['glyph']
        pen = SVGPathPen(glyphs); glyphs[name].draw(pen)
        original = pen.getCommands()
        bounds = BoundsPen(glyphs); glyphs[name].draw(bounds)
        x0, y0, x1, y1 = bounds.bounds
        item = {'glyph': name, 'advance_width': font['hmtx'][name][0],
                'path': f'M{x0} {y0}H{x1}V{y1}H{x0}Z',
                'master_sha256': hashlib.sha256(original.encode()).hexdigest(),
                'max_bound_delta': 2, 'notes': 'Synthetic format-only test drawing.'}
        file = self.family / 'source/truetype-glyphs' / (name + '.json')
        revival.write_json(file, item)
        selected = revival.truetype_approximations(self.family, font)
        converted = revival.to_truetype(font, preserve_origins=True, approximations=selected)
        self.assertEqual(font.getBestCmap(), converted.getBestCmap())
        self.assertEqual(font['hmtx'][name][0], converted['hmtx'][name][0])
        self.assertEqual(4, len(converted['glyf'][name].coordinates))
        fractional_x = int(x0) + 0.015625
        self.assertEqual(3, revival.cff_point_count('M0 0C0 1 1 1 0 0Z'))
        self.assertEqual(4, revival.cff_point_count('M0 0H10V10H0Z'))
        fractional = selected[name] | {'path': f'M{fractional_x} {y0}H{x1}V{y1}H{fractional_x}Z'}
        delivery = revival.font_delivery_master(font, m | {'otf_uses_truetype_approximations': True},
                                               {name: fractional})
        delivery.save(self.family / 'reviewed-otf.otf')
        with TTFont(self.family / 'reviewed-otf.otf') as reopened:
            exported_glyphs = reopened.getGlyphSet()
            exported_bounds = BoundsPen(exported_glyphs)
            exported_glyphs[name].draw(exported_bounds)
            self.assertEqual(fractional_x, exported_bounds.bounds[0])
            self.assertEqual(font['hmtx'][name][0], reopened['hmtx'][name][0])
        untouched = SVGPathPen(glyphs); glyphs[name].draw(untouched)
        self.assertEqual(original, untouched.getCommands())
        item['master_sha256'] = '0' * 64
        revival.write_json(file, item)
        with self.assertRaisesRegex(ValueError, 'Stale TrueType'):
            revival.truetype_approximations(self.family, font)

    @classmethod
    def setUpClass(cls):
        # Exercise edits on a small real fixture while the live collection grows.
        # The full release is independently rebuilt and checked by the CLI.
        cls.fixture_temp = tempfile.TemporaryDirectory()
        cls.fixture_root = Path(cls.fixture_temp.name)
        original = REPO / "collection/boston-cuts-1889"
        family = cls.fixture_root / "collection/boston-cuts-1889"
        family.mkdir(parents=True)
        shutil.copyfile(REPO / "LICENSE", cls.fixture_root / "LICENSE")
        shutil.copyfile(original / "CHANGELOG.md", family / "CHANGELOG.md")
        m = json.loads((original / "font.json").read_text())
        pilot = next(icon for icon in m["icons"] if icon["id"] == "boston-1889-4202")
        m["sources"] = [m["sources"][pilot["source_index"]]]
        pilot["source_index"] = 0
        m["icons"] = [pilot]
        revival.write_json(family / "font.json", m)
        tracing = json.loads((original / "source/tracing.json").read_text())
        tracing["glyphs"] = {"\ue000": tracing["glyphs"]["\ue000"]}
        revival.write_json(family / "source/tracing.json", tracing)
        sizing = json.loads((original / "source/sizing.json").read_text())
        sizing["rules"] = [r | {"characters": ''.join(c for c in r["characters"] if c in " \ue000")}
                           for r in sizing["rules"] if set(r["characters"]) & set(" \ue000")]
        revival.write_json(family / "source/sizing.json", sizing)
        for reference in {m["sources"][0]["file"], tracing["glyphs"]["\ue000"]["file"]}:
            (family / reference).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original / reference, family / reference)
        font = revival.load_source(original, m)
        # Compile the XML-loaded CFF charset before the subsetter traverses it.
        compiled = io.BytesIO(); font.save(compiled); compiled.seek(0)
        font = TTFont(compiled, recalcTimestamp=False)
        keep = [".notdef", "space", pilot["glyph"], *[layer["glyph"] for layer in pilot["multitone_layers"]]]
        selected = subset.Subsetter()
        selected.populate(glyphs=keep)
        selected.subset(font)
        font.saveXML(family / "source/font.ttx")
        with contextlib.redirect_stdout(io.StringIO()):
            revival.ROOT = cls.fixture_root
            try:
                revival.build_family(family)
            finally:
                revival.ROOT = REPO

    @classmethod
    def tearDownClass(cls):
        cls.fixture_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.family = self.root / "collection/boston-cuts-1889"
        shutil.copytree(self.fixture_root / "collection/boston-cuts-1889", self.family)
        shutil.copytree(REPO / "site", self.root / "site")
        shutil.copyfile(REPO / "LICENSE", self.root / "LICENSE")
        revival.ROOT = self.root
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.output.__exit__(None, None, None)
        revival.ROOT = REPO
        self.temp.cleanup()

    def test_clean_rebuild_and_gallery_separation(self):
        revival.build_family(self.family)
        revival.build_catalog()
        revival.check()
        catalog = json.loads((self.root / "catalog.json").read_text())
        self.assertEqual(catalog["families"], [])
        icons = json.loads((self.root / "icons.json").read_text())["icons"]
        self.assertEqual([i["id"] for i in icons], ["boston-1889-4202"])
        self.assertIn('href="icons/boston-1889-4202.html"', (self.root / "icons.html").read_text())
        self.assertNotIn("@@", (self.root / "icons.html").read_text())
        self.assertNotIn("<use ", (self.root / "icons.html").read_text())
        self.assertIn('class="fr-primary"', (self.root / "icons/boston-1889-4202.html").read_text())

    def test_svg_and_sprite_follow_glyph_override(self):
        revival.export_glyph(Namespace(id=self.family.name, character="uniE000"))
        edit = self.family / "source/glyphs/uniE000.json"
        data = json.loads(edit.read_text())
        # Add an interior counter; preserve the reviewed extents and advance.
        data["path"] += " M850 700V750H900V700Z"
        revival.write_json(edit, data)
        revival.build_family(self.family)
        revival.validate_family(self.family)
        ns = "{http://www.w3.org/2000/svg}"
        svg = ET.parse(self.family / "svg/boston-1889-4202.svg")
        sprite = ET.parse(self.family / "web/icons.svg")
        with TTFont(self.family / "fonts/BostonCuts1889-Regular.otf") as font:
            glyphs = font.getGlyphSet(); pen = SVGPathPen(glyphs)
            glyphs["uniE000"].draw(pen)
            for tree in (svg, sprite):
                path = tree.find(".//" + ns + "path")
                self.assertEqual(path.attrib["d"], pen.getCommands())
                self.assertEqual(path.attrib["transform"], "scale(1,-1)")
                self.assertEqual(path.attrib["fill"], "currentColor")
            viewbox = list(map(int, svg.getroot().attrib["viewBox"].split()))
            self.assertEqual(viewbox, [0, -1900, font["hmtx"]["uniE000"][0], 2048])

    def test_compact_grid_links_to_complete_local_detail_pages(self):
        m = revival.metadata(self.family)
        with TTFont(self.family / "fonts/BostonCuts1889-Regular.otf") as font:
            first = revival.icon_records(m, font)[0]
        records = [first | {"id": f"test-cut-{i}"} for i in range(97)]
        output = revival.icon_catalog_outputs([(m, records)])
        index = output['icons.html']
        self.assertEqual(index.count('class="icon-tile"'), 97)
        self.assertNotIn('<svg', index)
        self.assertNotIn('<path', index)
        grid = index.split('<div class="icon-grid"', 1)[1].split('</div>', 1)[0]
        self.assertNotIn('<img', grid)
        self.assertNotIn('Engraved detail, original proportions', index)
        self.assertNotIn('data-art-chunk', index)
        self.assertIn('data-id="test-cut-96"', index)
        self.assertEqual(len(re.findall(r'data-section="[^"]*\bholiday-cuts\b[^"]*" hidden>', index)), 1)
        for record in records:
            detail = output[f'icons/{record["id"]}.html']
            self.assertIn(revival.icon_artwork(first), detail)
            self.assertIn(revival.multitone_artwork(first), detail)
            self.assertIn('Three-tone image', detail)
            self.assertNotIn('tritone', detail.lower())
            self.assertNotIn('Engraved detail, original proportions', detail)
            self.assertIn('href="../icons.html#collection"', detail)
            self.assertIn('href="../collection/boston-cuts-1889/downloads/', detail)
            self.assertIn('src=&quot;collection/boston-cuts-1889/svg/multitone/', detail)
            self.assertNotIn('@@', detail)
        catalog = json.loads(output['icons.json'])
        self.assertEqual(catalog['icons'][0]['type'], 'cuts')
        self.assertIn('holiday-cuts', catalog['icons'][0]['sections'])
        self.assertEqual(catalog['icons'][0]['page'], 'icons/test-cut-0.html')
        self.assertIn('name="collection" value="boston-cuts-1889"', index)
        self.assertIn('name="type" value="cuts"', index)
        self.assertIn('name="section" value="holiday-cuts"', index)
        self.assertIn('<summary>Categories</summary>', index)
        self.assertNotIn('Specimen sections', index)

    def test_browse_fonts_preserve_monochrome_outlines_without_tone_layers(self):
        m = revival.metadata(self.family)
        with TTFont(self.family / "fonts/BostonCuts1889-Regular.otf") as font:
            records = revival.icon_records(m, font)
        output = revival.icon_browse_fonts([(m, records)])
        data = output['site/icon-fonts/boston-cuts-1889-000.woff2']
        with TTFont(io.BytesIO(data)) as browse:
            self.assertEqual(set(browse.getBestCmap()), {32, 0xE000})
            self.assertEqual(len(browse.getGlyphOrder()), 3)
            self.assertEqual(browse['glyf'][browse.getBestCmap()[32]].numberOfContours, 0)
            glyphs = browse.getGlyphSet()
            pen = SVGPathPen(glyphs)
            glyphs[browse.getBestCmap()[0xE000]].draw(pen)
            with TTFont(self.family / 'fonts/BostonCuts1889-Regular.ttf') as original:
                original_glyphs = original.getGlyphSet()
                original_pen = SVGPathPen(original_glyphs)
                original_glyphs[original.getBestCmap()[0xE000]].draw(original_pen)
                self.assertEqual(pen.getCommands(), original_pen.getCommands())
            self.assertEqual(browse['hmtx'][browse.getBestCmap()[0xE000]][0], records[0]['advance_width'])
        self.assertIn('unicode-range:U+20,U+E000', output['site/icon-fonts/icons.css'])

    def test_taxonomy_has_evidence_and_resolves_to_existing_icons(self):
        taxonomy = json.loads((REPO / 'site/icon-taxonomy.json').read_text())
        sections = taxonomy['sections']
        self.assertEqual(len({s['id'] for s in sections}), len(sections))
        families = {name: json.loads((REPO / 'collection' / name / 'font.json').read_text())
                    for name in taxonomy['collections']}
        for section in sections:
            m = families[section['collection']]
            with self.subTest(section=section['id']):
                self.assertTrue(section['historical_heading'])
                page_key = 'pdf_page' if 'pdf_pages' in section else 'printed_page'
                self.assertTrue(set(section[page_key + 's']) <= {i[page_key] for i in m['icons']})
                self.assertTrue(set(section.get('icons', [])) <= {i['id'] for i in m['icons']})
                selected = [i for i in m['icons'] if section in revival.icon_specimen_sections(m, i, taxonomy)]
                self.assertTrue(selected)
        cuts = families['boston-cuts-1889']
        santa = next(i for i in cuts['icons'] if i['id'] == 'boston-1889-4202')
        self.assertIn('holiday-cuts', [s['id'] for s in revival.icon_navigation(cuts, santa, taxonomy)[1]])

    def test_categories_cover_both_collections_by_subject(self):
        taxonomy = json.loads((REPO / 'site/icon-taxonomy.json').read_text())
        categories = taxonomy['categories']
        self.assertEqual(len({c['id'] for c in categories}), len(categories))
        membership = {c['id']: set() for c in categories}
        icon_categories, ids = {}, set()
        for family in taxonomy['collections']:
            m = json.loads((REPO / 'collection' / family / 'font.json').read_text())
            for icon in m['icons']:
                ids.add(icon['id'])
                matched = revival.icon_navigation(m, icon, taxonomy)[1]
                self.assertTrue(matched, icon['id'])
                icon_categories[icon['id']] = {c['id'] for c in matched}
                for category in matched:
                    membership[category['id']].add(family.split('-')[0])
        section_ids = {s['id'] for s in taxonomy['sections']}
        for category in categories:
            self.assertTrue(membership[category['id']], category['id'])
            self.assertNotRegex(category['label'], r'Boston|Baltimore')
            for rule in category['selectors']:
                self.assertLessEqual(set(rule.get('icons', [])), ids)
                self.assertLessEqual(set(rule.get('sections', [])), section_ids)
        for key in ['ships-steamers-and-yachts', 'horses-and-mules', 'american-flags-and-eagles',
                    'musical-instruments', 'maps-and-diagrams', 'borders-and-frames',
                    'art-initials', 'farming-and-harvest', 'books-and-printing']:
            self.assertEqual(membership[key], {'boston', 'baltimore'}, key)
        self.assertIn('farming-and-harvest', icon_categories['baltimore-1832-p141-125'])
        self.assertIn('dogs', icon_categories['baltimore-1832-p209-357-04'])
        self.assertIn('american-flags-and-eagles', icon_categories['baltimore-1832-p135-103'])
        self.assertNotIn('pointing-hands-outlined', icon_categories['baltimore-1832-p129-80'])

    def test_unnumbered_leaf_uses_pdf_page_for_navigation_and_proofs(self):
        m = revival.metadata(self.family)
        m['icons'][0]['printed_page'] = None
        revival.write_json(self.family / 'font.json', m)
        revival.metadata(self.family)
        section = {'id': 'metal-ornaments', 'collection': m['id'], 'pdf_pages': [281]}
        taxonomy = {'collections': {m['id']: {'type': 'cuts'}}, 'sections': [section]}
        self.assertEqual(revival.icon_specimen_sections(m, m['icons'][0], taxonomy), [section])
        other = m['icons'][0] | {'pdf_page': 282}
        self.assertEqual(revival.icon_specimen_sections(m, other, taxonomy), [])
        revival.build_family(self.family)
        self.assertTrue((self.family / 'specimens/specimen.pdf').exists())
        for invalid in (0, -1, '121', True):
            m['icons'][0]['printed_page'] = invalid
            with self.assertRaises(ValueError):
                revival.validate_icon_metadata(self.family, m)

    def test_web_bundle_resolves_copyable_html_and_stylesheet_assets(self):
        archive = self.family / "downloads/boston-cuts-1889-web.zip"
        extracted = self.root / "downloaded"
        with zipfile.ZipFile(archive) as bundle:
            self.assertIsNone(bundle.testzip())
            bundle.extractall(extracted)
        base = extracted / "collection/boston-cuts-1889"
        self.assertEqual((base / "LICENSE").read_bytes(), (REPO / "LICENSE").read_bytes())
        self.assertIn("place the extracted `collection` folder beside your HTML", (extracted / "README.md").read_text())
        with TTFont(self.family / "fonts/BostonCuts1889-Regular.otf") as font:
            record = revival.icon_records(revival.metadata(self.family), font)[0]
        examples = revival.icon_html_examples(record, "collection/boston-cuts-1889")
        for example in examples.values():
            for reference in re.findall(r'(?:src|href)="([^"]+)"', example):
                self.assertTrue((extracted / reference.split("#")[0]).is_file(), reference)
        for name in ("icons.css", "font.css"):
            for reference in re.findall(r'url\("([^"]+)"\)', (base / "web" / name).read_text()):
                self.assertTrue((base / "web" / reference).is_file(), reference)
        self.assertTrue((base / "png/multitone/boston-1889-4202.png").is_file())
        self.assertTrue((base / "fonts/BostonCuts1889-Regular.otf").is_file())

    def test_icon_coverage_exception_does_not_weaken_text_fonts(self):
        revival.validate_family(self.family)
        file = self.family / "font.json"
        m = json.loads(file.read_text()); m.pop("kind")
        revival.write_json(file, m)
        with self.assertRaisesRegex(ValueError, "missing printable Basic Latin"):
            revival.validate_family(self.family)

    def test_multitone_vectors_and_png_retain_tones_and_transparency(self):
        ns = "{http://www.w3.org/2000/svg}"
        svg = ET.parse(self.family / "svg/multitone/boston-1889-4202.svg")
        self.assertEqual(len(svg.findall(".//" + ns + "image")), 0)
        paths = svg.findall(".//" + ns + "path")
        self.assertEqual(len(paths), 3)
        for path, role, opacity in zip(paths, ("primary", "secondary", "tertiary"), ("1", "0.55", "0.25")):
            self.assertEqual(path.attrib["class"], "fr-" + role)
            self.assertEqual(path.attrib["fill-opacity"], f"var(--fr-{role}-opacity,{opacity})")
            self.assertEqual(path.attrib["fill"], f"var(--fr-{role}-color,currentColor)")
        with Image.open(self.family / "png/multitone/boston-1889-4202.png") as image:
            image = image.convert("RGBA")
            self.assertEqual(image.height, 1024)
            self.assertEqual(image.getpixel((0, 0))[3], 0)
            low, high = image.getchannel("A").getextrema()
            self.assertEqual(low, 0)
            self.assertEqual(high, 255)
            histogram = image.getchannel("A").histogram()
            self.assertTrue(all(histogram[level] > 1000 for level in (64, 140, 255)))
        with TTFont(self.family / "fonts/BostonCuts1889-Regular.otf") as font:
            self.assertEqual(set(font.getBestCmap()), {32, 0xE000})
            m = revival.metadata(self.family)
            records = revival.icon_records(m, font)
            self.assertEqual([p.attrib["d"] for p in paths], [t["path"] for t in records[0]["tones"]])

    def test_multitone_edit_rebuilds_tonal_outputs_without_changing_solid_art(self):
        mono = (self.family / "svg/boston-1889-4202.svg").read_bytes()
        gray = self.family / "svg/multitone/boston-1889-4202.svg"
        png = self.family / "png/multitone/boston-1889-4202.png"
        before_svg, before_png = gray.read_bytes(), png.read_bytes()
        revival.export_glyph(Namespace(id=self.family.name, character="uniE000.primary"))
        edit = self.family / "source/glyphs/uniE000.primary.json"
        data = json.loads(edit.read_text()); data["path"] += " M200 500H300V600H200Z"
        revival.write_json(edit, data)
        revival.build_family(self.family)
        revival.validate_family(self.family)
        self.assertNotEqual(before_svg, gray.read_bytes())
        self.assertNotEqual(before_png, png.read_bytes())
        self.assertEqual(mono, (self.family / "svg/boston-1889-4202.svg").read_bytes())

    def test_duplicate_id_and_out_of_range_codepoint_are_rejected(self):
        m = json.loads((self.family / "font.json").read_text())
        duplicate = copy.deepcopy(m); duplicate["icons"].append(copy.deepcopy(m["icons"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate icon"):
            revival.validate_icon_metadata(self.family, duplicate)
        for cp in ("0041", "F900", "../x"):
            invalid = copy.deepcopy(m); invalid["icons"][0]["codepoint"] = cp
            with self.subTest(codepoint=cp), self.assertRaisesRegex(ValueError, "Private Use"):
                revival.validate_icon_metadata(self.family, invalid)

    def test_multi_tone_requires_two_or_three_named_regions(self):
        m = json.loads((self.family / "font.json").read_text())
        for layers in ([m["icons"][0]["multitone_layers"][0]], m["icons"][0]["multitone_layers"] * 2):
            bad = copy.deepcopy(m); bad["icons"][0]["multitone_layers"] = layers
            with self.assertRaisesRegex(ValueError, "two or three"):
                revival.validate_icon_metadata(self.family, bad)
        self.assertFalse((self.family / "svg/grayscale").exists())
        self.assertFalse((self.family / "png/grayscale").exists())
        self.assertFalse((self.family / "web/icons-grayscale.svg").exists())

    def test_font_mapping_and_clipping_fail_before_packaging(self):
        file = self.family / "fonts/BostonCuts1889-Regular.otf"
        original = file.read_bytes()
        with TTFont(file, recalcTimestamp=False) as font:
            for table in font["cmap"].tables:
                if table.isUnicode() and 0xE000 in table.cmap:
                    table.cmap[0xE001] = table.cmap.pop(0xE000)
            font.save(file)
        with self.assertRaisesRegex(ValueError, "icon coverage differs"):
            revival.validate_family(self.family)
        file.write_bytes(original)
        revival.write_json(self.family / "source/glyphs/uniE000.json", {
            "glyph": "uniE000", "advance_width": 1955,
            "path": "M64 0H1800V2200H64Z", "notes": "Clipping regression fixture"})
        revival.build_family(self.family)
        with self.assertRaisesRegex(ValueError, "clip its SVG/em box"):
            revival.validate_family(self.family)

    def test_rebuild_detects_tampered_svg_and_stale_icon_gallery(self):
        revival.build_catalog()
        file = self.family / "svg/boston-1889-4202.svg"
        original = file.read_bytes()
        file.write_text(file.read_text().replace("currentColor", "red"))
        # Simulate someone refreshing hashes without regenerating from the master.
        (self.family / "SHA256SUMS.txt").write_text(revival.checksums(self.family))
        with self.assertRaisesRegex(ValueError, "rebuild differs"):
            revival.check()
        file.write_bytes(original)
        (self.family / "SHA256SUMS.txt").write_text(revival.checksums(self.family))
        gallery = self.root / "icons.html"
        gallery.write_text(gallery.read_text() + "<!-- stale -->")
        with self.assertRaisesRegex(ValueError, "icons.html is stale"):
            revival.check()


if __name__ == "__main__":
    unittest.main()
