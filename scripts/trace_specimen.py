#!/usr/bin/env python3
"""Reconstruct a documented initial master from historical crops and SVG drawings.

Optional source-preparation tool: Potrace 1.16 plus requirements.txt.
Normal release builds use source/font.ttx and do not run this script.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from fontTools.agl import UV2AGL
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path
from PIL import Image, ImageDraw, ImageFilter, ImageOps

import fontrevival


def components(mask, value):
    """Four-connected pixel components; crops are small, no numerical stack needed."""
    pixels = mask.load()
    unseen = {(x, y) for y in range(mask.height) for x in range(mask.width)
              if pixels[x, y] == value}
    result = []
    while unseen:
        seed = min(unseen)
        unseen.remove(seed)
        found, stack = [seed], [seed]
        while stack:
            x, y = stack.pop()
            for point in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
                if point in unseen:
                    unseen.remove(point)
                    found.append(point)
                    stack.append(point)
        result.append(found)
    return result


def clean_crop(image, entry):
    crop = image.crop(entry['box']).convert('L')
    draw = ImageDraw.Draw(crop)
    for rectangle in entry.get('erase', []):
        draw.rectangle(rectangle, fill=255)
    crop = ImageOps.expand(crop, border=4, fill=255)
    crop = crop.filter(ImageFilter.GaussianBlur(entry.get('blur', 0.55)))
    mask = crop.point(lambda p: 0 if p < entry.get('threshold', 135) else 255)
    ink = components(mask, 0)
    if not ink:
        raise ValueError('No ink in crop: ' + str(entry['box']))
    # These manifests select connected letters, not detached punctuation.
    largest = max(ink, key=len)
    clean = Image.new('L', mask.size, 255)
    for point in largest:
        clean.putpixel(point, 0)
    for component in components(clean, 255):
        if len(component) <= entry.get('fill_holes', 8):
            for point in component:
                clean.putpixel(point, 0)
    return clean


def trace(image, entry, potrace):
    mask = clean_crop(image, entry)
    with tempfile.TemporaryDirectory(prefix='revival-trace-') as tmp:
        pbm, svg = Path(tmp)/'crop.pbm', Path(tmp)/'crop.svg'
        mask.convert('1').save(pbm)
        subprocess.run([potrace, str(pbm), '--svg', '--output', str(svg),
                        '--turdsize', '0', '--alphamax', '1',
                        '--opttolerance', str(entry.get('tolerance', 0.35)),
                        '--unit', '10'], check=True, capture_output=True)
        # Potrace's path coordinates are already y-up in tenths of a pixel.
        # Ignore its display-only SVG group transform (y-down for browsers).
        rec = RecordingPen()
        for element in ET.parse(svg).iter('{http://www.w3.org/2000/svg}path'):
            parse_path(element.attrib['d'], rec)
    bounds = BoundsPen(None)
    rec.replay(bounds)
    x0, y0, x1, y1 = bounds.bounds
    scale = entry['height'] / (y1-y0)
    left, right = entry.get('bearings', [45, 45])
    sx = scale * entry.get('width_scale', 1)
    out = SVGPathPen(None)
    rec.replay(TransformPen(RoundingPen(out),
                           (sx, 0, 0, scale, left-x0*sx, entry.get('y_min', 0)-y0*scale)))
    return {'path': out.getCommands(), 'advance_width': round((x1-x0)*sx+left+right)}


def glyph_name(character):
    return UV2AGL.get(ord(character), f'uni{ord(character):04X}')


def assemble(family, drawings, aliases, output, features=''):
    """Make a complete static CFF OTF for the standard import command."""
    m = fontrevival.metadata(family)
    cmap = {ord(ch): glyph_name(ch) for ch in drawings}
    for ch, target in aliases.items():
        cmap[ord(ch)] = glyph_name(target)
    missing = set(range(32, 127)) - cmap.keys()
    if missing:
        raise ValueError('Missing Basic Latin: ' + ''.join(chr(cp) for cp in sorted(missing)))
    notdef = {'advance_width': 600, 'path': 'M60 0H540V700H60Z M100 40V660H500V40Z'}
    named = {'.notdef': notdef} | {glyph_name(ch): data for ch, data in drawings.items()}
    order = list(named)
    charstrings, metrics = {}, {}
    for name, data in named.items():
        pen = T2CharStringPen(data['advance_width'], None)
        parse_path(data['path'], pen)
        charstrings[name] = pen.getCharString()
        bounds = BoundsPen(None)
        parse_path(data['path'], bounds)
        metrics[name] = (data['advance_width'], round(bounds.bounds[0]) if bounds.bounds else 0)
    fb = FontBuilder(1000, isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupCFF(m['postscript_name'], {'FullName': m['name'], 'FamilyName': m['name'], 'Weight': 'Regular'}, charstrings, {})
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=850, descent=-200, lineGap=100)
    fb.setupNameTable({'familyName': m['name'], 'styleName': 'Regular', 'psName': m['postscript_name']})
    fb.setupOS2(sTypoAscender=850, sTypoDescender=-200, sTypoLineGap=100,
                usWinAscent=900, usWinDescent=220, sxHeight=700, sCapHeight=700,
                usWeightClass=400, usWidthClass=5, fsType=0)
    fb.setupPost()
    if features:
        addOpenTypeFeaturesFromString(fb.font, features)
    fontrevival.normalize(fb.font, m)
    output.parent.mkdir(parents=True, exist_ok=True)
    fb.save(output)


def prepare(family, output, potrace):
    version = subprocess.run([potrace, '--version'], check=True, capture_output=True, text=True).stdout
    if not version.startswith('potrace 1.16.'):
        raise ValueError('Source preparation requires Potrace 1.16.')
    manifest = json.loads((family/'source/tracing.json').read_text())
    images, drawings = {}, {}
    for ch, entry in manifest['glyphs'].items():
        file = family/entry['file']
        if file not in images:
            images[file] = Image.open(file).convert('L')
        drawings[ch] = trace(images[file], entry, potrace)
    companions = json.loads((family/'source/companions.json').read_text())
    for ch, entry in companions['glyphs'].items():
        if 'from' in entry:
            base = drawings[entry['from']]
            pen = SVGPathPen(None)
            parse_path(base['path'], TransformPen(RoundingPen(pen), entry.get('transform', [1,0,0,1,0,0])))
            drawings[ch] = {'path': pen.getCommands()+entry.get('append', ''),
                            'advance_width': entry.get('advance_width', base['advance_width'])}
        else:
            drawings[ch] = entry
    features_path = family/'source/features.fea'
    features = features_path.read_text() if features_path.exists() else ''
    assemble(family, drawings, companions['aliases'], output, features)
    # The audit JSON is disposable output, not a second authoritative master.
    fontrevival.write_json(output.with_suffix('.paths.json'), drawings)
    print(f'Prepared {output}; import it with scripts/fontrevival.py import {family.name} {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('id')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--potrace', default='potrace')
    args = parser.parse_args()
    prepare(fontrevival.family_dir(args.id), args.output, args.potrace)


if __name__ == '__main__':
    main()
