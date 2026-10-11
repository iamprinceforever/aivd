"""One-click pipeline tests. Every external command is MOCKED (fake run_cmd); the RC6 Part B handoff is a mock.
Nothing here runs pytest on the research repo, starts Ollama, or invokes scripts/rc6_partb_run.py."""
import json
import os
import stat
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path

from controller import pipeline as PL
from controller import server as S
from controller.tests.test_controller import ALLOW_ALL, WS, FAKE_PAT, Base, HttpTests, make_fake_repo

HIST = list(PL.HISTORICAL_FAILURES)


def fake_specs(avail, total=16_000_000):
    return {"mem_total_kb": total, "mem_available_kb": avail, "swap_total_kb": 0, "rc6_memory_gate_kb": 7_600_000,
            "rc6_memory_gate_met": avail >= 7_600_000, "cpu_count": 8, "cpu_model": "test cpu",
            "gpu": {"present": False, "kinds": [], "render_nodes": 0}, "balloon": True, "notes": []}


class FakeCmd:
    """Records every argv/env and returns canned output per (fixed) command kind."""

    def __init__(self, pytest_lines=None, pytest_timeout=False, sleep=0.0, on_pytest=None, vitest_ok=True):
        self.calls = []
        self.pytest_lines = pytest_lines if pytest_lines is not None else ["....", "== 120 passed, 2 skipped in 3.1s =="]
        self.pytest_timeout = pytest_timeout
        self.sleep = sleep
        self.on_pytest = on_pytest
        self.vitest_ok = vitest_ok
        self.lock = threading.Lock()

    def __call__(self, argv, cwd, env, timeout, on_line):
        with self.lock:
            self.calls.append({"argv": list(argv), "cwd": cwd, "env": dict(env), "timeout": timeout})
        joined = " ".join(argv)
        if argv[1:3] == ["-c", "import pytest"]:
            return 0, [], False
        if "pytest" in argv:
            if self.sleep:
                time.sleep(self.sleep)
            if self.on_pytest:
                self.on_pytest()
            lines = [ln + "\n" for ln in self.pytest_lines]
            for ln in lines:
                on_line(ln)
            return (1 if any(l.startswith("FAILED") for l in self.pytest_lines) else 0), lines, self.pytest_timeout
        if "vitest.mjs" in joined:
            lines = [" Test Files  7 passed (7)\n", "      Tests  44 passed (44)\n"] if self.vitest_ok else \
                ["      Tests  1 failed | 43 passed (44)\n"]
            return (0 if self.vitest_ok else 1), lines, False
        if "unittest" in argv:
            return 0, ["Ran 5 tests in 0.1s\n", "OK\n"], False
        if "scripts/scan_outgoing.py" in argv:
            return 0, [json.dumps({"files_scanned": 10, "files_with_hits": 0, "hit_counts": {}, "pass": True,
                                   "prior_seal_scan": {"state": "not supplied"}}) + "\n"], False
        return 1, [], False


class PipelineBase(Base):
    def setUp(self):
        super().setUp()
        self.cc = self.td / "cc"
        (self.cc / "node_modules" / "vitest").mkdir(parents=True)
        (self.cc / "node_modules" / "vitest" / "vitest.mjs").write_text("// fake")
        (self.repo / "tests" / "rc6_diag").mkdir(parents=True)
        (self.repo / "tests" / "rc6_run").mkdir(parents=True)

    def pctl(self, env=None, mem=6_640_000, guard_state=None, fake=None, handoff=None, **kw):
        self.marker = make_fake_repo(self.repo, guard_state=guard_state)
        c = S.Controller(self.cfg(test_python=sys.executable, cc_dir=str(self.cc), node=sys.executable, **kw),
                         env={} if env is None else env, meminfo=lambda: mem, proc_check=lambda: False)
        self.fake = fake or FakeCmd()
        self.handoffs = []

        def mock_handoff(model, attempt):
            self.handoffs.append((model, attempt))
            return 202, {"status": "STARTED"}
        c.pipeline = PL.Pipeline(c, run_cmd=self.fake, partb_handoff=handoff or mock_handoff)
        c.models.specs = lambda: fake_specs(mem)     # never read the real /proc in tests
        return c

    def run_to_end(self, c, **opts):
        body = {"full_suite": False, "partb_confirm": "", "model_id": "", "attempt_id": "", "auto_pull": False}
        body.update(opts)
        code, res = c.pipeline.start(body)
        self.assertEqual(code, 202, res)
        c.pipeline.thread.join(timeout=60)
        self.assertFalse(c.pipeline.thread.is_alive())
        return c.pipeline.get(res["run_id"])

    def step(self, doc, sid):
        return next(s for s in doc["steps"] if s["id"] == sid)


