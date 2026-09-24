# Stage G.2 selection freeze

Committed before behavioral measurement. Source class: SOURCE-E. Not Source-A.

These repositories are public. This is a precommitted external sample, not an experimenter-blind corpus. Public documentation of these projects may already be known. No candidate is chosen after its behavior is inspected.

| Id | Source | Repository | Pin |
|---|---|---|---|
| E1 | General Program Synthesis Benchmark | `thelmuth/program-synthesis-benchmark-datasets` | `c02d18c3608b164ff09cc5cad3c02f98f9c1ef21` (tag v1.2) |
| E2 | SyGuS Competition | `SyGuS-Org/benchmarks` | `13c8deb68a873635879c9a69bc78caebd340f646` |
| E3 | SyGuS-Comp14 | `rishabhs/sygus-comp14` | `c56409093597c4c1f358b42a9b0db8dfefe52040` |
| E4 | Microsoft PROSE | `microsoft/prose` | `50cc38f602fffe14073953cf128825ea8d92b188` |

Population: every regular file in that checkout, except `.git`. Sources are not merged.

Compatibility: the file is at most 1024 bytes and its text is one canonical Micro key. There is no translator from SyGuS, PROSE, Push, or any other language. Translator version `identity-micro-key-v0`.

Dedup: one copy of each canonical key. Order: SHA-256 of that key. Sample: at most 16, indices drawn from seed `aivd-4.0-stage-g2-source-e-v1` mixed with the source id. An incompatible file is counted and is not replaced.

Bank: `12df0f9376639650fe8386deb99532c62efef629fa8ac596cfe65e35db5761e5`. It is not changed if the sample is empty or ambiguous.

`microsoft/prose-benchmarks` is a different repository and is not part of this freeze.
