#!/usr/bin/env python3
"""Prepare selected glyph edits from historical crops without replacing a master.

Writes reviewable JSON into the requested output directory. The original CFF
master supplies glyph names, advances and unchanged accent contours. Normal
builds continue to apply the reviewed source/glyphs files over that master.
"""

import argparse
import json
from pathlib import Path

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont
from PIL import Image

import fontrevival
from trace_specimen import require_potrace, trace


def contours(glyph):
    """Retain exact commands, normalizing an optional closing line to its start."""
    pen = RecordingPen()
    glyph.draw(pen)
    result, current = [], []
    for operation in pen.value:
        current.append(operation)
        if operation[0] == 'closePath':
            if len(current) >= 3 and current[-2] == ('lineTo', current[0][1]):
                del current[-2]
            result.append(current)
            current = []
    if current:
        raise ValueError('Expected closed CFF contours.')
    return result


def replace_base(glyph, old_base, new_path):
    """Replace exact base contours, retaining every other contour unmodified."""
    remaining = contours(glyph)
    for contour in contours(old_base):
        if contour not in remaining:
            raise ValueError('Dependent glyph does not contain the exact base contours.')
        remaining.remove(contour)
    pen = SVGPathPen(None)
    parse_path(new_path, pen)
    for contour in remaining:
        recording = RecordingPen()
        recording.value = contour
        recording.replay(pen)
    return pen.getCommands()


def prepare(family, output, potrace):
    require_potrace(potrace)
    recipe = json.loads((family / 'source/tracing.json').read_text())
    if recipe.get('mode') != 'glyph-revision':
        raise ValueError('Revision preparation requires mode: glyph-revision.')
    drawings, images = {}, {}
    with TTFont(recalcTimestamp=False) as master:
        # Deliberately exclude overrides: repeated preparation must start from
        # the same original contours, including those in dependent accents.
        master.importXML(family / 'source/font.ttx')
        if 'CFF ' not in master or 'fvar' in master:
            raise ValueError('Revision preparation requires a static CFF master.')
        cmap, glyphs = master.getBestCmap(), master.getGlyphSet()
        for ch, entry in recipe['glyphs'].items():
            name = cmap[ord(ch)]
            if name in drawings:
                raise ValueError(f'Duplicate revision for aliased glyph {name}.')
            width = master['hmtx'][name][0]
            if entry.get('advance_width', width) != width:
                raise ValueError(f'Revision must preserve the advance width of {name}.')
            file = family / entry['file']
            if file not in images:
                with Image.open(file) as image:
                    images[file] = image.convert('L')
            drawing = trace(images[file], entry | {'advance_width': width}, potrace)
            drawings[name] = drawing | {'glyph': name, 'notes': entry['notes']}

        for base, dependents in recipe.get('replace_bases', {}).items():
            for name in dependents:
                if name in drawings:
                    raise ValueError(f'Duplicate revision for dependent glyph {name}.')
                drawings[name] = {
                    'glyph': name,
                    'advance_width': master['hmtx'][name][0],
                    'path': replace_base(glyphs[name], glyphs[base], drawings[base]['path']),
                    'notes': f'Use revised {base}; retain the original accent contours and positions. '
                             'The accent remains a modern reconstruction. See source/tracing.json.',
                }
    output.mkdir(parents=True, exist_ok=True)
    for name, drawing in drawings.items():
        fontrevival.write_json(output / f'{name}.json', drawing)
    print(f'Prepared {len(drawings)} glyph edits in {output}; review before copying into source/glyphs/.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('id')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--potrace', default='potrace')
    args = parser.parse_args()
    prepare(fontrevival.family_dir(args.id), args.output, args.potrace)
