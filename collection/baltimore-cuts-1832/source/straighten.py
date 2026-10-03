"""Apply the reviewed rotation plan once, retaining every contour and tone.

Usage from the repository root:
  python collection/baltimore-cuts-1832/source/straighten.py PLAN.json BACKUP_DIR

Normal builds read the resulting glyph overrides. The tracing recipe also keeps
these matrices, after its caption cleanup. BACKUP_DIR must not already exist;
this prevents accidental cumulative rotations. The saved canonical drawings and
font binaries make the before/after proofs independently reproducible.
"""
import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.svgLib.path import parse_path

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'scripts/fontrevival.py').exists())
sys.path.insert(0, str(ROOT/'scripts'))
import fontrevival as f
from trace_specimen import transform_drawing
from prepare_truetype import outline_counts


def signature(path):
    return hashlib.sha256(path.encode()).hexdigest()


def info(path):
    pen = RecordingPen(); parse_path(path, pen)
    bounds = BoundsPen(None); pen.replay(bounds)
    return {'sha256': signature(path), 'contours': sum(op == 'moveTo' for op, _ in pen.value),
            'operations': len(pen.value), 'bounds': list(bounds.bounds)}


def drawing(font, name):
    glyphs = font.getGlyphSet(); pen = SVGPathPen(glyphs); glyphs[name].draw(pen)
    return {'glyph': name, 'advance_width': font['hmtx'][name][0], 'path': pen.getCommands(),
            'preserve_commands': True, 'preserve_coordinates': True}


def apply(plan_file, backup, family=None):
    family = family or Path(__file__).resolve().parent.parent
    audit = json.loads(plan_file.read_text())
    if (family/'source/straightening.json').exists():
        raise ValueError('Straightening is already recorded; do not rotate a second time.')
    backup.mkdir(parents=True, exist_ok=False)
    for folder in ('fonts', 'web', 'source/truetype-glyphs'):
        if folder == 'web':
            (backup/folder).mkdir()
            for file in (family/folder).glob('*.woff*'): shutil.copy2(file, backup/folder/file.name)
        elif (family/folder).exists(): shutil.copytree(family/folder, backup/folder)
    for file in ('font.json', 'source/tracing.json', 'source/sizing.json'):
        (backup/file).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(family/file, backup/file)
    m = f.metadata(family); recipes = json.loads((family/'source/tracing.json').read_text())
    icons = {i['id']: i for i in m['icons']}
    font = f.load_source(family, m, encoded_only=True)
    top = font['CFF '].cff.topDictIndex[0]
    for row in audit['icons']:
        if row['status'] != 'rotate': continue
        icon = icons[row['id']]; name = icon['glyph']; width = font['hmtx'][name][0]
        angle = math.radians(row['angle_degrees']); c, s = math.cos(angle), math.sin(angle)
        cx, cy = width/2, 900
        matrix = [c, s, -s, c, cx-c*cx+s*cy, cy-s*cx-c*cy]
        row.update(pivot=[cx, cy], matrix=matrix, coordinate_grid=1/64, drawings={})
        names = [name, *(layer['glyph'] for layer in icon['multitone_layers'])]
        f.apply_glyphs(font, family/'source/glyphs', names=set(names[1:]))
        for glyph in names:
            before = drawing(font, glyph)
            f.write_json(backup/'source/glyphs'/f'{glyph}.json', before)
            after = transform_drawing(before, matrix)
            after['notes'] = (f"Full-detail drawing rotated {row['angle_degrees']:+.3f} degrees about ({cx}, {cy}) "
                              f"using the reviewed {row['reference']}. Every contour and the original advance are retained; "
                              "the same matrix applies to all tones. See straightening.json; caption cleanup precedes rotation.")
            a, b = info(before['path']), info(after['path'])
            assert a['contours'] == b['contours'], glyph
            assert 0 <= b['bounds'][0] < b['bounds'][2] <= width, (glyph, b['bounds'])
            assert -148 <= b['bounds'][1] < b['bounds'][3] <= 1900, (glyph, b['bounds'])
            row['drawings'][glyph] = {'before': a, 'after': b}
            f.write_json(family/'source/glyphs'/f'{glyph}.json', after)
        f.apply_glyphs(font, family/'source/glyphs', names={name})
        actual = drawing(font, name)
        approximation_file = family/'source/truetype-glyphs'/f'{name}.json'
        if approximation_file.exists():
            before = json.loads(approximation_file.read_text())
            assert before['master_sha256'] == row['drawings'][name]['before']['sha256'], name
            after = transform_drawing(before, matrix)
            after['master_sha256'] = signature(actual['path'])
            after['original_quadratic_points'], after['original_contours'] = outline_counts(actual['path'])
            after['original_cubic_points'] = f.cff_point_count(actual['path'])
            after['approximate_quadratic_points'], after['approximate_contours'] = outline_counts(after['path'])
            after['approximate_cubic_points'] = f.cff_point_count(after['path'])
            assert max(after['approximate_quadratic_points'], after['approximate_cubic_points']) <= 65535
            assert after['approximate_contours'] < 4095
            delta = max(abs(a-b) for a,b in zip(info(actual['path'])['bounds'], info(after['path'])['bounds']))
            after['max_bound_delta'] = max(after['max_bound_delta'], math.ceil(delta)+2)
            after['notes'] += ' Rotated with the complete master and all tone layers; see straightening.json.'
            row['font_approximation'] = {'before': info(before['path']), 'after': info(after['path'])}
            f.write_json(approximation_file, after)
        recipe = recipes['glyphs'][chr(int(icon['codepoint'],16))]
        recipe['post_trace_transform'] = matrix
        recipe['straightening_note'] = f"{row['angle_degrees']:+.3f} degrees; {row['reference']}; see straightening.json."
        # Release the large private layer programs while retaining their named slots.
        for glyph in names[1:]:
            from fontTools.pens.t2CharStringPen import T2CharStringPen
            top.CharStrings[glyph] = T2CharStringPen(width, None).getCharString(private=top.Private, globalSubrs=top.GlobalSubrs)
        print(row['specimen_number'], row['angle_degrees'], flush=True)
    f.truetype_approximations(family, font)
    font.save(backup.parent/'after-full-encoded.otf')
    f.write_json(family/'source/tracing.json', recipes)
    f.write_json(family/'source/straightening.json', audit)
    print('Applied', sum(r['status']=='rotate' for r in audit['icons']), 'reviewed rotations.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path); parser.add_argument('backup', type=Path)
    parser.add_argument('--family', type=Path, help='Another Baltimore family using the same canonical workflow.')
    args = parser.parse_args(); apply(args.plan, args.backup, args.family)