class FixedSequenceTests(PipelineBase):
    def test_unittest_skips_are_not_counted_as_failures(self):
        class Fk(FakeCmd):
            def __call__(self, argv, cwd, env, timeout, on_line):
                if "unittest" in argv:
                    return 1, ["Ran 10 tests in 0.1s\n", "FAILED (failures=1, errors=1, skipped=3)\n"], False
                return super().__call__(argv, cwd, env, timeout, on_line)
        c = self.pctl(fake=Fk())
        doc = self.run_to_end(c)
        py = self.step(doc, "cc_tests")["details"]["python"]["counts"]
        self.assertEqual(py, {"passed": 16, "failed": 4})          # 2 suites x (1 failure + 1 error); skips ignored

    def test_fixed_step_list_and_statuses(self):
        c = self.pctl()
        doc = self.run_to_end(c)
        self.assertEqual([s["id"] for s in doc["steps"]],
                         ["preflight", "guard", "rc6_tests", "full_suite", "cc_tests", "scans", "model", "partb", "summary"])
        for s in doc["steps"]:
            self.assertIn(s["status"], PL.STATUSES)
            self.assertIsInstance(s["duration_s"], float)
            self.assertTrue(s["reason"])
            self.assertTrue(s["started_at"] and s["ended_at"])
        self.assertEqual(self.step(doc, "full_suite")["status"], "SKIPPED")
        self.assertEqual(self.step(doc, "preflight")["status"], "FAIL")          # 6.64 GB < 7.6 GB gate
        self.assertIn("6640000 kB < 7600000 kB", self.step(doc, "preflight")["reason"])
        self.assertEqual(self.step(doc, "guard")["status"], "BLOCKED")
        self.assertEqual(self.step(doc, "rc6_tests")["status"], "PASS")
        self.assertEqual(self.step(doc, "cc_tests")["status"], "PASS")
        self.assertEqual(doc["state"], "completed")
        self.assertIsInstance(doc["total_duration_s"], float)

    def test_pytest_argv_is_fixed_safe_and_ignores_client_values(self):
        c = self.pctl(env={"AIVD_RC6_AUTHORIZE_MODEL_CALL": "x", "AIVD_POST_RC3_LOCAL_RUN_AUTHORIZED": "y",
                           "PYTEST_ADDOPTS": "--evil", "PATH": os.environ.get("PATH", "")})
        code, _ = c.pipeline.start({"full_suite": True, "partb_confirm": "", "model_id": "qwen3:8b; rm -rf ~",
                                    "attempt_id": "../../x", "auto_pull": True})
        self.assertEqual(code, 400)                                   # non-catalog model ids never start a run
        self.run_to_end(c, full_suite=True, model_id="qwen3:8b", attempt_id="../../x")
        py = [k for k in self.fake.calls if "pytest" in k["argv"]]
        self.assertEqual(len(py), 2)                                  # rc6 suites + full suite
        for call in self.fake.calls:
            self.assertNotIn("rm -rf", " ".join(call["argv"]))
            self.assertNotIn("../../x", " ".join(call["argv"]))
            self.assertFalse([k for k in call["env"] if "AUTHORI" in k.upper()], call["argv"])
            self.assertNotIn("PYTEST_ADDOPTS", call["env"])
            self.assertEqual(call["env"]["PYTHONDONTWRITEBYTECODE"], "1")
        a = py[0]["argv"]
        self.assertEqual(a[:9], [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=no", "-rfE",
                                 "--color=no"])
        self.assertEqual(a[9:11], ["tests/rc6_diag", "tests/rc6_run"])          # only suites that exist
        self.assertIn("tests/post_rc3_local/test_runner_entrypoint.py", a)
        for tid, reason in PL.EXCLUDED_TESTS:
            self.assertIn(tid, a)
            self.assertTrue(reason)
        self.assertEqual(py[1]["argv"][9], "tests")

    def test_http_client_cannot_inject_steps_or_args(self):
        bad = [{"steps": ["x"]}, {"full_suite": False, "partb_confirm": "", "model_id": "", "attempt_id": "", "auto_pull": False,
                                    "command": "id"},
               {"full_suite": "yes", "partb_confirm": "", "model_id": "", "attempt_id": "", "auto_pull": False},
               {"full_suite": 1, "partb_confirm": "", "model_id": "", "attempt_id": "", "auto_pull": False},
               {"full_suite": False, "partb_confirm": "x" * 121, "model_id": "", "attempt_id": "", "auto_pull": False},
               {"full_suite": False, "partb_confirm": True, "model_id": "", "attempt_id": "", "auto_pull": False},
               {"full_suite": False, "partb_confirm": "", "model_id": "", "attempt_id": "", "auto_pull": False, "cwd": "/"}]
        for b in bad:
            with self.subTest(b=b):
                self.assertIsNotNone(S.validate_body("/api/ops/run_pipeline", b))
        self.assertIsNone(S.validate_body("/api/ops/run_pipeline", {"full_suite": True, "partb_confirm": "",
                                                                    "model_id": "", "attempt_id": "", "auto_pull": False}))


