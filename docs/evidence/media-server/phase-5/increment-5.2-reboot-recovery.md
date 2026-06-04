# Increment 5.2 Reboot Recovery

Purpose:

- Document what to do after Dell reboots.

Allowed files changed:

- `docs/media-server/jellyfin-reboot-recovery.md`
- `docs/evidence/media-server/phase-5/increment-5.2-reboot-recovery.md`

Verification command:

```bash
sed -n '1,160p' docs/media-server/jellyfin-reboot-recovery.md
```

Verification result:

- Reboot checks include mount, container, compose status, local HTTP, and Tailscale status.
- Recovery command restarts only the standalone Jellyfin compose service.
- The doc says not to start Jellyfin if the 8 TB mount is missing.

Manual check:

- No systemd edit was made.
- No timer was installed.
- No service manager change was made.

Status: GO
