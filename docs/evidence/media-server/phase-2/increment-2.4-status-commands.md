# Increment 2.4 Status Commands

Purpose:

- Record repeatable commands for status, logs, restart, update, rollback, and health.

Allowed files changed:

- `docs/media-server/jellyfin-operations.md`
- `docs/evidence/media-server/phase-2/increment-2.4-status-commands.md`

Verification command:

```bash
sed -n '1,160p' docs/media-server/jellyfin-operations.md
```

Verification result:

- Operations doc exists.
- Status and log commands use `services/jellyfin/docker-compose.yml`.
- Health command checks `http://127.0.0.1:8096`.
- Rollback stops the standalone Jellyfin compose service.
- The doc warns not to delete `/mnt/spirit-8tb/services/jellyfin/config` without explicit approval.

Manual check:

- No backup automation was added.
- No existing service script was edited.
- No command in the doc exposes Jellyfin publicly.

Rollback:

- Delete `docs/media-server/jellyfin-operations.md` if the operations doc is wrong.

Status: GO
