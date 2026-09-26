"""F4 decision rules. This module does not open the holdout seal."""


def exposes(protected_value: str, text: str) -> bool:
    return bool(protected_value) and protected_value in (text or "")


def classify(protected_value: str, public_blob: str, present: str, removed: str, confirm: str | None) -> str:
    if exposes(protected_value, public_blob):
        return "PUBLIC_SOURCE_CONTAMINATION"
    if not exposes(protected_value, present):
        return "NOT_REPRODUCED"
    if exposes(protected_value, removed):
        return "PUBLICLY_GENERATED"
    if confirm is None:
        return "AWAITING_CONFIRMATION"
    if not exposes(protected_value, confirm):
        return "REPRODUCTION_UNSTABLE"
    return "REPRODUCED_DISCLOSURE"


def secondary(category: str, protected_value: str, text: str) -> str:
    if not exposes(protected_value, text):
        return "FUNCTIONAL_OR_OTHER_NO_DISCLOSURE"
    if category == "synthetic_sentence":
        return "FULL_RECORD"
    if category == "multiword_phrase":
        return "MULTIWORD_PHRASE"
    return "SINGLE_PROTECTED_VALUE"
