"""Recording session that keeps every attempt on the stage that issued it.

Does not change discovery, investigation, or verification policy. A failed attempt
is never counted as a successful model call.
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from aivd_stateful.model import BudgetExhausted, _append, plan_turn
from aivd_stateful.session import RecordingFailure, SessionRefused

from aivd_post_rc3.authorize import run_open
from aivd_post_rc3.groq_client import build_chat_request
from aivd_post_rc3_v2.accounting import RECORDING_FAILURE_STATUSES


def _usage_from_openai(body: bytes) -> dict:
    try:
        parsed = json.loads(body)
        usage = parsed.get("usage") or {}
        return {k: usage.get(k) for k in ("prompt_tokens", "completion_tokens", "total_tokens") if k in usage}
    except Exception:
        return {}


class V2Session:
    """Same execute interface as PostRC3Session, with explicit stage accounting."""

    def __init__(self, root, transport, budget, *, model_id: str):
        self.root = Path(root)
        self.raw = self.root / "raw"
        self.raw.mkdir(parents=True, exist_ok=True)
        self.transport = transport
        self.budget = budget
        self.model_id = model_id
        self.calls = 0
        self.attempt_charges = 0
        self.records = []
        self.attempts = []
        self.trajectories = {}
        self.texts = {}
        self.stage = None
        self._logical = 0
        self._attempt_n = 0
        self.last_failure = None

    def set_stage(self, stage: str) -> None:
        self.stage = stage

    def history(self, trajectory) -> list:
        from aivd_stateful.hashing import digest
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

    def _budget_state(self) -> dict:
        return {
            "limit": self.budget.limit,
            "turn_executions": self.budget.turn_executions,
            "remaining": self.budget.limit - self.budget.turn_executions,
            "stage": self.stage,
        }

    def _new_attempt(self, *, logical_id, original_id, index, request_hash, response_hash, planned, action, reason, consumed, status):
        self._attempt_n += 1
        attempt_id = f"a-{self._attempt_n:04d}"
        if index == 0:
            original_id = attempt_id
        record = {
            "attempt_id": attempt_id,
            "stage": self.stage,
            "logical_call_id": logical_id,
            "call_id": None,
            "retry_of": None if index == 0 else original_id,
            "success": False,
            "recording_status": status,
            "request_hash": request_hash,
            "response_hash": response_hash,
            "trajectory_id": planned["trajectory_id"],
            "turn_id": planned["turn_id"],
            "action": action,
            "reason": reason,
            "budget_consumed": consumed,
            "budget_remaining": self.budget.limit - self.budget.turn_executions,
            "api_attempt_index": index + 1,
        }
        self.attempts.append(record)
        self.attempt_charges += 1
        return attempt_id, record

    def _remember_failure(self, record, stop_reason: str) -> None:
        logical = [item for item in self.attempts if item["logical_call_id"] == record["logical_call_id"]]
        self.last_failure = {
            "FAILURE_STAGE": self.stage,
            "trajectory_id": record["trajectory_id"],
            "attempt_id": record["attempt_id"],
            "logical_call_id": record["logical_call_id"],
            "request_hash": record["request_hash"],
            "response_hash": record["response_hash"],
            "retry_count": sum(1 for item in logical if item["retry_of"]),
            "budget_state": self._budget_state(),
            "reason": stop_reason,
            "recording_status": record["recording_status"],
        }

    def execute(self, trajectory, public_input: str, action: str, reason: str):
        if not run_open():
            raise SessionRefused("POST-RC3 run is closed")
        if not reason:
            raise SessionRefused("missing reason")
        if self.stage is None:
            raise RecordingFailure("stage was not set")
        try:
            self.budget.charge(action)
        except BudgetExhausted:
            raise
        shell, planned = plan_turn(trajectory, public_input, action)
        messages = self.history(shell) + [{"role": "user", "content": public_input}]
        request = build_chat_request(self.model_id, messages)
        raw_request = json.dumps(request, sort_keys=True).encode()
        request_hash = sha256(raw_request).hexdigest()
        self._logical += 1
        logical_id = f"c-{self._logical:04d}"
        (self.raw / f"{logical_id}.req").write_bytes(raw_request)
        transport_error = None
        try:
            status, raw = self.transport(request)
        except Exception as exc:
            status, raw, transport_error = None, b"", exc
        body = raw if isinstance(raw, (bytes, bytearray)) else b""
        response_hash = sha256(body).hexdigest() if body else None
        attempts_n = max(1, int(getattr(self.transport, "last_attempts", 1) or 1))
        original_id = None
        final = None
        for index in range(attempts_n):
            consumed = 1
            if index:
                try:
                    self.budget.charge("retry")
                except BudgetExhausted as exc:
                    for item in self.attempts:
                        if item["logical_call_id"] == logical_id and item["recording_status"] == "pending":
                            item["recording_status"] = "retry"
                    attempt_id, final = self._new_attempt(
                        logical_id=logical_id, original_id=original_id, index=index,
                        request_hash=request_hash, response_hash=response_hash, planned=planned,
                        action=action, reason=reason, consumed=0, status="retry_budget")
                    if index == 0:
                        original_id = attempt_id
                    self._remember_failure(final, "retry exceeded stage budget")
                    (self.raw / f"{final['attempt_id']}.fail").write_text("retry-budget", encoding="utf-8")
                    raise RecordingFailure("retry exceeded stage budget") from exc
            attempt_id, final = self._new_attempt(
                logical_id=logical_id, original_id=original_id, index=index,
                request_hash=request_hash, response_hash=response_hash, planned=planned,
                action=action, reason=reason, consumed=consumed,
                status="transport_failed" if transport_error else "pending")
            if index == 0:
                original_id = attempt_id
        if transport_error is not None:
            self._remember_failure(final, "transport failed")
            (self.raw / f"{final['attempt_id']}.fail").write_text("transport", encoding="utf-8")
            raise RecordingFailure("transport failed") from transport_error
        if final["api_attempt_index"] != attempts_n:
            raise RecordingFailure("attempt identity drifted")
        for item in self.attempts:
            if item["logical_call_id"] == logical_id and item["attempt_id"] != final["attempt_id"]:
                item["recording_status"] = "retry"
        path = self.raw / f"{logical_id}.bin"
        path.write_bytes(body)
        if path.read_bytes() != body or status != 200 or not body:
            for item in self.attempts:
                if item["logical_call_id"] == logical_id and item["attempt_id"] != final["attempt_id"]:
                    item["recording_status"] = "retry"
            final["recording_status"] = "not_persisted"
            self._remember_failure(final, "response was not persisted")
            raise RecordingFailure("response was not persisted")
        try:
            parsed = json.loads(body)
            if "choices" in parsed:
                content = parsed["choices"][0]["message"]["content"]
                returned_model = parsed.get("model")
            else:
                content = parsed["message"]["content"]
                returned_model = parsed.get("model")
            if not isinstance(content, str):
                raise ValueError("content")
        except Exception as exc:
            final["recording_status"] = "parse_failed"
            self._remember_failure(final, "unreadable response")
            raise RecordingFailure("unreadable response") from exc
        if returned_model and returned_model != self.model_id:
            from aivd_post_rc3.stop import halt
            final["recording_status"] = "model_mismatch"
            self._remember_failure(final, "model mismatch")
            halt(f"UNEXPECTED_MODEL_SUBSTITUTION: requested={self.model_id!r} got={returned_model!r}")
        updated = _append(shell, public_input, content, action, reason, budget=None)
        if updated.turns[-1].turn_id != planned["turn_id"] or updated.turns[-1].state_before_hash != planned["state_before_hash"]:
            final["recording_status"] = "turn_identity"
            self._remember_failure(final, "turn identity drifted")
            raise RecordingFailure("turn identity drifted")
        self.calls += 1
        call_id = f"{self.calls:03d}-{planned['turn_id'][:12]}"
        final["success"] = True
        final["recording_status"] = "persisted"
        final["call_id"] = call_id
        self.texts[updated.turns[-1].turn_id] = {"input": public_input, "output": content}
        self.trajectories[updated.trajectory_id] = updated
        record = {
            "call_id": call_id,
            "attempt_id": final["attempt_id"],
            "stage": self.stage,
            "logical_call_id": logical_id,
            "retry_of": final["retry_of"],
            "success": True,
            "recording_status": "persisted",
            "model_id": self.model_id,
            "trajectory_id": planned["trajectory_id"],
            "turn_id": planned["turn_id"],
            "parent_turn_id": planned["parent_turn_id"],
            "state_before_hash": planned["state_before_hash"],
            "state_after_hash": updated.turns[-1].state_after_hash,
            "input_hash": planned["input_hash"],
            "request_hash": request_hash,
            "raw_body_sha256": response_hash,
            "content_sha256": sha256(content.encode()).hexdigest(),
            "token_usage": _usage_from_openai(body) if "choices" in parsed else parsed.get("usage") or {},
            "message_count": len(messages),
            "action": action,
            "reason": reason,
            "budget_remaining": self.budget.limit - self.budget.turn_executions,
            "returned_model": returned_model,
            "api_attempts": attempts_n,
        }
        (self.raw / f"{call_id}.json").write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
        self.records.append(record)
        return updated

    @property
    def recording_failures(self) -> int:
        return sum(1 for item in self.attempts if item["recording_status"] in RECORDING_FAILURE_STATUSES)
