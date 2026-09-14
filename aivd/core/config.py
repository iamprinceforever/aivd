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
    w_impact: float = 0.0  # optional; RewardCalculator also applies small extra
    w_dup: float = 0.0  # duplicate behavior (falls back to redundancy)
    novelty_gate_eps: float = 0.05
    # v3.2 continual: prefer new unique vulns / trigger families over reconfirmations
    w_unique_vuln: float = 0.45
    w_new_trigger_family: float = 0.25
    w_same_vuln_trigger_redundancy: float = 0.35
    # v3.3 investigation terms (default 0 → old totals unchanged)
    w_inv_delta: float = 0.0
    w_inv_localize: float = 0.0
    w_inv_boundary: float = 0.0
    w_inv_counterfactual: float = 0.0
    w_inv_negative: float = 0.0
    w_inv_repetition: float = 0.0
    # v3.6 causal extras (default 0 → no farming)
    w_causal_disc: float = 0.0
    w_causal_dim: float = 0.0
    w_causal_negative: float = 0.0
    w_causal_interaction: float = 0.0


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
            "mock://profile-a",
            "mock://profile-b",
            "mock://profile-c",
            "mock://profile-d",
            "mock://profile-e",
            "mock://profile-f",
            "mock://planted-offline",
            "mock://investigation-bench",
            "mock://no-fish-control",
        ]
    )
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    reward: RewardWeights = Field(default_factory=RewardWeights)
    seed: int = 42
    n_behavioral_clusters: int = 8
    embedding_dim: int = 64
    embedding_backend: Literal["hashing", "torch", "learned"] = "hashing"
    estimated_reachable_regions: int = 16
    world_model: bool = False
    world_model_ensemble: int = 3
    use_counterfactual: bool = False
    use_critic: bool = False
    use_investigation: bool = False  # v3.3 ABI hook (True enables single_shot unless investigation_mode set)
    # v3.4: off | single_shot | multi_step (preferred). When set, overrides use_investigation.
    investigation_mode: Literal["off", "single_shot", "multi_step"] | None = None
    investigation_max_episode_probes: int = 16
    investigation_budget_fraction: float = 0.25
    investigation_enter_threshold: float = 0.35
    investigation_policy: Literal["heuristic", "learned", "random"] = "heuristic"
    # v3.5 Active Behavioral Discovery (default off for compat)
    discovery_mode: Literal["off", "random", "heuristic", "learned"] = "off"
    discovery_max_amplify_steps: int = 6
    discovery_budget_fraction: float = 0.20
    discovery_handoff_threshold: float = 0.40
    # v3.6 unknown-dimension / active causal discovery (default off)
    causal_mode: Literal["off", "heuristic", "learned", "full"] = "off"
    causal_discovery_mode: Literal["off", "heuristic", "learned", "full"] | None = None  # alias
    causal_budget_fraction: float = 0.25
    causal_max_episode_probes: int = 12
    # v3.7 open-ended unknown / residual-channel discovery (default off)
    unknowns_mode: Literal["off", "on", "heuristic", "learned", "full"] = "off"
    aivd37_mode: Literal["off", "on", "heuristic", "learned", "full"] | None = None  # alias
    unknowns_budget_fraction: float = 0.20
    unknowns_max_episode_probes: int = 24
    # When True and target is non-mock, use RealModelSecurityAnalyzer
    use_real_model_analyzer: bool = False
    # v3.2 continual learning
    learning_mode: Literal["stateless", "continual"] = "stateless"
    memory_root: Path = Field(default_factory=lambda: Path("aivd_data/continual_memory"))
    checkpoint_root: Path = Field(default_factory=lambda: Path("aivd_data/checkpoints"))
    checkpoint_name: str = "ppo_continual"
    memory_namespace: str = "target"
    encoder_lambdas: dict[str, float] = Field(
        default_factory=lambda: {
            "contrastive": 1.0,
            "temporal": 0.25,
            "reconstruction": 0.1,
            "security": 0.5,
        }
    )
    extra: dict[str, Any] = Field(default_factory=dict)

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)


DEFAULT_CONFIG = AIVDConfig()
