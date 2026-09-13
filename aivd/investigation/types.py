"""Investigation-layer models (v3.3). Additive — does not replace core Finding/Experiment."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def new_inv_id(prefix: str = "inv_") -> str:
    return f"{prefix}{uuid4().hex[:12]}"


class StressLevel(int, Enum):
    L0 = 0
    L1 = 1
    L2 = 2
    L3 = 3
    L4 = 4
    L5 = 5
    L6 = 6
    L7 = 7
    L8 = 8
    L9 = 9


class HypothesisStatus(str, Enum):
    OPEN = "open"
    SUPPORTED = "supported"
    FALSIFIED = "falsified"
    UNRESOLVED = "unresolved"
    LOCALIZED = "localized"


class SensitivityClass(str, Enum):
    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    POSITIONAL = "positional"
    CONTEXTUAL = "contextual"
    INSENSITIVE = "insensitive"
    UNKNOWN = "unknown"


class DeltaDimension(str, Enum):
    SECURITY_SCORE = "security_score"
    RESPONSE_LENGTH = "response_length"
    SIGNAL_SET = "signal_set"
    EMBEDDING = "embedding"
    LATENCY = "latency"
    ERROR_STATE = "error_state"
    CLAIM_EFFECT = "claim_effect"
    REFUSAL_LANGUAGE = "refusal_language"


class BehavioralDelta(BaseModel):
    """Multi-dimension behavioral change between baseline and probe."""

    magnitude: float = 0.0
    dimensions: dict[str, float] = Field(default_factory=dict)
    changed_dimensions: list[str] = Field(default_factory=list)
    unchanged_dimensions: list[str] = Field(default_factory=list)
    security_delta: float = 0.0
    claim_without_effect: bool = False
    summary: str = ""
    meta: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_meaningful(self) -> bool:
        return self.magnitude >= 0.12 or abs(self.security_delta) >= 0.15


class InvestigationHypothesis(BaseModel):
    """Explicit hypothesis object spanning multiple probes."""

    id: str = Field(default_factory=lambda: new_inv_id("hyp_"))
    claim: str = ""
    region_id: str = ""
    dimension: str = ""
    status: HypothesisStatus = HypothesisStatus.OPEN
    prior: float = 0.5
    posterior: float = 0.5
    supporting_ids: list[str] = Field(default_factory=list)
    falsifying_ids: list[str] = Field(default_factory=list)
    minimal_trigger_estimate: str = ""
    changed_dimensions: list[str] = Field(default_factory=list)
    unchanged_dimensions: list[str] = Field(default_factory=list)
    sensitivity: SensitivityClass = SensitivityClass.UNKNOWN
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# Alias used in architecture note / API
Hypothesis = InvestigationHypothesis


class TriadExperiment(BaseModel):
    """Control / probe / counterfactual triad with dimension metadata."""

    id: str = Field(default_factory=lambda: new_inv_id("triad_"))
    control_prompt: str
    probe_prompt: str
    counterfactual_prompt: str
    changed_dimensions: list[str] = Field(default_factory=list)
    unchanged_dimensions: list[str] = Field(default_factory=list)
    hypothesis_id: str = ""
    stress_level: int = 0
    meta: dict[str, Any] = Field(default_factory=dict)


class BoundaryRecord(BaseModel):
    """High-gradient boundary between no-effect and effect."""

    id: str = Field(default_factory=lambda: new_inv_id("bnd_"))
    region_id: str = ""
    dimension: str = ""
    below_prompt: str = ""
    above_prompt: str = ""
    below_effect: float = 0.0
    above_effect: float = 0.0
    perturbation_size: float = 1.0
    boundary_score: float = 0.0
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)


class TriggerSensitivity(BaseModel):
    """Classification of what a trigger is sensitive to."""

    lexical: float = 0.0
    semantic: float = 0.0
    structural: float = 0.0
    positional: float = 0.0
    contextual: float = 0.0
    dominant: SensitivityClass = SensitivityClass.UNKNOWN
    notes: str = ""


class ProbEstimate(BaseModel):
    """P(trigger|condition) with simple CI — never treat one hit as deterministic."""

    p_hat: float = 0.0
    n: int = 0
    successes: int = 0
    ci_low: float = 0.0
    ci_high: float = 1.0
    deterministic_claim: bool = False  # always False unless n large and p≈1
    notes: str = ""


class InvestigationResult(BaseModel):
    """Summary of one BehavioralInvestigator.run."""

    hypotheses: list[InvestigationHypothesis] = Field(default_factory=list)
    boundaries: list[BoundaryRecord] = Field(default_factory=list)
    deltas: list[BehavioralDelta] = Field(default_factory=list)
    minimal_triggers: list[str] = Field(default_factory=list)
    negative_evidence: list[str] = Field(default_factory=list)
    experiments_used: int = 0
    budget: int = 0
    early_stopped: bool = False
    metrics: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "StressLevel",
    "HypothesisStatus",
    "SensitivityClass",
    "DeltaDimension",
    "BehavioralDelta",
    "InvestigationHypothesis",
    "Hypothesis",
    "TriadExperiment",
    "BoundaryRecord",
    "TriggerSensitivity",
    "ProbEstimate",
    "InvestigationResult",
    "new_inv_id",
]
