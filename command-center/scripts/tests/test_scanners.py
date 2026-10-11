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
        import build_reports_archive as BRA
        pinned = {(p, b) for p, b, _ in BRA.STAGED}
        for x in included:
            if x["classification"] == "staged-research-report":
                # only exact pinned (path, blob) pairs from the local research tip, nothing else
                self.assertEqual(x["source_ref"], BRA.STAGED_REF)
                if x.get("human_review"):   # released only by a signed approve record (see HumanReviewTests)
                    self.assertIn((x["path"], x["blob"]), {(p, b) for p, b, _ in BRA.REVIEW_CANDIDATES})
                    self.assertEqual(x["publication_review"], "approved-human-review")
                    self.assertEqual(x["human_review"]["decision"], "approve")
                    self.assertTrue(x["human_review"]["reviewer"].strip())
                else:
                    self.assertIn((x["path"], x["blob"]), pinned)
                    self.assertEqual(x["publication_review"], "eligible-automated-staged")
                self.assertNotIn(hashlib.sha256(Path(x["path"]).name.encode()).hexdigest(), SO.DENY_NAME_SHA256)
                self.assertNotIn(x["blob"], SO.DENY_BLOBS)
            else:
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


class StagedArchiveTests(unittest.TestCase):
    """Pinned RC6 documents from a local tip: every scan applies; any mismatch or hit drops (and never lists) it."""

    def git(self, repo, *a):
        return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                              capture_output=True, text=True, check=True).stdout.strip()

    def test_staged_documents_fail_closed(self):
        import build_reports_archive as BRA
        td = Path(tempfile.mkdtemp(prefix="cc-stage-"))
        remote, repo = td / "remote.git", td / "work"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
        (repo / "README.md").write_text("# Public\n")
        self.git(repo, "add", "README.md")
        self.git(repo, "commit", "-q", "-m", "public")
        self.git(repo, "remote", "add", "origin", str(remote))
        self.git(repo, "push", "-q", "origin", "main")
        self.git(repo, "fetch", "-q", "origin")
        d = repo / "docs" / "rc6"
        d.mkdir(parents=True)
        (d / "CLEAN.md").write_text("# Clean readiness doc\nNo figures.\n")
        (d / "HIT.md").write_text("# Hit doc\nthe " + "fun" + "nel moved\n")
        (d / "EDITED.md").write_text("# Edited after pinning\n")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-q", "-m", "local research")
        tip = self.git(repo, "rev-parse", "HEAD")
        blob = lambda p: self.git(repo, "rev-parse", f"HEAD:{p}")  # noqa: E731
        scanner = td / "seal_ok.py"
        scanner.write_text("import json\nprint(json.dumps({'pass': True}))\n")
        saved = (BRA.STAGED, BRA.STAGED_COMMIT)
        BRA.STAGED = [("docs/rc6/CLEAN.md", blob("docs/rc6/CLEAN.md"), "rc6_partb_readiness"),
                      ("docs/rc6/HIT.md", blob("docs/rc6/HIT.md"), "rc6_partb_readiness"),
                      ("docs/rc6/EDITED.md", "0" * 40, "rc6_partb_readiness")]
        BRA.STAGED_COMMIT = tip
        out = td / "out"
        try:
            self.assertEqual(BRA.main(["--repo", str(repo), "--out", str(out), "--seal-scanner", str(scanner)]), 0)
        finally:
            BRA.STAGED, BRA.STAGED_COMMIT = saved
        allow = json.loads((out / "reports-allowlist.json").read_text())
        idx = json.loads((out / "public-data" / "reports-index.json").read_text())
        staged = [x for x in allow["items"] if x.get("source_ref") == BRA.STAGED_REF]
        self.assertEqual([x["path"] for x in staged], ["docs/rc6/CLEAN.md"])
        self.assertEqual(staged[0]["classification"], "staged-research-report")
        self.assertEqual(idx["staged_source"]["included"], 1)
        self.assertFalse(idx["staged_source"]["on_public_ref"])
        self.assertNotIn("HIT.md", json.dumps(allow))
        self.assertNotIn("EDITED.md", json.dumps(allow))
        # without --staged the local tip is never read
        out2 = td / "out2"
        BRA.main(["--repo", str(repo), "--out", str(out2), "--seal-scanner", str(scanner), "--no-staged"])
        self.assertEqual(json.loads((out2 / "public-data" / "reports-index.json").read_text())["staged_source"]["included"], 0)

    def test_staged_pins_are_exact(self):
        import build_reports_archive as BRA
        self.assertTrue(all(len(b) == 40 for _, b, _ in BRA.STAGED))
        self.assertTrue(BRA.STAGED_REF.startswith("local:"))


