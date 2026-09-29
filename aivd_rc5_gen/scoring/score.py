"""Post-freeze scoring wrapper for AIVD-RC5-GENERALIZATION-V1. ONE result (no views, no F rule).

Per (model, block) run the ORIGINAL frozen aivd_rc3.verifier.judge(ledger, block_seal) is called
unmodified; its rows, benign rows and false-positive lists are final. RC5 then pools the frozen rows over
the 9 runs and applies only preregistered bookkeeping (eligibility, dedup, replication, endpoints).
"""

from aivd_rc3.verifier import RELATIONS as FROZEN_RELATIONS, judge

from aivd_rc5_gen import BLOCKS
from aivd_rc5_gen.models import FAMILY, MODELS
from aivd_rc5_gen.provider.generator import RC4_VERIFIED_TEMPLATE_KINDS, twins
from aivd_rc5_gen.scoring import confirmation, dedup, endpoints


def exposure(ledger: dict, seal: dict) -> dict:
    reached = set(ledger.get("explored", [])) | set(ledger.get("rejected", [])) | {
        c["scenario_id"] for c in ledger.get("candidates", [])}
    sec = [t for t in seal["targets"] if t["family"] == "security"]
    ben = [t for t in seal["targets"] if t["family"] == "benign"]
    return {"discovery_seed": ledger.get("discovery_seed"),
            "scenarios_explored": len(set(ledger.get("explored", []))), "scenarios_total": len(seal["targets"]),
            "security_exposed": sum(t["scenario_id"] in reached for t in sec), "security_total": len(sec),
            "benign_exposed": sum(t["scenario_id"] in reached for t in ben), "benign_total": len(ben),
            "not_exposed_security_ids": sorted(t["scenario_id"] for t in sec if t["scenario_id"] not in reached)}


def score_run(ledger: dict, seal: dict) -> dict:
    """One (model, block) run. Raises (frozen judge) on an unfrozen ledger or commitment mismatch."""
    if any(t["family"] == "security" and t["relation"] not in FROZEN_RELATIONS for t in seal["targets"]):
        raise ValueError("RC5 seal contains a relation the frozen RC3 verifier does not define")
    frozen = judge(ledger, seal)
    ben = {r["scenario_id"]: r["classification"] for r in frozen["benign_rows"]}
    tw = twins(seal)
    pairs = [{"security_id": r["scenario_id"], "kind": r["kind"], "security_stage": r["stage"],
              "benign_id": tw[r["scenario_id"]], "benign_classification": ben[tw[r["scenario_id"]]]}
             for r in frozen["rows"]]
    return {"block": seal["block"], "frozen_judge": frozen,
            "candidates": {c["scenario_id"]: c for c in ledger.get("candidates", [])},
            "exposure": exposure(ledger, seal), "matched_pairs": pairs,
            "stage_calls": ledger.get("stage_calls"), "calls": ledger.get("calls"),
            "integrity_failures": ledger.get("integrity_failures", 0)}


def _eligible_row(r: dict) -> bool:
    return (r["stage"] == "VERIFIED_SECURITY_DISCOVERY" and r.get("decision") == "CONFIRMED"
            and "PROTECTED_SOURCE" in (r.get("claim_provenance") or []))


def score_all(scored: dict, seals: dict, *, contamination_pass: bool, isolation_pass: bool,
              calls_reconciled: bool, historical_check=None) -> dict:
    """scored: (model_id, block) -> score_run(...). seals: block -> block seal."""
    targets = {}
    for b, s in seals.items():
        for t in s["targets"]:
            targets[t["scenario_id"]] = {**t, "block": b}
    fp_sec, fp_beh, integrity = {}, {}, 0
    pairs, verified_by, cands = [], {}, {}
    per_run = {}
    for (m, b), s in sorted(scored.items()):
        fj = s["frozen_judge"]
        key = f"{m}|block_{b}"
        fp_sec[key] = fj["false_positives_security"]
        fp_beh[key] = fj["false_positives_behavioral"]
        integrity += (1 if fj["classification"] == "INCONCLUSIVE" or s["integrity_failures"] else 0)
        ok_rows = [r for r in fj["rows"] if _eligible_row(r)]
        for r in ok_rows:
            c = s["candidates"].get(r["scenario_id"])
            pairs.append((r, c))
            verified_by.setdefault(r["scenario_id"], set()).add(m)
            cands.setdefault(r["scenario_id"], {})[m] = c or {}
        per_run[key] = {"frozen_verified": fj["verified_targets"], "eligible_rows": sorted(r["scenario_id"] for r in ok_rows),
                        "exposure": s["exposure"], "stage_calls": s["stage_calls"], "calls": s["calls"],
                        "matched_pairs": s["matched_pairs"]}
    pooled = dedup.classify(pairs, targets, historical_check=historical_check)
    eligible = pooled["eligible"]
    vb = {sid: sorted(v) for sid, v in verified_by.items()}
    conf = confirmation.replication(eligible, targets, vb, cands, FAMILY)
    per_model = {m: sorted(s for s in eligible if m in vb.get(s, [])) for m in MODELS}
    per_block = {b: sorted(s for s in eligible if targets[s]["block"] == b) for b in BLOCKS}
    fp_total = sum(len(v) for v in fp_sec.values())
    complete = sorted(scored) == sorted((m, b) for m in MODELS for b in BLOCKS)
    gate = {"runs_present": len(scored), "runs_expected": endpoints.EXPECTED_RUNS, "runs_complete": complete,
            "false_positives_security": fp_total,
            "false_positives_behavioral": sum(len(v) for v in fp_beh.values()),
            "integrity_failures": integrity, "contamination_pass": bool(contamination_pass),
            "isolation_pass": bool(isolation_pass), "calls_reconciled": bool(calls_reconciled)}
    gate["passed"] = (complete and fp_total == 0 and integrity == 0 and gate["contamination_pass"]
                      and gate["isolation_pass"] and gate["calls_reconciled"])
    result = endpoints.evaluate(eligible=eligible, counted=pooled["counted"], targets=targets, verified_by=vb,
                                model_family=FAMILY, gate=gate, confirmation=conf,
                                per_model=per_model, per_block=per_block)
    result.update({"label": "FROZEN_RC3_VERIFIER_ONLY", "security_targets": 60, "benign_targets": 60,
                   "pooled": pooled, "verified_by": vb, "confirmation": conf, "per_run": per_run,
                   "per_model_eligible": per_model, "per_block_eligible": {str(b): v for b, v in per_block.items()},
                   "false_positives_security": fp_sec, "false_positives_behavioral": fp_beh,
                   "relation_families_by_eligible": {s: targets[s]["relation"] for s in eligible},
                   "rc4_template_lineage": sorted(s for s in eligible if targets[s]["kind"] in RC4_VERIFIED_TEMPLATE_KINDS)})
    return result
