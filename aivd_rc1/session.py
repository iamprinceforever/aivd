"""RC1 recording session. Reuses the frozen trajectory primitives; gate is AIVD-RC1.

Every model call is recorded with request/response hashes, turn identity, and full
provenance (candidate -> trajectory -> turn -> probe -> evidence). A recording failure
raises RecordingFailure, which the driver treats as an integrity failure.
"""

import json
from hashlib import sha256

from aivd_stateful.model import BudgetExhausted, _append, plan_turn
from aivd_stateful.session import RecordingFailure, Session, SessionRefused
from aivd_stateful.transport import build_request

from aivd_rc1.authorize import run_open


class RC1Session(Session):
    def __init__(self, root, transport, budget):
        super().__init__(root, transport, budget)
        self.trajectories = {}

    def execute(self, trajectory, public_input: str, action: str, reason: str):
        if not run_open():
            raise SessionRefused("AIVD-RC1 run is closed")
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
        call_id = f"{self.calls:03d}-{planned['turn_id'][:12]}"
        (self.raw / f"{call_id}.req").write_bytes(raw_request)
        try:
            status, raw = self.transport(request)
        except Exception as exc:
            self._fail(call_id, "transport")
            raise RecordingFailure("transport failed") from exc
        body = raw if isinstance(raw, (bytes, bytearray)) else b""
        path = self.raw / f"{call_id}.bin"
        path.write_bytes(body)
        if path.read_bytes() != body or status != 200 or not body:
            self._fail(call_id, "persist")
            raise RecordingFailure("response was not persisted")
        try:
            content = json.loads(body)["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("content")
        except Exception as exc:
            self._fail(call_id, "parse")
            raise RecordingFailure("unreadable response") from exc
        updated = _append(shell, public_input, content, action, reason, budget=None)
        if updated.turns[-1].turn_id != planned["turn_id"] or updated.turns[-1].state_before_hash != planned["state_before_hash"]:
            raise RecordingFailure("turn identity drifted")
        self.texts[updated.turns[-1].turn_id] = {"input": public_input, "output": content}
        self.trajectories[updated.trajectory_id] = updated
        record = {
            "call_id": call_id,
            "trajectory_id": planned["trajectory_id"],
            "turn_id": planned["turn_id"],
            "parent_turn_id": planned["parent_turn_id"],
            "state_before_hash": planned["state_before_hash"],
            "state_after_hash": updated.turns[-1].state_after_hash,
            "input_hash": planned["input_hash"],
            "request_hash": sha256(raw_request).hexdigest(),
            "response_hash": sha256(body).hexdigest(),
            "message_count": len(messages),
            "action": action,
            "reason": reason,
        }
        (self.raw / f"{call_id}.json").write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
        self.records.append(record)
        return updated
