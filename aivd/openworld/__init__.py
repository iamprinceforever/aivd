"""AIVD 3.17 — Open-World Behavioral Representation & Generative Experimentation.

Default openworld_mode=off → ≈ 3.16. No holdout-specific rules.
"""
from aivd.openworld.scheduler import (
    OPENWORLD_MODES,
    is_openworld_mode,
    openworld_skips_legacy_invent,
    openworld_skips_duplicate_tower,
)
from aivd.openworld.primitives import Primitive, harvest_primitives, harvest_tokens
from aivd.openworld.features import BehavioralFeatures, extract_features
from aivd.openworld.representation import (
    OpenWorldRepresentation,
    representation_from_primitives,
    can_represent,
)
from aivd.openworld.relations import RelationKind, all_relation_kinds
from aivd.openworld.grammar import GrammarExpr, expressions_from_representation
from aivd.openworld.generator import generate_from_representation, info_acquisition_from_rep
from aivd.openworld.experiment import ExperimentRecord, predict_experiment
from aivd.openworld.budget import (
    OpenWorldBudget,
    protected_floor,
    invent_without_execute_guard,
    pipeline_reserve_plan,
)
from aivd.openworld.diagnostics import diagnose_openworld, success_levels, OpenWorldCode
from aivd.openworld.memory import OpenWorldMemory
from aivd.openworld.metrics import (
    open_world_discovery_rate,
    representation_to_experiment_success,
    experiment_starvation_rate,
    discovery_causality_gap,
    summarize_rows,
)
from aivd.openworld.expressiveness import (
    legacy_can_express,
    openworld_can_express,
    expressiveness_table,
)
from aivd.openworld.controller import OpenWorldController
from aivd.openworld.audit import scan_openworld_source, openworld_audit_record
from aivd.openworld.health import health_check

__all__ = [
    "OPENWORLD_MODES",
    "is_openworld_mode",
    "openworld_skips_legacy_invent",
    "openworld_skips_duplicate_tower",
    "Primitive",
    "harvest_primitives",
    "harvest_tokens",
    "BehavioralFeatures",
    "extract_features",
    "OpenWorldRepresentation",
    "representation_from_primitives",
    "can_represent",
    "RelationKind",
    "all_relation_kinds",
    "GrammarExpr",
    "expressions_from_representation",
    "generate_from_representation",
    "info_acquisition_from_rep",
    "ExperimentRecord",
    "predict_experiment",
    "OpenWorldBudget",
    "protected_floor",
    "invent_without_execute_guard",
    "pipeline_reserve_plan",
    "diagnose_openworld",
    "success_levels",
    "OpenWorldCode",
    "OpenWorldMemory",
    "open_world_discovery_rate",
    "representation_to_experiment_success",
    "experiment_starvation_rate",
    "discovery_causality_gap",
    "summarize_rows",
    "legacy_can_express",
    "openworld_can_express",
    "expressiveness_table",
    "OpenWorldController",
    "scan_openworld_source",
    "openworld_audit_record",
    "health_check",
]
