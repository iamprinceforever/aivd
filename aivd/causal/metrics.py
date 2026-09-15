"""Causal / unknown-dimension metrics — honest counters only."""
from __future__ import annotations

from typing import Any


def summarize_causal(trace: dict[str, Any]) -> dict[str, Any]:
    hyps = list(trace.get("hypotheses") or [])
    ent0 = float(trace.get("entropy_start") or 0.0)
    ent1 = float(trace.get("entropy_end") or 0.0)
    dim = trace.get("identified_dimension")
    return {
        "probes_used": int(trace.get("probes_used") or 0),
        "n_hypotheses": len(hyps),
        "hypothesis_entropy_start": ent0,
        "hypothesis_entropy_end": ent1,
        "hypothesis_entropy_drop": float(ent0 - ent1),
        "experiments_to_dimension_id": trace.get("experiments_to_dimension_id"),
        "identified_dimension": dim,
        "dimension_identified": bool(dim),
        "interaction_discovered": bool(trace.get("interaction_discovered")),
        "interaction_arity": trace.get("interaction_arity"),
        "stateful_detected": bool(trace.get("stateful_detected")),
        "temporal_detected": bool(trace.get("temporal_detected")),
        "indirect_detected": bool(trace.get("indirect_detected")),
        "false_correlation_rejected": bool(trace.get("false_correlation_rejected")),
        "handoff_amplify": bool(trace.get("handoff_amplify")),
        "handoff_investigate": bool(trace.get("handoff_investigate")),
        "gt_hit": trace.get("gt_hit"),
        "discovery_probability": 1.0 if trace.get("gt_hit") else 0.0,
        "ig_per_probe": float(trace.get("ig_sum") or 0.0) / max(1, int(trace.get("probes_used") or 1)),
        "causal_chain_accuracy": trace.get("causal_chain_accuracy"),
        "abandoned": bool(trace.get("abandoned")),
    }
