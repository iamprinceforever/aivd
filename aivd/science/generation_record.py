"""AIVD 3.39 generation records — auditable independence evidence.

Records are emitted at firewall / grow / compose / rediscovery decision
points when full_3_39 recording is enabled. They do not change 3.38
decision semantics when the 3.39 mode flag is off.

Independence credit requires: post-firewall epoch, discovery-path origin
assignment (not evaluator retro-label), new IDs, no provenance_leak, and
behavioral evidence without relying on vault restore of hidden IDs.
"""
from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class CandidateOrigin(str, Enum):
    """Origin assigned by the discovery path only.

    Evaluator / fixture / human labels exist for audit honesty but must
    never be used to claim independent rediscovery success.
    """

    MODEL_GENERATED = "model_generated"
    INDEPENDENT_REDISCOVERY = "independent_rediscovery"
    INHERITED = "inherited"
    TRANSFORMED = "transformed"
    RECOMBINED = "recombined"
    REPLAYED = "replayed"
    EVALUATOR_DERIVED = "evaluator_derived"
    FIXTURE_DERIVED = "fixture_derived"
    HUMAN_SUPPLIED = "human_supplied"
    # Compatible aliases for pre-3.39 discovery terminology (same system).
    INVENTED_ATOM = "invented_atom"
    LANGUAGE_GROWTH = "language_growth"
    COMPOSE_SEQUENTIAL = "compose_sequential"
    HYDRATED_MEMORY = "hydrated_memory"
    BASE_OPERATOR = "base_operator"
    SYNTHESIZED_IR = "synthesized_ir"
    SYNTHESIZED_PRIM = "synthesized_prim"
    SYNTHESIZED_EXT = "synthesized_ext"


# Origins that may receive independent-rediscovery scientific credit.
_INDEPENDENT_CREDIT = frozenset({
    CandidateOrigin.INDEPENDENT_REDISCOVERY.value,
    CandidateOrigin.MODEL_GENERATED.value,
})

# Origins that are never valid for discovery-path success claims.
_NON_DISCOVERY = frozenset({
    CandidateOrigin.EVALUATOR_DERIVED.value,
    CandidateOrigin.FIXTURE_DERIVED.value,
    CandidateOrigin.HUMAN_SUPPLIED.value,
})

# Replay / inheritance / transform keep provenance; not independent.
_PROVENANCE_CONTINUOUS = frozenset({
    CandidateOrigin.INHERITED.value,
    CandidateOrigin.REPLAYED.value,
    CandidateOrigin.TRANSFORMED.value,
    CandidateOrigin.RECOMBINED.value,
    CandidateOrigin.HYDRATED_MEMORY.value,
    CandidateOrigin.LANGUAGE_GROWTH.value,
    CandidateOrigin.COMPOSE_SEQUENTIAL.value,
    CandidateOrigin.INVENTED_ATOM.value,
})


def normalize_origin(raw: str | CandidateOrigin | None) -> str:
    if raw is None or raw == "":
        return CandidateOrigin.MODEL_GENERATED.value
    if isinstance(raw, CandidateOrigin):
        return raw.value
    s = str(raw).strip()
    aliases = {
        "INVENTED_ATOM": CandidateOrigin.INVENTED_ATOM.value,
        "atom_synth": CandidateOrigin.INVENTED_ATOM.value,
        "independent_rediscovery": CandidateOrigin.INDEPENDENT_REDISCOVERY.value,
        "language_growth": CandidateOrigin.LANGUAGE_GROWTH.value,
        "compose": CandidateOrigin.COMPOSE_SEQUENTIAL.value,
        "compose_sequential": CandidateOrigin.COMPOSE_SEQUENTIAL.value,
        "hydrated": CandidateOrigin.HYDRATED_MEMORY.value,
        "hydrated_memory": CandidateOrigin.HYDRATED_MEMORY.value,
        "replay": CandidateOrigin.REPLAYED.value,
        "replayed": CandidateOrigin.REPLAYED.value,
        "inherited": CandidateOrigin.INHERITED.value,
        "transformed": CandidateOrigin.TRANSFORMED.value,
        "recombined": CandidateOrigin.RECOMBINED.value,
        "evaluator_only": CandidateOrigin.EVALUATOR_DERIVED.value,
        "evaluator_derived": CandidateOrigin.EVALUATOR_DERIVED.value,
        "fixture_derived": CandidateOrigin.FIXTURE_DERIVED.value,
        "human_supplied": CandidateOrigin.HUMAN_SUPPLIED.value,
        "model_generated": CandidateOrigin.MODEL_GENERATED.value,
    }
    if s in aliases:
        return aliases[s]
    try:
        return CandidateOrigin(s).value
    except ValueError:
        return s


