"""Discovery metrics — honest counters only."""
from __future__ import annotations

from typing import Any


def summarize_discovery(trace: dict[str, Any]) -> dict[str, Any]:
    steps = list(trace.get("steps") or [])
    ampl = list(trace.get("amplify_steps") or [])
    strengths = [s.get("strength") for s in steps if s.get("strength")]
    first_signal_i = next((i for i, s in enumerate(steps) if s.get("strength") in ("weak", "medium", "strong")), None)
    first_strong_i = next((i for i, s in enumerate(steps) if s.get("strength") == "strong"), None)
    return {
        "n_steps": len(steps),
        "probes_used": int(trace.get("probes_used") or 0),
        "time_to_first_signal": first_signal_i,
        "time_to_strong": first_strong_i,
        "weak_signal_detected": any(s == "weak" for s in strengths),
        "medium_signal_detected": any(s == "medium" for s in strengths),
        "strong_signal_detected": any(s == "strong" for s in strengths),
        "amplification_steps": len(ampl),
        "amplification_success": bool(trace.get("handed_off")),
        "abandoned": bool(trace.get("abandoned") or trace.get("disappeared")),
        "frontier_visits": int(trace.get("frontier_visits") or 0),
        "handoff_investigate": bool(trace.get("handoff_investigate")),
        "discovery_probability": 1.0 if trace.get("gt_hit") else 0.0,
        "false_positive": bool(trace.get("false_positive")),
        "ig_per_probe": float(trace.get("ig_sum") or 0.0) / max(1, int(trace.get("probes_used") or 1)),
    }