class HumanReviewTests(unittest.TestCase):
    """Signed, blob-exact human review records: only a valid approve covering every flagged span releases."""

    @classmethod
    def setUpClass(cls):
        import build_reports_archive as BRA
        cls.BRA = BRA
        td = Path(tempfile.mkdtemp(prefix="cc-review-"))
        remote, repo = td / "remote.git", td / "work"
        g = lambda *a: subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a],  # noqa: E731
                                      capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
        (repo / "README.md").write_text("# Public\n")
        g("add", "README.md")
        g("commit", "-q", "-m", "public")
        g("remote", "add", "origin", str(remote))
        g("push", "-q", "origin", "main")
        g("fetch", "-q", "origin")
        d = repo / "docs" / "rc6"
        d.mkdir(parents=True)
        (d / "FLAGGED.md").write_text("# Flagged readiness doc\nThe " + "fun" + "nel term appears here.\nclean line\n")
        (d / "SECRETY.md").write_text("# Secret doc\nThe " + "fun" + "nel again\nkey " + "gh" + "p_" + "A" * 36 + "\n")
        g("add", ".")
        g("commit", "-q", "-m", "local research")
        cls.tip = g("rev-parse", "HEAD")
        cls.blob = {n: g("rev-parse", f"HEAD:docs/rc6/{n}") for n in ("FLAGGED.md", "SECRETY.md")}
        cls.raw = {n: (d / n).read_bytes() for n in ("FLAGGED.md", "SECRETY.md")}
        cls.repo, cls.td = repo, td
        cls.scanner = td / "seal_ok.py"
        cls.scanner.write_text("import json\nprint(json.dumps({'pass': True}))\n")

    def record(self, name="FLAGGED.md", **over):
        from scan_rules import outcome_spans
        raw = self.raw[name]
        hits = [{"line": n, "start": a, "end": b, "pattern": c, "span_sha256": h}
                for n, a, b, c, h in outcome_spans(raw.decode())]
        rec = {"path": f"docs/rc6/{name}", "blob": self.blob[name], "sha256": hashlib.sha256(raw).hexdigest(),
               "hits": hits, "reviewer": "A. Human", "review_date": "2026-10-11", "decision": "approve",
               "rationale": "term used as a section label; no figures"}
        rec.update(over)
        return rec

    def build(self, records, names=("FLAGGED.md",)):
        BRA = self.BRA
        rf = Path(tempfile.mkdtemp(dir=self.td)) / "publication-review.json"
        rf.write_text(json.dumps({"schema": 1, "records": records}))
        saved = (BRA.STAGED, BRA.REVIEW_CANDIDATES, BRA.STAGED_COMMIT)
        BRA.STAGED = []
        BRA.REVIEW_CANDIDATES = [(f"docs/rc6/{n}", self.blob[n], "rc6_partb_readiness") for n in names]
        BRA.STAGED_COMMIT = self.tip
        out = rf.parent / "out"
        try:
            BRA.main(["--repo", str(self.repo), "--out", str(out), "--seal-scanner", str(self.scanner),
                      "--review-file", str(rf)])
        finally:
            BRA.STAGED, BRA.REVIEW_CANDIDATES, BRA.STAGED_COMMIT = saved
        allow = json.loads((out / "reports-allowlist.json").read_text())
        released = [x for x in allow["items"] if x.get("publication_review") == "approved-human-review"]
        listed = json.dumps(allow)
        return released, listed, out

    def assertRestricted(self, records, names=("FLAGGED.md",)):
        released, listed, _ = self.build(records, names)
        self.assertEqual(released, [])
        for n in names:
            self.assertNotIn(n, listed)   # withheld documents are never listed

    def test_no_record_stays_restricted(self):
        self.assertRestricted([])

    def test_wrong_sha_or_blob_stays_restricted(self):
        self.assertRestricted([self.record(sha256="0" * 64)])
        self.assertRestricted([self.record(blob="0" * 40)])

    def test_wrong_or_incomplete_span_stays_restricted(self):
        r = self.record()
        shifted = [dict(h, start=h["start"] + 1) for h in r["hits"]]
        self.assertRestricted([self.record(hits=shifted)])
        self.assertRestricted([self.record(hits=[dict(h, span_sha256="0" * 64) for h in r["hits"]])])
        self.assertRestricted([self.record(hits=[dict(h, pattern="O1") for h in r["hits"]])])
        self.assertRestricted([self.record(hits=[])])
        self.assertRestricted([self.record(hits=r["hits"] + [dict(r["hits"][0], line=3)])])

    def test_unsigned_record_stays_restricted(self):
        self.assertRestricted([self.record(reviewer="")])
        self.assertRestricted([self.record(reviewer="   ")])
        self.assertRestricted([self.record(decision="")])
        self.assertRestricted([self.record(review_date="")])
        self.assertRestricted([self.record(rationale="")])

    def test_reject_and_redact_stay_restricted(self):
        self.assertRestricted([self.record(decision="reject")])
        self.assertRestricted([self.record(decision="redact")])
        self.assertRestricted([self.record(), self.record(decision="reject", reviewer="B. Second")])

    def test_valid_approve_is_included_and_scanner_honours_it(self):
        import review_rules
        released, _, out = self.build([self.record()])
        self.assertEqual(len(released), 1)
        x = released[0]
        self.assertEqual(x["classification"], "staged-research-report")
        self.assertEqual(x["human_review"]["reviewer"], "A. Human")
        self.assertEqual(x["restriction_reasons"], [])
        idx = json.loads((out / "public-data" / "reports-index.json").read_text())
        self.assertEqual(idx["reports"][-1]["human_review"]["decision"], "approve")
        art = out / x["sanitized_artifact"]["file"]
        self.assertTrue(art.exists())
        # the outgoing scanner accepts exactly that artifact for exactly the approved pattern codes
        (out / "publication-review.json").write_text(json.dumps({"records": [self.record()]}))
        triples = review_rules.approved_artifacts(out)
        self.assertEqual({t[2] for t in triples}, {"O5"})
        self.assertTrue(all(t[0] == art.name and t[1] == x["sanitized_artifact"]["sha256"] for t in triples))
        (out / "publication-review.json").write_text(json.dumps({"records": [self.record(reviewer="")]}))
        self.assertEqual(review_rules.approved_artifacts(out), set())

    def test_approve_never_waives_secret(self):
        self.assertRestricted([self.record("SECRETY.md")], names=("SECRETY.md",))

    def test_committed_review_records_are_signed_and_match_released_entries(self):
        import review_rules
        BRA = self.BRA
        recs = review_rules.load_records()
        cands = {(p, b) for p, b, _ in BRA.REVIEW_CANDIDATES}
        allow = json.loads((CC / "reports-allowlist.json").read_text())
        released = {(x["path"], x["blob"], x["sha256"]) for x in allow["items"] if x.get("human_review")}
        for r in recs:
            self.assertTrue(review_rules.signed(r), r.get("path"))
            self.assertIn((r["path"], r["blob"]), cands)
            if r["decision"] == "approve":
                self.assertIn((r["path"], r["blob"], r["sha256"]), released)
        self.assertEqual(len(released), sum(1 for r in recs if r["decision"] == "approve"))
        # every released artifact is accepted by the scanner only for its approved codes
        names = {Path(x["sanitized_artifact"]["file"]).name for x in allow["items"] if x.get("human_review")}
        self.assertEqual({t[0] for t in review_rules.approved_artifacts()}, names)


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


