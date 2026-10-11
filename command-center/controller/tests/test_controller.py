"""Controller tests. The research runner is ALWAYS mocked (fake guard + fake entry scripts in a temp dir), except
one read-only test that asks the repository's real aivd_rc6_guard for its status (skipped when absent)."""
import http.client
import json
import os
import socket
import stat
import sys
import tempfile
import textwrap
import threading
import time
import unittest
from pathlib import Path

from controller import server as S

REPO_ROOT = Path(__file__).resolve().parents[3]
WS = "/" + "workspace"            # assembled: the outgoing tree carries no literal local path
FAKE_PAT = "github" + "_pat_" + "A" * 24


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def make_fake_repo(td: Path, guard_state=None, run_exit=0, run_sleep=0.0, entry=True, reveal_entry=True,
                   guard=True, guard_garbage=False):
    (td / "scripts").mkdir(parents=True, exist_ok=True)
    marker = td / "RUNNER_WAS_EXECUTED"
    if guard:
        g = td / "aivd_rc6_guard"
        g.mkdir(exist_ok=True)
        (g / "__init__.py").write_text("")
        out = "print('not json')" if guard_garbage else textwrap.dedent(f"""
            import json, pathlib
            print(json.dumps(json.loads(pathlib.Path({str(td / 'guard_state.json')!r}).read_text())))
        """)
        (g / "__main__.py").write_text(out)
    acts = ("GENERATE_CORPUS", "CREATE_SECRET", "SEAL", "COMMIT_CORPUS", "START_RUNTIME", "MODEL_CALL", "REVEAL",
            "SCORE", "PUSH")
    state = {a: ["no APPROVED RC6_APPROVALS.json", "G_AUDIT: historical protected-path audit is not resolved"]
             for a in acts} if guard_state is None else guard_state
    (td / "guard_state.json").write_text(json.dumps(state))
    script = textwrap.dedent(f"""
        import json, pathlib, sys, time
        pathlib.Path({str(marker)!r}).write_text("x")
        time.sleep({run_sleep})
        print(json.dumps({{"status": "COMPLETE" if {run_exit} == 0 else "FAILED", "charged_calls": 0,
                           "failure": None, "note": {WS + "/secret/path"!r}}}))
        sys.exit({run_exit})
    """)
    if entry:
        (td / S.RUN_ENTRY).write_text(script)
    if reveal_entry:
        (td / S.REVEAL_ENTRY).write_text(script)
    return marker


ALLOW_ALL = {a: [] for a in ("START_RUNTIME", "MODEL_CALL", "REVEAL", "SCORE", "PUSH")}


class Base(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp(prefix="cc-ctl-test-"))
        self.repo = self.td / "repo"
        self.repo.mkdir()
        self.state = self.td / "state"
        self.rt = self.td / "runtime.bin"
        self.rt.write_bytes(b"runtime")
        import hashlib
        self.rt_sha = hashlib.sha256(b"runtime").hexdigest()

    def cfg(self, **kw):
        c = {"research_worktree": str(self.repo), "state_dir": str(self.state), "port": free_port(),
             "runtime_files": [{"name": "bin", "path": str(self.rt), "sha256": self.rt_sha}]}
        c.update(kw)
        return S.validate_config(c)

    def ctl(self, env=None, mem=8_000_000, proc=False, **kw):
        return S.Controller(self.cfg(**kw), env={} if env is None else env, meminfo=lambda: mem,
                            proc_check=lambda: proc)


