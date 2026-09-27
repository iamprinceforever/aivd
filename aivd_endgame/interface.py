"""Discovery-facing interface. It does not return prompts or seal fields."""

import hashlib
import json
from pathlib import Path

from aivd_endgame.authorize import capability_ok
from aivd_endgame.harness import BudgetExceeded, RecordingFailure, planned_requests
from aivd_endgame.provider import read_public
from aivd_endgame.spec import MAX_MODEL_CALLS


class InterfaceError(Exception):
    pass


class BlindInterface:
    def __init__(self, root: Path, transport, authorization, evidence: Path):
        self.root = root
        self.transport = transport
        self.authorization = authorization
        self.evidence = evidence
        self.calls = 0
        self.failures = []
        self.evidence.mkdir(parents=True, exist_ok=True)

    def list_scenarios(self) -> list:
        view = read_public(self.root)
        return [{"scenario_id": item["scenario_id"], "public_label": item["public_label"]} for item in view["scenarios"]]

    def complete(self, scenario_id: str, arm: str) -> dict:
        if not capability_ok(self.authorization):
            raise InterfaceError("execution is not authorized")
        if arm not in {"H", "P"}:
            raise InterfaceError("unknown arm")
        requests = planned_requests(self.root, scenario_id, arm)
        texts = []
        hashes = []
        for request in requests:
            if self.calls >= MAX_MODEL_CALLS:
                raise BudgetExceeded("model-call ceiling reached")
            self.calls += 1
            call_id = f"{self.calls:02d}-{scenario_id}-{arm}"
            raw_path = self.evidence / f"{call_id}.bin"
            body = json.dumps(request).encode()
            try:
                status, raw = self.transport(body)
            except Exception as exc:
                self.failures.append(call_id)
                raise RecordingFailure("transport failed") from exc
            if status != 200 or not raw:
                self.failures.append(call_id)
                raise RecordingFailure("empty response")
            raw_path.write_bytes(raw)
            if raw_path.read_bytes() != raw:
                self.failures.append(call_id)
                raise RecordingFailure("persist mismatch")
            try:
                payload = json.loads(raw)
                content = (payload.get("message") or {}).get("content")
                if not isinstance(content, str):
                    raise ValueError("missing content")
            except Exception as exc:
                self.failures.append(call_id)
                raise RecordingFailure("unreadable response") from exc
            texts.append(content)
            hashes.append(hashlib.sha256(raw).hexdigest())
        return {
            "scenario_id": scenario_id,
            "arm": arm,
            "text": texts[-1],
            "output_hash": hashes[-1],
            "request_hash": hashlib.sha256(body).hexdigest(),
            "model_calls": len(requests),
        }
