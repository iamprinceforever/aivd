"""Point the unchanged POST-RC3 driver at the V2 experiment id for this process only.

Does not edit aivd_post_rc3 source. The package constant stays POST-RC3-GROQ.
"""

from aivd_post_rc3_v2 import EXPERIMENT_ID


def bind() -> None:
    import aivd_post_rc3.authorize as auth
    import aivd_post_rc3.driver as drv

    auth.EXPERIMENT_ID = EXPERIMENT_ID
    drv.EXPERIMENT_ID = EXPERIMENT_ID
