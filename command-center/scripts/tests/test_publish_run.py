"""publish_run.py: the published copy of a run record carries no log, local paths, host names or pids, and the
committed public-data/runs files pass the same checks."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import publish_run as PR  # noqa: E402

WS = "/" + "workspace"          # assembled so this file holds no literal local path
HOMEBOX = "/home" + "/box"
VARTMP = "/var" + "/tmp"
HOST = "boxhost-7f3a"
RID = "r20261011T144715-c8b1d0"


def run_doc(**over):
    doc = {
        "schema": 1, "id": RID, "started_at": "2026-10-11T14:47:15+00:00", "finished_at": "2026-10-11T14:49:21+00:00",
        "state": "completed", "_t0": 123.4, "options": {"full_suite": True, "model_id": "qwen3:1.7b"},
        "limits": {"step_timeout_s": 1200, "total_timeout_s": 3600}, "total_duration_s": 126.0,
        "log": [{"t": 0.1, "step": "preflight", "line": f"cwd {WS}/aivd-rc6-diag on {HOST} pid 4242"}],
        "log_total": 1,
        "steps": [
            {"id": "preflight", "label": "Environment preflight", "status": "FAIL", "pid": 99,
             "reason": f"runtime file missing: {VARTMP}/ollama-v0344/extract/ollama", "started_at": None, "ended_at": None,
             "duration_s": 0.1, "details": {"state_dir": f"{HOMEBOX}/.local/state/x", "hostname": HOST,
                                            "argv": ["python", "-m", "pytest"], "note": f"ran on {HOST}.local",
                                            "worktrees": [{"name": "rc6-diag", "path": f"{WS}/aivd-rc6-diag"}],
                                            "other": "C:\\Users\\op\\aivd\\x.json and ~/aivd/state/y.json"}},
            {"id": "cc_tests", "label": "Command Center tests", "status": "PASS", "reason": "vitest 70 passed",
             "started_at": None, "ended_at": None, "duration_s": 70.0,
             "details": {"vitest": {"counts": {"passed": 70}}, "python": {"counts": {"passed": 128, "failed": 0}},
                         "suites": ["tests/rc6_diag"], "failing_historical": ["tests/rc5_gen/test_design.py::t"]}},
        ],
        "verdict": {"overall": "FAIL", "headline": "Software built: PASS; branch origin/main",
                    "note": "n", "lifecycle": [{"id": f"s{i}", "label": f"S{i}", "value": "NO"} for i in range(7)]},
    }
    doc.update(over)
    return doc


class SanitizeTests(unittest.TestCase):
    def test_drops_log_pids_hosts_paths_and_local_keys(self):
        out = PR.sanitize(run_doc(), "research computer", hosts={HOST})
        blob = json.dumps(out)
        for bad in (WS, HOMEBOX, VARTMP, HOST, "4242", "Users", "~/aivd", '"pid"', "state_dir", "argv", "_t0", "log_total"):
            self.assertNotIn(bad, blob, bad)
        self.assertEqual(out["log"], [])
        self.assertTrue(out["published"]["sanitized"])
        self.assertEqual(out["published"]["source"], "research computer")
        pre = out["steps"][0]
        self.assertNotIn("pid", pre)
        self.assertEqual(pre["reason"], "runtime file missing: <path>")
        self.assertNotIn("worktrees", pre["details"])

    def test_keeps_what_the_results_view_needs(self):
        out = PR.sanitize(run_doc(), "research computer", hosts={HOST})
        cc = out["steps"][1]["details"]
        self.assertEqual(cc["python"]["counts"], {"passed": 128, "failed": 0})
        self.assertEqual(cc["suites"], ["tests/rc6_diag"])                      # relative test ids are kept
        self.assertEqual(cc["failing_historical"], ["tests/rc5_gen/test_design.py::t"])
        self.assertEqual(out["verdict"]["headline"], "Software built: PASS; branch origin/main")
        self.assertEqual(len(out["verdict"]["lifecycle"]), 7)

    def test_refuses_incomplete_or_foreign_records(self):
        for bad in (run_doc(state="running"), run_doc(verdict=None), run_doc(id="../x"), [], {"id": RID}):
            with self.subTest(bad=str(bad)[:40]), self.assertRaises(PR.Refused):
                PR.sanitize(bad, "research computer", hosts=set())

    def test_check_flags_residue(self):
        self.assertIn("L_local_path", PR.check({"x": WS + "/a"}, set()))
        self.assertIn("H_hostname", PR.check({"x": "on " + HOST}, {HOST}))
        self.assertIn("P_pid", PR.check({"pid": 3}, set()))
        self.assertIn("G_raw_log", PR.check({"log": [{"line": "x"}]}, set()))
        self.assertEqual(PR.check({"x": "tests/a.py::b origin/main 127.0.0.1:8765"}, set()), set())

    def test_publish_writes_run_latest_and_newest_first_index(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            older = run_doc(id="r20261010T101010-aaaaaa", started_at="2026-10-10T10:10:10+00:00")
            PR.publish(run_doc(), d, "research computer", hosts=set())
            res = PR.publish(older, d, "research computer", hosts=set())
            self.assertEqual(res["latest"], RID)                                 # an older run never becomes latest
            idx = json.loads((d / "index.json").read_text())
            self.assertEqual([r["id"] for r in idx["runs"]], [RID, "r20261010T101010-aaaaaa"])
            self.assertEqual((d / "latest.json").read_text(), (d / f"{RID}.json").read_text())
            self.assertEqual(idx["runs"][0]["file"], f"runs/{RID}.json")


class CommittedRunsTests(unittest.TestCase):
    RUNS = HERE.parent / "public-data" / "runs"

    @unittest.skipUnless((HERE.parent / "public-data" / "runs" / "index.json").is_file(), "no published runs")
    def test_committed_published_runs_pass_the_checks(self):
        idx = json.loads((self.RUNS / "index.json").read_text())
        self.assertEqual(PR.check(idx, set()), set())
        for f in self.RUNS.glob("r*.json"):
            d = json.loads(f.read_text())
            self.assertEqual(PR.check(d, set()), set(), f.name)
            self.assertEqual(d["log"], [])
            self.assertEqual(f.stem, d["id"])
        self.assertEqual(json.loads((self.RUNS / "latest.json").read_text())["id"], idx["latest"])


if __name__ == "__main__":
    unittest.main()
