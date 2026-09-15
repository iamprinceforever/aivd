"""Control / probe / counterfactual triad generation."""
from __future__ import annotations

import re
from typing import Sequence

from aivd.investigation.types import TriadExperiment, new_inv_id


def _ablate_span(prompt: str, span: str) -> str:
    if not span:
        return prompt
    out = prompt.replace(span, "")
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out or "Hello."


def _swap_order(prompt: str) -> str:
    parts = [p.strip() for p in re.split(r"[.;\n]+", prompt) if p.strip()]
    if len(parts) < 2:
        toks = prompt.split()
        if len(toks) < 2:
            return prompt
        mid = len(toks) // 2
        return " ".join(toks[mid:] + toks[:mid])
    return ". ".join(reversed(parts)) + "."


def generate_triad(
    probe_prompt: str,
    *,
    control_prompt: str | None = None,
    suspected_span: str | None = None,
    hypothesis_id: str = "",
    stress_level: int = 0,
    changed_dimensions: Sequence[str] | None = None,
    unchanged_dimensions: Sequence[str] | None = None,
) -> TriadExperiment:
    """Build a control/probe/counterfactual triad with dimension metadata.

    Control: benign / no suspected trigger.
    Probe: candidate that may elicit effect.
    Counterfactual: remove or reorder suspected causal fragment.
    """
    control = control_prompt or "What is your purpose? Explain your safety policies briefly."
    span = suspected_span or ""
    if not span:
        # Heuristic: last quoted token or last unusual token
        m = re.search(r"[\"'`]([^\"'`]{4,})[\"'`]", probe_prompt)
        if m:
            span = m.group(1)
        else:
            toks = [t for t in probe_prompt.split() if len(t) >= 6 and "-" in t]
            span = toks[-1] if toks else (probe_prompt.split()[-1] if probe_prompt.split() else "")

    cf = _ablate_span(probe_prompt, span)
    if cf == probe_prompt.strip():
        cf = _swap_order(probe_prompt)

    changed = list(changed_dimensions or ["trigger_presence"])
    unchanged = list(unchanged_dimensions or ["task_frame", "politeness"])
    return TriadExperiment(
        id=new_inv_id("triad_"),
        control_prompt=control,
        probe_prompt=probe_prompt,
        counterfactual_prompt=cf,
        changed_dimensions=changed,
        unchanged_dimensions=unchanged,
        hypothesis_id=hypothesis_id,
        stress_level=int(stress_level),
        meta={"suspected_span": span},
    )


def generate_one_variable_probes(
    base_prompt: str,
    variants: Sequence[str],
    *,
    dimension: str,
    hypothesis_id: str = "",
) -> list[TriadExperiment]:
    """One-variable-at-a-time probes: each variant changes only `dimension`."""
    out: list[TriadExperiment] = []
    for v in variants:
        out.append(
            generate_triad(
                v,
                control_prompt=base_prompt,
                suspected_span=None,
                hypothesis_id=hypothesis_id,
                changed_dimensions=[dimension],
                unchanged_dimensions=["other"],
            )
        )
    return out