class TimeoutConcurrencyTests(PipelineBase):
    def test_step_timeout_is_error_and_pipeline_continues(self):
        c = self.pctl(fake=FakeCmd(pytest_timeout=True))
        doc = self.run_to_end(c)
        self.assertEqual(self.step(doc, "rc6_tests")["status"], "ERROR")
        self.assertIn("timeout", self.step(doc, "rc6_tests")["reason"])
        self.assertEqual(self.step(doc, "cc_tests")["status"], "PASS")
        self.assertEqual(doc["verdict"]["overall"], "ERROR")

    def test_total_timeout_skips_remaining_steps(self):
        c = self.pctl(fake=FakeCmd(sleep=1.5))
        c.pipeline.total_timeout = 1
        doc = self.run_to_end(c)
        st = {s["id"]: s["status"] for s in doc["steps"]}
        for sid in ("cc_tests", "scans", "partb"):
            self.assertEqual(st[sid], "SKIPPED", st)
        self.assertEqual(self.step(doc, "scans")["reason"], "total pipeline timeout reached before this step")
        self.assertIn(st["summary"], PL.STATUSES)

    def test_real_run_cmd_kills_process_group_on_timeout(self):
        c = self.pctl()
        t0 = time.time()
        rc, lines, to = c.pipeline._run_cmd([sys.executable, "-c", "print('hi', flush=True); import time; time.sleep(60)"],
                                            str(self.td), {"PATH": os.environ.get("PATH", "")}, 1, lambda ln: None)
        self.assertTrue(to)
        self.assertLess(time.time() - t0, 20)
        self.assertEqual(lines[0], "hi\n")              # SIGINT reaches the child (KeyboardInterrupt traceback follows)
        self.assertEqual(c.pipeline.last_stop_signal, "SIGINT")

    def test_one_pipeline_at_a_time_and_not_during_rc6_run(self):
        c = self.pctl(fake=FakeCmd(sleep=1.0))
        body = {"full_suite": False, "partb_confirm": "", "model_id": "", "attempt_id": "", "auto_pull": False}
        code, res = c.pipeline.start(body)
        self.assertEqual(code, 202)
        code2, res2 = c.pipeline.start(body)
        self.assertEqual(code2, 409)
        self.assertEqual(res2["run_id"], res["run_id"])
        c.pipeline.thread.join(timeout=60)
        c2 = self.pctl()
        c2.run = {"state": "running", "op": "rc6_run", "started": time.time()}
        self.assertEqual(c2.pipeline.start(body)[0], 409)


