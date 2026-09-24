# F2 — generic cross-language behavioral discovery

Status: **EXPERIMENT_BLOCKED**. The claim cannot be made.

The behavioral path executes `apply_micro` on a `Micro` tree. The signature is the ordered outputs of that executor on the frozen string bank. Stage G seals Micro trees. Stage G.2 admits a file only when the file is a canonical Micro key. SyGuS, SyGuS-Comp14, the program-synthesis benchmark, and PROSE contributed 0 such files. Nothing in those languages was executed.

There is no `LanguageAdapter` and no `execute(program, input)` that is separate from Micro. A signature therefore does not yet mean "behavior of an arbitrary language." It means "Micro on this bank."

Two deterministic languages were not run. Building a SyGuS or PROSE translator now would be a new experiment, and it is not justified by this audit. No adapter was added.

## What a later experiment would need

An adapter may expose only a language id and `deterministic_execute(program, input) -> output`. The signature layer may see input, output, and execution status. It may not see the benchmark name, a family, or a target. Two languages have to be executed under one frozen input list before any same-dimension or distinct-dimension claim. Until that executor exists, the cross-language experiment cannot start.
