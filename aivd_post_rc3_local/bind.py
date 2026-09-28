"""Point the unchanged POST-RC3 driver/session at POST-RC3-LOCAL-V1 for this process only.

Does not edit aivd_post_rc3 or aivd_rc3 source. Replaces, in-process, the experiment id and the
Groq request builder/contract with the local Ollama ones so the frozen stages run unchanged.
"""

from aivd_post_rc3_local import EXPERIMENT_ID
from aivd_post_rc3_local.ollama_backend import build_request, request_contract


def bind() -> None:
    import aivd_post_rc3.authorize as auth
    import aivd_post_rc3.driver as drv
    import aivd_post_rc3.session as sess

    auth.EXPERIMENT_ID = EXPERIMENT_ID
    drv.EXPERIMENT_ID = EXPERIMENT_ID
    drv.request_contract = request_contract
    sess.build_chat_request = build_request
