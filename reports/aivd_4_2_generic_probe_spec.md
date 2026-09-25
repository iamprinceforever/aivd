# Generic probe bank

Hash: `984ebf8a66a7d6695c03d7fef75e89f20b1a839626a1337be02adabece4243a5`

The hash is SHA-256 of the canonical JSON in the companion file, without the hash field. The F1 bank is not used.

Every probe is a string. That is the value class both executors can accept and return. The empty string is excluded because Micro returns it before the program runs. Integers, booleans, and lists are excluded because Micro has no such value. A digit inside a string is still a string.

| Id | Value |
|---|---|
| p01 | `a` |
| p02 | `aa` |
| p03 | `ab` |
| p04 | `abcd` |
| p05 | `ab cd` |
| p06 | `ab ab` |
| p07 | `a1` |
| p08 | `zz zz zz` |

The engine sees the id and the generic value. The CEL adapter binds that string to the name `input`. The Micro adapter passes the same string to its executor. Neither encoding is part of the signature.

A CEL string, int, bool, or list of those is canonical. A Micro result is a canonical string. Any other CEL value is `UNSUPPORTED_OUTPUT`. Values are not stringified in order to force a match. Identity means the canonical value equals the canonical input, type included.
