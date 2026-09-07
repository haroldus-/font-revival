"""Exercise contributor operations and catch release regressions."""

import contextlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from argparse import Namespace
from html.parser import HTMLParser
from pathlib import Path

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fontrevival", REPO / "scripts/fontrevival.py")
revival = importlib.util.module_from_spec(spec)
spec.loader.exec_module(revival)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copyfile(REPO / "LICENSE", self.root / "LICENSE")
        shutil.copytree(REPO / "site", self.root / "site")
        self.family = self.root / "collection" / "johnson-1892"
        shutil.copytree(REPO / "collection" / "johnson-1892", self.family)
        revival.ROOT = self.root
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.output.__exit__(None, None, None)
        revival.ROOT = REPO
        self.temp.cleanup()

    def test_ids_cannot_escape_collection(self):
        for value in ("../outside", "/tmp/font", "font/name", "Mixed Case"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                revival.family_dir(value)

    def test_scaffold_refuses_to_overwrite_existing_work(self):
        before = (self.family / "font.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "already exists"):
            revival.new_family(Namespace(id="johnson-1892", name="Replacement", year=1892))
        self.assertEqual(before, (self.family / "font.json").read_bytes())

    def test_new_family_requires_provenance_then_can_import_and_build(self):
        revival.new_family(Namespace(id="example-1890", name="Example 1890", year=1890))
        path = self.root / "collection/example-1890"
        with self.assertRaisesRegex(ValueError, "fill in"):
            revival.metadata(path)
        m = json.loads((self.family / "font.json").read_text())
        m.update(id="example-1890", name="Example 1890", postscript_name="Example1890-Regular", year=1890)
        shutil.copytree(self.family / "reference", path / "reference", dirs_exist_ok=True)
        revival.write_json(path / "font.json", m)
        revival.import_font(Namespace(id=m["id"], font=self.family / "fonts/Johnson1892-Regular.otf", replace=False))
        revival.build_family(path)
        revival.validate_family(path)
        with self.assertRaisesRegex(ValueError, "Source exists"):
            revival.import_font(Namespace(id=m["id"], font=path / "fonts/Example1890-Regular.otf", replace=False))

    def test_clean_rebuild_is_identical(self):
        revival.build_family(self.family)
        revival.build_catalog()
        revival.check()

    def test_source_change_requires_rebuilt_outputs(self):
        revival.build_catalog()
        revival.export_glyph(Namespace(id="johnson-1892", character="j"))
        path = self.family / "source/glyphs/j.json"
        data = json.loads(path.read_text())
        data["advance_width"] += 20
        revival.write_json(path, data)
        (self.family / "SHA256SUMS.txt").write_text(revival.checksums(self.family))
        with self.assertRaisesRegex(ValueError, "rebuild differs"):
            revival.check()

    def test_glyph_edit_reaches_all_formats_and_preserves_other_glyphs(self):
        old = TTFont(self.family / "fonts/Johnson1892-Regular.otf")
        p = RecordingPen(); old.getGlyphSet()["a"].draw(p)
        old_a = p.value
        revival.export_glyph(Namespace(id="johnson-1892", character="j"))
        path = self.family / "source/glyphs/j.json"
        data = json.loads(path.read_text())
        data["advance_width"] += 17
        revival.write_json(path, data)
        with self.assertRaisesRegex(ValueError, "already exists"):
            revival.export_glyph(Namespace(id="johnson-1892", character="j"))
        revival.build_family(self.family)
        revival.validate_family(self.family)
        font = TTFont(self.family / "fonts/Johnson1892-Regular.otf")
        self.assertEqual(data["advance_width"], font["hmtx"].metrics["j"][0])
        p = RecordingPen(); font.getGlyphSet()["a"].draw(p)
        self.assertEqual(old_a, p.value)
        self.assertEqual(old.getBestCmap(), font.getBestCmap())
        for tag in ("GPOS", "GSUB"):
            if tag in old:
                self.assertEqual(old[tag].compile(old), font[tag].compile(font))

    def test_empty_visible_glyph_is_rejected(self):
        revival.write_json(self.family / "source/glyphs/a.json", {
            "glyph": "a", "advance_width": 200, "path": "", "notes": "Broken input for regression test"})
        revival.build_family(self.family)
        with self.assertRaisesRegex(ValueError, "empty visible character"):
            revival.validate_family(self.family)

    def test_restricted_embedding_is_rejected(self):
        path = self.family / "fonts/Johnson1892-Regular.otf"
        font = TTFont(path, recalcTimestamp=False)
        font["OS/2"].fsType = 4
        font.save(path)
        with self.assertRaisesRegex(ValueError, "embedding must be unrestricted"):
            revival.validate_family(self.family)

    def test_reference_path_cannot_escape_family(self):
        m = json.loads((self.family / "font.json").read_text())
        m["sources"][0]["file"] = "../../LICENSE"
        revival.write_json(self.family / "font.json", m)
        with self.assertRaisesRegex(ValueError, "invalid reference path"):
            revival.metadata(self.family)

    def test_gallery_downloads_resolve(self):
        revival.build_catalog()
        paths = []

        class Links(HTMLParser):
            def handle_starttag(self, tag, attrs):
                for key, value in attrs:
                    if key in ("href", "src") and value.startswith("collection/"):
                        paths.append(value)

        Links().feed((self.root / "index.html").read_text())
        self.assertGreaterEqual(len(paths), 4)
        for path in paths:
            self.assertTrue((self.root / path).is_file(), path)


if __name__ == "__main__":
    unittest.main()
