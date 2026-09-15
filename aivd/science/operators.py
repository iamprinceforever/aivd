"""Generic experimental operators. Not an attack taxonomy.

These are structural edits a scientist can apply to any prompt:
omit, swap, wrap, repeat, separate. No vulnerability signatures,
no holdout names, no planted cue vocabulary.
"""
from __future__ import annotations

from typing import Callable


def split_prompt(prompt: str) -> list[str]:
    return [t for t in (prompt or "").split() if t]


def join_prompt(tokens: list[str]) -> str:
    return " ".join(tokens).strip()


def _omit_first(p: str) -> str:
    t = split_prompt(p)
    return join_prompt(t[1:]) if len(t) > 1 else p


def _omit_second(p: str) -> str:
    t = split_prompt(p)
    if len(t) < 2:
        return p
    return join_prompt(t[:1] + t[2:])


def _omit_last(p: str) -> str:
    t = split_prompt(p)
    return join_prompt(t[:-1]) if len(t) > 1 else p


def _swap_first_two(p: str) -> str:
    t = split_prompt(p)
    if len(t) < 2:
        return p
    t[0], t[1] = t[1], t[0]
    return join_prompt(t)


def _swap_last_two(p: str) -> str:
    t = split_prompt(p)
    if len(t) < 2:
        return p
    t[-1], t[-2] = t[-2], t[-1]
    return join_prompt(t)


def _reverse_content(p: str) -> str:
    t = split_prompt(p)
    return join_prompt(list(reversed(t))) if len(t) > 1 else p


def _repeat_last(p: str) -> str:
    t = split_prompt(p)
    if not t:
        return p
    return join_prompt(t + [t[-1]])


def _duplicate(p: str) -> str:
    t = split_prompt(p)
    return join_prompt(t + t) if t else p


def _wrap_quotes(p: str) -> str:
    s = (p or "").strip()
    if s.startswith('"') and s.endswith('"'):
        return s
    return f'"{s}"'


def _insert_sep(p: str) -> str:
    t = split_prompt(p)
    if len(t) < 2:
        return p
    return join_prompt(t[:-1] + ["|"] + t[-1:])


def _suffix_q(p: str) -> str:
    s = (p or "").rstrip()
    if s.endswith("?"):
        return s
    return s + " ?"


def _prefix_please(p: str) -> str:
    s = (p or "").strip()
    if s.lower().startswith("please"):
        return s
    return "please " + s


OPERATORS: dict[str, Callable[[str], str]] = {
    "omit_second": _omit_second,
    "omit_first": _omit_first,
    "wrap_quotes": _wrap_quotes,
    "swap_first_two": _swap_first_two,
    "swap_last_two": _swap_last_two,
    "repeat_last": _repeat_last,
    "insert_sep": _insert_sep,
    "suffix_q": _suffix_q,
    "duplicate": _duplicate,
    "reverse_content": _reverse_content,
    "omit_last": _omit_last,
    "prefix_please": _prefix_please,
}

# Cheap first-round battery. Repeat/duplicate are present so they can be
# falsified as high-metric traps, not because they are preferred.
BATTERY: tuple[str, ...] = (
    "omit_second",
    "omit_first",
    "wrap_quotes",
    "swap_first_two",
    "repeat_last",
    "insert_sep",
    "suffix_q",
    "swap_last_two",
)


def apply_operator(prompt: str, name: str) -> str:
    fn = OPERATORS.get(name)
    if fn is None:
        return prompt
    out = fn(prompt)
    return out if out else prompt


def apply_sequence(prompt: str, names: list[str]) -> str:
    cur = prompt
    for n in names:
        cur = apply_operator(cur, n)
    return cur


__all__ = [
    "OPERATORS",
    "BATTERY",
    "apply_operator",
    "apply_sequence",
    "split_prompt",
    "join_prompt",
]
