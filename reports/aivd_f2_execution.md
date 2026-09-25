# F2 execution

**F2 EXPERIMENT COMPLETE**

**CROSS_LANGUAGE_BEHAVIOR_DEMONSTRATED** on the frozen bank only.

The run used the frozen bank, the frozen samples, and the frozen order. Nothing was added or removed after the first candidate. Security was not scored.

| Pin | Value |
|---|---|
| Implementation | `e3ae322832cb704ecdd8226f1a80b8927935a5cb` |
| Design | `3cedb97a853a71bad8d0b4289bf82cd1d12d32b7` |
| Bank | `984ebf8a66a7d6695c03d7fef75e89f20b1a839626a1337be02adabece4243a5` |
| Selection | `3327aa65e688f4dac151c59c8fa0d17cda219a2a47487f689e3d7f7b06f6bcbf` |
| Micro sample | `df13d301cf88249720d20f27017ca8946b59529115a70ca370271ce5f49ac862` |
| CEL sample | `33999336c21e9bf5891214ba57596df1403b9e0d0acfec782df7bc92e31e838e` |
| CEL commit | `97611dc314dd41c9a4827b79f5196489f8a14201` |
| Ledger | `1cb83917a414c46c64ba9060dcb9c0b1650f344487e35f8850ac8251f8f28c24` |
| Primary record | `76a97150550a2718597d349bc7a58771face556473a1a2da3ddfd07d8a880244` |

The firewall stayed closed for every other process. This process set `AIVD_F2_AUTHORIZED=1` before measuring. The ledger was hashed before the reveal file was written. Replay matched the stored observations.

12 candidates were measured. 8 signatures were complete. 4 were incomplete, all Micro, and none of those became a dimension. The sample produced 53 `VALID_OUTPUT`, 20 `VALID_IDENTITY`, and 23 `INVALID_EXECUTION` observations. It produced no `AMBIGUOUS` and no `EXECUTION_FAILURE`.

| Condition | Dimensions | New | Equivalent | Insufficient |
|---|---:|---:|---:|---:|
| X1 Micro | 4 | 4 | 0 | 4 |
| X2 CEL | 3 | 3 | 1 | 0 |
| X3 shared | 6 | 6 | 2 | 4 |

The one cross-language match is `m00` = `TOK` and `c01` = `input`. Both returned the input string on all eight probes, so they share one dimension. That is equivalence on this bank, not equivalence for every possible input.

The other complete cross-language pairs are distinct. In particular `CAT(TOK|TOK)` and `input + input` do not match. The two CEL expressions that concatenate `input` three times do match each other. `input + input` does not match that triple.

Controls: C1 pass, C2 pass, C3 pass, C4 pass, C5 pass, C6 pass. Replay: `MATCH`.

The permitted claim is that these Micro and CEL observations were behaviorally equivalent, or distinct, on the frozen probe bank under the preregistered normalization. It is not a claim about every string, and it is not a security result. Every dimension remains `UNEVALUATED` for security.
