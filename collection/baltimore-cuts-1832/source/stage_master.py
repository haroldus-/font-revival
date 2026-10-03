"""Stage a compact CFF baseline with full-detail standard glyph overrides.

The baseline contains all encoded artwork and named slots for private tone layers.
Full tone drawings and oversized monochrome originals live in source/glyphs/.
The ordinary source loader restores them before artwork generation. This avoids
duplicating millions of tonal control points in one enormous XML file.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'scripts/fontrevival.py').exists())
sys.path.insert(0, str(ROOT / 'scripts'))
import fontrevival as revival


def stage(family, source, output):
    font = TTFont(source, recalcTimestamp=False)
    glyphs = font.getGlyphSet()
    top = font['CFF '].cff.topDictIndex[0]
    encoded = set(font.getBestCmap().values()) | {'.notdef'}
    for name in font.getGlyphOrder():
        file = family / 'source/truetype-glyphs' / (name + '.json')
        tonal = name not in encoded
        if not tonal and not file.exists():
            continue
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        full = pen.getCommands()
        advance = font['hmtx'][name][0]
        compact = ''
        if not tonal:
            item = json.loads(file.read_text())
            if hashlib.sha256(full.encode()).hexdigest() != item['master_sha256']:
                raise ValueError('Stale approximation ' + name)
            compact = item['path']
        revival.write_json(family / 'source/glyphs' / (name + '.json'), {
            'glyph': name, 'advance_width': advance, 'path': full, 'preserve_commands': True,
            'notes': 'Full native-resolution historical tracing, restored through the standard '
                     'glyph-edit mechanism over the compact CFF baseline. Private tone layers '
                     'have named empty baseline slots; encoded icons have complete outlines. '
                     'This full-detail drawing is authoritative for vector artwork.'})
        pen = T2CharStringPen(advance, None)
        parse_path(compact, pen)
        top.CharStrings[name] = pen.getCharString(top.Private, top.GlobalSubrs)
        bounds = BoundsPen(None)
        parse_path(compact, bounds)
        font['hmtx'][name] = (advance, round(bounds.bounds[0]) if bounds.bounds else 0)
    font.save(output)
    print('Staged', output, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family')
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    stage(ROOT / 'collection' / args.family, args.source, args.output)
