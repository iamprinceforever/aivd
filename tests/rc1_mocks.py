"""Deterministic mock transports for RC1 tests. They never read a seal: they only see the
request (which, via the wire, may contain an injected system note)."""

import json


def reply(text):
    return 200, json.dumps({"message": {"content": text}}).encode()


def _system(request):
    return next((m["content"] for m in request["messages"] if m["role"] == "system"), "")


def _users(request):
    return [m["content"] for m in request["messages"] if m["role"] == "user"]


def leak(request):
    """Leaks the injected note on every turn after the first user turn."""
    system = _system(request)
    if system and len(_users(request)) >= 2:
        return reply(system)
    if system:
        return reply("Noted.")
    return reply("Clear public reply.")


def wordy(request):
    """History changes wording but never reveals anything."""
    n = len(_users(request))
    return reply(("History-aware public reply " if n >= 2 else "Fresh public reply ") + str(n))


def silent(request):
    return reply("A short public reply.")


def long_words(request):
    """Emits long natural-language words (>=12 letters) that are NOT restricted values."""
    n = len(_users(request))
    return reply("Additionally the documentation remains straightforward " + ("again" if n >= 2 else ""))


def reset_leak(request):
    """Leaks even without history: novelty is not security relevance (reset arm is dirty)."""
    system = _system(request)
    return reply(system + (" more" if len(_users(request)) >= 2 else "")) if system else reply("Clear.")


class Counting:
    def __init__(self, inner):
        self.inner = inner
        self.calls = 0

    def __call__(self, request):
        self.calls += 1
        return self.inner(request)


class FailAt:
    def __init__(self, inner, at, mode="raise"):
        self.inner, self.at, self.mode, self.calls = inner, at, mode, 0

    def __call__(self, request):
        self.calls += 1
        if self.calls == self.at:
            if self.mode == "raise":
                raise OSError("transport down")
            if self.mode == "status":
                return 500, b"err"
            if self.mode == "garbage":
                return 200, b"not json"
        return self.inner(request)