class RedactionHistoryTests(PipelineBase):
    def test_log_lines_redacted_and_outcome_lines_withheld(self):
        o5 = "fun" + "nel"
        lines = [f"path {WS}/aivd-rc6-diag/x.py", f"token {FAKE_PAT}", "hash " + "ab" * 32,
                 f"the baseline {o5} counts", "== 3 passed in 0.1s =="]
        c = self.pctl(fake=FakeCmd(pytest_lines=lines))
        doc = self.run_to_end(c)
        text = json.dumps(doc)
        self.assertNotIn(WS + "/", text)
        self.assertNotIn(FAKE_PAT, text)
        self.assertNotIn("ab" * 32, text)
        self.assertNotIn(o5, text.lower())
        self.assertIn("<line withheld: matched an outcome pattern>", text)
        persisted = (self.state / "runs" / f"{doc['id']}.json").read_text()
        self.assertNotIn(WS + "/", persisted)
        self.assertNotIn(FAKE_PAT, persisted)

    def test_log_cap(self):
        c = self.pctl(fake=FakeCmd(pytest_lines=["x"] * (PL.MAX_LOG_LINES + 500) + ["== 1 passed in 1s =="]))
        doc = self.run_to_end(c)
        self.assertLessEqual(len(doc["log"]), PL.MAX_LOG_LINES + 1)
        self.assertGreater(doc["log_total"], PL.MAX_LOG_LINES)

    def test_history_persisted_private_outside_git_and_reloaded(self):
        c = self.pctl()
        doc = self.run_to_end(c)
        p = self.state / "runs" / f"{doc['id']}.json"
        self.assertTrue(p.exists())
        self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o600)
        c2 = self.pctl()
        hist = c2.pipeline.history()
        self.assertEqual(hist[0]["id"], doc["id"])
        self.assertEqual(len(hist[0]["steps"]), len(PL.STEP_DEFS))
        self.assertIsNone(c2.pipeline.get("../../etc/passwd"))
        self.assertEqual(c2.pipeline.get(doc["id"], since=2)["log_offset"], 2)
        audit = (self.state / "audit.jsonl").read_text()
        self.assertIn("run_pipeline", audit)

    def test_worktree_change_during_tests_fails_step(self):
        wt = self.td / "wt"
        wt.mkdir()
        subprocess.run(["git", "init", "-q", str(wt)], check=True)
        subprocess.run(["git", "-C", str(wt), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
                        "--allow-empty", "-m", "i"], check=True)
        fake = FakeCmd(on_pytest=lambda: (wt / "new.txt").write_text("x"))
        c = self.pctl(fake=fake, worktrees={"rc6-diag": str(wt)})
        doc = self.run_to_end(c)
        s = self.step(doc, "rc6_tests")
        self.assertEqual(s["status"], "FAIL")
        self.assertIn("rc6-diag", s["reason"])
        self.assertFalse(s["details"]["worktrees_unchanged"])


class ClassificationTests(PipelineBase):
    def test_historical_failures_labelled_not_counted_as_new(self):
        lines = [f"FAILED {h}" for h in HIST] + ["== 4 failed, 1112 passed, 4 skipped, 2 xfailed in 32.2s =="]
        c = self.pctl(fake=FakeCmd(pytest_lines=lines))
        doc = self.run_to_end(c, full_suite=True)
        s = self.step(doc, "full_suite")
        self.assertEqual(s["status"], "PASS")
        self.assertEqual(s["details"]["failing_historical"], HIST)
        self.assertEqual(s["details"]["failing_new"], [])
        self.assertEqual(s["details"]["counts"], {"failed": 4, "passed": 1112, "skipped": 4, "xfailed": 2})
        self.assertIn("pre-existing/historical", s["reason"])

    def test_new_failure_fails_step(self):
        lines = ["FAILED tests/rc6_run/test_x.py::test_new", "== 1 failed, 10 passed in 1s =="]
        c = self.pctl(fake=FakeCmd(pytest_lines=lines))
        doc = self.run_to_end(c)
        s = self.step(doc, "rc6_tests")
        self.assertEqual(s["status"], "FAIL")
        self.assertEqual(s["details"]["failing_new"], ["tests/rc6_run/test_x.py::test_new"])

    def test_cc_test_failure(self):
        c = self.pctl(fake=FakeCmd(vitest_ok=False))
        self.assertEqual(self.step(self.run_to_end(c), "cc_tests")["status"], "FAIL")

    def test_missing_test_python_is_error(self):
        c = self.pctl()
        c.cfg = dict(c.cfg)
        c.cfg.pop("test_python")
        doc = self.run_to_end(c)
        self.assertEqual(self.step(doc, "rc6_tests")["status"], "ERROR")


