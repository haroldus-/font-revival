"""Record source proportions and measured bounds of reviewed font approximations."""
import argparse
import json
from pathlib import Path
from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'scripts/fontrevival.py').exists())

def record(family, source):
    metadata = json.loads((family / 'font.json').read_text())
    font = TTFont(source)
    glyphs = font.getGlyphSet()
    rules = [{'characters': ' ', 'ink_width': [0, 0], 'ink_height': [0, 0],
              'advance_width': [512, 512], 'notes': 'New blank quarter-em composition space.'}]
    for icon in metadata['icons']:
        name = icon['glyph']
        pen = BoundsPen(glyphs)
        glyphs[name].draw(pen)
        bounds = [pen.bounds]
        visible = BoundsPen(glyphs, ignoreSinglePoints=True)
        glyphs[name].draw(visible)
        isolated_points = visible.bounds != pen.bounds
        if isolated_points:
            bounds.append(visible.bounds)
        file = family / 'source/truetype-glyphs' / (name + '.json')
        if file.exists():
            pen = BoundsPen(None)
            parse_path(json.loads(file.read_text())['path'], pen)
            bounds.append(pen.bounds)
        values = [{'y_min': y0, 'y_max': y1, 'ink_width': x1-x0, 'ink_height': y1-y0}
                  for x0, y0, x1, y1 in bounds]
        rule = {'characters': chr(int(icon['codepoint'], 16)),
                'advance_width': [font['hmtx'][name][0]] * 2,
                'notes': icon['name'] + ': source aspect ratio, uniform scaling and original advance retained.'}
        for key in values[0]:
            rule[key] = [round(min(v[key] for v in values))-2, round(max(v[key] for v in values))+2]
        if file.exists():
            rule['notes'] += ' Range includes the explicitly reviewed font approximation and curve-conversion rounding.'
        if isolated_points:
            rule['notes'] += ' Range also includes omission of invisible isolated points during TrueType conversion.'
        rules.append(rule)
    profile = {'schema_version': 1, 'notes': 'Historical artwork fits an 1800-unit maximum dimension in a 2048-unit em; source proportions and 64-unit sidebearings are retained. Review ranges include the full master and measured font approximation, where present.', 'rules': rules}
    (family / 'source/sizing.json').write_text(json.dumps(profile, ensure_ascii=False, indent=2) + '\n')
    print(f'Recorded {len(rules)} sizing rules for {family.name}', flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family')
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    record(ROOT / 'collection' / args.family, args.source)
