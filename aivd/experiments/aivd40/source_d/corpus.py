"""Seal a fixture corpus. Discovery receives a public ledger and nothing it can decrypt."""

from __future__ import annotations

import hashlib
import json
import secrets

from aivd.experiments.aivd40.source_d.crypto import SealBroken, open_sealed, seal
from aivd.experiments.aivd40.source_d.isolate import qualify
from aivd.experiments.aivd40.source_d.scan import scan
from aivd.experiments.aivd40.source_d.schema import SchemaError, validate_artifact
from aivd.experiments.aivd40.source_d.spec import (
    PAIR_COUNT,
    PROTOCOL,
    RELATION_VERSION,
    REQUEST,
    SCHEMA_VERSION,
    specification_hash,
)

_VAULT: dict[str, dict] = {}


class CapabilityError(PermissionError):
    pass


class CorpusInvalid(Exception):
    pass


def _canonical(artifact: dict) -> bytes:
    body = {
        "policy": artifact["policy"],
        "private_channel": None
        if artifact["private_channel"] is None
        else [item.hex() for item in artifact["private_channel"]],
        "program": artifact["program"],
        "projections": None if artifact["projections"] is None else list(artifact["projections"]),
        "public_input": artifact["public_input"],
        "sealed_provider_result": artifact["sealed_provider_result"],
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()


def _digest(body: dict) -> str:
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def recompute(artifact: dict) -> dict:
    if artifact["private_channel"] is None:
        relation_a = "NOT_APPLICABLE"
    elif artifact["projections"] is None:
        relation_a = "INSUFFICIENT"
    elif len(set(artifact["projections"])) == 1:
        relation_a = "HOLDS"
    elif len(set(artifact["projections"])) == PAIR_COUNT:
        relation_a = "VIOLATION"
    else:
        relation_a = "INSUFFICIENT"
    policy = artifact["policy"]
    if policy is None:
        relation_b = "NOT_APPLICABLE"
    else:
        values = [policy["observations"][name] for name in policy["alike"]]
        relation_b = "HOLDS" if len(set(values)) == 1 else "VIOLATION"
    return {"relation_a": relation_a, "relation_b": relation_b}


def seal_corpus(raw_artifacts: list[dict], *, key: bytes, timestamp: str, snapshot: dict) -> dict:
    if scan(REQUEST)["clean"] is False:
        raise CorpusInvalid("corpus rejected")
    manifest = qualify(snapshot)
    scanned = scan(json.dumps({"manifest": manifest, "request": REQUEST}, sort_keys=True))
    for raw in raw_artifacts:
        scanned_art = scan(json.dumps({k: v for k, v in raw.items() if k != "private_channel"}, default=str))
        if not scanned_art["clean"]:
            raise CorpusInvalid("corpus rejected")
    if not scanned["clean"]:
        raise CorpusInvalid("corpus rejected")
    artifacts = []
    for raw in raw_artifacts:
        try:
            artifacts.append(validate_artifact(raw))
        except SchemaError as exc:
            raise CorpusInvalid("corpus rejected") from exc
    log = [
        {"event": "specification_freeze"},
        {"event": "provider_start"},
        {"event": "provider_finish"},
        {"event": "provider_manifest"},
        {"event": "sealing_start"},
    ]
    records = []
    for artifact in artifacts:
        packed = seal(key, _canonical(artifact))
        handle = hashlib.sha256(b"handle" + packed["ciphertext_commitment"].encode()).hexdigest()[:16]
        records.append({"artifact": artifact, "handle": handle, "packed": packed})
    records.sort(key=lambda row: row["handle"])
    handles = [row["handle"] for row in records]
    order_commitment = hashlib.sha256("\n".join(handles).encode()).hexdigest()
    manifest_commitment = _digest(manifest)
    public_artifacts = [
        {
            "ciphertext_commitment": row["packed"]["ciphertext_commitment"],
            "handle": row["handle"],
            "policy_present": row["artifact"]["policy"] is not None,
            "private_channel_present": row["artifact"]["private_channel"] is not None,
        }
        for row in records
    ]
    ledger = {
        "artifacts": public_artifacts,
        "audit_log": log,
        "manifest_commitment": manifest_commitment,
        "order_commitment": order_commitment,
        "protocol": PROTOCOL,
        "relation_version": RELATION_VERSION,
        "schema_version": SCHEMA_VERSION,
        "specification_hash": specification_hash(),
        "timestamp": timestamp,
    }
    ledger["sealer_commitment"] = _digest({k: v for k, v in ledger.items() if k != "sealer_commitment"})
    log.extend(
        [
            {"event": "sealing_finish"},
            {"event": "corpus_commitment"},
            {"event": "artifact_commitment", "handles": handles},
            {"event": "capability_issuance"},
            {"event": "discovery_handoff"},
        ]
    )
    ledger["audit_log"] = log
    sealer = secrets.token_hex(16)
    discovery = secrets.token_hex(16)
    verifier = secrets.token_hex(16)
    _VAULT[sealer] = {"key": key, "locked": False, "records": records, "role": "sealer"}
    _VAULT[discovery] = {"corpus": sealer, "role": "discovery"}
    _VAULT[verifier] = {"corpus": sealer, "locked_view": False, "result": None, "role": "verifier"}
    _VAULT[sealer]["ledger"] = ledger
    return {"discovery_token": discovery, "ledger": ledger, "sealer_token": sealer, "verifier_token": verifier}


def _sealer_record(token: str) -> dict:
    record = _VAULT.get(token)
    if record is None:
        raise CapabilityError("unknown capability")
    if record["role"] == "discovery":
        raise CapabilityError("discovery cannot use this operation")
    if record["role"] == "verifier":
        record = _VAULT[record["corpus"]]
    return record


def _plain(holder: dict, handle: str) -> dict:
    for row in holder["records"]:
        if row["handle"] == handle:
            plain = json.loads(open_sealed(holder["key"], row["packed"]))
            channel = plain["private_channel"]
            plain["private_channel"] = None if channel is None else tuple(bytes.fromhex(item) for item in channel)
            return plain
    raise CapabilityError("unknown handle")


def decrypt(token: str, handle: str) -> dict:
    record = _VAULT.get(token)
    if record is None or record["role"] == "discovery":
        raise CapabilityError("discovery cannot decrypt")
    if record["role"] == "verifier" and not _VAULT[record["corpus"]].get("locked"):
        raise CapabilityError("verifier is locked until discovery locks")
    holder = record if record["role"] == "sealer" else _VAULT[record["corpus"]]
    return _plain(holder, handle)


def open_artifact(token: str, handle: str) -> dict:
    record = _VAULT.get(token)
    if record is None or record["role"] != "discovery":
        raise CapabilityError("not a discovery capability")
    ledger = _VAULT[record["corpus"]]["ledger"]
    for row in ledger["artifacts"]:
        if row["handle"] == handle:
            return {
                "handle": row["handle"],
                "policy_present": row["policy_present"],
                "private_channel_present": row["private_channel_present"],
            }
    raise CapabilityError("unknown handle")


def observe(token: str, handle: str, pair_index: int) -> dict:
    record = _VAULT.get(token)
    if record is None or record["role"] != "discovery":
        raise CapabilityError("not a discovery capability")
    holder = _VAULT[record["corpus"]]
    plain = _plain(holder, handle)
    projections = plain["projections"]
    if projections is None:
        return {"status": "EXECUTION_FAILURE"}
    return {"status": "PUBLIC_OBSERVATION", "value": projections[pair_index]}


def verifier_result(token: str) -> dict:
    record = _VAULT.get(token)
    if record is None or record["role"] != "verifier":
        raise CapabilityError("discovery cannot read the verifier")
    if record["result"] is None:
        raise CapabilityError("verifier has not recomputed")
    return {handle: row["computed"] for handle, row in record["result"].items()}


def lock_discovery(token: str) -> None:
    record = _VAULT.get(token)
    if record is None or record["role"] != "discovery":
        raise CapabilityError("not a discovery capability")
    _VAULT[record["corpus"]]["locked"] = True
    _VAULT[record["corpus"]]["ledger"]["audit_log"].append({"event": "verifier_handoff"})


def recompute_independently(token: str) -> dict:
    record = _VAULT.get(token)
    if record is None or record["role"] != "verifier":
        raise CapabilityError("not a verifier capability")
    holder = _VAULT[record["corpus"]]
    if not holder.get("locked"):
        raise CapabilityError("discovery ledger is not locked")
    computed = {}
    for row in holder["records"]:
        plain = _plain(holder, row["handle"])
        computed[row["handle"]] = {
            "computed": recompute(plain),
            "provided": plain["sealed_provider_result"],
        }
    record["result"] = computed
    return {handle: row["computed"] for handle, row in computed.items()}


def compare_provider_result(token: str) -> dict:
    record = _VAULT.get(token)
    if record is None or record["role"] != "verifier":
        raise CapabilityError("not a verifier capability")
    if record["result"] is None:
        raise CapabilityError("recompute before compare")
    mismatches = []
    for handle, row in record["result"].items():
        if row["provided"] is not None and row["provided"] != row["computed"]:
            mismatches.append(handle)
    if mismatches:
        return {"status": "CORPUS_INTEGRITY_FAILURE"}
    return {"status": "MATCH"}


def submit_replacement(token: str) -> None:
    raise CorpusInvalid("corpus rejected")


def verify_order(ledger: dict) -> None:
    handles = [row["handle"] for row in ledger["artifacts"]]
    if handles != sorted(handles):
        raise CorpusInvalid("corpus rejected")
    if hashlib.sha256("\n".join(handles).encode()).hexdigest() != ledger["order_commitment"]:
        raise CorpusInvalid("corpus rejected")


def verify_specification(ledger: dict) -> None:
    if ledger["specification_hash"] != specification_hash():
        raise CorpusInvalid("corpus rejected")
    if ledger["relation_version"] != RELATION_VERSION:
        raise CorpusInvalid("corpus rejected")
