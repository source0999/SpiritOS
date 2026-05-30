# Increment 1.2 Windows SFTP Dry-Run Preflight

Date: 2026-05-29

## Scope

Recorded operator-provided Windows preflight results and updated planned Windows backup scope.

No real Windows backup ran.

## Approved Windows Backup Paths

- `C:\Projects`
- `C:\Users\smith\OneDrive\Documents\spiritAgent`

This is not a whole-machine backup.

## Operator-Provided Preflight Results

Windows restic is installed:

```text
restic 0.18.1 compiled with go1.25.1 on windows/amd64
```

Windows SSH to Dell/source works:

```text
dell-ssh-ok
```

Windows dry-run planner worked with SFTP repository target:

```text
sftp:source@10.0.0.186:/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-windows
```

Dry-run command shape was printed only. No real backup ran.

## Current Status

Dry-run preflight: GO, with follow-up fix required so the planned command expands both Windows paths instead of printing a PowerShell array placeholder.

Real Windows backup: still NO-GO until the Windows restic repository is initialized, password handling is approved, first real backup is approved, snapshot metadata is verified, and isolated restore proof is completed.

## Safety

- No Windows backup ran.
- No Windows files were copied.
- No Windows secrets were read or printed.
- No timers were installed.
- No cloud sync ran.
- No pruning/deletion/forget ran.
- No commit/push ran.
