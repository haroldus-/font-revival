"""Prepare reviewed downloadable-font approximations of oversized CFF engravings.

Run from the repository root with FAMILY [MASTER.otf] --potrace PATH. This optional
authoring step uses Cairo 1.18.0 and Potrace 1.16. Normal builds only read the
resulting editable JSON paths; the master and SVG keep the canonical CFF outlines.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont
from PIL import Image, ImageFilter

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'scripts/fontrevival.py').exists())
sys.path.insert(0, str(ROOT / 'scripts'))
import trace_specimen as tracing
import fontrevival
from outline_raster import rasterize


def outline_counts(svg):
    pen = TTGlyphPen(None)
    parse_path(svg, Cu2QuPen(pen, .5, reverse_direction=True))
    glyph = pen.glyph()
    return len(glyph.coordinates), glyph.numberOfContours


def compact_path(svg):
    """Store binary-exact 1/64-unit coordinates, below conversion error."""
    pen = SVGPathPen(None, ntos=lambda value: f'{round(value * 64) / 64:.6f}'.rstrip('0').rstrip('.') if round(value * 64) else '0')
    parse_path(svg, pen)
    return pen.getCommands()


def prepare(family, source, potrace, names=None):
    tracing.require_potrace(potrace)
    folder = family / 'source/truetype-glyphs'
    folder.mkdir(exist_ok=True)
    if source:
        font = TTFont(source, recalcTimestamp=False)
    else:
        fontrevival.metadata(family)
        font = TTFont(recalcTimestamp=False)
        font.importXML(family / 'source/font.ttx')
        selected = set(names) if names else set(font.getBestCmap().values()) | {'.notdef'}
        # Preparation only reads outlines and frame metrics. Name/version and
        # global clipping normalization belong to the subsequent release build.
        fontrevival.apply_glyphs(font, family / 'source/glyphs', names=selected)
    glyphs = font.getGlyphSet()
    order = font.getGlyphOrder()
    upm, ascent = font['head'].unitsPerEm, font['hhea'].ascent
    settings_file = family / 'source/truetype-settings.json'
    settings = json.loads(settings_file.read_text()) if settings_file.exists() else {}
    encoded = set(font.getBestCmap().values()) | {'.notdef'}
    if names and set(names) - encoded:
        raise ValueError('Selected glyphs must be encoded monochrome drawings.')
    for index, name in enumerate(order):
        if name not in encoded or names and name not in names:
            continue
        svg = SVGPathPen(glyphs); glyphs[name].draw(svg)
        original = svg.getCommands()
        fingerprint = hashlib.sha256(original.encode()).hexdigest()
        method = settings.get('methods', {}).get(name, 'binary-threshold')
        output = folder / (name + '.json')
        if output.exists():
            cached = json.loads(output.read_text())
            if (cached.get('master_sha256') == fingerprint
                    and cached.get('approximation_method', 'binary-threshold') == method):
                if cached.get('coordinate_precision') != 1 / 64:
                    cached['path'] = compact_path(cached['path'])
                    cached['coordinate_precision'] = 1 / 64
                    cached['approximate_quadratic_points'], cached['approximate_contours'] = outline_counts(cached['path'])
                    fontrevival.write_json(output, cached)
                if (cached.get('approximate_contours', 65535) <= 4000
                        and outline_counts(cached['path'])[0] <= fontrevival.MAX_TRUETYPE_POINTS
                        and fontrevival.cff_point_count(cached['path']) <= fontrevival.MAX_RENDERER_POINTS):
                    continue
        count, contours = outline_counts(original)
        cubic_count = fontrevival.cff_point_count(original)
        if count <= fontrevival.MAX_TRUETYPE_POINTS and contours < 4095 and cubic_count <= fontrevival.MAX_RENDERER_POINTS:
            continue
        print('Preparing', name, count, 'points', flush=True)
        bounds = BoundsPen(None); parse_path(original, bounds)
        advance = font['hmtx'][name][0]
        candidates = ([(1536, 4, 1.2), (1536, 6, 1.6), (1536, 8, 2), (1536, 10, 2.5),
                       (1280, 8, 2), (1024, 8, 2), (896, 8, 2), (768, 8, 2),
                       (640, 8, 2), (512, 8, 2)] if method == 'coverage-screen' else
                      [(size, None, None) for size in (1536, 1280, 1024, 896, 768, 640, 512, 448, 384, 320, 256)])
        for size, period, blur in candidates:
            scale, padding = size / upm, 8
            mask = rasterize(original, math.ceil(advance * scale) + 2 * padding,
                             size + 2 * padding, scale, (padding, padding + ascent * scale))
            if method == 'coverage-screen':
                import numpy as np
                alpha = np.asarray(mask.filter(ImageFilter.GaussianBlur(blur)))
                y, x = np.indices(alpha.shape)
                threshold = (((x + y) % period) + .5) * 255 / period
                mask = Image.fromarray(np.where(alpha >= threshold, 0, 255).astype(np.uint8))
            else:
                mask = mask.point(lambda v: 0 if v >= 128 else 255)
            rec = tracing.trace_mask(mask, {'tolerance': .35}, potrace)
            path = SVGPathPen(None)
            rec.replay(TransformPen(path, (1 / (10 * scale), 0, 0, 1 / (10 * scale),
                                          -padding / scale, ascent - upm - padding / scale)))
            drawing = compact_path(path.getCommands())
            reduced, reduced_contours = outline_counts(drawing)
            reduced_cubic = fontrevival.cff_point_count(drawing)
            if reduced <= 32000 and reduced_contours <= 4000 and reduced_cubic <= 32000:
                measured = BoundsPen(None); parse_path(drawing, measured)
                delta = math.ceil(max(abs(a - b) for a, b in zip(bounds.bounds, measured.bounds))) + 2
                if delta > 64:
                    raise ValueError(f'{name}: approximation lost its frame ({delta} units)')
                item = {'glyph': name, 'advance_width': advance, 'path': drawing,
                        'master_sha256': fingerprint, 'max_bound_delta': delta,
                        'original_quadratic_points': count, 'approximate_quadratic_points': reduced,
                        'original_cubic_points': cubic_count, 'approximate_cubic_points': reduced_cubic,
                        'original_contours': contours, 'approximate_contours': reduced_contours,
                        'raster_em_pixels': size, 'coordinate_precision': 1 / 64,
                        'approximation_method': method,
                        'notes': 'downloadable-font approximation of an oversized CFF outline. '
                                 'Rasterized from the canonical glyph at the recorded em size, '
                                 'threshold 128, then Potrace 1.16 tolerance 0.35; original frame and advance retained. '
                                 'Full-detail master and SVG are unchanged; all downloadable fonts use this reviewed drawing. See format comparison proof.'}
                if method == 'coverage-screen':
                    item.update({'screen_period_pixels': period, 'coverage_blur_pixels': blur})
                    item['notes'] = ('downloadable-font coverage-preserving approximation of a dense engraving. '
                                     'Cairo coverage at the recorded em size is blurred by the recorded radius, '
                                     'then screened diagonally with thresholds (((x+y) % period)+0.5)*255/period. '
                                     'Potrace 1.16 tolerance 0.35 and 1/64-unit coordinates retain the original frame and advance. '
                                     'Screening is a modern font-format interpretation, not historical engraved linework. '
                                     'Full-detail master and SVG remain unchanged; all downloadable fonts use this reviewed drawing; see the display-size comparison proof.')
                fontrevival.write_json(output, item)
                print(name, count, '->', reduced, 'points;', size, 'pixels/em', flush=True)
                break
        else:
            raise ValueError(f'{name}: cannot fit CFF/TrueType limits at the reviewed resolutions')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family'); parser.add_argument('source', type=Path, nargs='?',
                        help='Optional prepared OTF; otherwise use the current editable master and glyph edits')
    parser.add_argument('--potrace', default='potrace')
    parser.add_argument('--glyph', nargs='+', help='Prepare only these encoded glyph names')
    args = parser.parse_args()
    prepare(ROOT / 'collection' / args.family, args.source, args.potrace, args.glyph)
