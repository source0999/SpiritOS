# Increment 4.4 Final Route

Purpose:

- Write the best currently verified private access route.

Allowed files changed:

- `docs/media-server/jellyfin-access.md`
- `docs/evidence/media-server/phase-4/increment-4.4-final-route.md`

Route decision:

- Best private route: `http://spirit.tailb69ea6.ts.net:8096`
- Fallback private route: `http://100.111.32.31:8096`
- Dell-local short route: `http://spirit:8096`

Verification:

```text
FQDN and Tailscale IPv4 returned HTTP/1.1 302 Found to web/ from a Tailscale-connected Windows client.
The short name spirit worked on the Dell but not from Windows due name-resolution collision.
```

Manual check still required:

- After Phase 3 is complete, log in from another Tailscale device and confirm Jellyfin opens with the configured libraries.

Status: PARTIAL-GO
