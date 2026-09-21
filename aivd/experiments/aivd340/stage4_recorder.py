"""Stage-4 observational growth-audit recorder (additive only; no growth semantics)."""
from __future__ import annotations

import copy
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aivd.experiments.aivd340.stage4_constants import RECORD_SCHEMA_VERSION


@dataclass
class Stage4Recorder:
    """Collects per-transition growth-audit events for Stage-4."""

    audit_id: str = ""
    episode_id: str = ""
    condition_id: str = ""
    control_id: str = ""
    mode_namespace: str = "CONTROLLED_INPUT"
    autonomous_discovery_credit: bool = False
    target_role: str = "S"
    seed: int = 0
    audit_mode: str = "OBS_ONLINE"
    representation_id: str = "R1"
    records: list[dict[str, Any]] = field(default_factory=list)
    integrity_ok: bool = True
    integrity_notes: list[str] = field(default_factory=list)
    controlled_injected: bool = False
    controlled_body_key: str | None = None
    _seq: int = 0

    def _envelope(self, *, event_kind: str, snapshot_phase: str, **extra: Any) -> dict[str, Any]:
        self._seq += 1
        row = {
            "record_schema_version": RECORD_SCHEMA_VERSION,
            "audit_id": self.audit_id or self.episode_id,
            "pool_snapshot_id": f"{self.episode_id}:s4:{self._seq}:{uuid.uuid4().hex[:8]}",
            "episode_id": self.episode_id,
            "condition_id": self.condition_id,
            "control_id": self.control_id,
            "mode_namespace": self.mode_namespace,
            "autonomous_discovery_credit": bool(self.autonomous_discovery_credit),
            "target_role": self.target_role,
            "seed": int(self.seed),
            "audit_mode": self.audit_mode,
            "representation_id": self.representation_id,
            "firewall_epoch": extra.pop("firewall_epoch", 0),
            "remaining_budget": extra.pop("remaining_budget", None),
            "snapshot_phase": snapshot_phase,
            "event_kind": event_kind,
            "claim_label": extra.pop("claim_label", "OBSERVED"),
            "leakage_flag": False,
            "recorded_at_unix": time.time(),
        }
        row.update(extra)
        return row

    def emit(self, *, event_kind: str, snapshot_phase: str, **extra: Any) -> dict[str, Any]:
        row = self._envelope(event_kind=event_kind, snapshot_phase=snapshot_phase, **extra)
        self.records.append(row)
        return row

    def mark_integrity_failure(self, note: str) -> None:
        self.integrity_ok = False
        self.integrity_notes.append(note)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_schema_version": RECORD_SCHEMA_VERSION,
            "audit_id": self.audit_id or self.episode_id,
            "episode_id": self.episode_id,
            "condition_id": self.condition_id,
            "control_id": self.control_id,
            "mode_namespace": self.mode_namespace,
            "autonomous_discovery_credit": self.autonomous_discovery_credit,
            "target_role": self.target_role,
            "seed": self.seed,
            "audit_mode": self.audit_mode,
            "representation_id": self.representation_id,
            "integrity_ok": self.integrity_ok,
            "integrity_notes": list(self.integrity_notes),
            "controlled_injected": self.controlled_injected,
            "controlled_body_key": self.controlled_body_key,
            "n_records": len(self.records),
            "records": copy.deepcopy(self.records),
        }

    def write_json(self, path: Path | str) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, default=str) + "\n")


__all__ = ["Stage4Recorder"]
