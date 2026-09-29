import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('build_site', Path(__file__).resolve().parents[1] / 'scripts/build_site.py')
site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(site)


class PublicSiteTests(unittest.TestCase):
    def test_local_gallery_and_downloads_survive_public_assembly(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'repository'; root.mkdir()
            output = Path(temp) / 'published'
            files = {
                'index.html': '<a href="icons.html">Icons</a>',
                'icons.html': '<link href="web/icons.css"><article data-art-chunk="art/1.js"><img src="proof.png"><a href="proof.pdf#page=2">Proof</a><a download href="bundle.zip">Download</a></article>',
                'catalog.json': '{}', 'icons.json': '{}', 'LICENSE': 'MIT',
                'web/icons.css': '@import url("font.css");',
                'web/font.css': '@font-face{src:url(../fonts/icons.woff2)}',
                'fonts/icons.woff2': 'font', 'art/1.js': 'artwork',
                'proof.png': 'preview', 'proof.pdf': 'full proof', 'bundle.zip': 'bundle',
                'source/font.ttx': 'editable master',
            }
            for name, text in files.items():
                file = root / name; file.parent.mkdir(parents=True, exist_ok=True); file.write_text(text)
            size, count = site.assemble(root, output, 'https://example.test/repository/')
            self.assertGreater(size, 0)
            self.assertEqual(count, 10)
            self.assertEqual((root / 'icons.html').read_text(), files['icons.html'])
            public = (output / 'icons.html').read_text()
            self.assertIn('https://example.test/repository/proof.pdf#page=2', public)
            self.assertIn('https://example.test/repository/bundle.zip', public)
            self.assertEqual((output / 'fonts/icons.woff2').read_text(), 'font')
            self.assertEqual((output / 'art/1.js').read_text(), 'artwork')
            self.assertFalse((output / 'source').exists())
            self.assertFalse((output / 'bundle.zip').exists())

    def test_nested_icon_pages_resolve_assets_and_filtered_return_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'repository'; root.mkdir()
            output = Path(temp) / 'published'
            files = {
                'index.html': '<a href="icons.html">Icons</a>',
                'icons.html': '<a href="icons/father-christmas.html">Father Christmas</a>',
                'icons/father-christmas.html': '<a href="../icons.html?section=holiday-cuts#collection">Holiday cuts</a><link href="../site/icon-fonts/icons.css"><script src="../site/icon-detail.js"></script><a href="../collection/cuts/downloads/web.zip">Download</a>',
                'site/icon-fonts/icons.css': '@font-face{src:url(cuts-000.woff2);unicode-range:U+E000}',
                'site/icon-fonts/cuts-000.woff2': 'subset',
                'site/icon-detail.js': 'controls',
                'collection/cuts/downloads/web.zip': 'bundle',
                'catalog.json': '{}', 'icons.json': '{}', 'LICENSE': 'MIT',
            }
            for name, text in files.items():
                file = root / name; file.parent.mkdir(parents=True, exist_ok=True); file.write_text(text)
            _, count = site.assemble(root, output, 'https://example.test/repository/')
            self.assertEqual(count, 9)
            public = (output / 'icons/father-christmas.html').read_text()
            self.assertIn('../icons.html?section=holiday-cuts#collection', public)
            self.assertIn('https://example.test/repository/collection/cuts/downloads/web.zip', public)
            self.assertEqual((output / 'site/icon-fonts/cuts-000.woff2').read_text(), 'subset')
            self.assertEqual((output / 'site/icon-detail.js').read_text(), 'controls')
            self.assertEqual((root / 'icons/father-christmas.html').read_text(), files['icons/father-christmas.html'])

    def test_missing_or_outside_assets_fail_before_deployment(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ValueError):
                site.local_path(root, root / 'icons.html', 'missing.svg')
            with self.assertRaises(ValueError):
                site.local_path(root, root / 'icons.html', '../outside.svg')


if __name__ == '__main__':
    unittest.main()
