# Increment 2.2 Windows Restore Proof Attempt 1

Date: 2026-05-29

## Scope

Recorded operator-provided isolated Windows restore proof attempt for snapshot `83c72fd5`.

Codex did not run the Windows restore command. The operator ran it manually from Windows PowerShell.

## Operator-Provided Restore Command

```powershell
$restoreTarget="C:\Projects\spiritos-restore-drills\windows-node-83c72fd5"
New-Item -ItemType Directory -Force $restoreTarget | Out-Null

restic restore 83c72fd5 --target $restoreTarget --include "C:/Projects/SpiritOS-full/scripts/backups/spiritos-backup-windows.ps1"
```

## Operator-Provided Result

```text
restoring snapshot 83c72fd5 of [C:\Projects C:\Users\smith\OneDrive\Documents\spiritAgent] at 2026-05-29 19:50:34.3483897 -0400 EDT by SPIRIT\smith@Spirit to C:\Projects\spiritos-restore-drills\windows-node-83c72fd5
Summary: Restored 0 files/dirs (0 B) in 0:00
```

Post-restore path-only listing returned no files.

## Current Status

- Windows first real backup: GO, snapshot `83c72fd5`
- Windows restore proof attempt 1: NO-GO, zero files restored

Likely next step is path-only snapshot inspection to identify the exact stored path for a known non-secret file, then retry isolated restore using that exact path.

## Safety

- Restore target was isolated under `C:\Projects\spiritos-restore-drills\windows-node-83c72fd5`.
- No live Windows project path was overwritten.
- No file contents were printed.
- No secrets were printed.
- No prune/delete/forget ran.
- No timers were installed.
