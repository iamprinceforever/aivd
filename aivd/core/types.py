"""Pydantic models for experiments, observations, findings, rewards."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class FindingStatus(str, Enum):
    TESTED = "tested"
    UNEXPLORED = "unexplored"
    ANOMALOUS = "anomalous"
    POTENTIALLY_VULNERABLE = "potentially_vulnerable"
    REPRODUCED = "reproduced"
    CONFIRMED = "confirmed"
    UNRESOLVED = "unresolved"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid4().hex[:12]}"


class Experiment(BaseModel):
    id: str = Field(default_factory=lambda: new_id("exp_"))
    explorer: str
    strategy: str = ""
    prompt: str
    target_id: str
    seed: int = 0
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)


class Observation(BaseModel):
    id: str = Field(default_factory=lambda: new_id("obs_"))
    experiment_id: str
    response_text: str
    latency_ms: float = 0.0
    error: Optional[str] = None
    features: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)


class Finding(BaseModel):
    id: str = Field(default_factory=lambda: new_id("find_"))
    experiment_id: str
    observation_id: str
    status: FindingStatus = FindingStatus.TESTED
    security_relevance: float = 0.0
    novelty: float = 0.0
    impact_score: float = 0.0
    confidence: float = 0.0
    repro_score: float = 0.0
    summary: str = ""
    ground_truth_hit: Optional[str] = None  # offline only; not shown to explorers
    evidence: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class RewardBreakdown(BaseModel):
    information_gain: float = 0.0
    delta_coverage: float = 0.0
    novelty: float = 0.0
    novelty_effective: float = 0.0
    delta_uncertainty: float = 0.0
    security_relevance: float = 0.0
    repro_score: float = 0.0
    confirmed_bonus: float = 0.0
    redundancy: float = 0.0
    low_info: float = 0.0
    invalid: float = 0.0
    repetition: float = 0.0
    normalized_cost: float = 0.0
    total: float = 0.0
    weights: dict[str, float] = Field(default_factory=dict)


class ProbeResult(BaseModel):
    experiment: Experiment
    observation: Observation
    finding: Finding
    reward: RewardBreakdown
