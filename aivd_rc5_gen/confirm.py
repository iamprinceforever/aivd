"""Preregistered confirmation request (EXPERIMENTER side; public text only).

The frozen driver's verification stage re-executes the candidate's final follow-up with the SAME public
input, so its C7 repeat is a same-request re-execution (RC4 caveat: byte-identical responses happened).
RC5 makes the confirmation request semantically equivalent but NOT byte-identical, WITHOUT editing any
frozen file: every public scenario carries a frozen alternate public context `confirm` (written at
generation time from a per-construction template, identical for a security target and its benign twin,
so it reveals no label). In-process, `session_class` replaces the driver's session class with a
subclass whose "verify" request uses `confirm` in place of the original follow-up. Nothing else changes: the source-swap
arm (C3/C5) is untouched and the frozen verifier's C7 still requires the exact sealed value in the
confirmation output.

Reporting distinction (preregistered; never changes a verifier decision):
  INDEPENDENT_CONFIRMATION  confirmation request differs from the original AND its output text differs
  DETERMINISTIC_REPLAY      confirmation output is byte-identical to the original output, or the
                            request was byte-identical (must not happen by construction; tested)
Byte-identical is NEVER called an independent reproduction.
"""

DETERMINISTIC_REPLAY = "DETERMINISTIC_REPLAY"
INDEPENDENT_CONFIRMATION = "INDEPENDENT_CONFIRMATION"
NOT_CONFIRMED = "NOT_CONFIRMED"


def confirm_map(ordered_public: list) -> dict:
    """original follow-up text -> frozen alternate confirmation text (the follow-up contains the sid, so
    the mapping is unique per scenario)."""
    out = {}
    for p in ordered_public:
        original = p["steps"][1] if p.get("steps") else p["probe"]
        alt = p.get("confirm")
        if not alt or alt == original:
            raise ValueError(f"scenario {p['scenario_id']} lacks a distinct frozen confirmation context")
        if original in out:
            raise ValueError("follow-up text is not unique")
        out[original] = alt
    return out


def session_class(mapping: dict):
    """A subclass of the frozen PostRC3Session whose 'verify' action uses the frozen alternate context.
    Installed in-process by aivd_rc5_gen.bind.bind(confirm_mapping=...) as aivd_post_rc3.driver.PostRC3Session;
    no frozen file is edited. Every other action is passed through unchanged."""
    from aivd_post_rc3.session import PostRC3Session

    class RC5ConfirmSession(PostRC3Session):
        rc5_confirmation = dict(mapping)

        def execute(self, trajectory, public_input, action, reason):
            if action == "verify":
                if public_input not in self.rc5_confirmation:
                    raise RuntimeError("verification follow-up has no preregistered confirmation context")
                public_input = self.rc5_confirmation[public_input]
            return super().execute(trajectory, public_input, action, reason)

    return RC5ConfirmSession


def classify(candidate: dict, *, confirmed_by_verifier: bool) -> str:
    po, vo = candidate.get("preserved_output"), candidate.get("verification_output")
    if not confirmed_by_verifier:
        return NOT_CONFIRMED
    if po is not None and vo is not None and po == vo:
        return DETERMINISTIC_REPLAY
    return INDEPENDENT_CONFIRMATION
