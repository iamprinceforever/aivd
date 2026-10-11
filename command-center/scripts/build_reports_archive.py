#!/usr/bin/env python3
"""Build the sanitized reports archive (reports-allowlist.json + public-data/) from PUBLIC git history.

Read-only against git: uses only `git ls-remote`-equivalent remote-tracking refs, `git ls-tree`, `git log`,
`git cat-file`. Never checks out, never writes to any worktree except the output directory given.

usage: build_reports_archive.py --repo <git dir or worktree> --out <command-center dir> [--seal-scanner <path>]

Eligibility rule (fail closed): a file is INCLUDED only if
  * the blob is reachable from a commit that is contained in a remote-tracking ref (origin/*) or a public tag,
  * its path is not under any protected/, raw/, wire/ directory and not a seal/ledger/salt file,
  * it has zero outcome-pattern hits (O1-O8, the RC6 outgoing-check patterns),
  * it has zero secret-pattern hits,
  * the prior-seal value scanner (when supplied) reports pass for it.
Local machine paths are redacted to "<local-path>" in the sanitized artifact (both hashes are recorded).
Unpublished material (the fifth release candidate's execution record, RC6 documents that fail the scans or are
deny-listed, the original RC6 prereg) is represented by restricted placeholders that carry no paths, hashes, or
findings.

Staged RC6 readiness/design documents (STAGED below): the RC6 research tip is local only (its ancestry carries
unpublished commits, so the RC6 pre-push gate refuses it). A short, explicitly pinned list of (path, blob id) from
that tip is read with `git cat-file` and goes through EVERY check above except the public-ref one, plus the RC6
deny-list (names and blob ids, via scan_outgoing). The pinned blob id must match exactly; any edit or any hit
drops the document (fail closed). Nothing outside the pinned list is ever read from the local tip, and documents
that fail are counted only, never listed.
Prints counts only.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_rules import SECRET_RX, LOCAL_PATH_RX, SEAL_KEY_RX, is_protected_path, outcome_hits  # noqa: E402
from scan_outgoing import DENY_BLOBS, DENY_NAME_SHA256, blob_id  # noqa: E402

# Public refs considered (remote-tracking refs / public tags only), in priority order (latest first per series).
PUBLIC_REFS = [
    ("origin/research/aivd-historical-seal-recovery", "historical-seal-recovery"),
    ("origin/research/aivd-rc5-generalization-v1-design", "RC5 design"),
    ("origin/research/aivd-rc4-multi-v1-design", "RC4-MULTI-V1"),
    ("origin/research/aivd-post-rc3-local-v1-final", "POST-RC3 LOCAL-V1"),
    ("origin/research/aivd-post-rc3-local-v1", "POST-RC3 LOCAL-V1"),
    ("origin/research/aivd-post-rc3-groq-evaluation", "POST-RC3 Groq"),
    ("origin/research/aivd-endgame-3-autonomous-security-discovery", "POST-RC3"),
    ("refs/tags/AIVD-RC3", "RC3"),
    ("refs/tags/AIVD-RC2", "RC2"),
    ("refs/tags/AIVD-RC1", "RC1"),
    ("origin/main", "AIVD 3.x (main)"),
]
NEVER_REFS = ("research/aivd-rc5-a2-local-uncommitted",)
REPORT_RX = re.compile(r"^([^/]+\.md|docs/.+\.md|reports/.+\.md)$")
SERIES_RX = [
    (re.compile(r"rc5_generalization|AIVD_RC5|rc5", re.I), "RC5-GENERALIZATION-V1 (design phase)"),
    (re.compile(r"rc4_multi", re.I), "RC4-MULTI-V1"),
    (re.compile(r"post_rc3_local|local_v1", re.I), "POST-RC3 LOCAL-V1"),
    (re.compile(r"post_rc3_v2", re.I), "POST-RC3 Groq V2"),
    (re.compile(r"post_rc3", re.I), "POST-RC3"),
    (re.compile(r"historical_recovery", re.I), "Historical seal recovery"),
    (re.compile(r"RC3|rc3", re.I), "RC3"),
    (re.compile(r"RC2|rc2", re.I), "RC2"),
    (re.compile(r"RC1|rc1", re.I), "RC1"),
    (re.compile(r"f3_lm", re.I), "AIVD 4.0 F3-LM"),
]
# Claim levels: only recorded when the report text itself states them (word-boundary match, case-sensitive caps
# words or the exact lower-case phrase); the UI must show "not stated" otherwise.
CLAIM_RX = {
    "discovery_candidate": re.compile(r"\bDISCOVERY[_ ]CANDIDATES?\b|\bdiscovery candidates?\b"),
    "verified": re.compile(r"\bVERIFIED\b"),
    "reproduced": re.compile(r"\bREPRODUCED\b|\breproduced\b"),
    "generalized": re.compile(r"\bGENERALI[SZ]ED\b"),
    "not_discovered": re.compile(r"\bNOT[_ ]DISCOVERED\b"),
}
# Pinned publication-safe RC6 documents from the local research tip (see module docstring). stage = the step of the
# research journey the document belongs to (site-data research_journey ids).
STAGED_REF = "local:research/aivd-rc6-partb-readiness"
STAGED_LABEL = "RC6 Part B readiness (local research tip; not on a public ref)"
STAGED_COMMIT = "cb8dc31fc0c7b0644cb2d45e000892c6825a1758"
STAGED_SERIES = "RC6 (diagnostics and Part B readiness)"
_D = "docs/rc6_investigation_diagnostics/"
STAGED = [
    (_D + "RC6_BREAKTHROUGH_CRITERIA.md", "ad7e2ceed3786cacf3bd26f724ce4e2e405974af", "rc6_design"),
    (_D + "RC6_EVIDENCE_FLOW_DESIGN.md", "559e6d4aca7177f2d18d2b43968c676048a2cfee", "rc6_part_a"),
    (_D + "RC6_EVIDENCE_COMPONENT_STUDY_PREREG_DRAFT.md", "9ef08e88d57a0bd82e2f4d7475fc1a30046d533c", "rc6_part_a"),
    (_D + "RC6_RUNNER_DESIGN.md", "ff3b31d007e5d5e46e0f04afaf09f55f5143f012", "rc6_partb_readiness"),
    (_D + "RC6_V1_FIELDS_SPEC.md", "1d0b57e38478fff77040630682497d26b999b17c", "rc6_partb_readiness"),
    (_D + "RC6_MEMORY_AND_FAILURE_PLAN.md", "f1b8bddc16f9bd9e46af9e3ed6bd80ac4e89e8fb", "rc6_partb_readiness"),
    (_D + "RC6_EXECUTION_READINESS.md", "d914ab8e328a4ad1b49fa015c9bd3f2dfaeae980", "rc6_partb_readiness"),
    (_D + "FROZEN_ANALYSIS_HISTORY.md", "7bbf92df625f308e8425e7808f351685583c78cf", "rc6_partb_readiness"),
    (_D + "RUNTIME_RESTORE_RECORD.md", "18f34a98fd45e56c6ae5305f76d3348d482c119e", "rc6_partb_readiness"),
    (_D + "REVIEWER_CHECKLIST.md", "4ff6ce04d4850518853b61df5daf04a6aac1e073", "rc6_partb_readiness"),
    (_D + "RC6_REPLICATION_PREREG_SKELETON.md", "477ae8ae602fe36a20509b56e21a4d47aa84aeab", "rc6_partb_readiness"),
    (_D + "RC6_REPLICATION_PREREGISTRATION.md", "02b88ccf98256af86f074bdf98250a8f07d51f27", "rc6_partb_readiness"),
    (_D + "RC6_REPLICATION_PREREG_AMENDMENT_A1.md", "8c66518a19b28dfb7de477afa63256dca61d8194", "rc6_partb_readiness"),
]
RESTRICTED = [
    {"id": "restricted-rc5-execution", "title": "Fifth release candidate (RC5): execution-phase record",
     "series": "RC5-GENERALIZATION-V1", "reason": "unpublished; not on any public ref; withheld pending "
     "the researcher's publication decision"},
    {"id": "restricted-rc6-docs", "title": "Other RC6 diagnostics and readiness documents (Part A results, decision "
     "report, readiness report and manifest, decision log, risk registers, SAP, redacted prereg candidate)",
     "series": "RC6", "reason": "withheld: outcome-pattern hits pending human review, deny-listed by name or blob, or "
     "restate unpublished earlier-study figures; only the pinned documents that pass every scan are archived"},
    {"id": "restricted-rc6-prereg-original", "title": "RC6 original preregistration and redaction diff",
     "series": "RC6", "reason": "withheld by rule: contains unpublished outcome references; only a redacted "
     "candidate exists and it is pending separate review"},
    {"id": "restricted-protected", "title": "Protected material (seals, ledgers, wire records, label salts)",
     "series": "all", "reason": "protected paths are never published, even when historically tracked"},
]


def git(repo, *a, binary=False):
    r = subprocess.run(["git", "-C", str(repo), *a], capture_output=True)
    if r.returncode:
        raise RuntimeError(f"git {a[0]} failed")
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def classify(path: str, title: str = "") -> str:
    """Series from the path first, then from the report's own title; default AIVD 3.x (main line)."""
    for text in (path, title):
        for rx, name in SERIES_RX:
            if rx.search(text):
                return name
    return "AIVD 3.x"


