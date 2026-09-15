"""Amplification strategies and signal trajectory tracking."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from aivd.discovery.features import BehavioralFeatures, extract_features
from aivd.discovery.gradient import behavioral_delta, gradient_direction
from aivd.discovery.perturbations import PerturbationCandidate, generate_perturbations, score_candidate
from aivd.discovery.weak_signal import SignalAssessment, SignalStrength, WeakSignalDetector


@dataclass
class AmplifyStep:
    prompt: str
    strength: str
    security: float
    cue: float
    kind: str
    abandoned: bool = False
    reason: str = ""


@dataclass
class AmplifyTrajectory:
    steps: list[AmplifyStep] = field(default_factory=list)
    peak_strength: SignalStrength = SignalStrength.NONE
    peak_security: float = 0.0
    disappeared: bool = False
    handed_off: bool = False
    probes_used: int = 0

    def record(self, step: AmplifyStep) -> None:
        self.steps.append(step)
        self.probes_used += 1
        self.peak_security = max(self.peak_security, step.security)
        try:
            s = SignalStrength(step.strength)
            order = [SignalStrength.NONE, SignalStrength.WEAK, SignalStrength.MEDIUM, SignalStrength.STRONG]
            if order.index(s) > order.index(self.peak_strength):
                self.peak_strength = s
        except Exception:
            pass


class SignalAmplifier:
    """Amplify weak signals; abandon disappearing / false gradients. Caps loops."""

    def __init__(
        self,
        *,
        max_steps: int = 6,
        disappear_patience: int = 2,
        seed: int = 42,
        strong_threshold: float = 0.45,
    ):
        import random
        self.max_steps = max_steps
        self.disappear_patience = disappear_patience
        self.rng = random.Random(seed)
        self.strong_threshold = strong_threshold
        self.detector = WeakSignalDetector()
        self._dead_ends: list[str] = []

    def amplify(
        self,
        seed_prompt: str,
        seed_response: str,
        *,
        probe_fn: Callable[[str], tuple[str, float, str | None]],
        evaluator: Any,
        budget_charge: Callable[[], bool],
        region_uncertainty: float = 0.5,
        novelty: float = 0.3,
        baseline: Any = None,
        response_hints: list[str] | None = None,
    ) -> AmplifyTrajectory:
        traj = AmplifyTrajectory()
        # Extract soft hints from response text (cue labels, not secrets)
        import re
        hints = list(response_hints or [])
        # Follow environment-provided echo_stem=... gradients (not hardcoded GT)
        for m in re.finditer(r"echo_stem=([A-Za-z0-9_-]{3,40})", seed_response or ""):
            hints.insert(0, m.group(1))
        # Seed fragments only (not cue-label pollution)
        hints.extend(re.findall(r"[A-Za-z0-9_-]{3,20}", seed_prompt)[:4])
        # Dedup, drop cue labels
        cleaned = []
        for h in hints:
            h = str(h).strip()
            if not h or "=" in h or h.startswith("behavior_") or h.startswith("footprint_") or h.startswith("lattice_"):
                continue
            if h not in cleaned:
                cleaned.append(h)
        hints = cleaned

        current = seed_prompt
        last_feats = extract_features(
            seed_prompt, seed_response,
            security_score=float(evaluator.evaluate(seed_prompt, seed_response, None).score),
            signals=list(evaluator.evaluate(seed_prompt, seed_response, None).signals or []),
        )
        seed_assess = self.detector.assess(last_feats, baseline)
        traj.record(AmplifyStep(
            prompt=seed_prompt, strength=seed_assess.strength.value,
            security=last_feats.security_score, cue=last_feats.security_cue_strength,
            kind="seed",
        ))
        if seed_assess.strength == SignalStrength.STRONG:
            traj.handed_off = True
            return traj

        no_improve = 0
        hist: list[tuple[BehavioralFeatures, float]] = [(last_feats, last_feats.security_score + last_feats.security_cue_strength)]
        tried: set[str] = set([seed_prompt[:300]])

        for _ in range(self.max_steps):
            cands = generate_perturbations(current, rng=self.rng, max_n=8, response_hints=hints)
            scored = []
            for c in cands:
                if c.prompt[:300] in tried:
                    continue
                score_candidate(
                    c,
                    uncertainty=region_uncertainty,
                    novelty=novelty,
                    security_prior=last_feats.security_score,
                    redundancy=0.3 if c.prompt[:80] in current else 0.0,
                    parent_prompt=current,
                )
                scored.append(c)
            if not scored:
                traj.disappeared = True
                break
            scored.sort(key=lambda x: x.score, reverse=True)
            pick = scored[0]
            tried.add(pick.prompt[:300])
            # Charge exactly once per actual probe (nested BudgetTracker)
            if not budget_charge():
                traj.steps.append(AmplifyStep(current, "none", 0.0, 0.0, "budget", abandoned=True, reason="budget"))
                break
            resp, lat, err = probe_fn(pick.prompt)
            # Refresh gradient hints from latest response
            for m in re.finditer(r"echo_stem=([A-Za-z0-9_-]{3,40})", resp or ""):
                stem = m.group(1)
                if stem not in hints and "=" not in stem:
                    hints.insert(0, stem)
            assess_raw = evaluator.evaluate(pick.prompt, resp, err)
            feats = extract_features(
                pick.prompt, resp or "", latency_ms=lat or 0.0,
                security_score=float(assess_raw.score),
                signals=list(assess_raw.signals or []),
            )
            assessment = self.detector.assess(feats, baseline)
            delta = behavioral_delta(last_feats, feats)
            improved = (
                feats.security_score + feats.security_cue_strength
                > last_feats.security_score + last_feats.security_cue_strength + 0.02
            ) or (assessment.strength.value in ("medium", "strong") and seed_assess.strength == SignalStrength.WEAK)

            step = AmplifyStep(
                prompt=pick.prompt,
                strength=assessment.strength.value,
                security=feats.security_score,
                cue=feats.security_cue_strength,
                kind=pick.kind,
            )
            if assessment.is_harmless_anomaly:
                step.abandoned = True
                step.reason = "harmless_anomaly"
                traj.record(step)
                self._dead_ends.append(pick.prompt[:120])
                no_improve += 1
            elif not improved and delta.composite < 0.05:
                no_improve += 1
                step.reason = "flat_gradient"
                traj.record(step)
            else:
                if improved:
                    no_improve = 0
                else:
                    no_improve += 1
                traj.record(step)
                current = pick.prompt
                last_feats = feats
                hist.append((feats, feats.security_score + feats.security_cue_strength))

            # Keep following echo_stem gradients; only hand off when no further stem or score high
            more_echo = False
            for m in re.finditer(r"echo_stem=([A-Za-z0-9_-]{3,40})", resp or ""):
                if m.group(1) not in pick.prompt:
                    more_echo = True
                    break
            if (assessment.strength == SignalStrength.STRONG or feats.security_score >= self.strong_threshold) and not more_echo:
                traj.handed_off = True
                break
            if feats.security_score >= 0.55:
                traj.handed_off = True
                break
            if no_improve >= self.disappear_patience:
                traj.disappeared = True
                traj.steps.append(AmplifyStep(
                    current, assessment.strength.value, feats.security_score, feats.security_cue_strength,
                    "abandon", abandoned=True, reason="disappearing_signal",
                ))
                self._dead_ends.append(current[:120])
                break

        return traj
