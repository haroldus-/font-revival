#!/usr/bin/env python3
"""One source and one build pipeline for every Font Revival family."""

from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import math
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as PDFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
EPOCH = 3850070400  # 2026-01-01 UTC in OpenType's 1904 epoch; fixed for builds.
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
    return m


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
    copyright_text = "Copyright (c) 2026 Font Revival contributors. Historical design: " + m["designer"] + "."
    names = {
        0: copyright_text, 1: m["name"], 2: m["style"],
        3: f'{m["postscript_name"]};{m["version"]}',
        4: f'{m["name"]} {m["style"]}', 5: "Version " + m["version"],
        6: m["postscript_name"], 8: "Font Revival contributors", 9: m["designer"],
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
        top.Copyright = "MIT License; see name table and accompanying LICENSE."


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


def to_truetype(otf):
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
    return font


def fit_pdf(c, text, name, size, x, y, width):
    size = min(size, size * width / max(pdfmetrics.stringWidth(text, name, size), 1))
    c.setFont(name, size)
    c.drawString(x, y, text)


def specimen(path, m):
    folder = path / "specimens"
    folder.mkdir(exist_ok=True)
    ttf = path / "fonts" / f'{m["postscript_name"]}.ttf'
    pdfname = m["id"]
    pdfmetrics.registerFont(PDFont(pdfname, str(ttf)))
    c = canvas.Canvas(str(folder / "specimen.pdf"), pagesize=(842, 595), invariant=1, pageCompression=1)
    c.setTitle(m["name"] + " | Font Revival specimen")
    c.setAuthor("Font Revival contributors")
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


def family_readme(m, stats):
    ps = m["postscript_name"]
    sources = "\n".join(
        f'{i}. [{s["title"]}]({s["url"]}) — {s["rights"]} '
        f'[Rights basis]({s["rights_url"]}).' for i, s in enumerate(m["sources"], 1)
    )
    return f'''# {m["name"]}

{m["description"]}

![{m["name"]} specimen](specimens/preview.png)

**{m["year"]} · {m["style"]} · Version {m["version"]} · {stats["characters"]} characters · MIT**

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
The digital revival is released under the included [MIT License](LICENSE).

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


def build_family(path):
    m = metadata(path)
    font = load_source(path, m)
    for sub in ("fonts", "web", "specimens"):
        (path / sub).mkdir(exist_ok=True)
    ps = m["postscript_name"]
    font.save(path / "fonts" / f"{ps}.otf")
    ttf = to_truetype(font)
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
    specimen(path, m)
    shutil.copyfile(ROOT / "LICENSE", path / "LICENSE")
    (path / "README.md").write_text(family_readme(m, stats))
    (path / "SHA256SUMS.txt").write_text(checksums(path))
    print(f'Built {m["id"]} {m["version"]}: {stats["characters"]} characters, {stats["glyphs"]} glyphs')
    return m | stats


def build_catalog():
    entries = []
    cards, styles = [], []
    for path in families():
        m = metadata(path)
        with TTFont(path / "fonts" / f'{m["postscript_name"]}.otf') as font:
            m = m | {"characters": len(font.getBestCmap()), "glyphs": len(font.getGlyphOrder())}
        entries.append(m)
        e = {key: html.escape(str(value), quote=True) for key, value in m.items() if isinstance(value, (str, int))}
        base = f'collection/{m["id"]}'
        styles.append(f'@font-face{{font-family:"{m["id"]}";src:url("{base}/web/{m["postscript_name"]}.woff2") format("woff2");font-display:swap}}')
        links = " ".join(f'<a download href="{base}/{folder}/{m["postscript_name"]}.{ext}">{ext.upper()} <span aria-hidden="true">↗</span></a>'
                         for folder, ext in [("fonts", "otf"), ("fonts", "ttf"), ("web", "woff2")])
        cards.append(f'''<article class="font-card" id="{m["id"]}">
  <div class="card-meta"><span>{e["year"]} / {e["foundry"]}</span><span>0{len(entries)}</span></div>
  <h2 style="font-family:'{m["id"]}',serif">{e["name"]}</h2>
  <p class="description">{e["description"]}</p>
  <div class="type-sample" style="font-family:'{m["id"]}',serif" data-default="{e["sample_text"]}">{e["sample_text"]}</div>
  <p class="coverage">{m["characters"]} characters · Regular · v{e["version"]}</p>
  <div class="downloads">{links}<a href="{base}/specimens/specimen.pdf">Specimen PDF ↗</a><a href="https://github.com/haroldus-/font-revival/tree/main/{base}">Sources ↗</a></div>
</article>''')
    write_json(ROOT / "catalog.json", {"schema_version": 1, "families": entries})
    template = (ROOT / "site" / "index.template.html").read_text()
    for token, replacement in {"@@FONT_CSS@@": "\n".join(styles), "@@CARDS@@": "\n".join(cards), "@@COUNT@@": str(len(entries))}.items():
        template = template.replace(token, replacement)
    (ROOT / "index.html").write_text(template)


def validate_family(path):
    m = metadata(path)
    expected = None
    for folder, ext in [("fonts", "otf"), ("fonts", "ttf"), ("web", "woff"), ("web", "woff2")]:
        file = path / folder / f'{m["postscript_name"]}.{ext}'
        with TTFont(file, checkChecksums=2) as font:
            cmap = font.getBestCmap()
            if not set(range(32, 127)).issubset(cmap):
                raise ValueError(f"{file}: missing printable Basic Latin characters.")
            if font["OS/2"].fsType != 0:
                raise ValueError(f"{file}: embedding must be unrestricted.")
            if font["head"].yMax > font["OS/2"].usWinAscent or -font["head"].yMin > font["OS/2"].usWinDescent:
                raise ValueError(f"{file}: Windows line metrics would clip glyphs.")
            if font['name'].getDebugName(13) != (ROOT / 'LICENSE').read_text().strip():
                raise ValueError(f"{file}: missing MIT license metadata.")
            if font['name'].getDebugName(1) != m['name'] or font['name'].getDebugName(5) != 'Version ' + m['version']:
                raise ValueError(f"{file}: family/version metadata mismatch.")
            shape = (cmap, font.getGlyphOrder(), font["hmtx"].metrics)
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
    if (path / "SHA256SUMS.txt").read_text() != checksums(path):
        raise ValueError(f"{path.name}: stale checksums. Run build.")
    print(f"Validated {path.name}: formats, coverage, outlines, licensing and checksums")


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
    # Generate the index in an isolated root, including when checking one family.
    global ROOT
    original_root = ROOT
    with tempfile.TemporaryDirectory(prefix="font-revival-catalog-") as temp:
        temp_root = Path(temp)
        shutil.copytree(ROOT / "collection", temp_root / "collection")
        shutil.copytree(ROOT / "site", temp_root / "site")
        try:
            ROOT = temp_root
            build_catalog()
        finally:
            ROOT = original_root
        for file in ("catalog.json", "index.html"):
            if (ROOT / file).read_bytes() != (temp_root / file).read_bytes():
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
        "license": "MIT", "sample_text": "The quick brown fox jumps over the lazy dog",
        "observed": "TODO: characters directly evidenced by the historical sources",
        "reconstructed": "TODO: inferred or newly drawn characters; use None if all are observed",
        "sources": [{"title": "TODO", "url": "TODO", "rights": "TODO", "rights_url": "TODO", "file": "reference/TODO.png"}],
        "revival": {"contributors": [], "tools": [], "notes": ""},
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
    for index, (label, file) in enumerate((("Before", args.before), ("After", after))):
        name = f"comparison-{index}"
        pdfmetrics.registerFont(PDFont(name, str(file)))
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
        elif args.command == "package": package(args.id)
        elif args.command == "new": new_family(args)
        elif args.command == "import": import_font(args)
        elif args.command == "glyph": export_glyph(args)
        elif args.command == "compare": comparison(args)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
