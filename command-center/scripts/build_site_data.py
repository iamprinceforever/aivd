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
    "observed_at": "2026-10-11",
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
# Latest research tip. It is LOCAL: its ancestry holds unpublished commits, so the RC6 pre-push gate refuses it and
# it is deliberately absent from public_refs. Only pinned, scanned documents from it are archived.
RESEARCH_TIP = {
    "branch": "research/aivd-rc6-partb-readiness",
    "commit": "cb8dc31fc0c7b0644cb2d45e000892c6825a1758",
    "date": "2026-10-10",
    "on_public_ref": False,
    "note": "Local research tip (RC6 Part B readiness closure). Not pushed: its ancestry carries unpublished commits "
            "and the RC6 pre-push gate refuses the outgoing set. Publication-safe documents from it are archived "
            "individually after every scan.",
}
# Research journey. Outcome values: PUBLIC_REPORTS (see the archive), RESTRICTED (exists, withheld),
# NOT_RECORDED (no result exists), NOT_APPLICABLE. No unpublished figure is ever written here.
JOURNEY = [
    ("rc1_rc3", "RC1 to RC3 release candidates", "2026-09-28", "FROZEN", "PUBLIC_REPORTS",
     "Pipeline built, audited and frozen across three release candidates; freeze records are public tags.",
     ["tag AIVD-RC1", "tag AIVD-RC2", "tag AIVD-RC3"]),
    ("post_rc3_rc4", "POST-RC3 model generalization and RC4-MULTI-V1", "2026-09-29", "FROZEN", "PUBLIC_REPORTS",
     "Sealed corpora, preregistrations and local-model evaluations; RC4 multi-target design and sealed results.",
     ["research/aivd-post-rc3-local-v1-final", "research/aivd-rc4-multi-v1-design"]),
    ("rc5_design", "RC5-GENERALIZATION-V1 design", "2026-09-30", "DESIGN_PUBLIC", "PUBLIC_REPORTS",
     "Design phase only: target families, frozen verifier, model matrix, blinding, scoring and reproduction "
     "protocols.", ["research/aivd-rc5-generalization-v1-design"]),
    ("rc5_execution", "RC5 execution phase", "2026-10-09", "EXECUTED_LOCAL", "RESTRICTED",
     "Corpus binding, per-model authorizations and the execution amendment were recorded locally. The execution "
     "record and every outcome are unpublished and withheld pending the researcher's publication decision.", []),
    ("rc6_design", "RC6 investigation design and breakthrough criteria", "2026-10-09", "DESIGNED", "NOT_APPLICABLE",
     "Diagnostic design, hypotheses and preregistered breakthrough criteria (criteria only, no results).",
     ["local tip"]),
    ("rc6_part_a", "RC6 Part A: synthetic diagnostics", "2026-10-09", "COMPLETED_LOCAL", "RESTRICTED",
     "Synthetic diagnostics with 0 model calls, followed by evidence-flow design work. The Part A results document "
     "restates earlier-study figures and stays restricted.", ["local tip"]),
    ("rc6_partb_readiness", "RC6 Part B readiness", "2026-10-10", "BUILT_NOT_AUTHORIZED", "NOT_RECORDED",
     "Runner, decision-trace fields, guarded runtime controller, validity and replication gates, frozen analysis, "
     "runtime restore record, independent-replication preregistration (registered locally, not externally) and a "
     "fail-closed pre-push gate.", ["local tip"]),
    ("rc6_partb_guarded", "RC6 Part B experiment (guarded)", None, "NOT_AUTHORIZED", "NOT_RECORDED",
     "Not authorized. The guard refuses runtime start, model calls, reveal and scoring; the Command Center "
     "pipeline reports the Part B step as BLOCKED until every gate and an explicit operator authorization agree.",
     []),
]
# The built end-to-end process, in order. state: what holds today, never an outcome.
PROCESS = [
    ("author", "Design and preregister", "Design docs, preregistration drafts and breakthrough criteria are "
     "written before any corpus, run or reveal.", "BUILT"),
    ("freeze", "Freeze", "Analysis code and preregistration are hash-pinned (FROZEN_ANALYSIS, prereg sha256); any "
     "change needs a recorded re-freeze.", "BUILT"),
    ("guard", "Guard", "aivd_rc6_guard refuses START_RUNTIME, MODEL_CALL, REVEAL, SCORE and PUSH unless an approved "
     "record, an operator-supplied authorization and the prereg hash all agree.", "ENFORCED"),
    ("controller", "Local controller", "A paired controller on 127.0.0.1 exposes only fixed, server-defined "
     "operations with CSRF, timeouts, a single run slot and redacted logs.", "BUILT"),
    ("pipeline", "One-click pipeline", "preflight, guard, rc6_tests, full_suite, cc_tests, scans, model, partb, "
     "summary: each step reports PASS, FAIL, BLOCKED, SKIPPED or ERROR.", "BUILT"),
    ("partb_gate", "Part B gate", "Fail closed: guard, memory, runtime hashes, model readiness and the operator's "
     "authorization must all pass before the guarded entry script may start.", "NOT_AUTHORIZED"),
    ("reveal_gate", "Reveal and score gates", "G_REPLICATION and G_VALIDITY must pass before any reveal or "
     "scoring.", "NOT_AUTHORIZED"),
    ("validate", "Independent validation", "A separate human reviewer validates any result. The software never "
     "asserts this state.", "NOT_RECORDED"),
    ("publish", "Publication gate", "RC6 pre-push checks K1 to K5, the Command Center scanners and the reports "
     "allowlist decide what can leave the machine.", "ENFORCED"),
    ("site", "Static site", "This read-only site shows only scanned, sanitized data.", "BUILT"),
]
POLICY = [
    ("rc6-not-authorized", "RC6 execution is not authorized as of this build: no corpus, secrets, seals, model "
     "calls, reveal or scoring. Part B stays fail-closed in the controller.",
     "researcher instruction for this build (2026-10-11)"),
    ("rc6-tip-local", "The latest research tip (research/aivd-rc6-partb-readiness @ cb8dc31) is local and not on "
     "a public ref; only pinned, scanned RC6 readiness and design documents from it are archived.",
     "scripts/build_reports_archive.py STAGED list"),
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
        "research_tip": RESEARCH_TIP,
        "research_journey": [{"id": i, "label": l, "date": d, "status": st, "outcome": o, "summary": sm,
                              "refs": refs} for i, l, d, st, o, sm, refs in JOURNEY],
        "process_flow": [{"id": i, "label": l, "detail": d, "state": st} for i, l, d, st in PROCESS],
    }
    p = Path(a.out) / "public-data" / "site-data.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=1) + "\n")
    print(json.dumps({"public_refs": len(refs)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
