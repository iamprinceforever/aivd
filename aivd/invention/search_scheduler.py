"""Adaptive search scheduler — explore/exploit/revive budgets; family then within-family.

GENERAL stem ordering from residual evidence (not Holdout-named early stems).
Counterfactual slots discriminate competing hypotheses H1/H2.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from aivd.invention.archive import FamilyArchive
from aivd.invention.dynamic_ranking import family_values, rank_dynamically
from aivd.invention.intervention_space import Intervention, extract_residual_tokens
from aivd.invention.priority_history import PriorityHistory
from aivd.invention.residual_salience import residual_salience, salience_linked_stems
from aivd.invention.family import cluster_interventions


@dataclass
class AdaptiveBudget:
    """Adaptive explore / exploit / revive allocation (fractions sum ~1)."""
    explore: float = 0.45
    exploit: float = 0.40
    revive: float = 0.15
    # Dynamically tilt based on coverage / salience
    adaptive: bool = True

    def tilt(
        self,
        *,
        coverage: float,
        salience: float,
        n_revivable: int,
        strong_success: bool = False,
    ) -> "AdaptiveBudget":
        if not self.adaptive:
            return AdaptiveBudget(self.explore, self.exploit, self.revive, adaptive=False)
        explore, exploit, revive = self.explore, self.exploit, self.revive
        # Low coverage → more explore
        if coverage < 0.25:
            explore += 0.12
            exploit -= 0.08
            revive -= 0.04
        # Without strong success, keep explore floor (anti-lock-in on mild echoes)
        if not strong_success:
            explore = max(explore, 0.50)
            exploit = min(exploit, 0.35)
        # High salience + coverage + strong success → more exploit
        if strong_success and salience >= 0.7 and coverage >= 0.2:
            exploit += 0.10
            explore -= 0.06
            revive -= 0.04
        # Reviable saturated families → revive budget
        if n_revivable > 0:
            revive = max(revive, 0.18)
            explore -= 0.04
            exploit -= 0.04
        # renormalize
        s = max(1e-9, explore + exploit + revive)
        return AdaptiveBudget(explore / s, exploit / s, revive / s, adaptive=True)

    def as_dict(self) -> dict[str, float | bool]:
        return {
            "explore": self.explore,
            "exploit": self.exploit,
            "revive": self.revive,
            "adaptive": self.adaptive,
        }


@dataclass
class SearchScheduler:
    """Family-level adaptive pick then within-family candidate pick + reorder."""
    archive: FamilyArchive
    priority_history: PriorityHistory
    seed: int = 0
    budget: AdaptiveBudget = field(default_factory=AdaptiveBudget)
    history: list[dict[str, Any]] = field(default_factory=list)
    ablation: str | None = None

    def _rng(self) -> random.Random:
        return random.Random(int(self.seed) + len(self.history) * 17)

    def allocate_slot_kind(self) -> str:
        sal = 0.5
        cov = self.archive.coverage()
        n_rev = len([
            b for b in self.archive.beliefs.values()
            if b.saturated or (self.priority_history.records.get(f"family:{b.family_id}")
                               and self.priority_history.records[f"family:{b.family_id}"].decayed)
        ])
        # salience from last history step if present
        if self.history:
            sal = float((self.history[-1].get("salience") or {}).get("aggregate") or 0.5)
        strong = any(
            b.n_success > 0 and (b.sum_effect / max(1, b.n_tested)) >= 0.5
            for b in self.archive.beliefs.values()
        )
        tilted = self.budget.tilt(
            coverage=cov, salience=sal, n_revivable=n_rev, strong_success=strong,
        )
        r = self._rng().random()
        if r < tilted.exploit:
            kind = "exploit"
        elif r < tilted.exploit + tilted.explore:
            kind = "explore"
        else:
            kind = "revive"
        self.history.append({
            "kind": "slot",
            "slot": kind,
            "budget": tilted.as_dict(),
            "coverage": cov,
            "salience": {"aggregate": sal},
        })
        return kind

    def pick_family(
        self,
        candidate_fids: list[str],
        *,
        residual_context: dict[str, Any] | None = None,
        slot: str | None = None,
    ) -> str | None:
        if not candidate_fids:
            return None
        slot = slot or self.allocate_slot_kind()
        ctx = residual_context or {}
        fvals = family_values(
            self.archive, residual_context=ctx, priority_history=self.priority_history
        )
        # GENERAL stem ordering from evidence
        stem_order = salience_linked_stems(ctx)
        stem_rank = {s: i for i, s in enumerate(stem_order)}

        def sort_key(fid: str) -> tuple:
            b = self.archive.beliefs.get(fid)
            feats = (b.features or {}) if b else {}
            stem = str(feats.get("stem_bucket") or "")
            val = fvals.get(fid, 0.0)
            sr = stem_rank.get(stem, 10_000)
            tested = b.n_tested if b else 0
            saturated = bool(b and b.saturated and not b.revived)
            revived = bool(b and b.revived)
            return (val, sr, tested, saturated, revived, fid)

        if slot == "exploit":
            # highest family value among non-barren
            eligible = [
                f for f in candidate_fids
                if not (
                    f in self.archive.beliefs
                    and self.archive.beliefs[f].saturated
                    and not self.archive.beliefs[f].revived
                )
            ] or list(candidate_fids)
            fid = max(eligible, key=lambda f: (sort_key(f)[0], -sort_key(f)[1], f))
        elif slot == "revive":
            revivable = [
                f for f in candidate_fids
                if f in self.archive.beliefs and (
                    self.archive.beliefs[f].saturated
                    or self.archive.beliefs[f].revived
                    or (
                        f"family:{f}" in self.priority_history.records
                        and self.priority_history.records[f"family:{f}"].decayed
                    )
                )
            ]
            if revivable:
                fid = max(revivable, key=lambda f: (sort_key(f)[0], f))
            else:
                # fall back to least tested residual-linked
                fid = min(
                    candidate_fids,
                    key=lambda f: (
                        self.archive.beliefs[f].n_tested if f in self.archive.beliefs else 0,
                        sort_key(f)[1],
                        f,
                    ),
                )
        else:  # explore
            # Prefer untested / residual-linked under GENERAL stem order from evidence
            untested = [
                f for f in candidate_fids
                if f not in self.archive.beliefs or self.archive.beliefs[f].n_tested == 0
            ]
            pool = untested or list(candidate_fids)
            # residual-linked first; then evidence stem order; then family value (not alpha)
            def explore_key(f: str):
                b = self.archive.beliefs.get(f)
                feats = (b.features or {}) if b else {}
                stem = str(feats.get("stem_bucket") or "")
                res = 0 if feats.get("residual_linked") else 1
                return (res, stem_rank.get(stem, 10_000), -fvals.get(f, 0.0), f)
            pool = sorted(pool, key=explore_key)
            fid = pool[0]

        self.history.append({
            "kind": "family_pick",
            "family_id": fid,
            "slot": slot,
            "family_value": fvals.get(fid),
        })
        return fid

    def pick_within_family(
        self,
        members: list[Intervention],
        *,
        residual_context: dict[str, Any] | None = None,
        seen_sequences: set[str] | None = None,
        prefer_counterfactual: bool = False,
    ) -> Intervention | None:
        if not members:
            return None
        ranked = rank_dynamically(
            members, self.archive,
            residual_context=residual_context,
            seen_sequences=seen_sequences,
            priority_history=self.priority_history,
            ablation=self.ablation,
        )
        if prefer_counterfactual:
            cf = [c for c in ranked if c.strategy == "counterfactual"]
            if cf:
                return cf[0]
        return ranked[0]

    def select_batch(
        self,
        cands: list[Intervention],
        *,
        residual_context: dict[str, Any] | None = None,
        seen_sequences: set[str] | None = None,
        batch_size: int = 8,
    ) -> tuple[list[Intervention], list[dict[str, Any]]]:
        """Adaptive batch: family-level stats then within-family pick; log reasons."""
        ctx = residual_context or {}
        rtoks = extract_residual_tokens(ctx)
        sal = residual_salience(ctx)
        clusters = cluster_interventions(cands, residual_tokens=rtoks, coarse=True)
        for fid, members in clusters.items():
            feats = (members[0].meta or {}).get("family_features") or {}
            self.archive.ensure(fid, features=feats)
            self.priority_history.ensure(f"family:{fid}", initial=0.5 + 0.2 * (1.0 if feats.get("residual_linked") else 0.0))

        self.archive.revive_on_evidence(rtoks)
        self.priority_history.revive_matching(
            rtoks,
            {f"family:{fid}": (self.archive.beliefs[fid].features or {}) for fid in clusters},
        )

        selected: list[Intervention] = []
        selected_ids: set[str] = set()
        remaining = {fid: list(members) for fid, members in clusters.items()}
        steps: list[dict[str, Any]] = []
        bs = max(1, int(batch_size))

        # Counterfactual discrimination slot (H1/H2) when multi-channel residual
        n_sec = len(ctx.get("security_shaped_residuals") or [])
        need_cf = n_sec >= 1 or float(ctx.get("unexplained") or 0) > 0.5

        while len(selected) < bs and remaining:
            slot = self.allocate_slot_kind()
            fid = self.pick_family(list(remaining.keys()), residual_context=ctx, slot=slot)
            if fid is None or fid not in remaining:
                break
            members = [m for m in remaining[fid] if m.id not in selected_ids]
            if not members:
                remaining.pop(fid, None)
                continue
            prefer_cf = need_cf and len(selected) == 0
            pick = self.pick_within_family(
                members,
                residual_context=ctx,
                seen_sequences=seen_sequences,
                prefer_counterfactual=prefer_cf,
            )
            if pick is None:
                remaining.pop(fid, None)
                continue
            selected.append(pick)
            selected_ids.add(pick.id)
            remaining[fid] = [m for m in members if m.id != pick.id]
            if not remaining[fid]:
                remaining.pop(fid, None)
            reason = {
                "slot": slot,
                "family_id": fid,
                "candidate_id": pick.id,
                "sequence": list(pick.sequence),
                "score": pick.score,
                "strategy": pick.strategy,
                "salience_aggregate": sal["aggregate"],
                "prefer_counterfactual": prefer_cf and pick.strategy == "counterfactual",
                "value_terms": (pick.meta or {}).get("value_terms"),
            }
            steps.append(reason)

        if len(selected) < bs:
            leftovers = [c for c in cands if c.id not in selected_ids]
            for m in rank_dynamically(
                leftovers, self.archive,
                residual_context=ctx,
                seen_sequences=seen_sequences,
                priority_history=self.priority_history,
                top_k=bs - len(selected),
                ablation=self.ablation,
            ):
                selected.append(m)
                steps.append({
                    "slot": "leftover",
                    "family_id": (m.meta or {}).get("family_id"),
                    "candidate_id": m.id,
                    "sequence": list(m.sequence),
                    "score": m.score,
                })

        return selected[:bs], steps

    def as_dict(self) -> dict[str, Any]:
        return {
            "budget": self.budget.as_dict(),
            "n_history": len(self.history),
            "ablation": self.ablation,
            "priority": self.priority_history.as_dict(),
        }
