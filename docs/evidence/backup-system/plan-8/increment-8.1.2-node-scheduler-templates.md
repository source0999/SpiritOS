# Increment 8.1.2 Mac Launchd And Windows Task Templates

Date: 2026-05-29

Artifacts:

- `docs/backup-system/templates/spiritos-backup-mac-launchd.plist.example`
- `docs/backup-system/templates/spiritos-backup-windows-task.xml.example`

Checks run:

- `grep -n "ProgramArguments\|spiritos-backup-mac" docs/backup-system/templates/spiritos-backup-mac-launchd.plist.example`: PASS
- `grep -n "PowerShell\|spiritos-backup-windows.ps1" docs/backup-system/templates/spiritos-backup-windows-task.xml.example`: PASS
- `git diff --check`: PASS

Result: GO. Templates only; no scheduler was installed.
