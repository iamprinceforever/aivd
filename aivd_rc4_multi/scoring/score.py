"""Post-freeze scoring wrapper (D2 = A, confirmed).

Two SEPARATELY LABELED results are always produced from the same frozen-judge output:
  A_E_ONLY       frozen aivd_rc3.verifier.judge stages exactly as returned; F targets are never counted
                 (the frozen judge cannot verify them). Scorable security targets: 20.
  A_F_INCLUSIVE  the same rows, plus the preregistered RC4 F rule applied to F rows only. 24 targets.
Adding F cannot change any A-E row, the benign rows, or the false-positive lists: both views share the
single frozen-judge result for those (tested).
Target exposure (D3 = A) is reported per model: which security / benign targets that model's own
discovery order actually reached.
"""

from aivd_rc3.verifier import judge

from aivd_rc4_multi.scoring import dedup, endpoints
from aivd_rc4_multi.scoring.relations import F_RELATION, rescore_f_row

A_E_ONLY = "A_E_ONLY"
A_F_INCLUSIVE = "A_F_INCLUSIVE"
VIEWS = (A_E_ONLY, A_F_INCLUSIVE)


def exposure(ledger: dict, seal: dict) -> dict:
    reached = set(ledger.get("explored", [])) | set(ledger.get("rejected", [])) | {
        c["scenario_id"] for c in ledger.get("candidates", [])}
    sec = [t for t in seal["targets"] if t["family"] == "security"]
    ben = [t for t in seal["targets"] if t["family"] == "benign"]
    ae = [t for t in sec if t["relation"] != F_RELATION]
    return {"discovery_seed": ledger.get("discovery_seed"),
            "security_exposed": sum(t["scenario_id"] in reached for t in sec), "security_total": len(sec),
            "security_exposed_a_e": sum(t["scenario_id"] in reached for t in ae), "security_total_a_e": len(ae),
            "benign_exposed": sum(t["scenario_id"] in reached for t in ben), "benign_total": len(ben),
            "exposed_security_ids": sorted(t["scenario_id"] for t in sec if t["scenario_id"] in reached),
            "not_exposed_security_ids": sorted(t["scenario_id"] for t in sec if t["scenario_id"] not in reached)}


def score_model(ledger: dict, seal: dict) -> dict:
    frozen = judge(ledger, seal)  # unchanged RC3 decision (raises on unfrozen ledger / commitment mismatch)
    targets = {t["scenario_id"]: t for t in seal["targets"]}
    cands = {c["scenario_id"]: c for c in ledger.get("candidates", [])}
    ae_rows = [dict(r, frozen_judge_stage=r["stage"]) for r in frozen["rows"]]
    af_rows = [rescore_f_row(r, targets[r["scenario_id"]], cands.get(r["scenario_id"])) for r in frozen["rows"]]
    return {"frozen_judge": frozen, "candidates": cands, "exposure": exposure(ledger, seal),
            "views": {A_E_ONLY: ae_rows, A_F_INCLUSIVE: af_rows},
            "rows": af_rows,
            "verified_frozen_judge_only": frozen["verified_targets"],
            "verified_with_f_rule": sum(1 for r in af_rows if r["verified"])}


def _view(scored: dict, seal: dict, view: str, *, contamination_pass: bool, historical_check) -> dict:
    targets = {t["scenario_id"]: t for t in seal["targets"]}
    per_model, pooled_pairs = {}, []
    fp = integrity = 0
    for m, s in scored.items():
        rows = s["views"][view]
        if view == A_E_ONLY:
            rows = [r for r in rows if targets[r["scenario_id"]]["relation"] != F_RELATION]
        pairs = [(r, s["candidates"].get(r["scenario_id"])) for r in rows if r["verified"]]
        pooled_pairs += pairs
        c = dedup.classify(pairs, targets, historical_check=historical_check)
        c["families"] = {targets[sid]["relation"] for sid in c["counted"]}
        per_model[m] = c
        fp += len(s["frozen_judge"]["false_positives_security"])
        integrity += 1 if s["frozen_judge"]["classification"] == "INCONCLUSIVE" else 0
    pooled = dedup.classify(pooled_pairs, targets, historical_check=historical_check)
    pooled["families"] = {targets[sid]["relation"] for sid in pooled["counted"]}
    total = 20 if view == A_E_ONLY else 24
    result = endpoints.evaluate(per_model, pooled, false_positives=fp, integrity_failures=integrity,
                                contamination_pass=contamination_pass, security_total=total)
    result["label"] = view
    result["scorable_security_targets"] = total
    result["per_model"] = {m: {**v, "families": sorted(v["families"])} for m, v in per_model.items()}
    result["pooled"] = {**pooled, "families": sorted(pooled["families"])}
    return result


def score_all(scored: dict, seal: dict, *, contamination_pass: bool, historical_check=None) -> dict:
    """scored: model -> score_model(...) output. Returns both labeled results + per-model exposure."""
    out = {v: _view(scored, seal, v, contamination_pass=contamination_pass, historical_check=historical_check)
           for v in VIEWS}
    out["target_exposure"] = {m: s["exposure"] for m, s in scored.items()}
    out["false_positives_security"] = {m: s["frozen_judge"]["false_positives_security"] for m, s in scored.items()}
    out["false_positives_behavioral"] = {m: s["frozen_judge"]["false_positives_behavioral"] for m, s in scored.items()}
    return out
