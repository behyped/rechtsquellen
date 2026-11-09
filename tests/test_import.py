from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_case import ROOT, read_json, EvidenceError
from import_evidence import import_capture

class LocalImportTest(unittest.TestCase):
    def setUp(self):
        work = ROOT / "private/test-work"
        work.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=work)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.entry = read_json(ROOT / "docs/evidence/catalog-manifest.json")["captures"]["eu-gdpr-oj-en.pdf"]
        self.source = ROOT / self.entry["path"]
        self.entry["path"] = "private/evidence/test.pdf"

    def test_import_checks_hash_and_keeps_original_timestamp(self):
        before = deepcopy(self.entry)
        result = import_capture(self.root, self.entry, self.source)
        self.assertEqual(self.entry, before)
        self.assertEqual((self.root / result["path"]).read_bytes(), self.source.read_bytes())

    def test_import_rejects_wrong_bytes(self):
        self.entry["sha256"] = "0" * 64
        with self.assertRaisesRegex(EvidenceError, "Hash"):
            import_capture(self.root, self.entry, self.source)

    def test_import_rejects_escape_from_private(self):
        self.entry["path"] = "outside.pdf"
        with self.assertRaisesRegex(EvidenceError, "private/evidence"):
            import_capture(self.root, self.entry, self.source)
