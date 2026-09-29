"""Post-freeze scoring wrapper: frozen judge per model, RC4 F rule, dedup, endpoints."""

from aivd_rc3.verifier import judge

from aivd_rc4_multi.scoring import dedup, endpoints
from aivd_rc4_multi.scoring.relations import rescore_f_row


def score_model(ledger: dict, seal: dict) -> dict:
    frozen = judge(ledger, seal)  # unchanged RC3 decision (raises on unfrozen ledger / commitment mismatch)
    targets = {t["scenario_id"]: t for t in seal["targets"]}
    cands = {c["scenario_id"]: c for c in ledger.get("candidates", [])}
    rows = [rescore_f_row(r, targets[r["scenario_id"]], cands.get(r["scenario_id"])) for r in frozen["rows"]]
    return {"frozen_judge": frozen, "rows": rows, "candidates": cands,
            "verified_frozen_judge_only": frozen["verified_targets"],
            "verified_with_f_rule": sum(1 for r in rows if r["verified"])}


def score_all(scored: dict, seal: dict, *, contamination_pass: bool, historical_check=None) -> dict:
    """scored: model -> score_model(...) output."""
    targets = {t["scenario_id"]: t for t in seal["targets"]}
    per_model, pooled_pairs = {}, []
    fp = integrity = 0
    for m, s in scored.items():
        pairs = [(r, s["candidates"].get(r["scenario_id"])) for r in s["rows"] if r["verified"]]
        pooled_pairs += pairs
        c = dedup.classify(pairs, targets, historical_check=historical_check)
        c["families"] = {targets[sid]["relation"] for sid in c["counted"]}
        per_model[m] = c
        fp += len(s["frozen_judge"]["false_positives_security"])
        integrity += 1 if s["frozen_judge"]["classification"] == "INCONCLUSIVE" else 0
    pooled = dedup.classify(pooled_pairs, targets, historical_check=historical_check)
    pooled["families"] = {targets[sid]["relation"] for sid in pooled["counted"]}
    result = endpoints.evaluate(per_model, pooled, false_positives=fp, integrity_failures=integrity,
                                contamination_pass=contamination_pass)
    result["per_model"] = {m: {**v, "families": sorted(v["families"])} for m, v in per_model.items()}
    result["pooled"] = {**pooled, "families": sorted(pooled["families"])}
    return result
