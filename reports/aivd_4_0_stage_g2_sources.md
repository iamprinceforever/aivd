# AIVD 4.0 Stage G.2

Claim: **no compatible candidate was present under the frozen Micro-key rule.**

This is SOURCE-E, a precommitted sample of public corpora. It is not Source-A, not an experimenter-blind corpus, and not a security finding. Public documentation of these projects may already be known. No file was kept or dropped because of its behavior.

The selection freeze is commit `a460c04`, before this measurement. The seed, the cap of 16, the bank, and the compatibility rule were not changed after the counts came back.

## Pins

| Id | Source | Commit | Files | Compatible | Selected |
|---|---|---|---|---:|---:|
| E1 | General Program Synthesis Benchmark, tag v1.2 | `c02d18c3608b164ff09cc5cad3c02f98f9c1ef21` | 207 | 0 | 0 |
| E2 | SyGuS Competition | `13c8deb68a873635879c9a69bc78caebd340f646` | 9755 | 0 | 0 |
| E3 | SyGuS-Comp14 | `c56409093597c4c1f358b42a9b0db8dfefe52040` | 2066 | 0 | 0 |
| E4 | Microsoft PROSE | `50cc38f602fffe14073953cf128825ea8d92b188` | 9570 | 0 | 0 |

Acquisition date: 2026-09-24. E1 and E4 have a root `LICENSE` file. E2 and E3 do not, so their license is `NOT_RECORDED`. Translator: `identity-micro-key-v0`. There is no translator from SyGuS, PROSE, or Push.

Blobs larger than the frozen 1024-byte cap were counted from `git ls-tree` and not downloaded. That is the same cap as the freeze. It is not a second sample.

## What was measured

Nothing. A file entered the sample only if its entire text was one canonical Micro key. None of the 21,598 files were. Incompatible files were not replaced.

| Source | Classification | Commitment |
|---|---|---|
| E1 | NO COMPATIBLE CANDIDATES | `ccc0e23309ac42a6ea360cd152d695c1b3122dec24edab7b4e433b471f0b001a` |
| E2 | NO COMPATIBLE CANDIDATES | `8ad336fe6bdc34fec3728ea34392a13e7fa130005325bd1a371a96fca0d9f34d` |
| E3 | NO COMPATIBLE CANDIDATES | `e06f7faf3c0aa1e8b71654ace5a60c42ba2c36297acfd32c4170fb9616bb2e7d` |
| E4 | NO COMPATIBLE CANDIDATES | `050bcfcd44f6ae371e351138db4ba24005138524144e760770588e06e5825af8` |

Bank `12df0f9376639650fe8386deb99532c62efef629fa8ac596cfe65e35db5761e5` was not executed. Complete signatures: 0. Dimensions: 0. Ambiguity rate: not applicable, because measurement did not start. Sources were not pooled, so no cross-source identity was computed.

## What this does not say

It does not say these corpora contain no novel behavior. They are specifications, examples, and programs in other languages. The frozen protocol cannot score that behavior, and the grammar was not rewritten to force a score.

Source-A, experimenter-blind discovery, a vulnerability, and a verified finding are not supported. `microsoft/prose-benchmarks` was not added after the fact.
