import io
import json
import math
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from profile_design import activity as a


def fixture(start=date(2025, 10, 28), total=10):
    entries = [
        {"date": str(start + timedelta(days=i)), "contributionCount": total if i == 10 else 0}
        for i in range(365)
    ]
    return {
        "user": "SouphianeJ",
        "fetched_at": "2026-10-27T22:00:00Z",
        "collection": {
            "startedAt": str(start) + "T00:00:00Z",
            "endedAt": str(start + timedelta(days=364)) + "T22:00:00Z",
            "hasAnyRestrictedContributions": total > 0,
            "restrictedContributionsCount": min(8, total),
            "contributionCalendar": {
                "totalContributions": total,
                "weeks": [{"contributionDays": entries}],
            },
        },
    }


class ActivityTests(unittest.TestCase):
    def test_private_counts_not_added_twice(self):
        with tempfile.TemporaryDirectory() as d:
            a.publish_local(fixture(), d)
            output = json.loads((Path(d) / "activity.json").read_text())
            self.assertEqual(output["total_contributions"], 10)
            self.assertEqual(output["restricted_contributions"], 8)
            self.assertEqual(sum(x["count"] for x in output["days"]), 10)

    def test_empty_activity_produces_valid_finite_graphs(self):
        for svg in a.render(fixture(total=0)).values():
            root = ET.fromstring(svg)
            for element in root.iter():
                for name, value in element.attrib.items():
                    if name in {"x", "y", "width", "height", "font-size", "stroke-width"}:
                        self.assertTrue(math.isfinite(float(value)), (name, value))

    def test_leap_day_window_is_exactly_365_days(self):
        data = fixture(date(2023, 3, 2))
        start, end, days = a.validate(data)
        self.assertEqual(end, date(2024, 2, 29))
        self.assertEqual(len(days), 365)

    def test_calendar_padding_days_are_not_counted(self):
        data = fixture()
        data["collection"]["contributionCalendar"]["weeks"][0]["contributionDays"].insert(
            0, {"date": "2025-10-26", "contributionCount": 999}
        )
        self.assertEqual(sum(a.validate(data)[2].values()), 10)

    def test_missing_day_preserves_previous_output(self):
        data = fixture()
        data["collection"]["contributionCalendar"]["weeks"][0]["contributionDays"].pop()
        with tempfile.TemporaryDirectory() as d:
            previous = Path(d) / "activity.svg"
            previous.write_text("previous valid graph")
            with self.assertRaises(ValueError):
                a.publish_local(data, d)
            self.assertEqual(previous.read_text(), "previous valid graph")
            self.assertEqual([p.name for p in Path(d).iterdir()], ["activity.svg"])

    def test_incoherent_total_rejected(self):
        data = fixture()
        data["collection"]["contributionCalendar"]["totalContributions"] = 18
        with self.assertRaises(ValueError):
            a.render(data)

    def test_duplicate_day_rejected(self):
        data = fixture()
        entries = data["collection"]["contributionCalendar"]["weeks"][0]["contributionDays"]
        entries.append(entries[0].copy())
        with self.assertRaises(ValueError):
            a.render(data)

    def test_negative_day_rejected(self):
        data = fixture()
        data["collection"]["contributionCalendar"]["weeks"][0]["contributionDays"][0][
            "contributionCount"
        ] = -1
        with self.assertRaises(ValueError):
            a.render(data)

    def test_raw_private_metadata_never_exported(self):
        data = fixture()
        data["privateRepositoryName"] = "DO-NOT-PUBLISH"
        data["token"] = "DO-NOT-PUBLISH"
        with tempfile.TemporaryDirectory() as d:
            a.publish_local(data, d)
            for f in Path(d).iterdir():
                self.assertNotIn("DO-NOT-PUBLISH", f.read_text())

    def test_xml_escapes_profile_text(self):
        data = fixture()
        data["user"] = "name<&"
        for svg in a.render(data).values():
            ET.fromstring(svg)

    def test_unshared_activity_not_claimed_as_private(self):
        data = fixture(total=0)
        self.assertIn("Activité visible au jeton", a.render(data)["activity.svg"])
        self.assertNotIn(
            "Contributions privées partagées anonymement incluses", a.render(data)["activity.svg"]
        )

    def test_http_failure_does_not_echo_response_or_token(self):
        failure = HTTPError(
            "https://api.github.com/graphql", 403, "SECRET", {}, io.BytesIO(b"SECRET")
        )
        with (
            patch.dict("os.environ", {"GITHUB_TOKEN": "SECRET"}),
            patch.object(a, "urlopen", side_effect=failure),
        ):
            with self.assertRaises(ValueError) as error:
                a.fetch("SouphianeJ", datetime.now(UTC))
        self.assertNotIn("SECRET", str(error.exception))
        self.assertIn("403", str(error.exception))

    def test_unchanged_data_does_not_create_timestamp_only_diff(self):
        with tempfile.TemporaryDirectory() as d:
            a.publish_local(fixture(), d)
            before = {p.name: p.read_text() for p in Path(d).iterdir()}
            repeated = fixture()
            repeated["fetched_at"] = "2026-10-27T23:00:00Z"
            a.publish_local(repeated, d)
            self.assertEqual(before, {p.name: p.read_text() for p in Path(d).iterdir()})

    def test_new_contributions_are_not_suppressed(self):
        with tempfile.TemporaryDirectory() as d:
            a.publish_local(fixture(), d)
            changed = fixture(total=11)
            changed["fetched_at"] = "2026-10-27T23:00:00Z"
            a.publish_local(changed, d)
            data = json.loads((Path(d) / "activity.json").read_text())
            self.assertEqual(data["total_contributions"], 11)
            self.assertEqual(data["fetched_at"], changed["fetched_at"])

    def test_malformed_json_payload_is_reported_without_traceback(self):
        for payload in [b"[]", b'{"data": []}', b'{"data": {"user": []}}']:
            with (
                self.subTest(payload=payload),
                patch.dict("os.environ", {"GITHUB_TOKEN": "SECRET"}),
                patch.object(a, "urlopen", return_value=io.BytesIO(payload)),
            ):
                with self.assertRaises(ValueError):
                    a.fetch("SouphianeJ", datetime.now(UTC))

    def test_graphql_failure_is_not_published_as_zero(self):
        class Response(io.BytesIO):
            pass

        with (
            patch.dict("os.environ", {"GITHUB_TOKEN": "SECRET"}),
            patch.object(a, "urlopen", return_value=Response(b'{"errors":[{"message":"SECRET"}]}')),
        ):
            with self.assertRaises(ValueError) as error:
                a.fetch("SouphianeJ", datetime.now(UTC))
        self.assertNotIn("SECRET", str(error.exception))


if __name__ == "__main__":
    unittest.main()
