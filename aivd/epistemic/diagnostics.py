"""Pipeline-level diagnostics for global allocation (3.18)."""
from __future__ import annotations

from typing import Any

from aivd.epistemic.accounting import GlobalLedger
from aivd.epistemic.branch import BranchRegistry
from aivd.epistemic.reservation import ReservationBook
from aivd.epistemic.shadow import ShadowLog
from aivd.epistemic.types import ExperimentTraceRecord


def pipeline_experiment_slot_efficiency(
    traces: list[ExperimentTraceRecord],
    *,
    verified: bool,
    max_completion_p: float,
    budget_used: int,
    budget_total: int,
) -> float:
    """How effectively did the pipeline convert a fixed budget into verified-discovery progress?

    Transparent mix:
      0.40 · fraction of executed experiments that were informative (actual_ig > 0.01
             or security_relevance > 0.15)
      0.30 · mean positive completion-probability progress proxy (actual_ig clipped)
      0.30 · verified (1.0) else 0.5 · max branch completion probability

    Range approximately [0, 1]. Not an optimality claim.
    """
    n = max(1, len(traces))
    informative = sum(
        1 for t in traces
        if float(t.actual_ig) > 0.01 or float(t.security_relevance) > 0.15
    ) / n
    mean_progress = sum(max(0.0, float(t.actual_ig)) for t in traces) / n
    terminal = 1.0 if verified else 0.5 * max(0.0, min(1.0, float(max_completion_p)))
    used_frac = min(1.0, float(budget_used) / float(max(1, budget_total)))
    # Penalize spending the whole budget with no informative experiments
    return float(
        0.40 * informative
        + 0.30 * min(1.0, mean_progress * 4.0)
        + 0.30 * terminal
        - 0.05 * max(0.0, used_frac - informative)
    )


def budget_concentration(by_branch: dict[str, int]) -> float:
    """Herfindahl-style concentration in [0, 1]. 1 = one branch ate everything."""
    vals = [max(0, int(v)) for v in by_branch.values()]
    s = sum(vals)
    if s <= 0:
        return 0.0
    return float(sum((v / s) ** 2 for v in vals))


def ig_calibration_error(traces: list[ExperimentTraceRecord]) -> float:
    if not traces:
        return 0.0
    return sum(abs(float(t.expected_ig) - float(t.actual_ig)) for t in traces) / len(traces)


def first_index(traces: list[ExperimentTraceRecord], pred) -> int | None:
    for t in traces:
        if pred(t):
            return int(t.global_index)
    return None


def report(
    ledger: GlobalLedger,
    registry: BranchRegistry,
    book: ReservationBook,
    shadow: ShadowLog | None,
    *,
    verified: bool = False,
    false_positive: bool = False,
    unresolved_invisible: bool = False,
    brute_force: bool = False,
    secret_found: bool = False,
) -> dict[str, Any]:
    traces = ledger.traces
    n = len(traces)
    max_cp = max((b.completion_p for b in registry.branches.values()), default=0.0)
    starved = sum(1 for b in registry.branches.values() if b.state.value == "STARVED")
    abandoned = sum(1 for b in registry.branches.values() if b.state.value == "ABANDONED")
    first_inf = first_index(traces, lambda t: t.actual_ig > 0.01)
    first_causal = first_index(traces, lambda t: t.security_relevance > 0.2 and t.actual_ig > 0.02)
    first_disc = first_index(traces, lambda t: t.security_relevance >= 0.99)
    first_ver = first_index(traces, lambda t: t.verification_relevance >= 0.7) if secret_found else None
    mean_e = (sum(t.expected_ig for t in traces) / n) if n else 0.0
    mean_a = (sum(t.actual_ig for t in traces) / n) if n else 0.0
    opp = sum(float((b.meta or {}).get("opportunity_cost_total") or 0) for b in registry.branches.values())
    wait = sum(b.wait_time for b in registry.branches.values())
    deltas = []
    for b in registry.branches.values():
        if len(b.history) >= 2:
            # proxy: evidence change
            deltas.append(b.evidence_strength)
    slot_eff = pipeline_experiment_slot_efficiency(
        traces,
        verified=verified or secret_found,
        max_completion_p=max_cp,
        budget_used=ledger.used,
        budget_total=ledger.total,
    )
    diversity = len({t.subsystem for t in traces}) / max(1, len(ledger.by_subsystem) or 1)
    out: dict[str, Any] = {
        "budget_total": ledger.total,
        "budget_used": ledger.used,
        "budget_remaining": ledger.remaining(),
        "experiments_by_subsystem": dict(ledger.by_subsystem),
        "experiments_by_branch": dict(ledger.by_branch),
        "experiments_before_first_informative_signal": first_inf,
        "experiments_before_first_causal_signal": first_causal,
        "experiments_before_discovery": first_disc,
        "experiments_before_verification": first_ver,
        "branch_completion_probability": {
            k: v.completion_p for k, v in registry.branches.items()
        },
        "branch_completion_probability_delta": {
            k: v.evidence_strength for k, v in registry.branches.items()
        },
        "mean_expected_ig": mean_e,
        "mean_actual_ig": mean_a,
        "ig_calibration_error": ig_calibration_error(traces),
        "budget_reallocation_count": ledger.reallocation_count,
        "budget_reallocation_latency": wait,
        "reservation_release_count": len(book.released),
        "reservation_revocation_count": len(book.revoked),
        "branch_starvation_count": starved,
        "branch_abandonment_count": abandoned,
        "opportunity_cost_total": opp,
        "budget_concentration": budget_concentration(ledger.by_branch),
        "proposal_diversity": diversity,
        "verified_discoveries": 1 if (verified or secret_found) else 0,
        "false_positive_count": 1 if false_positive else 0,
        "unresolved_invisible_count": 1 if unresolved_invisible else 0,
        "brute_force_score": 1.0 if brute_force else 0.0,
        "legacy_vs_arbiter_choice_agreement": shadow.agreement_rate() if shadow else None,
        "legacy_vs_arbiter_regret": {
            "legacy_regret": shadow.legacy_regret() if shadow else None,
            "arbiter_regret": shadow.arbiter_regret() if shadow else None,
        },
        "pipeline_experiment_slot_efficiency": slot_eff,
        "invariant_ok": ledger.invariant_ok(),
    }
    return out


__all__ = [
    "pipeline_experiment_slot_efficiency",
    "budget_concentration",
    "ig_calibration_error",
    "report",
]
