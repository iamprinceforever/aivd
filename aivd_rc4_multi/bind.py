"""Point the unchanged POST-RC3 driver at AIVD-RC4-MULTI-V1 for this process only.

No aivd_rc3 / aivd_post_rc3 / aivd_post_rc3_local source is edited. In-process only it replaces:
experiment id, request builder/contract (local Ollama, reused from aivd_post_rc3_local), and the
per-stage ceilings (48 / 24 / 12, + 6 repeat) which the frozen driver reads as module globals.
"""

from aivd_rc4_multi import EXPERIMENT_ID
from aivd_rc4_multi import config as C
from aivd_post_rc3_local.ollama_backend import build_request, request_contract

BOUND = (("authorize", "EXPERIMENT_ID"), ("driver", "EXPERIMENT_ID"), ("driver", "request_contract"),
         ("session", "build_chat_request"), ("driver", "DISCOVERY_LIMIT"), ("driver", "INVESTIGATION_LIMIT"),
         ("driver", "VERIFICATION_LIMIT"), ("driver", "MODEL_ALLOCATION"), ("config", "REPRO_CALLS_PER_MODEL"))


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
