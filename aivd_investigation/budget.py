"""Separate units for investigation, probes, and verification. One probe is one future model call."""


class BudgetExhausted(Exception):
    pass


class Budget:
    def __init__(self, investigate: int, probe: int, verify: int):
        self.investigate_limit = investigate
        self.probe_limit = probe
        self.verify_limit = verify
        self.investigate_used = 0
        self.probe_used = 0
        self.verify_used = 0
        self.stops = ()

    def charge(self, kind: str) -> int:
        if kind == "investigate":
            if self.investigate_used >= self.investigate_limit:
                self.stops += ("INVESTIGATE_EXHAUSTED",)
                raise BudgetExhausted(kind)
            self.investigate_used += 1
            return self.investigate_limit - self.investigate_used
        if kind == "probe":
            if self.probe_used >= self.probe_limit:
                self.stops += ("PROBE_EXHAUSTED",)
                raise BudgetExhausted(kind)
            self.probe_used += 1
            return self.probe_limit - self.probe_used
        if kind == "verify":
            if self.verify_used >= self.verify_limit:
                self.stops += ("VERIFY_EXHAUSTED",)
                raise BudgetExhausted(kind)
            self.verify_used += 1
            return self.verify_limit - self.verify_used
        raise BudgetExhausted(kind)
