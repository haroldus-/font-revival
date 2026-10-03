#!/usr/bin/env python3
"""Reconstruct a documented initial master from historical crops and SVG drawings.

Optional source-preparation tool: Potrace 1.16 plus requirements.txt.
Normal release builds use source/font.ttx and do not run this script.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import math
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from fontTools.agl import UV2AGL
from fontTools.cffLib import PrivateDict
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

import fontrevival


def components(mask, value):
    """Four-connected pixel components; crops are small, no numerical stack needed."""
    pixels = mask.load()
    unseen = {(x, y) for y in range(mask.height) for x in range(mask.width)
              if pixels[x, y] == value}
    result = []
    # Column-major seeds preserve the old min(unseen) order without repeatedly
    # scanning the whole set on engravings with thousands of detached marks.
    for seed in ((x, y) for x in range(mask.width) for y in range(mask.height)):
        if seed not in unseen:
            continue
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
    rotation = entry.get('rotation', 0)
    if rotation not in (0, 90, 180, 270):
        raise ValueError('Crop rotation must be a counterclockwise quarter turn.')
    if rotation:
        crop = crop.rotate(rotation, expand=True)
    # Optional illumination correction for weak impressions on uneven paper.
    # Estimate the paper locally without adding or closing engraved strokes.
    radius = entry.get('paper_normalization_radius', 0)
    if radius:
        paper = crop.filter(ImageFilter.MaxFilter(2 * radius + 1)).filter(
            ImageFilter.GaussianBlur(radius / 3))
        crop = Image.frombytes('L', crop.size, bytes(
            min(255, round(value * 255 / max(background, 1)))
            for value, background in zip(crop.tobytes(), paper.tobytes())))
    draw = ImageDraw.Draw(crop)
    for rectangle in entry.get('erase', []):
        draw.rectangle(rectangle, fill=255)
    crop = ImageOps.expand(crop, border=4, fill=255)
    crop = crop.filter(ImageFilter.GaussianBlur(entry.get('blur', 0.55)))
    mask = crop.point(lambda p: 0 if p < entry.get('threshold', 135) else 255)
    erosion = entry.get('ink_erosion', 0)
    if erosion:
        mask = mask.filter(ImageFilter.MaxFilter(2 * erosion + 1))
    ink = components(mask, 0)
    if not ink:
        raise ValueError('No ink in crop: ' + str(entry['box']))
    # The default preserves earlier connected-letter recipes. Dots, ornamental
    # islands and Hades's broken outlines need explicitly retained components.
    if 'component_min_area' in entry:
        selected = [part for part in ink if len(part) >= entry['component_min_area']]
    else:
        selected = sorted(ink, key=len, reverse=True)[:entry.get('keep_components', 1)]
    if not selected:
        raise ValueError('No components survive crop cleanup: ' + str(entry['box']))
    clean = Image.new('L', mask.size, 255)
    for part in selected:
        for point in part:
            clean.putpixel(point, 0)
    hole_limit = entry.get('fill_holes', 8)
    if hole_limit:
        for component in components(clean, 255):
            if len(component) <= hole_limit:
                for point in component:
                    clean.putpixel(point, 0)
    return clean


def trace_mask(mask, entry, potrace):
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
    return rec


def trace_transform(rec, entry):
    bounds = BoundsPen(None)
    rec.replay(bounds)
    x0, y0, x1, y1 = bounds.bounds
    scale = entry['height'] / (y1-y0)
    if 'max_ink_dimension' in entry:
        scale = min(scale, entry['max_ink_dimension'] / max(x1-x0, y1-y0))
    left, right = entry.get('bearings', [45, 45])
    sx = (entry['ink_width'] / (x1-x0) if 'ink_width' in entry
          else scale * entry.get('width_scale', 1))
    advance = entry.get('advance_width', round((x1-x0)*sx+left+right))
    if entry.get('center', False):
        left = (advance - (x1-x0)*sx) / 2
    baseline = entry.get('y_min', 0)
    if entry.get('center_vertical', False):
        baseline += (entry['height'] - (y1-y0)*scale) / 2
    return (sx, 0, 0, scale, left-x0*sx, baseline-y0*scale), advance


def trace(image, entry, potrace):
    rec = trace_mask(clean_crop(image, entry), entry, potrace)
    reference = rec
    if 'frame_threshold' in entry:
        frame = entry | {'threshold': entry['frame_threshold'],
                         'erase': entry.get('erase', []) + entry.get('multitone', {}).get('erase', [])}
        reference = trace_mask(clean_crop(image, frame), frame, potrace)
    transform, advance = trace_transform(reference, entry)
    out = SVGPathPen(None)
    rec.replay(TransformPen(RoundingPen(out), transform))
    return {'path': out.getCommands(), 'advance_width': advance}


def trace_tones(image, entry, layers, potrace):
    """Make two or three disjoint tone regions in the solid drawing's frame."""
    from outline_geometry import _path, _svg, boolean_op
    import pathops

    frame = entry
    if 'frame_threshold' in entry:
        frame = entry | {'threshold': entry['frame_threshold'],
                         'erase': entry.get('erase', []) + entry['multitone'].get('erase', [])}
    reference = trace_mask(clean_crop(image, frame), frame, potrace)
    transform, advance = trace_transform(reference, entry)
    settings = entry['multitone']
    if settings.get('separation') == 'native-mask-bands':
        # A documented fallback for an engraving whose vector intersection
        # graph cannot be resolved in practical time. Keep every native pixel;
        # separate the nested masks before fitting the same Potrace curves.
        covered = None
        drawings = {}
        for layer in layers:
            tonal = entry | {'threshold': settings['thresholds'][layer['role']],
                             'erase': entry.get('erase', []) + settings.get('erase', [])}
            mask = clean_crop(image, tonal)
            band = mask if covered is None else ImageChops.lighter(mask, ImageOps.invert(covered))
            covered = mask if covered is None else ImageChops.darker(covered, mask)
            rec = trace_mask(band, tonal, potrace)
            out = SVGPathPen(None)
            rec.replay(TransformPen(RoundingPen(out), transform))
            drawings[layer['glyph']] = {'path': out.getCommands(), 'advance_width': advance}
        return drawings

    traced = []
    for layer in layers:
        threshold = settings['thresholds'][layer['role']]
        tonal = entry | {'threshold': threshold, 'erase': entry.get('erase', []) + settings.get('erase', [])}
        rec = trace_mask(clean_crop(image, tonal), tonal, potrace)
        traced.append((layer, rec))


    def separate(round_inputs, quadratic=False):
        drawings, covered = {}, pathops.Path()
        for layer, rec in traced:
            out = SVGPathPen(None)
            rec.replay(TransformPen(RoundingPen(out) if round_inputs else out, transform))
            shape = _path(out.getCommands())
            if quadratic:
                converted = pathops.Path()
                shape.draw(Cu2QuPen(converted.getPen(), .05, reverse_direction=False))
                shape = converted
            region = boolean_op(shape, covered, pathops.PathOp.DIFFERENCE)
            drawings[layer['glyph']] = {'path': _svg(region), 'advance_width': advance}
            covered = boolean_op(covered, shape, pathops.PathOp.UNION)
        return drawings

    initial_rounding = settings.get('round_inputs', True)
    if type(initial_rounding) is not bool:
        raise ValueError('multitone.round_inputs must be boolean.')
    try:
        return separate(round_inputs=initial_rounding)
    except ValueError:
        # Integer rounding can create artificial tangencies before subtraction.
        # Retry with the original fitted curves, rounding only the final regions.
        # Existing successful traces, including the pilot, stay unchanged.
        try:
            return separate(round_inputs=not initial_rounding)
        except ValueError:
            # A final vector-only fallback avoids unstable cubic intersections.
            # Its 0.05-unit curve error is ten times finer than release TTFs.
            return separate(round_inputs=True, quadratic=True)


