"""Agents package — lazy exports to avoid explorers↔controller circular import."""

from aivd.agents.generators import PromptGenerator
from aivd.agents.planner import Planner

__all__ = ["Controller", "Planner", "PromptGenerator"]


def __getattr__(name: str):
    if name == "Controller":
        from aivd.agents.controller import Controller
        return Controller
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
