# Language selection

No second language was selected. A toy language was not written.

The four pinned corpora were already classified. None of them is a Micro program: 21,598 files, 0 Micro keys, and the Micro bank was not run. This audit did not re-download them. The public descriptions of those pins are enough to reject them as Language B.

| Pin | What it is | Why it is not Language B |
|---|---|---|
| E1 `c02d18c` | A dataset release. | A table of synthesis examples is not `execute(program, probe)`. No interpreter is recorded in that pin. |
| E2 `13c8deb` | SyGuS-Comp specifications. | A specification asks a solver to search. It is not a deterministic interpreter of a candidate. |
| E3 `c564090` | The 2014 benchmarks, plus solvers. | The benchmarks are specifications. The solvers are search programs, not a small interpreter of those specifications. |
| E4 `50cc38f` | The PROSE SDK and its samples. | The samples are examples and host-language projects. Running them needs that SDK. It is not a small trusted interpreter. |

Translating any of these into Micro is the experiment this stage forbids. An AIVD-internal layer other than Micro would also fail the requirement that Language B be independent of AIVD.

File-extension counts were not retaken. The GitHub tree API returned 403. That recount is `NOT_RECORDED`. It is not needed for the decision above.
