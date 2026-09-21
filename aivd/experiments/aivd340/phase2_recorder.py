"""Observational Phase-2 pool/score/rank/select recorder (additive only)."""
from __future__ import annotations

import copy
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from aivd.experiments.aivd340.phase2_constants import RECORD_SCHEMA_VERSION


@dataclass
class Phase2Recorder:
    """Collects pre-selection / post-selection / post-verify / terminal snapshots."""

    episode_id: str = ""
    condition_id: str = ""
    mode: str = "A"
    autonomous_discovery_credit: bool = True
    controlled_availability: bool = False
    target_role: str = "S"
    seed: int = 0
    representation_id: str = "R1"
    records: list[dict[str, Any]] = field(default_factory=list)
    integrity_ok: bool = True
    integrity_notes: list[str] = field(default_factory=list)
    mode_b_injected: bool = False
    mode_b_injection_body_key: str | None = None
    _seq: int = 0

    def _envelope(self, *, event_kind: str, snapshot_phase: str, **extra: Any) -> dict[str, Any]:
        self._seq += 1
        row = {
            "record_schema_version": RECORD_SCHEMA_VERSION,
            "pool_snapshot_id": f"{self.episode_id}:snap:{self._seq}:{uuid.uuid4().hex[:8]}",
            "generation_id": extra.pop("generation_id", f"gen-{self._seq}"),
            "parent_id": extra.pop("parent_id", None),
            "episode_id": self.episode_id,
            "condition_id": self.condition_id,
            "mode": self.mode,
            "autonomous_discovery_credit": bool(self.autonomous_discovery_credit),
            "controlled_availability": bool(self.controlled_availability),
            "target_role": self.target_role,
            "seed": int(self.seed),
            "firewall_epoch": extra.pop("firewall_epoch", 0),
            "representation_id": self.representation_id,
            "event_kind": event_kind,
            "snapshot_phase": snapshot_phase,
            "remaining_budget": extra.pop("remaining_budget", None),
            "leakage_flag": False,
            "record_label": "observed",
            "recorded_at_unix": time.time(),
        }
        row.update(extra)
        return row

    def record_pre_selection(
        self,
        *,
        candidates: list[dict[str, Any]],
        ranking_ordered_body_keys: list[str],
        ties: list[dict[str, Any]],
        selection_rule_id: str,
        tie_break_rule_id: str,
        remaining_budget: Any,
        firewall_epoch: int = 0,
        generation_id: str | None = None,
        event_kind: str = "rank",
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = self._envelope(
            event_kind=event_kind,
            snapshot_phase="pre_selection",
            generation_id=generation_id or f"gen-{self._seq + 1}",
            remaining_budget=remaining_budget,
            firewall_epoch=firewall_epoch,
            candidates=copy.deepcopy(candidates),
            pool_size=len(candidates),
            ranking_ordered_body_keys=list(ranking_ordered_body_keys),
            ties=copy.deepcopy(ties),
            selection_rule_id=selection_rule_id,
            tie_break_rule_id=tie_break_rule_id,
            tie_break_inputs={},
            selected_candidate_id=None,
            selected_body_key=None,
        )
        if extra:
            row.update(extra)
        self.records.append(row)
        return row

    def record_post_selection(
        self,
        *,
        selected_candidate_id: str | None,
        selected_body_key: str | None,
        rejected_candidates: list[dict[str, Any]],
        remaining_budget: Any,
        firewall_epoch: int = 0,
        generation_id: str | None = None,
        action: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = self._envelope(
            event_kind="select",
            snapshot_phase="post_selection",
            generation_id=generation_id or f"gen-{self._seq + 1}",
            remaining_budget=remaining_budget,
            firewall_epoch=firewall_epoch,
            selected_candidate_id=selected_candidate_id,
            selected_body_key=selected_body_key,
            rejected_candidates=copy.deepcopy(rejected_candidates),
            action=action,
        )
        if extra:
            row.update(extra)
        self.records.append(row)
        return row

    def record_mode_b_availability(self, *, body_key: str, remaining_budget: Any, firewall_epoch: int = 0) -> dict[str, Any]:
        self.mode_b_injected = True
        self.mode_b_injection_body_key = body_key
        row = self._envelope(
            event_kind="mode_b_availability",
            snapshot_phase="pre_selection",
            remaining_budget=remaining_budget,
            firewall_epoch=firewall_epoch,
            body_key=body_key,
            origin="controlled_availability_mode_b",
            autonomous_discovery_credit=False,
            controlled_availability=True,
            claim_label="CONTROLLED_INPUT",
        )
        self.records.append(row)
        return row

    def record_post_verify(
        self,
        *,
        verification_candidate_id: str | None,
        verification_body_key: str | None,
        verification_result: str,
        verification_reason_code: str | None = None,
        remaining_budget: Any = None,
        firewall_epoch: int = 0,
    ) -> dict[str, Any]:
        row = self._envelope(
            event_kind="verify",
            snapshot_phase="post_verify",
            remaining_budget=remaining_budget,
            firewall_epoch=firewall_epoch,
            verification_candidate_id=verification_candidate_id,
            verification_body_key=verification_body_key,
            verification_result=verification_result,
            verification_reason_code=verification_reason_code,
        )
        self.records.append(row)
        return row

    def record_terminal(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        row = self._envelope(
            event_kind="terminal",
            snapshot_phase="terminal",
            remaining_budget=payload.get("budget_remaining"),
            firewall_epoch=int(payload.get("firewall_epoch") or 0),
            terminal_payload={
                k: payload.get(k)
                for k in (
                    "terminal_state",
                    "pipeline_verified",
                    "strict_independence",
                    "secret_found",
                    "n_generation_records",
                    "leftover_at_firewall_decision",
                )
            },
        )
        self.records.append(row)
        return row

    def mark_integrity_failure(self, note: str) -> None:
        self.integrity_ok = False
        self.integrity_notes.append(note)

    def pre_selection_count(self) -> int:
        return sum(1 for r in self.records if r.get("snapshot_phase") == "pre_selection" and r.get("event_kind") in ("rank", "grow", "compose", "select"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "condition_id": self.condition_id,
            "mode": self.mode,
            "autonomous_discovery_credit": self.autonomous_discovery_credit,
            "controlled_availability": self.controlled_availability,
            "target_role": self.target_role,
            "seed": self.seed,
            "representation_id": self.representation_id,
            "integrity_ok": self.integrity_ok,
            "integrity_notes": list(self.integrity_notes),
            "mode_b_injected": self.mode_b_injected,
            "mode_b_injection_body_key": self.mode_b_injection_body_key,
            "n_records": len(self.records),
            "records": list(self.records),
        }

    def dump(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, default=str) + "\n")


def candidate_entry(
    *,
    candidate_id: str,
    body_key: str,
    origin: str | None,
    parent_id: str | None,
    representation_id: str,
    growth_or_composition_op: str | None,
    score: float | None,
    rank: int | None,
    selected: bool = False,
    rejection_category: str | None = None,
    rejection_reason: str | None = None,
    score_components: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "body_key": body_key,
        "identity": body_key,
        "origin": origin,
        "parent_id": parent_id,
        "representation_id": representation_id,
        "growth_or_composition_op": growth_or_composition_op,
        "score": score,
        "score_components": score_components,
        "rank": rank,
        "rejection_category": rejection_category,
        "rejection_reason": rejection_reason,
        "selected": selected,
        "verification_candidate": False,
        "verification_result": None,
        "in_pool": True,
    }


__all__ = ["Phase2Recorder", "candidate_entry"]