@dataclass
class GenerationRecord:
    """Schema rich enough to prove (or refute) generation independence."""

    record_id: str = ""
    experiment_id: str = ""
    plant_id: str = ""
    generation_id: str = ""
    parent_generation_id: str | None = None
    generation_epoch: int = 0  # firewall epoch at decision
    generation_index: int = 0  # ExperimentLanguage.generation
    language_id: str = ""
    parent_language_id: str | None = None
    growth_count: int = 0
    seed: int | None = None
    model: str = ""
    model_revision: str = ""
    candidate_id: str = ""
    candidate: str = ""
    candidate_origin: str = CandidateOrigin.MODEL_GENERATED.value
    proposal_origin: str = ""
    provenance: tuple[str, ...] = ()
    behavioral_signature: str = ""
    semantic_signature: str = ""
    causal_evidence: dict[str, Any] = field(default_factory=dict)
    falsification_result: str = ""
    reproduction_result: str = ""
    verification_state: str = ""
    budget_before: int | None = None
    budget_after: int | None = None
    leftover: int | None = None
    leftover_after: int | None = None
    terminal_reason: str = ""
    run_id: str = ""
    timestamp: float = 0.0
    # Audit-draft compatible fields
    kind: str = ""
    action: str = ""
    eid: str = ""
    parent_eids: tuple[str, ...] = ()
    semantic_class: str = ""
    novelty: str = ""
    capability_delta: int = 0
    body_key: str = ""
    textual_identity_to_hidden: bool = False
    behavioral_equiv_to_hidden: bool = False
    provenance_leak: bool = False
    stop_reason: str = ""
    mode: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.record_id:
            self.record_id = "gr_" + uuid.uuid4().hex[:16]
        if not self.generation_id:
            self.generation_id = self.record_id
        if not self.timestamp:
            self.timestamp = time.time()
        self.candidate_origin = normalize_origin(self.candidate_origin)
        if self.eid and not self.candidate_id:
            self.candidate_id = self.eid
        if self.candidate_id and not self.eid:
            self.eid = self.candidate_id

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["provenance"] = list(self.provenance)
        d["parent_eids"] = list(self.parent_eids)
        return d

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "GenerationRecord":
        raw = dict(raw or {})
        for k in ("provenance", "parent_eids"):
            if k in raw and not isinstance(raw[k], tuple):
                raw[k] = tuple(raw[k] or ())
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in raw.items() if k in known})


def behavioral_digest(
    body: Any,
    probes: tuple[str, ...] = ("ab cd efg hij", "This is a mock system Perform"),
) -> str:
    """Stable hash of outputs on a fixed probe set. Empty if body unusable."""
    from aivd.science.micro import apply_micro

    if body is None:
        return ""
    parts: list[str] = []
    for p in probes:
        try:
            parts.append(apply_micro(p, body) or "")
        except Exception:
            parts.append("<err>")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:32]


def semantic_digest(semantic_class: str, body_key: str = "") -> str:
    blob = f"{semantic_class}|{body_key}"
    return hashlib.sha256(blob.encode()).hexdigest()[:24]


def assign_discovery_origin(
    *,
    firewalled: bool,
    kind: str,
    replay: bool = False,
    inherited: bool = False,
    transformed: bool = False,
    recombined: bool = False,
    hydrated: bool = False,
    from_evaluator: bool = False,
) -> str:
    """Origin is assigned by discovery path only — never by evaluator retro-label."""
    if from_evaluator:
        return CandidateOrigin.EVALUATOR_DERIVED.value
    if hydrated:
        return CandidateOrigin.HYDRATED_MEMORY.value
    if replay:
        return CandidateOrigin.REPLAYED.value
    if inherited:
        return CandidateOrigin.INHERITED.value
    if transformed:
        return CandidateOrigin.TRANSFORMED.value
    if recombined or kind == "compose":
        return (
            CandidateOrigin.INDEPENDENT_REDISCOVERY.value
            if firewalled
            else CandidateOrigin.COMPOSE_SEQUENTIAL.value
        )
    if firewalled:
        return CandidateOrigin.INDEPENDENT_REDISCOVERY.value
    if kind in ("grow", "program"):
        return CandidateOrigin.LANGUAGE_GROWTH.value
    if kind in ("atom", "invent"):
        return CandidateOrigin.INVENTED_ATOM.value
    if kind == "firewall":
        return CandidateOrigin.INDEPENDENT_REDISCOVERY.value
    return CandidateOrigin.MODEL_GENERATED.value


