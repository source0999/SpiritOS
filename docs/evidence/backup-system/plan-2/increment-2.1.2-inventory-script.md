# Increment 2.1.2 Read-only Inventory Script

Date: 2026-05-29

Artifact: `scripts/backups/spiritos-backup-inventory.sh`

Checks run:

- `bash -n scripts/backups/spiritos-backup-inventory.sh`: PASS
- `scripts/backups/spiritos-backup-inventory.sh --dry-run | head -120`: PASS
- `git diff --check`: PASS

Observed facts:

- Host: `source-server`
- Dell mount `/mnt/spirit-8tb`: present, ext4, about 7.3T size.
- Docker command is available.
- Secret contents were not printed by the script.

Result: GO.
