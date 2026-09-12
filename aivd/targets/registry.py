"""Allowlist registry for targets."""
from __future__ import annotations

from typing import Any

from aivd.targets.mock import MockTarget
from aivd.targets.openai_compat import OpenAICompatStub
from aivd.targets.local_stub import LocalStubTarget

ALLOWED_TARGETS = {
    "mock://default": lambda **kw: MockTarget(**kw),
    "local://stub": lambda **kw: LocalStubTarget(),
    "openai-compat://stub": lambda **kw: OpenAICompatStub(**kw),
}


def get_target(target_id: str, allowlist: list[str] | None = None, **kwargs: Any):
    if allowlist is not None and target_id not in allowlist:
        raise PermissionError(f"Target {target_id!r} not in allowlist")
    if target_id not in ALLOWED_TARGETS:
        raise PermissionError(f"Unknown / non-allowlisted target: {target_id!r}")
    return ALLOWED_TARGETS[target_id](**kwargs)
