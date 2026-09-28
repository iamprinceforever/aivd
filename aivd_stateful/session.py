"""Execute one model call, persist the raw response, then extend a trajectory."""

import json
from hashlib import sha256
from pathlib import Path

from aivd_stateful.authorize import session_open
from aivd_stateful.hashing import digest
from aivd_stateful.model import BudgetExhausted, _append, plan_turn
from aivd_stateful.transport import build_request


class RecordingFailure(Exception):
    pass


class SessionRefused(Exception):
    pass


class Session:
    def __init__(self, root: Path, transport, budget):
        self.root = Path(root)
        self.transport = transport
        self.budget = budget
        self.calls = 0
        self.texts = {}
        self.records = []
        self.raw = self.root / "raw"
        self.raw.mkdir(parents=True, exist_ok=True)

    def history(self, trajectory) -> list:
        messages = []
        for turn_id, input_hash, output_hash in trajectory.prefix:
            text = self.texts.get(turn_id)
            if text is None:
                raise RecordingFailure("missing inherited turn")
            if digest({"public_input": text["input"]}) != input_hash or digest({"output": text["output"]}) != output_hash:
                raise RecordingFailure("inherited turn hash mismatch")
            messages.append({"role": "user", "content": text["input"]})
            messages.append({"role": "assistant", "content": text["output"]})
        for turn in trajectory.turns:
            messages.append({"role": "user", "content": turn.public_input})
            messages.append({"role": "assistant", "content": turn.output})
        return messages

    def execute(self, trajectory, public_input: str, action: str, reason: str):
        if not session_open():
            raise SessionRefused("execution session is closed")
        if not reason:
            raise SessionRefused("missing reason")
        try:
            self.budget.charge(action)
        except BudgetExhausted:
            raise
        shell, planned = plan_turn(trajectory, public_input, action)
        messages = self.history(shell) + [{"role": "user", "content": public_input}]
        request = build_request(messages)
        raw_request = json.dumps(request, sort_keys=True).encode()
        self.calls += 1
        call_id = f"{self.calls:02d}-{planned['turn_id'][:12]}"
        (self.raw / f"{call_id}.req").write_bytes(raw_request)
        try:
            status, raw = self.transport(request)
        except Exception as exc:
            self._fail(call_id, "transport")
            raise RecordingFailure("transport failed") from exc
        path = self.raw / f"{call_id}.bin"
        path.write_bytes(raw if isinstance(raw, (bytes, bytearray)) else b"")
        if path.read_bytes() != (raw if isinstance(raw, (bytes, bytearray)) else b""):
            self._fail(call_id, "persist")
            raise RecordingFailure("persist mismatch")
        if status != 200 or not raw:
            self._fail(call_id, "status")
            raise RecordingFailure("empty response")
        try:
            content = json.loads(raw)["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("content")
        except Exception as exc:
            self._fail(call_id, "parse")
            raise RecordingFailure("unreadable response") from exc
        updated = _append(shell, public_input, content, action, reason, budget=None)
        if updated.turns[-1].turn_id != planned["turn_id"]:
            raise RecordingFailure("turn identity drifted")
        if updated.turns[-1].state_before_hash != planned["state_before_hash"]:
            raise RecordingFailure("state identity drifted")
        self.texts[updated.turns[-1].turn_id] = {"input": public_input, "output": content}
        record = {
            "call_id": call_id,
            "trajectory_id": planned["trajectory_id"],
            "turn_id": planned["turn_id"],
            "parent_turn_id": planned["parent_turn_id"],
            "state_before_hash": planned["state_before_hash"],
            "state_after_hash": updated.turns[-1].state_after_hash,
            "input_hash": planned["input_hash"],
            "request_hash": sha256(raw_request).hexdigest(),
            "response_hash": sha256(raw).hexdigest(),
            "message_count": len(messages),
            "action": action,
            "reason": reason,
        }
        (self.raw / f"{call_id}.json").write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
        self.records.append(record)
        return updated

    def _fail(self, call_id: str, kind: str) -> None:
        (self.raw / f"{call_id}.fail").write_text(kind, encoding="utf-8")
