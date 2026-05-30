# Windows Node Backup Final Closeout

Date: 2026-05-29

Status: GO

## Approved Windows Backup Paths

- `C:\Projects`
- `C:\Users\smith\OneDrive\Documents\spiritAgent`

## Repository

Windows-accessible restic repository:

```text
sftp:source@10.0.0.186:/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-windows
```

## Proof

- Windows restic installed: GO
- Windows SSH to Dell/source: GO
- Windows SFTP restic repo initialized: GO, repo `d6a37f7745`
- First real Windows backup: GO, snapshot `83c72fd5`
- Isolated restore proof: GO

## Restore Proof

Snapshot `83c72fd5` restored the known non-secret planner file:

```text
/C/Projects/SpiritOS-full/scripts/backups/spiritos-backup-windows.ps1
```

into isolated target:

```text
C:\Projects\spiritos-restore-drills\windows-node-83c72fd5-retry2
```

Restore summary:

```text
Summary: Restored 6 / 1 files/dirs (1.268 KiB / 1.268 KiB) in 0:00
```

## Safety

- No file contents were printed.
- No secrets were printed.
- No timers were installed.
- No cloud sync ran.
- No pruning/deletion/forget ran.
- No containers were stopped/restarted.
- No commit/push ran.
