"""ScienceProposer — hypothesis-discrimination experiments for the arbiter."""
from __future__ import annotations

from typing import Any

from aivd.epistemic.types import ExperimentProposal
from aivd.science.designer import ScienceDesigner


class ScienceProposer:
    def __init__(self, *, seed: int = 0, max_new: int = 16, mode: str = "off"):
        self.seed = int(seed)
        self.max_new = int(max_new)
        self.mode = str(mode or "off")
        self.designer: ScienceDesigner | None = None
        self.baseline: Any = None

    def bind(self, seed_prompt: str, baseline: Any) -> None:
        self.designer = ScienceDesigner(
            seed_prompt=seed_prompt, seed=self.seed, max_new=self.max_new, mode=self.mode,
        )
        self.baseline = baseline
        self.designer.tested.add(seed_prompt)

    def observe(self, prompt: str, obs: Any, *, ops: list[str] | None = None) -> None:
        if self.designer is None:
            return
        self.designer.observe(prompt, obs, baseline=self.baseline, ops=ops)

    def invent(self) -> list[str]:
        if self.designer is None:
            return []
        return self.designer.invent()

    def propose(
        self,
        *,
        remaining_steps: int = 6,
        evidence_strength: float = 0.45,
    ) -> list[ExperimentProposal]:
        if self.designer is None:
            return []
        return self.designer.propose(
            remaining_steps=remaining_steps,
            evidence_strength=evidence_strength,
        )


__all__ = ["ScienceProposer"]
