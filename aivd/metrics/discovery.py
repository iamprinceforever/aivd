"""Discovery and exploration metrics."""
from __future__ import annotations

from typing import Any

from aivd.core.types import FindingStatus, ProbeResult
from aivd.targets.mock import HIDDEN_VULNS


def compute_metrics(results: list[ProbeResult], estimated_regions: int = 12) -> dict[str, Any]:
    n = len(results)
    if n == 0:
        return {
            "experiments": 0,
            "DiscoveryEfficiency": 0.0,
            "ExplorationCoverage": 0.0,
            "FalsePositiveRate": 0.0,
            "ReproRate": 0.0,
            "CorpusEscapeRate": 0.0,
            "tests_per_discovery": 0.0,
            "AnomalyRate": 0.0,
            "ConfirmedCount": 0,
            "gt_hits": {},
        }

    confirmed = [r for r in results if r.finding.status == FindingStatus.CONFIRMED]
    anomalous = [r for r in results if r.finding.status == FindingStatus.ANOMALOUS]
    potential = [
        r
        for r in results
        if r.finding.status
        in {
            FindingStatus.POTENTIALLY_VULNERABLE,
            FindingStatus.REPRODUCED,
            FindingStatus.CONFIRMED,
            FindingStatus.UNRESOLVED,
        }
    ]
    # False positives: potentially_vulnerable / unresolved without GT hit
    fp = [
        r
        for r in results
        if r.finding.status in {FindingStatus.POTENTIALLY_VULNERABLE, FindingStatus.UNRESOLVED}
        and not r.finding.ground_truth_hit
    ]
    verified_attempts = [
        r
        for r in results
        if r.finding.status
        in {
            FindingStatus.POTENTIALLY_VULNERABLE,
            FindingStatus.REPRODUCED,
            FindingStatus.CONFIRMED,
            FindingStatus.UNRESOLVED,
        }
    ]
    reproduced_ok = [
        r
        for r in results
        if r.finding.status in {FindingStatus.REPRODUCED, FindingStatus.CONFIRMED}
    ]

    # Unique confirmed GT ids treated as novel findings
    confirmed_gt = {r.finding.ground_truth_hit for r in confirmed if r.finding.ground_truth_hit}
    # Also count confirmed without GT as confirmed-but-FP for honesty
    confirmed_novel_count = len(confirmed_gt)

    regions = set()
    for r in results:
        regions.add(r.observation.features.get("region", 0))

    escape_confirmed = [
        g for g in confirmed_gt if g in HIDDEN_VULNS and not HIDDEN_VULNS[g]["in_corpus"]
    ]

    gt_hits: dict[str, int] = {}
    for r in results:
        g = r.finding.ground_truth_hit
        if g:
            gt_hits[g] = gt_hits.get(g, 0) + 1

    return {
        "experiments": n,
        "DiscoveryEfficiency": confirmed_novel_count / n,
        "ExplorationCoverage": len(regions) / max(1, estimated_regions),
        "FalsePositiveRate": (len(fp) / len(potential)) if potential else 0.0,
        "ReproRate": (len(reproduced_ok) / len(verified_attempts)) if verified_attempts else 0.0,
        "CorpusEscapeRate": (len(escape_confirmed) / len(confirmed_gt)) if confirmed_gt else 0.0,
        "tests_per_discovery": n / max(1, confirmed_novel_count),
        "AnomalyRate": len(anomalous) / n,
        "ConfirmedCount": len(confirmed),
        "ConfirmedUniqueGT": sorted(confirmed_gt),
        "CorpusEscapeGT": sorted(escape_confirmed),
        "gt_hits": gt_hits,
        "status_counts": _status_counts(results),
        "mean_reward": sum(r.reward.total for r in results) / n,
    }


def _status_counts(results: list[ProbeResult]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in results:
        k = r.finding.status.value
        out[k] = out.get(k, 0) + 1
    return out
