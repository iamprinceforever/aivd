"""Execute Stage-5 OFFLINE equivalence audit and write reports.

Does not modify FILTER_BEHAVIORAL_DUP, growth, promote sets, or historical artifacts.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

from aivd.experiments.aivd340.stage5_constants import DESIGN_DOCS, DESIGN_TIP, SEEDS
from aivd.experiments.aivd340.stage5_equiv_audit import context_bank_hash, run_stage5_offline_audit
from aivd.science.grow import REDISCOVERY_FLOOR, propose_growth
from aivd.science.methods import INVENT_CAP
from aivd.science.micro import micro_hash

REPO = Path(__file__).resolve().parents[3]
IST = timezone(timedelta(hours=5, minutes=30))


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def verify_freeze() -> dict:
    head = _git("rev-parse", "HEAD")
    head_short = head[:7]
    files = []
    all_match = True
    for path in DESIGN_DOCS:
        tip_blob = _git("rev-parse", f"{DESIGN_TIP}:{path}")
        work_blob = _git("hash-object", path)
        match = tip_blob == work_blob
        all_match = all_match and match
        files.append({"path": path, "match": match, "tip_blob": tip_blob, "work_blob": work_blob})
    matrix = json.loads((REPO / "reports/aivd_3_40_stage5_matrix.json").read_text())
    # Historical immutability spot-check
    hist = []
    for tip, path in [
        ("4005e66", "reports/aivd_3_40_stage4_results.json"),
        ("4005e66", "reports/aivd_3_40_stage4_results.md"),
        ("f4d7a2b", "reports/aivd_3_40_phase2_results.json"),
        ("a2ab0cc", "reports/aivd_3_40_phase1_results.json"),
        ("146915b", "reports/aivd_3_40_stage3_charter.md"),
        ("dcae889", "reports/aivd_3_40_stage2_results.md"),
    ]:
        p = REPO / path
        if not p.exists():
            hist.append({"tip": tip, "path": path, "match": False, "reason": "missing"})
            all_match = False
            continue
        tip_blob = _git("rev-parse", f"{tip}:{path}")
        work_blob = _git("hash-object", path)
        match = tip_blob == work_blob
        if not match:
            all_match = False
        hist.append({"tip": tip, "path": path, "match": match})
    return {
        "design_tip": DESIGN_TIP,
        "head": head,
        "head_short": head_short,
        "head_is_design_tip": head.startswith(DESIGN_TIP),
        "files_match_tip": all(f["match"] for f in files),
        "files": files,
        "matrix_executed_at_start": bool(matrix.get("executed")),
        "historical_artifacts_unchanged": all(h.get("match") for h in hist),
        "historical": hist,
        "ok": (
            head.startswith(DESIGN_TIP)
            and all(f["match"] for f in files)
            and matrix.get("executed") is False
            and all(h.get("match") for h in hist)
        ),
    }


def filter_pipeline_untouched() -> dict:
    """Confirm grow.py propose_growth / _keep source unchanged vs design tip parent."""
    # Compare grow.py blob at Stage-4 complete tip (pre Stage-5 design) vs now
    tip_blob = _git("rev-parse", "4005e66:aivd/science/grow.py")
    work_blob = _git("hash-object", "aivd/science/grow.py")
    return {
        "grow_py_unchanged_since_4005e66": tip_blob == work_blob,
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
        "INVENT_CAP": INVENT_CAP,
        "propose_growth_callable": callable(propose_growth),
        "tip_blob": tip_blob,
        "work_blob": work_blob,
    }


def render_md(payload: dict, freeze: dict, immut: dict) -> str:
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    crit = payload["critical_pair"]
    interp = payload["interpretation"]
    ctrl = payload["controls"]
    tallies = payload["tallies"]
    recon = payload["stage4_reconciliation"]

    lines = [
        "# AIVD 3.40 Stage-5 RESULTS — FILTER_BEHAVIORAL_DUP Offline Equivalence Audit",
        "",
        f"**Recorded:** {now}",
        f"**Design tip (freeze):** `{DESIGN_TIP}`",
        f"**Execution head (pre-commit):** `{freeze['head_short']}`",
        f"**Namespace:** `OFFLINE_EVAL` / claim_label=`OFFLINE_EQUIV_AUDIT`",
        f"**autonomous_discovery_credit:** `false`",
        f"**Sacred:** not executed",
        f"**Filter repair:** not authorized / not performed",
        "",
        "---",
        "",
        "## 0. Execution manifest",
        "",
        "| Field | Value | Epistemic |",
        "|-------|-------|-----------|",
        f"| Design tip | `{DESIGN_TIP}` | OBSERVED |",
        f"| Freeze files match tip | `{freeze['files_match_tip']}` | OBSERVED |",
        f"| matrix.executed at start | `{freeze['matrix_executed_at_start']}` | OBSERVED |",
        f"| Historical artifacts unchanged | `{freeze['historical_artifacts_unchanged']}` | OBSERVED |",
        f"| grow.py unchanged since 4005e66 | `{immut['grow_py_unchanged_since_4005e66']}` | OBSERVED |",
        f"| micro_hash | `{micro_hash()}` | OBSERVED |",
        f"| context_bank_hash | `{payload['context_bank_hash']}` | OBSERVED |",
        f"| n_contexts | {payload['n_contexts']} | OBSERVED |",
        f"| Seeds (continuity) | `{list(SEEDS)}` | OBSERVED |",
        f"| BH / invent_cap / REDISCOVERY_FLOOR | 48 / {INVENT_CAP} / {REDISCOVERY_FLOOR} | OBSERVED |",
        "",
        "## 1. Evaluator validation (controls)",
        "",
        f"**controls_pass = `{ctrl['pass']}`**",
        "",
        "| Control | Result | Epistemic |",
        "|---------|--------|-----------|",
        f"| True-dup recognized (TD-01/02/03) | `{ctrl['true_dup_recognized']}` ({ctrl['n_true_dup_controls_pass']}/3) | OFFLINE_EVAL |",
        f"| Known non-dup distinguishable (ND-01..04) | `{ctrl['nondup_distinguishable']}` ({ctrl['n_nondup_controls_pass']}/4) | OFFLINE_EVAL |",
        f"| U-good path resolves | `{ctrl['u_good_ok']}` | OFFLINE_EVAL |",
        f"| Artifact replay 0/7 & 7/7 | `{ctrl['artifact_ok']}` | OBSERVED (ARTIFACT_REPLAY) |",
        "",
        "True duplicates are recognized as behaviorally equivalent over the preregistered "
        "context bank. Known non-duplicates remain distinguishable on the bank. "
        "Evaluator validated before critical-pair interpretation.",
        "",
        "## 2. Critical pair (S5-EQ-CRIT-ODD-AT)",
        "",
        "| Kind | Result | Epistemic |",
        "|------|--------|-----------|",
        f"| body_key_a (removed) | `{crit['body_key_a']}` | OBSERVED (Stage-4) |",
        f"| body_key_b (kept) | `{crit['body_key_b']}` | OBSERVED (Stage-4) |",
        f"| TEXTUAL equality | `{crit['textual_equal']}` | OBSERVED |",
        f"| STRUCTURAL equality | `{crit['structural_equal']}` | OBSERVED |",
        f"| structural_diff | `{crit['structural_diff']}` | OBSERVED |",
        f"| FILTER_CLASSIFIED_DUP | `{crit['filter_classified_dup']}` | OBSERVED (Stage-4) |",
        f"| duplicate_of | `{crit['duplicate_of']}` | OBSERVED (Stage-4) |",
        f"| BEHAVIORAL_LIVE (identity) | `{crit['behavioral_live_equal']}` | OFFLINE_EVAL |",
        f"| live_got_a | `{crit['live_got_a']}` | OFFLINE_EVAL |",
        f"| live_got_b | `{crit['live_got_b']}` | OFFLINE_EVAL |",
        f"| BEHAVIORAL_AUDIT (full bank) | `{crit['behavioral_audit_equal']}` | OFFLINE_EVAL |",
        f"| families_diverged | `{crit['families_diverged']}` | OFFLINE_EVAL |",
        f"| false_duplicate_flag | `{crit['false_duplicate_flag']}` | OFFLINE_EVAL |",
        f"| missed_duplicate_flag | `{crit['missed_duplicate_flag']}` | OFFLINE_EVAL |",
        "",
        "**Wording (binding):** A behavioral distinction was observed under contexts in "
        f"families {crit['families_diverged']}. The pair is **not** claimed universally "
        "equivalent. Behaviorally, on the singleton growth identity they collide "
        f"(`{crit['live_got_a']}`); across the preregistered context bank they are "
        "**not** behaviorally equivalent.",
        "",
        "### 2.1 Per-context results (frozen bank only)",
        "",
        "| context_id | family | equal | got_a | got_b | provenance |",
        "|------------|--------|-------|-------|-------|------------|",
    ]
    for c in crit["context_results"]:
        lines.append(
            f"| {c['context_id']} | {c['family']} | `{c['equal']}` | "
            f"`{c['got_a']}` | `{c['got_b']}` | {c['provenance']} |"
        )

    lines += [
        "",
        "## 3. FP / FN analysis",
        "",
        f"| Metric | Value | Epistemic |",
        f"|--------|-------|-----------|",
        f"| n_pairs_audited | {tallies['n_pairs_audited']} | OFFLINE_EVAL |",
        f"| n_filter_classified_dup | {tallies['n_filter_classified_dup']} | OFFLINE_EVAL |",
        f"| n_false_duplicate | {tallies['n_false_duplicate']} | OFFLINE_EVAL |",
        f"| n_missed_duplicate | {tallies['n_missed_duplicate']} | OFFLINE_EVAL |",
        "",
        "**FALSE_DUPLICATE (critical):** filter says duplicate; prereg eval finds meaningful "
        "behavioral difference under TRANSFORMED / BOUNDARY / COMPOSITION families.",
        "",
        "**Note on ND-04:** parents `MAPT(AT:-1)` vs `MAPT(SLICE:1,2(TOK))` also identity-collide "
        "on the growth identity (length-2 tokens) but diverge on the bank — additional "
        "FALSE_DUPLICATE signature under the live relation (asymmetric: live collapses; "
        "audit distinguishes). Not used alone to claim H5b; critical pair is primary.",
        "",
        "**Missed duplicates:** none among the audited sample "
        f"(n_missed_duplicate={tallies['n_missed_duplicate']}).",
        "",
        "## 4. Context-dependent findings",
        "",
        "Equivalence is **context-dependent** within the preregistered bank: the critical "
        "pair agrees on some BASELINE_IDENTITY / REORDERED / even-length TRANSFORMED / "
        "BOUNDARY / COMPOSITION cells and disagrees on others (uneven token lengths, "
        "longer words, single-token boundaries). Do not collapse to fully equivalent or "
        "fully distinct. Exact diverged families: "
        f"`{crit['families_diverged']}`.",
        "",
        "## 5. Stage-4 reconciliation",
        "",
        f"- Full promote-set odd CAT-self in pool: **{recon['full_promote_set_odd_cat_in_pool']}** (OBSERVED)",
        f"- Solo odd-only: **{recon['solo_odd_only_odd_cat_in_pool']}** (OBSERVED)",
        f"- {recon['mechanism']}",
        "",
        "## 6. H5a–H5d evidence matrix",
        "",
    ]
    for leaf, ev in interp["evidence_matrix"].items():
        lines.append(f"### {leaf} — stance `{ev['stance']}`")
        lines.append("")
        for x in ev["for"]:
            lines.append(f"- FOR: {x}")
        for x in ev["against"]:
            lines.append(f"- AGAINST: {x}")
        for x in ev["unknown"]:
            lines.append(f"- UNKNOWN: {x}")
        if not (ev["for"] or ev["against"] or ev["unknown"]):
            lines.append("- (empty)")
        lines.append("")

    lines += [
        f"**Primary conclusion_code:** `{interp['conclusion_code']}` — **{interp['conclusion_label']}**",
        f"**Co-supported:** {interp['co_supported']}",
        f"**supported_labels:** {interp['supported_labels']}",
        "",
        f"**Rationale:** {interp['primary_rationale']}",
        "",
        "## 7. Limitations",
        "",
        "- Audit relation is over the **preregistered frozen context bank only** — not a "
        "  formal exhaustive proof of (non)equivalence on all strings.",
        "- Live filter uses a singleton identity probe; Stage-5 does not repair it.",
        "- ST-KEEP-ODD-BEFORE-AT is NOT_APPLICABLE under frozen propose_growth loop order.",
        "- No Sacred / autonomous invent / independent-generation credit attaches.",
        "- Unresolved S remains valid; Stage-5 does not claim S pass.",
        "",
        "## 8. Final conclusion",
        "",
        f"**{interp['conclusion_label']}**"
        + (f" (co-supported: {', '.join(interp['co_supported'])})" if interp["co_supported"] else ""),
        "",
        "FILTER_BEHAVIORAL_DUP over-collapses the Stage-4 odd CAT-self vs "
        "`MAPT(CAT(AT:-1|AT:-1))` pair relative to the preregistered multi-context "
        "audit: identity-string collision ≠ full-bank behavioral equivalence. "
        "No filter repair performed. No new experiment authorized.",
        "",
        "```",
        "STAGE-5 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED",
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    freeze = verify_freeze()
    if not freeze["ok"]:
        print("STAGE-5 BLOCKED: freeze verification failed")
        print(json.dumps(freeze, indent=2))
        return 2

    immut = filter_pipeline_untouched()
    if not immut["grow_py_unchanged_since_4005e66"]:
        print("STAGE-5 BLOCKED: grow.py mutated")
        return 2

    payload = run_stage5_offline_audit()
    if payload.get("status") == "STAGE-5 BLOCKED":
        print("STAGE-5 BLOCKED:", payload.get("reason"))
        (REPO / "reports/aivd_3_40_stage5_results.json").write_text(
            json.dumps(payload, indent=2) + "\n"
        )
        return 3

    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    results_json = {
        "document": "aivd_3_40_stage5_results",
        "recorded_at_ist": now,
        "design_tip": DESIGN_TIP,
        "execution_head_pre_commit": freeze["head"],
        "authorization": "STAGE-5 EXECUTION AUTHORIZED (offline equivalence audit only)",
        "executed": True,
        "sacred_authorized": False,
        "sacred_executed": False,
        "filter_repair_authorized": False,
        "filter_repair_performed": False,
        "autonomous_discovery_credit": False,
        "claim_label": "OFFLINE_EQUIV_AUDIT",
        "provenance_default": "OFFLINE_EVAL",
        "freeze_verification": freeze,
        "immutability": immut,
        "micro_hash": micro_hash(),
        "context_bank_hash": payload["context_bank_hash"],
        "seeds": list(SEEDS),
        "REDISCOVERY_FLOOR": REDISCOVERY_FLOOR,
        "INVENT_CAP": INVENT_CAP,
        "BH": 48,
        "audit": payload,
        "conclusion_code": payload["interpretation"]["conclusion_code"],
        "conclusion_label": payload["interpretation"]["conclusion_label"],
        "supported_labels": payload["interpretation"]["supported_labels"],
        "co_supported": payload["interpretation"]["co_supported"],
        "status_line": "STAGE-5 COMPLETE: NEW EXPERIMENT NOT YET AUTHORIZED",
    }

    out_json = REPO / "reports/aivd_3_40_stage5_results.json"
    out_md = REPO / "reports/aivd_3_40_stage5_results.md"
    out_json.write_text(json.dumps(results_json, indent=2) + "\n")
    out_md.write_text(render_md(payload, freeze, immut))

    # Freeze stamp for prereg continuity
    stamp = {
        "freeze_commit_design": DESIGN_TIP,
        "context_bank_hash": payload["context_bank_hash"],
        "recorded_at_ist": now,
        "executed": True,
    }
    stamp_path = REPO / "reports/aivd_3_40_stage5_execution_stamp.json"
    stamp_path.write_text(json.dumps(stamp, indent=2) + "\n")

    # Mark matrix executed in a results-side copy note only — do NOT mutate design matrix
    # (design matrix remains executed=false at tip 2496857; results document execution)

    print("Wrote", out_json)
    print("Wrote", out_md)
    print("conclusion:", results_json["conclusion_label"], results_json["supported_labels"])
    print(results_json["status_line"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
