"""Design the next experiment to discriminate remaining hypotheses.

3.21: keep a LIVE informative state. When a continuation collapses,
do not chain the dead prompt. Invent a new method from the live state
and keep spending remaining budget.
"""
from __future__ import annotations

from typing import Any

from aivd.epistemic.types import ExperimentProposal
from aivd.science.contrast import Contrast, contrast
from aivd.science.hypotheses import HypothesisBoard
from aivd.science.methods import MethodInventor
from aivd.science.operators import BATTERY, apply_operator, apply_sequence


class ScienceDesigner:
    """Hypothesis → experiment. Residual tokens are not the search."""

    def __init__(self, *, seed_prompt: str, seed: int = 0, max_new: int = 16):
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
        self.content_tokens: list[str] = []
        self.recent_tokens: list[str] = []
        self.live_prompt = seed_prompt
        self.live_ops: list[str] = []
        self.live_metric = 0.0
        self.live_error = ""
        self.collapsed = False
        self.tried_on_live: set[str] = set()
        self.inventor = MethodInventor()
        self.methods_log: list[dict[str, str]] = []
        for op in BATTERY:
            self.board.add(
                f"op:{op}",
                f"security-relevant behavior is gated by operator {op}",
                [op],
                prior=0.35,
                why="generic structural edit; competing, not assumed",
            )

    @property
    def invented(self) -> list[str]:
        return list(self.inventor.invented)

    def _apply(self, prompt: str, name: str) -> str:
        return self.inventor.apply(prompt, name)

    def _apply_seq(self, prompt: str, names: list[str]) -> str:
        return self.inventor.apply_sequence(prompt, names)

    def invent(self) -> list[str]:
        """Invent methods from the live prompt. Called when current method dies."""
        base = self.live_prompt or self.seed_prompt
        new = self.inventor.invent(base)
        for name in new:
            if f"op:{name}" not in self.board.nodes:
                self.board.add(
                    f"op:{name}",
                    f"invented method {name} may gate security-relevant behavior",
                    [name],
                    prior=0.28,
                    why="runtime invention after collapse or cheap-battery exhaustion",
                )
        if new:
            self.methods_log.append({"event": "invent", "ops": ",".join(new)})
        return new

    def observe(self, prompt: str, obs: Any, *, baseline: Any | None, ops: list[str] | None = None) -> Contrast:
        from aivd.science.contrast import _text
        import re

        c = contrast(obs, baseline)
        used_ops = list(ops or [])
        self.tested.add(prompt)
        self.last_prompt = prompt
        self.last_ops = used_ops
        text = _text(obs)
        labels = {m.lower() for m in re.findall(r"\b([A-Za-z]{3,24})\s*:", text)}
        stop = {
            "the", "and", "for", "with", "from", "this", "that", "then",
            "next", "also", "just", "only", "ok",
        }
        recent: list[str] = []
        for raw in text.replace(":", " ").replace(",", " ").replace("|", " ").split():
            t = raw.strip().lower()
            if not (3 <= len(t) <= 24 and t.isalpha()):
                continue
            if t in labels or t in stop:
                continue
            if t not in self.content_tokens:
                self.content_tokens.append(t)
                self.board.add(
                    f"tok:{t}",
                    f"just-observed token {t} is an operand worth testing",
                    [f"token:{t}"],
                    prior=0.4,
                    why="content appeared after a probe; not a catalog name",
                )
            if t not in recent:
                recent.append(t)
        self.recent_tokens = recent
        self.history.append({
            "prompt": prompt,
            "ops": used_ops,
            "contrast": c.as_dict(),
            "recent": recent,
            "live": self.live_prompt,
            "collapsed": self.collapsed,
        })

        if not used_ops:
            self.live_prompt = prompt
            self.live_ops = []
            self.live_metric = c.metric
            self.live_error = c.error
            self.tried_on_live = set()
            return c

        last = used_ops[-1]
        self.tried_on_live.add(last)

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

        informative = bool(
            c.secret
            or (c.security_shaped and not c.greedy_metric)
            or (c.metric_delta >= 0.08 and c.error and not c.greedy_metric)
        )
        prev = self.live_metric
        upgraded = False
        if c.greedy_metric:
            self.collapsed = False
        elif c.secret or c.metric > prev + 0.05:
            self.live_prompt = prompt
            self.live_ops = used_ops
            self.live_metric = c.metric
            self.live_error = c.error
            self.collapsed = False
            self.tried_on_live = {last}
            upgraded = True
        elif informative and prev < 0.2:
            self.live_prompt = prompt
            self.live_ops = used_ops
            self.live_metric = c.metric
            self.live_error = c.error
            self.collapsed = False
            self.tried_on_live = {last}
            upgraded = True
        elif prev >= 0.2 and (c.metric < prev - 0.06 or (self.live_error and not c.error)):
            self.collapsed = True
            hid = "dead:" + "+".join(used_ops)
            self.board.add(
                hid,
                "continuation of the live state collapsed",
                used_ops,
                prior=0.15,
                why="signal lost; do not chain the dead prompt",
            )
            self.board.update(hid, support=0.0, against=0.7)
            self.methods_log.append({
                "event": "collapse",
                "ops": "+".join(used_ops),
                "live": self.live_prompt,
            })
        else:
            self.collapsed = False

        if upgraded:
            for op in used_ops:
                if op not in self.supported_ops and op not in self.trap_ops:
                    self.supported_ops.append(op)
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
            meta={"ops": list(ops), "why": why, "live": self.live_prompt, "collapsed": self.collapsed},
        )

    def _candidate_ops(self) -> list[str]:
        seen: list[str] = []
        for op in list(BATTERY) + list(self.inventor.promoted) + list(self.inventor.invented):
            if op not in seen:
                seen.append(op)
        return seen

    def propose(self, *, remaining_steps: int = 6, evidence_strength: float = 0.4) -> list[ExperimentProposal]:
        out: list[ExperimentProposal] = []

        def add(p: ExperimentProposal | None) -> None:
            if p is not None and len(out) < self.max_new:
                out.append(p)

        # Invent once we have a live informative state, a collapse, or the
        # cheap battery has been fully tested — not before any evidence.
        battery_untested = [
            op for op in BATTERY
            if f"op:{op}" not in self.board.nodes or self.board.nodes[f"op:{op}"].tests == 0
        ]
        if not self.inventor.invented:
            if self.collapsed or self.supported_ops or not battery_untested:
                self.invent()
        elif self.collapsed and remaining_steps <= 4 and len(self.inventor.invented) < 8:
            self.invent()

        # 0. Collapse restore / live-state compose.
        #    Remaining operators on the LIVE prompt, never on a collapsed last_prompt.
        if self.collapsed or self.supported_ops:
            base = self.live_prompt
            base_ops = list(self.live_ops)
            for other in self._candidate_ops():
                if other in self.trap_ops:
                    continue
                if other in self.tried_on_live:
                    continue
                if base_ops and other == base_ops[-1]:
                    continue
                nxt = self._apply(base, other)
                if not nxt or nxt == base:
                    continue
                seq = base_ops + [other]
                in_battery = other in BATTERY
                node = self.board.nodes.get(f"op:{other}")
                tested_n = int(getattr(node, "tests", 0) or 0) if node is not None else 0
                # On a live informative prompt: untried methods first.
                # Already-tested singles that produced no support must not
                # exhaust the remaining 32 before invented methods run.
                if self.collapsed and in_battery:
                    disc = 0.96
                elif tested_n == 0:
                    disc = 0.94
                elif other in self.supported_ops:
                    disc = 0.90
                else:
                    disc = 0.78
                add(self._prop(
                    nxt,
                    seq,
                    disc=disc,
                    eig=0.32 if self.collapsed else 0.28,
                    sec=0.58,
                    unlock=True,
                    remaining=1,
                    evidence=max(evidence_strength, 0.7 if self.collapsed else 0.6),
                    why=(
                        f"restore live state then {other}"
                        if self.collapsed
                        else f"compose {other} onto live informative prompt"
                    ),
                ))
            if self.collapsed and out:
                return out[: self.max_new]

        # 1. Just-observed content tokens — test NEXT, not FIFO behind chrome.
        for tok in self.recent_tokens:
            add(self._prop(
                f"{self.seed_prompt} {tok}".strip(),
                [f"token:{tok}"],
                disc=0.92,
                eig=0.32,
                sec=0.5,
                unlock=True,
                remaining=1,
                evidence=0.7,
                why=f"just-observed content {tok}; test immediately as operand",
            ))
            live = self.live_prompt
            if live and live != self.seed_prompt:
                add(self._prop(
                    f"{live} {tok}".strip(),
                    (self.live_ops or []) + [f"token:{tok}"],
                    disc=0.93,
                    eig=0.33,
                    sec=0.55,
                    unlock=True,
                    remaining=1,
                    evidence=0.75,
                    why=f"append just-observed {tok} to the live informative prompt",
                ))
            if len(out) >= self.max_new:
                return out

        # 2. Seed-side compose of supported operators (same-prompt conjunction).
        for op in self.supported_ops:
            for other in self._candidate_ops():
                if other == op or other in self.trap_ops:
                    continue
                seq = [op, other]
                in_battery = other in BATTERY
                add(self._prop(
                    self._apply_seq(self.seed_prompt, seq),
                    seq,
                    disc=0.88 if in_battery else 0.84,
                    eig=0.28,
                    sec=0.55,
                    unlock=True,
                    remaining=1,
                    evidence=max(evidence_strength, 0.6),
                    why=f"supported {op}; compose with {other} from seed to discriminate conjunction",
                ))
                if len(out) >= self.max_new:
                    return out

        # 3. Untested battery / invented singles — competing hyps, not greedy-EIG.
        for op in self._candidate_ops():
            node = self.board.nodes.get(f"op:{op}")
            if node is not None and node.tests > 0:
                continue
            trap = op in ("repeat_last", "duplicate")
            in_battery = op in BATTERY
            add(self._prop(
                self._apply(self.seed_prompt, op),
                [op],
                disc=0.75 if in_battery else 0.72,
                eig=0.18 if trap else 0.22,
                sec=0.22,
                unlock=False,
                remaining=max(2, remaining_steps),
                evidence=0.25 if trap else evidence_strength,
                why=(
                    f"untested operator {op}; discriminate against alternatives"
                    if in_battery
                    else f"invented method {op}; cheap battery did not suffice"
                ),
            ))

        # 4. Reverse-order falsifiers for two-op live histories.
        if len(self.live_ops) >= 2:
            rev = list(reversed(self.live_ops[:2]))
            add(self._prop(
                self._apply_seq(self.seed_prompt, rev),
                rev,
                disc=0.8,
                eig=0.22,
                sec=0.4,
                unlock=False,
                remaining=2,
                evidence=0.4,
                why="reverse order to falsify order-insensitive conjunction",
            ))

        # 5. Ablation: drop last live op.
        if self.live_ops:
            rest = self.live_ops[:-1]
            prompt = self._apply_seq(self.seed_prompt, rest) if rest else self.seed_prompt
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


# Keep apply_operator / apply_sequence import used by tests that patch designer.
_ = (apply_operator, apply_sequence)


__all__ = ["ScienceDesigner"]
