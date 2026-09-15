"""AIVD 3.18/3.19 — Global Epistemic Budget Arbitration.

Default epistemic_mode=off → ≈ 3.17. No holdout-specific rules.
ONE global experiment budget of 32. Subsystems propose; the arbiter selects.

3.18: arbiter owns leftover after sequential peel.
3.19: arbiter owns the episode after infra smoke (no sweep/gate lock).
"""
from aivd.epistemic.scheduler import (
    EPISTEMIC_MODES,
    is_epistemic_mode,
    is_authoritative,
    is_shadow_mode,
    epistemic_skips_legacy_tower,
    epistemic_owns_episode,
)
from aivd.epistemic.types import (
    BranchState,
    ExperimentProposal,
    ScoreBreakdown,
    AllocationDecision,
    ExperimentTraceRecord,
)
from aivd.epistemic.scoring import (
    DEFAULT_WEIGHTS,
    score_proposal,
    apply_opportunity_costs,
    greedy_eig_select,
    completion_probability,
)
from aivd.epistemic.accounting import GlobalLedger
from aivd.epistemic.reservation import (
    Reservation,
    ReservationBook,
    earns_protected_floor,
    protected_slots,
)
from aivd.epistemic.branch import Branch, BranchRegistry
from aivd.epistemic.allocation import select_next, legacy_choice
from aivd.epistemic.arbiter import GlobalEpistemicArbiter
from aivd.epistemic.shadow import ShadowLog, compare_choices
from aivd.epistemic.diagnostics import (
    pipeline_experiment_slot_efficiency,
    report,
)
from aivd.epistemic.metrics import summarize_rows
from aivd.epistemic.controller import EpistemicController
from aivd.epistemic.audit import scan_epistemic_source, epistemic_audit_record
from aivd.epistemic.memory import roundtrip, dump_state, load_state

__all__ = [
    "EPISTEMIC_MODES",
    "is_epistemic_mode",
    "is_authoritative",
    "is_shadow_mode",
    "epistemic_skips_legacy_tower",
    "epistemic_owns_episode",
    "BranchState",
    "ExperimentProposal",
    "ScoreBreakdown",
    "AllocationDecision",
    "ExperimentTraceRecord",
    "DEFAULT_WEIGHTS",
    "score_proposal",
    "apply_opportunity_costs",
    "greedy_eig_select",
    "completion_probability",
    "GlobalLedger",
    "Reservation",
    "ReservationBook",
    "earns_protected_floor",
    "protected_slots",
    "Branch",
    "BranchRegistry",
    "select_next",
    "legacy_choice",
    "GlobalEpistemicArbiter",
    "ShadowLog",
    "compare_choices",
    "pipeline_experiment_slot_efficiency",
    "report",
    "summarize_rows",
    "EpistemicController",
    "scan_epistemic_source",
    "epistemic_audit_record",
    "roundtrip",
    "dump_state",
    "load_state",
]
