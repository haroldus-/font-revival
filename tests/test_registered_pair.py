"""Cross-family contracts needed for registered overprinting."""
import unittest
from pathlib import Path
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]


def pairs(font):
    return {(left, r.SecondGlyph): r.Value1.XAdvance
            for lookup in font['GPOS'].table.LookupList.Lookup
            for table in lookup.SubTable
            for left, pairset in zip(table.Coverage.glyphs, table.PairSet)
            for r in pairset.PairValueRecord}


class RegisteredPairTests(unittest.TestCase):
    def test_every_format_keeps_the_same_registration(self):
        for folder, ext in [('fonts', 'otf'), ('fonts', 'ttf'), ('web', 'woff'), ('web', 'woff2')]:
            with self.subTest(format=ext), TTFont(ROOT / f'collection/erebus-1894/{folder}/Erebus1894-Regular.{ext}') as solid, TTFont(ROOT / f'collection/hades-1894/{folder}/Hades1894-Regular.{ext}') as shadow:
                self.assertEqual(solid.getBestCmap(), shadow.getBestCmap())
                self.assertEqual({g: w for g, (w, _) in solid['hmtx'].metrics.items()},
                                 {g: w for g, (w, _) in shadow['hmtx'].metrics.items()})
                self.assertEqual(pairs(solid), pairs(shadow))
                self.assertEqual(solid['head'].unitsPerEm, shadow['head'].unitsPerEm)
                self.assertEqual(solid['hhea'].ascent, shadow['hhea'].ascent)
                self.assertEqual(solid['hhea'].descent, shadow['hhea'].descent)
                self.assertEqual(solid['OS/2'].usWinAscent, shadow['OS/2'].usWinAscent)
                self.assertEqual(solid['OS/2'].usWinDescent, shadow['OS/2'].usWinDescent)
