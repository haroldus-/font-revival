#!/usr/bin/env python3
"""One source and one build pipeline for every Font Revival family."""

from __future__ import annotations

import argparse
import copy
import hashlib
import html
import io
import json
import math
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from statistics import median

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as PDFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
EPOCH = 3850070400  # 2026-01-01 UTC in OpenType's 1904 epoch; fixed for builds.
COPYRIGHT_HOLDER = "Harold Lehmann"
COPYRIGHT_NOTICE = f"Copyright (c) 2026 {COPYRIGHT_HOLDER}"
PAPER, INK, ACCENT = "#f4f0e7", "#24251f", "#a5422c"
SLUG = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def family_dir(slug):
    if not SLUG.fullmatch(slug):
        raise ValueError("Use a lowercase family ID such as nero-1888.")
    path = ROOT / "collection" / slug
    if path.is_symlink():
        raise ValueError("Family directories must not be symbolic links.")
    return path


def families(slug=None):
    if slug:
        paths = [family_dir(slug)]
    else:
        paths = sorted((ROOT / "collection").glob("*"))
    paths = [p for p in paths if p.is_dir()]
    if not paths:
        raise ValueError("No font families found.")
    return paths


def metadata(path):
    m = json.loads((path / "font.json").read_text())
    for key in ("id", "name", "style", "version", "description", "designer", "foundry", "sample_text"):
        if not isinstance(m.get(key), str) or not m[key].strip() or "TODO" in m[key]:
            raise ValueError(f"{path.name}: fill in {key} in font.json.")
    if m["id"] != path.name or not SLUG.fullmatch(m["id"]):
        raise ValueError(f"{path}: font.json id must match its directory.")
    if m.get("schema_version") != 1 or m.get("license") != "MIT":
        raise ValueError(f"{path.name}: schema_version must be 1 and license MIT.")
    if m.get("copyright") != COPYRIGHT_NOTICE:
        raise ValueError(f"{path.name}: copyright must be {COPYRIGHT_NOTICE}.")
    if m["style"] != "Regular":
        raise ValueError("The current collection format supports one Regular style per family.")
    if any(ch in m["name"] for ch in ('"', '\\', '\n', '\r')):
        raise ValueError("Family names must not contain quotes, backslashes or line breaks.")
    if not re.fullmatch(r"\d+\.\d{3}", m["version"]):
        raise ValueError("Font versions use three decimals, for example 1.001.")
    if not isinstance(m.get("year"), int) or not 1000 <= m["year"] <= 2100:
        raise ValueError("Set the historical publication year.")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{1,62}", m.get("postscript_name", "")):
        raise ValueError("Set a PostScript name using ASCII letters, numbers and hyphens.")
    if not m.get("sources"):
        raise ValueError("At least one documented historical source is required.")
    for source in m["sources"]:
        for key in ("title", "url", "rights", "rights_url"):
            if not source.get(key) or "TODO" in source[key]:
                raise ValueError(f"{path.name}: complete source {key}.")
        for key in ("url", "rights_url"):
            if not source[key].startswith("https://"):
                raise ValueError("Source links must use HTTPS.")
        if source.get("file"):
            ref = path / source["file"]
            if not ref.resolve().is_relative_to((path / "reference").resolve()) or not ref.is_file():
                raise ValueError(f"Missing reference or invalid reference path: {ref}")
    for key in ("observed", "reconstructed"):
        if not m.get(key) or "TODO" in m[key]:
            raise ValueError(f"{path.name}: document {key} character forms.")
    if not (path / "CHANGELOG.md").is_file():
        raise ValueError(f"{path.name}: CHANGELOG.md is required.")
    if m.get("kind", "typeface") not in ("typeface", "icons"):
        raise ValueError("font.json kind must be typeface or icons.")
    if m.get("kind") == "icons":
        validate_icon_metadata(path, m)
    return m


def validate_icon_metadata(path, m):
    icons = m.get("icons")
    if not isinstance(icons, list) or not icons:
        raise ValueError("Icon collections need a nonempty icons list.")
    ids, codes, glyphs = set(), set(), set()
    recipe = json.loads((path / "source/tracing.json").read_text())
    for icon in icons:
        if not isinstance(icon.get("id"), str) or not SLUG.fullmatch(icon["id"]):
            raise ValueError("Icon IDs must be lowercase slugs.")
        cp = icon.get("codepoint", "")
        if not re.fullmatch(r"[E-F][0-9A-F]{3}", cp) or not 0xE000 <= int(cp, 16) <= 0xF8FF:
            raise ValueError("Icon codepoints must be BMP Private Use, E000 through F8FF.")
        if icon.get("glyph") != f"uni{cp}":
            raise ValueError("Icon glyph must match its stable Private Use codepoint.")
        if icon["id"] in ids or cp in codes or icon["glyph"] in glyphs:
            raise ValueError("Duplicate icon ID, codepoint or glyph.")
        ids.add(icon["id"]); codes.add(cp); glyphs.add(icon["glyph"])
        for key in ("name", "specimen_number"):
            if not isinstance(icon.get(key), str) or not icon[key].strip():
                raise ValueError(f"Icon needs {key}.")
        for key in ("printed_page", "pdf_page", "recommended_min_px"):
            if type(icon.get(key)) is not int or icon[key] < 1:
                raise ValueError(f"Icon needs a positive {key}.")
        index = icon.get("source_index")
        if type(index) is not int or not 0 <= index < len(m["sources"]):
            raise ValueError("Icon needs a valid source_index.")
        if not isinstance(icon.get("tags"), list) or any(not isinstance(t, str) for t in icon["tags"]):
            raise ValueError("Icon tags must be a list of strings.")
        entry = recipe["glyphs"].get(chr(int(cp, 16)))
        if not entry:
            raise ValueError("Every icon needs a documented historical crop.")
        layers = icon.get("multitone_layers", [])
        if layers:
            if not isinstance(layers, list) or not 2 <= len(layers) <= 3:
                raise ValueError("Multi-tone icons need two or three layers.")
            roles = []
            for layer in layers:
                if (not isinstance(layer, dict)
                        or layer.get("role") not in ("primary", "secondary", "tertiary")
                        or layer.get("glyph") != icon["glyph"] + "." + layer["role"]
                        or layer["glyph"] in glyphs
                        or type(layer.get("opacity")) not in (int, float)
                        or not 0 < layer["opacity"] <= 1):
                    raise ValueError("Invalid or duplicate multitone glyph/opacity.")
                glyphs.add(layer["glyph"])
                roles.append(layer["role"])
            if roles != ["primary", "secondary", "tertiary"][:len(layers)]:
                raise ValueError("Tone layers must be primary, secondary, then optional tertiary.")
            if not isinstance(entry.get("multitone"), dict):
                raise ValueError("Three-tone layers need a documented tonal recipe.")
        ref = path / entry["file"]
        if not ref.resolve().is_relative_to((path / "reference").resolve()) or not ref.is_file():
            raise ValueError("Icon crop must use a local reference file.")
        with Image.open(ref) as im:
            box = entry.get("box", [])
            if (len(box) != 4 or any(type(v) is not int for v in box)
                    or not 0 <= box[0] < box[2] <= im.width
                    or not 0 <= box[1] < box[3] <= im.height):
                raise ValueError("Icon crop lies outside its reference image.")


def normalize(font, m):
    font.recalcTimestamp = False
    font["head"].created = font["head"].modified = EPOCH
    font["head"].fontRevision = float(m["version"])
    font["OS/2"].fsType = 0
    # Windows uses these values as clipping limits. Include all accented outlines.
    glyph_set = font.getGlyphSet()
    bounds = BoundsPen(glyph_set)
    for glyph in glyph_set.values():
        glyph.draw(bounds)
    if bounds.bounds:
        font["OS/2"].usWinAscent = max(font["OS/2"].usWinAscent, math.ceil(bounds.bounds[3]))
        font["OS/2"].usWinDescent = max(font["OS/2"].usWinDescent, math.ceil(-bounds.bounds[1]))
    copyright_text = COPYRIGHT_NOTICE + ". Historical design: " + m["designer"] + "."
    names = {
        0: copyright_text, 1: m["name"], 2: m["style"],
        3: f'{m["postscript_name"]};{m["version"]}',
        4: f'{m["name"]} {m["style"]}', 5: "Version " + m["version"],
        6: m["postscript_name"], 8: COPYRIGHT_HOLDER, 9: m["designer"],
        10: m["description"], 11: "https://github.com/haroldus-/font-revival",
        13: (ROOT / "LICENSE").read_text().strip(),
        14: "https://opensource.org/license/mit",
        16: m["name"], 17: m["style"],
    }
    for name_id, value in names.items():
        font["name"].removeNames(nameID=name_id)
        font["name"].setName(value, name_id, 3, 1, 0x409)
    if "DSIG" in font:
        del font["DSIG"]
    if "CFF " in font:
        cff = font["CFF "].cff
        cff.fontNames = [m["postscript_name"]]
        top = cff.topDictIndex[0]
        top.version = m["version"]
        top.FamilyName = m["name"]
        top.FullName = names[4]
        top.Notice = copyright_text
        top.Copyright = COPYRIGHT_NOTICE


def apply_glyphs(font, folder):
    top = font["CFF "].cff.topDictIndex[0]
    for path in sorted(folder.glob("*.json")):
        data = json.loads(path.read_text())
        name = data["glyph"]
        if name != path.stem or name not in font.getGlyphOrder():
            raise ValueError(f"Invalid glyph override: {path}")
        width = data["advance_width"]
        if not isinstance(width, int) or not 0 <= width <= 65535:
            raise ValueError(f"Invalid advance width: {path}")
        pen = T2CharStringPen(width, None)
        parse_path(data["path"], pen)
        top.CharStrings[name] = pen.getCharString(private=top.Private, globalSubrs=top.GlobalSubrs)
        bounds = BoundsPen(None)
        parse_path(data["path"], bounds)
        font["hmtx"].metrics[name] = (width, round(bounds.bounds[0]) if bounds.bounds else 0)


