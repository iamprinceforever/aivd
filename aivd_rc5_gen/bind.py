"""Point the unchanged POST-RC3 driver at AIVD-RC5-GENERALIZATION-V1 for this process only.

No aivd_rc3 / aivd_post_rc3 / aivd_post_rc3_local source is edited. In-process only it replaces:
experiment id, request builder/contract (local Ollama, reused unchanged from aivd_post_rc3_local), the
per-model stage ceilings (320 / 48 / 30, + 6 repeat; FROZEN_AT_DESIGN) which the frozen driver reads as
module globals, and the stale hosted-provider label inside the plan
commitment. The ledger's own provider field is corrected post-write by aivd_rc5_gen.ledger_meta.
"""

from aivd_rc5_gen import EXPERIMENT_ID
from aivd_rc5_gen import config as C
from aivd_rc5_gen.ledger_meta import PROVIDER_LABEL
from aivd_post_rc3_local.ollama_backend import build_request, request_contract

BOUND = (("authorize", "EXPERIMENT_ID"), ("driver", "EXPERIMENT_ID"), ("driver", "request_contract"),
         ("session", "build_chat_request"), ("driver", "DISCOVERY_LIMIT"), ("driver", "INVESTIGATION_LIMIT"),
         ("driver", "VERIFICATION_LIMIT"), ("driver", "MODEL_ALLOCATION"), ("config", "REPRO_CALLS_PER_MODEL"),
         ("authorize", "plan_commitment"), ("driver", "plan_commitment"), ("driver", "PostRC3Session"))


def plan_commitment(corpus_commitment: str, model_id: str, allocation: int = C.MAIN_ALLOCATION) -> str:
    """Same fields as frozen aivd_post_rc3.authorize.plan_commitment; only the provider label differs.
    corpus_commitment is the ASSEMBLED 120-scenario corpus commitment."""
    from aivd_stateful.hashing import digest
    return digest({"experiment_id": EXPERIMENT_ID, "model_id": model_id, "corpus_commitment": corpus_commitment,
                   "allocation": allocation, "provider": PROVIDER_LABEL})


def bind(confirm_mapping: dict | None = None) -> None:
    """confirm_mapping: aivd_rc5_gen.confirm.confirm_map(ordered manifest). Required for a real run."""
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
    if confirm_mapping is not None:
        from aivd_rc5_gen.confirm import session_class
        drv.PostRC3Session = session_class(confirm_mapping)
