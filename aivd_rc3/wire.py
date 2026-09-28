"""Evaluator-side note injection for RC3, with the generic source-swap condition.

Discovery never imports this module. The wire injects a scenario's sealed note as a system message
ONLY when the public transcript contains that scenario's setup mark and its scenario id (the
privileged context the model saw during setup), and records every request/response.

Source-swap condition (condition B)
-----------------------------------
When the incoming transcript carries the public SWAP_SENTINEL, the wire is in condition B: it
replaces the sealed token inside the injected note with swap(token) (see aivd_rc3.provenance),
and strips the sentinel from the messages it forwards to the model, so the model's visible prompt
is identical to condition A except that the restricted SOURCE now holds the swapped value. The
sentinel is a fixed public string; it carries no sealed information. A value the model copies from
the restricted source therefore tracks the swap; an invented value does not.
"""

import json
from hashlib import sha256

from aivd_rc3.provenance import swap
from aivd_rc3.provider import CTX_MARK, STEP_MARK, SWAP_SENTINEL


class Wire:
    def __init__(self, seal: dict, inner, wire_dir):
        self.notes = {r["scenario_id"]: r["note"] for r in seal["targets"]}
        self.tokens = {r["scenario_id"]: r.get("token", "") for r in seal["targets"]}
        self.inner = inner
        self.wire_dir = wire_dir
        self.wire_dir.mkdir(parents=True, exist_ok=True)
        self.calls = 0

    def __call__(self, request: dict) -> tuple:
        messages = list(request["messages"])
        raw_transcript = "\n".join(m.get("content", "") for m in messages)
        swap_active = SWAP_SENTINEL in raw_transcript
        if swap_active:
            messages = [{**m, "content": m.get("content", "").replace(SWAP_SENTINEL, "").lstrip("\n")}
                        for m in messages]
        transcript = "\n".join(m.get("content", "") for m in messages)
        note = None
        for sid, text in self.notes.items():
            if (STEP_MARK in transcript or CTX_MARK in transcript) and sid in transcript:
                token = self.tokens.get(sid) or ""
                if swap_active and token:
                    text = text.replace(token, swap(token))
                note = text
                break
        if note is not None:
            messages = [{"role": "system", "content": note}] + messages
        sent = dict(request)
        sent["messages"] = messages
        raw = json.dumps(sent, sort_keys=True).encode()
        self.calls += 1
        (self.wire_dir / f"{self.calls:03d}.req").write_bytes(raw)
        status, response = self.inner(sent)
        body = response if isinstance(response, (bytes, bytearray)) else b""
        (self.wire_dir / f"{self.calls:03d}.bin").write_bytes(body)
        (self.wire_dir / f"{self.calls:03d}.hash").write_text(sha256(raw).hexdigest(), encoding="utf-8")
        return status, response
