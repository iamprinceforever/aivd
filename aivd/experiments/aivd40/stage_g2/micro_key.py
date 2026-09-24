"""Parse the frozen Micro.key() text. This is not a translator from another language."""

from __future__ import annotations

from aivd.science.micro import MICRO_OPS, Micro, canonicalize_micro, validate_micro


class NotMicroKey(ValueError):
    pass


def parse_micro_key(text: str) -> Micro:
    parser = _Parser(text)
    body = parser.parse_expr()
    parser.skip()
    if parser.i != len(parser.text):
        raise NotMicroKey("trailing bytes")
    canonical = canonicalize_micro(body)
    if canonical is None or validate_micro(canonical, n_tokens=4) is not None:
        raise NotMicroKey("rejected by the frozen grammar")
    if canonical.key() != text:
        raise NotMicroKey("not in canonical key form")
    return canonical


class _Parser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.i = 0

    def parse_expr(self) -> Micro:
        op = self._ident()
        if op not in MICRO_OPS:
            raise NotMicroKey("unknown operator")
        args: tuple[int, ...] = ()
        if self._peek() == ":":
            self.i += 1
            args = self._args()
        kids: tuple[Micro, ...] = ()
        if self._peek() == "(":
            self.i += 1
            parts = [self.parse_expr()]
            while self._peek() == "|":
                self.i += 1
                parts.append(self.parse_expr())
            if self._peek() != ")":
                raise NotMicroKey("unclosed children")
            self.i += 1
            kids = tuple(parts)
        return Micro(op, args, kids)

    def skip(self) -> None:
        return None

    def _ident(self) -> str:
        start = self.i
        while self.i < len(self.text) and self.text[self.i].isalpha():
            self.i += 1
        if start == self.i:
            raise NotMicroKey("missing operator")
        return self.text[start : self.i]

    def _args(self) -> tuple[int, ...]:
        values = [self._int()]
        while self._peek() == ",":
            self.i += 1
            values.append(self._int())
        return tuple(values)

    def _int(self) -> int:
        start = self.i
        if self._peek() == "-":
            self.i += 1
        if self.i >= len(self.text) or not self.text[self.i].isdigit():
            raise NotMicroKey("missing integer")
        while self.i < len(self.text) and self.text[self.i].isdigit():
            self.i += 1
        return int(self.text[start : self.i])

    def _peek(self) -> str:
        if self.i >= len(self.text):
            return ""
        return self.text[self.i]