def glyph_name(character):
    return UV2AGL.get(ord(character), f'uni{ord(character):04X}')


def assemble(family, drawings, aliases, output, features='', metrics=None, extra_drawings=None):
    """Make a complete static CFF OTF for the standard import command."""
    m = fontrevival.metadata(family)
    settings = metrics or {}
    cmap = {ord(ch): glyph_name(ch) for ch in drawings}
    for ch, target in aliases.items():
        cmap[ord(ch)] = glyph_name(target)
    missing = set(range(32, 127)) - cmap.keys()
    if missing and m.get('kind') != 'icons':
        raise ValueError('Missing Basic Latin: ' + ''.join(chr(cp) for cp in sorted(missing)))
    fixed_width = None
    if settings.get('monospaced'):
        widths = {data['advance_width'] for data in drawings.values()}
        if len(widths) != 1:
            raise ValueError('Monospaced drawings must have one advance width.')
        fixed_width = widths.pop()
    notdef = {'advance_width': fixed_width if fixed_width is not None else 600,
              'path': 'M60 0H540V700H60Z M100 40V660H500V40Z'}
    named = {'.notdef': notdef} | {glyph_name(ch): data for ch, data in drawings.items()}
    for name, data in (extra_drawings or {}).items():
        if name in named:
            raise ValueError('Duplicate tonal glyph: ' + name)
        named[name] = data
    order = list(named)
    charstrings, metrics = {}, {}
    for name, data in named.items():
        pen = T2CharStringPen(data['advance_width'], None,
                             roundTolerance=0 if data.get('preserve_coordinates') else 0.5)
        parse_path(data['path'], pen)
        charstrings[name] = pen.getCharString(optimize=not data.get('preserve_commands', False))
        bounds = BoundsPen(None)
        parse_path(data['path'], bounds)
        metrics[name] = (data['advance_width'], round(bounds.bounds[0]) if bounds.bounds else 0)
    fb = FontBuilder(settings.get('units_per_em', 1000), isTTF=False)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupCFF(m['postscript_name'], {'FullName': m['name'], 'FamilyName': m['name'], 'Weight': 'Regular'}, charstrings, {})
    fb.setupHorizontalMetrics(metrics)
    ascent = settings.get('ascent', 850)
    descent = settings.get('descent', -200)
    line_gap = settings.get('line_gap', 100)
    fb.setupHorizontalHeader(ascent=ascent, descent=descent, lineGap=line_gap)
    fb.setupNameTable({'familyName': m['name'], 'styleName': 'Regular', 'psName': m['postscript_name']})
    fb.setupOS2(sTypoAscender=ascent, sTypoDescender=descent, sTypoLineGap=line_gap,
                usWinAscent=settings.get('win_ascent', 900),
                usWinDescent=settings.get('win_descent', 220),
                sxHeight=settings.get('x_height', 700), sCapHeight=settings.get('cap_height', 700),
                usWeightClass=400, usWidthClass=5, fsType=0)
    fb.setupPost(isFixedPitch=int(settings.get('monospaced', False)))
    if settings.get('monospaced'):
        fb.font['CFF '].cff.topDictIndex[0].isFixedPitch = True
    if features:
        addOpenTypeFeaturesFromString(fb.font, features)
    fontrevival.normalize(fb.font, m)
    output.parent.mkdir(parents=True, exist_ok=True)
    fb.save(output)