class ConfigTests(Base):
    def test_invalid_configs_refuse(self):
        bad = [
            "x", {}, {"research_worktree": "relative"}, {"research_worktree": str(self.repo), "bogus": 1},
            {"research_worktree": str(self.repo), "port": 80},
            {"research_worktree": str(self.repo), "port": True},
            {"research_worktree": str(self.repo), "extra_origins": ["*"]},
            {"research_worktree": str(self.repo), "extra_origins": ["https://*.github.io"]},
            {"research_worktree": str(self.repo), "extra_origins": ["https://x.io/path"]},
            {"research_worktree": str(self.repo), "state_dir": str(self.repo / "st")},
            {"research_worktree": str(self.repo), "state_dir": "rel"},
            {"research_worktree": str(self.repo), "runtime_files": [{"name": "a", "path": "/x", "sha256": "zz"}]},
            {"research_worktree": str(self.repo), "runtime_files": [{"name": "a", "path": "rel", "sha256": "a" * 64}]},
            {"research_worktree": str(self.repo), "worktrees": {"a b": "/x"}},
            {"research_worktree": str(self.repo), "max_run_seconds": 1},
            {"research_worktree": str(self.td / "missing")},
        ]
        for b in bad:
            with self.subTest(b=b), self.assertRaises(S.ConfigError):
                S.validate_config(b)

    def test_main_refuses_bad_config(self):
        p = self.td / "c.json"
        p.write_text('{"research_worktree": "nope"}')
        self.assertEqual(S.main(["--config", str(p)]), 2)

    def test_example_config_is_placeholder_only(self):
        ex = json.loads((Path(S.__file__).parent / "config.example.json").read_text())
        self.assertEqual(set(ex) - set(S.CONFIG_KEYS), set())
        with self.assertRaises(S.ConfigError):
            S.validate_config(ex)


