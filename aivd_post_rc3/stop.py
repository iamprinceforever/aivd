"""STOP-condition checks for the POST-RC3 Groq evaluation.

Any trigger halts the whole evaluation. POST-RC3 / NOT PART OF RC3 RELEASE.
"""

from pathlib import Path

from aivd_post_rc3.key_scan import GSK_PATTERN, scan_for_gsk
from aivd_post_rc3.models import MODELS
from aivd_post_rc3.rc3_freeze_blobs import RC3_FREEZE_BLOBS, RC3_FREEZE_COMMIT


class StopCondition(RuntimeError):
    """Raised to halt the entire evaluation."""


def halt(reason: str) -> None:
    raise StopCondition(reason)


def check_rc3_source_unmodified() -> None:
    import hashlib
    for path, expected in RC3_FREEZE_BLOBS.items():
        p = Path(path)
        if not p.is_file():
            halt(f"RC3_SOURCE_MODIFICATION: missing {path}")
        data = p.read_bytes()
        sha = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        if sha != expected:
            halt(f"RC3_SOURCE_MODIFICATION: {path} differs from {RC3_FREEZE_COMMIT}")


def check_no_api_key_leakage(paths=None) -> None:
    hits = scan_for_gsk(paths)
    if hits:
        halt(f"API_KEY_LEAKAGE: gsk_ pattern in {hits[0]}")


def check_model_match(requested: str, response_model: str) -> None:
    if requested not in MODELS:
        halt(f"UNEXPECTED_MODEL_SUBSTITUTION: requested {requested!r} is not in the preregistered set")
    # Groq may return the id as-is; reject any mismatch.
    if response_model != requested:
        halt(f"UNEXPECTED_MODEL_SUBSTITUTION: requested={requested!r} response.model={response_model!r}")


def check_corpus_commitment(ledger_commitment: str, expected: str) -> None:
    if ledger_commitment != expected:
        halt(f"CORPUS_MISMATCH: ledger={ledger_commitment[:16]}… expected={expected[:16]}…")


def check_candidate_ids_unique(candidates: list) -> None:
    ids = [c.get("candidate_id") for c in candidates]
    if len(ids) != len(set(ids)):
        halt("CANDIDATE_ID_COLLISION")


def check_no_target_leakage(public_text: str, tokens: list, notes: list) -> None:
    for t in tokens:
        if t and t in public_text:
            halt("TARGET_LEAKAGE: sealed token in public artifact")
    for n in notes:
        if n and n in public_text:
            halt("TARGET_LEAKAGE: sealed note in public artifact")


def check_no_verifier_leakage(public_obj: dict) -> None:
    forbidden = {"token", "note", "relation", "protected_value", "label", "target_label",
                 "verifier_state", "security_score", "similarity", "hidden_label"}
    def walk(obj, path="$"):
        if isinstance(obj, dict):
            bad = forbidden & set(obj)
            if bad:
                halt(f"VERIFIER_LEAKAGE: keys {sorted(bad)} at {path}")
            for k, v in obj.items():
                walk(v, path + "." + str(k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}]")
    walk(public_obj)


def check_ledger_integrity(ledger: dict) -> None:
    from aivd_rc3.verifier import ledger_hash
    if ledger.get("frozen_hash") != ledger_hash(ledger):
        halt("LEDGER_CORRUPTION: frozen_hash mismatch")
    if ledger.get("integrity_failures"):
        halt(f"LEDGER_CORRUPTION: integrity_failures={ledger['integrity_failures']}")


def check_authorization(token: dict, expected_kind: str) -> None:
    if token.get("kind") != expected_kind:
        halt("AUTHORIZATION_FAILURE: token kind mismatch")
