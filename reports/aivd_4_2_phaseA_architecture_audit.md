# Phase A — what is language-neutral

F2 is **EXPERIMENT_BLOCKED**. Nothing was implemented. F1 was not modified.

The signature store does not know Micro. The code that fills it does.

| Piece | Knows a language? |
|---|---|
| `BehavioralSignature`, `compare`, `content_id` | No. They store a bank hash and ordered `(index, output, status)`. |
| `BehavioralMemory.add` | No. Lookup is the content id. There is no language partition. |
| `BehavioralDimension` | No language field. Provenance is a handle, parents, and an event. |
| Stage E `experiment.py` and `engine.py` | Yes. Both call `apply_micro` on a Micro tree. |
| F1 `contract.py` | Yes. It calls `eval_micro` and `apply_micro`. |
| Stage G generator and Stage G.2 rule | Yes. They emit or accept only Micro keys. |
| Both probe banks | Built for Micro string/token behavior. The F1 bank is not a generic input. |

So the answers are:

1. The stored signature, the comparison, and the memory key are already language-blind.
2. Every producer is Micro-specific. So is `AMBIGUOUS_COPY`, which means the Micro executor returned the probe, including its empty-output fallback.
3. The signature structure can hold a generic observation. Nothing today produces one from a non-Micro program. `complete()` still means "every status is NORMAL", which is the Stage E vocabulary.
4. A dimension can be stored without a language name. That path has been used only for Micro.
5. Memory is not partitioned by language. A second language was never inserted, so this is untested.
6. `compare` would treat two complete signatures as the same dimension when the outputs match. It cannot tell two executors apart, and it also cannot tell that their probes meant different things. The engine never runs a second executor.
7. An adapter must not pass an AST, an operator name, a benchmark name, a dataset name, a semantic class, or a target. A language id may sit in provenance. It must not be an input to `compare`.

The F1 bank `e417e460…` stays a Micro bank. It is not reused here.
