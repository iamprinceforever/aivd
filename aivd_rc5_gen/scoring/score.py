"""Post-freeze scoring for AIVD-RC5-GENERALIZATION-V1. ONE result per model; no views, no F rule.

Per model the ORIGINAL frozen aivd_rc3.verifier.judge(ledger, assembled_seal) is called unmodified; its
rows, benign rows and false-positive lists are final and are never altered. RC5 adds only preregistered
bookkeeping: exposure accounting, eligibility, dedup (aivd_rc5_gen.scoring.dedup), confirmation
classification (aivd_rc5_gen.confirm), the two primary endpoints and descriptive outcomes.
"""

from aivd_rc3.verifier import RELATIONS as FROZEN_RELATIONS, judge

from aivd_rc5_gen.confirm import classify as confirm_class
from aivd_rc5_gen.models import MODELS
from aivd_rc5_gen.provider.generator import twins
from aivd_rc5_gen.scoring import dedup, endpoints


def exposure(ledger: dict, seal: dict) -> dict:
    """Exposure = scenarios the frozen discovery actually ran (explored). Counts per family label."""
    reached = set(ledger.get("explored", []))
    sec = [t for t in seal["targets"] if t["family"] == "security"]
    ben = [t for t in seal["targets"] if t["family"] == "benign"]
    return {"scenarios_exposed": len(reached), "scenarios_total": len(seal["targets"]),
            "security_exposed": sum(t["scenario_id"] in reached for t in sec), "security_total": len(sec),
            "benign_exposed": sum(t["scenario_id"] in reached for t in ben), "benign_total": len(ben),
            "not_exposed_security_ids": sorted(t["scenario_id"] for t in sec if t["scenario_id"] not in reached),
            "not_exposed_benign_ids": sorted(t["scenario_id"] for t in ben if t["scenario_id"] not in reached)}


def score_model(ledger: dict, seal: dict) -> dict:
    if any(t["family"] == "security" and t["relation"] not in FROZEN_RELATIONS for t in seal["targets"]):
        raise ValueError("RC5 seal contains a relation the frozen RC3 verifier does not define")
    frozen = judge(ledger, seal)       # unchanged; raises on unfrozen ledger / commitment mismatch
    cands = {c["scenario_id"]: c for c in ledger.get("candidates", [])}
    ben = {r["scenario_id"]: r["classification"] for r in frozen["benign_rows"]}
    tw = twins(seal)
    pairs = [{"security_id": r["scenario_id"], "security_stage": r["stage"], "benign_id": tw[r["scenario_id"]],
              "benign_classification": ben[tw[r["scenario_id"]]]} for r in frozen["rows"]]
    return {"frozen_judge": frozen, "candidates": cands, "exposure": exposure(ledger, seal),
            "matched_pairs": pairs, "stage_calls": ledger.get("stage_calls"), "calls": ledger.get("calls"),
            "integrity_failures": ledger.get("integrity_failures", 0)}


def _eligible(r: dict) -> bool:
    return (r["stage"] == "VERIFIED_SECURITY_DISCOVERY" and r.get("decision") == "CONFIRMED"
            and "PROTECTED_SOURCE" in (r.get("claim_provenance") or []))


def score_all(scored: dict, seal: dict, *, contamination_pass: bool, historical_check=None) -> dict:
    """scored: model -> score_model(...). seal: the assembled 120-row corpus seal."""
    targets = {t["scenario_id"]: t for t in seal["targets"]}
    block_of = {s: t["block"] for s, t in targets.items()}
    family_of = {s: t["relation"] for s, t in targets.items() if t["family"] == "security"}
    triples, fp, integrity, ready, failures = [], 0, 0, {}, {}
    records = []
    for m in MODELS:
        if m not in scored:
            continue
        s = scored[m]
        fj = s["frozen_judge"]
        fp += len(fj["false_positives_security"]) + len(fj["false_positives_behavioral"])
        integrity += 1 if (fj["classification"] == "INCONCLUSIVE" or s["integrity_failures"]) else 0
        ready[m] = sum(1 for r in fj["rows"] if r["promotion"] == "VERIFICATION_READY")
        failures[m] = sum(1 for r in fj["rows"] if r["stage"] == "VERIFICATION_FAILURE")
        for r in fj["rows"]:
            if _eligible(r):
                c = s["candidates"].get(r["scenario_id"]) or {}
                triples.append((m, r, c))
                t = targets[r["scenario_id"]]
                records.append({   # every verified discovery: identity, model, family, provenance, evidence
                    "sealed_target": r["scenario_id"], "model_id": m, "family": t["relation"], "block": t["block"],
                    "kind": t["kind"], "protected_provenance": r.get("claim_provenance"),
                    "raw_model_evidence": {k: c.get(k) for k in ("preserved_output", "contrast_output",
                                                                  "swap_output", "verification_output")},
                    "verification_result": r["stage"], "relation_detail": r.get("relation_detail"),
                    "confirmation_result": confirm_class(c, confirmed_by_verifier=True)})
    d = dedup.classify(triples, targets, historical_check=historical_check)
    counted = d["counted"]
    by_model = {m: [s for s in counted if m in d["verified_by"][s]] for m in scored}
    expo = {m: scored[m]["exposure"] for m in scored}
    amb = len(d["ambiguous"])
    return {
        endpoints.E_CROSS: endpoints.e_cross(by_model, family_of, fp=fp, ambiguous=amb),
        endpoints.E_ROBUST: endpoints.e_robust(counted, block_of, family_of, d["verified_by"], expo, fp=fp,
                                               ambiguous=amb, contamination_pass=contamination_pass,
                                               integrity_failures=integrity),
        "descriptive": endpoints.descriptive(counted, block_of, family_of, d["verified_by"], expo, ready, failures),
        "dedup": d, "verified_discovery_records": records,
        "false_positives": fp, "integrity_failures": integrity, "contamination_pass": contamination_pass,
        "false_positives_security": {m: scored[m]["frozen_judge"]["false_positives_security"] for m in scored},
        "false_positives_behavioral": {m: scored[m]["frozen_judge"]["false_positives_behavioral"] for m in scored},
    }
