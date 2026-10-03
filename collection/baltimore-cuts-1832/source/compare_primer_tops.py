"""Compare the retained 1.001 glyph exports with the restored Primer panels."""
import argparse
import json
import math
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'scripts/fontrevival.py').exists())
sys.path.insert(0, str(ROOT / 'scripts'))
from outline_raster import rasterize

FAMILY = Path(__file__).resolve().parent.parent


def load(folder, name):
    return json.loads((folder / f'{name}.json').read_text())


def tonal(drawings, layers, bounds):
    x0, y0, x1, y1 = bounds
    scale = min(520 / (x1 - x0), 310 / (y1 - y0))
    origin = (20 - x0 * scale, 20 + y1 * scale)
    image = Image.new('RGB', (560, 350), 'white')
    for layer in layers:
        mask = rasterize(drawings[layer['glyph']]['path'], 560, 350, scale, origin)
        mask = mask.point(lambda value: round(value * layer['opacity']))
        image.paste('black', (0, 0), mask)
    return image


def monochrome(drawing, size):
    width = math.ceil(drawing['advance_width'] * size / 2048)
    mask = rasterize(drawing['path'], width, size, size / 2048, (0, 1900 * size / 2048))
    image = Image.new('RGB', mask.size, 'white')
    image.paste('black', (0, 0), mask)
    return image


def proof(before, output):
    metadata = json.loads((FAMILY / 'font.json').read_text())
    audit = json.loads((FAMILY / 'source/primer-top-review.json').read_text())
    icons = {icon['id']: icon for icon in metadata['icons']}
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output), pagesize=(842, 595), invariant=1)
    pdf.setTitle('Baltimore Cuts 1832 | Primer upper-boundary restoration')
    pdf.setAuthor('Harold Lehmann')
    with Image.open(FAMILY / audit['source_file']) as scan:
        for row in audit['icons']:
            icon = icons[row['id']]
            names = [icon['glyph'], *(layer['glyph'] for layer in icon['multitone_layers'])]
            old = {name: load(before, name) for name in names}
            new = {name: load(FAMILY / 'source/glyphs', name) for name in names}
            bounds = BoundsPen(None)
            for drawings in (old, new):
                for drawing in drawings.values():
                    parse_path(drawing['path'], bounds)
            pdf.setFont('Helvetica', 18)
            pdf.drawString(36, 560, icon['name'] + ' / No. ' + icon['specimen_number'])
            pdf.setFont('Helvetica', 9)
            pdf.drawString(36, 540, 'Baltimore Type Foundry, 1832 / unnumbered leaf, PDF page 209 / versions 1.001 and 1.002')
            for x, label in [(36, 'Historical scan'), (300, 'Before / three tones'), (564, 'Restored / three tones')]:
                pdf.drawString(x, 510, label)
            crop = scan.crop(row['box'])
            factor = min(242 / crop.width, 180 / crop.height)
            pdf.drawImage(ImageReader(crop), 36, 475 - crop.height * factor,
                          width=crop.width * factor, height=crop.height * factor)
            for x, drawings in [(290, old), (554, new)]:
                image = tonal(drawings, icon['multitone_layers'], bounds.bounds)
                pdf.drawImage(ImageReader(image), x, 300, width=260, height=162.5)
            pdf.drawString(36, 280, 'Full observed upper rule and adjoining detail restored. Original scale, position, advance and rotation retained.')
            pdf.drawString(36, 263, 'Natural gaps in the printed rules remain. The lower boundary is unchanged; no border or illustration is newly drawn.')
            for x, size in [(36, 48), (183, 96), (430, 192)]:
                pdf.drawString(x, 230, f'{size} px / before, after')
                left = monochrome(old[icon['glyph']], size)
                right = monochrome(new[icon['glyph']], size)
                for offset, image in [(0, left), (left.width + 12, right)]:
                    pdf.drawImage(ImageReader(image), x + offset, 215 - size,
                                  width=image.width, height=image.height)
            pdf.showPage()
    pdf.save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True, help='Directory containing the retained previous glyph JSON exports')
    parser.add_argument('--output', type=Path, default=FAMILY / 'specimens/primer-top-review.pdf')
    args = parser.parse_args()
    proof(args.before, args.output)
