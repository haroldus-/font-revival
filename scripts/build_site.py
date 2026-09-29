#!/usr/bin/env python3
"""Assemble the public gallery; keep large downloads on the repository host.

The editable masters, native scans and full proofs remain in the repository.
Local galleries retain relative paths. Only the staged site's PDF/ZIP links are
rewritten to the same committed files on GitHub, avoiding duplicate large assets
in GitHub Pages' 1 GB published-site allowance.
"""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
from urllib.parse import quote, unquote, urlsplit

REPO = Path(__file__).resolve().parents[1]
DOWNLOAD_BASE = 'https://raw.githubusercontent.com/haroldus-/font-revival/main/'
CSS_URL = re.compile(r'url\(\s*[\'"]?([^\s\)\'"]+)[\'"]?\s*\)')


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('src', 'href', 'data-art-chunk') and value:
                self.urls.add(value)


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
            references = set(CSS_URL.findall(content))
            if file.suffix == '.html':
                parser = References(); parser.feed(content)
                references.update(parser.urls)
            for url in sorted(references):
                target = local_path(root, file, url)
                if target is None:
                    continue
                if target.suffix.lower() in ('.pdf', '.zip'):
                    remote = download_base + quote(target.relative_to(root).as_posix())
                    fragment = urlsplit(url).fragment
                    if fragment:
                        remote += '#' + fragment
                    content = content.replace('"' + url + '"', '"' + remote + '"')
                else:
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
