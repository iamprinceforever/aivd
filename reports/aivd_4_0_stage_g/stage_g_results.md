# AIVD 4.0 Stage G

Claim: **SOURCE-D DISCOVERY FRONTIER NOT REACHED.**

This is not Source-A. It is not an independent human corpus. It is not a security finding. The doubled-odd body was not constructed, and the generator was not told to find it or avoid it.

## What ran

A 64-member corpus was sampled from the frozen Micro grammar with seed `aivd-4.0-stage-g-source-d-v1`, then sealed. The commitment is SHA-256 over a canonical record of the protocol, the grammar version, the seed hash, the ordered handles, the ciphertext hash, and the bank hash. Encryption is an HMAC-SHA256 keystream. Handles are `sd_000001` onward. They are not derived from the body.

The public files do not contain the seed or a body key. The experimenter session has no decrypt method. Measurement and reveal ran in the same process, in that order. A process that holds `SealedCorpus` can still decrypt. Blindness is enforced on `ExperimenterSession`, not by a separate machine.

The frozen bank `12df0f9376639650fe8386deb99532c62efef629fa8ac596cfe65e35db5761e5` was executed. Stage E's constructor still refuses that bank. Stage G did not edit it. It bound the existing engine and called `characterize` and `grow`.

Budget stayed 256, split 128/128. Characterization used 128 calls, which is 16 candidates. The other 48 were not measured. Pair calls used 0. Nothing entered memory, so the frontier had no pairs. That is not a budget increase.

## What was found

| Fact | Value |
|---|---|
| Unique bodies | 64 |
| Candidates measured | 16 |
| Never measured | 48 |
| Probe results that were `NORMAL` | 58 |
| Probe results that were `AMBIGUOUS_COPY` | 70 |
| Complete signatures | 0 |
| Dimensions | 0 |
| Pair compositions | 0 |
| Security findings | 0 |

Every measured signature included at least one `AMBIGUOUS_COPY`. The frozen rule does not mint a dimension from an incomplete signature. The sampler was not changed after this result.

Discovery was locked before reveal. The reveal file did not change the ledger. No body key was written to the experimenter ledger.

## Permitted claim

A self-generated, precommitted corpus was measured without body keys on the experimenter ledger. It did not produce a behavioral dimension.

## Forbidden claims

Source-A. An independent human provider. A vulnerability. A verified finding. A blind recursive discovery. A statement that the frontier was reached.
