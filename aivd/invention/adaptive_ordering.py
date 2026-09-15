"""Adaptive Search Ordering — 3.11 layer over 3.9/3.10 invention.

Pipeline: invent → families → initial priority → TEST → observe →
update evidence → recalculate residual salience + family value → REORDER → next.

Config: adaptive_ordering_mode / invention modes adaptive|adaptive_full (default off).
No Holdout-named rules; no GT inspection; priority decay ≠ blacklist.
"""
from __future__ import annotations

from typing import Any

from aivd.invention.archive import FamilyArchive
from aivd.invention.dynamic_ranking import rank_dynamically, ranking_snapshot, family_values
from aivd.invention.evidence_update import update_evidence
from aivd.invention.intervention_space import Intervention
from aivd.invention.priority_history import PriorityHistory
from aivd.invention.residual_salience import residual_salience, salience_linked_stems
from aivd.invention.search_scheduler import AdaptiveBudget, SearchScheduler


ADAPTIVE_MODES = frozenset({
    "adaptive", "adaptive_full", "adaptive_heuristic",
})


def is_adaptive_mode(mode: str | None) -> bool:
    m = (mode or "off").lower().strip()
    return m in ADAPTIVE_MODES


def _base_gen_mode(mode: str) -> str:
    m = (mode or "off").lower().strip()
    if m in ("adaptive", "adaptive_full"):
        return "full"
    if m == "adaptive_heuristic":
        return "heuristic"
    return m


class AdaptiveOrderingState:
    """Episode state for adaptive reorder loop."""

    def __init__(
        self,
        *,
        mode: str = "adaptive",
        seed: int = 0,
        ablation: str | None = None,
        saturation_enabled: bool = True,
        revival_enabled: bool = True,
    ):
        self.mode = (mode or "adaptive").lower().strip()
        self.seed = int(seed)
        self.ablation = ablation
        self.archive = FamilyArchive(
            saturation_enabled=saturation_enabled,
            revival_enabled=revival_enabled,
        )
        self.priority_history = PriorityHistory()
        self.scheduler = SearchScheduler(
            archive=self.archive,
            priority_history=self.priority_history,
            seed=self.seed,
            budget=AdaptiveBudget(),
            ablation=ablation,
        )
        self.search_trace: list[dict[str, Any]] = []
        self.step_i = 0
        self.residual_context: dict[str, Any] = {}

    def initial_order(
        self,
        cands: list[Intervention],
        *,
        residual_context: dict[str, Any] | None = None,
        seen_sequences: set[str] | None = None,
        batch_size: int = 8,
    ) -> list[Intervention]:
        self.residual_context = dict(residual_context or {})
        sal = residual_salience(self.residual_context)
        ordered, steps = self.scheduler.select_batch(
            cands,
            residual_context=self.residual_context,
            seen_sequences=seen_sequences,
            batch_size=batch_size,
        )
        self.search_trace.append({
            "step": self.step_i,
            "kind": "initial_order",
            "salience": sal,
            "stem_order_head": salience_linked_stems(self.residual_context)[:12],
            "family_values_head": dict(list(family_values(
                self.archive,
                residual_context=self.residual_context,
                priority_history=self.priority_history,
            ).items())[:8]),
            "selection": steps,
            "ranking": ranking_snapshot(ordered),
        })
        self.step_i += 1
        return ordered

    def after_test(
        self,
        *,
        inv: Intervention,
        effect: float,
        success: bool,
        obs_meta: dict[str, Any] | None = None,
        remaining: list[Intervention],
        seen_sequences: set[str] | None = None,
    ) -> list[Intervention]:
        """Observe → update evidence → recalculate → REORDER remaining."""
        fid = (inv.meta or {}).get("family_id") or "unknown"
        feats = (inv.meta or {}).get("family_features") or {}
        evidence = update_evidence(
            residual_context=self.residual_context,
            archive=self.archive,
            priority_history=self.priority_history,
            family_id=fid,
            candidate_id=inv.id,
            effect=effect,
            success=success,
            obs_meta=obs_meta,
            features=feats,
        )
        self.residual_context = evidence["residual_context"]

        reordered = rank_dynamically(
            remaining, self.archive,
            residual_context=self.residual_context,
            seen_sequences=seen_sequences,
            priority_history=self.priority_history,
            ablation=self.ablation,
        )
        # Optionally re-batch via scheduler for explore/exploit tilt
        if len(reordered) > 1 and self.mode in ("adaptive", "adaptive_full"):
            batch, sel_steps = self.scheduler.select_batch(
                reordered,
                residual_context=self.residual_context,
                seen_sequences=seen_sequences,
                batch_size=len(reordered),
            )
            reordered = batch
        else:
            sel_steps = []

        self.search_trace.append({
            "step": self.step_i,
            "kind": "reorder_after_test",
            "tested_id": inv.id,
            "tested_sequence": list(inv.sequence),
            "family_id": fid,
            "effect": effect,
            "success": success,
            "evidence": {
                "salience": evidence["salience"],
                "family_priority": evidence["family_priority"],
                "revived_priorities": evidence["revived_priorities"],
                "archive_revived": evidence["archive_revived"],
            },
            "selection": sel_steps,
            "new_ranking": ranking_snapshot(reordered),
            "reason": (
                "update_evidence→residual_salience+family_value→reorder"
            ),
        })
        self.step_i += 1
        return reordered

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "ablation": self.ablation,
            "n_search_steps": len(self.search_trace),
            "search_trace": list(self.search_trace),
            "archive": self.archive.as_dict(),
            "priority_history": self.priority_history.as_dict(),
            "scheduler": self.scheduler.as_dict(),
            "residual_salience": residual_salience(self.residual_context),
        }


def counterfactual_ordering_score(
    inv: Intervention,
    *,
    residual_context: dict[str, Any] | None = None,
) -> float:
    """Score for discriminating H1/H2 under residual — used in unit tests / audit."""
    ctx = residual_context or {}
    if inv.strategy != "counterfactual":
        return 0.0
    n_sec = len(ctx.get("security_shaped_residuals") or [])
    unexplained = float(ctx.get("unexplained") or 0.0)
    sal = residual_salience(ctx)["aggregate"]
    return min(1.0, 0.4 + 0.2 * (1 if n_sec else 0) + 0.2 * unexplained + 0.2 * sal)
