from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_case import EvidenceError, ROOT, check_case, read_json


class CitationGateTest(unittest.TestCase):
    def setUp(self):
        self.case = read_json(ROOT / "cases/eu-web-inquiry.json")
        self.catalog = read_json(ROOT / "sources/cy-eu.json")
        self.manifest = read_json(ROOT / self.catalog["manifest_path"])

    def verify(self):
        return check_case(self.case, self.catalog, self.manifest, ROOT)

    def test_accepts_pinned_sources(self):
        result = self.verify()
        self.assertEqual([item["jurisdiction"] for item in result["citations"]], ["EU"])

    def test_rejects_unregistered_source(self):
        self.case["citations"][0]["source_id"] = "made-up-source"
        with self.assertRaisesRegex(EvidenceError, "nicht registriert"):
            self.verify()

    def test_rejects_guidance_as_statute(self):
        self.case["citations"][0]["source_id"] = "cy-consumer"
        with self.assertRaisesRegex(EvidenceError, "keine amtliche Norm"):
            self.verify()

    def test_rejects_wrong_version(self):
        self.case["citations"][0]["version_id"] = "CY:26(I)/2022:art19-1:el"
        with self.assertRaisesRegex(EvidenceError, "Falsche oder unbelegte Fassung"):
            self.verify()

    def test_rejects_in_force_but_not_yet_applicable(self):
        self.case["as_of"] = "2018-05-24"
        with self.assertRaisesRegex(EvidenceError, "außerhalb"):
            self.verify()

    def test_rejects_after_last_review(self):
        self.case["as_of"] = "2026-11-09"
        with self.assertRaisesRegex(EvidenceError, "außerhalb"):
            self.verify()

    def test_rejects_superseded_version(self):
        version = self.catalog["sources"]["eu-gdpr-art13"]["version"]
        version["applies_until_exclusive"] = self.case["as_of"]
        with self.assertRaisesRegex(EvidenceError, "abgelöst"):
            self.verify()

    def test_rejects_wrong_locator(self):
        self.case["citations"][0]["locator"] = "Art. 14 Abs. 1 Buchst. a"
        with self.assertRaisesRegex(EvidenceError, "Fundstelle nicht geprüft"):
            self.verify()

    def test_rejects_wrong_quote(self):
        self.case["citations"][0]["quote"] = "a different quote"
        with self.assertRaisesRegex(EvidenceError, "Zitat weicht ab"):
            self.verify()

    def test_rejects_matching_catalog_quote_absent_from_pdf(self):
        claim = self.case["citations"][0]
        source = self.catalog["sources"][claim["source_id"]]
        claim["quote"] = "a fabricated quote"
        source["provisions"][claim["locator"]]["quote"] = claim["quote"]
        with self.assertRaisesRegex(EvidenceError, "Zitat fehlt im PDF"):
            self.verify()

    def test_rejects_hash_mismatch(self):
        self.manifest["captures"]["eu-gdpr-oj-en.pdf"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(EvidenceError, "SHA-256"):
            self.verify()

    def test_rejects_absent_corrigendum_evidence(self):
        del self.manifest["captures"]["eu-gdpr-corrigendum-en.pdf"]
        with self.assertRaisesRegex(EvidenceError, "Nachweis fehlt"):
            self.verify()

    def test_rejects_truncated_download_with_matching_hash(self):
        self.manifest["captures"]["eu-gdpr-oj-en.pdf"]["transport_body_bytes"] += 1
        with self.assertRaisesRegex(EvidenceError, "Antwortkörper unvollständig"):
            self.verify()

    def test_rejects_path_outside_evidence(self):
        self.manifest["captures"]["eu-gdpr-oj-en.pdf"]["path"] = "README.md"
        with self.assertRaisesRegex(EvidenceError, "außerhalb"):
            self.verify()

    def test_rejects_unofficial_translation_as_statute(self):
        self.catalog["sources"]["eu-gdpr-art13"]["kind"] = "unofficial_translation"
        with self.assertRaisesRegex(EvidenceError, "keine amtliche Norm"):
            self.verify()


class LocalCountryIntegrationTest(unittest.TestCase):
    def country(self, case_file, catalog_file, expected):
        case = read_json(ROOT / case_file)
        catalog = read_json(ROOT / catalog_file)
        manifest = read_json(ROOT / catalog["manifest_path"])
        needed = set()
        for c in case["citations"]:
            source = catalog["sources"][c["source_id"]]
            needed.add(source["provisions"][c["locator"]]["capture_id"])
            needed.update(source["version"]["review_capture_ids"])
        missing = [i for i in needed if not (ROOT / manifest["captures"][i]["path"]).is_file()]
        if missing:
            self.skipTest("Lawfully obtained local evidence missing: " + ", ".join(sorted(missing)))
        result = check_case(case, catalog, manifest, ROOT)
        self.assertEqual([c["jurisdiction"] for c in result["citations"]], expected)
        return case, catalog, manifest

    def test_cy_local_sources(self):
        self.country("cases/cy-web-inquiry.json", "sources/cy-eu.json", ["EU", "CY"])

    def test_za_local_sources_and_commencement(self):
        case, catalog, manifest = self.country("cases/za-web-inquiry.json", "sources/za.json", ["ZA", "ZA"])
        case["as_of"] = "2020-06-30"
        with self.assertRaisesRegex(EvidenceError, "außerhalb"):
            check_case(case, catalog, manifest, ROOT)
        case["as_of"] = "2020-07-01"
        check_case(case, catalog, manifest, ROOT)
        del manifest["captures"]["za-commencement.pdf"]
        with self.assertRaisesRegex(EvidenceError, "Nachweis fehlt"):
            check_case(case, catalog, manifest, ROOT)
