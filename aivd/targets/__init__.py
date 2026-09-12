from aivd.targets.mock import MockTarget, HIDDEN_VULNS
from aivd.targets.openai_compat import OpenAICompatStub
from aivd.targets.local_stub import LocalStubTarget
from aivd.targets.registry import get_target, ALLOWED_TARGETS

__all__ = [
    "MockTarget",
    "HIDDEN_VULNS",
    "OpenAICompatStub",
    "LocalStubTarget",
    "get_target",
    "ALLOWED_TARGETS",
]
