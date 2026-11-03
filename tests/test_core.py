from __future__ import annotations

import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from sovriva import db
from sovriva.api import PairingClaimRequest, claim_pairing, start_pairing
from sovriva.imports import ArchiveValidationError, parse_archive
from sovriva.intelligence import compare_platforms, drift_compare, normalize_interest


class CoreTests(unittest.TestCase):
    def make_zip(self, filename: str, payload: object) -> bytes:
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(filename, json.dumps(payload))
        return output.getvalue()

    def test_google_records_keep_source_provenance(self) -> None:
        archive = self.make_zip(
            "Google/My Activity/Search/MyActivity.json",
            {"items": [{"title": "Search: hiking shoes", "url": "https://example.test", "timestamp": "2026-01-01"}]},
        )
        parsed = parse_archive(archive, "google.zip")
        self.assertEqual(parsed.platform, "google")
        self.assertEqual(parsed.activities[0].source_file, "Google/My Activity/Search/MyActivity.json")
        self.assertEqual(parsed.activities[0].source_record_path, "items[0]")

    def test_legacy_google_html_is_extracted_as_activity(self) -> None:
        archive = self.make_zip(
            "Google/My Activity/Search/MyActivity.html",
            "<html><body><a href='https://example.test/search'><b>Search result</b></a><script>ignored()</script></body></html>",
        )
        parsed = parse_archive(archive, "google-html.zip")
        self.assertEqual(parsed.activities[0].title, "Search result")
        self.assertEqual(parsed.activities[0].source_record_path, "html.a[0]")
        self.assertIn("legacy-html", parsed.coverage["formats"])

    def test_meta_interest_is_normalized_without_losing_original(self) -> None:
        archive = self.make_zip(
            "facebook/ads_information/advertisers_using_your_activity.json",
            {"items": [{"name": "Trail running", "category": "sports"}]},
        )
        parsed = parse_archive(archive, "meta.zip")
        self.assertEqual(parsed.platform, "meta")
        self.assertEqual(parsed.interests[0].original_label, "Trail running")
        normalized = normalize_interest(parsed.interests[0].original_label)
        self.assertEqual(normalized[1], "sports")

    def test_traversal_is_rejected(self) -> None:
        archive = self.make_zip("../../outside.json", {"items": []})
        with self.assertRaises(ArchiveValidationError):
            parse_archive(archive, "unsafe.zip")

    def test_drift_distinguishes_uncertain_absence(self) -> None:
        before = [{"id": "one", "normalized_label": "sports:trail-running", "original_label": "Trail running", "category": "sports"}]
        after = []
        result = drift_compare(before, after, {"explicit_interest_support": True}, {"explicit_interest_support": False})
        self.assertEqual(result["removed"], [])
        self.assertEqual(result["uncertain_absence"][0]["id"], "one")

    def test_cross_platform_does_not_force_weak_match(self) -> None:
        records = [
            {"id": "g", "platform": "google", "normalized_label": "shopping:running-shoes", "original_label": "Running shoes"},
            {"id": "m", "platform": "meta", "normalized_label": "food:coffee", "original_label": "Coffee"},
        ]
        result = compare_platforms(records)
        self.assertEqual(result["matches"], [])
        self.assertEqual(len(result["platform_specific"]), 2)


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        db.DATA_DIR = Path(self.temp.name)
        db.DB_PATH = Path(self.temp.name) / "sovriva.db"
        db.init_db()

    def tearDown(self) -> None:
        # sqlite keeps the file locked until every connection is explicitly closed on Windows.
        connection = db.connect()
        connection.close()
        self.temp.cleanup()

    def test_schema_initializes_with_secure_defaults(self) -> None:
        connection = db.connect()
        try:
            settings = {row["key"]: row["value"] for row in connection.execute("SELECT key, value FROM settings")}
        finally:
            connection.close()
        self.assertEqual(settings["privacy_mode"], "BALANCED")
        self.assertEqual(settings["ad_blocking_enabled"], "true")

    def test_pairing_code_is_one_time_and_token_is_hashed(self) -> None:
        pairing = start_pairing()
        claimed = claim_pairing(PairingClaimRequest(code=pairing["code"], extension_id="test-extension"))
        self.assertEqual(claimed["status"], "paired")
        self.assertNotEqual(claimed["token"], pairing["code"])
        connection = db.connect()
        try:
            row = connection.execute("SELECT token_hash FROM extension_tokens").fetchone()
        finally:
            connection.close()
        self.assertIsNotNone(row)
        self.assertNotEqual(row["token_hash"], claimed["token"])


if __name__ == "__main__":
    unittest.main()
