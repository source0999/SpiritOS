# Mac Worker Diff And Safety

Dell source supports `mac_isolated_write_proof`: yes.

Mac checkout supports `mac_isolated_write_proof`: no.

Mac checkout path:

`/Users/spiritmac/spiritos-worker/SpiritOS`

Mac target file status:

```text
?? scripts/mac-worker/spirit-mac-worker.mjs
?? scripts/mac-worker/spirit_mac_worker.py
```

Hash comparison:

```text
Dell scripts/mac-worker/spirit_mac_worker.py: 0dce66493313b39f749442c9eae1b9e00860e4e061a06194e59980d8a5681ae8
Mac  scripts/mac-worker/spirit_mac_worker.py: a67d6dfe51acb6066b2566545371a376cf49d4ed0cd4f8297f98f95f50c68f66
Dell scripts/mac-worker/spirit-mac-worker.mjs: 5ccd1d40d061055cb53b0354682c4ecabb6591ee383d11a24662780fc35edafa
Mac  scripts/mac-worker/spirit-mac-worker.mjs: 5ccd1d40d061055cb53b0354682c4ecabb6591ee383d11a24662780fc35edafa
```

Diff truth:

- `scripts/mac-worker/spirit_mac_worker.py` differs and is untracked on Mac.
- `scripts/mac-worker/spirit-mac-worker.mjs` matches Dell content but is still untracked on Mac.

Safety decision:

`BLOCKED_HUMAN`

Reason:

The patch-2 prompt forbids overwriting remote dirty/conflicting target files. The live Mac target files are untracked, and the Python worker differs from Dell HEAD. No sync was performed.

Exact file that would need approval or cleanup before sync:

- `scripts/mac-worker/spirit_mac_worker.py`

Possible next safe actions:

- Britton approves replacing the untracked Mac worker files after backup.
- Or the Mac checkout owner stages/commits/removes/otherwise resolves the untracked worker files, then patch 2 can resume.
