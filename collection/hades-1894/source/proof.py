#!/usr/bin/env python3
"""Render the registered pair after both families have been built."""
import sys
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from fontrevival import register_pdf_font


def proof():
    families = [ROOT / 'collection' / name for name in ('erebus-1894', 'hades-1894')]
    files = [p / 'fonts' / f'{p.name.split("-")[0].title()}1894-Regular.ttf' for p in families]
    fonts = [TTFont(file) for file in files]
    assert fonts[0].getBestCmap() == fonts[1].getBestCmap()
    assert {g: w for g, (w, lsb) in fonts[0]['hmtx'].metrics.items()} == {g: w for g, (w, lsb) in fonts[1]['hmtx'].metrics.items()}
    def pairs(font):
        return {(left, r.SecondGlyph): r.Value1.XAdvance
                for lookup in font['GPOS'].table.LookupList.Lookup
                for table in lookup.SubTable
                for left, pairset in zip(table.Coverage.glyphs, table.PairSet)
                for r in pairset.PairValueRecord}
    assert pairs(fonts[0]) == pairs(fonts[1])
    for name, file in zip(('solid', 'shadow'), files):
        register_pdf_font(name, file)
    c = canvas.Canvas(str(families[1] / 'specimens/pairing.pdf'), pagesize=(842, 595), invariant=1)
    c.setTitle('Erebus 1894 + Hades 1894 | Registration proof')
    c.setAuthor('Font Revival contributors')
    c.setFont('Helvetica', 18)
    c.drawString(36, 555, 'Erebus + Hades / One origin, two colours')
    c.setFont('Helvetica', 10)
    c.drawString(36, 530, 'Identical advances and kerning. Shadow offset: -28, -28 font units; 1000 units per em.')
    for label, y, faces in [('Erebus', 414, [('solid', '#be7950')]),
                            ('Hades', 294, [('shadow', '#24251f')]),
                            ('Overprint', 174, [('solid', '#be7950'), ('shadow', '#24251f')])]:
        c.setFillColor(HexColor('#68675c'));c.setFont('Helvetica', 10);c.drawString(36, y+69, label)
        for face, colour in faces:
            c.setFillColor(HexColor(colour));c.setFont(face, 66);c.drawString(36, y, 'WALNUT GROVES 87')
    c.setFillColor(HexColor('#68675c'));c.setFont('Helvetica', 9)
    c.drawString(36, 114, 'Smaller overprint / 24 pt')
    for face, colour in [('solid', '#be7950'), ('shadow', '#24251f')]:
        c.setFillColor(HexColor(colour));c.setFont(face, 24)
        c.drawString(36, 78, 'BASKET HOLDER / BANK QUARTZ / 0123456789')
    c.save()


if __name__ == '__main__':
    proof()
