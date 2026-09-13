"""Investigator explorer — hybrid exploration + BehavioralInvestigator follow-ups.

When context signals an interesting security delta / open hypotheses, switches
into investigation-mode prompts. Does NOT embed ground-truth trigger strings.
"""
from __future__ import annotations

from typing import Any

from aivd.agents.generators import PromptGenerator, STRATEGY_TEMPLATES
from aivd.explorers.hybrid import HybridExplorer
from aivd.investigation.matrix import matrix_prompts_for_dimension, select_dimensions


class InvestigatorExplorer:
    """Wraps HybridExplorer; emits investigation follow-ups when signaled."""

    name = "investigator"

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.hybrid = HybridExplorer(seed=seed)
        self.gen = PromptGenerator(seed=seed + 7)
        self._mode = "explore"
        self._followups: list[tuple[str, str]] = []
        self._last_info: dict[str, Any] = {}
        self.rng_n = 0
        # optional continual flags (controller may set)
        self.continual = False
        self.include_memory = False

    def next_prompt(self, context: dict[str, Any]) -> tuple[str, str]:
        # Prefer queued investigation follow-ups
        if self._followups:
            return self._followups.pop(0)

        inv_mode = context.get("investigation_mode") or context.get("inv_mode")
        preferred = list(context.get("preferred_dimensions") or [])
        open_dims = list(context.get("open_dimensions") or preferred)
        signal = float(context.get("last_security_relevance") or context.get("inv_signal") or 0.0)
        residual = float(context.get("mem_residual_uncertainty") or 0.0)

        if inv_mode == "investigate" or signal >= 0.2 or (residual > 0.25 and open_dims):
            self._mode = "investigate"
            dims = select_dimensions(open_dims, max_dims=3, force=preferred[:2])
            if dims:
                d = dims[self.rng_n % len(dims)]
                self.rng_n += 1
                prompts = matrix_prompts_for_dimension(d)
                # Use generator strategies when dimension maps to known strategies
                strat_map = {
                    "encoding": "encoding_probe",
                    "delimiter": "delimiter_probe",
                    "rare_token": "sparse_token_hunt",
                    "indirect": "indirect_probe",
                    "role": "corpus_role",
                }
                if d in strat_map and strat_map[d] in STRATEGY_TEMPLATES:
                    return self.gen.from_strategy(strat_map[d])
                return f"investigate_{d}", prompts[self.rng_n % len(prompts)]

        self._mode = "explore"
        return self.hybrid.next_prompt(context)

    def observe(self, strategy: str, prompt: str, reward: float, info: dict[str, Any]) -> None:
        self._last_info = dict(info or {})
        finding = info.get("finding")
        sec = float(getattr(finding, "security_relevance", 0.0) or 0.0) if finding else 0.0
        inv = info.get("investigation") or {}
        # Queue one follow-up when signal interesting (non-GT)
        if sec >= 0.25 and len(self._followups) < 3:
            # Counterfactual-ish: mild ablation / paraphrase — no GT tokens
            self._followups.append(
                ("investigate_cf_ablate", prompt.replace("override", "over-ride") + "\n(confirm?)")
            )
            self._followups.append(
                ("investigate_cf_para", "In other words: " + prompt[:300])
            )
        # Pass through to hybrid/RL
        self.hybrid.observe(strategy, prompt, reward, info)
