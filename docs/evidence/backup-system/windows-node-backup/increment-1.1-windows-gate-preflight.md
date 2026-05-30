# Increment 1.1 Windows Gate Preflight

Date: 2026-05-29

Scope:

- Windows node backup gate only.
- No Windows backup, copy, install, or restore was run.

Checks run:

- Config/example search for Windows telemetry and allowlist settings: PASS
- Windows PowerShell planner inspection: PASS
- Windows agent script inventory: PASS
- Process environment check for active Windows bridge configuration: PASS
- `git diff --check`: PASS

Observed config examples:

- `.env.local.example` documents:
  - `SPIRITDESKTOP_TELEMETRY_URL=http://REPLACE_WITH_WINDOWS_LAN_IP:3000/api/telemetry/self`
  - `SPIRIT_WINDOWS_FS_ENABLED=false`
  - `SPIRIT_WINDOWS_FS_BASE_URL=http://REPLACE_WITH_WINDOWS_LAN_IP:3000`
  - `SPIRIT_WINDOWS_FS_ALLOWLIST=C:\Projects`

Observed planner:

- `scripts/backups/spiritos-backup-windows.ps1` is scoped to `C:\Projects`.
- It defaults to dry-run.
- Real execution is intentionally not implemented in v0.1 planner.

Observed current Dell shell environment:

```text
SPIRIT_WINDOWS_FS_ENABLED_NOT_TRUE
SPIRIT_WINDOWS_FS_BASE_URL_NOT_SET
SPIRIT_WINDOWS_FS_ALLOWLIST_NOT_SET
SPIRIT_WINDOWS_FS_TOKEN_NOT_SET
```

Result: NO-GO.

Reason:

There is no active Windows execution or pull channel available from this Dell session. The existing Windows backup planner is designed to be run on the Windows node, and no configured Windows filesystem bridge is enabled for Dell-side discovery or pull.

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
