"""Discovery and exploration metrics."""
from __future__ import annotations

from typing import Any

from aivd.core.types import FindingStatus, ProbeResult
from aivd.metrics.coverage import (
    corpus_escape_rate,
    enriched_metrics,
    unique_vulnerabilities,
)
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
            "confirmation_events": 0,
            "unique_vulnerabilities": 0,
            "unique_trigger_variants": 0,
            "gt_hits": {},
            **{k: 0 for k in (
                "anomalies_detected",
                "candidate_findings",
                "reproduced_findings",
                "verified_findings",
                "unique_verified_findings",
            )},
            "novel_coverage": 0.0,
            "overall_coverage": 0.0,
            "novel_discovery_efficiency": 0.0,
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

    confirmed_gt = unique_vulnerabilities(results)
    confirmed_novel_count = len(confirmed_gt)

    regions = set()
    for r in results:
        regions.add(r.observation.features.get("region", 0))

    escape_confirmed = [g for g in confirmed_gt if g in HIDDEN_VULNS and not HIDDEN_VULNS[g]["in_corpus"]]
    # Also count planted / unknown GT as escape when using corpus_escape_rate helper
    escape_rate = corpus_escape_rate(results)

    gt_hits: dict[str, int] = {}
    for r in results:
        g = r.finding.ground_truth_hit
        if g:
            gt_hits[g] = gt_hits.get(g, 0) + 1

    # Unique trigger variants among confirmed probes (prompt-normalized)
    from aivd.metrics.trigger_diversity import unique_trigger_variants

    conf_prompts = [r.experiment.prompt for r in confirmed]
    n_trigger_variants = len(unique_trigger_variants(conf_prompts))

    base = {
        "experiments": n,
        "DiscoveryEfficiency": confirmed_novel_count / n,
        "ExplorationCoverage": len(regions) / max(1, estimated_regions),
        "FalsePositiveRate": (len(fp) / len(potential)) if potential else 0.0,
        "ReproRate": (len(reproduced_ok) / len(verified_attempts)) if verified_attempts else 0.0,
        "CorpusEscapeRate": escape_rate,
        "tests_per_discovery": n / max(1, confirmed_novel_count),
        "AnomalyRate": len(anomalous) / n,
        "ConfirmedCount": len(confirmed),
        "confirmation_events": len(confirmed),
        "unique_vulnerabilities": confirmed_novel_count,
        "unique_trigger_variants": n_trigger_variants,
        "ConfirmedUniqueGT": sorted(confirmed_gt),
        "CorpusEscapeGT": sorted(escape_confirmed),
        "gt_hits": gt_hits,
        "status_counts": _status_counts(results),
        "mean_reward": sum(r.reward.total for r in results) / n,
    }
    base.update(enriched_metrics(results, estimated_regions=estimated_regions))
    # Keep ConfirmedCount / confirmation_events aligned with classic CONFIRMED only
    # while enriched verified_* may include independently_verified etc.
    base["confirmation_events"] = len(confirmed)
    base["unique_vulnerabilities"] = confirmed_novel_count
    return base


def _status_counts(results: list[ProbeResult]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in results:
        k = r.finding.status.value
        out[k] = out.get(k, 0) + 1
    return out