class PartBTests(PipelineBase):
    def test_partb_blocked_with_every_open_gate_and_exact_reasons(self):
        c = self.pctl(env={S.PARTB_ENV: "set-by-operator"})
        doc = self.run_to_end(c, partb_confirm=S.RUN_CONFIRM, model_id="qwen3:8b", attempt_id="a1")
        s = self.step(doc, "partb")
        self.assertEqual(s["status"], "BLOCKED")
        ids = {i["id"]: i for i in s["details"]["checklist"]}
        for gid in ("PREREG_APPROVAL", "OSF_REGISTRATION", "G_AUDIT", "MEMORY"):
            self.assertEqual(ids[gid]["state"], "FAIL", gid)
            self.assertTrue(ids[gid]["fix"])
        self.assertIn("no APPROVED RC6_APPROVALS.json", ids["PREREG_APPROVAL"]["reasons"])
        self.assertIn("G_AUDIT: historical protected-path audit is not resolved", ids["G_AUDIT"]["reasons"])
        self.assertIn("Ollama not started", s["reason"])
        self.assertFalse(s["details"]["ollama_started"])
        self.assertEqual(self.handoffs, [])
        self.assertFalse(self.marker.exists())
        v = doc["verdict"]
        self.assertFalse(v["experiment_ran"])
        self.assertIn("Authorized: NO", v["headline"])
        self.assertIn("Experiment: NOT RUN", v["headline"])
        life = {x["id"]: x for x in v["lifecycle"]}
        self.assertNotIn("MODEL_ATTEMPT", life["prerequisites_satisfied"]["open"])
        self.assertNotIn("CONFIRM_PHRASE", life["prerequisites_satisfied"]["open"])
        self.assertIn("G_AUDIT", life["prerequisites_satisfied"]["open"])
        self.assertIn("MEMORY", life["prerequisites_satisfied"]["open"])
        self.assertIn("PREREG_APPROVAL", life["explicitly_authorized"]["open"])
        for word in ("ready", "succeeded"):
            self.assertNotIn(word, v["headline"].lower())

    def test_partb_blocked_without_operator_env_even_when_guard_allows(self):
        c = self.pctl(env={}, mem=8_000_000, guard_state=ALLOW_ALL)
        doc = self.run_to_end(c, partb_confirm=S.RUN_CONFIRM, model_id="qwen3:8b", attempt_id="a1")
        s = self.step(doc, "partb")
        self.assertEqual(s["status"], "BLOCKED")
        self.assertIn(S.PARTB_ENV, s["reason"])
        self.assertEqual(self.handoffs, [])

    def test_partb_blocked_without_phrase_or_with_wrong_phrase(self):
        for phrase in ("", S.RUN_CONFIRM.lower()):
            with self.subTest(phrase=phrase):
                c = self.pctl(env={S.PARTB_ENV: "x"}, mem=8_000_000, guard_state=ALLOW_ALL)
                doc = self.run_to_end(c, partb_confirm=phrase, model_id="qwen3:8b", attempt_id="a1")
                s = self.step(doc, "partb")
                self.assertEqual(s["status"], "BLOCKED")
                self.assertIn("confirmation phrase", s["reason"])
                self.assertEqual(self.handoffs, [])

    def test_partb_blocked_with_bad_model_or_attempt(self):
        for model, attempt in (("qwen3:4b", "a1"), ("qwen3:8b", "../x"), ("", "")):
            with self.subTest(model=model, attempt=attempt):
                c = self.pctl(env={S.PARTB_ENV: "x"}, mem=8_000_000, guard_state=ALLOW_ALL)
                doc = self.run_to_end(c, partb_confirm=S.RUN_CONFIRM, model_id=model, attempt_id=attempt)
                self.assertEqual(self.step(doc, "partb")["status"], "BLOCKED")
                self.assertEqual(self.handoffs, [])

    def test_mocked_handoff_only_with_all_gates_env_and_phrase(self):
        c = self.pctl(env={S.PARTB_ENV: "x"}, mem=8_000_000, guard_state=ALLOW_ALL)
        c.pipeline.step_model = lambda doc, ctx, dl: ("PASS", "stub: model installed and verified", {})
        doc = self.run_to_end(c, partb_confirm=S.RUN_CONFIRM, model_id="qwen3:8b", attempt_id="a1")
        s = self.step(doc, "partb")
        self.assertEqual(s["status"], "PASS", s["reason"])
        self.assertEqual(self.handoffs, [("qwen3:8b", "a1")])
        self.assertFalse(self.marker.exists())        # mocked: the real entry script never ran
        self.assertEqual(doc["verdict"]["lifecycle"][5]["value"], "NO")      # completed: NO
        self.assertFalse(doc["verdict"]["experiment_ran"])