class GateTests(Base):
    def all_pass_ctl(self, **kw):
        marker = make_fake_repo(self.repo, guard_state=ALLOW_ALL, **kw)
        return self.ctl(env={S.PARTB_ENV: "operator-supplied"}), marker

    def body(self, model="qwen3:8b"):
        return {"model_id": model, "attempt_id": "a1", "confirm": S.RUN_CONFIRM}

    def test_default_guard_refuses_run_and_runner_never_executes(self):
        marker = make_fake_repo(self.repo)
        c = self.ctl(env={S.PARTB_ENV: "x"})
        code, res = c.op_run(self.body())
        self.assertEqual(code, 403)
        self.assertEqual(res["status"], "REFUSED")
        self.assertFalse(marker.exists())

    def test_reveal_refused_by_guard(self):
        marker = make_fake_repo(self.repo)
        code, res = self.ctl().op_reveal({"confirm": S.REVEAL_CONFIRM})
        self.assertEqual(code, 403)
        self.assertFalse(marker.exists())
        self.assertEqual({g["id"]: g["state"] for g in res["gates"]}["GUARD_REVEAL"], "FAIL")

    def test_each_gate_fails_closed(self):
        cases = {
            "GUARD_START_RUNTIME": dict(guard_state={**ALLOW_ALL, "START_RUNTIME": ["G_CORPUS: no committed corpus"]}),
            "GUARD_MODEL_CALL": dict(guard_state={**ALLOW_ALL, "MODEL_CALL": ["environment authorization absent"]}),
            "PARTB_ENV": dict(env={}),
            "MEMORY": dict(mem=6_640_000),
            "MEMORY_UNREADABLE": dict(mem=None),
            "RUNTIME_FILES": dict(rt_bad=True),
            "NO_FOREIGN_RUNTIME": dict(proc=True),
            "PROC_UNREADABLE": dict(proc=None),
            "ENTRY": dict(entry=False),
            "GUARD_MISSING": dict(guard=False),
            "GUARD_GARBAGE": dict(guard_garbage=True),
            "GUARD_MISSING_ACTION": dict(guard_state={"MODEL_CALL": []}),
        }
        for name, kw in cases.items():
            with self.subTest(gate=name):
                import shutil
                shutil.rmtree(self.repo)
                self.repo.mkdir()
                marker = make_fake_repo(self.repo, guard_state=kw.get("guard_state", ALLOW_ALL),
                                        entry=kw.get("entry", True), guard=kw.get("guard", True),
                                        guard_garbage=kw.get("guard_garbage", False))
                if kw.get("rt_bad"):
                    self.rt.write_bytes(b"tampered")
                c = self.ctl(env=kw.get("env", {S.PARTB_ENV: "x"}), mem=kw.get("mem", 8_000_000),
                             proc=kw.get("proc", False))
                code, res = c.op_run(self.body())
                self.assertEqual(code, 403, name)
                self.assertTrue(any(g["state"] != "PASS" for g in res["gates"]))
                time.sleep(0.05)
                self.assertFalse(marker.exists(), name)
                self.rt.write_bytes(b"runtime")

    def test_insufficient_memory_reason(self):
        c = self.ctl(mem=6_640_000)
        m = c.memory()
        self.assertEqual(m["state"], "FAIL")
        self.assertIn("6640000", m["reason"])

    def test_invalid_model_and_attempt_and_confirm(self):
        c, marker = self.all_pass_ctl()
        self.assertEqual(c.op_run(self.body("evil:latest"))[0], 400)
        self.assertEqual(c.op_run({**self.body(), "attempt_id": "../x"})[0], 400)
        self.assertEqual(c.op_run({**self.body(), "confirm": "yes"})[0], 400)
        self.assertEqual(c.op_reveal({"confirm": "yes"})[0], 400)
        self.assertFalse(marker.exists())

    def wait_done(self, c, t=15):
        end = time.time() + t
        while time.time() < end:
            if c.run["state"] != "running":
                return c.run
            time.sleep(0.05)
        self.fail("run did not finish")

    def test_mocked_runner_completion_failure_and_redaction(self):
        c, marker = self.all_pass_ctl()
        code, _ = c.op_run(self.body())
        self.assertEqual(code, 202)
        r = self.wait_done(c)
        self.assertEqual(r["state"], "completed")
        self.assertTrue(marker.exists())
        self.assertNotIn(WS, json.dumps(r))
        self.assertEqual(c.status()["lifecycle"]["completed"]["state"], "PASS")
        self.assertEqual(c.status()["lifecycle"]["independently_validated"]["state"], "NOT_VERIFIED")

    def test_mocked_runner_failure(self):
        c, _ = self.all_pass_ctl(run_exit=4)
        c.op_run(self.body())
        self.assertEqual(self.wait_done(c)["state"], "failed")

    def test_mocked_runner_entry_refusal_exit3(self):
        c, _ = self.all_pass_ctl(run_exit=3)
        c.op_run(self.body())
        self.assertEqual(self.wait_done(c)["state"], "refused")

    def test_mocked_runner_timeout_and_single_run(self):
        c, _ = self.all_pass_ctl(run_sleep=30)
        c.cfg["max_run_seconds"] = 1
        self.assertEqual(c.op_run(self.body())[0], 202)
        code, res = c.op_run(self.body())          # a second concurrent run is refused
        self.assertEqual(code, 403)
        self.assertIn("NO_ACTIVE_RUN", [g["id"] for g in res["gates"] if g["state"] != "PASS"])
        st = c.status()
        self.assertEqual(st["lifecycle"]["running"]["state"], "PASS")
        self.assertIn("no incremental progress", st["run"]["progress"])
        self.assertEqual(self.wait_done(c, 30)["state"], "timeout")

    def test_cancel_unavailable(self):
        self.assertFalse(self.ctl().status()["ops"]["cancel"]["available"])

    def test_lifecycle_never_authorized_without_operator_env(self):
        make_fake_repo(self.repo, guard_state=ALLOW_ALL)
        lc = self.ctl(env={}).status()["lifecycle"]
        self.assertEqual(lc["explicitly_authorized"]["state"], "FAIL")
        self.assertEqual(lc["software_built"]["state"], "PASS")
        self.assertEqual(lc["running"]["state"], "FAIL")

    def test_lifecycle_separates_prerequisites_from_authorization(self):
        make_fake_repo(self.repo)
        lc = self.ctl(env={}).status()["lifecycle"]
        self.assertTrue(any("G_AUDIT" in r for r in lc["prerequisites_satisfied"]["reasons"]))
        self.assertTrue(any("RC6_APPROVALS" in r for r in lc["explicitly_authorized"]["reasons"]))

    def test_controller_never_mutates_env(self):
        env = {S.PARTB_ENV: "x"}
        c, _ = self.all_pass_ctl()
        c.env = env
        c.status()
        c.op_run(self.body())
        self.wait_done(c)
        self.assertEqual(env, {S.PARTB_ENV: "x"})
        src = Path(S.__file__).read_text()
        for bad in ("os.environ[", "os.putenv", "environ.update", "setdefault(\"AIVD", "AIVD_RC6_AUTHORIZE_"):
            self.assertNotIn(bad, src)

    def test_never_mentions_starting_ollama(self):
        src = Path(S.__file__).read_text()
        self.assertNotIn("ollama serve", src)
        self.assertNotIn("11434", src)

    def test_audit_log_redacted_and_private(self):
        c = self.ctl()
        c.audit("x", "y", [WS + "/aivd/x", "token " + FAKE_PAT])
        txt = c.audit_path.read_text()
        self.assertNotIn(WS, txt)
        self.assertNotIn(FAKE_PAT, txt)
        self.assertEqual(stat.S_IMODE(c.audit_path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(c.pair_file.stat().st_mode), 0o600)
        e = c.audit_tail()
        self.assertEqual(len(e), 1)

    def test_worktree_status_counts_only(self):
        import subprocess
        wt = self.td / "wt"
        subprocess.run(["git", "init", "-q", str(wt)], check=True)
        subprocess.run(["git", "-C", str(wt), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                        "--allow-empty", "-m", "init"], check=True)
        (wt / "secret_name_RC5_outcome.md").write_text("x")
        c = self.ctl(worktrees={"w": str(wt)})
        out = json.dumps(c.worktrees())
        self.assertNotIn("secret_name", out)
        self.assertIn('"untracked": 1', out)


@unittest.skipUnless((REPO_ROOT / "aivd_rc6_guard" / "__init__.py").exists(), "real guard not in this checkout")
class RealGuardReadOnly(Base):
    def test_real_guard_refuses_run_and_reveal(self):
        c = S.Controller(S.validate_config({"research_worktree": str(REPO_ROOT), "state_dir": str(self.state),
                                            "port": free_port()}), env={}, meminfo=lambda: 9_000_000,
                         proc_check=lambda: False)
        g = c.guard()
        self.assertTrue(g["available"])
        self.assertTrue(g["actions"]["MODEL_CALL"])
        self.assertTrue(g["actions"]["REVEAL"])
        code, _ = c.op_run({"model_id": "qwen3:8b", "attempt_id": "t", "confirm": S.RUN_CONFIRM})
        self.assertEqual(code, 403)
        self.assertEqual(c.op_reveal({"confirm": S.REVEAL_CONFIRM})[0], 403)


class HttpTests(Base):
    def setUp(self):
        super().setUp()
        make_fake_repo(self.repo)
        ui = self.td / "dist"
        ui.mkdir()
        (ui / "index.html").write_text("<html>ui</html>")
        (self.td / "outside.json").write_text("{}")
        cfg = self.cfg(ui_dir=str(ui), extra_origins=["https://example.github.io"])
        self.port = cfg["port"]
        self.c = S.Controller(cfg, env={}, meminfo=lambda: 1, proc_check=lambda: False)
        self.httpd = S.ThreadingHTTPServer(("127.0.0.1", self.port), S.make_handler(self.c))
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.origin = f"http://127.0.0.1:{self.port}"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def req(self, method, path, body=None, headers=None, raw=None):
        h = {"Host": f"127.0.0.1:{self.port}"}
        h.update(headers or {})
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        if data is not None:
            h.setdefault("Content-Type", "application/json")
            h.setdefault("Content-Length", str(len(data)))
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        for k, v in h.items():
            conn.putheader(k, v)
        conn.endheaders()
        if data:
            conn.send(data)
        r = conn.getresponse()
        txt = r.read()
        hdrs = dict(r.getheaders())
        conn.close()
        try:
            return r.status, json.loads(txt), hdrs
        except ValueError:
            return r.status, txt, hdrs

    def pair(self):
        st, res, _ = self.req("POST", "/api/pair", {"code": self.c.pair_code}, {"Origin": self.origin})
        self.assertEqual(st, 200)
        return res

    def auth(self, res, csrf=True):
        h = {"Origin": self.origin, "Authorization": "Bearer " + res["session"]}
        if csrf:
            h["X-AIVD-CSRF"] = res["csrf"]
        return h

    def test_binds_loopback_only(self):
        self.assertEqual(self.httpd.server_address[0], "127.0.0.1")
        self.assertEqual(S.make_handler(self.c).timeout, S.SOCKET_TIMEOUT)

    def test_health_and_host_check(self):
        self.assertEqual(self.req("GET", "/api/health")[0], 200)
        self.assertEqual(self.req("GET", "/api/health", headers={"Host": "evil.example:80"})[0], 421)
        self.assertEqual(self.req("GET", "/api/health", headers={"Host": f"attacker.test:{self.port}"})[0], 421)

    def test_status_requires_pairing(self):
        self.assertEqual(self.req("GET", "/api/status")[0], 401)
        self.assertEqual(self.req("GET", "/api/status", headers={"Authorization": "Bearer forged.token"})[0], 401)

    def test_pairing_flow_one_time_and_lockout(self):
        st, _, _ = self.req("POST", "/api/pair", {"code": "WRONG-CODE"}, {"Origin": self.origin})
        self.assertEqual(st, 403)
        res = self.pair()
        self.assertFalse(self.c.pair_file.exists())
        st, body, _ = self.req("GET", "/api/status", headers=self.auth(res))
        self.assertEqual(st, 200)
        self.assertEqual(body["memory"]["state"], "FAIL")
        self.assertEqual(self.req("POST", "/api/pair", {"code": self.c.pair_code}, {"Origin": self.origin})[0], 403)

    def test_pairing_lockout(self):
        for _ in range(S.PAIR_MAX_FAILS):
            self.req("POST", "/api/pair", {"code": "BAD-BAD-BAD"}, {"Origin": self.origin})
        self.assertEqual(self.req("POST", "/api/pair", {"code": self.c.pair_code}, {"Origin": self.origin})[0], 403)

    def test_pairing_expiry(self):
        self.c.pair_issued -= S.PAIR_TTL + 1
        self.assertEqual(self.req("POST", "/api/pair", {"code": self.c.pair_code}, {"Origin": self.origin})[0], 403)

    def test_origin_enforced_on_post(self):
        self.assertEqual(self.req("POST", "/api/pair", {"code": self.c.pair_code})[0], 403)
        self.assertEqual(self.req("POST", "/api/pair", {"code": self.c.pair_code},
                                  {"Origin": "https://evil.example"})[0], 403)
        self.assertEqual(self.req("POST", "/api/pair", {"code": self.c.pair_code}, {"Origin": "null"})[0], 403)
        self.assertEqual(self.req("GET", "/api/health", headers={"Origin": "https://evil.example"})[0], 403)

    def test_csrf_required(self):
        res = self.pair()
        b = {"model_id": "qwen3:8b", "attempt_id": "a", "confirm": S.RUN_CONFIRM}
        self.assertEqual(self.req("POST", "/api/ops/rc6_run", b, self.auth(res, csrf=False))[0], 403)
        h = self.auth(res)
        h["X-AIVD-CSRF"] = "wrong"
        self.assertEqual(self.req("POST", "/api/ops/rc6_run", b, h)[0], 403)

    def test_run_and_reveal_refuse_over_http(self):
        res = self.pair()
        st, body, _ = self.req("POST", "/api/ops/rc6_run",
                               {"model_id": "qwen3:8b", "attempt_id": "a", "confirm": S.RUN_CONFIRM}, self.auth(res))
        self.assertEqual(st, 403)
        self.assertEqual(body["status"], "REFUSED")
        st, body, _ = self.req("POST", "/api/ops/rc6_reveal", {"confirm": S.REVEAL_CONFIRM}, self.auth(res))
        self.assertEqual(st, 403)
        self.assertEqual(self.req("POST", "/api/ops/cancel", {}, self.auth(res))[0], 501)

    def test_schema_size_type_and_unknown_ops(self):
        res = self.pair()
        h = self.auth(res)
        self.assertEqual(self.req("POST", "/api/ops/rc6_run", {"model_id": "qwen3:8b"}, h)[0], 400)
        self.assertEqual(self.req("POST", "/api/ops/rc6_run", {"model_id": "q", "attempt_id": "a", "confirm": "c",
                                                               "cmd": "rm -rf /"}, h)[0], 400)
        self.assertEqual(self.req("POST", "/api/ops/rc6_run", {"model_id": 1, "attempt_id": "a", "confirm": "c"},
                                  h)[0], 400)
        self.assertEqual(self.req("POST", "/api/ops/rc6_run", raw=b"{not json", headers=h)[0], 400)
        self.assertEqual(self.req("POST", "/api/ops/rc6_run", raw=b"x" * (S.MAX_BODY + 1), headers=h)[0], 413)
        self.assertEqual(self.req("POST", "/api/ops/rc6_run", raw=b"{}",
                                  headers={**h, "Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.req("POST", "/api/ops/shell", {"cmd": "id"}, h)[0], 404)
        self.assertEqual(self.req("POST", "/api/ops/rc6_run/../../x", {}, h)[0], 404)
        self.assertEqual(self.req("GET", "/api/exec?cmd=id", headers=h)[0], 404)
        self.assertEqual(self.req("PUT", "/api/status", headers=h)[0], 405)
        self.assertEqual(self.req("DELETE", "/api/status", headers=h)[0], 405)

    def test_cors_exact_origins_only(self):
        st, _, hd = self.req("OPTIONS", "/api/status", headers={"Origin": "https://evil.example",
                                                                 "Access-Control-Request-Method": "GET"})
        self.assertEqual(st, 403)
        self.assertNotIn("Access-Control-Allow-Origin", hd)
        st, _, hd = self.req("OPTIONS", "/api/status", headers={"Origin": "https://example.github.io",
                                                                 "Access-Control-Request-Private-Network": "true"})
        self.assertEqual(st, 204)
        self.assertEqual(hd["Access-Control-Allow-Origin"], "https://example.github.io")
        self.assertNotIn("Access-Control-Allow-Credentials", hd)
        _, _, hd = self.req("GET", "/api/health", headers={"Origin": self.origin})
        self.assertNotIn("Access-Control-Allow-Origin", hd)   # same-origin needs no CORS
        self.assertEqual(hd["X-Frame-Options"], "DENY")
        self.assertIn("frame-ancestors 'none'", hd["Content-Security-Policy"])

    def test_static_serving_and_traversal(self):
        st, body, _ = self.req("GET", "/aivd/")
        self.assertEqual(st, 200)
        self.assertEqual(self.req("GET", "/aivd/../outside.json")[0], 404)
        self.assertEqual(self.req("GET", "/aivd/%2e%2e/outside.json")[0], 404)
        self.assertEqual(self.req("GET", "/etc/passwd")[0], 404)
        self.assertEqual(self.req("GET", "/")[0], 302)

    def test_slow_client_times_out(self):
        s = socket.create_connection(("127.0.0.1", self.port))
        s.sendall(b"POST /api/pair HTTP/1.1\r\nHost: 127.0.0.1\r\n")
        s.settimeout(S.SOCKET_TIMEOUT + 5)
        t = time.time()
        try:
            data = s.recv(100)
        except socket.timeout:
            data = None
        s.close()
        self.assertLess(time.time() - t, S.SOCKET_TIMEOUT + 4)
        self.assertIn(data, (b"", None))


if __name__ == "__main__":
    unittest.main()