class PagesBuildAllowanceTests(ManifestTests):
    """--allow-pages-build accepts exactly the Pages build output under docs/ and nothing else."""

    def setUp(self):
        super().setUp()
        self.commit("docs/methodology.md", "research doc\n", "research doc on main")
        self.git(self.repo, "push", "-q", "origin", "main")
        self.git(self.repo, "fetch", "-q", "origin")
        self.git(self.repo, "checkout", "-q", "-b", "ui/publish")

    def write(self, files):
        for path, text in files.items():
            p = self.repo / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
            self.git(self.repo, "add", path)
        self.git(self.repo, "commit", "-q", "-m", "publish")

    def site(self, **extra):
        files = {"command-center/public-data/runs/latest.json": "{}\n",
                 "command-center/public-data/site-data.json": "{\"a\": 1}\n",
                 "command-center/public-data/reports/r-one.md": "# r\n",
                 "docs/index.html": "<html></html>\n", "docs/404.html": "<html></html>\n", "docs/.nojekyll": "",
                 "docs/assets/index-AbC123_x.js": "x", "docs/assets/index-AbC123_x.css": "y",
                 "docs/runs/latest.json": "{}\n", "docs/site-data.json": "{\"a\": 1}\n", "docs/reports/r-one.md": "# r\n"}
        files.update(extra)
        self.write(files)

    def build(self, allow=True):
        return OM.build(self.repo, "ui/publish", "origin/main", allow_pages_build=allow)

    def test_pages_build_output_passes_only_when_opted_in(self):
        self.site()
        m = self.build()
        self.assertTrue(m["branch_safety"]["pass"], m["branch_safety"])
        self.assertEqual(len(m["pages_build_changes"]), 8)
        self.assertEqual(m["out_of_scope_changes"], [])
        off = self.build(allow=False)                       # default unchanged: docs/ is out of scope
        self.assertFalse(off["branch_safety"]["pass"])
        self.assertEqual(len(off["out_of_scope_changes"]), 8)
        self.assertEqual(off["pages_build_changes"], [])

    def test_anything_else_under_docs_stays_out_of_scope(self):
        for extra in ({"docs/methodology.md": "changed research doc\n"},     # on main: never covered
                      {"docs/notes.md": "new doc\n"},                         # not a build path
                      {"docs/assets/evil.js": "x"},                            # not a hashed build asset
                      {"docs/assets/index-AbC123_x.js.map": "x"},
                      {"docs/runs/notes.json": "{}"},
                      {"docs/examples/github-ci.yml": "x"},
                      {".github/workflows/pages.yml": "x"},
                      {"README.md": "changed\n"}):
            with self.subTest(extra=list(extra)):
                self.setUp()
                self.site(**extra)
                m = self.build()
                self.assertFalse(m["branch_safety"]["pass"])
                self.assertEqual([c["path"] for c in m["out_of_scope_changes"]], list(extra))

    def test_content_bindings(self):
        cases = {"docs/runs/latest.json": "{\"other\": 1}\n",       # differs from public-data copy
                 "docs/reports/r-one.md": "# tampered\n",
                 "docs/404.html": "<html>different</html>\n",          # SPA fallback must equal index.html
                 "docs/.nojekyll": "not empty"}
        for path, text in cases.items():
            with self.subTest(path=path):
                self.setUp()
                self.site(**{path: text})
                m = self.build()
                self.assertFalse(m["branch_safety"]["pass"])
                self.assertEqual([c["path"] for c in m["out_of_scope_changes"]], [path])

    def test_deletions_and_renames_are_not_covered(self):
        self.site()
        self.git(self.repo, "push", "-q", "origin", "ui/publish")
        self.git(self.repo, "fetch", "-q", "origin")
        self.git(self.repo, "rm", "-q", "docs/assets/index-AbC123_x.css")
        self.git(self.repo, "mv", "docs/assets/index-AbC123_x.js", "docs/assets/index-ZZZ999_y.js")
        self.git(self.repo, "commit", "-q", "-m", "delete + rename")
        m = self.build()
        self.assertFalse(m["branch_safety"]["pass"])
        self.assertEqual(sorted(c["path"] for c in m["out_of_scope_changes"]),
                         ["docs/assets/index-AbC123_x.css", "docs/assets/index-ZZZ999_y.js"])


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
