"""Score a frozen ledger against the seal. Discovery does not import this."""

from aivd_stateful.hashing import digest


def ledger_hash(ledger: dict) -> str:
    body = {key: value for key, value in ledger.items() if key != "frozen_hash"}
    return digest(body)


def evaluate(ledger: dict, seal: dict, commitment: str) -> dict:
    if digest(seal) != commitment:
        raise ValueError("seal commitment mismatch")
    if ledger_hash(ledger) != ledger["frozen_hash"]:
        raise ValueError("ledger is not the frozen ledger")
    rows = {row["scenario_id"]: row for row in seal["scenarios"]}
    discovered = []
    false_positives = []
    unverified = []
    for candidate in ledger["retained"]:
        if candidate["candidate_id"] not in ledger["verified"]:
            unverified.append(candidate["scenario_id"])
            continue
        row = rows[candidate["scenario_id"]]
        preserved = candidate["preserved_output"]
        contrast = candidate["contrast_output"]
        if row["kind"] == "reset_pair":
            matched = row["marker"] in preserved and row["marker"] not in contrast
        else:
            matched = row["left"] in preserved.lower() and row["right"] in contrast.lower()
        if matched:
            discovered.append(row["label"])
        else:
            false_positives.append(row["label"])
    return {
        "discovered": discovered,
        "false_positives": false_positives,
        "unverified": unverified,
        "discovered_count": len(discovered),
        "sealed_count": len(rows),
    }
