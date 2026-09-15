"""Family archive — coverage, history, saturation state (revisitable, not blacklist)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aivd.invention.family import FamilyBelief


@dataclass
class FamilyArchive:
    """Tracks structural families seen / tested across an invention episode."""
    beliefs: dict[str, FamilyBelief] = field(default_factory=dict)
    coverage_order: list[str] = field(default_factory=list)
    # saturation thresholds (revisitable — never hard blacklist)
    sat_min_tests: int = 4
    sat_max_mean: float = 0.12
    revival_enabled: bool = True
    saturation_enabled: bool = True

    def ensure(self, family_id: str, features: dict[str, Any] | None = None) -> FamilyBelief:
        if family_id not in self.beliefs:
            self.beliefs[family_id] = FamilyBelief(
                family_id=family_id, features=dict(features or {})
            )
            self.coverage_order.append(family_id)
        elif features:
            # merge features if empty
            b = self.beliefs[family_id]
            if not b.features:
                b.features = dict(features)
        return self.beliefs[family_id]

    def record(
        self,
        family_id: str,
        *,
        effect: float,
        success: bool,
        features: dict[str, Any] | None = None,
        evidence: str = "",
    ) -> FamilyBelief:
        b = self.ensure(family_id, features=features)
        b.update(effect=effect, success=success, evidence=evidence)
        if self.saturation_enabled:
            self._maybe_saturate(b)
        return b

    def _maybe_saturate(self, b: FamilyBelief) -> None:
        if b.revived:
            return
        if b.n_tested < self.sat_min_tests:
            return
        emp = b.sum_effect / max(1, b.n_tested)
        # Saturate on empirical barrenness (revisitable via revival — never blacklist)
        if b.n_success == 0 or emp <= self.sat_max_mean:
            b.saturated = True

    def revive_on_evidence(self, evidence_tokens: list[str] | None) -> list[str]:
        """Revive saturated families whose features overlap new residual evidence."""
        if not self.revival_enabled or not evidence_tokens:
            return []
        toks = {str(t).lower() for t in evidence_tokens if t}
        revived: list[str] = []
        for fid, b in self.beliefs.items():
            if not b.saturated:
                continue
            feats = b.features or {}
            stem = str(feats.get("stem_bucket") or "").lower()
            surface = str(feats.get("surface") or "")
            # structural overlap with residual tokens → revive (not GT match)
            if stem and stem in toks:
                b.saturated = False
                b.revived = True
                b.beta = max(1.0, b.beta * 0.5)  # soften failure prior
                revived.append(fid)
            elif any(t in stem for t in toks if len(t) >= 3):
                b.saturated = False
                b.revived = True
                b.beta = max(1.0, b.beta * 0.5)
                revived.append(fid)
            elif surface.startswith("compound") and toks:
                # residual present after saturation → mild revival of compound families
                if b.n_success == 0 and b.n_tested >= self.sat_min_tests:
                    b.saturated = False
                    b.revived = True
                    revived.append(fid)
        return revived

    def coverage(self) -> float:
        """Fraction of known families that have been tested at least once."""
        if not self.beliefs:
            return 0.0
        tested = sum(1 for b in self.beliefs.values() if b.n_tested > 0)
        return tested / len(self.beliefs)

    def unique_tested(self) -> int:
        return sum(1 for b in self.beliefs.values() if b.n_tested > 0)

    def n_families(self) -> int:
        return len(self.beliefs)

    def saturated_ids(self) -> list[str]:
        return [fid for fid, b in self.beliefs.items() if b.saturated]

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_families": self.n_families(),
            "coverage": self.coverage(),
            "unique_tested": self.unique_tested(),
            "saturated": self.saturated_ids(),
            "beliefs": {fid: b.as_dict() for fid, b in self.beliefs.items()},
            "saturation_enabled": self.saturation_enabled,
            "revival_enabled": self.revival_enabled,
        }
