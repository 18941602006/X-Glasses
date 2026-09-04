"""Review-snapshot regression tests; never access network or edit the snapshot."""

import json
import unittest
from pathlib import Path

from tools.check_source_audit import validate


class SourceAuditTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "docs/dependencies/sources.audit.json"
        self.data = json.loads(path.read_text(encoding="utf-8"))

    def test_reviewed_snapshot(self):
        self.assertEqual(validate(self.data), [])

    def test_invalid_schema(self):
        self.assertTrue(validate([]))

    def test_empty_entries(self):
        self.data["entries"] = []
        self.assertTrue(validate(self.data))

    def test_duplicate_source(self):
        self.data["entries"].append(self.data["entries"][0].copy())
        self.assertTrue(any("duplicate" in error for error in validate(self.data)))

    def test_floating_revision(self):
        self.data["entries"][0]["revision"] = "main"
        self.assertTrue(any("immutable" in error for error in validate(self.data)))

    def test_unpinned_license_link(self):
        entry = self.data["entries"][0]
        entry["license"]["url"] = entry["license"]["url"].replace(entry["revision"], "main")
        self.assertTrue(any("pinned revision" in error for error in validate(self.data)))

    def test_fabricated_runtime_success(self):
        for value in (True, "false", None):
            with self.subTest(value=value):
                self.data["entries"][0]["runtime_verified"] = value
                self.assertTrue(any("runtime/import" in error for error in validate(self.data)))

    def test_evaluation_cannot_be_promoted_to_unrestricted_candidate(self):
        entry = next(e for e in self.data["entries"] if e["id"] == "locateanything-model")
        entry["disposition"] = "adapt_candidate"
        self.assertTrue(any("cannot be released" in error for error in validate(self.data)))

    def test_model_scope_cannot_be_silently_removed(self):
        self.data["entries"] = [e for e in self.data["entries"] if e["kind"] != "model"]
        self.assertTrue(any("source set" in error for error in validate(self.data)))

    def test_missing_gates(self):
        self.data["entries"][0]["gates"] = []
        self.assertTrue(any("gates" in error for error in validate(self.data)))

    def test_evaluation_requires_explicit_authorization(self):
        entry = next(e for e in self.data["entries"] if e["id"] == "locateanything-model")
        entry.pop("usage_authorization")
        self.assertTrue(any("evaluation authorization" in error for error in validate(self.data)))

    def test_commercial_use_not_authorized(self):
        entry = next(e for e in self.data["entries"] if e["id"] == "locateanything-model")
        entry["usage_authorization"]["production_or_commercial_use"] = True
        self.assertTrue(any("evaluation authorization" in error for error in validate(self.data)))


if __name__ == "__main__":
    unittest.main()
