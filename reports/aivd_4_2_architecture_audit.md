# Architecture audit

Same finding as the Phase A note. The behavioral record is language-blind. The only executor is Micro. No second adapter was added. F2 is **EXPERIMENT_BLOCKED**.

`compare` in [compare.py](aivd/behavior/discovery/compare.py) decides from outputs on one bank hash. `apply_micro` is the only function that produces those outputs, in [experiment.py](aivd/behavior/discovery/experiment.py) and in the F1 contract. Sharing the record across languages is possible only after a second interpreter emits the same observation shape. That interpreter is not in the pinned corpora, and it was not invented here.
