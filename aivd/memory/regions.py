"""Behavioral region records: a finding is a point, not region exhaustion."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


# Dimensions that can remain unexplored after a single finding.
DEFAULT_DIMENSIONS = (
    "delimiter",
    "encoding",
    "rare_token",
    "compositional",
    "sequential",
    "contextual",
    "role",
    "indirect",
)


@dataclass
class RegionRecord:
    """Per-region semantic memory.

    Core invariant: discovering vulnerability A must NOT force priority → 0.
    Residual uncertainty + unexplored dimensions keep the region eligible.
    """

    region_id: str
    namespace: str = "target"  # run | target | global
    known_findings: list[str] = field(default_factory=list)
    trigger_families: list[str] = field(default_factory=list)
    successful_strategies: dict[str, int] = field(default_factory=dict)
    failed_strategies: dict[str, int] = field(default_factory=dict)  # contextual negative memory
    dimensions_coverage: dict[str, float] = field(default_factory=dict)
    residual_uncertainty: float = 1.0
    coverage: float = 0.0
    vulnerability_density: float = 0.0
    open_hypotheses: list[str] = field(default_factory=list)
    confirmation_events: int = 0
    unique_findings: int = 0
    security_relevance_max: float = 0.0
    expected_ig: float = 0.5
    visit_count: int = 0
    saturated: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.dimensions_coverage:
            self.dimensions_coverage = {d: 0.0 for d in DEFAULT_DIMENSIONS}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RegionRecord":
        known = dict(data)
        # tolerate unknown keys
        fields = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        known = {k: v for k, v in known.items() if k in fields}
        rec = cls(**known)
        return rec

    def record_finding(
        self,
        vuln_id: str,
        *,
        trigger_family: str | None = None,
        dimension: str | None = None,
        security_relevance: float = 0.0,
        strategy: str | None = None,
        success: bool = True,
    ) -> None:
        """Register a finding as a *point*; keep residual uncertainty if dims remain."""
        self.confirmation_events += 1
        self.visit_count += 1
        self.security_relevance_max = max(self.security_relevance_max, float(security_relevance))
        if vuln_id and vuln_id not in self.known_findings:
            self.known_findings.append(vuln_id)
            self.unique_findings = len(self.known_findings)
            # Finding increases density signal but does NOT zero uncertainty
            self.vulnerability_density = min(1.0, self.vulnerability_density + 0.15)
            # Slight uncertainty drop from confirming a point; leave residual for other dims
            self.residual_uncertainty = max(0.15, self.residual_uncertainty * 0.85)
            self.expected_ig = max(0.1, self.expected_ig * 0.9)
            if dimension and dimension in self.dimensions_coverage:
                self.dimensions_coverage[dimension] = min(
                    1.0, self.dimensions_coverage[dimension] + 0.5
                )
            # Open hypotheses for remaining dimensions
            unexplored = [
                d for d, c in self.dimensions_coverage.items() if c < 0.4
            ]
            self.open_hypotheses = [f"unexplored:{d}" for d in unexplored[:6]]
        else:
            # Confirmation of known finding: denser evidence, little new IG
            self.residual_uncertainty = max(0.1, self.residual_uncertainty * 0.95)
            self.expected_ig = max(0.05, self.expected_ig * 0.85)

        if trigger_family and trigger_family not in self.trigger_families:
            self.trigger_families.append(trigger_family)
            # New family → bump residual uncertainty slightly (more structure unknown)
            self.residual_uncertainty = min(1.0, self.residual_uncertainty + 0.05)

        if strategy:
            bucket = self.successful_strategies if success else self.failed_strategies
            bucket[strategy] = int(bucket.get(strategy, 0)) + 1

        self.coverage = self._mean_dim_coverage()
        self.saturated = self.is_saturated()

    def record_visit(
        self,
        *,
        dimension: str | None = None,
        strategy: str | None = None,
        success: bool = False,
        security_relevance: float = 0.0,
    ) -> None:
        self.visit_count += 1
        self.security_relevance_max = max(self.security_relevance_max, float(security_relevance))
        if dimension and dimension in self.dimensions_coverage:
            # Exploring a dimension without a hit still covers a bit
            self.dimensions_coverage[dimension] = min(
                1.0, self.dimensions_coverage[dimension] + 0.1
            )
        if strategy:
            bucket = self.successful_strategies if success else self.failed_strategies
            bucket[strategy] = int(bucket.get(strategy, 0)) + 1
        self.coverage = self._mean_dim_coverage()
        # Visits without findings reduce uncertainty slowly
        self.residual_uncertainty = max(0.05, self.residual_uncertainty * 0.98)
        self.saturated = self.is_saturated()

    def _mean_dim_coverage(self) -> float:
        if not self.dimensions_coverage:
            return 0.0
        return float(sum(self.dimensions_coverage.values()) / len(self.dimensions_coverage))

    def unexplored_coverage(self) -> float:
        """1 - mean dimension coverage (higher = more unexplored)."""
        return float(max(0.0, 1.0 - self._mean_dim_coverage()))

    def is_saturated(
        self,
        *,
        coverage_thresh: float = 0.85,
        uncertainty_thresh: float = 0.12,
        ig_thresh: float = 0.12,
    ) -> bool:
        """Saturation only when coverage high AND uncertainty low AND diminishing IG."""
        return (
            self._mean_dim_coverage() >= coverage_thresh
            and self.residual_uncertainty <= uncertainty_thresh
            and self.expected_ig <= ig_thresh
        )

    def strategy_priority_modifier(self, strategy: str) -> float:
        """Contextual negative memory: reduce priority for repeatedly failed strategies.

        Never a permanent blacklist — modifier stays in (0.15, 1.0].
        """
        fails = int(self.failed_strategies.get(strategy, 0))
        wins = int(self.successful_strategies.get(strategy, 0))
        if fails == 0:
            return 1.0
        # Soft decay; wins recover priority
        raw = 1.0 / (1.0 + 0.35 * fails) * (1.0 + 0.2 * wins)
        return float(max(0.15, min(1.0, raw)))

    def is_blacklisted(self, strategy: str) -> bool:
        """Always False — negative memory is contextual, never permanent blacklist."""
        return False


def region_priority(
    record: RegionRecord,
    *,
    security_relevance: Optional[float] = None,
) -> float:
    """Priority for continuing exploration in this region.

    Finding a vuln must NOT set priority to 0; density can increase the signal.
    """
    sec = float(
        security_relevance
        if security_relevance is not None
        else record.security_relevance_max
    )
    sec = max(0.0, min(1.0, sec))
    ru = float(max(0.0, min(1.0, record.residual_uncertainty)))
    unex = float(max(0.0, min(1.0, record.unexplored_coverage())))
    ig = float(max(0.0, min(1.0, record.expected_ig)))
    dens = float(max(0.0, min(1.0, record.vulnerability_density)))

    # Weighted blend — density after a find *raises* interest, not kills it
    priority = (
        0.20 * sec
        + 0.30 * ru
        + 0.25 * unex
        + 0.15 * ig
        + 0.10 * dens
    )
    if record.is_saturated():
        # Soft floor, not hard zero — rare reopen if new hypothesis arrives
        priority = min(priority, 0.08)
    return float(max(0.05, min(1.0, priority)))


# --- v3.3 investigation helpers (store via meta; keep RegionRecord lean) ---

def record_boundary(record: RegionRecord, boundary: dict[str, Any]) -> None:
    """Persist a boundary discovery without saturating the region."""
    bounds = list(record.meta.get("boundaries") or [])
    bounds.append(boundary)
    record.meta["boundaries"] = bounds[-50:]
    # Boundary discovery raises residual uncertainty slightly (structure found → more to map)
    record.residual_uncertainty = min(1.0, record.residual_uncertainty + 0.03)
    record.expected_ig = min(1.0, record.expected_ig + 0.05)
    record.saturated = record.is_saturated()


def record_hypothesis_result(
    record: RegionRecord,
    *,
    hypothesis_id: str,
    claim: str = "",
    success: bool,
    minimal_trigger: str = "",
) -> None:
    """Store successful/failed hypotheses + negative evidence."""
    key = "successful_hypotheses" if success else "failed_hypotheses"
    bucket = list(record.meta.get(key) or [])
    bucket.append({"id": hypothesis_id, "claim": claim, "minimal_trigger": minimal_trigger})
    record.meta[key] = bucket[-40:]
    if not success:
        negs = list(record.meta.get("negative_evidence") or [])
        negs.append(hypothesis_id)
        record.meta["negative_evidence"] = negs[-40:]
        # Useful negative: slight IG bump for clarifying what does not work
        record.expected_ig = min(1.0, record.expected_ig + 0.02)
    else:
        if minimal_trigger:
            mts = list(record.meta.get("minimal_triggers") or [])
            if minimal_trigger not in mts:
                mts.append(minimal_trigger)
            record.meta["minimal_triggers"] = mts[-20:]
    # Never force saturation from a single hypothesis outcome
    record.saturated = record.is_saturated()


def record_unexplored_dims(record: RegionRecord, dims: list[str]) -> None:
    record.meta["unexplored_dims"] = list(dims)
    for d in dims:
        if d not in record.dimensions_coverage:
            record.dimensions_coverage[d] = 0.0
