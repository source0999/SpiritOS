# Increment 3.1R Mac Staging Restic Backup

Date: 2026-05-29

Checks run:

- `restic backup --tag spiritos-mac-node --tag spirit-mac-mini /mnt/spirit-8tb/spiritos-backups/staging/spirit-mac-mini/SpiritOS`: PASS
- `restic snapshots`: PASS
- `git diff --check`: PASS

Observed:

```text
Files:        1534 new,     0 changed,     0 unmodified
Dirs:          328 new,     0 changed,     0 unmodified
Added to the repository: 9.814 MiB (4.268 MiB stored)
processed 1534 files, 32.620 MiB in 0:00
snapshot b9761b0c saved
```

Snapshot:

- `b9761b0c`, tags `spiritos-mac-node,spirit-mac-mini`

Result: GO. Mac staging folder was backed up into the Dell restic repo. No secrets were printed.
