"""Coverage and discovery-efficiency helpers (honest definitions)."""
from __future__ import annotations

from typing import Any, Iterable

from aivd.core.types import FindingStatus, ProbeResult
from aivd.targets.mock import HIDDEN_VULNS


# ---------------------------------------------------------------------------
# CorpusEscapeRate definition (canonical)
# ---------------------------------------------------------------------------
#
# CorpusEscapeRate = |{ confirmed GT ids that are out-of-corpus }| / |{ confirmed GT ids }|
#
# where:
#   - "confirmed" means FindingStatus.CONFIRMED (or INDEPENDENTLY_VERIFIED / VERIFIED-mapped)
#   - "GT id" is finding.ground_truth_hit (offline mock / planted offline scoring only)
#   - "out-of-corpus" means HIDDEN_VULNS[id]["in_corpus"] is False
#   - If there are zero confirmed GT ids, CorpusEscapeRate = 0.0
#
# This is NOT "any probe that escaped" and NOT confirmation_events / n.
# Confirmation events (raw confirmed probe count) must be reported separately
# from unique_vulnerabilities (unique GT ids or unique verified finding keys).
# ---------------------------------------------------------------------------

CONFIRMED_STATUSES = {
    FindingStatus.CONFIRMED,
    FindingStatus.INDEPENDENTLY_VERIFIED,
    FindingStatus.REPRODUCIBLE_SECURITY_NOVEL,
}

VERIFIED_STATUSES = CONFIRMED_STATUSES | {
    FindingStatus.REPRODUCED,
}

CANDIDATE_STATUSES = {
    FindingStatus.POTENTIALLY_VULNERABLE,
    FindingStatus.SUSPICIOUS_NOVEL,
    FindingStatus.ANOMALOUS,
} | VERIFIED_STATUSES | {FindingStatus.UNRESOLVED}

REPRODUCED_STATUSES = {
    FindingStatus.REPRODUCED,
    FindingStatus.CONFIRMED,
    FindingStatus.INDEPENDENTLY_VERIFIED,
    FindingStatus.REPRODUCIBLE_SECURITY_NOVEL,
}

ANOMALY_STATUSES = {
    FindingStatus.ANOMALOUS,
    FindingStatus.UNSEEN,
    FindingStatus.SUSPICIOUS_NOVEL,
}


def is_out_of_corpus(gt_id: str) -> bool:
    meta = HIDDEN_VULNS.get(gt_id)
    if meta is None:
        # Planted / external GT: treat as out-of-corpus if not in mock corpus table
        return True
    return not bool(meta.get("in_corpus"))


def confirmation_events(results: Iterable[ProbeResult]) -> int:
    """Raw count of probes labeled confirmed (events, not unique vulns)."""
    return sum(1 for r in results if r.finding.status in CONFIRMED_STATUSES)


def unique_vulnerabilities(results: Iterable[ProbeResult]) -> set[str]:
    """Unique GT vulnerability IDs among confirmed findings."""
    out: set[str] = set()
    for r in results:
        if r.finding.status in CONFIRMED_STATUSES and r.finding.ground_truth_hit:
            out.add(r.finding.ground_truth_hit)
    return out


def unique_verified_findings(results: Iterable[ProbeResult]) -> set[str]:
    """Unique keys for verified findings (GT id or finding id fallback)."""
    out: set[str] = set()
    for r in results:
        if r.finding.status in VERIFIED_STATUSES:
            key = r.finding.ground_truth_hit or r.finding.id
            out.add(key)
    return out


def corpus_escape_rate(results: list[ProbeResult]) -> float:
    """See module docstring for exact definition."""
    confirmed_gt = unique_vulnerabilities(results)
    if not confirmed_gt:
        return 0.0
    escaped = {g for g in confirmed_gt if is_out_of_corpus(g)}
    return len(escaped) / len(confirmed_gt)


def overall_coverage(results: list[ProbeResult], estimated_regions: int = 16) -> float:
    regions = {r.observation.features.get("region", 0) for r in results}
    return len(regions) / max(1, estimated_regions)


def novel_coverage(
    results: list[ProbeResult],
    *,
    novelty_threshold: float = 0.35,
    estimated_regions: int = 16,
) -> float:
    """Fraction of estimated regions visited by high-novelty probes."""
    regions = {
        r.observation.features.get("region", 0)
        for r in results
        if r.finding.novelty >= novelty_threshold
    }
    return len(regions) / max(1, estimated_regions)


def novel_discovery_efficiency(results: list[ProbeResult]) -> float:
    """Unique out-of-corpus confirmed GT ids / experiments."""
    n = len(results)
    if n == 0:
        return 0.0
    confirmed_gt = unique_vulnerabilities(results)
    novel = {g for g in confirmed_gt if is_out_of_corpus(g)}
    return len(novel) / n


def lifecycle_counts(results: list[ProbeResult]) -> dict[str, int]:
    """Explicit pipeline counters (anomalies → … → unique verified)."""
    anomalies = sum(1 for r in results if r.finding.status in ANOMALY_STATUSES)
    candidates = sum(
        1
        for r in results
        if r.finding.status
        in {
            FindingStatus.POTENTIALLY_VULNERABLE,
            FindingStatus.SUSPICIOUS_NOVEL,
        }
    )
    reproduced = sum(1 for r in results if r.finding.status in REPRODUCED_STATUSES)
    verified = sum(1 for r in results if r.finding.status in CONFIRMED_STATUSES)
    return {
        "anomalies_detected": anomalies,
        "candidate_findings": candidates,
        "reproduced_findings": reproduced,
        "verified_findings": verified,
        "unique_verified_findings": len(unique_verified_findings(results)),
        "confirmation_events": confirmation_events(results),
        "unique_vulnerabilities": len(unique_vulnerabilities(results)),
    }


def enriched_metrics(
    results: list[ProbeResult],
    estimated_regions: int = 16,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Coverage + lifecycle block suitable for merging into compute_metrics."""
    lc = lifecycle_counts(results)
    out = {
        **lc,
        "novel_coverage": novel_coverage(results, estimated_regions=estimated_regions),
        "overall_coverage": overall_coverage(results, estimated_regions=estimated_regions),
        "novel_discovery_efficiency": novel_discovery_efficiency(results),
        "CorpusEscapeRate_definition": (
            "|{confirmed GT ids with in_corpus=False}| / |{confirmed GT ids}|; "
            "0 if no confirmed GT. Separate from confirmation_events."
        ),
    }
    if extra:
        out.update(extra)
    return out
