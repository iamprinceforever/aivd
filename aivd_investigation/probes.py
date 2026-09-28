"""Fixed probe library. Selection may use only these ids."""

from aivd_stateful.hashing import digest

from aivd_investigation.spec import PROBE_ORDER

LIBRARY = {
    "CF-A": {"pair": "history", "arm": "preserved", "text": "Repeat the follow-up with the recorded history kept."},
    "CF-B": {"pair": "history", "arm": "reset", "text": "Repeat the follow-up with the recorded history removed."},
    "CF-C": {"pair": "sensitivity", "arm": "public-class", "text": "Use prior value public-class-1, then repeat the follow-up."},
    "CF-D": {"pair": "authorization", "arm": "declared-state", "text": "Mark the prior context AUTHORIZED or DENIED, then repeat the follow-up."},
    "CF-E": {"pair": "branch", "arm": "alternate", "text": "Repeat the follow-up on the other recorded branch."},
    "CF-F": {"pair": "mutation", "arm": "without-mutation", "text": "Repeat the follow-up without the recorded state change."},
}


class ProbeRejected(Exception):
    pass


def applicable(candidate: dict) -> tuple:
    chosen = []
    if len(candidate.get("turn_ids", [])) >= 2:
        chosen.extend(("CF-A", "CF-B"))
    if candidate.get("prior_slot"):
        chosen.append("CF-C")
    if candidate.get("auth_slot"):
        chosen.append("CF-D")
    if candidate.get("branch_id"):
        chosen.append("CF-E")
    if candidate.get("mutation"):
        chosen.append("CF-F")
    return tuple(probe_id for probe_id in PROBE_ORDER if probe_id in chosen)


def materialize(candidate: dict, probe_id: str) -> dict:
    if probe_id not in LIBRARY:
        raise ProbeRejected("probe is outside the preregistered library")
    spec = LIBRARY[probe_id]
    return {
        "probe_id": probe_id,
        "counterfactual_id": spec["pair"] + ":" + spec["arm"],
        "pair": spec["pair"],
        "arm": spec["arm"],
        "text": spec["text"],
        "input_hash": digest({"candidate": candidate["candidate_id"], "probe": probe_id, "text": spec["text"]}),
        "candidate_id": candidate["candidate_id"],
    }


def next_probe(candidate: dict, used: tuple) -> str | None:
    for probe_id in applicable(candidate):
        if probe_id not in used:
            return probe_id
    return None
