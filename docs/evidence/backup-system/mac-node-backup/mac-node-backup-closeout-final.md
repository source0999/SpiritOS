# Mac Node Backup Final Closeout

Date: 2026-05-29

Status: GO

Mac preflight:

- Mac SSH works.
- Mac restic is installed: `restic 0.18.1 compiled with go1.25.1 on darwin/amd64`.
- Mac checkout exists at `/Users/spiritmac/spiritos-worker/SpiritOS`.

Dell-side staging:

- Mac checkout pulled into `/mnt/spirit-8tb/spiritos-backups/staging/spirit-mac-mini/SpiritOS`.
- Staged file count: `1534`.
- Secret-shaped excluded file count in staging: `0`.

Restic backup:

- Snapshot `b9761b0c`, tags `spiritos-mac-node,spirit-mac-mini`.

Restore proof:

- Isolated restore target: `/mnt/spirit-8tb/spiritos-backups/restore-drills/mac-node-20260529T193726Z`.
- Restored file count: `1534`.
- Restored secret-shaped excluded file count: `0`.

Safety:

- No Windows backup ran.
- No DB dumps ran.
- No Docker volume exports ran.
- No containers were stopped or restarted.
- No timers were installed.
- No cloud sync ran.
- No pruning/deletion ran.
- No commit/push ran.
- No secrets were printed.
