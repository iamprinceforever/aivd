"""Point the unchanged POST-RC3 driver at AIVD-RC4-MULTI-V1 for this process only.

No aivd_rc3 / aivd_post_rc3 / aivd_post_rc3_local source is edited. In-process only it replaces:
experiment id, request builder/contract (local Ollama, reused from aivd_post_rc3_local), and the
per-stage ceilings (152 / 24 / 24, + 6 repeat; D1=C) which the frozen driver reads as module globals,
and the stale hosted-provider label inside the plan commitment (`plan_commitment`), replaced by an RC4
function with the identical fields except provider = local Ollama. The ledger's own provider field is a
literal inside the frozen driver and is corrected post-write by aivd_rc4_multi.ledger_meta.
"""

from aivd_rc4_multi import EXPERIMENT_ID
from aivd_rc4_multi import config as C
from aivd_rc4_multi.ledger_meta import PROVIDER_LABEL
from aivd_post_rc3_local.ollama_backend import build_request, request_contract

BOUND = (("authorize", "EXPERIMENT_ID"), ("driver", "EXPERIMENT_ID"), ("driver", "request_contract"),
         ("session", "build_chat_request"), ("driver", "DISCOVERY_LIMIT"), ("driver", "INVESTIGATION_LIMIT"),
         ("driver", "VERIFICATION_LIMIT"), ("driver", "MODEL_ALLOCATION"), ("config", "REPRO_CALLS_PER_MODEL"),
         ("authorize", "plan_commitment"), ("driver", "plan_commitment"))


def plan_commitment(corpus_commitment: str, model_id: str, allocation: int = C.MAIN_ALLOCATION) -> str:
    """Same fields as frozen aivd_post_rc3.authorize.plan_commitment; only the provider label differs."""
    from aivd_stateful.hashing import digest
    return digest({"experiment_id": EXPERIMENT_ID, "model_id": model_id, "corpus_commitment": corpus_commitment,
                   "allocation": allocation, "provider": PROVIDER_LABEL})


def bind() -> None:
    import aivd_post_rc3.authorize as auth
    import aivd_post_rc3.config as cfg
    import aivd_post_rc3.driver as drv
    import aivd_post_rc3.session as sess

    if drv.VERIFY_COST != C.VERIFY_COST:
        raise RuntimeError("frozen VERIFY_COST changed")
    auth.EXPERIMENT_ID = EXPERIMENT_ID
    drv.EXPERIMENT_ID = EXPERIMENT_ID
    drv.request_contract = request_contract
    sess.build_chat_request = build_request
    drv.DISCOVERY_LIMIT = C.DISCOVERY_LIMIT
    drv.INVESTIGATION_LIMIT = C.INVESTIGATION_LIMIT
    drv.VERIFICATION_LIMIT = C.VERIFICATION_LIMIT
    drv.MODEL_ALLOCATION = C.MAIN_ALLOCATION
    cfg.REPRO_CALLS_PER_MODEL = C.REPRO_CALLS_PER_MODEL
    auth.plan_commitment = plan_commitment
    drv.plan_commitment = plan_commitment
