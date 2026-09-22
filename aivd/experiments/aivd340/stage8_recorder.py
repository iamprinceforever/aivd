"""Stage-8 mechanism recorder — A–I fates observed, never inferred."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Stage8Recorder:
    condition_id: str
    family: str
    plant_id: str
    seed: int
    events: list[dict[str, Any]] = field(default_factory=list)
    equiv_decisions: list[dict[str, Any]] = field(default_factory=list)
    repair_calls_total: int = 0
    # body_key → stage annotations
    body_state: dict[str, dict[str, Any]] = field(default_factory=dict)
    selected_keys: set[str] = field(default_factory=set)
    pool_survived_keys: set[str] = field(default_factory=set)
    pool_removed_keys: set[str] = field(default_factory=set)
    pool_entered_keys: set[str] = field(default_factory=set)
    invent_keys: set[str] = field(default_factory=set)
    compose_fail_keys: set[str] = field(default_factory=set)
    verified_keys: set[str] = field(default_factory=set)
    rediscovered_keys: set[str] = field(default_factory=set)
    recursive_keys: set[str] = field(default_factory=set)
    recursive_edges: list[dict[str, str]] = field(default_factory=list)
    unobserved_reasons: dict[str, str] = field(default_factory=dict)

    def emit(self, **kwargs: Any) -> None:
        self.events.append(dict(kwargs))

    def repair_ledger_add(self, n: int) -> None:
        self.repair_calls_total += int(n or 0)

    def equiv_decision(
        self,
        *,
        family: str,
        candidate_key: str,
        label: str,
        action: str,
        apply_micro_calls: int,
        ambiguity_state: str | None,
        compared_keys: list[str],
        comparisons: list[dict[str, Any]],
    ) -> None:
        row = {
            "event": "equiv_decision",
            "family": family,
            "candidate_key": candidate_key,
            "label": label,
            "action": action,
            "apply_micro_calls": apply_micro_calls,
            "ambiguity_state": ambiguity_state,
            "compared_keys": list(compared_keys),
            "comparisons": comparisons,
        }
        self.equiv_decisions.append(row)
        self.events.append(row)
        self.pool_entered_keys.add(candidate_key)
        st = self.body_state.setdefault(candidate_key, {})
        st["reached_equiv"] = True
        st["equiv_label"] = label
        st["equiv_action"] = action
        if action == "reject" and label == "duplicate":
            self.pool_removed_keys.add(candidate_key)
            st["fate_hint"] = "D"
        elif action == "keep":
            self.pool_survived_keys.add(candidate_key)
            st["fate_hint"] = "survived_equiv"

    def note_selected(self, body_key: str | None) -> None:
        if not body_key:
            return
        self.selected_keys.add(body_key)
        self.body_state.setdefault(body_key, {})["selected"] = True
        self.emit(event="select", body_key=body_key)

    def note_invent(self, body_key: str) -> None:
        self.invent_keys.add(body_key)
        self.body_state.setdefault(body_key, {})["invented"] = True

    def note_compose_fail(self, body_key: str) -> None:
        self.compose_fail_keys.add(body_key)
        self.body_state.setdefault(body_key, {})["compose_failed"] = True

    def ingest_generation_records(self, records: list[dict[str, Any]]) -> None:
        parents_seen: set[str] = set()
        for r in records or []:
            bk = r.get("body_key") or ""
            if not bk:
                continue
            origin = r.get("candidate_origin") or r.get("origin") or ""
            if origin == "independent_rediscovery":
                self.rediscovered_keys.add(bk)
            parents = r.get("parent") or r.get("parents") or ()
            if isinstance(parents, str):
                parents = (parents,)
            for p in parents or ():
                if p:
                    parents_seen.add(str(p))
                    self.recursive_edges.append({"parent": str(p), "child": bk})
                    self.recursive_keys.add(str(p))
            st = self.body_state.setdefault(bk, {})
            st["in_generation_records"] = True
            st["origin"] = origin

    def ingest_terminal(self, *, verified: bool, secret_body_key: str | None = None) -> None:
        if verified and secret_body_key:
            self.verified_keys.add(secret_body_key)
            self.body_state.setdefault(secret_body_key, {})["verified"] = True

    def assign_primary_fates(self) -> dict[str, str]:
        """Mutually exclusive primary fate per tracked body. Missing → UNOBSERVED.

        Priority follows pipeline progress (G/I before E/D). Independent rediscovery
        (H) is assigned only when the body was not already fate-progressed through
        live pool/select/verify instrumentation — otherwise record H as secondary
        via rediscovered_keys without collapsing D/E evidence.
        """
        fates: dict[str, str] = {}
        tracked = set(self.body_state) | self.pool_entered_keys | self.pool_survived_keys
        tracked |= self.pool_removed_keys | self.selected_keys | self.verified_keys
        tracked |= self.rediscovered_keys | self.recursive_keys | self.invent_keys

        for bk in tracked:
            st = self.body_state.get(bk, {})
            # Furthest live progress first
            if bk in self.verified_keys:
                if bk in self.recursive_keys:
                    fates[bk] = "I"
                else:
                    fates[bk] = "G"
                continue
            if bk in self.pool_removed_keys:
                if st.get("equiv_label") == "duplicate":
                    fates[bk] = "D"
                else:
                    fates[bk] = "UNOBSERVED"
                    self.unobserved_reasons[bk] = "removed_without_duplicate_label"
                continue
            if bk in self.selected_keys:
                fates[bk] = "F" if st.get("verify_attempted") or st.get("verify_failed") else "E"
                continue
            if bk in self.pool_survived_keys:
                fates[bk] = "E"
                continue
            if st.get("reached_equiv"):
                fates[bk] = "E" if st.get("equiv_action") == "keep" else "D"
                continue
            if st.get("compose_failed"):
                fates[bk] = "B"
                continue
            if st.get("invented") and not st.get("reached_equiv"):
                fates[bk] = "C"
                continue
            # H only when rediscovery is the primary observed path (no pool fate)
            if bk in self.rediscovered_keys:
                fates[bk] = "H"
                continue
            if bk in self.recursive_keys:
                fates[bk] = "I"
                continue
            fates[bk] = "UNOBSERVED"
            self.unobserved_reasons[bk] = "insufficient_instrumentation"
        return fates


    # --- AIVD 3.41 Stage-8 invent recorder gap completion (observation only) ---
    invent_attempt_rows: list[dict[str, Any]] = field(default_factory=list)
    invent_reject_rows: list[dict[str, Any]] = field(default_factory=list)
    score_rank_select_rows: list[dict[str, Any]] = field(default_factory=list)

    def note_invent_attempt(self, row: dict[str, Any]) -> None:
        """Record an invent-attempt / propose observation (Stage-9 gap close)."""
        payload = dict(row)
        payload.setdefault("event", "invent_attempt")
        self.invent_attempt_rows.append(payload)
        self.emit(**payload)

    def note_invent_reject(self, row: dict[str, Any]) -> None:
        """Record invent-path reject (validation/novelty/duplicate)."""
        payload = dict(row)
        payload["event"] = "invent_reject"
        self.invent_reject_rows.append(payload)
        self.emit(**payload)

    def note_score_rank_select(self, row: dict[str, Any]) -> None:
        """Record score/rank/select/skip on invent orchestration path."""
        payload = dict(row)
        payload.setdefault("event", "score_rank_select")
        self.score_rank_select_rows.append(payload)
        self.emit(**payload)

    def ingest_planner_audit_ledger(self, ledger_events: list[dict[str, Any]] | None) -> None:
        """Project AIVD41 planner-audit ledger rows into Stage-8 invent gap ledgers."""
        for ev in ledger_events or []:
            et = ev.get("event")
            if et == "propose":
                self.note_invent_attempt(ev)
            elif et == "reject":
                self.note_invent_reject(ev)
            elif et in ("score", "rank", "select", "skip", "invent"):
                self.note_score_rank_select(ev)

    def invent_gap_summary(self) -> dict[str, Any]:
        return {
            "n_invent_attempts": len(self.invent_attempt_rows),
            "n_invent_rejects": len(self.invent_reject_rows),
            "n_score_rank_select": len(self.score_rank_select_rows),
            "invent_attempt_rows": list(self.invent_attempt_rows),
            "invent_reject_rows": list(self.invent_reject_rows),
            "score_rank_select_rows": list(self.score_rank_select_rows),
        }

    def summary(self) -> dict[str, Any]:
        fates = self.assign_primary_fates()
        from collections import Counter

        counts = Counter(fates.values())
        n_pool = len(self.pool_entered_keys)
        n_d = sum(1 for bk, f in fates.items() if f == "D" and bk in self.pool_entered_keys)
        n_surv = len(self.pool_survived_keys)
        return {
            "condition_id": self.condition_id,
            "family": self.family,
            "plant_id": self.plant_id,
            "seed": self.seed,
            "n_equiv_decisions": len(self.equiv_decisions),
            "n_pool_entered": n_pool,
            "n_pool_removed_D": len(self.pool_removed_keys),
            "n_pool_survived": n_surv,
            "n_selected": len(self.selected_keys),
            "n_verified_keys": len(self.verified_keys),
            "n_rediscovered": len(self.rediscovered_keys),
            "n_recursive": len(self.recursive_keys),
            "D_rate": (n_d / max(1, n_pool)),
            "surv_rate": (n_surv / max(1, n_pool)),
            "fate_counts": dict(counts),
            "fates": fates,
            "unobserved_reasons": dict(self.unobserved_reasons),
            "repair_calls_total": self.repair_calls_total,
            "recursive_edges": list(self.recursive_edges),
            "equiv_decisions": self.equiv_decisions,
            "invent_gap": self.invent_gap_summary(),
        }
