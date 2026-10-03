"""Review compatible font exports against a retained previous TrueType font."""
import argparse
import json
import math
import sys
from pathlib import Path

from fontTools.pens.reportLabPen import ReportLabPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'scripts/fontrevival.py').exists())
sys.path.insert(0, str(ROOT / 'scripts'))
from outline_raster import rasterize


class ClosedOutlinePen(ReportLabPen):
    def _closePath(self):
        self.path.close()


def compare(family, before, review_dir):
    m = json.loads((family / 'font.json').read_text())
    recipe = json.loads((family / 'source/tracing.json').read_text())
    after = family / 'fonts' / (m['postscript_name'] + '.ttf')
    fonts = [TTFont(file) for file in (before, after)]
    sets = [font.getGlyphSet() for font in fonts]
    assert fonts[0].getBestCmap() == fonts[1].getBestCmap()
    assert fonts[0].getGlyphOrder() == fonts[1].getGlyphOrder()
    assert {n: v[0] for n, v in fonts[0]['hmtx'].metrics.items()} == {
        n: v[0] for n, v in fonts[1]['hmtx'].metrics.items()}
    review_dir.mkdir(parents=True, exist_ok=True)
    output = family / 'specimens/font-compatibility-review.pdf'
    pdf = canvas.Canvas(str(output), pagesize=(1000, 900), invariant=1)
    pdf.setTitle(m['name'] + ' | Font renderer compatibility review')
    pdf.setAuthor('Harold Lehmann')
    upm, ascent = fonts[1]['head'].unitsPerEm, fonts[1]['hhea'].ascent
    rows = []
    for icon in m['icons']:
        name = icon['glyph']
        paths = []
        for glyphs in sets:
            pen = SVGPathPen(glyphs)
            glyphs[name].draw(pen)
            paths.append(pen.getCommands())
        if paths[0] == paths[1]:
            continue
        counts = [len(font['glyf'][name].coordinates) for font in fonts]
        rows.append({'id': icon['id'], 'glyph': name, 'points_before': counts[0],
                     'points_after': counts[1], 'advance': fonts[1]['hmtx'][name][0]})
        pdf.setFont('Helvetica', 18)
        pdf.drawString(36, 868, icon['name'] + ' / No. ' + icon['specimen_number'])
        pdf.setFont('Helvetica', 10)
        pdf.drawString(36, 846, icon['id'] + ' / Full-detail historical artwork unchanged')
        pdf.drawString(36, 822, f'Previous font: {counts[0]:,} quadratic points')
        pdf.drawString(536, 822, f'Compatible font: {counts[1]:,} quadratic points')
        for index, glyphs in enumerate(sets):
            form = f'{name}-{index}'
            pdf.beginForm(form, 0, fonts[1]['hhea'].descent, rows[-1]['advance'], ascent)
            drawing = pdf.beginPath()
            glyphs[name].draw(ClosedOutlinePen(glyphs, drawing))
            pdf.drawPath(drawing, stroke=0, fill=1, fillMode=1)
            pdf.endForm()
            for size, baseline in [(384, 420), (192, 210), (96, 98), (48, 40)]:
                pdf.saveState()
                pdf.translate(36 + index * 500, baseline)
                pdf.scale(size / upm, size / upm)
                pdf.doForm(form)
                pdf.restoreState()
                pdf.setFont('Helvetica', 9)
                pdf.drawString(440 + index * 500, baseline, f'{size} pt')
        pdf.showPage()
        # A source/previous/compatible raster sheet supports visual review even
        # when the old glyph is rejected by the installed font renderer.
        sheet = Image.new('RGB', (1320, 500), 'white')
        draw = ImageDraw.Draw(sheet)
        label = ImageFont.load_default(size=17)
        draw.text((16, 12), icon['id'] + ' / ' + icon['name'], font=label, fill='black')
        entry = recipe['glyphs'][chr(int(icon['codepoint'], 16))]
        with Image.open(family / entry['file']) as scan:
            crop = scan.crop(entry['box'])
        if entry.get('rotation'):
            crop = crop.rotate(entry['rotation'], expand=True)
        crop.thumbnail((400, 384))
        sheet.paste(crop.convert('RGB'), (16, 84))
        draw.text((16, 54), 'Historical scan', font=label, fill='black')
        for index, path in enumerate(paths):
            mask = rasterize(path, math.ceil(rows[-1]['advance'] * 384 / upm),
                             384, 384 / upm, (0, ascent * 384 / upm))
            x = 448 + 432 * index
            draw.text((x, 54), ['Previous font', 'Compatible font'][index], font=label, fill='black')
            sheet.paste('black', (x, 84), mask)
        sheet.save(review_dir / (icon['id'] + '.png'))
    pdf.save()
    (review_dir / 'review.json').write_text(json.dumps(rows, indent=2) + '\n')
    print(f'Reviewed {len(rows)} changed font drawings: {output}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family')
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--review-dir', type=Path, required=True)
    args = parser.parse_args()
    compare(ROOT / 'collection' / args.family, args.before, args.review_dir)
