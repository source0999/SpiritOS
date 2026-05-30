# Windows Node First Backup Approval Packet

APPROVAL REQUIRED before any real Windows backup command is run.

## Copy And Run Instructions

Run the PowerShell planner from the Windows desktop after reviewing the script:

```powershell
PowerShell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backups\spiritos-backup-windows.ps1 -DryRun
```

## Scope

The Windows backup scope is:

- `C:\Projects`
- `C:\Users\smith\OneDrive\Documents\spiritAgent`

It is not a whole-machine backup.

## Restic Repo Target On Dell

Preferred Windows-accessible SFTP target:

```text
sftp:source@10.0.0.186:/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-windows
```

Dell-local path:

```text
/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-windows
```

## Token And Secrets Warning

Do not print, copy, or transmit `.env`, tokens, private keys, certificates, or credential contents unless Britton approves that specific secret-handling gate.

## Future Approval Commands

```powershell
$env:SPIRIT_BACKUP_MODE="real"
$env:SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES="true"
$env:RESTIC_REPOSITORY="sftp:source@10.0.0.186:/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-windows"
restic -r $env:RESTIC_REPOSITORY backup --exclude node_modules --exclude .next --exclude dist C:\Projects C:\Users\smith\OneDrive\Documents\spiritAgent
```
