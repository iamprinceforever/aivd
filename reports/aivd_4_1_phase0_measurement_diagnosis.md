# Phase 0 — why Stage G recorded 70 AMBIGUOUS_COPY

Status of the cause: **established**. It is more than one cause. `AMBIGUOUS_COPY` is not treated as a bug, and it is not treated as one behavior.

The label is assigned only by `out == probe` in [experiment.py](aivd/behavior/discovery/experiment.py) and [engine.py](aivd/behavior/discovery/engine.py). `apply_micro` returns the original prompt when `split_prompt` is empty, and again when evaluation leaves no nonempty token ([micro.py](aivd/science/micro.py)). Those paths are not separated from a program that was evaluated and actually reproduced the probe.

The Stage G reveal was replayed. Only the 16 candidates that have stored outputs were used. The 70 labels split as follows:

| Cause | Count | What the executor did |
|---|---:|---|
| Empty probe never evaluates | 16 | Probe `""` has no token. `apply_micro` returns it immediately. Every measured candidate. |
| Evaluated identity | 28 | The program ran. The joined output was the probe. |
| Empty-output fallback | 26 | Evaluation produced no nonempty token. `apply_micro` returned the probe anyway. |

Nothing in the 70 was an exception. The replay matched the stored output on every one of those probes.

The empty probe is also a coverage failure. Because it is always a copy, no program can obtain a complete signature on bank `12df0f9376639650fe8386deb99532c62efef629fa8ac596cfe65e35db5761e5` under the rule "every probe must be NORMAL." That is a property of this bank plus this status rule. It is not a property that was fixed by editing Stage E.
