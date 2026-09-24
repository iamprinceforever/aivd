# F1 result

**F1 DEMONSTRATED**

The discovery ledger, written before the lock, recorded 16 measurements: 8 complete signatures, 8 incomplete, 7 new dimensions, and 1 repeat of a dimension already stored in that run. The evaluator then replayed the sealed programs. Every recorded output matched. The ledger was not modified.

The repeat is `h0004`, which received the same dimension handle as `h0000`. The discovery process did not know either body. After the lock, `h0000` was `REV(TOK)`. The other new bodies were `TOK`, `AT:0`, `AT:-1`, and three concatenations. None of those names was an input. One concatenation contains a slice subexpression. It was not selected for that. The historical doubled construction was not generated as a target and was not supplied.

The seed was not written to disk. The evaluator checked that regenerating from the seed reproduced the ciphertext, then discarded the seed. A later party cannot reopen this draw. The check itself passed.

| Condition | Result |
|---|---|
| candidate sealed before experiment | PASS |
| candidate body hidden | PASS |
| experimenter lacked decryption key | PASS |
| candidate not target-selected | PASS |
| target not provided | PASS |
| probe bank frozen before reveal | PASS |
| complete signature | PASS |
| signature distinct | PASS |
| new dimension before reveal | PASS |
| semantic name absent | PASS |
| discovery lock before reveal | PASS |
| post-reveal confirmation | PASS |
| no target leakage | PASS |

F2, F3, and F4 were not run and are not claimed. Stage E was not modified.
