# Increment 3.1R Final Dry-run

Date: 2026-05-29

Environment used:

- `RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server`
- `RESTIC_PASSWORD_FILE=/home/source/.config/spiritos-backup/restic-source-server.pass`

Checks run:

- `scripts/backups/spiritos-backup-dell.sh --dry-run | tee /tmp/spiritos-backup-dell-final-dry-run.txt`: PASS
- `grep -E "DRY|dry-run|restic|backup|exclude|/mnt/spirit-8tb" /tmp/spiritos-backup-dell-final-dry-run.txt`: PASS
- `git diff --check`: PASS

Observed:

- Dry-run mode was active.
- Planned `restic backup` command targeted `/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server`.
- Excludes were visible: `node_modules`, `.next`, `dist`, `coverage`, `.turbo`, `.cache`, `repomix-output.*`, and `*.tsbuildinfo`.
- Runtime candidate paths were printed as paths only.

Result: GO. No secret contents were printed.
