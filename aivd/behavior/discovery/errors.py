"""Protocol refusals. These are not behavioral dimensions."""


class DiscoveryBankSealed(RuntimeError):
    """The frozen discovery bank must not be executed in this package path."""


class BudgetExhausted(RuntimeError):
    """The relevant half of the 256-call budget cannot pay for this step."""


class BlindnessBroken(RuntimeError):
    """Plaintext would become visible to the experimenter."""


class CorpusRejected(RuntimeError):
    """The object is not an external Source-A seal."""
