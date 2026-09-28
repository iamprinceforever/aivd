"""Downstream stub. The investigation engine does not import this module."""


def independent_check(*, investigation_status: str, sealed_relation_supplied: bool) -> str:
    if investigation_status != "VERIFICATION_READY" or not sealed_relation_supplied:
        return "NOT_VERIFIED"
    return "VERIFIED_SECURITY_DISCOVERY"
