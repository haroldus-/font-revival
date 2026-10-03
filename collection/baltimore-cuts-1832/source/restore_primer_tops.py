"""Reproduce the 1.002 Primer top-boundary repairs as candidate glyph edits.

Run with the pinned source/requirements.txt and Potrace 1.16. This reads the
reviewed recipes and writes only to --output; normal builds use source/glyphs/.
"""
import argparse
import json
from pathlib import Path

from PIL import Image
import prepare

tracing = prepare.tracing
FAMILY = Path(__file__).resolve().parent.parent
NOTES = ('Restored the observed top frame and adjoining detail from PDF page 209. '
         'Original scan-to-font transform, advance and reviewed rotation retained; '
         'see primer-top-review.json.')


def restore(output, potrace):
    tracing.require_potrace(potrace)
    metadata = json.loads((FAMILY / 'font.json').read_text())
    recipes = json.loads((FAMILY / 'source/tracing.json').read_text())['glyphs']
    audit = json.loads((FAMILY / 'source/primer-top-review.json').read_text())
    icons = {icon['id']: icon for icon in metadata['icons']}
    for row in audit['icons']:
        icon = icons[row['id']]
        entry = recipes[chr(int(icon['codepoint'], 16))]
        frame = entry | {'threshold': entry['frame_threshold']}
        with Image.open(FAMILY / entry['file']) as image:
            reference = tracing.trace_mask(tracing.clean_crop(image, frame), frame, potrace)
        transform, advance = tracing.trace_transform(reference, entry)
        if advance != row['advance_width'] or any(
                abs(a - b) > 1e-10 for a, b in zip(transform, row['source_to_font'])):
            raise ValueError(f'{icon["id"]}: the original coordinate frame changed.')
        drawings = tracing.prepare_entry((str(FAMILY / entry['file']), entry,
                     icon['multitone_layers'], '', None, potrace, icon['id']))
        for name, drawing in ({icon['glyph']: drawings['solid']} | drawings['tones']).items():
            tracing.fontrevival.write_json(output / f'{name}.json',
                                           drawing | {'glyph': name, 'notes': NOTES})
        prepare.cached.clear()
        prepare.papers.clear()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--potrace', default='potrace')
    args = parser.parse_args()
    restore(args.output, args.potrace)
