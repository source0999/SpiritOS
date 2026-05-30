# Increment 7.1.1 Restore Drill Helper

Date: 2026-05-29

Artifact: `scripts/backups/spiritos-restore-drill.sh`

Checks run:

- `bash -n scripts/backups/spiritos-restore-drill.sh`: PASS
- `scripts/backups/spiritos-restore-drill.sh --dry-run | head -160`: PASS
- Grep for restore-drills, refuse, overwrite, approval guard path, and restic restore planning: PASS
- `git diff --check`: PASS

Observed facts:

- Dry-run target: `/mnt/spirit-8tb/spiritos-backups/restore-drills/2026-05-29/source-server`
- Helper refuses overwrite if target exists.
- Helper refuses restore over `/home/source/SpiritOS`.
- No restore was performed.

Result: GO.
