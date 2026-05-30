# Increment 2.1.3 Backup Candidate Manifest Generator

Date: 2026-05-29

Artifact: `scripts/backups/spiritos-backup-manifest.sh`

Checks run:

- `bash -n scripts/backups/spiritos-backup-manifest.sh`: PASS
- `scripts/backups/spiritos-backup-manifest.sh --dry-run | head -200`: PASS
- Candidate grep for runtime, rebuildable, Mac, and Windows paths: PASS
- `git diff --check`: PASS

Result: GO. Manifest includes runtime candidates, Docker candidates, Mac/Windows candidates, rebuildable exclusions, and unsafe secret-content exclusions.
