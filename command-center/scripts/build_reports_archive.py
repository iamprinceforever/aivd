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
Unpublished material (the fifth release candidate's execution record, RC6 documents, the original RC6
prereg) is represented by
restricted placeholders that carry no paths, hashes, or findings.
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
from scan_rules import SECRET_RX, LOCAL_PATH_RX, is_protected_path, outcome_hits  # noqa: E402

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
RESTRICTED = [
    {"id": "restricted-rc5-execution", "title": "Fifth release candidate (RC5): execution-phase record",
     "series": "RC5-GENERALIZATION-V1", "reason": "unpublished; not on any public ref; withheld pending "
     "the researcher's publication decision"},
    {"id": "restricted-rc6-docs", "title": "RC6 investigation diagnostics and readiness documents",
     "series": "RC6", "reason": "unpublished; pending separate review; some documents restate unpublished earlier-study "
     "figures"},
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
    for n, it in enumerate(items):
        rid = re.sub(r"[^a-z0-9]+", "-", it["path"].lower()).strip("-")[:90]
        included = not it["_reasons"]
        art = None
        if included:
            body = it["_text"].encode("utf-8")
            art = {"file": f"public-data/reports/{rid}.md", "sha256": sha(body)}
            (dest / f"{rid}.md").write_bytes(body)
        entry = {k: v for k, v in it.items() if not k.startswith("_")}
        entry.update({"id": rid, "classification": "historical-report",
                      "contains_unpublished_outcomes": False if included else None,
                      "contains_protected_material": is_protected_path(it["path"]),
                      "publication_review": "eligible-automated" if included else "restricted",
                      "restriction_reasons": it["_reasons"], "sanitized_artifact": art})
        if not included:  # restricted entries keep provenance but carry no title text beyond the file name
            entry["title"] = Path(it["path"]).name
            entry["claims_stated_in_report"] = []
        allow.append(entry)
        if included:
            index.append({k: entry[k] for k in ("id", "title", "series", "path", "source_ref", "source_label", "commit",
                                                "sha256", "historical", "claims_stated_in_report",
                                                "local_paths_redacted", "sanitized_artifact")})
    for r in RESTRICTED:
        allow.append({**r, "classification": "restricted-placeholder", "source_ref": None, "commit": None,
                      "path": None, "sha256": None, "contains_unpublished_outcomes": True,
                      "contains_protected_material": r["id"] == "restricted-protected",
                      "publication_review": "restricted", "sanitized_artifact": None})
    meta = {"schema": 1, "rule": "public-ref commits only; no protected paths; 0 outcome/secret/seal hits",
            "prior_seal_scanner": scanner_state}
    (out / "reports-allowlist.json").write_text(json.dumps({**meta, "items": allow}, indent=1) + "\n")
    (dest.parent / "reports-index.json").write_text(json.dumps({**meta, "restricted_placeholders": RESTRICTED,
                                                               "reports": index}, indent=1) + "\n")
    inc = sum(1 for x in allow if x["publication_review"] != "restricted")
    print(json.dumps({"candidates": len(items), "included": inc, "restricted": len(allow) - inc,
                      "prior_seal_scanner": scanner_state}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
