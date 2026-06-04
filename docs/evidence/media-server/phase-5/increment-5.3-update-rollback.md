# Increment 5.3 Update And Rollback

Purpose:

- Document controlled update and rollback commands.

Allowed files changed:

- `docs/media-server/jellyfin-update-rollback.md`
- `docs/evidence/media-server/phase-5/increment-5.3-update-rollback.md`

Verification command:

```bash
sed -n '1,160p' docs/media-server/jellyfin-update-rollback.md
```

Verification result:

- Update commands are documented for future user-approved execution.
- Rollback options avoid deleting media.
- Stop command uses the standalone Jellyfin compose file.

Manual check:

- No image pull was run.
- No update was run.
- No automatic update tool was added.
- No media folders were deleted or moved.

Status: GO