def load_source(path, m):
    font = TTFont(recalcTimestamp=False)
    font.importXML(path / "source" / "font.ttx")
    if "CFF " not in font or "fvar" in font:
        raise ValueError("The canonical source must be a static CFF OpenType font.")
    apply_glyphs(font, path / "source" / "glyphs")
    normalize(font, m)
    return font


def to_truetype(otf, preserve_origins=False):
    font = copy.deepcopy(otf)
    glyph_set = font.getGlyphSet()
    glyphs = {}
    for name in font.getGlyphOrder():
        pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(Cu2QuPen(pen, max_err=0.5, reverse_direction=True))
        glyphs[name] = pen.glyph()
    del font["CFF "]
    font.sfntVersion = "\x00\x01\x00\x00"
    builder = FontBuilder(font=font)
    builder.isTTF = True
    builder.setupGlyf(glyphs)
    builder.setupMaxp()
    old_post = font["post"]
    builder.setupPost(keepGlyphNames=True, italicAngle=old_post.italicAngle,
                      underlinePosition=old_post.underlinePosition,
                      underlineThickness=old_post.underlineThickness,
                      isFixedPitch=old_post.isFixedPitch)
    # Quadratic control points can extend beyond the cubic curve's tight bounds.
    # Windows clipping limits must cover the bounds written to the TTF head too.
    for name, glyph in glyphs.items():
        glyph.recalcBounds(font['glyf'])
        if glyph.numberOfContours:
            if preserve_origins:
                # TrueType positions its control-point box using hmtx.lsb.
                # CFF uses a tight curve bound, which can differ substantially.
                # Register icon layers at their original coordinates instead of
                # letting that difference translate each region independently.
                advance = font['hmtx'][name][0]
                font['hmtx'][name] = (advance, glyph.xMin)
            font['OS/2'].usWinAscent = max(font['OS/2'].usWinAscent, glyph.yMax)
            font['OS/2'].usWinDescent = max(font['OS/2'].usWinDescent, -glyph.yMin)
    return font


def fit_pdf(c, text, name, size, x, y, width):
    size = min(size, size * width / max(pdfmetrics.stringWidth(text, name, size), 1))
    c.setFont(name, size)
    c.drawString(x, y, text)


def register_pdf_font(name, file):
    # ReportLab caches faces by the internal PostScript name. Two revisions of
    # the same family otherwise render as the first face in a comparison proof.
    with TTFont(file, recalcTimestamp=False) as font:
        unique_name = font["name"].getDebugName(6) + "-" + digest(Path(file))[:12]
        font["name"].removeNames(nameID=6)
        font["name"].setName(unique_name, 6, 3, 1, 0x409)
        stream = io.BytesIO()
        font.save(stream)
    stream.seek(0)
    pdfmetrics.registerFont(PDFont(name, stream))


