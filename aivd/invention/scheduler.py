"""Family-level adaptive budget allocation with saturation / revival."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aivd.invention.archive import FamilyArchive
from aivd.invention.exploration import select_family
from aivd.invention.intervention_space import ACTION_STEMS


@dataclass
class FamilyScheduler:
    """Allocates cheap-test slots across structural families."""
    archive: FamilyArchive
    exploration: str = "thompson"
    seed: int = 0
    exploration_enabled: bool = True
    # per-family soft caps (revisitable when saturated cleared)
    per_family_cap: int = 6
    allocated: dict[str, int] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def allocate_next(self, candidate_fids: list[str]) -> str | None:
        if not candidate_fids:
            return None
        if not self.exploration_enabled:
            # round-robin / least-allocated coverage without bandit
            fid = min(candidate_fids, key=lambda f: (self.allocated.get(f, 0), f))
            self.allocated[fid] = self.allocated.get(fid, 0) + 1
            self.history.append({"family_id": fid, "policy": "coverage_rr"})
            return fid

        # respect soft caps but never hard-blacklist
        eligible = [
            f for f in candidate_fids
            if self.allocated.get(f, 0) < self.per_family_cap
            or (f in self.archive.beliefs and self.archive.beliefs[f].revived)
        ]
        if not eligible:
            eligible = list(candidate_fids)

        # Prefer never-tested residual-linked families (structural evidence, not GT names).
        # While any remain, round-robin by stem for systematic coverage (not novelty-alone).
        untested_residual = [
            f for f in eligible
            if f in self.archive.beliefs
            and self.archive.beliefs[f].n_tested == 0
            and bool((self.archive.beliefs[f].features or {}).get("residual_linked"))
        ]
        if untested_residual:
            stem_order = {s: i for i, s in enumerate(ACTION_STEMS)}
            untested_residual = sorted(
                untested_residual,
                key=lambda f: (
                    stem_order.get(
                        str((self.archive.beliefs[f].features or {}).get("stem_bucket") or ""),
                        10_000,
                    ),
                    f,
                ),
            )
            # Walk in ACTION_STEMS order (lexicon coverage), advancing each allocation
            idx = min(len(self.history), len(untested_residual) - 1)
            # prefer least-allocated among the next window to avoid alphabetical starvation
            # Take the first never-allocated in stem order
            fid = None
            for cand in untested_residual:
                if self.allocated.get(cand, 0) == 0:
                    fid = cand
                    break
            if fid is None:
                fid = untested_residual[0]
            self.allocated[fid] = self.allocated.get(fid, 0) + 1
            self.history.append({"family_id": fid, "policy": "residual_coverage_rr"})
            return fid
        fid = select_family(
            self.exploration,
            self.archive,
            eligible,
            seed=self.seed + len(self.history),
            allow_saturated=False,
        )
        if fid is None:
            # all saturated — allow revisit of least-tested saturated
            fid = select_family(
                self.exploration,
                self.archive,
                eligible,
                seed=self.seed + len(self.history),
                allow_saturated=True,
            )
        if fid is None:
            return None
        self.allocated[fid] = self.allocated.get(fid, 0) + 1
        self.history.append({"family_id": fid, "policy": self.exploration})
        return fid

    def maybe_revive(self, evidence_tokens: list[str] | None) -> list[str]:
        return self.archive.revive_on_evidence(evidence_tokens)

    def as_dict(self) -> dict[str, Any]:
        return {
            "exploration": self.exploration,
            "exploration_enabled": self.exploration_enabled,
            "allocated": dict(self.allocated),
            "n_allocations": len(self.history),
            "per_family_cap": self.per_family_cap,
        }