def require_potrace(potrace):
    version = subprocess.run([potrace, '--version'], check=True, capture_output=True, text=True).stdout
    if not version.startswith('potrace 1.16.'):
        raise ValueError('Source preparation requires Potrace 1.16.')


_decoded_images = {}


def erase_disconnected_contours(svg, rectangles):
    """Remove isolated caption remnants within measured font-space rectangles."""
    from fontTools.pens.boundsPen import ControlBoundsPen
    recorded = RecordingPen()
    parse_path(svg, recorded)
    output, current, removed = SVGPathPen(None), RecordingPen(), 0
    for operation, points in recorded.value:
        getattr(current, operation)(*points)
        if operation not in ('closePath', 'endPath'):
            continue
        bounds = ControlBoundsPen(None)
        current.replay(bounds)
        box = bounds.bounds
        erase = box is not None and any(x0 <= box[0] and y0 <= box[1] and
                                       box[2] <= x1 and box[3] <= y1
                                       for x0, y0, x1, y1 in rectangles)
        if erase:
            removed += 1
        else:
            current.replay(output)
        current = RecordingPen()
    if current.value:
        current.replay(output)
    return output.getCommands(), removed


def transform_drawing(drawing, matrix):
    """Apply a reviewed post-trace affine on a binary-exact 1/64-unit grid.

    Whole contours, including isolated points, retain their order. Use the same
    matrix for the monochrome drawing and every tone to retain registration.
    """
    if (len(matrix) != 6 or any(not isinstance(v, (int, float)) or
                               not math.isfinite(v) for v in matrix)):
        raise ValueError('post_trace_transform requires six finite numbers.')
    pen = SVGPathPen(None)
    parse_path(drawing['path'], TransformPen(
        RoundingPen(pen, roundFunc=lambda v: round(v * 64) / 64), matrix))
    return drawing | {'path': pen.getCommands(), 'preserve_coordinates': True,
                      'preserve_commands': True}


