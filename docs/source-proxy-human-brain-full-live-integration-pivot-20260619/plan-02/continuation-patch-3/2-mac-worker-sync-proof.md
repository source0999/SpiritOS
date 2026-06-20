# Mac Worker Sync Proof

Backup created on the Mac:

`.spiritos-backups/plan2-patch3/scripts_mac-worker_spirit_mac_worker.py.20260620T015800.bak`

Exact file synced:

`scripts/mac-worker/spirit_mac_worker.py`

Post-sync Mac hash:

`90a40d6f33e73963a15977bf347516703f6f1a1e2be784fa4398978449d5e473`

Post-sync grep confirmed `mac_isolated_write_proof` in the Mac worker at lines including:

- supported job type
- handler function
- dispatcher branch
- structured proof reason codes

No broad rsync was used.

No other Mac worker file was replaced.
