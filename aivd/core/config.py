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
    # v3.9/3.10 open intervention invention (+ diversity; default off) — ABOVE causal, BEFORE residual handoff
    invention_mode: Literal[
        "off", "random", "heuristic", "full",
        "diversity", "bandit", "diversity_full", "diversity_heuristic",
        "adaptive", "adaptive_full", "adaptive_heuristic",
        "interaction", "interaction_full", "interaction_random",
        "joint", "joint_full", "joint_only", "joint_random",
        "interaction_joint", "full_3_13",
        "cross_signal", "cross_signal_full", "cross_signal_only", "cross_signal_random",
        "cross_joint", "full_3_14",
        "autonomy", "autonomy_full", "autonomy_only", "autonomy_random",
        "autonomy_cross", "full_3_15", "full_3_16",
        "reasoning", "reasoning_full", "reasoning_only",
        "experimental_reasoning",
        "openworld", "openworld_full", "openworld_only", "openworld_random",
        "full_3_17",
        "epistemic", "epistemic_full", "epistemic_only", "epistemic_shadow",
        "arbiter", "shadow", "full_3_18", "full_3_19", "full_3_20", "full_3_21", "full_3_22", "full_3_23", "full_3_24", "full_3_25", "full_3_26", "full_3_27", "full_3_28", "full_3_29", "full_3_30", "full_3_31", "full_3_32", "full_3_33", "full_3_34", "full_3_35", "full_3_36", "full_3_37", "full_3_38",
        "science", "science_full", "science_only",
    ] = "off"
    invention_max_candidates: int = 16
    invention_max_cheap_tests: int = 16
    invention_budget_fraction: float = 0.25
    # v3.10 diversity layer (default off for compat)
    invention_diversity_mode: Literal["off", "heuristic", "bandit", "full"] = "off"
    invention_exploration: Literal[
        "epsilon_greedy", "ucb", "thompson", "entropy", "novelty_bandit", "hierarchical",
    ] = "thompson"
    invention_saturation: bool = True
    invention_revival: bool = True
    invention_exploration_enabled: bool = True
    # v3.11 adaptive search ordering (default off)
    adaptive_ordering_mode: Literal["off", "on", "full", "heuristic"] = "off"
    invention_adaptive_ablation: str | None = None
    # v3.12 open interaction discovery (default off)
    interaction_mode: Literal[
        "off", "random", "static", "diversity", "adaptive",
        "interaction", "interaction_full", "interaction_random",
    ] = "off"
    interaction_max_pairs: int = 24
    interaction_max_screen: int = 8
    interaction_max_counterfactuals: int = 4
    interaction_max_triples: int = 2
    invention_interaction_ablation: str | None = None
    # v3.13 joint residual budget allocation (default off)
    joint_mode: Literal[
        "off", "joint", "joint_full", "joint_only", "joint_random",
        "interaction_joint", "full_3_13",
    ] = "off"
    joint_max_hypotheses: int = 6
    joint_max_combinations: int = 4
    joint_alloc_policy: Literal[
        "static", "equal", "greedy", "joint_aware", "adaptive", "random",
    ] = "joint_aware"
    joint_reserve_fraction: float = 0.25
    invention_joint_ablation: str | None = None
    # v3.14 cross-signal co-exploration (default off)
    cross_signal_mode: Literal[
        "off", "cross_signal", "cross_signal_full", "cross_signal_only",
        "cross_signal_random", "cross_joint", "full_3_14",
    ] = "off"
    cross_signal_max_hypotheses: int = 6
    cross_signal_max_combinations: int = 4
    cross_signal_reserve_fraction: float = 0.25
    invention_cross_signal_ablation: str | None = None
    # v3.15 autonomous signal-to-intervention discovery (default off)
    autonomy_mode: Literal[
        "off", "autonomy", "autonomy_full", "autonomy_only", "autonomy_random",
        "autonomy_cross", "full_3_15", "full_3_16",
        "reasoning", "reasoning_full", "reasoning_only",
        "experimental_reasoning",
        "openworld", "openworld_full", "openworld_only", "openworld_random",
        "full_3_17",
        "epistemic", "epistemic_full", "epistemic_only", "epistemic_shadow",
        "arbiter", "shadow", "full_3_18", "full_3_19", "full_3_20", "full_3_21", "full_3_22", "full_3_23", "full_3_24", "full_3_25", "full_3_26", "full_3_27", "full_3_28", "full_3_29", "full_3_30", "full_3_31", "full_3_32", "full_3_33", "full_3_34", "full_3_35", "full_3_36", "full_3_37", "full_3_38",
        "science", "science_full", "science_only",
    ] = "off"
    autonomy_max_steps: int = 32
    autonomy_max_candidates: int = 24
    autonomy_reserve_fraction: float = 0.25
    invention_autonomy_ablation: str | None = None
    # v3.16 discovery reasoning reset (default off)
    reasoning_mode: Literal[
        "off", "reasoning", "reasoning_full", "reasoning_only",
        "experimental_reasoning", "full_3_16",
    ] = "off"
    reasoning_max_steps: int = 32
    reasoning_max_candidates: int = 24
    reasoning_reserve_fraction: float = 0.15
    invention_reasoning_ablation: str | None = None
    # v3.17 open-world behavioral representation (default off)
    openworld_mode: Literal[
        "off", "openworld", "openworld_full", "openworld_only",
        "openworld_random", "full_3_17",
    ] = "off"
    openworld_max_steps: int = 32
    openworld_max_candidates: int = 24
    openworld_floor_fraction: float = 0.40
    invention_openworld_ablation: str | None = None
    # v3.18/3.19 global epistemic budget arbitration (default off)
    epistemic_mode: Literal[
        "off", "epistemic", "epistemic_full", "epistemic_only",
        "epistemic_shadow", "arbiter", "shadow", "full_3_18", "full_3_19",
        "full_3_20", "full_3_21", "full_3_22", "full_3_23", "full_3_24", "full_3_25", "full_3_26", "full_3_27", "full_3_28", "full_3_29", "full_3_30", "full_3_31", "full_3_32", "full_3_33", "full_3_34", "full_3_35", "full_3_36", "full_3_37", "full_3_38", "science", "science_full", "science_only",
    ] = "off"
    epistemic_max_steps: int = 32
    epistemic_max_candidates: int = 24
    invention_epistemic_ablation: str | None = None
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
