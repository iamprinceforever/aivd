"""AIVD 3.7 — Open-Ended Unknown Vulnerability Discovery.

Sits ABOVE 3.6 causal discovery. Completes terminal semantics via residual-channel
sweep → VERIFIED (observable unknown vuln) or UNRESOLVED_INVISIBLE (AO hard control).
Same architecture for both paths; no AO special-case cheat.
"""
__version__ = "3.7.0"

from aivd37.unknowns.terminal import TerminalState, is_vulnerability
from aivd37.unknowns.pipeline import UnknownsPipeline

__all__ = [
    "__version__",
    "TerminalState",
    "is_vulnerability",
    "UnknownsPipeline",
]
