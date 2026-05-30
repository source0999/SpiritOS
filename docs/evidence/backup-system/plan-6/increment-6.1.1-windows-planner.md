# Increment 6.1.1 Windows PowerShell Planner

Date: 2026-05-29

Artifact: `scripts/backups/spiritos-backup-windows.ps1`

Checks run:

- `grep -n "C:\\\\Projects\|DryRun\|RESTIC\|APPROVAL" scripts/backups/spiritos-backup-windows.ps1`: PASS
- `git diff --check`: PASS
- Optional `pwsh` parse check: skipped because `pwsh` was not available, or returned no output through the optional guarded command.

Result: GO. Script is scoped to `C:\Projects`, dry-run by default, and does not browse the whole machine.