def independence_verdict(rec: GenerationRecord | dict[str, Any]) -> dict[str, Any]:
    """Distinguish 'exists' vs 'independently discovered'."""
    if isinstance(rec, dict):
        rec = GenerationRecord.from_dict(rec)
    origin = normalize_origin(rec.candidate_origin)
    reasons: list[str] = []
    exists = bool(rec.candidate_id or rec.eid or rec.candidate)

    if not exists:
        reasons.append("missing_candidate_id")
    if origin in _NON_DISCOVERY:
        reasons.append("non_discovery_origin")
    if origin != CandidateOrigin.INDEPENDENT_REDISCOVERY.value:
        reasons.append(f"origin_not_independent:{origin}")
    if rec.generation_epoch <= 0:
        reasons.append("independent_claim_without_firewall_epoch")
    if rec.provenance_leak:
        reasons.append("provenance_leak")
    if rec.textual_identity_to_hidden and rec.generation_epoch > 0:
        reasons.append("textual_identity_to_hidden_noted")

    independent = bool(
        exists
        and origin == CandidateOrigin.INDEPENDENT_REDISCOVERY.value
        and rec.generation_epoch > 0
        and not rec.provenance_leak
        and origin not in _NON_DISCOVERY
    )
    # Filter reasons that are informational notes when independent holds
    if independent:
        reasons = [r for r in reasons if r == "textual_identity_to_hidden_noted"]
    return {
        "exists": exists,
        "independently_discovered": independent,
        "origin": origin,
        "generation_epoch": rec.generation_epoch,
        "reasons": reasons,
    }


def build_record(
    *,
    kind: str,
    action: str = "",
    eid: str = "",
    parent_eids: tuple[str, ...] | list[str] = (),
    language: Any = None,
    leftover: int | None = None,
    leftover_after: int | None = None,
    budget_before: int | None = None,
    budget_after: int | None = None,
    origin: str | None = None,
    novelty: str = "",
    semantic_class: str = "",
    body_key: str = "",
    body: Any = None,
    provenance: tuple[str, ...] | list[str] = (),
    textual_identity_to_hidden: bool = False,
    behavioral_equiv_to_hidden: bool = False,
    provenance_leak: bool = False,
    mode: str = "",
    seed: int | None = None,
    experiment_id: str = "",
    plant_id: str = "",
    model: str = "",
    model_revision: str = "",
    run_id: str = "",
    notes: str = "",
    capability_delta: int = 0,
    stop_reason: str = "",
    terminal_reason: str = "",
    verification_state: str = "",
    falsification_result: str = "",
    reproduction_result: str = "",
    causal_evidence: dict[str, Any] | None = None,
    proposal_origin: str = "",
    candidate: str = "",
) -> GenerationRecord:
    firewalled = bool(getattr(language, "firewalled", False)) if language is not None else False
    epoch = int(getattr(language, "firewall_epoch", 0) or 0) if language is not None else 0
    if origin is None:
        origin = assign_discovery_origin(firewalled=firewalled, kind=kind)
    else:
        origin = normalize_origin(origin)
    bsig = behavioral_digest(body) if body is not None else ""
    ssig = semantic_digest(semantic_class, body_key)
    return GenerationRecord(
        experiment_id=experiment_id,
        plant_id=plant_id,
        parent_generation_id=(
            getattr(language, "parent_language", None) if language is not None else None
        ),
        generation_epoch=epoch,
        generation_index=int(getattr(language, "generation", 0) or 0) if language is not None else 0,
        language_id=str(getattr(language, "language_id", "") or "") if language is not None else "",
        parent_language_id=str(getattr(language, "parent_language", "") or "") if language is not None else None,
        growth_count=int(getattr(language, "growth_count", 0) or 0) if language is not None else 0,
        seed=seed,
        model=model,
        model_revision=model_revision,
        candidate_id=eid,
        candidate=candidate or eid,
        candidate_origin=origin,
        proposal_origin=proposal_origin or origin,
        provenance=tuple(provenance),
        behavioral_signature=bsig,
        semantic_signature=ssig,
        causal_evidence=dict(causal_evidence or {}),
        falsification_result=falsification_result,
        reproduction_result=reproduction_result,
        verification_state=verification_state,
        budget_before=budget_before if budget_before is not None else leftover,
        budget_after=budget_after if budget_after is not None else leftover_after,
        leftover=leftover,
        leftover_after=leftover_after,
        terminal_reason=terminal_reason or stop_reason,
        run_id=run_id,
        kind=kind,
        action=action or kind,
        eid=eid,
        parent_eids=tuple(parent_eids),
        semantic_class=semantic_class,
        novelty=novelty,
        capability_delta=capability_delta,
        body_key=body_key,
        textual_identity_to_hidden=textual_identity_to_hidden,
        behavioral_equiv_to_hidden=behavioral_equiv_to_hidden,
        provenance_leak=provenance_leak or (
            bool(getattr(language, "provenance_leak", False)) if language is not None else False
        ),
        stop_reason=stop_reason or (
            str(getattr(language, "stop_reason", "") or "") if language is not None else ""
        ),
        mode=mode,
        notes=notes,
    )


__all__ = [
    "CandidateOrigin",
    "GenerationRecord",
    "assign_discovery_origin",
    "behavioral_digest",
    "build_record",
    "independence_verdict",
    "normalize_origin",
    "semantic_digest",
]