def transform_traced_drawing(drawing, matrix):
    """Rotate the same canonical CFF geometry produced by the initial import.

    CFF specialization joins some collinear line segments before a revision.
    Reproduce that step before rotation; rounding an extra intermediate vertex
    after rotation could otherwise introduce a tiny bend absent from the master.
    """
    pen = T2CharStringPen(drawing['advance_width'], None)
    parse_path(drawing['path'], pen)
    canonical = SVGPathPen(None)
    pen.getCharString(private=PrivateDict()).draw(canonical)
    return transform_drawing(drawing | {'path': canonical.getCommands()}, matrix)


def prepare_entry(task):
    file, entry, layers, signature, cached, potrace, label = task
    if cached and cached.exists():
        return json.loads(cached.read_text())
    if file not in _decoded_images:
        _decoded_images[file] = Image.open(file).convert('L')
    image = _decoded_images[file]
    try:
        result = {'solid': trace(image, entry, potrace), 'tones': {}}
        if 'multitone' in entry:
            result['tones'] = trace_tones(image, entry, layers, potrace)
        if entry.get('post_trace_remove_contours'):
            for drawing in [result['solid'], *result['tones'].values()]:
                drawing['path'], _ = erase_disconnected_contours(drawing['path'], entry['post_trace_remove_contours'])
        if 'post_trace_transform' in entry:
            matrix = entry['post_trace_transform']
            result['solid'] = transform_traced_drawing(result['solid'], matrix)
            result['tones'] = {name: transform_traced_drawing(drawing, matrix)
                               for name, drawing in result['tones'].items()}
    except Exception as exc:
        raise ValueError(f'Tracing {label}: {exc}') from exc
    if cached:
        fontrevival.write_json(cached, result)
    return result


def prepare(family, output, potrace, cache=None, jobs=1):
    require_potrace(potrace)
    manifest = json.loads((family/'source/tracing.json').read_text())
    if manifest.get('mode') == 'glyph-revision':
        raise ValueError('Use trace_revisions.py for a glyph-revision recipe.')
    source_hashes, drawings, extra, tasks = {}, {}, {}, []
    tool_hash = hashlib.sha256(Path(__file__).read_bytes() + Path(__file__).with_name('outline_geometry.py').read_bytes()).hexdigest()
    if cache:
        cache.mkdir(parents=True, exist_ok=True)
    m = fontrevival.metadata(family)
    icon_map = {chr(int(i['codepoint'], 16)): i for i in m.get('icons', [])}
    for ch, entry in manifest['glyphs'].items():
        file = family/entry['file']
        if file not in source_hashes:
            source_hashes[file] = hashlib.sha256(file.read_bytes()).hexdigest()
        layers = icon_map.get(ch, {}).get('multitone_layers', [])
        signature = json.dumps([tool_hash, source_hashes[file], entry, layers], sort_keys=True)
        cached = cache / (hashlib.sha256(signature.encode()).hexdigest() + '.json') if cache else None
        tasks.append((file, entry, layers, signature, cached, potrace, icon_map.get(ch, {}).get('id', ch)))
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            results = list(pool.map(prepare_entry, tasks))
    else:
        results = list(map(prepare_entry, tasks))
    for ch, result in zip(manifest['glyphs'], results):
        drawings[ch] = result['solid']
        extra.update(result['tones'])
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
    assemble(family, drawings, companions['aliases'], output, features, manifest.get('font_metrics'), extra)
    # The audit JSON is disposable output, not a second authoritative master.
    fontrevival.write_json(output.with_suffix('.paths.json'), drawings)
    print(f'Prepared {output}; import it with scripts/fontrevival.py import {family.name} {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('id')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--potrace', default='potrace')
    parser.add_argument('--cache', type=Path, help='Optional disposable cache keyed by source, recipe and preparation code')
    parser.add_argument('--jobs', type=int, default=1, help='Independent preparation workers; output order remains deterministic')
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    prepare(fontrevival.family_dir(args.id), args.output, args.potrace, args.cache, args.jobs)


if __name__ == '__main__':
    main()
