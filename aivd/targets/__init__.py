from aivd.targets.mock import MockTarget, HIDDEN_VULNS
from aivd.targets.openai_compat import OpenAICompatStub, OpenAICompatTarget
from aivd.targets.local_stub import LocalStubTarget
from aivd.targets.anthropic import AnthropicTarget
from aivd.targets.gemini import GeminiTarget
from aivd.targets.local_model import LocalModelTarget
from aivd.targets.registry import get_target, ALLOWED_TARGETS

__all__ = [
    "MockTarget",
    "HIDDEN_VULNS",
    "OpenAICompatStub",
    "OpenAICompatTarget",
    "LocalStubTarget",
    "AnthropicTarget",
    "GeminiTarget",
    "LocalModelTarget",
    "get_target",
    "ALLOWED_TARGETS",
]
