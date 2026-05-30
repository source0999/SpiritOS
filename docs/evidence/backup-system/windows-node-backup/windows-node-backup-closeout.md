# Windows Node Backup Closeout

Date: 2026-05-29

Status: NO-GO

Gate stopped at:

- Phase 1 / Increment 1.1 Windows preflight.

What is ready:

- Windows planner exists at `scripts/backups/spiritos-backup-windows.ps1`.
- Planner scope has been updated after operator clarification to include:
  - `C:\Projects`
  - `C:\Users\smith\OneDrive\Documents\spiritAgent`
- Planner defaults to dry-run and does not imply whole-machine backup.
- Windows agent files exist under `scripts/spiritdesktop-windows/`.

What blocked the gate:

- No active Windows bridge configuration is present in this Dell shell.
- `SPIRIT_WINDOWS_FS_ENABLED` is not true.
- `SPIRIT_WINDOWS_FS_BASE_URL`, `SPIRIT_WINDOWS_FS_ALLOWLIST`, and `SPIRIT_WINDOWS_FS_TOKEN` are not set in this shell.
- The current PowerShell planner intentionally does not perform real backup execution in v0.1.

Follow-up operator-provided progress after this NO-GO closeout:

- Windows restic is installed.
- Windows SSH to Dell/source works.
- Windows SFTP repository target dry-run works.
- Windows restic repo `spirit-windows` was initialized at `sftp:source@10.0.0.186:/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-windows`.
- Windows first real backup snapshot `83c72fd5` was created for `C:\Projects` and `C:\Users\smith\OneDrive\Documents\spiritAgent`.
- Windows isolated restore proof was later recorded as GO in `docs/evidence/backup-system/windows-node-backup/increment-2.3-windows-restore-proof-go.md`.
- Final Windows closeout is GO in `docs/evidence/backup-system/windows-node-backup/windows-node-backup-closeout-final.md`.

Required next operator decision:

- Either run the Windows PowerShell planner/backup from the Windows desktop with an approved repo target and password handling design, or approve/configure a Dell-side Windows filesystem bridge/pull design for the approved Windows paths:
  - `C:\Projects`
  - `C:\Users\smith\OneDrive\Documents\spiritAgent`

Safety:

- No Windows backup ran.
- No Windows files were copied.
- No Windows secrets were read or printed.
- No DB dumps ran.
- No Docker volume exports ran.
- No Mac backup ran.
- No containers were stopped or restarted.
- No timers were installed.
- No cloud sync ran.
- No pruning/deletion ran.
- No commit/push ran.
