"""Protect icon identity and the shared SVG/font maintenance contract."""

import contextlib
import copy
import importlib.util
import io
import json
import re
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from argparse import Namespace
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools import subset
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fontrevival_icons", REPO / "scripts/fontrevival.py")
revival = importlib.util.module_from_spec(spec)
spec.loader.exec_module(revival)


class IconWorkflowTests(unittest.TestCase):
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
        self.assertNotIn('<img', index)
        self.assertNotIn('Engraved detail, original proportions', index)
        self.assertNotIn('data-art-chunk', index)
        self.assertIn('data-id="test-cut-96"', index)
        self.assertEqual(index.count('data-section="holiday-cuts" hidden>'), 1)
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
        self.assertEqual(catalog['icons'][0]['sections'], ['holiday-cuts'])
        self.assertEqual(catalog['icons'][0]['page'], 'icons/test-cut-0.html')
        self.assertIn('name="collection" value="boston-cuts-1889"', index)
        self.assertIn('name="type" value="cuts"', index)
        self.assertIn('name="section" value="holiday-cuts"', index)

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
                self.assertTrue(set(section['printed_pages']) <= {i['printed_page'] for i in m['icons']})
                self.assertTrue(set(section.get('icons', [])) <= {i['id'] for i in m['icons']})
                selected = [i for i in m['icons'] if section in revival.icon_navigation(m, i, taxonomy)[1]]
                self.assertTrue(selected)
        cuts = families['boston-cuts-1889']
        santa = next(i for i in cuts['icons'] if i['id'] == 'boston-1889-4202')
        self.assertEqual([s['id'] for s in revival.icon_navigation(cuts, santa, taxonomy)[1]], ['holiday-cuts'])

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
