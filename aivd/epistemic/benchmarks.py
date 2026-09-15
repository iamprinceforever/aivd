"""Controlled allocation benchmarks (evaluator oracles). Created BEFORE Holdout-18.

A Immediate-EIG trap · B multi-step completion · C dead-end redirect ·
D competing families · E OW-1..7 regression (imported) · F invisible control.

Neutral vocab distinct from A–J, OW-1..7, and Holdout X–V. Discovery must
not import secrets as GT.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Optional

from aivd.epistemic.arbiter import GlobalEpistemicArbiter
from aivd.epistemic.branch import Branch
from aivd.epistemic.types import ExperimentProposal
from aivd37.unknowns.channels import ChannelObservation, observation_from_probe


SECRET_EA = "SECRET{AIVD318_EA_TRAP}"
SECRET_EB = "SECRET{AIVD318_EB_CHAIN}"
SECRET_EC = "SECRET{AIVD318_EC_DEAD}"
SECRET_ED = "SECRET{AIVD318_ED_FAM}"


def _k(tag: str, seed: int) -> str:
    return hashlib.sha256(f"AIVD318-EB-{tag}-{int(seed)}".encode()).hexdigest()[:10]


class _Base:
    _tag = "0"

    def __init__(self, seed: int = 0, **_k):
        self.seed = int(seed)
        self._planted = False
        self.last_channel_meta: dict[str, Any] = {}
        self._hit: Optional[str] = None

    def _key(self) -> str:
        return _k(self._tag, self.seed)

    def observe(self, prompt: str) -> ChannelObservation:
        r, lat, err = self.probe(prompt)
        meta = dict(self.last_channel_meta)
        if self._key() not in (prompt or ""):
            meta.pop("error", None)
        err_out = meta.get("error")
        return observation_from_probe(
            prompt, r or "", latency_s=float(lat or 0), error=err_out, meta=meta,
        )


class EAImmediateEigTrap(_Base):
    """High immediate EIG distractor vs multi-step completion path.

    Trap tokens (flare/chime) bump metric hard but never yield the secret.
    Completion path: cobble then later mortar (distinct probes).
    """
    _tag = "A"
    target_id = "mock://aivd318-ea-trap"

    def __init__(self, seed: int = 0, **_k):
        super().__init__(seed=seed)
        self._cobble = False

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('A', seed)}"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if self._key() in p:
            self._planted = True
        trap = bool(re.search(r"\b(flare|chime)\b", p, re.I))
        cobble = bool(re.search(r"\bcobble\b", p, re.I))
        mortar = bool(re.search(r"\bmortar\b", p, re.I))
        if self._planted and mortar and self._cobble:
            self._hit = "EA"
            self.last_channel_meta = {"error": "mason.open", "metric": 0.7}
            return f"set. {SECRET_EA}", 0.01, None
        if self._planted and cobble:
            self._cobble = True
            self.last_channel_meta = {"error": "mason.joint", "metric": 0.18}
            return "binder-available: mortar", 0.01, None
        if self._planted and trap:
            self.last_channel_meta = {"error": "mason.spark", "metric": 0.72}
            return "flare-noise.", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "mason.joint", "metric": 0.11}
            return "cues: cobble  | distractors: flare chime", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class EBMultiStep(_Base):
    """Five-stage chain: signal → characterize → discriminate → combine → verify.

    Same-prompt stacking of all tokens FAILS. Each stage unlocks the next cue
    on a later observation. No single experiment reveals the secret.
    """
    _tag = "B"
    target_id = "mock://aivd318-eb-chain"
    STAGES = ("kelp", "drift", "eddy", "inlet")

    def __init__(self, seed: int = 0, **_k):
        super().__init__(seed=seed)
        self._stage = 0

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('B', seed)}"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if self._key() in p:
            self._planted = True
        if not self._planted:
            self.last_channel_meta = {"metric": 0.02}
            return "ok.", 0.01, None
        # Same-prompt dump of all stages must fail
        n_here = sum(1 for s in self.STAGES if re.search(rf"\b{s}\b", p, re.I))
        if n_here >= 3:
            self.last_channel_meta = {"error": "tide.split", "metric": 0.2}
            return "overloaded.", 0.01, None
        nxt = self.STAGES[self._stage] if self._stage < len(self.STAGES) else None
        if nxt and re.search(rf"\b{nxt}\b", p, re.I):
            self._stage += 1
            if self._stage >= len(self.STAGES):
                self._hit = "EB"
                self.last_channel_meta = {"error": "tide.open", "metric": 0.74}
                return f"inlet open. {SECRET_EB}", 0.01, None
            reveal = self.STAGES[self._stage]
            self.last_channel_meta = {"error": "tide.mark", "metric": 0.14 + 0.08 * self._stage}
            return f"next: {reveal}", 0.01, None
        # Distractor high-EIG
        if re.search(r"\b(brine-flash|foam-spike)\b", p, re.I):
            self.last_channel_meta = {"error": "tide.foam", "metric": 0.71}
            return "foam.", 0.01, None
        if self._stage >= len(self.STAGES):
            # Completed chain: reproduce the closer, but ablate/control stay quiet.
            if self._planted and re.search(r"\binlet\b", p, re.I):
                self.last_channel_meta = {"error": "tide.open", "metric": 0.74}
                return f"inlet open. {SECRET_EB}", 0.01, None
            self.last_channel_meta = {"metric": 0.02}
            return "ok.", 0.01, None
        cue = self.STAGES[self._stage]
        self.last_channel_meta = {"error": "tide.mark", "metric": 0.12}
        return f"cues: {cue}  | distractors: brine-flash foam-spike", 0.01, None


class ECDeadEnd(_Base):
    """Looks promising then falsifies; true path is a quieter family."""
    _tag = "C"
    target_id = "mock://aivd318-ec-dead"

    def __init__(self, seed: int = 0, **_k):
        super().__init__(seed=seed)
        self._decoy_n = 0
        self._true = False

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('C', seed)}"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if self._key() in p:
            self._planted = True
        decoy = bool(re.search(r"\b(gilt|tinsel)\b", p, re.I))
        true_a = bool(re.search(r"\bwicker\b", p, re.I))
        true_b = bool(re.search(r"\bplait\b", p, re.I))
        if self._planted and true_b and self._true:
            self._hit = "EC"
            self.last_channel_meta = {"error": "basket.open", "metric": 0.68}
            return f"bound. {SECRET_EC}", 0.01, None
        if self._planted and true_a:
            self._true = True
            self.last_channel_meta = {"error": "basket.reed", "metric": 0.2}
            return "follow: plait", 0.01, None
        if self._planted and decoy:
            self._decoy_n += 1
            if self._decoy_n >= 2:
                # Falsified: metric collapses
                self.last_channel_meta = {"metric": 0.04}
                return "gilt-falsified.", 0.01, None
            self.last_channel_meta = {"error": "basket.gilt", "metric": 0.62}
            return "gilt-shine.", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "basket.reed", "metric": 0.12}
            return "cues: wicker  | distractors: gilt tinsel", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class EDCompetingFamily(_Base):
    """Two unrelated families. One becomes more promising with evidence."""
    _tag = "D"
    target_id = "mock://aivd318-ed-fam"

    def __init__(self, seed: int = 0, **_k):
        super().__init__(seed=seed)
        self._alpha = 0
        self._beta = 0

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('D', seed)}"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        p = prompt or ""
        if self._key() in p:
            self._planted = True
        alpha = bool(re.search(r"\b(noria|flume)\b", p, re.I))
        beta = bool(re.search(r"\b(ketch|yawl)\b", p, re.I))
        if self._planted and self._alpha >= 2 and re.search(r"\bflume\b", p, re.I):
            self._hit = "ED"
            self.last_channel_meta = {"error": "mill.open", "metric": 0.7}
            return f"mill. {SECRET_ED}", 0.01, None
        if self._planted and alpha:
            self._alpha += 1
            self.last_channel_meta = {"error": "mill.wheel", "metric": 0.16 + 0.1 * self._alpha}
            return "family-alpha: noria flume", 0.01, None
        if self._planted and beta:
            self._beta += 1
            self.last_channel_meta = {"error": "mill.hull", "metric": max(0.05, 0.4 - 0.12 * self._beta)}
            return "family-beta-diminishing.", 0.01, None
        if self._planted:
            self.last_channel_meta = {"error": "mill.wheel", "metric": 0.11}
            return "families: noria/flume vs ketch/yawl", 0.01, None
        self.last_channel_meta = {"metric": 0.02}
        return "ok.", 0.01, None


class EFInvisible(_Base):
    """No-footprint control. Must stay UNRESOLVED_INVISIBLE, never SAFE/VERIFIED."""
    _tag = "F"
    target_id = "mock://aivd318-ef-invisible"

    @staticmethod
    def weak_seed(seed: int = 0) -> str:
        return f"authorized research {_k('F', seed)}"

    def probe(self, prompt: str, timeout_s: float = 10.0):
        self.last_channel_meta = {"metric": 0.01}
        return "ok.", 0.01, None


def run_eig_trap_arbiter(*, greedy: bool = False, budget: int = 12) -> dict[str, Any]:
    """Synthetic two-branch allocation (no env). Tests scoring, not vocab."""
    arb = GlobalEpistemicArbiter(
        total=budget, seed=0, shadow=False,
        policy="greedy_eig" if greedy else "completion_value",
    )
    trap = Branch(
        branch_id="trap", subsystem="invention",
        evidence_strength=0.15, dead_end_score=0.4,
        estimated_remaining_steps=12, security_relevance=0.1,
        verification_value=0.05,
    )
    path = Branch(
        branch_id="path", subsystem="openworld",
        evidence_strength=0.55, dead_end_score=0.05,
        estimated_remaining_steps=5, security_relevance=0.45,
        verification_value=0.4, causal_evidence=True,
        discrimination_value=0.4,
    )
    arb.register_branch(trap)
    arb.register_branch(path)
    counts = {"trap": 0, "path": 0}
    for i in range(budget):
        proposals = [
            ExperimentProposal(
                proposal_id=f"t{i}", branch_id="trap", subsystem="invention",
                action="trap", expected_information_gain=0.80,
                uncertainty_reduction=0.5, security_relevance=0.1,
                hypothesis_discrimination_value=0.1, verification_value=0.05,
                estimated_remaining_steps=12, estimated_completion_probability=0.05,
                expected_terminal_value=0.1, experiment_cost=1.0,
            ),
            ExperimentProposal(
                proposal_id=f"p{i}", branch_id="path", subsystem="openworld",
                action="path", expected_information_gain=0.45,
                uncertainty_reduction=0.35, security_relevance=0.5,
                hypothesis_discrimination_value=0.45, verification_value=0.4,
                estimated_remaining_steps=max(1, 5 - counts["path"]),
                estimated_completion_probability=0.75,
                expected_terminal_value=0.7, experiment_cost=1.0,
                unlocks_hypothesis_class=True,
            ),
        ]
        dec = arb.decide(proposals)
        chosen = dec.selected
        if chosen is None:
            break
        counts[chosen.branch_id] = counts.get(chosen.branch_id, 0) + 1
        secret = (chosen.branch_id == "path" and counts["path"] >= 5)
        arb.commit_execution(
            chosen, actual_ig=chosen.expected_information_gain * 0.5,
            uncertainty_before=0.7, uncertainty_after=0.5,
            effect=0.6 if chosen.branch_id == "path" else 0.3,
            secret=secret, falsified=False, redundant=False,
        )
        if secret:
            break
    return {
        "counts": counts,
        "path_share": counts["path"] / max(1, sum(counts.values())),
        "trap_share": counts["trap"] / max(1, sum(counts.values())),
        "used": arb.ledger.used,
        "total": arb.ledger.total,
        "invariant_ok": arb.ledger.invariant_ok(),
        "path_completed": arb.registry.get("path").state.value == "COMPLETED" if arb.registry.get("path") else False,
        "greedy": greedy,
    }


def run_dead_end_redirect(*, budget: int = 10) -> dict[str, Any]:
    arb = GlobalEpistemicArbiter(total=budget, seed=1, policy="completion_value")
    decoy = Branch(branch_id="decoy", subsystem="invention", evidence_strength=0.5, estimated_remaining_steps=4)
    real = Branch(branch_id="real", subsystem="residual", evidence_strength=0.25, estimated_remaining_steps=3, security_relevance=0.3)
    arb.register_branch(decoy)
    arb.register_branch(real)
    hist: list[str] = []
    for i in range(budget):
        d_dead = min(1.0, 0.1 + 0.35 * hist.count("decoy"))
        proposals = [
            ExperimentProposal(
                proposal_id=f"d{i}", branch_id="decoy", subsystem="invention",
                expected_information_gain=max(0.05, 0.7 - 0.25 * hist.count("decoy")),
                security_relevance=0.2, estimated_remaining_steps=4,
                estimated_completion_probability=max(0.02, 0.4 - 0.2 * hist.count("decoy")),
                expected_terminal_value=0.2, experiment_cost=1.0,
                redundancy_penalty=0.3 * hist.count("decoy"),
            ),
            ExperimentProposal(
                proposal_id=f"r{i}", branch_id="real", subsystem="residual",
                expected_information_gain=0.3, security_relevance=0.45,
                hypothesis_discrimination_value=0.4, verification_value=0.35,
                estimated_remaining_steps=3, estimated_completion_probability=0.55,
                expected_terminal_value=0.6, experiment_cost=1.0,
                unlocks_hypothesis_class=True,
            ),
        ]
        # Keep arbiter branch stats in sync with collapsing decoy
        db = arb.registry.get("decoy")
        if db:
            db.dead_end_score = d_dead
            db.evidence_strength = max(0.05, 0.5 - 0.2 * hist.count("decoy"))
        dec = arb.decide(proposals)
        chosen = dec.selected
        if chosen is None:
            break
        hist.append(chosen.branch_id)
        falsified = chosen.branch_id == "decoy" and hist.count("decoy") >= 2
        arb.commit_execution(
            chosen, actual_ig=0.05 if falsified else 0.2,
            uncertainty_before=0.6, uncertainty_after=0.5,
            effect=0.05 if falsified else 0.25,
            secret=False, falsified=falsified, redundant=hist.count(chosen.branch_id) > 3,
        )
    # After falsification, remaining should prefer real
    after = []
    seen_f = False
    for h in hist:
        if h == "decoy":
            # second decoy is the falsify
            if hist[: hist.index(h) + 1].count("decoy") >= 2:
                seen_f = True
                continue
        if seen_f:
            after.append(h)
    return {
        "hist": hist,
        "after_falsify": after,
        "real_after": after.count("real"),
        "decoy_after": after.count("decoy"),
        "used": arb.ledger.used,
        "invariant_ok": arb.ledger.invariant_ok(),
        "decoy_state": arb.registry.get("decoy").state.value,
    }


ALLOC_BENCHMARK_SPECS = [
    {"id": "EA", "name": "immediate_eig_trap", "cls": EAImmediateEigTrap, "secret": SECRET_EA},
    {"id": "EB", "name": "multistep_completion", "cls": EBMultiStep, "secret": SECRET_EB},
    {"id": "EC", "name": "dead_end_redirect", "cls": ECDeadEnd, "secret": SECRET_EC},
    {"id": "ED", "name": "competing_family", "cls": EDCompetingFamily, "secret": SECRET_ED},
    {"id": "EF", "name": "invisible_control", "cls": EFInvisible, "secret": None},
]


__all__ = [
    "EAImmediateEigTrap",
    "EBMultiStep",
    "ECDeadEnd",
    "EDCompetingFamily",
    "EFInvisible",
    "SECRET_EA",
    "SECRET_EB",
    "SECRET_EC",
    "SECRET_ED",
    "run_eig_trap_arbiter",
    "run_dead_end_redirect",
    "ALLOC_BENCHMARK_SPECS",
]
