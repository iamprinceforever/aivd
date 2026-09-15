"""Memory of tested interaction hypotheses and outcomes."""
from __future__ import annotations

from typing import Any

from aivd.interaction.representation import InteractionCandidate


class InteractionMemory:
    def __init__(self) -> None:
        self.tested: list[dict[str, Any]] = []
        self.security_hits: list[dict[str, Any]] = []
        self.additive_rejects: list[dict[str, Any]] = []
        self.by_key: dict[str, dict[str, Any]] = {}

    def record(self, cand: InteractionCandidate, result: dict[str, Any]) -> None:
        key = "|".join(sorted(cand.component_ids or []))
        entry = {
            "id": cand.id,
            "key": key,
            "strategy": cand.strategy,
            "synergy_type": cand.synergy_type,
            "is_security_interaction": cand.is_security_interaction,
            "interaction_residual": cand.interaction_residual,
            "observed_combined": cand.observed_combined,
            "observed_individual": list(cand.observed_individual),
            "result": {k: v for k, v in result.items() if k != "obs"},
        }
        self.tested.append(entry)
        self.by_key[key] = entry
        if cand.is_security_interaction:
            self.security_hits.append(entry)
        if cand.synergy_type == "additive":
            self.additive_rejects.append(entry)

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_tested": len(self.tested),
            "n_security_hits": len(self.security_hits),
            "n_additive_rejects": len(self.additive_rejects),
            "tested": list(self.tested),
        }
