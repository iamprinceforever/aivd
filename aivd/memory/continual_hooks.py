"""Controller hooks for continual learning — keep Controller lean."""
from __future__ import annotations

from typing import Any, Optional

from aivd.memory.manager import ContinualMemory
from aivd.memory.regions import region_priority
from aivd.metrics.trigger_diversity import classify_trigger_families


# Map GT / families → exploration dimensions for same-region residual uncertainty
VULN_TO_DIMENSION = {
    "PV-DELIM-BACKDOOR": "delimiter",
    "PV-SR-ENCODING": "encoding",
    "PV-SR-RAREFRAG": "rare_token",
    "PV-MEDIUM-LEET": "delimiter",
    "PV-COMPOSITIONAL": "compositional",
    "PV-SEQUENTIAL": "sequential",
    "PV-CONTEXTUAL": "contextual",
    "PV-RARE-CANARY": "rare_token",
    "PV-SPARSE-TOKEN": "rare_token",
    "PV-PROBABILISTIC": "indirect",
    "IB-A-PURE-SPARSE": "rare_token",
    "IB-B-SPARSE-FOOTPRINT": "rare_token",
    "IB-C-COMPOSITIONAL": "compositional",
    "IB-D-SEQUENTIAL": "sequential",
    "IB-E-CONTEXTUAL": "contextual",
    "IB-F-ENCODING": "encoding",
    "IB-G-PROBABILISTIC": "indirect",
    "IB-H-BOUNDARY": "delimiter",
    "IB-I-DELIM": "delimiter",
    "IB-I-ENC": "encoding",
    "IB-I-RARE": "rare_token",
    "IB-J-DECOY": "indirect",
}

# Logical behavioral region for the same-region multi-vuln suite
SAME_REGION_ID = "override_smuggling"
SAME_REGION_VULNS = {"PV-DELIM-BACKDOOR", "PV-SR-ENCODING", "PV-SR-RAREFRAG"}


def semantic_region_id(cluster_region: int | str, gt_hit: str | None) -> str:
    """Prefer stable semantic id for planted same-region suite; else cluster id."""
    if gt_hit and gt_hit in SAME_REGION_VULNS:
        return SAME_REGION_ID
    return f"cluster_{cluster_region}"


class ContinualSession:
    def __init__(
        self,
        memory: ContinualMemory,
        *,
        run_id: str,
        target_id: str,
        namespace: str = "target",
    ):
        self.memory = memory
        self.run_id = run_id
        self.target_id = target_id
        self.namespace = namespace
        self.known_vulns: set[str] = set()
        self.known_families: set[str] = set()
        self.seen_vuln_trigger: set[tuple[str, str]] = set()
        self.seen_strategies: set[str] = set()
        self.seen_regions: set[str] = set()
        # seed from persistent memory
        for rec in memory.semantic.list_regions(namespace):
            for v in rec.known_findings:
                self.known_vulns.add(v)
            for f in rec.trigger_families:
                self.known_families.add(f)
            self.seen_regions.add(rec.region_id)

    def reward_flags(self, *, gt_hit: str | None, prompt: str, region_id: str) -> dict[str, bool]:
        families = classify_trigger_families(prompt)
        primary_fam = families[0] if families else "other"
        is_new_vuln = bool(gt_hit) and gt_hit not in self.known_vulns
        is_new_fam = primary_fam not in self.known_families and primary_fam != "other"
        same_vt = False
        if gt_hit:
            key = (gt_hit, primary_fam)
            same_vt = key in self.seen_vuln_trigger
        dim = VULN_TO_DIMENSION.get(gt_hit or "", "")
        rec = self.memory.semantic.get(region_id, namespace=self.namespace)
        same_region_new_dim = False
        if dim and rec.dimensions_coverage.get(dim, 0.0) < 0.4:
            # exploring under-covered dimension in (possibly known) region
            same_region_new_dim = region_id in self.seen_regions or bool(rec.known_findings)
        return {
            "is_new_unique_vuln": is_new_vuln,
            "is_new_trigger_family": is_new_fam,
            "same_vuln_same_trigger": same_vt,
            "same_region_new_dimension": same_region_new_dim and not same_vt,
            "primary_family": primary_fam,
            "dimension": dim or None,
        }

    def after_probe(
        self,
        *,
        gt_hit: str | None,
        prompt: str,
        strategy: str,
        region_id: str,
        security: float,
        verification: float,
        reward: float,
        embedding: list[float],
        novelty: float,
        global_novelty: float,
        state: list[float] | dict,
        action: str | list | dict,
        success: bool,
    ) -> dict[str, Any]:
        flags = self.reward_flags(gt_hit=gt_hit, prompt=prompt, region_id=region_id)
        fam = flags["primary_family"]
        dim = flags["dimension"]
        rec = self.memory.semantic.get(region_id, namespace=self.namespace)
        # also write to run namespace
        rec_run = self.memory.semantic.get(region_id, namespace="run")

        if gt_hit:
            for r in (rec, rec_run):
                r.record_finding(
                    gt_hit,
                    trigger_family=fam,
                    dimension=dim,
                    security_relevance=security,
                    strategy=strategy,
                    success=success,
                )
            self.known_vulns.add(gt_hit)
            self.seen_vuln_trigger.add((gt_hit, fam))
        else:
            for r in (rec, rec_run):
                r.record_visit(
                    dimension=dim,
                    strategy=strategy,
                    success=False,
                    security_relevance=security,
                )

        if fam and fam != "other":
            self.known_families.add(fam)
        self.seen_strategies.add(strategy)
        self.seen_regions.add(region_id)
        self.memory.semantic.put(rec, namespace=self.namespace)
        self.memory.semantic.put(rec_run, namespace="run")
        if embedding:
            self.memory.semantic.add_embedding(
                embedding, region_id=region_id, namespace=self.namespace, vuln_id=gt_hit or ""
            )

        self.memory.replay.add(
            state=state if not isinstance(state, dict) else state,
            action=action,
            reward=reward,
            embedding=embedding,
            region_id=region_id,
            novelty=novelty,
            global_novelty=global_novelty,
            security=security,
            verification=verification,
            run_id=self.run_id,
            target_id=self.target_id,
            namespace=self.namespace,
            vuln_id=gt_hit or "",
            trigger_family=fam,
            strategy=strategy,
            meta={"flags": {k: v for k, v in flags.items() if k != "primary_family"}},
        )
        return {
            "flags": flags,
            "region_priority": region_priority(rec),
            "residual_uncertainty": rec.residual_uncertainty,
            "known_findings": list(rec.known_findings),
        }

    def features_for_region(self, region_id: str, strategy: str = "") -> dict[str, float]:
        return self.memory.memory_features(region_id, namespace=self.namespace, strategy=strategy)

    def global_archive(self) -> list[list[float]]:
        return self.memory.semantic.archive_embeddings(namespace=self.namespace, limit=2000)
