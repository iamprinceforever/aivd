"""Honest 3.7 metrics — never fabricate; novelty ≠ vulnerability."""
from __future__ import annotations

from typing import Any

from aivd37.unknowns.terminal import TerminalState, is_vulnerability


def summarize_unknowns(trace: dict[str, Any]) -> dict[str, Any]:
    term = trace.get("terminal") or {}
    state = term.get("terminal_state") or trace.get("terminal_state")
    return {
        "probes_used": int(trace.get("probes_used") or 0),
        "terminal_state": state,
        "is_vulnerability": bool(term.get("is_vulnerability")) if "is_vulnerability" in term else is_vulnerability(state or ""),
        "classification": term.get("classification"),
        "chosen_axis": trace.get("chosen_axis"),
        "sweep_actionable": bool((trace.get("sweep") or {}).get("actionable")),
        "security_shaped_residuals": list((trace.get("sweep") or {}).get("security_shaped_residuals") or []),
        "preferred_over_out_len": bool((trace.get("sweep") or {}).get("preferred_over_out_len")),
        "mode": trace.get("mode"),
    }


def aggregate_runs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows) or 1
    verified = sum(1 for r in rows if r.get("terminal_state") == TerminalState.VERIFIED.value)
    invisible = sum(1 for r in rows if r.get("terminal_state") == TerminalState.UNRESOLVED_INVISIBLE.value)
    rejected = sum(1 for r in rows if r.get("terminal_state") == TerminalState.REJECTED.value)
    unresolved = sum(1 for r in rows if r.get("terminal_state") == TerminalState.UNRESOLVED.value)
    vulns = sum(1 for r in rows if r.get("is_vulnerability"))
    return {
        "n": len(rows),
        "verified_rate": verified / n,
        "unresolved_invisible_rate": invisible / n,
        "rejected_rate": rejected / n,
        "unresolved_rate": unresolved / n,
        "vulnerability_rate": vulns / n,
        "mean_probes": sum(float(r.get("probes_used") or 0) for r in rows) / n,
    }
