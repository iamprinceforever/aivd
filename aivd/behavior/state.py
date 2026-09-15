"""Strongly typed behavioral state for maps, world models, and RL policies."""
from __future__ import annotations

from typing import Any, Optional, Sequence

import numpy as np
from pydantic import BaseModel, Field


class BehavioralState(BaseModel):
    """Fixed-view behavioral state used by Controller / PPO / world model.

    Embedding ``z`` is the primary continuous representation. Other fields
    summarize map statistics so policies need not re-query the archive.

    v3.2 memory-derived fields (optional, default 0 / 1) extend the tensor view
    without breaking older consumers that only read the classic extras.
    """

    model_config = {"arbitrary_types_allowed": True}

    z: list[float] = Field(default_factory=list)
    region_id: int = 0
    novelty: float = 0.0
    redundancy: float = 0.0
    density: float = 0.0
    visit_count_region: int = 0
    coverage: float = 0.0
    uncertainty: float = 0.0
    delta_uncertainty: float = 0.0
    security_relevance: float = 0.0
    trajectory_length: int = 0
    unexplored_hint: list[float] = Field(default_factory=list)
    # --- continual / memory-derived (v3.2) ---
    global_novelty: float = 0.0
    mem_coverage: float = 0.0
    mem_residual_uncertainty: float = 1.0
    mem_known_findings_count: float = 0.0
    mem_vulnerability_density: float = 0.0
    mem_region_priority: float = 0.5
    mem_strategy_success: float = 0.0
    mem_strategy_fail: float = 0.0
    meta: dict[str, Any] = Field(default_factory=dict)

    def as_tensor_view(self, dim: int | None = None, *, include_memory: bool = False) -> np.ndarray:
        """Fixed-length float vector for MLP policies (CPU numpy).

        Layout: z[dim] + classic extras(10) + hint(8) [+ memory extras(8) if include_memory].
        Default include_memory=False → classic 64+10+8 = 82 (baselines preserved).
        Continual PPO passes include_memory=True → +8 memory extras (90-d).
        """
        z = list(self.z)
        if dim is not None:
            if len(z) < dim:
                z = z + [0.0] * (dim - len(z))
            else:
                z = z[:dim]
        extras = [
            float(self.region_id),
            float(self.novelty),
            float(self.redundancy),
            float(self.density),
            float(self.visit_count_region),
            float(self.coverage),
            float(self.uncertainty),
            float(self.delta_uncertainty),
            float(self.security_relevance),
            float(self.trajectory_length),
        ]
        hint = list(self.unexplored_hint[:8])
        if len(hint) < 8:
            hint = hint + [0.0] * (8 - len(hint))
        vec = z + extras + hint
        if include_memory:
            mem = [
                float(self.global_novelty),
                float(self.mem_coverage),
                float(self.mem_residual_uncertainty),
                float(self.mem_known_findings_count),
                float(self.mem_vulnerability_density),
                float(self.mem_region_priority),
                float(self.mem_strategy_success),
                float(self.mem_strategy_fail),
            ]
            vec = vec + mem
        return np.asarray(vec, dtype=np.float64)

    @classmethod
    def from_map_result(
        cls,
        beh: dict[str, Any],
        *,
        security_relevance: float = 0.0,
        density: float = 0.0,
        visit_count_region: int = 0,
        uncertainty: float = 0.0,
        trajectory_length: int = 0,
        unexplored_hint: Sequence[float] | None = None,
        meta: Optional[dict[str, Any]] = None,
        **memory_kwargs: Any,
    ) -> "BehavioralState":
        allowed = {
            "global_novelty",
            "mem_coverage",
            "mem_residual_uncertainty",
            "mem_known_findings_count",
            "mem_vulnerability_density",
            "mem_region_priority",
            "mem_strategy_success",
            "mem_strategy_fail",
        }
        mem = {k: v for k, v in memory_kwargs.items() if k in allowed}
        return cls(
            z=list(beh.get("embedding") or []),
            region_id=int(beh.get("region") or 0),
            novelty=float(beh.get("novelty") or 0.0),
            redundancy=float(beh.get("redundancy") or 0.0),
            density=float(density if density else beh.get("density") or 0.0),
            visit_count_region=int(visit_count_region),
            coverage=float(beh.get("coverage") or 0.0),
            uncertainty=float(uncertainty),
            delta_uncertainty=float(beh.get("delta_uncertainty") or 0.0),
            security_relevance=float(security_relevance),
            trajectory_length=int(trajectory_length),
            unexplored_hint=list(unexplored_hint or []),
            meta=dict(meta or {}),
            **mem,
        )

    @classmethod
    def from_observation(
        cls,
        observation: Any,
        *,
        novelty: float = 0.0,
        redundancy: float = 0.0,
        coverage: float = 0.0,
        region_id: int | None = None,
        security_relevance: float = 0.0,
        **kwargs: Any,
    ) -> "BehavioralState":
        emb = list(getattr(observation, "embedding", None) or [])
        feats = getattr(observation, "features", None) or {}
        rid = region_id if region_id is not None else int(feats.get("region") or 0)
        return cls(
            z=emb,
            region_id=rid,
            novelty=float(novelty),
            redundancy=float(redundancy),
            coverage=float(coverage),
            security_relevance=float(security_relevance),
            meta={"observation_id": getattr(observation, "id", None)},
            **kwargs,
        )
