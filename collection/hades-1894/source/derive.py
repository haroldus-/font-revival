#!/usr/bin/env python3
"""Prepare a registered Hades master from the committed Erebus CFF source.

Requires requirements-tracing.txt. Writes an OTF and companion audit JSON only;
use the normal import command to install the reviewed master.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import fontrevival
from outline_geometry import shadow
from trace_specimen import assemble
from fontTools.pens.svgPathPen import SVGPathPen


def prepare(output):
    family = Path(__file__).resolve().parents[1]
    recipe = json.loads((family / 'source/registration.json').read_text())
    original = fontrevival.family_dir(recipe['source_family'])
    metadata = fontrevival.metadata(original)
    if metadata['version'] != recipe['source_version']:
        raise ValueError('Review the pairing before deriving from a different Erebus version.')
    font = fontrevival.load_source(original, metadata)
    cmap, glyphs = font.getBestCmap(), font.getGlyphSet()
    drawings, aliases, encoded = {}, {}, {}
    for cp, name in sorted(cmap.items()):
        ch = chr(cp)
        if name in encoded:
            aliases[ch] = encoded[name]
            continue
        encoded[name] = ch
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        drawings[ch] = {
            'path': shadow(pen.getCommands(), *recipe['offset']),
            'advance_width': font['hmtx'][name][0],
            'notes': 'Registered reconstruction from Erebus 1894; shifted silhouette minus original. See registration.json.',
        }
    features = (family / 'source/features.fea').read_text()
    if features != (original / 'source/features.fea').read_text():
        raise ValueError('Paired fonts must use identical kerning.')
    assemble(family, drawings, aliases, output, features, {
        'cap_height': font['OS/2'].sCapHeight,
        'x_height': font['OS/2'].sxHeight,
        'win_ascent': font['OS/2'].usWinAscent,
        'win_descent': font['OS/2'].usWinDescent,
    })
    fontrevival.write_json(output.with_suffix('.companions.json'), {'glyphs': drawings, 'aliases': aliases})
    print(f'Prepared {output}. Review, retain companion paths, then use import.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    prepare(parser.parse_args().output)
