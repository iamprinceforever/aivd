"""Unified continual memory facade: checkpoint + replay + semantic."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from aivd.memory.checkpoint import CheckpointStore
from aivd.memory.regions import RegionRecord, region_priority
from aivd.memory.replay import ExperienceReplay
from aivd.memory.semantic import SemanticMemory


class ContinualMemory:
    def __init__(
        self,
        root: Path | str = "aivd_data/continual_memory",
        checkpoint_root: Path | str = "aivd_data/checkpoints",
    ):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.semantic = SemanticMemory(self.root / "semantic.db")
        self.replay = ExperienceReplay(self.root / "replay.db")
        self.checkpoints = CheckpointStore(checkpoint_root)

    def get_region(self, region_id: str, namespace: str = "target") -> RegionRecord:
        return self.semantic.get(region_id, namespace=namespace)

    def priority(self, region_id: str, namespace: str = "target") -> float:
        return region_priority(self.semantic.get(region_id, namespace=namespace))

    def memory_features(
        self,
        region_id: str,
        *,
        namespace: str = "target",
        strategy: str = "",
    ) -> dict[str, float]:
        """Fields for BehavioralState / PPO extras."""
        rec = self.semantic.get(region_id, namespace=namespace)
        return {
            "mem_coverage": float(rec.coverage),
            "mem_residual_uncertainty": float(rec.residual_uncertainty),
            "mem_known_findings_count": float(rec.unique_findings),
            "mem_vulnerability_density": float(rec.vulnerability_density),
            "mem_region_priority": float(region_priority(rec)),
            "mem_strategy_modifier": float(rec.strategy_priority_modifier(strategy)) if strategy else 1.0,
            "mem_confirmation_events": float(rec.confirmation_events),
            "mem_unexplored": float(rec.unexplored_coverage()),
        }

    def stats(self) -> dict[str, Any]:
        return {
            "semantic_run": self.semantic.stats("run"),
            "semantic_target": self.semantic.stats("target"),
            "semantic_global": self.semantic.stats("global"),
            "replay": self.replay.stats(),
            "checkpoints": self.checkpoints.list_checkpoints(),
        }

    def consolidate(self) -> dict[str, Any]:
        a = self.semantic.consolidate("run", "target")
        b = self.semantic.consolidate("target", "global")
        return {"run_to_target": a, "target_to_global": b}
