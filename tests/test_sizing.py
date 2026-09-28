"""Sizing regressions must be detected even when spacing and coverage survive."""

import contextlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fontrevival", ROOT / "scripts/fontrevival.py")
revival = importlib.util.module_from_spec(spec)
spec.loader.exec_module(revival)
FAMILY = ROOT / "collection/remington-1888"


def transform(font, name, matrix):
    top = font["CFF "].cff.topDictIndex[0]
    pen = T2CharStringPen(font["hmtx"][name][0], None)
    font.getGlyphSet()[name].draw(TransformPen(pen, matrix))
    top.CharStrings[name] = pen.getCharString(private=top.Private, globalSubrs=top.GlobalSubrs)


class SizingTests(unittest.TestCase):
    def setUp(self):
        self.profile = revival.sizing_profile(FAMILY)

    def current(self):
        return revival.load_source(FAMILY, revival.metadata(FAMILY))

    def test_original_remington_exposes_t_and_e_despite_correct_advances(self):
        with TTFont() as font:
            font.importXML(FAMILY / "source/font.ttx")
            report = revival.sizing_report(font, self.profile)
            self.assertEqual({"t", "e"}, {v["character"] for v in report["violations"]})
            self.assertIn("t", {v["character"] for v in report["warnings"]})
            self.assertEqual(600, report["measurements"]["t"]["advance_width"])
            self.assertEqual(600, report["measurements"]["e"]["advance_width"])

    def test_all_released_formats_pass_reviewed_sizes_and_keep_spacing(self):
        for folder, ext in (("fonts", "otf"), ("fonts", "ttf"), ("web", "woff"), ("web", "woff2")):
            with self.subTest(format=ext), TTFont(FAMILY / folder / f"Remington1888-Regular.{ext}") as font:
                report = revival.sizing_report(font, self.profile)
                self.assertFalse(report["violations"])
                self.assertFalse(report["warnings"])
                self.assertTrue(all(row["advance_width"] == 600 for row in report["measurements"].values()))

    def test_revision_changes_only_e_and_t_and_preserves_font_contracts(self):
        with TTFont() as before, self.current() as after:
            before.importXML(FAMILY / "source/font.ttx")
            self.assertEqual(before.getBestCmap(), after.getBestCmap())
            self.assertEqual(before.getGlyphOrder(), after.getGlyphOrder())
            self.assertEqual(before["post"].isFixedPitch, after["post"].isFixedPitch)
            changed = set()
            for name in before.getGlyphOrder():
                self.assertEqual(before["hmtx"][name][0], after["hmtx"][name][0])
                old, new = RecordingPen(), RecordingPen()
                before.getGlyphSet()[name].draw(old)
                after.getGlyphSet()[name].draw(new)
                if old.value != new.value:
                    changed.add(name)
            self.assertEqual({"e", "t"}, changed)
            for tag in ("GPOS", "GSUB", "kern"):
                self.assertEqual(tag in before, tag in after)
                if tag in before:
                    self.assertEqual(before[tag].compile(before), after[tag].compile(after))

    def test_peer_audit_detects_shrunken_e_without_a_profile(self):
        with self.current() as font:
            transform(font, "e", (.6, 0, 0, .6, 120, 0))
            report = revival.sizing_report(font)
            metrics = {v["metric"] for v in report["warnings"] if v["character"] == "e"}
            self.assertEqual({"y_max", "ink_width"}, metrics)
            self.assertFalse(report["violations"])

    def test_reviewed_limits_catch_width_only_and_baseline_regressions(self):
        for matrix, metric in (((.75, 0, 0, 1, 75, 0), "ink_width"),
                               ((1, 0, 0, 1, 0, 30), "y_min")):
            with self.subTest(metric=metric), self.current() as font:
                transform(font, "e", matrix)
                report = revival.sizing_report(font, self.profile)
                self.assertIn(metric, {v["metric"] for v in report["violations"]})

    def test_tail_descenders_dots_and_narrow_letters_are_not_body_outliers(self):
        with self.current() as font:
            report = revival.sizing_report(font, self.profile)
            self.assertFalse(report["warnings"])
            self.assertFalse(report["violations"])
            self.assertGreater(report["measurements"]["Q"]["ink_height"], 800)
            self.assertLess(report["measurements"]["j"]["y_min"], -180)
            self.assertLess(report["measurements"]["c"]["ink_width"], 400)

    def test_capitals_only_fonts_do_not_get_lowercase_heuristics(self):
        with TTFont(ROOT / "collection/erebus-1894/fonts/Erebus1894-Regular.otf") as font:
            report = revival.sizing_report(font, character_style="capitals-only")
            self.assertTrue(all(not v["character"].islower() for v in report["warnings"]))

    def test_ranges_are_in_font_units_and_heuristics_scale_with_the_font(self):
        with self.current() as font:
            for name in font.getGlyphOrder():
                transform(font, name, (2, 0, 0, 2, 0, 0))
            font["head"].unitsPerEm *= 2
            report = revival.sizing_report(font)
            self.assertFalse(report["warnings"])
            self.assertEqual(2000, report["units_per_em"])

    def test_invalid_profiles_cannot_silently_disable_rules(self):
        profiles = [
            {}, {"schema_version": 2, "rules": []},
            {"schema_version": 1, "rules": [{"characters": "e", "notes": "typo", "width": [1, 2]}]},
        ]
        for limits in ([10, 1], [1], [False, 2], [0, float("inf")], [0, float("nan")]):
            profiles.append({"schema_version": 1, "rules": [
                {"characters": "e", "notes": "invalid range", "ink_width": limits}]})
        profiles.append({"schema_version": 1, "rules": [
            {"characters": "é", "notes": "absent accent", "y_max": [1, 700]}]})
        with self.current() as font:
            for profile in profiles:
                with self.subTest(profile=profile), self.assertRaisesRegex(ValueError, "sizing.json"):
                    revival.sizing_report(font, profile)

    def test_null_profile_file_is_not_treated_as_an_absent_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            family = Path(tmp)
            (family / "source").mkdir()
            (family / "source/sizing.json").write_text("null\n")
            with self.assertRaisesRegex(ValueError, "sizing.json"):
                revival.sizing_profile(family)

    def test_cli_measures_unbuilt_edits_and_emits_machine_readable_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            family = root / "collection/remington-1888"
            shutil.copytree(FAMILY, family)
            shutil.copyfile(ROOT / "LICENSE", root / "LICENSE")
            edit = family / "source/glyphs/t.json"
            data = json.loads(edit.read_text())
            data["path"] = "M150 0H450V480H150Z"
            revival.write_json(edit, data)
            original_root = revival.ROOT
            revival.ROOT = root
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output), self.assertRaisesRegex(ValueError, "sizing check failed"):
                    revival.sizecheck("remington-1888", json_output=True)
            finally:
                revival.ROOT = original_root
            report = json.loads(output.getvalue())["remington-1888"]
            self.assertEqual({"t"}, {v["character"] for v in report["violations"]})

    def test_normal_check_rejects_sizing_before_checksums(self):
        with tempfile.TemporaryDirectory() as tmp:
            family = Path(tmp) / "remington-1888"
            shutil.copytree(FAMILY, family)
            file = family / "fonts/Remington1888-Regular.otf"
            with TTFont(file) as font:
                transform(font, "t", (1, 0, 0, .65, 0, 0))
                font.save(file)
            with self.assertRaisesRegex(ValueError, "character sizing violations"):
                revival.validate_family(family)


if __name__ == "__main__":
    unittest.main()
