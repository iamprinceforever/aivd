# F1 blind experiment

Frozen in `11357bf` before the official draw.

The discovery process drew a 32-byte seed, generated 64 Micro programs, and wrote the ciphertext and the commitment before measuring. It then measured the first 16 in generator order. It did not drop, reorder, or look up a name. The seed was sent to the evaluator on a pipe only after `LOCK` was written. The experimenter process read the ledger and the count summary. It did not read the pipe.

Memory started empty. A dimension id is the hash of the bank and the observations. Security checks were not called.

The same machine ran both processes. A person with access to that machine could have interfered. The experimenter program did not receive the seed. That is process separation, not a second party.
