# Restore Drill Checklist

1. Choose a snapshot with `restic snapshots`.
2. Restore to an isolated `/mnt/spirit-8tb/spiritos-backups/restore-drills/YYYY-MM-DD/` path.
3. Verify no overwrite risk before running the restore.
4. Compare expected files such as `docs/backup-system/backup-system-v0.1-contract.md`.
5. Record evidence, including command output and target path.
6. Closeout with GO/NO-GO and any residual risk.

The drill must not restore over `/home/source/SpiritOS`.
