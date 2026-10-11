"""Scanner, archive-rule, manifest and branch-safety tests (stdlib only; temp git repos)."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import outgoing_manifest as OM  # noqa: E402
import scan_outgoing as SO  # noqa: E402
from scan_rules import is_protected_path  # noqa: E402

CC = HERE.parent


def run_scan(*args):
    r = subprocess.run([sys.executable, str(HERE / "scan_outgoing.py"), *args], capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout.strip().splitlines()[-1])


class ScannerTests(unittest.TestCase):
    def dist(self, files):
        td = Path(tempfile.mkdtemp(prefix="cc-dist-"))
        for rel, data in files.items():
            p = td / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data if isinstance(data, bytes) else data.encode())
        return td

    def test_clean_dist_passes(self):
        code, res = run_scan("--dist", str(self.dist({"index.html": "<html>ok</html>", "a.json": "{}"})))
        self.assertEqual(code, 0)
        self.assertTrue(res["pass"])

    def test_each_rule_fails_the_build(self):
        tok = "ghp_" + "A" * 36
        pat = "github" + "_pat_" + "B" * 30
        ws, home, vt = "/" + "workspace", "/home" + "/box", "/var" + "/tmp"
        pk = "-----BEGIN OPENSSH " + "PRIVATE KEY-----"
        cases = {
            "P": {"reports/x/protected/seal.json": "{}"},
            "P2": {"final_seal.json": "{}"},
            "D:name": {"RC6_PREREGISTRATION_DRAFT.md": "x"},
            "L": {"a.js": f"const p='{ws}/aivd/x'"},
            "L2": {"a.js": f"x={home}/.ollama"},
            "L3": {"a.js": f"x={vt}/ollama"},
            "S:github_token": {"a.js": f"t='{tok}'"},
            "S:github_pat": {"a.js": f"t='{pat}'"},
            "S:private_key": {"k.txt": pk},
            "S:url_credentials": {"a.txt": "https://user:" + "pw" + "@github.com/x"},
            "K": {"s.json": '{"label_salt": "abc"}'},
            "O1": {"r.md": "we saw 17/" + "120 rows"},
            "O2": {"r.md": "post-" + "reveal analysis"},
            "O3": {"r.md": "R" + "C5 verified discoveries"},
            "O5": {"r.md": "the fun" + "nel"},
            "O8": {"r.md": "R" + "C5 ledger had 12 entries"},
        }
        for rule, files in cases.items():
            with self.subTest(rule=rule):
                code, res = run_scan("--dist", str(self.dist(files)))
                self.assertEqual(code, 1, rule)
                self.assertFalse(res["pass"])
                self.assertGreater(sum(res["hit_counts"].values()), 0)
                out = json.dumps(res)
                self.assertNotIn("/" + "workspace", out)   # counts only, never matched text
                self.assertNotIn("ghp_", out)

    def test_o6_token_hash_matching(self):
        import scan_rules as R
        self.assertEqual(len(R.O6_TOKEN_SHA256), 4)
        tok = "synthetic_local_only_artifact"
        R.O6_TOKEN_SHA256.add(hashlib.sha256(tok.encode()).hexdigest())
        try:
            self.assertIn("O6", SO.scan_item("r.md", f"see {tok.upper()}.json".encode(), set()))
            self.assertNotIn("O6", SO.scan_item("r.md", b"see something_else_entirely", set()))
        finally:
            R.O6_TOKEN_SHA256.discard(hashlib.sha256(tok.encode()).hexdigest())

    def test_deny_name_hashes(self):
        self.assertEqual(len(SO.DENY_NAME_SHA256), 18)
        self.assertIn("D:name", SO.scan_item("x/final_seal.json", b"{}", set()))

    def test_scanner_files_still_checked_for_paths_and_secrets(self):
        rel = "command-center/scripts/scan_rules.py"
        self.assertIn(rel, SO.SELF)
        self.assertIn("L", SO.scan_item(rel, ("/" + "workspace/x").encode(), set(), self_exempt=True))

    def test_deny_blob(self):
        data = b"some local-only document"
        SO.DENY_BLOBS.add(SO.blob_id(data))
        try:
            self.assertIn("D:blob", SO.scan_item("x.md", data, set()))
        finally:
            SO.DENY_BLOBS.discard(SO.blob_id(data))

    def test_allowlist_is_exact(self):
        data = b"post-" b"reveal"
        sha = hashlib.sha256(data).hexdigest()
        self.assertEqual(SO.scan_item("a.md", data, {("a.md", sha, "O2")}), [])
        self.assertIn("O2", SO.scan_item("b.md", data, {("a.md", sha, "O2")}))
        self.assertIn("O2", SO.scan_item("a.md", data + b" ", {("a.md", sha, "O2")}))

    def test_seal_scanner_required_and_failing(self):
        d = str(self.dist({"a.txt": "ok"}))
        code, res = run_scan("--dist", d, "--require-seal-scan")
        self.assertEqual(code, 1)
        self.assertIn("V:unavailable", res["hit_counts"])
        bad = Path(tempfile.mkdtemp()) / "fake_scanner.py"
        bad.write_text('import json; print(json.dumps({"files": 1, "pass": False, "prior_value_hits": 1}))')
        code, res = run_scan("--dist", d, "--seal-scanner", str(bad))
        self.assertEqual(code, 1)
        self.assertEqual(res["prior_seal_scan"]["prior_value_hits"], 1)
        good = bad.with_name("ok_scanner.py")
        good.write_text('import json; print(json.dumps({"files": 1, "pass": True}))')
        self.assertEqual(run_scan("--dist", d, "--seal-scanner", str(good))[0], 0)

    def test_protected_path_rule(self):
        for p in ("reports/aivd_rc4_multi_v1/protected/x.json", "a/raw/b.jsonl", "a/wire/c", "x/final_seal.json",
                  "x/block_seal_1.json", "r/full_ledger.jsonl", "r/label_salts.json"):
            self.assertTrue(is_protected_path(p), p)
        for p in ("AIVD_RC3.md", "docs/rc4_multi_v1/SCORING_PROTOCOL.md", "reports/aivd_rc1/summary.md"):
            self.assertFalse(is_protected_path(p), p)

    def test_committed_public_data_and_source_tree_are_clean(self):
        code, res = run_scan("--tree", str(CC / "public-data"))
        self.assertEqual(code, 0, res)
        code, res = run_scan("--tree", str(CC))
        self.assertEqual(code, 0, res)


class ArchiveConsistencyTests(unittest.TestCase):
    def test_allowlist_rules(self):
        allow = json.loads((CC / "reports-allowlist.json").read_text())
        idx = json.loads((CC / "public-data" / "reports-index.json").read_text())
        included = [x for x in allow["items"] if x["publication_review"] != "restricted"]
        self.assertEqual(len(included), len(idx["reports"]))
        for x in included:
            self.assertTrue(x["source_ref"].startswith(("origin/", "refs/tags/")))
            self.assertNotIn("rc5-a2-local-uncommitted", x["source_ref"])
            self.assertFalse(is_protected_path(x["path"]))
            self.assertFalse(x["contains_protected_material"])
            self.assertEqual(x["restriction_reasons"], [])
            art = CC / x["sanitized_artifact"]["file"]
            self.assertEqual(hashlib.sha256(art.read_bytes()).hexdigest(), x["sanitized_artifact"]["sha256"])
        for x in allow["items"]:
            if x["classification"] == "restricted-placeholder":
                self.assertIsNone(x["path"])
                self.assertIsNone(x["sha256"])
                self.assertIsNone(x["sanitized_artifact"])
        files = {p.name for p in (CC / "public-data" / "reports").glob("*.md")}
        self.assertEqual(files, {Path(x["sanitized_artifact"]["file"]).name for x in included})


class ManifestTests(unittest.TestCase):
    def git(self, repo, *a):
        return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                              capture_output=True, text=True, check=True).stdout.strip()

    def setUp(self):
        td = Path(tempfile.mkdtemp(prefix="cc-man-"))
        self.remote = td / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.remote)], check=True)
        self.repo = td / "work"
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.repo)], check=True)
        (self.repo / "README.md").write_text("public\n")
        self.git(self.repo, "add", "README.md")
        self.git(self.repo, "commit", "-q", "-m", "public base")
        self.git(self.repo, "remote", "add", "origin", str(self.remote))
        self.git(self.repo, "push", "-q", "origin", "main")
        self.git(self.repo, "fetch", "-q", "origin")

    def commit(self, path, text, msg):
        p = self.repo / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        self.git(self.repo, "add", path)
        self.git(self.repo, "commit", "-q", "-m", msg)
        return self.git(self.repo, "rev-parse", "HEAD")

    def test_ui_only_branch_passes(self):
        self.git(self.repo, "checkout", "-q", "-b", "ui/x")
        self.commit("command-center/a.txt", "a", "ui")
        m = OM.build(self.repo, "ui/x", "origin/main")
        self.assertTrue(m["branch_safety"]["pass"], m["branch_safety"])
        self.assertEqual(m["outgoing_commits"], 1)
        f = m["commits"][0]["files"][0]
        self.assertEqual(f["sha256"], hashlib.sha256(b"a").hexdigest())

    def test_research_ancestry_is_flagged(self):
        self.git(self.repo, "checkout", "-q", "-b", "ui/y")
        research = self.commit("docs/secret_study.md", "x", "unpublished research")
        self.commit("command-center/a.txt", "a", "ui")
        OM.DENY_COMMITS[research] = "test deny"
        try:
            m = OM.build(self.repo, "ui/y", "origin/main")
        finally:
            OM.DENY_COMMITS.pop(research)
        self.assertFalse(m["branch_safety"]["pass"])
        self.assertIn(research, m["unpublished_non_ui_commits"])
        self.assertEqual(m["deny_listed_commits"][0]["commit"], research)
        self.assertTrue(any("outside the UI scope" in r for r in m["branch_safety"]["reasons"]))

    def test_unrelated_history_and_main_refused(self):
        self.git(self.repo, "checkout", "-q", "--orphan", "other")
        self.commit("command-center/b.txt", "b", "orphan ui")
        m = OM.build(self.repo, "other", "origin/main")
        self.assertIsNone(m["merge_base"])
        self.assertFalse(m["branch_safety"]["pass"])
        m = OM.build(self.repo, "main", "origin/main")
        self.assertIn("tip is the main branch itself", m["branch_safety"]["reasons"])


class WorkflowTests(unittest.TestCase):
    def test_workflow_security_properties(self):
        wf = (CC.parent / ".github" / "workflows" / "command-center.yml")
        if not wf.exists():
            self.skipTest("workflow not present in this checkout")
        t = wf.read_text()
        import re
        uses = re.findall(r"uses:\s*([^\s#]+)", t)
        self.assertTrue(uses)
        for u in uses:
            self.assertRegex(u, r"@[0-9a-f]{40}$", u)          # every action pinned to a full commit SHA
        self.assertIn("contents: read", t)
        self.assertIn("pages: write", t)
        self.assertIn("id-token: write", t)
        self.assertIn("concurrency:", t)
        self.assertIn("actions/deploy-pages@", t)
        self.assertIn("actions/upload-pages-artifact@", t)
        self.assertRegex(t, r"if:\s*github\.event_name == 'push' && github\.ref == 'refs/heads/main'")
        self.assertNotIn("pull_request_target", t)
        self.assertNotIn("write-all", t)


if __name__ == "__main__":
    unittest.main()
