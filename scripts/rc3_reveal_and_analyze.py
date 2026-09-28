"""RC3 reveal + analysis. Run ONLY after both pass ledgers are committed.

Checks: the protected seal matches the committed corpus commitment and every label commitment;
each full (protected) ledger matches the hash recorded in its committed public ledger; both
ledgers were produced under the committed preregistration (budget, seeds, model, runtime, RC3
code/config hashes). Computes contamination evidence between the passes and the RC3
reproducibility report (L1-L5 + bitwise). Writes public, token-free outputs:
  reports/aivd_rc3/final/label_reveal.json
  reports/aivd_rc3/final/results.json

Terminology: "retained" = kept by the discovery stage as a behavioral candidate (NOT a discovery);
"promoted" = investigation promoted it to VERIFICATION_READY; "verified" = the pipeline's blind
decision was CONFIRMED and the isolated verifier confirmed the sealed value (the only discovery claim).
"""

import json
import sys
from pathlib import Path

from aivd_rc3.protected import scan
from aivd_rc3.provider import commit, label_commitment, label_reveal
from aivd_rc3.publish import public_ledger
from aivd_rc3.reproducibility import SUPPORTED_LEVEL, compare
from aivd_rc3.verifier import judge, ledger_hash

FINAL = Path("reports/aivd_rc3/final")
PROTECTED = Path("reports/aivd_rc3/protected")
PASSES = ("P1", "P2")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def contamination(a: dict, b: dict) -> dict:
    """Evidence that the passes share no trajectory, turn or candidate state."""
    def ids(ledger, key):
        return {r[key] for r in ledger.get("requests", [])}
    shared_traj = ids(a, "trajectory_id") & ids(b, "trajectory_id")
    shared_turn = ids(a, "turn_id") & ids(b, "turn_id")
    ca = {c["candidate_id"] for c in a.get("candidates", [])}
    cb = {c["candidate_id"] for c in b.get("candidates", [])}
    return {"shared_trajectory_ids": len(shared_traj), "shared_turn_ids": len(shared_turn),
            "shared_candidate_ids": len(ca & cb), "different_seeds": a["discovery_seed"] != b["discovery_seed"],
            "clean": not (shared_traj or shared_turn or (ca & cb)) and a["discovery_seed"] != b["discovery_seed"]}


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
    for pid in PASSES:
        full = load(PROTECTED / pid / "ledger.json")
        pub = load(Path("reports/aivd_rc3") / pid / "ledger_public.json")
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
        if full.get("config_hashes") != prereg["config_hashes"]:
            problems.append(f"{pid} config/code hash mismatch")
        passes[pid] = {"ledger": full, "scored": judge(full, seal)}
    if problems:
        print(json.dumps({"problems": problems}))
        sys.exit(1)

    kinds = {r["scenario_id"]: r for r in seal["targets"]}
    per_target, per_benign = [], []
    for sid, row in kinds.items():
        entry = {"scenario_id": sid, "kind": row["kind"], "dimension": row["dimension"],
                 "relation": row.get("relation", "BENIGN")}
        for pid in PASSES:
            sc = passes[pid]["scored"]
            src = sc["rows"] if row["family"] == "security" else sc["benign_rows"]
            match = next(x for x in src if x["scenario_id"] == sid)
            entry[pid] = match["stage"] if row["family"] == "security" else match["classification"]
            entry[pid + "_retained"] = match["retained"]
            entry[pid + "_promotion"] = match["promotion"]
            entry[pid + "_decision"] = match["decision"]
            entry[pid + "_blind_reason"] = match.get("blind_reason")
            entry[pid + "_claim_provenance"] = match.get("claim_provenance")
        (per_target if row["family"] == "security" else per_benign).append(entry)

    def count(pid, key):
        return passes[pid]["scored"][key]

    led = {pid: passes[pid]["ledger"] for pid in PASSES}
    ret = {pid: {e["scenario_id"] for e in per_target if e[pid + "_retained"]} for pid in PASSES}
    prom = {pid: {e["scenario_id"] for e in per_target if e[pid + "_promotion"] == "VERIFICATION_READY"} for pid in PASSES}
    ver = {pid: {e["scenario_id"] for e in per_target if e[pid] == "VERIFIED_SECURITY_DISCOVERY"} for pid in PASSES}
    bfp = {pid: {e["scenario_id"] for e in per_benign if e[pid] == "BEHAVIORAL_FALSE_POSITIVE"} for pid in PASSES}
    ben_ret = {pid: {e["scenario_id"] for e in per_benign if e[pid + "_retained"]} for pid in PASSES}
    calls = {pid: led[pid]["stage_calls"] for pid in PASSES}
    integrity = sum(led[pid]["integrity_failures"] for pid in PASSES)
    errors = [led[pid]["error"] for pid in PASSES if led[pid]["error"]]
    n_sec = sum(1 for r in seal["targets"] if r["family"] == "security")
    n_ben = sum(1 for r in seal["targets"] if r["family"] == "benign")
    union_ver = ver["P1"] | ver["P2"]
    contam = contamination(led["P1"], led["P2"])
    decisions = {pid: {e["scenario_id"]: (e[pid + "_promotion"], e[pid + "_decision"]) for e in per_target + per_benign}
                 for pid in PASSES}
    repro = {
        "cross_pass_compare": compare(led["P1"], led["P2"]),
        "note": "P1 and P2 use different discovery seeds and pass ids, so request bytes (L2) are not comparable "
                "across passes; L2 is established by the RC3 diagnostics and dev E2E. Cross-pass levels are keyed by scenario id.",
        "security_decision_agreement": sum(1 for s in decisions["P1"] if decisions["P1"][s] == decisions["P2"][s]),
        "security_decision_scenarios": len(decisions["P1"]),
        "verified_both": len(ver["P1"] & ver["P2"]), "verified_once": len(ver["P1"] ^ ver["P2"]),
        "retained_both": len(ret["P1"] & ret["P2"]), "retained_once": len(ret["P1"] ^ ret["P2"]),
        "consistent_behavioral_fp": len(bfp["P1"] & bfp["P2"]),
        "supported_level": SUPPORTED_LEVEL,
    }
    results = {
        "per_target": sorted(per_target, key=lambda e: e["scenario_id"]),
        "per_benign": sorted(per_benign, key=lambda e: e["scenario_id"]),
        "passes": {pid: {"stage_calls": calls[pid], "calls": led[pid]["calls"],
                         "integrity_failures": led[pid]["integrity_failures"], "error": led[pid]["error"],
                         "explored": len(led[pid]["explored"]),
                         "retained_total": len(led[pid]["candidates"]),
                         "discovery_selectivity": f'{len(led[pid]["candidates"])}/{len(led[pid]["explored"])} explored scenarios retained',
                         "security_retained": len(ret[pid]), "benign_retained": len(ben_ret[pid]),
                         "security_promoted": len(prom[pid]), "verified": len(ver[pid]),
                         "behavioral_fp": len(count(pid, "false_positives_behavioral")),
                         "security_fp": len(count(pid, "false_positives_security")),
                         "classification": passes[pid]["scored"]["classification"],
                         "full_ledger_hash": led[pid]["frozen_hash"]} for pid in PASSES},
        "contamination": contam,
        "reproducibility": repro,
        "metrics": {
            "SECURITY_TARGETS": n_sec, "BENIGN_DISTRACTORS": n_ben, "PASSES": 2,
            "TARGETS_RETAINED_BY_DISCOVERY_UNION": len(ret["P1"] | ret["P2"]),
            "TARGETS_PROMOTED_UNION": len(prom["P1"] | prom["P2"]),
            "TARGETS_VERIFIED": len(union_ver),
            "TARGETS_MISSED": n_sec - len(union_ver),
            "BEHAVIORAL_FPS": len(bfp["P1"] | bfp["P2"]),
            "SECURITY_VERIFICATION_FPS": len(count("P1", "false_positives_security")) + len(count("P2", "false_positives_security")),
            "CONTAMINATION": "NONE" if contam["clean"] else "DETECTED",
            "INTEGRITY_FAILURES": integrity, "PASS_ERRORS": len(errors),
            "TOTAL_CALLS": sum(sum(c.values()) for c in calls.values()),
            "DISCOVERY_CALLS": sum(c["discovery"] for c in calls.values()),
            "INVESTIGATION_CALLS": sum(c["investigation"] for c in calls.values()),
            "VERIFICATION_CALLS": sum(c["verification"] for c in calls.values()),
            "BUDGET_ALLOCATED": 2 * prereg["allocation_per_pass"]["total"],
            "RELATION_TYPES": len({r.get("relation") for r in seal["targets"] if r["family"] == "security"}),
            "DIMENSIONS": len({r["dimension"] for r in seal["targets"] if r["family"] == "security"}),
            "PROTECTED_ORIGIN_NOT_EXACT": sum(1 for e in per_target for pid in PASSES if e[pid] == "PROTECTED_ORIGIN_NOT_EXACT"),
        },
        "definitions": {"retained": "kept by discovery as a behavioral candidate; NOT a discovery claim",
                        "promoted": "investigation promoted to VERIFICATION_READY",
                        "verified": "blind decision CONFIRMED and sealed value confirmed by the isolated verifier",
                        "unions": "over both passes"},
    }
    (FINAL / "label_reveal.json").write_text(json.dumps(reveal, sort_keys=True, indent=1), encoding="utf-8")
    (FINAL / "results.json").write_text(json.dumps(results, sort_keys=True, indent=1), encoding="utf-8")
    from aivd_rc3.provenance import swap
    tokens = ({r["token"] for r in seal["targets"] if r["token"]} | {swap(r["token"]) for r in seal["targets"] if r["token"]}
              | {r["note"] for r in seal["targets"] if r["family"] == "security"})
    leaks = scan([str(FINAL / "label_reveal.json"), str(FINAL / "results.json")], tokens)
    if leaks:
        sys.exit("protected value in public output")
    print(json.dumps({"metrics": results["metrics"], "reproducibility": repro, "contamination": contam}, indent=1))


if __name__ == "__main__":
    main()
