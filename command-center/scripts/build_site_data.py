#!/usr/bin/env python3
"""Write public-data/site-data.json from read-only git refs plus the GitHub API snapshot recorded below.

usage: build_site_data.py --repo <git dir> --out <command-center dir>
The snapshot values were read with read-only GitHub API calls (repository, branch list, rulesets, workflows)
on the observed_at date. Re-run and update them before each deploy if they change.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

GITHUB_SNAPSHOT = {
    "observed_at": "2026-10-10",
    "source": "GitHub REST API, read-only (repository, branches, rulesets, workflows)",
    "repository": "iamprinceforever/aivd",
    "visibility": "public",
    "default_branch": "main",
    "has_pages": False,
    "main_protected": False,
    "main_rulesets": 0,
    "workflows": 0,
    "secret_scanning": "disabled",
    "pages_url_if_enabled": "https://iamprinceforever.github.io/aivd/",
}
OMIT_REFS = ("research/aivd-rc5-a2-local-uncommitted",)
LIFECYCLE = [
    ("software_built", "Software built", "The guard module and guarded entry scripts exist in the research worktree."),
    ("runtime_available", "Runtime available", "Pinned runtime files are present and match their sha256. The runtime is not started."),
    ("prerequisites_satisfied", "Prerequisites satisfied", "Every readiness gate in aivd_rc6_guard passes, and so does the memory gate."),
    ("explicitly_authorized", "Explicitly authorized", "The approval record, the operator-supplied environment authorization and the prereg hash all agree."),
    ("running", "Running", "A guarded run started by this controller session is in progress."),
    ("completed", "Completed", "The guarded entry script exited successfully in this controller session."),
    ("independently_validated", "Independently validated", "An independent human reviewer has validated the result. The software never asserts this."),
]
RUN_GATES = [
    ("ENTRY", "Guarded entry script present"),
    ("GUARD_START_RUNTIME", "aivd_rc6_guard allows START_RUNTIME"),
    ("GUARD_MODEL_CALL", "aivd_rc6_guard allows MODEL_CALL"),
    ("PARTB_ENV", "AIVD_RC6_PARTB_AUTHORIZED supplied by the operator's shell"),
    ("MEMORY", "MemAvailable >= 7600000 kB"),
    ("RUNTIME_FILES", "Runtime files match pinned hashes"),
    ("NO_FOREIGN_RUNTIME", "No Ollama process already running"),
    ("NO_ACTIVE_RUN", "No run already in progress"),
]
REVEAL_GATES = [
    ("ENTRY", "Guarded analysis entry present"),
    ("GUARD_REVEAL", "aivd_rc6_guard allows REVEAL"),
    ("GUARD_SCORE", "aivd_rc6_guard allows SCORE"),
    ("NO_ACTIVE_RUN", "No run in progress"),
]
POLICY = [
    ("rc6-not-authorized", "RC6 execution is not authorized as of this build: no corpus, secrets, seals, model "
     "calls, reveal or scoring.", "researcher instruction for this build (2026-10-10)"),
    ("never-published", "Unpublished outcomes, protected material (seals, ledgers, wire records, label salts), "
     "secrets and local machine paths are excluded from this site and its build output.",
     "build scanners (scripts/scan_outgoing.py) and the reports allowlist"),
    ("static-is-readonly", "The public site is static and read-only. Guarded operations exist only through a "
     "local controller bound to 127.0.0.1.", "COMMAND_CENTER_SECURITY.md"),
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = subprocess.run(["git", "-C", a.repo, "for-each-ref", "--format=%(refname) %(objectname)",
                          "refs/remotes/origin", "refs/tags"], capture_output=True, text=True, check=True).stdout
    refs = []
    for line in out.splitlines():
        name, sha = line.split()
        if name.endswith("/HEAD") or any(o in name for o in OMIT_REFS):
            continue
        if name.startswith("refs/tags/"):
            sha = subprocess.run(["git", "-C", a.repo, "rev-parse", f"{name}^{{commit}}"], capture_output=True,
                                 text=True, check=True).stdout.strip()
            name = "tag " + name[len("refs/tags/"):]
        else:
            name = name[len("refs/remotes/origin/"):]
        refs.append({"name": name, "commit": sha})
    data = {
        "schema": 1,
        "generated_from": "git remote-tracking refs (equal to git ls-remote at observation) + GitHub API snapshot",
        "github_snapshot": GITHUB_SNAPSHOT,
        "public_refs": refs,
        "lifecycle_states": [{"id": i, "label": l, "meaning": m} for i, l, m in LIFECYCLE],
        "run_gate_catalog": [{"id": i, "label": l, "source": "controller/server.py run_gates"} for i, l in RUN_GATES],
        "reveal_gate_catalog": [{"id": i, "label": l, "source": "controller/server.py reveal_gates"}
                                for i, l in REVEAL_GATES],
        "preregistered_models": ["qwen3:1.7b", "llama3.2:3b", "qwen3:8b"],
        "memory_threshold_kb": 7600000,
        "policy": [{"id": i, "statement": s, "source": src} for i, s, src in POLICY],
    }
    p = Path(a.out) / "public-data" / "site-data.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1) + "\n")
    print(json.dumps({"public_refs": len(refs)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
