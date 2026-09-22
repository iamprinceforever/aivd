"""AIVD 3.41 — behavior-preserving planner audit ledger.

Append-only observational instrumentation. Gate: AIVD41_PLANNER_AUDIT.
When OFF (default), every public entrypoint is a no-op: zero budget, zero
planner RNG, zero ordering/hashing/timing effects on the decision path.

When ON, records propose/reject/score/rank/select/invent/skip into a
side-channel never consulted by the planner.

Does NOT change propose_atoms entries, score/rank/select math, grow.py,
FILTER_BEHAVIORAL_DUP, invent_cap, novelty, or firewall behavior.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

MODE_ENV = "AIVD41_PLANNER_AUDIT"
_TRUE = frozenset({"1", "true", "yes", "on", "audit"})

# Lifecycle states (minimum set from charter — do not infer missing ones)
NEVER_PROPOSED = "NEVER_PROPOSED"
NOT_REACHED_BEFORE_BUDGET_EXHAUSTION = "NOT_REACHED_BEFORE_BUDGET_EXHAUSTION"
PROPOSED = "PROPOSED"
REJECTED = "REJECTED"
SCORED = "SCORED"
RANKED = "RANKED"
SELECTED = "SELECTED"
INVENTED = "INVENTED"
SKIPPED = "SKIPPED"
NOT_RECORDED = "NOT_RECORDED"

REQUIRED_FIELDS = (
    "candidate_key",
    "candidate_family",
    "candidate_origin",
    "candidate_generation_method",
    "proposal_index",
    "proposal_epoch",
    "proposal_state",
    "rejection_state",
    "rejection_reason",
    "score",
    "score_components",
    "rank",
    "selection_state",
    "selection_reason",
    "budget_before",
    "budget_after",
    "firewall_epoch",
    "novelty_state",
    "behavioral_identity",
    "body_key",
    "language_key",
    "parent_key",
    "provenance",
    "seed",
    "plant_id",
)

_thread_local = threading.local()


def _tls() -> dict[str, Any]:
    d = getattr(_thread_local, "state", None)
    if d is None:
        d = {"forced_on": False, "ledger": None}
        _thread_local.state = d
    return d


def audit_enabled() -> bool:
    raw = os.environ.get(MODE_ENV, "")
    if str(raw).strip().lower() in _TRUE:
        return True
    return bool(_tls().get("forced_on"))


def enable_audit(*, force: bool = True) -> None:
    _tls()["forced_on"] = bool(force)


def disable_audit() -> None:
    _tls()["forced_on"] = False


@dataclass
class LedgerRow:
    event: str
    candidate_key: Any = NOT_RECORDED
    candidate_family: Any = NOT_RECORDED
    candidate_origin: Any = NOT_RECORDED
    candidate_generation_method: Any = NOT_RECORDED
    proposal_index: Any = NOT_RECORDED
    proposal_epoch: Any = NOT_RECORDED
    proposal_state: Any = NOT_RECORDED
    rejection_state: Any = NOT_RECORDED
    rejection_reason: Any = NOT_RECORDED
    score: Any = NOT_RECORDED
    score_components: Any = NOT_RECORDED
    rank: Any = NOT_RECORDED
    selection_state: Any = NOT_RECORDED
    selection_reason: Any = NOT_RECORDED
    budget_before: Any = NOT_RECORDED
    budget_after: Any = NOT_RECORDED
    firewall_epoch: Any = NOT_RECORDED
    novelty_state: Any = NOT_RECORDED
    behavioral_identity: Any = NOT_RECORDED
    body_key: Any = NOT_RECORDED
    language_key: Any = NOT_RECORDED
    parent_key: Any = NOT_RECORDED
    provenance: Any = NOT_RECORDED
    seed: Any = NOT_RECORDED
    plant_id: Any = NOT_RECORDED
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        extra = d.pop("extra", {}) or {}
        out = {k: d[k] for k in REQUIRED_FIELDS}
        out["event"] = d["event"]
        for k, v in extra.items():
            if k not in out or out[k] == NOT_RECORDED:
                out[k] = v
        return out


class PlannerAuditLedger:
    """Side-channel append-only ledger. Never consulted by planner decisions."""

    def __init__(self, *, seed: Any = NOT_RECORDED, plant_id: Any = NOT_RECORDED) -> None:
        self.rows: list[LedgerRow] = []
        self.seed = seed if seed is not None else NOT_RECORDED
        self.plant_id = plant_id if plant_id is not None else NOT_RECORDED
        self.proposal_epoch = 0
        self._seq = 0

    def append(self, row: LedgerRow) -> None:
        if row.seed == NOT_RECORDED:
            row.seed = self.seed
        if row.plant_id == NOT_RECORDED:
            row.plant_id = self.plant_id
        self._seq += 1
        row.extra.setdefault("seq", self._seq)
        self.rows.append(row)

    def digest(self) -> str:
        payload = []
        for r in self.rows:
            d = r.as_dict()
            stable = {k: d[k] for k in sorted(d.keys()) if k not in ("wall_time", "timestamp")}
            payload.append(stable)
        blob = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def events(self) -> list[dict[str, Any]]:
        return [r.as_dict() for r in self.rows]

    def classify_budget_reach(self, candidate_key: str) -> str:
        """Distinguish NEVER_PROPOSED vs NOT_REACHED_BEFORE_BUDGET_EXHAUSTION.

        Returns NOT_RECORDED when evidence is insufficient.
        """
        proposed = False
        budget_skip = False
        any_propose = False
        budget_reasons = {
            "ATOM_INVENTION_SKIPPED_BY_PLANNING",
            "BUDGET_ALLOCATION_FAILURE",
            "leftover_below_floor",
            "BUDGET_EXHAUSTED",
            "INVENTORY_CAPACITY_FAILURE",
        }
        for r in self.rows:
            d = r.as_dict()
            if d.get("proposal_state") == PROPOSED or d.get("event") == "propose":
                any_propose = True
            reason = str(d.get("selection_reason", "") or "")
            if d.get("selection_state") == SKIPPED and (
                reason in budget_reasons
                or "budget" in reason.lower()
                or "leftover" in reason.lower()
                or "planning" in reason.lower()
            ):
                budget_skip = True
            k = d.get("candidate_key")
            if k == candidate_key:
                if d.get("proposal_state") == PROPOSED or d.get("event") == "propose":
                    proposed = True
                if d.get("selection_state") == SKIPPED and (
                    reason in budget_reasons or "budget" in reason.lower()
                ):
                    budget_skip = True
        if proposed and budget_skip:
            return NOT_REACHED_BEFORE_BUDGET_EXHAUSTION
        if not proposed and any_propose:
            return NEVER_PROPOSED
        if not proposed and budget_skip and not any_propose:
            return NEVER_PROPOSED
        return NOT_RECORDED


def get_ledger() -> PlannerAuditLedger | None:
    if not audit_enabled():
        return None
    return _tls().get("ledger")


def ensure_ledger(*, seed: Any = NOT_RECORDED, plant_id: Any = NOT_RECORDED) -> PlannerAuditLedger | None:
    if not audit_enabled():
        return None
    tls = _tls()
    led = tls.get("ledger")
    if led is None:
        led = PlannerAuditLedger(seed=seed, plant_id=plant_id)
        tls["ledger"] = led
    else:
        if seed != NOT_RECORDED and led.seed == NOT_RECORDED:
            led.seed = seed
        if plant_id != NOT_RECORDED and led.plant_id == NOT_RECORDED:
            led.plant_id = plant_id
    return led


def reset_ledger(*, seed: Any = NOT_RECORDED, plant_id: Any = NOT_RECORDED) -> PlannerAuditLedger | None:
    if not audit_enabled():
        _tls()["ledger"] = None
        return None
    led = PlannerAuditLedger(seed=seed, plant_id=plant_id)
    _tls()["ledger"] = led
    return led


def clear_ledger() -> None:
    _tls()["ledger"] = None


def _atom_fields(atom: Any) -> dict[str, Any]:
    if atom is None:
        return {}
    key: Any = NOT_RECORDED
    try:
        if callable(getattr(atom, "key", None)):
            key = atom.key()
        else:
            key = getattr(atom, "key", NOT_RECORDED)
    except Exception:
        key = NOT_RECORDED
    family = getattr(atom, "semantic_class", None) or NOT_RECORDED
    origin = getattr(atom, "origin", None) or NOT_RECORDED
    proposal_index = getattr(atom, "proposal_index", NOT_RECORDED)
    novelty = getattr(atom, "novelty", NOT_RECORDED)
    provenance = getattr(atom, "provenance", NOT_RECORDED)
    if isinstance(provenance, tuple):
        provenance = list(provenance)
    parent = getattr(atom, "parent", NOT_RECORDED)
    if isinstance(parent, tuple):
        parent = list(parent)
    return {
        "candidate_key": key,
        "body_key": key,
        "candidate_family": family,
        "candidate_origin": origin,
        "proposal_index": proposal_index,
        "novelty_state": novelty,
        "provenance": provenance,
        "parent_key": parent,
    }


def observe_propose(
    atoms: Iterable[Any],
    *,
    generation_method: str = "propose_atoms",
    proposal_epoch: Any = NOT_RECORDED,
) -> None:
    if not audit_enabled():
        return
    led = ensure_ledger()
    if led is None:
        return
    if proposal_epoch == NOT_RECORDED:
        led.proposal_epoch += 1
        proposal_epoch = led.proposal_epoch
    for atom in atoms:
        fields = _atom_fields(atom)
        led.append(
            LedgerRow(
                event="propose",
                proposal_state=PROPOSED,
                candidate_generation_method=generation_method,
                proposal_epoch=proposal_epoch,
                **fields,
            )
        )


def observe_reject(
    atom: Any = None,
    *,
    candidate_key: Any = NOT_RECORDED,
    rejection_reason: str = NOT_RECORDED,
    proposal_index: Any = NOT_RECORDED,
    **kwargs: Any,
) -> None:
    if not audit_enabled():
        return
    led = ensure_ledger()
    if led is None:
        return
    fields = _atom_fields(atom) if atom is not None else {}
    if candidate_key != NOT_RECORDED:
        fields["candidate_key"] = candidate_key
        fields.setdefault("body_key", candidate_key)
    if proposal_index != NOT_RECORDED:
        fields["proposal_index"] = proposal_index
    led.append(
        LedgerRow(
            event="reject",
            proposal_state=PROPOSED,
            rejection_state=REJECTED,
            rejection_reason=rejection_reason,
            extra=dict(kwargs),
            **fields,
        )
    )


def observe_score(
    atom: Any,
    *,
    score: Any,
    score_components: Any = NOT_RECORDED,
    **kwargs: Any,
) -> None:
    if not audit_enabled():
        return
    led = ensure_ledger()
    if led is None:
        return
    fields = _atom_fields(atom)
    led.append(
        LedgerRow(
            event="score",
            proposal_state=SCORED,
            score=score,
            score_components=score_components,
            extra=dict(kwargs),
            **fields,
        )
    )


def observe_rank(
    ranked: Iterable[Any],
    *,
    rejected_classes: Any = NOT_RECORDED,
    leftover: Any = NOT_RECORDED,
) -> None:
    if not audit_enabled():
        return
    led = ensure_ledger()
    if led is None:
        return
    comps: Any = NOT_RECORDED
    if rejected_classes != NOT_RECORDED or leftover != NOT_RECORDED:
        comps = {
            "rejected_classes": list(rejected_classes)
            if isinstance(rejected_classes, (set, list, tuple))
            else rejected_classes,
            "leftover": leftover,
        }
    for i, atom in enumerate(ranked):
        fields = _atom_fields(atom)
        led.append(
            LedgerRow(
                event="rank",
                proposal_state=RANKED,
                rank=i,
                score_components=comps,
                **fields,
            )
        )


def observe_select(
    atom: Any = None,
    *,
    selection_state: str = SELECTED,
    selection_reason: str = NOT_RECORDED,
    budget_before: Any = NOT_RECORDED,
    budget_after: Any = NOT_RECORDED,
    candidate_key: Any = NOT_RECORDED,
    **kwargs: Any,
) -> None:
    if not audit_enabled():
        return
    led = ensure_ledger()
    if led is None:
        return
    fields = _atom_fields(atom) if atom is not None else {}
    if candidate_key != NOT_RECORDED:
        fields["candidate_key"] = candidate_key
        fields.setdefault("body_key", candidate_key)
    led.append(
        LedgerRow(
            event="select" if selection_state == SELECTED else "skip",
            proposal_state=selection_state if selection_state in (SELECTED, SKIPPED) else PROPOSED,
            selection_state=selection_state,
            selection_reason=selection_reason,
            budget_before=budget_before,
            budget_after=budget_after,
            extra=dict(kwargs),
            **fields,
        )
    )


def observe_invent(
    atom: Any = None,
    *,
    body_key: Any = NOT_RECORDED,
    budget_before: Any = NOT_RECORDED,
    budget_after: Any = NOT_RECORDED,
    firewall_epoch: Any = NOT_RECORDED,
    **kwargs: Any,
) -> None:
    if not audit_enabled():
        return
    led = ensure_ledger()
    if led is None:
        return
    fields = _atom_fields(atom) if atom is not None else {}
    if body_key != NOT_RECORDED:
        fields["body_key"] = body_key
        fields.setdefault("candidate_key", body_key)
    led.append(
        LedgerRow(
            event="invent",
            proposal_state=INVENTED,
            selection_state=SELECTED,
            budget_before=budget_before,
            budget_after=budget_after,
            firewall_epoch=firewall_epoch,
            extra=dict(kwargs),
            **fields,
        )
    )


def observe_skip(
    *,
    selection_reason: str,
    budget_before: Any = NOT_RECORDED,
    budget_after: Any = NOT_RECORDED,
    candidate_key: Any = NOT_RECORDED,
    **kwargs: Any,
) -> None:
    observe_select(
        None,
        selection_state=SKIPPED,
        selection_reason=selection_reason,
        budget_before=budget_before,
        budget_after=budget_after,
        candidate_key=candidate_key,
        **kwargs,
    )


def observe_firewall(
    *,
    firewall_epoch: Any = NOT_RECORDED,
    reason: Any = NOT_RECORDED,
    **kwargs: Any,
) -> None:
    if not audit_enabled():
        return
    led = ensure_ledger()
    if led is None:
        return
    led.append(
        LedgerRow(
            event="firewall",
            firewall_epoch=firewall_epoch,
            selection_reason=reason,
            extra=dict(kwargs),
        )
    )


def observe_not_recorded(field_name: str, *, reason: str = "instrumentation_gap") -> None:
    if not audit_enabled():
        return
    led = ensure_ledger()
    if led is None:
        return
    led.append(
        LedgerRow(
            event="not_recorded",
            extra={"field": field_name, "reason": reason},
        )
    )


def twin_outcome_snapshot(
    *,
    proposal_keys: list[str],
    scores: list[Any] | None = None,
    ranks: list[Any] | None = None,
    selections: list[str] | None = None,
    inventions: list[str] | None = None,
    budget_series: list[Any] | None = None,
    final_state: Any = NOT_RECORDED,
) -> dict[str, Any]:
    return {
        "proposal_keys": list(proposal_keys),
        "scores": list(scores or []),
        "ranks": list(ranks or []),
        "selections": list(selections or []),
        "inventions": list(inventions or []),
        "budget_series": list(budget_series or []),
        "final_state": final_state,
    }


def snapshots_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


__all__ = [
    "MODE_ENV",
    "NEVER_PROPOSED",
    "NOT_REACHED_BEFORE_BUDGET_EXHAUSTION",
    "PROPOSED",
    "REJECTED",
    "SCORED",
    "RANKED",
    "SELECTED",
    "INVENTED",
    "SKIPPED",
    "NOT_RECORDED",
    "REQUIRED_FIELDS",
    "LedgerRow",
    "PlannerAuditLedger",
    "audit_enabled",
    "enable_audit",
    "disable_audit",
    "get_ledger",
    "ensure_ledger",
    "reset_ledger",
    "clear_ledger",
    "observe_propose",
    "observe_reject",
    "observe_score",
    "observe_rank",
    "observe_select",
    "observe_invent",
    "observe_skip",
    "observe_firewall",
    "observe_not_recorded",
    "twin_outcome_snapshot",
    "snapshots_equal",
]
