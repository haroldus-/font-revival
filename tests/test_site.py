import importlib.util
import base64
import gzip
from pathlib import Path
import tempfile
import re
import unittest

SPEC = importlib.util.spec_from_file_location('build_site', Path(__file__).resolve().parents[1] / 'scripts/build_site.py')
site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(site)


class PublicSiteTests(unittest.TestCase):
    def test_social_images_are_published_from_absolute_metadata_urls(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'repository'; root.mkdir()
            output = Path(temp) / 'published'
            image_url = site.SITE_BASE + 'site/preview.png'
            files = {
                'index.html': f'<meta property="og:image" content="{image_url}">',
                'icons.html': f'<meta name="twitter:image" content="{image_url}">',
                'site/preview.png': 'preview',
                'catalog.json': '{}', 'icons.json': '{}', 'LICENSE': 'MIT',
            }
            for name, content in files.items():
                file = root / name; file.parent.mkdir(parents=True, exist_ok=True); file.write_text(content)
            site.assemble(root, output)
            self.assertEqual((output / 'site/preview.png').read_text(), 'preview')
            for page in ('index.html', 'icons.html'):
                self.assertEqual((output / page).read_text(), files[page])
            self.assertIsNone(site.local_path(root, root / 'index.html', 'https://example.test/preview.png'))
            (root / 'site/preview.png').unlink()
            with self.assertRaisesRegex(ValueError, 'Missing gallery asset'):
                site.assemble(root, output)

    def test_published_artwork_round_trips_without_changing_paths_or_accessibility(self):
        artwork = '<path class="fr-primary" transform="scale(1 -1)" d="' + 'M0 0L123.015625 456.984375Z' * 5000 + '"/>'
        original = ('<body><svg data-icon-format="multitone" aria-label="Historical &amp; new" '
                    'viewBox="0 -1900 2048 2048">' + artwork + '</svg>'
                    '<a download href="../collection/cuts/svg/multitone/example.svg">SVG</a></body>')
        packed = site.pack_detail_artwork(original, '../site/unpack-art.js')
        payload = re.search(r'data-packed-svg>([^<]+)</script>', packed).group(1)
        self.assertEqual(gzip.decompress(base64.b64decode(payload)).decode(), artwork)
        self.assertLess(len(packed), len(original) // 2)
        self.assertIn('aria-label="Historical &amp; new"', packed)
        self.assertIn('x="0" y="-1900" width="2048" height="2048"', packed)
        self.assertEqual(packed.count('src="../site/unpack-art.js"'), 1)
        self.assertEqual(packed, site.pack_detail_artwork(original, '../site/unpack-art.js'))

    def test_small_or_unlinked_artwork_stays_inline(self):
        original = '<body><svg data-icon-format="monochrome" viewBox="0 0 10 10"><path d="M0 0H10V10Z"/></svg></body>'
        self.assertEqual(site.pack_detail_artwork(original, 'loader.js'), original)
        self.assertEqual(site.pack_detail_artwork(original, 'loader.js', minimum=0), original)

    def test_public_assembly_copies_unpacker_and_routes_fallback_to_download(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'repository'; root.mkdir()
            output = Path(temp) / 'published'
            artwork = '<path d="' + 'M0 0H10V10Z' * 10000 + '"/>'
            page = ('<body><svg data-icon-format="monochrome" viewBox="0 -1900 2048 2048">' + artwork +
                    '</svg><a download href="../collection/cuts/svg/example.svg">SVG</a></body>')
            files = {'index.html': '<a href="icons.html">Icons</a>',
                     'icons.html': '<a href="icons/example.html">Example</a>',
                     'icons/example.html': page, 'site/unpack-art.js': 'unpack',
                     'collection/cuts/svg/example.svg': '<svg/>',
                     'catalog.json': '{}', 'icons.json': '{}', 'LICENSE': 'MIT'}
            for name, content in files.items():
                file = root / name; file.parent.mkdir(parents=True, exist_ok=True); file.write_text(content)
            site.assemble(root, output, 'https://example.test/repository/')
            self.assertEqual((root / 'icons/example.html').read_text(), page)
            self.assertEqual((output / 'site/unpack-art.js').read_text(), 'unpack')
            public = (output / 'icons/example.html').read_text()
            self.assertIn('<image data-fallback-href="https://example.test/repository/collection/cuts/svg/example.svg"', public)
            self.assertIn('data-packed-svg>', public)
            self.assertFalse((output / 'collection/cuts/svg/example.svg').exists())

    def test_download_artwork_and_comparison_images_do_not_duplicate_the_gallery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'repository'; root.mkdir()
            output = Path(temp) / 'published'
            files = {'index.html': '<a href="icons.html">Icons</a>',
                     'icons.html': '<svg><path d="M0 0H10V10Z"/></svg><a download href="art.svg">SVG</a><img class="comparison" src="comparison.png"><a download href="thumb.png">PNG</a><img src="thumb.png">',
                     'catalog.json': '{}', 'icons.json': '{}', 'LICENSE': 'MIT',
                     'art.svg': '<svg/>', 'comparison.png': 'large proof', 'thumb.png': 'thumbnail'}
            for name, content in files.items():
                (root / name).write_text(content)
            site.assemble(root, output, 'https://example.test/repository/')
            public = (output / 'icons.html').read_text()
            self.assertIn('href="https://example.test/repository/art.svg"', public)
            self.assertIn('src="https://example.test/repository/comparison.png"', public)
            self.assertIn('src="thumb.png"', public)
            self.assertTrue((output / 'thumb.png').is_file())
            self.assertFalse((output / 'art.svg').exists())
            self.assertFalse((output / 'comparison.png').exists())
            self.assertEqual(files['icons.html'], (root / 'icons.html').read_text())

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