class PipelineHttpTests(HttpTests):
    def setUp(self):
        super().setUp()
        self.c.pipeline = PL.Pipeline(self.c, run_cmd=FakeCmd(), partb_handoff=lambda m, a: self.fail("handoff"))

    def body(self):
        return {"full_suite": False, "partb_confirm": "", "model_id": "", "attempt_id": "", "auto_pull": False}

    def test_run_pipeline_requires_session_csrf_and_origin(self):
        st, _, _ = self.req("POST", "/api/ops/run_pipeline", self.body(), {"Origin": self.origin})
        self.assertEqual(st, 401)
        res = self.pair()
        st, _, _ = self.req("POST", "/api/ops/run_pipeline", self.body(), self.auth(res, csrf=False))
        self.assertEqual(st, 403)
        h = self.auth(res)
        h["Origin"] = "https://evil.example"
        st, _, _ = self.req("POST", "/api/ops/run_pipeline", self.body(), h)
        self.assertEqual(st, 403)
        st, _, _ = self.req("POST", "/api/ops/run_pipeline", dict(self.body(), steps=["x"]), self.auth(res))
        self.assertEqual(st, 400)
        st, out, _ = self.req("POST", "/api/ops/run_pipeline", self.body(), self.auth(res))
        self.assertEqual(st, 202)
        rid = out["run_id"]
        st, _, _ = self.req("GET", f"/api/runs/{rid}", headers={"Origin": self.origin})
        self.assertEqual(st, 401)
        self.c.pipeline.thread.join(timeout=60)
        st, doc, _ = self.req("GET", f"/api/runs/{rid}?since=1", headers=self.auth(res))
        self.assertEqual(st, 200)
        self.assertEqual(doc["log_offset"], 1)
        self.assertEqual(doc["state"], "completed")
        st, _, _ = self.req("GET", f"/api/runs/{rid}?cmd=x", headers=self.auth(res))
        self.assertEqual(st, 400)
        st, _, _ = self.req("GET", "/api/runs/r20990101T000000-abcdef", headers=self.auth(res))
        self.assertEqual(st, 404)
        st, hist, _ = self.req("GET", "/api/runs", headers=self.auth(res))
        self.assertEqual(hist["runs"][0]["id"], rid)
        st, status, _ = self.req("GET", "/api/status", headers=self.auth(res))
        self.assertTrue(status["pipeline"]["available"])
        self.assertEqual([s["id"] for s in status["pipeline"]["steps"]], [s for s, _ in PL.STEP_DEFS])


del HttpTests  # do not re-run the imported base HTTP tests in this module

if __name__ == "__main__":
    unittest.main()
