#!/usr/bin/env python3
"""Assemble the public gallery; keep large downloads on the repository host.

The editable masters, native scans and full proofs remain in the repository.
Local galleries retain relative paths. Staged downloads and comparison previews
link to the same committed files on GitHub, avoiding duplicate large assets
in GitHub Pages' 1 GB published-site allowance.
"""
import argparse
import base64
import gzip
from html.parser import HTMLParser
import html
import os
from pathlib import Path
import re
import shutil
from urllib.parse import quote, unquote, urlsplit

REPO = Path(__file__).resolve().parents[1]
DOWNLOAD_BASE = 'https://raw.githubusercontent.com/haroldus-/font-revival/main/'
CSS_URL = re.compile(r'url\(\s*[\'"]?([^\s\)\'"]+)[\'"]?\s*\)')
DETAIL_SVG = re.compile(r'(<svg\b[^>]*\bdata-icon-format="(multitone|monochrome)"[^>]*>)(.*?)(</svg>)', re.S)


def pack_detail_artwork(content, helper_url, minimum=100_000):
    """Losslessly pack large preview paths in the published HTML only.

    The ordinary SVG download is also a visible fallback. The browser restores
    the exact inline paths so the existing size and colour controls still work.
    Local repository pages and downloadable artwork stay plain SVG.
    """
    packed = False

    def replace(match):
        nonlocal packed
        opening, kind, artwork, closing = match.groups()
        if len(artwork.encode()) < minimum:
            return match.group()
        prefix = 'multitone/' if kind == 'multitone' else ''
        download = re.search(r'<a download href="([^"]+/svg/' + prefix + r'[^/"<>]+\.svg)">', content)
        viewbox = re.search(r'viewBox="([^"]+)"', opening)
        if not download or not viewbox:
            return match.group()
        x, y, width, height = viewbox.group(1).split()
        payload = base64.b64encode(gzip.compress(artwork.encode(), mtime=0)).decode('ascii')
        if len(payload) >= len(artwork):
            return match.group()
        packed = True
        fallback = (f'<image data-fallback-href="{download.group(1)}" x="{x}" y="{y}" '
                    f'width="{width}" height="{height}"/>')
        return opening + fallback + '<script type="application/octet-stream" data-packed-svg>' + payload + '</script>' + closing

    content = DETAIL_SVG.sub(replace, content)
    if packed:
        script = f'<script defer src="{html.escape(helper_url, quote=True)}"></script>\n'
        content = content.replace('</body>', script + '</body>')
    return content


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()
        self.downloads = set()
        self.comparison_images = set()
        self.inline_assets = set()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == 'a' and 'download' in attributes and attributes.get('href'):
            self.downloads.add(attributes['href'])
        comparison = tag == 'img' and 'comparison' in attributes.get('class', '').split()
        if comparison and attributes.get('src'):
            self.comparison_images.add(attributes['src'])
        for key, value in attrs:
            if key in ('src', 'href', 'data-art-chunk') and value:
                self.urls.add(value)
                if key in ('src', 'data-art-chunk') and not comparison:
                    self.inline_assets.add(value)


def local_path(root, origin, url):
    parts = urlsplit(url)
    if parts.scheme or parts.netloc or not parts.path:
        return None
    target = ((root if parts.path.startswith('/') else origin.parent) /
              unquote(parts.path).lstrip('/')).resolve()
    target.relative_to(root.resolve())
    if not target.is_file():
        raise ValueError(f'Missing gallery asset: {target.relative_to(root)}')
    return target


def assemble(root, output, download_base=DOWNLOAD_BASE):
    root, output = root.resolve(), output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    pending = [root / name for name in ('index.html', 'icons.html', 'catalog.json', 'icons.json', 'LICENSE')]
    written = set()
    while pending:
        file = pending.pop()
        relative = file.relative_to(root)
        if relative in written or file.suffix.lower() in ('.pdf', '.zip'):
            continue
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if file.suffix in ('.html', '.css'):
            content = file.read_text()
            if file.suffix == '.html' and '</body>' in content:
                helper = os.path.relpath(root / 'site/unpack-art.js', file.parent)
                content = pack_detail_artwork(content, Path(helper).as_posix())
            references = set(CSS_URL.findall(content))
            downloads, comparisons, inline = set(), set(), set(references)
            if file.suffix == '.html':
                parser = References(); parser.feed(content)
                references.update(parser.urls)
                downloads, comparisons = parser.downloads, parser.comparison_images
                inline.update(parser.inline_assets)
            for url in sorted(references):
                target = local_path(root, file, url)
                if target is None:
                    continue
                remote_asset = target.suffix.lower() in ('.pdf', '.zip') or url in downloads or url in comparisons
                if remote_asset:
                    remote = download_base + quote(target.relative_to(root).as_posix())
                    fragment = urlsplit(url).fragment
                    if fragment:
                        remote += '#' + fragment
                    if url in comparisons:
                        content = content.replace('src="' + url + '"', 'src="' + remote + '"')
                    if url in downloads or target.suffix.lower() in ('.pdf', '.zip'):
                        content = content.replace('href="' + url + '"', 'href="' + remote + '"')
                if not remote_asset or url in inline:
                    pending.append(target)
            destination.write_text(content)
        else:
            shutil.copyfile(file, destination)
        written.add(relative)
    total = sum((output / name).stat().st_size for name in written)
    if total > 1_000_000_000:
        raise ValueError(f'Published site exceeds 1 GB: {total:,} bytes')
    return total, len(written)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=REPO / '_site')
    args = parser.parse_args()
    total, count = assemble(REPO, args.output)
    print(f'Staged {count:,} files, {total / 1_000_000:.1f} MB, in {args.output}')
