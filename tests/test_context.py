from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_case import ROOT, read_json
from source_context import select

class ContextSelectionTest(unittest.TestCase):
    def setUp(self):
        self.catalogs = [read_json(ROOT / "sources/cy-eu.json"), read_json(ROOT / "sources/za.json")]

    def test_greek_accent_and_english_search_resolve_same_law(self):
        for query in ["ΠΡΟΣΩΠΙΚΑ ΔΕΔΟΜΕΝΑ", "data protection", "Datenschutz"]:
            result = select(self.catalogs, "CY", query)
            self.assertIn("cy-law125-art19", [x["source_id"] for x in result["sources"]])
            self.assertTrue(all(x["jurisdiction"] == "CY" for x in result["sources"]))

    def test_stale_date_stays_visible(self):
        result = select(self.catalogs, "CY", source_id="cy-law125-art19", as_of="2026-11-10")
        self.assertEqual(result["sources"][0]["date_status"], "outside_review_window")

    def test_translation_remains_separate_from_law(self):
        result = select(self.catalogs, source_id="cy-dpa-translation")
        self.assertEqual(result["sources"][0]["kind"], "unofficial_translation")
        self.assertEqual(result["sources"][0]["date_status"], "not_a_verified_provision")

    def test_context_bound_and_truncation_are_explicit(self):
        result = select(self.catalogs, limit=1)
        self.assertEqual(len(result["sources"]), 1)
        self.assertTrue(result["truncated"])
        with self.assertRaises(ValueError):select(self.catalogs, limit=100)
