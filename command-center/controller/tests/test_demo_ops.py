"""DEMO – not a research result. Tests for the allowlisted interview-demo controller action."""
from __future__ import annotations

import json
import sys
import threading
import time
import unittest
from pathlib import Path

from controller import demo_ops as DEMO
from controller.tests.test_controller import Base, make_fake_repo, ALLOW_ALL


class DemoOpsUnit(unittest.TestCase):
    def test_sanitize_strips_local_paths(self):
        doc = {"label": "x", "note": "/" + "workspace/secret/path", "_paths": {"json": "/tmp/x"}}
        out = DEMO.sanitize_doc(doc)
        self.assertEqual(out["label"], DEMO.LABEL)
        self.assertTrue(out["publication_safe"])
        self.assertNotIn("_paths", out)
        blob = json.dumps(out)
        self.assertNotIn("/" + "workspace", blob)
        self.assertIn("<local-path>", blob)

    def test_confirm_required(self):
        class Fake:
            cfg = {}
            env = {}
            lock = threading.Lock()
            run = {"state": "idle"}
            pipeline = type("P", (), {"lock": threading.Lock(), "current": None})()
            models = type("M", (), {"puller": type("Pu", (), {"busy": staticmethod(lambda: False)})()})()

            def audit(self, *a, **k):
                pass

        r = DEMO.DemoRunner(Fake())
        code, res = r.start({"confirm": "nope"})
        self.assertEqual(code, 400)
        self.assertIn("DEMO", res["label"])


class DemoRunnerIntegration(Base):
    def setUp(self):
        super().setUp()
        self.demo = self.td / "demo-wt"
        pkg = self.demo / "demo" / "aivd_interview"
        (pkg / "reports").mkdir(parents=True)
        (pkg / "run_demo.py").write_text("# placeholder for config check\n")
        (self.demo / "demo" / "__init__.py").write_text("")
        (pkg / "__init__.py").write_text("LABEL = 'DEMO – not a research result'\n")
        (pkg / "__main__.py").write_text(
            "import json, pathlib\n"
            "out = pathlib.Path(__file__).resolve().parent / 'reports'\n"
            "out.mkdir(exist_ok=True)\n"
            "doc = {'label': 'DEMO – not a research result', 'demo_id': 't',\n"
            " 'mode_used': {'models': 'deterministic_only_fallback', 'models_run': []},\n"
            " 'per_target_summary': [{'target': 'avatar_store', 'planted': True,\n"
            "   'deterministic': {'verified': True, 'status': 'VERIFIED'}, 'models': []}],\n"
            " 'honesty': 'stub'}\n"
            "(out / 'latest.json').write_text(json.dumps(doc))\n"
            "(out / 'EXPLAINER.md').write_text('# DEMO – not a research result\\n')\n"
            "print(json.dumps({'ok': True}))\n"
        )
        self.cc = self.td / "cc"
        (self.cc / "public-data" / "demo").mkdir(parents=True)
        make_fake_repo(self.repo, guard_state=ALLOW_ALL)

    def test_missing_confirm_and_missing_worktree(self):
        c = self.ctl()
        code, res = c.demo.start({"confirm": DEMO.DEMO_CONFIRM})
        self.assertEqual(code, 503)
        self.assertIn("DEMO", res["label"])

    def test_op_start_writes_report(self):
        c = self.ctl(demo_worktree=str(self.demo), cc_dir=str(self.cc))
        c.python = sys.executable
        # Controller stores python on self.python via __init__ arg
        c.python = sys.executable
        code, res = c.demo.start({"confirm": "no"})
        self.assertEqual(code, 400)
        code, res = c.demo.start({"confirm": DEMO.DEMO_CONFIRM})
        self.assertEqual(code, 202, res)
        for _ in range(100):
            if c.demo.status()["state"] != "running":
                break
            time.sleep(0.05)
        st = c.demo.status()
        self.assertEqual(st["state"], "completed", st)
        latest = c.demo.get_latest()
        self.assertIsNotNone(latest)
        self.assertIn("DEMO", latest["label"])
        mirrored = self.cc / "public-data" / "demo" / "latest.json"
        self.assertTrue(mirrored.is_file())
        self.assertIn("DEMO", mirrored.read_text())
        # status payload exposes demo
        st_doc = c.status()
        self.assertIn("run_demo", st_doc["ops"])
        self.assertTrue(st_doc["ops"]["run_demo"]["available"])
        self.assertEqual(st_doc["demo"]["state"], "completed")


if __name__ == "__main__":
    unittest.main()
