# Increment 2.1 Helper Patch

Date: 2026-05-29

Patched file:

- `scripts/backups/spiritos-restore-drill.sh`

Changes:

- Default restore source now uses a proven non-secret snapshot path:
  `/home/source/SpiritOS/docs/runbooks/spiritos-backup-runbook.md`
- Restore drill target now uses a unique timestamped subfolder under:
  `/mnt/spirit-8tb/spiritos-backups/restore-drills/YYYY-MM-DD/HHMMSSZ/source-server`
- Helper refuses targets outside `/mnt/spirit-8tb/spiritos-backups/restore-drills`.
- Helper still refuses restore over `/home/source/SpiritOS`.
- Helper keeps real-restore approval gates.
- Helper checks restored file count and fails if zero files are restored.
- Helper prints restored file paths only, not file contents.

Checks run:

- `bash -n scripts/backups/spiritos-restore-drill.sh`: PASS
- `git diff -- scripts/backups/spiritos-restore-drill.sh`: PASS command execution; file is untracked in this worktree, so no tracked diff output was produced
- `git diff --check`: PASS

Result: GO. Bash syntax passes and the helper explicitly rejects zero-file restores.
