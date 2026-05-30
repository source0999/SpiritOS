# Increment 2.1 Windows First Real Backup

Date: 2026-05-29

## Scope

Recorded operator-provided first real Windows backup result.

Codex did not run the Windows backup command. The operator ran it manually from Windows PowerShell.

## Approved Windows Backup Paths

- `C:\Projects`
- `C:\Users\smith\OneDrive\Documents\spiritAgent`

## Repository

Windows-accessible restic repository:

```text
sftp:source@10.0.0.186:/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-windows
```

Restic password file path on Windows:

```text
C:\Users\smith\.config\spiritos-backup\restic-windows.pass
```

Password contents were not printed or recorded.

## Pre-Backup Checks

Operator-provided results:

- `Test-Path $env:RESTIC_PASSWORD_FILE`: `True`
- `restic snapshots`: repository opened; zero snapshots before first backup
- `restic check`: GO, zero snapshots, no errors found

## Operator-Provided Backup Command

```powershell
restic backup --exclude node_modules --exclude .next --exclude dist C:\Projects C:\Users\smith\OneDrive\Documents\spiritAgent
```

## Operator-Provided Backup Result

```text
Files:       11412 new,     0 changed,     0 unmodified
Dirs:         1717 new,     0 changed,     0 unmodified
Added to the repository: 577.695 MiB (530.526 MiB stored)

processed 11412 files, 872.780 MiB in 1:09
snapshot 83c72fd5 saved
```

## Current Status

- Windows repo initialized: GO
- Windows first real backup: GO
- Windows snapshot: `83c72fd5`
- Windows restore proof: NO-GO / pending

Windows node backup must not be marked full GO until isolated restore proof is completed and recorded.

## Safety

- No DB dumps ran.
- No Docker volume exports ran.
- No Mac backup ran.
- No timers were installed.
- No cloud sync ran.
- No pruning/deletion/forget ran.
- No containers were stopped/restarted.
- No commit/push ran.
- No secrets were printed.
