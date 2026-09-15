"""Design the next experiment to discriminate remaining hypotheses."""
from __future__ import annotations

from typing import Any

from aivd.epistemic.types import ExperimentProposal
from aivd.science.contrast import Contrast, contrast
from aivd.science.hypotheses import HypothesisBoard, HypState
from aivd.science.operators import BATTERY, apply_operator, apply_sequence


class ScienceDesigner:
    """Hypothesis → experiment. Residual tokens are not the search."""

    def __init__(self, *, seed_prompt: str, seed: int = 0, max_new: int = 8):
        self.seed_prompt = seed_prompt
        self.seed = int(seed)
        self.max_new = int(max_new)
        self.board = HypothesisBoard(seed=seed)
        self.tested: set[str] = set()
        self.seq = 0
        self.supported_ops: list[str] = []
        self.trap_ops: list[str] = []
        self.last_prompt = seed_prompt
        self.last_ops: list[str] = []
        self.history: list[dict[str, Any]] = []
        for op in BATTERY:
            self.board.add(
                f"op:{op}",
                f"security-relevant behavior is gated by operator {op}",
                [op],
                prior=0.35,
                why="generic structural edit; competing, not assumed",
            )

    def observe(self, prompt: str, obs: Any, *, baseline: Any | None, ops: list[str] | None = None) -> Contrast:
        c = contrast(obs, baseline)
        used_ops = list(ops or [])
        self.tested.add(prompt)
        self.last_prompt = prompt
        self.last_ops = used_ops
        self.history.append({"prompt": prompt, "ops": used_ops, "contrast": c.as_dict()})
        if not used_ops:
            return c
        for op in used_ops:
            hid = f"op:{op}"
            if hid not in self.board.nodes:
                self.board.add(hid, f"operator {op}", [op], prior=0.3)
            if c.secret:
                self.board.update(hid, support=1.0)
                if op not in self.supported_ops:
                    self.supported_ops.append(op)
            elif c.greedy_metric:
                self.board.update(hid, support=0.05, against=0.55)
                if op not in self.trap_ops:
                    self.trap_ops.append(op)
            elif c.security_shaped or (c.metric_delta >= 0.08 and c.error):
                self.board.update(hid, support=0.55)
                if op not in self.supported_ops:
                    self.supported_ops.append(op)
            elif c.metric_delta < 0.03 and not c.error_appeared and not c.text_changed:
                self.board.update(hid, support=0.0, against=0.45)
            else:
                self.board.update(hid, support=0.12)
        if len(used_ops) >= 2:
            hid = "cmp:" + "+".join(used_ops)
            self.board.add(
                hid,
                f"composition {' then '.join(used_ops)} is required",
                used_ops,
                prior=0.45,
                why="single operators did not suffice; testing conjunction",
            )
            if c.secret:
                self.board.update(hid, support=1.0)
            elif c.security_shaped:
                self.board.update(hid, support=0.4)
            else:
                self.board.update(hid, support=0.05, against=0.2)
        return c

    def _prop(
        self,
        prompt: str,
        ops: list[str],
        *,
        disc: float,
        eig: float,
        sec: float,
        unlock: bool,
        remaining: int,
        evidence: float,
        why: str,
    ) -> ExperimentProposal | None:
        if not prompt or prompt in self.tested:
            return None
        self.seq += 1
        hid = "+".join(ops) if ops else "contrast"
        return ExperimentProposal(
            proposal_id=f"sci_{self.seq}",
            branch_id="science",
            subsystem="science",
            hypothesis_id=hid,
            action=hid,
            prompt=prompt,
            expected_information_gain=eig,
            uncertainty_reduction=0.2 + 0.3 * disc,
            security_relevance=sec,
            hypothesis_discrimination_value=disc,
            verification_value=0.25 if unlock else 0.08,
            novelty_value=0.3,
            experiment_cost=1.0,
            estimated_remaining_steps=remaining,
            estimated_completion_probability=evidence,
            unlocks_hypothesis_class=unlock,
            provenance="science.designer",
            meta={"ops": list(ops), "why": why},
        )

    def propose(self, *, remaining_steps: int = 6, evidence_strength: float = 0.4) -> list[ExperimentProposal]:
        out: list[ExperimentProposal] = []

        def add(p: ExperimentProposal | None) -> None:
            if p is not None and len(out) < self.max_new:
                out.append(p)

        # 1. Continuations of supported operators (just-unlocked path).
        for op in self.supported_ops:
            for other in BATTERY:
                if other == op or other in self.trap_ops:
                    continue
                seq = [op, other]
                add(self._prop(
                    apply_sequence(self.seed_prompt, seq),
                    seq,
                    disc=0.88,
                    eig=0.28,
                    sec=0.55,
                    unlock=True,
                    remaining=1,
                    evidence=max(evidence_strength, 0.6),
                    why=f"supported {op}; compose with {other} to discriminate conjunction vs single",
                ))
                add(self._prop(
                    apply_operator(self.last_prompt, other),
                    self.last_ops + [other],
                    disc=0.9,
                    eig=0.3,
                    sec=0.55,
                    unlock=True,
                    remaining=1,
                    evidence=max(evidence_strength, 0.65),
                    why=f"apply {other} to the just-informative prompt (sequential compose)",
                ))
                if len(out) >= self.max_new:
                    return out

        # 2. Untested battery operators — competing hyps, not greedy-EIG ranked.
        for op in BATTERY:
            if f"op:{op}" in self.board.nodes and self.board.nodes[f"op:{op}"].tests > 0:
                continue
            trap = op in ("repeat_last", "duplicate")
            add(self._prop(
                apply_operator(self.seed_prompt, op),
                [op],
                disc=0.75,
                eig=0.18 if trap else 0.22,
                sec=0.22,
                unlock=False,
                remaining=max(2, remaining_steps),
                evidence=0.25 if trap else evidence_strength,
                why=f"untested operator {op}; discriminate against alternatives",
            ))

        # 3. Reverse-order falsifiers for two-op histories.
        if len(self.last_ops) >= 2:
            rev = list(reversed(self.last_ops[:2]))
            add(self._prop(
                apply_sequence(self.seed_prompt, rev),
                rev,
                disc=0.8,
                eig=0.22,
                sec=0.4,
                unlock=False,
                remaining=2,
                evidence=0.4,
                why="reverse order to falsify order-insensitive conjunction",
            ))

        # 4. Ablation: drop last op.
        if self.last_ops:
            rest = self.last_ops[:-1]
            prompt = apply_sequence(self.seed_prompt, rest) if rest else self.seed_prompt
            add(self._prop(
                prompt,
                rest or ["ablate"],
                disc=0.7,
                eig=0.15,
                sec=0.2,
                unlock=False,
                remaining=2,
                evidence=0.3,
                why="ablate last edit; if effect vanishes the last op was necessary",
            ))
        return out[: self.max_new]


__all__ = ["ScienceDesigner"]
