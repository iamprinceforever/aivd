"""Open-ended unknown vulnerability discovery (AIVD 3.7)."""
from aivd37.unknowns.terminal import TerminalState, TerminalResult, is_vulnerability
from aivd37.unknowns.channels import ChannelSpec, ChannelObservation, SECURITY_SHAPED
from aivd37.unknowns.pipeline import UnknownsPipeline, store_terminal_memory
from aivd37.unknowns.classify import Classification

__all__ = [
    "TerminalState",
    "TerminalResult",
    "is_vulnerability",
    "ChannelSpec",
    "ChannelObservation",
    "SECURITY_SHAPED",
    "UnknownsPipeline",
    "store_terminal_memory",
    "Classification",
]
