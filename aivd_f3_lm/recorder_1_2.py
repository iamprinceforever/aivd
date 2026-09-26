"""F3-LM-1.2 response recorder. Never calls a model."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

EXPERIMENT_ID = "F3-LM-1.2"
F3_LM_EXECUTION_AUTHORIZED = False


class ExecutionRefused(Exception):
    pass


class DuplicateTrial(Exception):
    code = "RECOVERY_REQUIRED"


class PersistenceFailure(Exception):
    pass


def attempt_model_execution() -> None:
    if not F3_LM_EXECUTION_AUTHORIZED:
        raise ExecutionRefused("F3_LM_EXECUTION_AUTHORIZED is false")


def new_experiment_state() -> dict:
    return {
        "experiment_id": EXPERIMENT_ID,
        "trial_count": 0,
        "discovery_memory": [],
        "behavioral_memory": [],
        "security_hypotheses": [],
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _field(present: bool, value, optional: bool = True) -> dict:
    if not present:
        return {"status": "MISSING_OPTIONAL" if optional else "INVALID", "value": None}
    if optional is False and value is None:
        return {"status": "INVALID", "value": None}
    return {"status": "PRESENT", "value": value}


class Recorder:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.raw_dir = self.root / "raw"
        self.norm_dir = self.root / "normalized"
        self.exec_dir = self.root / "executed"
        self.model_calls = 0

    def executed_path(self, trial_id: str) -> Path:
        return self.exec_dir / f"{trial_id}.json"

    def raw_path(self, trial_id: str) -> Path:
        return self.raw_dir / f"{trial_id}.json"

    def is_executed(self, trial_id: str) -> bool:
        return self.executed_path(trial_id).exists()

    def mark_executed(self, trial_id: str, request_hash: str, sequence: int) -> None:
        if self.is_executed(trial_id):
            raise DuplicateTrial("RECOVERY_REQUIRED")
        marker = {
            "experiment_id": EXPERIMENT_ID,
            "trial_id": trial_id,
            "request_hash": request_hash,
            "request_sequence": sequence,
            "state": "EXECUTED",
        }
        atomic_write(self.executed_path(trial_id), json.dumps(marker).encode())

    def submit(self, trial_id: str, request_hash: str, sequence: int, call):
        self.mark_executed(trial_id, request_hash, sequence)
        self.model_calls += 1
        return call()

    def capture(self, trial_id: str, http_status: int, raw: bytes, meta: dict) -> dict:
        record = {
            "request_id": meta["request_id"],
            "http_status": http_status,
            "raw_text": raw.decode("utf-8"),
            "response_sha256": _sha256(raw),
            "receipt_timestamp": datetime.now(timezone.utc).isoformat(),
            "model_digest": meta["model_digest"],
            "runtime_manifest_hash": meta["runtime_manifest_hash"],
            "experiment_authorization_hash": meta["experiment_authorization_hash"],
        }
        try:
            atomic_write(self.raw_path(trial_id), json.dumps(record).encode())
        except OSError as exc:
            raise PersistenceFailure("raw response was not stored") from exc
        stored = self.raw_path(trial_id).read_bytes()
        if json.loads(stored)["response_sha256"] != record["response_sha256"]:
            raise PersistenceFailure("raw hash mismatch after write")
        return record

    def normalize(self, record: dict) -> dict:
        raw = record["raw_text"].encode("utf-8")
        if _sha256(raw) != record["response_sha256"]:
            raise PersistenceFailure("raw hash mismatch before parse")
        observation = {
            "http_status": _field(True, record["http_status"], optional=False),
            "raw_response_hash": _field(True, record["response_sha256"], optional=False),
            "response_text": _field(False, None),
            "thinking_text": _field(False, None),
            "done": _field(False, None),
            "done_reason": _field(False, None),
            "token_count": _field(False, None),
            "template_id": _field(False, None),
            "template_id_status": "MISSING_OPTIONAL",
            "model_metadata": _field(False, None),
            "parse_status": "OK",
        }
        if record["http_status"] != 200:
            observation["response_text"] = {"status": "NOT_APPLICABLE", "value": None}
            observation["parse_status"] = "HTTP_ERROR"
            return observation
        try:
            payload = json.loads(record["raw_text"])
        except json.JSONDecodeError:
            observation["parse_status"] = "RAW_RESPONSE_PERSISTED_PARSE_FAILURE"
            return observation
        if not isinstance(payload, dict):
            observation["parse_status"] = "RAW_RESPONSE_PERSISTED_PARSE_FAILURE"
            return observation
        message = payload.get("message") if isinstance(payload.get("message"), dict) else {}
        if "content" in message:
            observation["response_text"] = _field(True, message.get("content"))
        if "thinking" in message:
            observation["thinking_text"] = _field(True, message.get("thinking"))
        elif "thinking" in payload:
            observation["thinking_text"] = _field(True, payload.get("thinking"))
        if "done" in payload:
            observation["done"] = _field(True, payload.get("done"))
        if "done_reason" in payload:
            observation["done_reason"] = _field(True, payload.get("done_reason"))
        if "eval_count" in payload:
            observation["token_count"] = _field(True, payload.get("eval_count"))
        if "template_id" in payload:
            value = payload.get("template_id")
            if isinstance(value, str) and value:
                observation["template_id"] = _field(True, value)
                observation["template_id_status"] = "PRESENT"
            else:
                observation["template_id"] = {"status": "INVALID", "value": None}
                observation["template_id_status"] = "INVALID"
        extra = {key: payload[key] for key in payload if key not in {"message", "done", "done_reason", "eval_count", "template_id"}}
        if extra:
            observation["model_metadata"] = _field(True, extra)
        observation["behavioral_signature"] = hashlib.sha256(
            (observation["response_text"]["value"] or "").encode("utf-8")
        ).hexdigest()
        return observation

    def process(self, trial_id: str, http_status: int, raw: bytes, meta: dict, parser=None) -> dict:
        record = self.capture(trial_id, http_status, raw, meta)
        try:
            if parser is not None:
                parser(record)
            observation = self.normalize(record)
        except Exception as exc:
            observation = {
                "parse_status": "RAW_RESPONSE_PERSISTED_PARSE_FAILURE",
                "error_type": type(exc).__name__,
                "raw_response_hash": _field(True, record["response_sha256"], optional=False),
                "template_id_status": "MISSING_OPTIONAL",
            }
        atomic_write(self.norm_dir / f"{trial_id}.json", json.dumps(observation).encode())
        return observation

    def recover(self) -> list:
        recovered = []
        if not self.raw_dir.exists():
            return recovered
        for path in sorted(self.raw_dir.glob("*.json")):
            if (self.norm_dir / path.name).exists():
                continue
            record = json.loads(path.read_text(encoding="utf-8"))
            observation = self.normalize(record)
            atomic_write(self.norm_dir / path.name, json.dumps(observation).encode())
            recovered.append(observation)
        return recovered


def regression_fixture() -> bytes:
    return json.dumps(
        {
            "model": "fixture",
            "message": {"role": "assistant", "content": "SYNTHETIC_FIXTURE_TEXT"},
            "done": True,
            "done_reason": "stop",
            "eval_count": 17,
        }
    ).encode()
