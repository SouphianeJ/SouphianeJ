"""Repository-level checks for reproducibility, accessibility and SVG composition."""

import copy
import json
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from profile_design.build import ROOT, artifacts, build, load_content, validate_snapshot
from profile_design.calendar import render_calendar
from profile_design.sprites import PATTERNS, chase
from profile_design.svg import static_version


class ProfileTests(unittest.TestCase):
    def test_svg_ids_and_local_references_are_unambiguous(self):
        root = ET.fromstring(artifacts(ROOT)["assets/profile.svg"])
        ids = [element.attrib["id"] for element in root.iter() if "id" in element.attrib]
        self.assertEqual(len(ids), len(set(ids)))
        import re

        for element in root.iter():
            for name, value in element.attrib.items():
                for reference in re.findall(r"url\(#([^)]*)\)", value):
                    self.assertIn(reference, ids)
                if name.endswith("href"):
                    self.assertTrue(value.startswith("#"))

    def test_static_version_is_complete_without_animation_layers(self):
        svg = static_version(artifacts(ROOT)["assets/profile.svg"])
        self.assertNotIn("<style>", svg)
        self.assertNotIn("game-mouth-closed", svg)
        root = ET.fromstring(svg)
        text = " ".join(root.itertext())
        for phrase in ["iStage", "Intra-ILEPS", "193", "4 200", "CARTE D’ACTIVITÉ"]:
            self.assertIn(phrase, text)

    def test_only_one_image_block_prevents_markdown_gaps(self):
        readme = artifacts(ROOT)["README.md"]
        self.assertEqual(readme.count("<picture>"), 1)
        self.assertEqual(readme.count("<img "), 2)
        self.assertIn('href="https://www.linkedin.com/in/souphiane-jender/"', readme)
        self.assertTrue(
            readme.startswith('<a href="https://www.linkedin.com/in/souphiane-jender/"')
        )
        self.assertIn("<details>", readme)
        self.assertNotIn("{{impact_summary}}", readme)

    def test_all_icons_share_the_same_grid(self):
        for name, rows in PATTERNS.items():
            self.assertEqual(len(rows), 13, name)
            self.assertEqual({len(row) for row in rows}, {13}, name)

    def test_chase_and_escape_have_distinct_clips_and_directions(self):
        hunting, _ = chase(0, "process-game", reverse=True, hunting=True)
        escaping, _ = chase(0, "calendar-game")
        self.assertIn("scale(-1 1)", hunting)
        self.assertNotIn("scale(-1 1)", escaping)
        self.assertIn("process-game-clip", hunting)
        self.assertIn("calendar-game-clip", escaping)
        self.assertNotIn("calendar-game", hunting)

    def test_every_calendar_day_survives_decorative_animation(self):
        snapshot = json.loads((ROOT / "assets/activity.json").read_text())
        root = ET.fromstring(render_calendar(snapshot))
        actual = [
            element.attrib["data-date"] for element in root.iter() if "data-date" in element.attrib
        ]
        self.assertEqual(sorted(actual), sorted(entry["date"] for entry in snapshot["days"]))
        self.assertEqual(len(actual), 365)

    def test_invalid_snapshot_is_not_accepted(self):
        snapshot = json.loads((ROOT / "assets/activity.json").read_text())
        snapshot["days"].append(copy.deepcopy(snapshot["days"][0]))
        with self.assertRaises(ValueError):
            validate_snapshot(snapshot)

    def test_impact_categories_can_be_partial_but_not_exceed_total(self):
        source, impact = load_content(ROOT)
        self.assertIn("dont **145 vacataires**", source)
        self.assertLess(
            impact["temporary_lecturers"] + impact["self_employed"], impact["active_contributors"]
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "content", root / "content")
            impact["temporary_lecturers"] = impact["active_contributors"]
            (root / "content/impact.json").write_text(json.dumps(impact))
            with self.assertRaises(ValueError):
                load_content(root)

    def test_generation_is_repeatable_and_check_mode_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "content", root / "content")
            shutil.copytree(ROOT / "assets", root / "assets")
            build(root)
            before = {name: (root / name).read_bytes() for name in artifacts(root)}
            build(root)
            build(root, check=True)
            self.assertEqual(before, {name: (root / name).read_bytes() for name in before})
            readme = root / "README.md"
            readme.write_text("An intentional manual edit")
            with self.assertRaises(ValueError):
                build(root, check=True)
            self.assertEqual(readme.read_text(), "An intentional manual edit")


if __name__ == "__main__":
    unittest.main()
