"""Public rows. Source text stays out of the ledger."""

from __future__ import annotations

from aivd.experiments.aivd40.stage_4_2.observation import BehavioralObservation


def public_row(handle: str, probe_index: int, observation: BehavioralObservation) -> dict[str, object]:
    return {
        "canonical": observation.canonical,
        "handle": handle,
        "probe_index": probe_index,
        "status": observation.status,
    }
