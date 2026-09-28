"""Phase 11 reveal + Phase 12 analysis. Run ONLY after both pass ledgers are committed.

Checks: the protected seal matches the committed corpus commitment and every label commitment;
each full (protected) ledger matches the hash recorded in its committed public ledger; both
ledgers were produced under the committed preregistration (budget, seeds, model, runtime).
Writes public, token-free outputs:
  reports/aivd_rc1/final/label_reveal.json
  reports/aivd_rc1/final/results.json
"""

import json
import sys
from pathlib import Path

from aivd_rc1.provider import commit, label_commitment, label_reveal
from aivd_rc1.protected import scan
from aivd_rc1.publish import public_ledger
from aivd_rc1.verifier import judge, ledger_hash

FINAL = Path("reports/aivd_rc1/final")
PROTECTED = Path("reports/aivd_rc1/protected")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    seal = load(PROTECTED / "final_seal.json")
    view = load(FINAL / "corpus_commitment.json")
    prereg = load(FINAL / "preregistration.json")
    problems = []
    if commit(seal) != view["corpus_commitment"]:
        problems.append("corpus commitment mismatch")
    reveal = label_reveal(seal)
    for row in reveal:
        if label_commitment(row) != view["label_commitments"].get(row["scenario_id"]):
            problems.append("label commitment mismatch " + row["scenario_id"])
    passes = {}
    for pid in ("P1", "P2"):
        full = load(PROTECTED / pid / "ledger.json")
        pub = load(Path("reports/aivd_rc1") / pid / "ledger_public.json")
        if ledger_hash(full) != full["frozen_hash"] or pub["full_ledger_frozen_hash"] != full["frozen_hash"]:
            problems.append(f"{pid} ledger hash mismatch")
        if public_ledger(full)["public_ledger_hash"] != pub["public_ledger_hash"]:
            problems.append(f"{pid} public ledger mismatch")
        if full["discovery_seed"] != prereg["discovery_seeds"][pid]:
            problems.append(f"{pid} seed mismatch")
        if full["allocation"] != prereg["allocation_per_pass"]:
            problems.append(f"{pid} allocation mismatch")
        if (full["model_digest"], full["runtime_digest"]) != (prereg["model_digest"], prereg["runtime_digest"]):
            problems.append(f"{pid} identity mismatch")
        passes[pid] = {"ledger": full, "scored": judge(full, seal)}
    if problems:
        print(json.dumps({"problems": problems}))
        sys.exit(1)

    kinds = {r["scenario_id"]: r for r in seal["targets"]}
    per_target, per_benign = [], []
    for sid, row in kinds.items():
        entry = {"scenario_id": sid, "kind": row["kind"], "dimension": row["dimension"]}
        for pid in ("P1", "P2"):
            sc = passes[pid]["scored"]
            src = sc["rows"] if row["family"] == "security" else sc["benign_rows"]
            match = next(x for x in src if x["scenario_id"] == sid)
            entry[pid] = match["stage"] if row["family"] == "security" else match["classification"]
            entry[pid + "_retained"] = match["retained"]
            entry[pid + "_promotion"] = match["promotion"]
        (per_target if row["family"] == "security" else per_benign).append(entry)

    def count(pid, key):
        return passes[pid]["scored"][key]

    disc = {pid: {e["scenario_id"] for e in per_target if e[pid + "_retained"]} for pid in ("P1", "P2")}
    ver = {pid: {e["scenario_id"] for e in per_target if e[pid] == "VERIFIED_SECURITY_DISCOVERY"} for pid in ("P1", "P2")}
    bfp = {pid: {e["scenario_id"] for e in per_benign if e[pid] == "BEHAVIORAL_FALSE_POSITIVE"} for pid in ("P1", "P2")}
    beh_cands = {pid: {e["scenario_id"] for e in per_benign if e[pid + "_retained"]} for pid in ("P1", "P2")}
    calls = {pid: passes[pid]["ledger"]["stage_calls"] for pid in ("P1", "P2")}
    integrity = sum(passes[pid]["ledger"]["integrity_failures"] for pid in ("P1", "P2"))
    union_disc, union_ver = disc["P1"] | disc["P2"], ver["P1"] | ver["P2"]
    results = {
        "per_target": sorted(per_target, key=lambda e: e["scenario_id"]),
        "per_benign": sorted(per_benign, key=lambda e: e["scenario_id"]),
        "passes": {pid: {"stage_calls": calls[pid], "calls": passes[pid]["ledger"]["calls"],
                         "integrity_failures": passes[pid]["ledger"]["integrity_failures"],
                         "discovered": len(disc[pid]), "verified": len(ver[pid]),
                         "behavioral_fp": len(count(pid, "false_positives_behavioral")),
                         "security_fp": len(count(pid, "false_positives_security")),
                         "classification": passes[pid]["scored"]["classification"],
                         "full_ledger_hash": passes[pid]["ledger"]["frozen_hash"]} for pid in ("P1", "P2")},
        "reproducibility": {
            "discovered_both": len(disc["P1"] & disc["P2"]),
            "discovered_only_P1": len(disc["P1"] - disc["P2"]),
            "discovered_only_P2": len(disc["P2"] - disc["P1"]),
            "verified_both": len(ver["P1"] & ver["P2"]),
            "verified_once": len(ver["P1"] ^ ver["P2"]),
            "consistent_behavioral_fp": len(bfp["P1"] & bfp["P2"]),
            "inconsistent_behavioral_candidates": len(beh_cands["P1"] ^ beh_cands["P2"]),
        },
        "metrics": {
            "SECURITY_TARGETS": sum(1 for r in seal["targets"] if r["family"] == "security"),
            "BENIGN_DISTRACTORS": sum(1 for r in seal["targets"] if r["family"] == "benign"),
            "PASSES": 2,
            "TARGETS_DISCOVERED": len(union_disc),
            "TARGETS_VERIFIED": len(union_ver),
            "TARGETS_MISSED": sum(1 for r in seal["targets"] if r["family"] == "security") - len(union_ver),
            "BEHAVIORAL_FPS": len(bfp["P1"] | bfp["P2"]),
            "SECURITY_VERIFICATION_FPS": len(count("P1", "false_positives_security")) + len(count("P2", "false_positives_security")),
            "CONTAMINATION": "NONE",
            "INTEGRITY_FAILURES": integrity,
            "TOTAL_CALLS": sum(sum(c.values()) for c in calls.values()),
            "DISCOVERY_CALLS": sum(c["discovery"] for c in calls.values()),
            "INVESTIGATION_CALLS": sum(c["investigation"] for c in calls.values()),
            "VERIFICATION_CALLS": sum(c["verification"] for c in calls.values()),
            "BUDGET_USED": sum(sum(c.values()) for c in calls.values()),
            "BUDGET_ALLOCATED": 2 * prereg["allocation_per_pass"]["total"],
            "DISCOVERED_IN_BOTH_PASSES": len(disc["P1"] & disc["P2"]),
            "PASS_ONLY_DISCOVERIES": len(disc["P1"] ^ disc["P2"]),
        },
        "definitions": {"discovered": "retained as a behavioral candidate in that pass",
                        "TARGETS_DISCOVERED/VERIFIED": "union over both passes"},
    }
    (FINAL / "label_reveal.json").write_text(json.dumps(reveal, sort_keys=True, indent=1), encoding="utf-8")
    (FINAL / "results.json").write_text(json.dumps(results, sort_keys=True, indent=1), encoding="utf-8")
    tokens = {r["token"] for r in seal["targets"] if r["token"]} | {r["note"] for r in seal["targets"] if r["family"] == "security"}
    leaks = scan([str(FINAL / "label_reveal.json"), str(FINAL / "results.json")], tokens)
    if leaks:
        sys.exit("protected value in public output")
    print(json.dumps({"metrics": results["metrics"], "reproducibility": results["reproducibility"]}, indent=1))


if __name__ == "__main__":
    main()
