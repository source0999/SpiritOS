# Remote Mac Worker Reconciliation

Remote checkout: `/Users/spiritmac/spiritos-worker/SpiritOS`

Remote target files observed before sync:

- `?? scripts/mac-worker/spirit_mac_worker.py`
- `?? scripts/mac-worker/spirit-mac-worker.mjs`

Evidence copied to external raw evidence before mutation:

- `/home/source/spiritos-evidence/plan-02-continuation-patch-3/remote-before/scripts/mac-worker/spirit_mac_worker.py`
- `/home/source/spiritos-evidence/plan-02-continuation-patch-3/remote-before/scripts/mac-worker/spirit-mac-worker.mjs`

Hashes:

- Dell Python worker: `90a40d6f33e73963a15977bf347516703f6f1a1e2be784fa4398978449d5e473`
- Mac Python worker before: `a67d6dfe51acb6066b2566545371a376cf49d4ed0cd4f8297f98f95f50c68f66`
- Dell Node worker: `5ccd1d40d061055cb53b0354682c4ecabb6591ee383d11a24662780fc35edafa`
- Mac Node worker before: `5ccd1d40d061055cb53b0354682c4ecabb6591ee383d11a24662780fc35edafa`

Classification:

- `scripts/mac-worker/spirit_mac_worker.py`: `REMOTE_UNTRACKED_BUT_SAFE_TO_REPLACE`; remote copy only lacked Dell `mac_isolated_write_proof` support and trace/result hardening.
- `scripts/mac-worker/spirit-mac-worker.mjs`: `SAME`; no sync needed.

No Mac git commit, push, reset, clean, pull, or checkout was performed.
