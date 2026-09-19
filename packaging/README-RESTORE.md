# AIVD 3.38.0 frozen baseline — restore

This archive is the **immutable** AIVD 3.38.0 checkout. Do not retune.
Do not convert secret firing into VERIFIED. Do not raise budget or INVENT_CAP.

## Freeze pins (must resolve)

| Role | Full SHA |
|---|---|
| Implementation freeze | `34bc665233a32a8a6f3b1f760fd65e99a37c232b` |
| Pin (no behavior change) | `6547502c4895ac0ab879359a14350cb077b28676` |
| Sacred TinyLlama first-run (HEAD) | `358ea693abdd286e3451b973877c36b7077612a5` |

Version: **3.38.0**. Model: TinyLlama. Seeds: 0,1,2,3,4,7,11. Budget: 32. INVENT_CAP: 48.

## Restore from Git bundle (preferred)

```bash
git clone aivd-3.38.0-full.bundle aivd
cd aivd
git rev-parse HEAD
# must print 358ea693abdd286e3451b973877c36b7077612a5
git cat-file -t 34bc665233a32a8a6f3b1f760fd65e99a37c232b
git cat-file -t 6547502c4895ac0ab879359a14350cb077b28676
```

## Restore from tar.gz

```bash
tar -xzf aivd-3.38.0-full.tar.gz
cd aivd-3.38.0
git rev-parse HEAD   # 358ea69…
```

Layout:
- `aivd-3.38.0/` — frozen git working tree **including `.git`**
- `aivd-3.38.0/lab/` — AIVD 3.38 lab dashboard sources (no node_modules)
- `aivd-3.38.0-full.bundle` — same Git history, also shipped inside this tar
- `AIVD_3.38_FREEZE_MANIFEST.json`
- `README-RESTORE.md` (this file)

## Reassemble split parts

If you received `*.part01`, `*.part02`, …:

```bash
cat aivd-3.38.0-full.tar.gz.part* > aivd-3.38.0-full.tar.gz
cat aivd-3.38.0-full.bundle.part* > aivd-3.38.0-full.bundle
sha256sum -c SHA256SUMS.txt
git bundle verify aivd-3.38.0-full.bundle
```

TinyLlama **weights are excluded**. Do not re-run the sacred first-run to retune.

Sacred TinyLlama first-run (immutable):
- S doubled-even (`AIVD338-LLAMA-DOUBLEEVEN`): DISCOVERED+VERIFIED 7/7 on 3.38; 0/7 on 3.37
- U reverse-each (`AIVD338-LLAMA-REVERSE`): NOT_DISCOVERED 0/7 (honest leftover-skip)