def specimen(path, m):
    folder = path / "specimens"
    folder.mkdir(exist_ok=True)
    ttf = path / "fonts" / f'{m["postscript_name"]}.ttf'
    pdfname = m["id"]
    register_pdf_font(pdfname, ttf)
    c = canvas.Canvas(str(folder / "specimen.pdf"), pagesize=(842, 595), invariant=1, pageCompression=1)
    c.setTitle(m["name"] + " | Font Revival specimen")
    c.setAuthor(COPYRIGHT_HOLDER)
    c.setFillColor(HexColor(PAPER)); c.rect(0, 0, 842, 595, fill=1, stroke=0)
    c.setFillColor(HexColor(ACCENT)); c.setFont("Helvetica", 10)
    c.drawString(42, 550, f'FONT REVIVAL     /     {m["year"]}     /     {m["version"]}')
    c.setFillColor(HexColor(INK))
    fit_pdf(c, m["name"], pdfname, 82, 42, 431, 758)
    fit_pdf(c, m["sample_text"], pdfname, 43, 42, 339, 758)
    for line, y in [("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 253), ("abcdefghijklmnopqrstuvwxyz", 200),
                    ("0123456789  & ! ? @ $ % ( )", 147)]:
        fit_pdf(c, line, pdfname, 34, 42, y, 758)
    c.setStrokeColor(HexColor(ACCENT)); c.line(42, 96, 800, 96)
    c.setFont("Helvetica", 10)
    c.drawString(42, 68, "Regular  /  MIT License  /  Desktop + web")
    c.drawRightString(800, 68, "Historical forms. Shared futures.")
    c.showPage()
    # Every encoded character is printed, so additions and regressions are visible.
    with TTFont(ttf) as font:
        codepoints = sorted(font.getBestCmap())
    for start in range(0, len(codepoints), 120):
        c.setFillColor(HexColor(PAPER)); c.rect(0, 0, 842, 595, fill=1, stroke=0)
        c.setFillColor(HexColor(INK)); c.setFont("Helvetica", 11)
        c.drawString(42, 558, f'{m["name"]} / Character inventory / {len(codepoints)} encoded characters')
        for i, cp in enumerate(codepoints[start:start + 120]):
            x, y = 42 + (i % 15) * 51, 488 - (i // 15) * 60
            c.setFont(pdfname, 27); c.drawString(x, y, chr(cp))
            c.setFont("Helvetica", 6); c.drawString(x, y - 15, f"U+{cp:04X}")
        c.showPage()
    c.save()
    image = Image.new("RGB", (1600, 820), PAPER)
    draw = ImageDraw.Draw(image)
    label = ImageFont.load_default(size=21)
    draw.text((70, 42), f'FONT REVIVAL   /   {m["year"]}   /   MIT', font=label, fill=ACCENT)
    for text, y, size in [(m["name"], 260, 155), (m["sample_text"], 422, 92),
                           ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 561, 64),
                           ("abcdefghijklmnopqrstuvwxyz 0123456789", 681, 64)]:
        font = ImageFont.truetype(str(ttf), size)
        width = draw.textlength(text, font=font)
        if width > 1460:
            font = ImageFont.truetype(str(ttf), int(size * 1460 / width))
        draw.text((70, y), text, font=font, fill=INK, anchor="ls")
    draw.line((70, 754, 1530, 754), fill=ACCENT, width=2)
    draw.text((70, 779), "HISTORICAL FORMS. SHARED FUTURES.", font=label, fill=ACCENT)
    image.save(folder / "preview.png", optimize=False)


def source_review(path, m):
    """Pair documented crops with released glyphs, then show words at four sizes."""
    manifest = path / "source" / "tracing.json"
    if not manifest.exists():
        return
    recipe = json.loads(manifest.read_text())
    entries = recipe["glyphs"]
    companions = path / "source" / "companions.json"
    drawings = ({} if recipe.get("mode") == "glyph-revision" and not companions.exists()
                else json.loads(companions.read_text())["glyphs"])
    capitals_only = m.get("character_style") == "capitals-only"
    chars = recipe.get("review_characters", "ABCDEFGHIJKLMNOPQRSTUVWXYZ" +
                       ("" if capitals_only else "abcdefghijklmnopqrstuvwxyz") + "0123456789&$")
    fontname = m["id"] + "-source-review"
    register_pdf_font(fontname, path / "fonts" / f'{m["postscript_name"]}.ttf')
    c = canvas.Canvas(str(path / "specimens" / "source-review.pdf"), pagesize=(842, 595), invariant=1)
    c.setTitle(m["name"] + " | Historical source review")
    c.setAuthor(COPYRIGHT_HOLDER)
    images = {}
    for start in range(0, len(chars), 24):
        c.setFont("Helvetica", 14)
        c.drawString(36, 565, m["name"] + " / Source above, revival below")
        c.setFont("Helvetica", 8)
        c.drawString(36, 549, "Compare forms, not scale. Crops retain scan damage; drawings repair it. Coordinates: source/tracing.json.")
        for i, ch in enumerate(chars[start:start+24]):
            x, y = 36 + (i % 8)*97, 516 - (i // 8)*164
            c.setFont("Helvetica", 9)
            c.drawString(x, y, ch + (" / redrawn" if ch in drawings else " / traced"))
            entry = entries.get(ch)
            if entry:
                file = path / entry["file"]
                if file not in images:
                    images[file] = Image.open(file).convert("RGB")
                crop = images[file].crop(entry["box"])
                factor = min(80/crop.width, 52/crop.height)
                c.drawImage(ImageReader(crop), x, y-62, crop.width*factor, crop.height*factor)
            else:
                c.setFont("Helvetica", 8)
                c.drawString(x, y-35, "Inferred companion")
            c.setFont(fontname, 53)
            c.drawString(x, y-122, ch)
        c.showPage()
    c.setFont("Helvetica", 14)
    c.drawString(36, 555, m["name"] + " / Words and spacing")
    lines = recipe.get("review_words", [m["sample_text"], "AVATAR WAVY TYPE", "BANK QUARTZ 0123456789",
                                       "Mixed case maps to capitals." if capitals_only else "Quick jigs, waltzes & rhythms."])
    for size, y, line in zip((64, 36, 24, 16), (430, 320, 225, 145), lines):
        c.setFont("Helvetica", 9)
        c.drawString(36, y+65, f"{size} pt maximum")
        fit_pdf(c, line, fontname, size, 36, y, 770)
    c.save()


def family_readme(m, stats):
    ps = m["postscript_name"]
    sources = "\n".join(
        f'{i}. [{s["title"]}]({s["url"]}) — {s["rights"]} '
        f'[Rights basis]({s["rights_url"]}).' for i, s in enumerate(m["sources"], 1)
    )
    return f'''# {m["name"]}

{m["description"]}

![{m["name"]} specimen](specimens/preview.png)

**{m["year"]} · {m["style"]} · Version {m["version"]} · {stats["characters"]} characters{ ' · Capitals only' if m.get('character_style') == 'capitals-only' else ''} · MIT**

[OTF](fonts/{ps}.otf) · [TTF](fonts/{ps}.ttf) · [WOFF2](web/{ps}.woff2) · [PDF specimen](specimens/specimen.pdf) · [Changes](CHANGELOG.md)

## Use

Install either desktop format. For websites, copy `web/`, include `font.css`,
and use `font-family: "{m["name"]}"`. Designed for display sizes.

## Design

**Designer:** {m["designer"]}

**Foundry:** {m["foundry"]}

**Observed:** {m["observed"]}

**Reconstructed:** {m["reconstructed"]}

## Sources

{sources}

Source images are in `reference/`; the source record is [font.json](font.json).
Historical reference material retains the rights status recorded there.
{m["copyright"]}. The digital revival is released under the included [MIT License](LICENSE).

## Build or improve

From the repository root:

```sh
python scripts/fontrevival.py build {m["id"]}
python scripts/fontrevival.py check {m["id"]}
```

Edit `source/font.ttx` or export an individual glyph with
`python scripts/fontrevival.py glyph {m["id"]} j`.
Follow the shared [revival workflow](../../docs/WORKFLOW.md) for additions and revisions.
'''


def checksums(path):
    files = sorted(p for p in path.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt")
    return "".join(f"{digest(p)}  {p.relative_to(path).as_posix()}\n" for p in files)


def icon_records(m, font):
    """SVGs and CSS share the master, cmap, advances and em box with the fonts."""
    records = []
    glyphs = font.getGlyphSet()
    for icon in m["icons"]:
        if font.getBestCmap().get(int(icon["codepoint"], 16)) != icon["glyph"]:
            raise ValueError(f'{icon["id"]}: icon mapping differs from the master.')
        pen = SVGPathPen(glyphs)
        glyphs[icon["glyph"]].draw(pen)
        advance = font["hmtx"][icon["glyph"]][0]
        height = font["hhea"].ascent - font["hhea"].descent
        tones = []
        for layer in icon.get("multitone_layers", []):
            if layer["glyph"] not in glyphs:
                raise ValueError(f'Missing multitone layer {layer["glyph"]}.')
            tone = SVGPathPen(glyphs); glyphs[layer["glyph"]].draw(tone)
            tones.append(layer | {"path": tone.getCommands()})
        records.append(icon | {"path": pen.getCommands(), "tones": tones, "advance_width": advance,
                               "viewBox": f'0 {-font["hhea"].ascent} {advance} {height}',
                               "aspect_ratio": advance / height})
    return records


def icon_artwork(record):
    return f'<path fill="currentColor" transform="scale(1,-1)" d="{record["path"]}"/>'


def multitone_artwork(record):
    return '\n'.join(f'<path class="fr-{layer["role"]}" fill="var(--fr-{layer["role"]}-color,currentColor)" fill-opacity="var(--fr-{layer["role"]}-opacity,{layer["opacity"]:g})" transform="scale(1,-1)" d="{layer["path"]}"/>'
                     for layer in record["tones"])


def public_icon(record):
    return {k: v for k, v in record.items() if k not in ("path", "tones")}


def multitone_face(path, records, size=1024):
    """Prepare one in-memory font for all tonal PNGs in a collection.

    Temporary supplementary PUA mappings expose unencoded layer glyphs to the
    rasterizer. They are never saved in a release font or assigned to an icon.
    """
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
    with TTFont(path, recalcTimestamp=False) as font:
        table = CmapSubtable.newSubtable(12)
        table.platformID, table.platEncID, table.language = 3, 10, 0
        layers = [layer for record in records for layer in record["tones"]]
        table.cmap = {0xF0000 + i: layer["glyph"] for i, layer in enumerate(layers)}
        font["cmap"].tables = [table]
        upm, ascent = font["head"].unitsPerEm, font["hhea"].ascent
        stream = io.BytesIO(); font.save(stream)
    stream.seek(0)
    face = ImageFont.truetype(stream, size)
    return face, {name: chr(cp) for cp, name in table.cmap.items()}, upm, ascent


def render_multitone(path, record, size=1024, prepared=None):
    """Rasterise committed regions through Pillow, keeping PNG alpha."""
    face, characters, upm, ascent = prepared or multitone_face(path, [record], size)
    image = Image.new("RGBA", (math.ceil(record["advance_width"] * size / upm), size))
    for i, layer in enumerate(record["tones"]):
        mask = Image.new("L", image.size)
        ImageDraw.Draw(mask).text((0, ascent * size / upm), characters[layer["glyph"]], font=face, fill=255, anchor="ls")
        mask = mask.point(lambda alpha: round(alpha * layer["opacity"]))
        ink = Image.new("RGBA", image.size); ink.putalpha(mask)
        image = Image.alpha_composite(image, ink)
    return image


def icon_proofs(path, m, font):
    recipe = json.loads((path / "source/tracing.json").read_text())
    file = path / "fonts" / f'{m["postscript_name"]}.ttf'
    name = m["id"] + "-icons"
    register_pdf_font(name, file)
    c = canvas.Canvas(str(path / "specimens/specimen.pdf"), pagesize=(842, 595), invariant=1)
    c.setTitle(m["name"] + " | Historical icon comparison and size proof")
    c.setAuthor(COPYRIGHT_HOLDER)
    source_pages = {}
    glyphs = font.getGlyphSet()
    for i, icon in enumerate(m["icons"]):
        ch = chr(int(icon["codepoint"], 16))
        entry = recipe["glyphs"][ch]
        if entry["file"] not in source_pages:
            with Image.open(path / entry["file"]) as source:
                source_pages[entry["file"]] = source.convert("RGB")
        crop = source_pages[entry["file"]].crop(entry["box"])
        gray_file = path / "png/multitone" / f'{icon["id"]}.png'
        full_gray = Image.open(gray_file).convert("RGBA") if icon.get("multitone_layers") else None
        gray = full_gray
        if gray is not None:
            gray = gray.crop(gray.getbbox())
        c.setFont("Helvetica", 18)
        c.drawString(36, 553, f'{icon["name"]} / No. {icon["specimen_number"]}')
        c.setFont("Helvetica", 10)
        c.drawString(36, 529, f'{m["name"]} · printed p. {icon["printed_page"]} · PDF page {icon["pdf_page"]}')
        c.drawString(36, 481, "Historical scan")
        mono_x = 566 if gray is not None else 442
        panel_width = 230 if gray is not None else 340
        if gray is not None:
            c.drawString(301, 481, "Three-tone vector (rendered)")
            factor = min(panel_width / gray.width, 300 / gray.height)
            pdf_gray = gray.copy()
            pdf_gray.thumbnail((448, 448), Image.Resampling.LANCZOS)
            c.drawImage(ImageReader(pdf_gray), 301, 145, gray.width*factor, gray.height*factor, mask="auto")
        c.drawString(mono_x, 481, "Monochrome vector")
        factor = min(panel_width / crop.width, 300 / crop.height)
        pdf_crop = crop.copy()
        pdf_crop.thumbnail((800, 800), Image.Resampling.LANCZOS)
        c.drawImage(ImageReader(pdf_crop), 36, 145, crop.width * factor, crop.height * factor)
        bounds = BoundsPen(glyphs); glyphs[icon["glyph"]].draw(bounds)
        x0, y0, x1, y1 = bounds.bounds
        scale = min(panel_width / (x1-x0), 300 / (y1-y0))
        c.setFont(name, font["head"].unitsPerEm * scale)
        c.drawString(mono_x - x0 * scale, 145 - y0 * scale, ch)
        c.setFont("Helvetica", 10)
        c.drawString(36, 102, "Three distinct ink tones interpret the engraving; the solid version remains available. Proportions are retained.")
        c.drawString(36, 83, "Paper, specimen number and price are excluded. See source/METHOD.md for measured cleanup settings.")
        c.showPage()
        if gray is not None:
            c.setFont("Helvetica", 18); c.drawString(36, 553, icon["name"] + " / Three-tone at different sizes")
            x = 36
            pdf_full_gray = full_gray.copy()
            pdf_full_gray.thumbnail((448, 448), Image.Resampling.LANCZOS)
            tonal_reader = ImageReader(pdf_full_gray)
            for size in (16, 24, 32, 48, 64, 96, 192):
                width = size * full_gray.width / full_gray.height
                c.drawImage(tonal_reader, x, 305, width, size, mask="auto")
                c.setFont("Helvetica", 9); c.drawString(x, 282, f"{size} pt")
                x += width + 22
            c.setFont("Helvetica", 11)
            c.drawString(36, 180, "Sizes use the font em box. Original proportions. Raster shown in this PDF; download SVG for vector artwork.")
            c.drawString(36, 158, "The standard icon font and solid SVG remain monochrome. No additional shading has been invented.")
            c.showPage()
        c.setFont("Helvetica", 18); c.drawString(36, 553, icon["name"] + " / Size and inline proof")
        x = 36
        for size in (16, 24, 32, 48, 64, 96, 192):
            c.setFont("Helvetica", 9); c.drawString(x, 282, f"{size} pt")
            c.setFont(name, size); c.drawString(x, 305, ch)
            x += pdfmetrics.stringWidth(ch, name, size) + 22
        c.setFont("Helvetica", 18); c.drawString(36, 215, "Illustrated detail")
        c.setFont(name, 48); c.drawString(220, 210, ch)
        c.setFont("Helvetica", 12)
        c.drawString(36, 147, f'Detailed cut: recommended from {icon["recommended_min_px"]} px; inspect the intended output size.')
        c.drawString(36, 126, "At small sizes the engraving becomes dense. No simplified substitute is supplied.")
        c.drawString(36, 83, f'{icon["id"]}  /  U+{icon["codepoint"]}  /  SVG, sprite and icon font use the same master.')
        c.showPage()
        # One PNG comparison per icon, and the first as the collection preview.
        im = Image.new("RGB", (1700 if gray is not None else 1200, 690), PAPER)
        draw = ImageDraw.Draw(im); label = ImageFont.load_default(size=22)
        draw.text((40, 24), f'{icon["name"]} / No. {icon["specimen_number"]} / {m["year"]}', font=label, fill=INK)
        draw.text((40, 76), "Historical scan", font=label, fill=ACCENT)
        mono_x = 1160 if gray is not None else 650
        draw.text((mono_x, 76), "Monochrome vector", font=label, fill=ACCENT)
        if gray is not None:
            draw.text((600, 76), "Three-tone vector", font=label, fill=ACCENT)
            factor = min(470/gray.width, 440/gray.height)
            tonal = gray.resize((round(gray.width*factor), round(gray.height*factor)), Image.Resampling.LANCZOS)
            im.paste(tonal, (600, 126), tonal)
        factor = min(470 / crop.width, 440 / crop.height)
        im.paste(crop.resize((round(crop.width*factor), round(crop.height*factor)), Image.Resampling.LANCZOS), (40, 126))
        pixel_scale = min(470/(x1-x0), 440/(y1-y0))
        face = ImageFont.truetype(str(file), round(font["head"].unitsPerEm*pixel_scale))
        draw.text((mono_x-x0*pixel_scale, 126+y1*pixel_scale), ch, font=face, fill=INK, anchor="ls")
        draw.text((40, 624), f'Printed p. {icon["printed_page"]} / source detail retained / MIT digital revival', font=label, fill=ACCENT)
        im.save(path / "specimens" / f'{icon["id"]}.png')
        if i == 0:
            im.save(path / "specimens/preview.png")
    c.save()
    shutil.copyfile(path / "specimens/specimen.pdf", path / "specimens/source-review.pdf")


def icon_html_examples(record, base):
    """Copyable examples shared by the gallery and generated family instructions."""
    name = html.escape(record["name"], quote=True)
    icon_id = record["id"]
    variant = "multitone/" if record["tones"] else ""
    sprite = "icons-multitone.svg" if record["tones"] else "icons.svg"
    return {
        "image": f'<img src="{base}/svg/{variant}{icon_id}.svg"\n     alt="{name}" height="96">',
        "font": f'<link rel="stylesheet" href="{base}/web/icons.css">\n<span class="fr-icon fr-{icon_id}" aria-hidden="true"\n      style="font-size:96px;color:#a5422c"></span>\n<span>{name}</span>',
        "sprite": f'''<style>
  .revival-cut {{
    display: inline-block;
    font-size: 96px;
    height: 1em;
    width: {record["aspect_ratio"]:.6f}em;
    vertical-align: middle;
    --fr-primary-color: #24251f;
    --fr-secondary-color: #a5422c;
    --fr-tertiary-color: #a5422c;
    --fr-primary-opacity: 1;
    --fr-secondary-opacity: 0.55;
    --fr-tertiary-opacity: 0.25;
  }}
</style>
<svg class="revival-cut" role="img" aria-label="{name}">
  <use href="{base}/web/{sprite}#{icon_id}"></use>
</svg>''',
    }


def build_icons(path, m, font):
    records = icon_records(m, font)
    tonal_face = multitone_face(path / "fonts" / f'{m["postscript_name"]}.ttf', records) if any(r["tones"] for r in records) else None
    folder = path / "svg"
    folder.mkdir(exist_ok=True)
    # Avoid shipping deleted/renamed icons left over from an earlier build.
    names = {r["id"] + ".svg" for r in records}
    for old in folder.glob("*.svg"):
        if old.name not in names:
            raise ValueError(f"Obsolete generated SVG {old}; review the icon inventory before removing it.")
    symbols, gray_symbols = [], []
    for r in records:
        title = html.escape(r["name"])
        (folder / f'{r["id"]}.svg').write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{r["viewBox"]}" role="img" aria-label="{html.escape(r["name"], quote=True)}">\n'
            f'<title>{title}</title>\n<metadata>{m["copyright"]}; MIT. Historical source: {html.escape(m["sources"][r["source_index"]]["url"])}</metadata>\n'
            + icon_artwork(r) + '\n</svg>\n')
        symbols.append(f'<symbol id="{r["id"]}" viewBox="{r["viewBox"]}">{icon_artwork(r)}</symbol>')
        if r["tones"]:
            gray_folder = path / "svg/multitone"
            gray_folder.mkdir(exist_ok=True)
            (gray_folder / f'{r["id"]}.svg').write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{r["viewBox"]}" role="img" aria-label="{html.escape(r["name"], quote=True)} — three-tone">\n'
                f'<title>{title} — three-tone</title>\n<metadata>{m["copyright"]}; MIT. Layered vector interpretation of source tones; paper is transparent.</metadata>\n'
                + multitone_artwork(r) + '\n</svg>\n')
            gray_symbols.append(f'<symbol id="{r["id"]}" viewBox="{r["viewBox"]}">{multitone_artwork(r)}</symbol>')
            png_folder = path / "png/multitone"
            png_folder.mkdir(parents=True, exist_ok=True)
            rendered = render_multitone(path / "fonts" / f'{m["postscript_name"]}.ttf', r, prepared=tonal_face)
            # The raster is black ink with 256 possible alpha values. An indexed
            # alpha palette stores exactly those pixels without RGBA duplication.
            indexed = Image.frombytes("P", rendered.size, rendered.getchannel("A").tobytes())
            indexed.putpalette([0] * 768)
            indexed.save(png_folder / f'{r["id"]}.png', transparency=bytes(range(256)))
    (path / "web/icons.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg">\n' + '\n'.join(symbols) + '\n</svg>\n')
    if gray_symbols:
        (path / "web/icons-multitone.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg">\n' + '\n'.join(gray_symbols) + '\n</svg>\n')
    css = ['/* ' + m["copyright"] + '; MIT. Keep LICENSE with redistributed assets. */',
           '@import url("./font.css");',
           '.fr-icon { display: inline-block; font-style: normal; font-weight: 400; font-variant: normal; text-transform: none; line-height: 1; letter-spacing: 0; }',
           '.fr-icon::before { display: inline-block; font-style: normal; font-weight: 400; font-synthesis: none; }']
    for r in records:
        css.append(f'.fr-{r["id"]} {{ font-family: "{m["name"]}"; }}')
        css.append(f'.fr-{r["id"]}::before {{ content: "\\{r["codepoint"]}"; }}')
    (path / "web/icons.css").write_text('\n'.join(css) + '\n')
    public = [public_icon(r) | {"svg": f'svg/{r["id"]}.svg',
              "sprite": f'web/icons.svg#{r["id"]}', "css_class": f'fr-icon fr-{r["id"]}'} for r in records]
    for r, item in zip(records, public):
        if r["tones"]:
            item["multitone"] = {"svg": f'svg/multitone/{r["id"]}.svg', "png": f'png/multitone/{r["id"]}.png',
                                 "sprite": f'web/icons-multitone.svg#{r["id"]}'}
    write_json(path / "icons.json", {"schema_version": 1, "collection": m["id"], "version": m["version"], "icons": public})
    icon_proofs(path, m, font)
    first = records[0]; ps = m["postscript_name"]
    examples = icon_html_examples(first, f'collection/{m["id"]}')
    sources = '\n'.join(f'- [{s["title"]}]({s["url"]}) — {s["rights"]} [Rights basis]({s["rights_url"]}).' for s in m["sources"])
    return f'''# {m["name"]}

{m["description"]}

![Historical scan beside the vector revival](specimens/preview.png)

**{len(records)} icon(s) · Version {m["version"]} · MIT**

[SVG files](svg/) · [SVG sprite](web/icons.svg) · [OTF](fonts/{ps}.otf) · [TTF](fonts/{ps}.ttf) · [WOFF2](web/{ps}.woff2) · [Comparison and size proof](specimens/specimen.pdf) · [Icon manifest](icons.json) · [Changes](CHANGELOG.md)

{'[Three-tone SVGs](svg/multitone/) · [Three-tone sprite](web/icons-multitone.svg) · [Transparent three-tone PNGs](png/multitone/)' if gray_symbols else ''}

## Use in HTML

[Download the web bundle (ZIP)](downloads/{m["id"]}-web.zip), unzip it, and place
the extracted `collection` folder beside your HTML file. Keep its subfolders
together. The examples below then work as written; adjust the paths if you move
the folder elsewhere. The bundle contains SVGs, PNGs, fonts, CSS, instructions
and the license. No JavaScript or font installation is needed for SVG use.

### Three-tone image — works from disk too

The individual SVG displays all three tones at their default strengths, with a
transparent background. Change `height` to resize it; the proportions are retained.

```html
{examples["image"]}
```

An `<img>` has its own colour context: page CSS cannot recolour its internal
regions. For a decorative image beside a text label, use `alt=""` instead.

### Three-tone sprite — customise every tone

Copy `web/icons-multitone.svg` and use the following complete example on an
HTTP(S) page served from the same origin as the sprite. It draws dark primary ink
and two strengths of red. Each colour and opacity can be changed independently.

```html
{examples["sprite"]}
```

Use the same secondary and tertiary colour and opacity for a two-tone appearance.
The defaults are primary 100%, secondary 55% and tertiary 25%; these are separate
vector regions, not a gradient. The tone assignments interpret the historical
impression. A transparent PNG of the default tones is also provided.

External SVG sprites can be blocked on `file://` pages. To customise tones on a
page opened from disk, open the individual SVG in a text editor, copy its complete
`<svg>…</svg>` markup into your HTML, and add `class="revival-cut"` to that SVG.
The same CSS above then applies to its inline paths. Keep its `viewBox` and paths.
The gallery itself uses inline SVG so its previews work directly from disk.

### Monochrome icon font

Copy the whole `web/` folder, including CSS and webfonts. Standard icon fonts show
the solid artwork; use the SVG examples above for three-tone artwork.

```html
{examples["font"]}
```

The example hides a decorative icon from screen readers and supplies visible
text. For an icon that conveys meaning on its own, use `role="img"` and an
`aria-label` instead of `aria-hidden`. Font size and colour use ordinary CSS.

Install the OTF or TTF for desktop use. The manifest lists Private Use codepoints
(pilot: U+{first["codepoint"]}); these are not ordinary text characters. IDs and
codepoints are permanent within this collection. Keep the included LICENSE with
redistributed assets. Detailed cuts need display sizes: the pilot is recommended
from {first["recommended_min_px"]} px, with 16–192 pt proofs supplied for review.

## Evidence and editing

**Foundry:** {m["foundry"]}

**Designer:** {m["designer"]}

**Observed:** {m["observed"]}

**Interpreted or new:** {m["reconstructed"]}

{sources}

{m["copyright"]}. Historical public-domain material retains its status.
Read [the method](source/METHOD.md), [inventory](source/inventory.json) and
[icon workflow](../../docs/ICONS.md). The canonical master is `source/font.ttx`;
SVGs, sprite, fonts and manifests are generated from it with glyph edits applied.

```sh
python scripts/fontrevival.py build {m["id"]}
python scripts/fontrevival.py sizecheck {m["id"]}
python scripts/fontrevival.py check {m["id"]}
python scripts/fontrevival.py glyph {m["id"]} {first["glyph"]}
```
'''


def build_icon_download(path, m):
    """Ship a self-contained web folder with the same paths as the gallery examples."""
    base = f'collection/{m["id"]}'
    with TTFont(path / "fonts" / f'{m["postscript_name"]}.otf') as font:
        example = icon_html_examples(icon_records(m, font)[0], base)
    readme = f'''# {m["name"]} — Web bundle

Unzip this download and place the extracted `collection` folder beside your HTML
file. Keep its subfolders together. The examples below then work as written;
adjust their paths if you put the folder elsewhere.

## SVG image

```html
{example["image"]}
```

## SVG sprite with custom colours

Serve the HTML and assets from the same website. Set each region's colour and
opacity independently. Use matching secondary and tertiary values for two tones.

```html
{example["sprite"]}
```

## Monochrome icon font

```html
{example["font"]}
```

The font uses the solid artwork. SVG provides the three-tone version.
Keep `collection/{m["id"]}/LICENSE` with the assets when redistributing them.
{m["copyright"]}. MIT licensed.
'''
    files = {"README.md": readme.encode()}
    for folder in ("svg", "png", "fonts", "web"):
        for file in sorted((path / folder).rglob("*")):
            if file.is_file():
                files[f'{base}/{file.relative_to(path).as_posix()}'] = file.read_bytes()
    for name in ("LICENSE", "icons.json"):
        files[f"{base}/{name}"] = (path / name).read_bytes()
    archive = path / "downloads" / f'{m["id"]}-web.zip'
    archive.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data)


def build_family(path):
    m = metadata(path)
    font = load_source(path, m)
    for sub in ("fonts", "web", "specimens"):
        (path / sub).mkdir(exist_ok=True)
    ps = m["postscript_name"]
    font.save(path / "fonts" / f"{ps}.otf")
    ttf = to_truetype(font, preserve_origins=m.get("kind") == "icons")
    ttf.save(path / "fonts" / f"{ps}.ttf")
    for flavor in ("woff", "woff2"):
        ttf.flavor = flavor
        ttf.save(path / "web" / f"{ps}.{flavor}")
    (path / "web" / "font.css").write_text(
        f'@font-face {{\n  font-family: "{m["name"]}";\n'
        f'  src: url("./{ps}.woff2") format("woff2"),\n'
        f'       url("./{ps}.woff") format("woff");\n'
        '  font-style: normal;\n  font-weight: 400;\n  font-display: swap;\n}\n')
    stats = {"characters": len(font.getBestCmap()), "glyphs": len(font.getGlyphOrder())}
    if m.get("kind") == "icons":
        readme = build_icons(path, m, font)
    else:
        specimen(path, m)
        source_review(path, m)
        readme = family_readme(m, stats)
    shutil.copyfile(ROOT / "LICENSE", path / "LICENSE")
    (path / "README.md").write_text(readme)
    if m.get("kind") == "icons":
        build_icon_download(path, m)
    (path / "SHA256SUMS.txt").write_text(checksums(path))
    print(f'Built {m["id"]} {m["version"]}: {stats["characters"]} characters, {stats["glyphs"]} glyphs')
    return m | stats


def site_header(current, prefix=''):
    """One header for the typeface index, icon index and individual icons."""
    template = (ROOT / 'site/header.template.html').read_text()
    for token, replacement in {'@@PREFIX@@': prefix,
                               '@@TYPEFACES_CURRENT@@': ' aria-current="page"' if current == 'typefaces' else '',
                               '@@ICONS_CURRENT@@': ' aria-current="page"' if current == 'icons' else ''}.items():
        template = template.replace(token, replacement)
    return template.rstrip()


def site_ornament_outputs(collections):
    """Reuse the original artwork as small, cacheable SVGs in the site palette."""
    selected = {'boston-1889-p258-word-11-2': ('site/header-ornaments/ribbon-left.svg', True),
                'boston-1889-p258-word-11-6': ('site/header-ornaments/ribbon-right.svg', True),
                'boston-1889-p258-word-20-1': ('site/header-ornaments/terminal-left.svg', True),
                'boston-1889-p258-word-20-5': ('site/header-ornaments/terminal-right.svg', True),
                'boston-1889-p271-2519': ('site/field-manicule.svg', False)}
    css = (ROOT / 'site/shared.css').read_text()
    palette = dict(re.findall(r'--(red|ink|muted):\s*(#[0-9a-fA-F]{6})', css))
    colours = dict(zip(('primary', 'secondary', 'tertiary'), (palette['red'], palette['ink'], palette['muted'])))
    style = ';'.join(f'--fr-{role}-color:{colour};--fr-{role}-opacity:1' for role, colour in colours.items())
    outputs = {}
    for _, records in collections:
        for record in records:
            if record['id'] not in selected:
                continue
            filename, multitone = selected[record['id']]
            # Crop the font's empty sidebearings for layout; preserve every path.
            bounds = BoundsPen(None)
            for layer in record['tones'] if multitone else [record]:
                parse_path(layer['path'], bounds)
            x0, y0, x1, y1 = bounds.bounds
            viewbox = f'{x0:g} {-y1:g} {x1 - x0:g} {y1 - y0:g}'
            artwork_style = style if multitone else f'color:{palette["muted"]}'
            format_name = 'three-tone' if multitone else 'monochrome'
            outputs[filename] = (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" style="{artwork_style}">\n'
                f'<title>{html.escape(record["name"])} — {format_name}</title>\n'
                f'<metadata>{COPYRIGHT_NOTICE}; MIT. Generated from {record["id"]}; site palette.</metadata>\n'
                + (multitone_artwork(record) if multitone else icon_artwork(record)) + '\n</svg>\n')
    return outputs


def catalog_outputs():
    """Render the catalog without writes or a temporary copy of the collection."""
    entries, icon_collections = [], []
    cards, styles = [], []
    for path in families():
        m = metadata(path)
        with TTFont(path / "fonts" / f'{m["postscript_name"]}.otf') as font:
            m = m | {"characters": len(font.getBestCmap()), "glyphs": len(font.getGlyphOrder())}
            if m.get("kind") == "icons":
                icon_collections.append((m, icon_records(m, font)))
                continue
        entries.append(m)
        e = {key: html.escape(str(value), quote=True) for key, value in m.items() if isinstance(value, (str, int))}
        base = f'collection/{m["id"]}'
        styles.append(f'@font-face{{font-family:"{m["id"]}";src:url("{base}/web/{m["postscript_name"]}.woff2") format("woff2");font-display:swap}}')
        links = " ".join(f'<a download href="{base}/{folder}/{m["postscript_name"]}.{ext}">{ext.upper()} <span aria-hidden="true">↗</span></a>'
                         for folder, ext in [("fonts", "otf"), ("fonts", "ttf"), ("web", "woff2")])
        cards.append(f'''<article class="font-card" id="{m["id"]}">
  <div class="card-meta"><span>{e["year"]} / {e["foundry"]}</span><span>{len(entries):02d}</span></div>
  <h2 style="font-family:'{m["id"]}',serif">{e["name"]}</h2>
  <p class="description">{e["description"]}</p>
  <div class="type-sample" style="font-family:'{m["id"]}',serif" data-default="{e["sample_text"]}">{e["sample_text"]}</div>
  <p class="coverage">{m["characters"]} characters{ ' · Capitals only' if m.get('character_style') == 'capitals-only' else ''} · Regular · v{e["version"]}</p>
  <div class="downloads">{links}<a href="{base}/specimens/specimen.pdf">Specimen PDF ↗</a><a href="https://github.com/haroldus-/font-revival/tree/main/{base}">Sources ↗</a></div>
</article>''')
    catalog = json.dumps({"schema_version": 1, "families": entries}, indent=2, ensure_ascii=False) + "\n"
    template = (ROOT / "site" / "index.template.html").read_text()
    for token, replacement in {"@@FONT_CSS@@": "\n".join(styles), "@@SITE_CSS@@": (ROOT / "site/shared.css").read_text(), "@@SITE_HEADER@@": site_header('typefaces'), "@@CARDS@@": "\n".join(cards), "@@COUNT@@": str(len(entries))}.items():
        template = template.replace(token, replacement)
    brand_styles = [style for style in styles if any(f'font-family:"{family}"' in style
                   for family in ("quaint-gothic-1894", "erebus-1894", "hades-1894", "remington-1888"))]
    return {"catalog.json": catalog, "index.html": template} | site_ornament_outputs(icon_collections) | icon_catalog_outputs(icon_collections, brand_styles)


def icon_navigation(m, record, taxonomy):
    """Keep navigation terms separate from permanent icon identities and outlines."""
    category = taxonomy['collections'].get(m['id'], {}).get('type', 'cuts')
    sections = []
    for section in taxonomy['sections']:
        if section['collection'] != m['id'] or record['printed_page'] not in section['printed_pages']:
            continue
        if 'icons' in section and record['id'] not in section['icons']:
            continue
        if 'specimen_prefixes' in section and not any(record['specimen_number'].startswith(p) for p in section['specimen_prefixes']):
            continue
        if 'tags_any' in section and not set(record['tags']).intersection(section['tags_any']):
            continue
        sections.append(section)
    return category, sections


def icon_browse_fonts(collections):
    """Subset only encoded monochrome art, with lazy Unicode ranges per 96 icons."""
    from fontTools import subset
    outputs, css = {}, [f'/* {COPYRIGHT_NOTICE}; MIT. Generated monochrome browsing fonts. */']
    for m, records in collections:
        source = ROOT / 'collection' / m['id'] / 'fonts' / f'{m["postscript_name"]}.ttf'
        for start in range(0, len(records), 96):
            codepoints = sorted({int(r['codepoint'], 16) for r in records[start:start + 96]})
            # A family's first available font must contain a space to supply
            # its line metrics. Without it, browsers use fallback-font metrics
            # even while drawing the correct Private Use glyphs.
            if start == 0:
                codepoints.insert(0, 32)
            with TTFont(source, recalcTimestamp=False) as font:
                upm = font['head'].unitsPerEm
                ascent = 100 * font['hhea'].ascent / upm
                descent = -100 * font['hhea'].descent / upm
                selected = subset.Subsetter()
                selected.populate(unicodes=codepoints)
                selected.subset(font)
                font.flavor = 'woff2'
                data = io.BytesIO(); font.save(data)
            filename = f'{m["id"]}-{start // 96:03d}.woff2'
            outputs[f'site/icon-fonts/{filename}'] = data.getvalue()
            ranges = ','.join(f'U+{cp:X}' for cp in codepoints)
            # Use the same TrueType outlines as the released webfont, with an
            # explicit baseline matching the SVG frame across browsers.
            css.append(f'@font-face{{font-family:"browse-{m["id"]}";src:url("{filename}") format("woff2");font-weight:400;font-style:normal;font-display:block;ascent-override:{ascent:.8f}%;descent-override:{descent:.8f}%;line-gap-override:0%;unicode-range:{ranges}}}')
    outputs['site/icon-fonts/icons.css'] = '\n'.join(css) + '\n'
    return outputs


def icon_font_span(m, record):
    return (f'<span class="grid-icon" aria-hidden="true" style="font-family:\'browse-{m["id"]}\'">'
            f'&#x{record["codepoint"]};</span>')


def icon_detail(m, r, sections):
    base = f'../collection/{m["id"]}'
    title = html.escape(r['name'], quote=True)
    examples = icon_html_examples(r, f'collection/{m["id"]}')
    tags = ''.join(f'<li>{html.escape(tag)}</li>' for tag in r['tags'])
    section_links = ''.join(f'<a href="../icons.html?section={s["id"]}#collection">{html.escape(s["label"])}</a>' for s in sections)
    ps = m['postscript_name']
    links = ' '.join(f'<a download href="{base}/{folder}/{ps}.{ext}">{ext.upper()}</a>'
                     for folder, ext in (("fonts", "otf"), ("fonts", "ttf"), ("web", "woff2")))
    tone_preview = (f'<figure><div class="art"><svg data-icon-format="multitone" role="img" aria-label="{title} — three-tone" viewBox="{r["viewBox"]}" style="width:{r["aspect_ratio"]:.6f}em;height:1em">{multitone_artwork(r)}</svg></div><figcaption>Three-tone SVG</figcaption></figure>' if r['tones'] else '')
    tone_links = (f'<a download href="{base}/svg/multitone/{r["id"]}.svg">Three-tone SVG</a><a download href="{base}/png/multitone/{r["id"]}.png">Three-tone PNG</a><a download href="{base}/web/icons-multitone.svg">Three-tone sprite</a>' if r['tones'] else '')
    image_title = 'Three-tone image' if r['tones'] else 'Monochrome image'
    image_description = ('This displays all three tones with a transparent background.' if r['tones'] else 'This displays the monochrome artwork with a transparent background.')
    return f'''<article class="icon-card" id="{r['id']}">
  <p class="card-meta"><a href="../icons.html?collection={m['id']}#collection">{html.escape(m['name'])}</a><span>No. {html.escape(r['specimen_number'])}</span></p>
  <h1>{title}</h1>
  <ul class="tags" aria-label="Themes and search terms">{tags}</ul>
  <div class="section-links">{section_links}</div>
  <div class="tester controls">
    <div class="size-control"><label for="icon-size">ICON SIZE / <output id="size-output" for="icon-size">192</output> PX</label><input id="icon-size" type="range" min="16" max="320" value="192"></div>
    <div class="colour-control"><label for="icon-color">COLOUR</label><input type="color" id="icon-color" value="#24251f"></div>
  </div>
  <div class="renderings" role="group" aria-label="Formats for {title}">
    {tone_preview}
    <figure><div class="art"><svg data-icon-format="monochrome" role="img" aria-label="{title}" viewBox="{r['viewBox']}" style="width:{r['aspect_ratio']:.6f}em;height:1em">{icon_artwork(r)}</svg></div><figcaption>Monochrome SVG</figcaption></figure>
    <figure><div class="art" role="img" aria-label="{title}">{icon_font_span(m, r)}</div><figcaption>Monochrome icon font</figcaption></figure>
  </div>
  <div class="downloads"><a download href="{base}/downloads/{m['id']}-web.zip">Download web bundle (ZIP)</a>{tone_links}<a download href="{base}/svg/{r['id']}.svg">Monochrome SVG</a><a download href="{base}/web/icons.svg">Monochrome sprite</a>{links}<a href="{base}/specimens/specimen.pdf">Comparison PDF</a><a href="{base}/font.json">Source record</a></div>
  <details><summary>Use this icon in HTML</summary>
    <p><a download href="{base}/downloads/{m['id']}-web.zip">Download the web bundle (ZIP)</a>, unzip it, then place the extracted <code>collection</code> folder beside your HTML file. Keep its subfolders together. The examples below will then work as written; adjust the paths if you put the folder elsewhere. The bundle includes the SVGs, PNGs, fonts, CSS, instructions and license.</p>
    <h3>{image_title}</h3>
    <p>{image_description} Set the height; the width follows the original proportions.</p>
    <pre><code data-example="image">{html.escape(examples['image'])}</code></pre>
    <p>An image has its own colour context, so page CSS cannot recolour its internal regions. For a decorative image beside a text label, use <code>alt=""</code>.</p>
    <h3>{'Three-tone' if r['tones'] else 'SVG'} with your own colours</h3>
    <p>On an HTTP(S) page, load the sprite from the same site. This complete example uses dark primary ink and two strengths of red. Each region has an independent colour and opacity; set the secondary and tertiary values alike for a two-tone appearance.</p>
    <pre><code data-example="sprite">{html.escape(examples['sprite'])}</code></pre>
    <h3>Monochrome icon font</h3>
    <p>Copy the whole <code>web/</code> folder, including CSS and webfonts. Font size and colour use ordinary CSS. The icon font draws the solid version; use SVG for three-tone artwork.</p>
    <pre><code data-example="font">{html.escape(examples['font'])}</code></pre>
    <p>The decorative font icon is hidden from screen readers and has a visible text label. An icon conveying meaning on its own needs <code>role="img"</code> and an <code>aria-label</code> instead of <code>aria-hidden</code>.</p>
  </details>
  <details><summary>Compare with the historical impression</summary><img class="comparison" loading="lazy" src="{base}/specimens/{r['id']}.png" alt="Historical scan beside the three-tone and monochrome vector revivals"></details>
</article>'''


def icon_catalog_outputs(collections, brand_styles=()):
    taxonomy = json.loads((ROOT / 'site/icon-taxonomy.json').read_text())
    outputs = icon_browse_fonts(collections)
    tiles, icons, seen = [], [], set()
    sections_used = {}
    detail_template = (ROOT / 'site/icon.template.html').read_text()
    detail_template = detail_template.replace('@@SITE_HEADER@@', site_header('icons', '../'))
    shared_css = (ROOT / 'site/shared.css').read_text()
    for m, records in collections:
        base = f'collection/{m["id"]}'
        for r in records:
            if r['id'] in seen:
                raise ValueError(f'Duplicate icon ID across collections: {r["id"]}')
            seen.add(r['id'])
            category, sections = icon_navigation(m, r, taxonomy)
            sections_used.update({s['id']: s for s in sections})
            public = public_icon(r)
            if r['tones']:
                public['multitone'] = {'svg': f'{base}/svg/multitone/{r["id"]}.svg',
                                       'png': f'{base}/png/multitone/{r["id"]}.png',
                                       'sprite': f'{base}/web/icons-multitone.svg#{r["id"]}'}
            detail_path = f'icons/{r["id"]}.html'
            icons.append(public | {'collection': m['id'], 'type': category, 'sections': [s['id'] for s in sections],
                                  'page': detail_path, 'svg': f'{base}/svg/{r["id"]}.svg',
                                  'sprite': f'{base}/web/icons.svg#{r["id"]}', 'css_class': f'fr-icon fr-{r["id"]}',
                                  'source': m['sources'][r['source_index']]})
            title = html.escape(r['name'], quote=True)
            search = html.escape(' '.join([r['name'], *r['tags'], m['name'], taxonomy['types'][category],
                                          *[s['label'] + ' ' + s['historical_heading'] for s in sections]]), quote=True)
            section_ids = ' '.join(s['id'] for s in sections)
            tiles.append(f'<a class="icon-tile" href="{detail_path}" aria-label="{title}" data-id="{r["id"]}" data-search="{search}" data-collection="{m["id"]}" data-type="{category}" data-section="{section_ids}"{ " hidden" if len(icons) > 96 else ""}>{icon_font_span(m, r)}<span class="tile-name" aria-hidden="true">{title}</span></a>')
            detail = detail_template
            for token, replacement in {'@@TITLE@@': title, '@@DESCRIPTION@@': f'{title}: three-tone and monochrome SVGs, icon fonts and HTML examples.',
                                       '@@ICON_DETAIL@@': icon_detail(m, r, sections),
                                       '@@SITE_CSS@@': shared_css.replace('url("collection/', 'url("../collection/'),
                                       '@@BRAND_FONTS@@': '\n'.join(brand_styles).replace('url("collection/', 'url("../collection/')}.items():
                detail = detail.replace(token, replacement)
            outputs[detail_path] = detail
    def options(group, items):
        labels = []
        for key, label in items:
            count = sum(key in i['sections'] if group == 'section' else i[group] == key for i in icons)
            labels.append(f'<label class="filter-option"><input type="checkbox" name="{group}" value="{key}"><span>{html.escape(label)}</span><small aria-hidden="true">{count:,}</small></label>')
        return '\n'.join(labels)
    type_options = options('type', [(k, v) for k, v in taxonomy['types'].items() if any(i['type'] == k for i in icons)])
    collection_options = options('collection', [(m['id'], m['name']) for m, _ in collections])
    section_options = options('section', [(s['id'], s['label']) for s in sorted(sections_used.values(), key=lambda s: s['label'].lower())])
    filters = f'''<fieldset><legend>Type</legend><div class="filter-options">{type_options}</div></fieldset>
<details open><summary>Collection</summary><fieldset><legend class="sr-only">Collection</legend><div class="filter-options">{collection_options}</div></fieldset></details>
<details><summary>Specimen sections</summary><label class="sr-only" for="section-search">Find a specimen section</label><input class="section-search" id="section-search" type="search" placeholder="Find a section" autocomplete="off"><fieldset><legend class="sr-only">Specimen sections</legend><div class="filter-options section-options">{section_options}</div></fieldset></details>'''
    first = next(((m, r) for m, records in collections for r in records), None)
    hero = f'<span class="hero-face">{icon_font_span(*first)}</span>' if first else ''
    template = (ROOT / 'site/icons.template.html').read_text()
    for token, replacement in {'@@ICON_TILES@@': '\n'.join(tiles), '@@ICON_FILTERS@@': filters,
                               '@@SITE_CSS@@': shared_css, '@@SITE_HEADER@@': site_header('icons'), '@@BRAND_FONTS@@': '\n'.join(brand_styles),
                               '@@HERO_ICON@@': hero, '@@ICON_COUNT@@': f'{len(icons):,}'}.items():
        template = template.replace(token, replacement)
    return outputs | {'icons.html': template,
                      'icons.json': json.dumps({'schema_version': 1, 'collections': [m for m, _ in collections],
                                                'types': taxonomy['types'],
                                                'sections': [{k: s[k] for k in ('id', 'label', 'historical_heading', 'collection', 'printed_pages')} for s in sections_used.values()],
                                                'icons': icons}, indent=2, ensure_ascii=False) + '\n'}


def output_bytes(content):
    return content if isinstance(content, bytes) else content.encode()


def build_catalog():
    outputs = catalog_outputs()
    # Only these dedicated directories contain disposable generated site assets.
    # The obsolete local path chunks are superseded by individual detail pages.
    for folder, pattern in (('site/icon-art', '*.js'), ('site/icon-fonts', '*.woff2'), ('icons', '*.html')):
        for old in (ROOT / folder).glob(pattern):
            if old.relative_to(ROOT).as_posix() not in outputs:
                old.unlink()
    for filename, content in outputs.items():
        output = ROOT / filename
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(output_bytes(content))

SIZE_METRICS = ("y_min", "y_max", "ink_width", "ink_height", "advance_width")


def sizing_profile(path):
    file = path / "source" / "sizing.json"
    if not file.exists():
        return None
    profile = json.loads(file.read_text())
    if not isinstance(profile, dict):
        raise ValueError(f"{file}: sizing.json must contain a rule object.")
    return profile


def sizing_report(font, profile=None, character_style=None):
    """Measure ink, suggest peer outliers, and enforce reviewed family limits.

    Advance widths alone cannot detect a tiny drawing in a normal-sized cell.
    BoundsPen measures curve extrema and resolves components in either outline
    format. Top heights are compared separately from descenders and Q tails.
    """
    glyphs = font.getGlyphSet()
    measurements = {}
    for cp, name in sorted(font.getBestCmap().items()):
        pen = BoundsPen(glyphs)
        glyphs[name].draw(pen)
        x0, y0, x1, y1 = pen.bounds or (0, 0, 0, 0)
        measurements[chr(cp)] = {
            "glyph": name, "codepoint": f"U+{cp:04X}",
            "y_min": y0, "y_max": y1, "ink_width": x1 - x0,
            "ink_height": y1 - y0, "advance_width": font["hmtx"][name][0],
        }
    warnings, violations = [], []
    covered = set()

    def finding(ch, metric, low, high, reason):
        return {"character": ch, "glyph": measurements[ch]["glyph"],
                "metric": metric, "actual": measurements[ch][metric],
                "expected": [low, high], "reason": reason}

    if profile is not None:
        if (not isinstance(profile, dict) or profile.get("schema_version") != 1
                or set(profile) - {"schema_version", "notes", "rules"}
                or not isinstance(profile.get("rules"), list) or not profile["rules"]):
            raise ValueError("sizing.json: expected schema_version 1 and nonempty rules.")
        for rule in profile["rules"]:
            if (not isinstance(rule, dict) or set(rule) - {*SIZE_METRICS, "characters", "notes"}
                    or not isinstance(rule.get("characters"), str) or not rule["characters"]
                    or not isinstance(rule.get("notes"), str) or not rule["notes"].strip()
                    or not any(metric in rule for metric in SIZE_METRICS)):
                raise ValueError("sizing.json: each rule needs characters, metric ranges and notes; unknown keys are invalid.")
            chars = measurements if rule["characters"] == "*" else rule["characters"]
            missing = set(chars) - measurements.keys()
            if missing:
                raise ValueError(f"sizing.json: unsupported characters {sorted(missing)!r}.")
            covered.update(chars)
            for metric in SIZE_METRICS:
                if metric not in rule:
                    continue
                limits = rule[metric]
                if (not isinstance(limits, list) or len(limits) != 2
                        or any(type(v) not in (int, float) or not math.isfinite(v) for v in limits)
                        or limits[0] > limits[1]):
                    raise ValueError(f"sizing.json: {metric} needs a finite [minimum, maximum] range.")
                low, high = limits
                for ch in dict.fromkeys(chars):
                    if not low <= measurements[ch][metric] <= high:
                        violations.append(finding(ch, metric, low, high, rule["notes"]))

    def peer_group(chars, metric, tolerance, label):
        chars = [ch for ch in chars if ch in measurements and measurements[ch][metric] > 0]
        if len(chars) < 3:
            return None
        target = median(measurements[ch][metric] for ch in chars)
        low, high = target * (1 - tolerance), target * (1 + tolerance)
        for ch in chars:
            if not low <= measurements[ch][metric] <= high:
                warnings.append(finding(ch, metric, low, high, f"{label}: peer median {target:.1f}"))
        return target

    peer_group("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "y_max", .20, "capital tops")
    peer_group("0123456789", "y_max", .20, "figure tops")
    capitals_only = character_style == "capitals-only" or all(
        ch in measurements and ch.upper() in measurements
        and measurements[ch]["glyph"] == measurements[ch.upper()]["glyph"]
        for ch in "abcdefghijklmnopqrstuvwxyz")
    if not capitals_only:
        x_height = peer_group("acemnorsuvwxz", "y_max", .20, "lowercase body tops")
        ascender = peer_group("bdfhkl", "y_max", .20, "ascender tops")
        peer_group("ceo", "ink_width", .25, "round lowercase widths")
        if x_height and ascender and ascender > 1.15 * x_height and "t" in measurements:
            low, high = x_height + .20 * (ascender - x_height), 1.15 * ascender
            if not low <= measurements["t"]["y_max"] <= high:
                warnings.append(finding("t", "y_max", low, high, "t should usually rise above the lowercase body"))
    return {"units_per_em": font["head"].unitsPerEm, "measurements": measurements,
            "profile_characters": len(covered), "warnings": warnings, "violations": violations}


def sizing_message(item):
    low, high = item["expected"]
    return (f'{item["character"]!r} ({item["glyph"]}) {item["metric"]}={item["actual"]:.1f}; '
            f'expected {low:.1f}..{high:.1f}: {item["reason"]}')


def sizecheck(slug=None, json_output=False, strict=False):
    reports = {}
    for path in families(slug):
        m = metadata(path)
        with load_source(path, m) as font:
            reports[path.name] = sizing_report(font, sizing_profile(path), m.get("character_style"))
    if json_output:
        print(json.dumps(reports, indent=2, ensure_ascii=False))
    else:
        for name, report in reports.items():
            print(f'{name}: measured {len(report["measurements"])} characters in font units; '
                  f'{report["profile_characters"]} covered by reviewed rules; '
                  f'{len(report["violations"])} violations, {len(report["warnings"])} review warnings')
            for label, key in (("ERROR", "violations"), ("REVIEW", "warnings")):
                for item in report[key]:
                    print(f"  {label}: {sizing_message(item)}")
    if any(r["violations"] or (strict and r["warnings"]) for r in reports.values()):
        raise ValueError("Character sizing check failed. Review the reported glyphs against the historical source.")


def validate_family(path):
    m = metadata(path)
    profile = sizing_profile(path)
    expected = None
    expected_icon_bounds = {}
    for folder, ext in [("fonts", "otf"), ("fonts", "ttf"), ("web", "woff"), ("web", "woff2")]:
        file = path / folder / f'{m["postscript_name"]}.{ext}'
        with TTFont(file, checkChecksums=2) as font:
            cmap = font.getBestCmap()
            if m.get("kind") == "icons":
                expected_cmap = {32: "space"} | {int(i["codepoint"], 16): i["glyph"] for i in m["icons"]}
                if cmap != expected_cmap:
                    raise ValueError(f"{file}: icon coverage differs from the stable manifest.")
                if font["hhea"].ascent - font["hhea"].descent != font["head"].unitsPerEm or font["hhea"].lineGap:
                    raise ValueError(f"{file}: icons need a one-em box with no line gap.")
                bounds_set = font.getGlyphSet()
                drawings = [entry for icon in m["icons"] for entry in [icon, *icon.get("multitone_layers", [])]]
                for icon in drawings:
                    if icon["glyph"] not in bounds_set:
                        raise ValueError(f"{file}: missing multitone layer.")
                    pen = BoundsPen(bounds_set); bounds_set[icon["glyph"]].draw(pen)
                    if pen.bounds is None:
                        raise ValueError(f"{file}: empty visible character or tonal layer {icon['glyph']}.")
                    if pen.bounds:
                        x0, y0, x1, y1 = pen.bounds
                        if (x0 < 0 or x1 > font["hmtx"][icon["glyph"]][0]
                                or y0 < font["hhea"].descent or y1 > font["hhea"].ascent):
                            raise ValueError(f"{file}: icon would clip its SVG/em box.")
                        if ext == "otf":
                            expected_icon_bounds[icon["glyph"]] = pen.bounds
                        elif any(abs(a - b) > 2 for a, b in zip(
                                pen.bounds, expected_icon_bounds[icon["glyph"]])):
                            raise ValueError(f"{file}: icon layer changed position during conversion: {icon['glyph']}.")
            elif not set(range(32, 127)).issubset(cmap):
                raise ValueError(f"{file}: missing printable Basic Latin characters.")
            if font["OS/2"].fsType != 0:
                raise ValueError(f"{file}: embedding must be unrestricted.")
            if font["head"].yMax > font["OS/2"].usWinAscent or -font["head"].yMin > font["OS/2"].usWinDescent:
                raise ValueError(f"{file}: Windows line metrics would clip glyphs.")
            expected_notice = COPYRIGHT_NOTICE + ". Historical design: " + m["designer"] + "."
            if font['name'].getDebugName(0) != expected_notice or font['name'].getDebugName(8) != COPYRIGHT_HOLDER:
                raise ValueError(f"{file}: copyright holder metadata mismatch.")
            if "CFF " in font:
                top = font["CFF "].cff.topDictIndex[0]
                if top.Notice != expected_notice or top.Copyright != COPYRIGHT_NOTICE:
                    raise ValueError(f"{file}: CFF copyright metadata mismatch.")
            if font['name'].getDebugName(13) != (ROOT / 'LICENSE').read_text().strip():
                raise ValueError(f"{file}: missing MIT license metadata.")
            if font['name'].getDebugName(1) != m['name'] or font['name'].getDebugName(5) != 'Version ' + m['version']:
                raise ValueError(f"{file}: family/version metadata mismatch.")
            # Registered icon layers have format-specific control-point LSBs;
            # their actual ink bounds above and their advances must agree.
            metrics = ({name: width for name, (width, _) in font["hmtx"].metrics.items()}
                       if m.get("kind") == "icons" else font["hmtx"].metrics)
            shape = (cmap, font.getGlyphOrder(), metrics)
            if expected is not None and shape != expected:
                raise ValueError(f"{file}: formats have inconsistent characters or spacing.")
            expected = shape
            glyph_set = font.getGlyphSet()
            for cp, glyph in cmap.items():
                bounds = BoundsPen(glyph_set); glyph_set[glyph].draw(bounds)
                if bounds.bounds is None and not chr(cp).isspace() and cp not in (0, 13, 0x200b, 0x200c, 0x200d, 0xfeff):
                    raise ValueError(f"{file}: empty visible character U+{cp:04X}.")
            for ch in m["sample_text"]:
                if ord(ch) not in cmap:
                    raise ValueError(f"{file}: sample text uses unsupported character {ch!r}.")
            sizes = sizing_report(font, profile, m.get("character_style"))
            if sizes["violations"]:
                raise ValueError(f"{file}: character sizing violations:\n" +
                                 "\n".join(sizing_message(item) for item in sizes["violations"]))
            if ext == "otf":
                for item in sizes["warnings"]:
                    print(f"Review sizing {path.name}: {sizing_message(item)}")
    if (path / "SHA256SUMS.txt").read_text() != checksums(path):
        raise ValueError(f"{path.name}: stale checksums. Run build.")
    print(f"Validated {path.name}: formats, coverage, outlines, sizing, licensing and checksums")


def check(slug=None):
    selected = families(slug)
    for path in selected:
        validate_family(path)
    # Rebuild from committed source in isolation. Comparing all outputs detects
    # manual binary edits, stale proofs, and source changes not rebuilt for review.
    with tempfile.TemporaryDirectory(prefix="font-revival-check-") as temp:
        for path in selected:
            clone = Path(temp) / path.name
            shutil.copytree(path, clone)
            build_family(clone)
            original = {p.relative_to(path): digest(p) for p in path.rglob("*") if p.is_file()}
            rebuilt = {p.relative_to(clone): digest(p) for p in clone.rglob("*") if p.is_file()}
            differences = sorted(str(p) for p in original.keys() | rebuilt.keys() if original.get(p) != rebuilt.get(p))
            if differences:
                raise ValueError(f'{path.name}: rebuild differs: {", ".join(differences)}. Run build with requirements.txt.')
    # Check all cards even when checking one family. Rendering in memory avoids
    # copying large historical scans and temporarily mutating the global ROOT.
    for file, content in catalog_outputs().items():
        if (ROOT / file).read_bytes() != output_bytes(content):
            raise ValueError(f"{file} is stale. Run build.")
    print("Rebuild matches every committed output.")


def new_family(args):
    path = family_dir(args.id)
    if path.exists():
        raise ValueError(f"{args.id} already exists; edit it using the improvement workflow.")
    path.mkdir(parents=True)
    for sub in ("reference", "source/glyphs", "specimens"):
        (path / sub).mkdir(parents=True)
    write_json(path / "font.json", {
        "schema_version": 1, "id": args.id, "name": args.name, "style": "Regular", "version": "1.000",
        "postscript_name": re.sub(r"[^A-Za-z0-9]", "", args.name) + "-Regular",
        "year": args.year, "designer": "TODO: historical designer or documented attribution",
        "foundry": "TODO: historical foundry", "description": "TODO: one sentence describing this revival",
        "license": "MIT", "copyright": COPYRIGHT_NOTICE, "sample_text": "The quick brown fox jumps over the lazy dog",
        "observed": "TODO: characters directly evidenced by the historical sources",
        "reconstructed": "TODO: inferred or newly drawn characters; use None if all are observed",
        "sources": [{"title": "TODO", "url": "TODO", "rights": "TODO", "rights_url": "TODO", "file": "reference/TODO.png"}],
        "revival": {"author": COPYRIGHT_HOLDER, "tools": [], "notes": ""},
    })
    (path / "CHANGELOG.md").write_text(f"# Changes\n\n## 1.000\n\n- Initial revival.\n")
    print(f"Created {path.relative_to(ROOT)}. Complete font.json, add references, then import an OTF master.")


def import_font(args):
    path = family_dir(args.id)
    m = metadata(path)
    output = path / "source" / "font.ttx"
    if output.exists() and not args.replace:
        raise ValueError("Source exists. Use --replace intentionally, or edit individual glyphs.")
    with TTFont(args.font, recalcTimestamp=False) as font:
        if "CFF " not in font or "fvar" in font:
            raise ValueError("Export a static OpenType/CFF (.otf) master from your font editor or generator.")
        normalize(font, m)
        output.parent.mkdir(parents=True, exist_ok=True)
        font.saveXML(output)
    print(f"Imported {output.relative_to(ROOT)}. Run build {args.id}.")


def export_glyph(args):
    path = family_dir(args.id)
    m = metadata(path)
    font = load_source(path, m)
    name = font.getBestCmap().get(ord(args.character)) if len(args.character) == 1 else args.character
    if name not in font.getGlyphOrder():
        raise ValueError(f"Unknown glyph {args.character!r}.")
    output = path / "source" / "glyphs" / f"{name}.json"
    if output.exists():
        raise ValueError(f"{output.relative_to(ROOT)} already exists; edit that file.")
    pen = SVGPathPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    write_json(output, {"glyph": name, "advance_width": font["hmtx"].metrics[name][0],
                        "path": pen.getCommands(), "notes": "Font units; y increases upwards. Record your design rationale here."})
    print(f"Edit {output.relative_to(ROOT)}, then build {args.id}.")


def comparison(args):
    path = family_dir(args.id)
    m = metadata(path)
    after = path / "fonts" / f'{m["postscript_name"]}.ttf'
    for file in (Path(args.before), after):
        with TTFont(file) as font:
            if any(ord(ch) not in font.getBestCmap() for ch in args.text):
                raise ValueError(f"Comparison text contains characters absent from {file}.")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output), pagesize=(842, 595), invariant=1)
    c.setTitle(m["name"] + " | Revision comparison")
    c.setAuthor(COPYRIGHT_HOLDER)
    for index, (label, file) in enumerate((("Before", args.before), ("After", after))):
        name = f"comparison-{index}"
        register_pdf_font(name, file)
        top = 550 - index * 280
        c.setFont("Helvetica", 11); c.drawString(40, top, m["name"] + " / " + label)
        for size, offset in [(84, 112), (36, 183), (20, 226)]:
            fit_pdf(c, args.text, name, size, 40, top - offset, 762)
    c.save()
    print(f"Wrote {output}")


def package(slug=None):
    check(slug)
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    for path in families(slug):
        m = metadata(path)
        archive = out / f'{m["id"]}-{m["version"]}.zip'
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for file in sorted(p for p in path.rglob("*") if p.is_file()):
                info = zipfile.ZipInfo(f'{path.name}/{file.relative_to(path).as_posix()}', (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, file.read_bytes())
        print(f"Packaged {archive.relative_to(ROOT)}")
    (out / "SHA256SUMS.txt").write_text("".join(f"{digest(p)}  {p.name}\n" for p in sorted(out.glob("*.zip"))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("build", "check", "package"):
        sub = commands.add_parser(command)
        sub.add_argument("id", nargs="?")
    sub = commands.add_parser("sizecheck", help="Audit source glyph sizes and enforce reviewed family limits")
    sub.add_argument("id", nargs="?")
    sub.add_argument("--json", action="store_true", help="Print all measurements and findings as JSON")
    sub.add_argument("--strict", action="store_true", help="Also fail on heuristic review warnings")
    sub = commands.add_parser("new", help="Scaffold a family")
    sub.add_argument("id"); sub.add_argument("--name", required=True); sub.add_argument("--year", type=int, required=True)
    sub = commands.add_parser("import", help="Import an OTF into the shared editable source format")
    sub.add_argument("id"); sub.add_argument("font", type=Path); sub.add_argument("--replace", action="store_true")
    sub = commands.add_parser("glyph", help="Export an existing glyph as an editable SVG path in JSON")
    sub.add_argument("id"); sub.add_argument("character")
    sub = commands.add_parser("compare", help="Make a before/after PDF for a font revision")
    sub.add_argument("id"); sub.add_argument("--before", required=True); sub.add_argument("--text", required=True)
    sub.add_argument("--output", default="workspace/comparison.pdf")
    args = parser.parse_args()
    try:
        if args.command == "build":
            for path in families(args.id):
                build_family(path)
            build_catalog()
        elif args.command == "check": check(args.id)
        elif args.command == "sizecheck": sizecheck(args.id, args.json, args.strict)
        elif args.command == "package": package(args.id)
        elif args.command == "new": new_family(args)
        elif args.command == "import": import_font(args)
        elif args.command == "glyph": export_glyph(args)
        elif args.command == "compare": comparison(args)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
