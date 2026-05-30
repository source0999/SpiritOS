# Increment 2.3 Windows Restore Proof GO

Date: 2026-05-29

## Scope

Recorded operator-provided successful isolated Windows restore proof for snapshot `83c72fd5`.

Codex did not run the Windows restore command. The operator ran it manually from Windows PowerShell.

## Snapshot

`83c72fd5`

## Restored Path

Restic stored the Windows path as:

```text
/C/Projects/SpiritOS-full/scripts/backups/spiritos-backup-windows.ps1
```

## Operator-Provided Restore Command

```powershell
$restoreTarget="C:\Projects\spiritos-restore-drills\windows-node-83c72fd5-retry2"
New-Item -ItemType Directory -Force $restoreTarget | Out-Null

restic restore 83c72fd5 --target $restoreTarget --include "/C/Projects/SpiritOS-full/scripts/backups/spiritos-backup-windows.ps1"
```

## Operator-Provided Restore Result

```text
restoring snapshot 83c72fd5 of [C:\Projects C:\Users\smith\OneDrive\Documents\spiritAgent] at 2026-05-29 19:50:34.3483897 -0400 EDT by SPIRIT\smith@Spirit to C:\Projects\spiritos-restore-drills\windows-node-83c72fd5-retry2
Summary: Restored 6 / 1 files/dirs (1.268 KiB / 1.268 KiB) in 0:00
```

Path-only verification showed the restored file under:

```text
C:\Projects\spiritos-restore-drills\windows-node-83c72fd5-retry2\C\Projects\SpiritOS-full\scripts\backups\spiritos-backup-windows.ps1
```

No file contents were printed.

## Current Status

- Windows repo initialized: GO
- Windows first real backup: GO
- Windows restore proof: GO
- Windows node backup lane: GO

## Safety

- Restore target was isolated under `C:\Projects\spiritos-restore-drills\windows-node-83c72fd5-retry2`.
- No live Windows project path was overwritten.
- No file contents were printed.
- No secrets were printed.
- No prune/delete/forget ran.
- No timers were installed.
