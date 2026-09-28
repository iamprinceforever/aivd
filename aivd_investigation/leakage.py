"""Reject fields the investigator is not allowed to see."""

from aivd_investigation.spec import FORBIDDEN_KEYS


class LeakageError(Exception):
    pass


def reject(payload) -> None:
    if isinstance(payload, dict):
        found = FORBIDDEN_KEYS & set(payload)
        if found:
            raise LeakageError("investigation input contains a hidden field")
        for value in payload.values():
            reject(value)
    elif isinstance(payload, (list, tuple)):
        for value in payload:
            reject(value)
