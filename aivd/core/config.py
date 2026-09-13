"""Global configuration."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class BudgetConfig(BaseModel):
    max_experiments: int = 100
    max_concurrency: int = 2
    request_timeout_s: float = 10.0
    wall_clock_s: float = 600.0
    max_prompt_chars: int = 4000


class RewardWeights(BaseModel):
    w_ig: float = 0.15
    w_cov: float = 0.15
    w_nov: float = 0.20
    w_unc: float = 0.10
    w_sec: float = 0.25
    w_repro: float = 0.10
    w_conf: float = 0.30
    w_red: float = 0.20
    w_low: float = 0.10
    w_inv: float = 0.50
    w_rep: float = 0.15
    w_cost: float = 0.0  # optional cost penalty; 0 keeps v1 behavior
    novelty_gate_eps: float = 0.05


class AIVDConfig(BaseModel):
    data_dir: Path = Field(default_factory=lambda: Path("aivd_data"))
    db_path: Path = Field(default_factory=lambda: Path("aivd_data/aivd.db"))
    audit_path: Path = Field(default_factory=lambda: Path("aivd_data/audit.jsonl"))
    reports_dir: Path = Field(default_factory=lambda: Path("reports"))
    allowlist: list[str] = Field(
        default_factory=lambda: [
            "mock://default",
            "local://stub",
            "openai-compat://stub",
            "openai-compat://api",
            "anthropic://api",
            "gemini://api",
            "local://model",
        ]
    )
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    reward: RewardWeights = Field(default_factory=RewardWeights)
    seed: int = 42
    n_behavioral_clusters: int = 8
    embedding_dim: int = 64
    embedding_backend: Literal["hashing", "torch"] = "hashing"
    estimated_reachable_regions: int = 16
    extra: dict[str, Any] = Field(default_factory=dict)

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)


DEFAULT_CONFIG = AIVDConfig()
