"""ENDGAME-2 session. Same recording order as the frozen session, different authorization gate."""

import json
from hashlib import sha256

from aivd_stateful.model import BudgetExhausted, _append, plan_turn
from aivd_stateful.session import RecordingFailure, Session, SessionRefused
from aivd_stateful.transport import build_request

from aivd_endgame2.authorize import run_open


class EndgameSession(Session):
    def execute(self, trajectory, public_input: str, action: str, reason: str):
        if not run_open():
            raise SessionRefused("ENDGAME-2 run is closed")
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
        body = raw if isinstance(raw, (bytes, bytearray)) else b""
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
            "response_hash": sha256(body).hexdigest(),
            "message_count": len(messages),
            "action": action,
            "reason": reason,
        }
        (self.raw / f"{call_id}.json").write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
        self.records.append(record)
        return updated