def title_of(text: str, path: str) -> str:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()[:160]
    return Path(path).stem


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seal-scanner", default=None)
    ap.add_argument("--no-staged", dest="staged", action="store_false",
                    help="skip the pinned RC6 staged documents")
    a = ap.parse_args(argv)
    repo, out = Path(a.repo), Path(a.out)
    remote_refs = set(git(repo, "for-each-ref", "--format=%(refname)", "refs/remotes/origin", "refs/tags").split())
    cand = {}  # path -> (ref label, ref, blob)
    for ref, label in PUBLIC_REFS:
        full = ref if ref.startswith("refs/") else f"refs/remotes/{ref}"
        if full not in remote_refs or any(n in ref for n in NEVER_REFS):
            continue
        for line in git(repo, "ls-tree", "-r", ref).splitlines():
            meta, path = line.split("\t", 1)
            if REPORT_RX.match(path) and path not in cand:
                cand[path] = (label, ref, meta.split()[2])
    items, files_for_scan = [], []
    tmp = Path(tempfile.mkdtemp(prefix="cc-scan-"))
    staged_dropped = 0
    have_tip = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", STAGED_COMMIT + "^{commit}"],
                              capture_output=True).returncode == 0
    for path, pinned, stage in (STAGED if a.staged else []):
        reasons = []
        raw = b""
        if not have_tip:
            reasons.append("staged tip not present")
        else:
            r = subprocess.run(["git", "-C", str(repo), "rev-parse", f"{STAGED_COMMIT}:{path}"], capture_output=True,
                               text=True)
            if r.returncode or r.stdout.strip() != pinned:
                reasons.append("blob differs from the pinned id")
            else:
                raw = git(repo, "cat-file", "blob", pinned, binary=True)
        if raw and (blob_id(raw) in DENY_BLOBS or sha(Path(path).name.encode()) in DENY_NAME_SHA256):
            reasons.append("deny-listed")
        text = raw.decode("utf-8", "replace")
        if raw and SEAL_KEY_RX.search(text):
            reasons.append("seal-like key")
        if reasons:
            staged_dropped += 1
            continue
        commit = git(repo, "log", "-1", "--format=%H", STAGED_COMMIT, "--", path).strip()
        sanitized = LOCAL_PATH_RX.sub("<local-path>", text)
        hits = sorted(outcome_hits(text))
        if hits:
            reasons.append("outcome")
        if any(rx.search(text) for rx in SECRET_RX.values()):
            reasons.append("secret")
        if is_protected_path(path):
            reasons.append("protected")
        f = tmp / f"{len(files_for_scan):04d}.md"
        f.write_text(sanitized, encoding="utf-8")
        files_for_scan.append(f)
        items.append({"path": path, "source_ref": STAGED_REF, "source_label": STAGED_LABEL, "commit": commit,
                      "blob": pinned, "sha256": sha(raw), "bytes": len(raw), "series": STAGED_SERIES,
                      "title": title_of(text, path), "historical": False, "journey_stage": stage,
                      "claims_stated_in_report": sorted(k for k, rx in CLAIM_RX.items() if rx.search(text)),
                      "local_paths_redacted": sanitized != text, "_reasons": reasons, "_text": sanitized,
                      "_scan_file": str(f), "_staged": True})
    for path, (label, ref, blob) in sorted(cand.items()):
        commit = git(repo, "log", "-1", "--format=%H", ref, "--", path).strip()
        public = bool(git(repo, "branch", "-r", "--contains", commit).strip()) or bool(
            git(repo, "tag", "--contains", commit).strip())
        raw = git(repo, "cat-file", "blob", blob, binary=True)
        text = raw.decode("utf-8", "replace")
        reasons = []
        if not public:
            reasons.append("commit not contained in any public ref")
        if is_protected_path(path):
            reasons.append("protected path")
        hits = sorted(outcome_hits(text))
        if hits:
            reasons.append("outcome-pattern hit(s) " + ",".join(h.split("_")[0] for h in hits) + " pending human review")
        if any(rx.search(text) for rx in SECRET_RX.values()):
            reasons.append("secret-like pattern")
        sanitized = LOCAL_PATH_RX.sub("<local-path>", text)
        f = tmp / f"{len(files_for_scan):04d}.md"
        f.write_text(sanitized, encoding="utf-8")
        files_for_scan.append(f)
        claims = sorted(k for k, rx in CLAIM_RX.items() if rx.search(text))
        items.append({"path": path, "source_ref": ref, "source_label": label, "commit": commit, "blob": blob,
                      "sha256": sha(raw), "bytes": len(raw), "series": classify(path, title_of(text, path)), "title": title_of(text, path),
                      "historical": True, "claims_stated_in_report": claims,
                      "local_paths_redacted": sanitized != text, "_reasons": reasons, "_text": sanitized,
                      "_scan_file": str(f)})
    # prior-seal value scanner, per file (counts only), fail closed when unavailable
    scanner_state = "unavailable"
    if a.seal_scanner and Path(a.seal_scanner).exists():
        scanner_state = "ran"
        for it in items:
            r = subprocess.run([sys.executable, a.seal_scanner, it["_scan_file"]], capture_output=True, text=True)
            try:
                ok = json.loads(r.stdout.strip().splitlines()[-1]).get("pass") is True
            except (ValueError, IndexError):
                ok = False
            if not ok:
                it["_reasons"].append("prior-seal value scan did not pass")
    else:
        for it in items:
            it["_reasons"].append("prior-seal value scan unavailable (fail closed)")
    dest = out / "public-data" / "reports"
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob("*.md"):
        old.unlink()
    allow, index = [], []
    items.sort(key=lambda it: bool(it.get("_staged")))  # public historical reports first, staged RC6 after
    for n, it in enumerate(items):
        rid = re.sub(r"[^a-z0-9]+", "-", it["path"].lower()).strip("-")[:90]
        included = not it["_reasons"]
        if it.get("_staged") and not included:   # never list a failing local-only document, count it only
            staged_dropped += 1
            continue
        art = None
        if included:
            body = it["_text"].encode("utf-8")
            art = {"file": f"public-data/reports/{rid}.md", "sha256": sha(body)}
            (dest / f"{rid}.md").write_bytes(body)
        entry = {k: v for k, v in it.items() if not k.startswith("_")}
        staged = bool(it.get("_staged"))
        entry.update({"id": rid, "classification": "staged-research-report" if staged else "historical-report",
                      "contains_unpublished_outcomes": False if included else None,
                      "contains_protected_material": is_protected_path(it["path"]),
                      "publication_review": ("eligible-automated-staged" if staged else "eligible-automated")
                      if included else "restricted",
                      "restriction_reasons": it["_reasons"], "sanitized_artifact": art})
        if not included:  # restricted entries keep provenance but carry no title text beyond the file name
            entry["title"] = Path(it["path"]).name
            entry["claims_stated_in_report"] = []
        allow.append(entry)
        if included:
            row = {k: entry[k] for k in ("id", "title", "series", "path", "source_ref", "source_label", "commit",
                                         "sha256", "historical", "claims_stated_in_report",
                                         "local_paths_redacted", "sanitized_artifact")}
            if staged:
                row["journey_stage"] = entry["journey_stage"]
            index.append(row)
    for r in RESTRICTED:
        allow.append({**r, "classification": "restricted-placeholder", "source_ref": None, "commit": None,
                      "path": None, "sha256": None, "contains_unpublished_outcomes": True,
                      "contains_protected_material": r["id"] == "restricted-protected",
                      "publication_review": "restricted", "sanitized_artifact": None})
    meta = {"schema": 1, "rule": "public-ref commits only (plus pinned RC6 staged documents from the local research "
            "tip); no protected paths; 0 outcome/secret/seal hits", "prior_seal_scanner": scanner_state,
            "staged_source": {"ref": STAGED_REF, "commit": STAGED_COMMIT, "on_public_ref": False,
                              "pinned": len(STAGED) if a.staged else 0,
                              "included": sum(1 for x in allow if x["classification"] == "staged-research-report")}}
    (out / "reports-allowlist.json").write_text(json.dumps({**meta, "items": allow}, indent=1) + "\n")
    (dest.parent / "reports-index.json").write_text(json.dumps({**meta, "restricted_placeholders": RESTRICTED,
                                                               "reports": index}, indent=1) + "\n")
    inc = sum(1 for x in allow if x["publication_review"] != "restricted")
    print(json.dumps({"candidates": len(items), "included": inc, "restricted": len(allow) - inc,
                      "staged_included": meta["staged_source"]["included"], "staged_dropped": staged_dropped,
                      "prior_seal_scanner": scanner_state}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
