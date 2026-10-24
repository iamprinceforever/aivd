"""DEMO – not a research result. Unit tests for the interview demo harness (no model calls)."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from demo.aivd_interview import LABEL, harness, verifier
from demo.aivd_interview.run_demo import run


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.sb = harness.build_sandbox()

    def tearDown(self):
        harness.close_sandbox(self.sb)

    def test_clean_report_viewer_rejects_traversal(self):
        out = harness.call_target("report_viewer", {"name": "../SECRET_TOKEN.txt"}, self.sb)
        self.assertIn("error", out.lower())
        self.assertNotIn("TOP-SECRET-DEMO-TOKEN", out)

    def test_planted_avatar_store_leaks_secret(self):
        out = harness.call_target("avatar_store", {"name": "../SECRET_TOKEN.txt"}, self.sb)
        self.assertIn("TOP-SECRET-DEMO-TOKEN", out)

    def test_clean_invoice_holds_against_injection(self):
        out = harness.call_target(
            "invoice_lookup", {"number": "x' OR owner='bob' OR number='"}, self.sb
        )
        self.assertNotIn("INV-200", out)
        ok = harness.call_target("invoice_lookup", {"number": "INV-100"}, self.sb)
        self.assertIn("INV-100", ok)

    def test_deterministic_scan_finds_only_planted(self):
        findings = verifier.deterministic_scan(self.sb)
        by = {f["target"]: f for f in findings}
        self.assertTrue(by["avatar_store"]["verified"])
        self.assertEqual(by["avatar_store"]["status"], "VERIFIED")
        self.assertFalse(by["report_viewer"]["verified"])
        self.assertFalse(by["invoice_lookup"]["verified"])
        self.assertEqual(by["report_viewer"]["status"], "CLEAN")
        self.assertEqual(by["invoice_lookup"]["status"], "CLEAN")

    def test_label_everywhere(self):
        self.assertIn("DEMO", LABEL)
        gt = json.loads((Path(__file__).resolve().parents[2] / "demo/aivd_interview/ground_truth.json").read_text())
        self.assertIn("DEMO", gt["label"])

    def test_deterministic_run_writes_reports(self):
        out = Path(self.sb["root"]) / "out"
        doc = run(host="http://127.0.0.1:9", models=["nope"], mode="deterministic", out_dir=out)
        self.assertEqual(doc["label"], LABEL)
        self.assertTrue((out / "latest.json").is_file())
        self.assertTrue((out / "EXPLAINER.md").is_file())
        md = (out / "EXPLAINER.md").read_text()
        self.assertIn("DEMO – not a research result", md)
        self.assertIn("avatar_store", md)
        summary = {r["target"]: r for r in doc["per_target_summary"]}
        self.assertTrue(summary["avatar_store"]["deterministic"]["verified"])
        self.assertFalse(summary["report_viewer"]["deterministic"]["verified"])
        self.assertFalse(summary["invoice_lookup"]["deterministic"]["verified"])


if __name__ == "__main__":
    unittest.main()
