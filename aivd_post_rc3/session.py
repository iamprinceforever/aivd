"""Recording session for POST-RC3. Same execute interface RC3 discovery expects.

POST-RC3 / MODEL GENERALIZATION / NOT PART OF RC3 RELEASE.
Builds Groq OpenAI-compatible requests; records hashes + budget remaining.
Never stores the API key.
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from aivd_stateful.model import BudgetExhausted, _append, plan_turn
from aivd_stateful.session import RecordingFailure, SessionRefused

from aivd_post_rc3.authorize import run_open
from aivd_post_rc3.groq_client import build_chat_request


def _usage_from_openai(body: bytes) -> dict:
    try:
        parsed = json.loads(body)
        usage = parsed.get("usage") or {}
        return {k: usage.get(k) for k in ("prompt_tokens", "completion_tokens", "total_tokens")
                if k in usage}
    except Exception:
        return {}


class PostRC3Session:
    """Drop-in for the interface discover.run / driver expect: execute, budget, calls, records, trajectories, texts."""

    def __init__(self, root, transport, budget, *, model_id: str):
        self.root = Path(root)
        self.raw = self.root / "raw"
        self.raw.mkdir(parents=True, exist_ok=True)
        self.transport = transport
        self.budget = budget
        self.model_id = model_id
        self.calls = 0
        self.attempt_charges = 0  # includes retries
        self.records = []
        self.trajectories = {}
        self.texts = {}

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

    def _fail(self, call_id: str, reason: str) -> None:
        (self.raw / f"{call_id}.fail").write_text(reason, encoding="utf-8")

    def execute(self, trajectory, public_input: str, action: str, reason: str):
        if not run_open():
            raise SessionRefused("POST-RC3 run is closed")
        if not reason:
            raise SessionRefused("missing reason")
        try:
            self.budget.charge(action)
        except BudgetExhausted:
            raise
        shell, planned = plan_turn(trajectory, public_input, action)
        messages = self.history(shell) + [{"role": "user", "content": public_input}]
        # Build the OpenAI-shaped request that the wire / Groq transport will see.
        request = build_chat_request(self.model_id, messages)
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
        # Preregistered retry accounting: every real API attempt is one budget unit. The first
        # attempt was charged above; each extra (retry) attempt reported by the transport charges
        # one more unit on the CURRENT stage. Exceeding the ceiling is an integrity failure.
        attempts = int(getattr(self.transport, "last_attempts", 1) or 1)
        self.attempt_charges += attempts
        for _ in range(attempts - 1):
            try:
                self.budget.charge("retry")
            except BudgetExhausted as exc:
                self._fail(call_id, "retry-budget")
                raise RecordingFailure("retry exceeded stage budget") from exc
        path = self.raw / f"{call_id}.bin"
        path.write_bytes(body)
        if path.read_bytes() != body or status != 200 or not body:
            self._fail(call_id, "persist")
            raise RecordingFailure("response was not persisted")
        try:
            parsed = json.loads(body)
            # Accept either native OpenAI shape or the ollama-shaped wire helper.
            if "choices" in parsed:
                content = parsed["choices"][0]["message"]["content"]
                returned_model = parsed.get("model")
            else:
                content = parsed["message"]["content"]
                returned_model = parsed.get("model")
            if not isinstance(content, str):
                raise ValueError("content")
        except Exception as exc:
            self._fail(call_id, "parse")
            raise RecordingFailure("unreadable response") from exc
        if returned_model and returned_model != self.model_id:
            from aivd_post_rc3.stop import halt
            halt(f"UNEXPECTED_MODEL_SUBSTITUTION: requested={self.model_id!r} got={returned_model!r}")
        updated = _append(shell, public_input, content, action, reason, budget=None)
        if updated.turns[-1].turn_id != planned["turn_id"] or updated.turns[-1].state_before_hash != planned["state_before_hash"]:
            raise RecordingFailure("turn identity drifted")
        self.texts[updated.turns[-1].turn_id] = {"input": public_input, "output": content}
        self.trajectories[updated.trajectory_id] = updated
        record = {
            "call_id": call_id,
            "model_id": self.model_id,
            "trajectory_id": planned["trajectory_id"],
            "turn_id": planned["turn_id"],
            "parent_turn_id": planned["parent_turn_id"],
            "state_before_hash": planned["state_before_hash"],
            "state_after_hash": updated.turns[-1].state_after_hash,
            "input_hash": planned["input_hash"],
            "request_hash": sha256(raw_request).hexdigest(),
            "raw_body_sha256": sha256(body).hexdigest(),
            "content_sha256": sha256(content.encode()).hexdigest(),
            "token_usage": _usage_from_openai(body) if "choices" in parsed else parsed.get("usage") or {},
            "message_count": len(messages),
            "action": action,
            "reason": reason,
            "budget_remaining": self.budget.limit - self.budget.turn_executions,
            "returned_model": returned_model,
            "api_attempts": attempts,
        }
        (self.raw / f"{call_id}.json").write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
        self.records.append(record)
        return updated
