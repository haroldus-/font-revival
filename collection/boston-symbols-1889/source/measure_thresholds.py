"""Print candidate ink thresholds for review; never overwrite tracing.json.

Run with the repository's pinned Pillow dependency. Candidates use Otsu's
between-class variance after the same paper correction as trace_specimen.py.
The committed recipe includes visually reviewed overrides for fine detail.
"""
import json
from pathlib import Path

from PIL import Image, ImageFilter


def candidate_threshold(image):
    histogram = image.histogram()
    total = sum(histogram)
    total_sum = sum(value * count for value, count in enumerate(histogram))
    count_low = sum_low = 0
    best_variance, threshold = -1, 180
    for value, count in enumerate(histogram):
        count_low += count
        sum_low += value * count
        count_high = total - count_low
        if count_low and count_high:
            variance = count_low * count_high * (
                sum_low / count_low - (total_sum - sum_low) / count_high
            ) ** 2
            if variance > best_variance:
                best_variance, threshold = variance, value + 1
    return min(225, max(130, threshold))


if __name__ == '__main__':
    family = Path(__file__).resolve().parent.parent
    recipes = json.loads((family / 'source/tracing.json').read_text())['glyphs']
    icons = json.loads((family / 'font.json').read_text())['icons']
    images, candidates = {}, {}
    for icon in icons:
        entry = recipes[chr(int(icon['codepoint'], 16))]
        file = entry['file']
        if file not in images:
            images[file] = Image.open(family / file).convert('L')
        crop = images[file].crop(entry['box'])
        radius = entry['paper_normalization_radius']
        paper = crop.filter(ImageFilter.MaxFilter(2 * radius + 1)).filter(
            ImageFilter.GaussianBlur(radius / 3))
        normalized = Image.frombytes('L', crop.size, bytes(
            min(255, round(value * 255 / max(background, 1)))
            for value, background in zip(crop.tobytes(), paper.tobytes())))
        candidates[icon['id']] = candidate_threshold(normalized)
    print(json.dumps(candidates, indent=2))
