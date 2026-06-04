# Increment 4.3 Optional Tailscale Serve

Purpose:

- Decide whether to add a cleaner private HTTPS route after plain MagicDNS works.

Read-only command:

```bash
tailscale serve status || true
```

Output:

```text
https://spirit.tailb69ea6.ts.net (tailnet only)
|-- / proxy http://127.0.0.1:3000
```

Decision:

- Do not change Tailscale Serve in this Jellyfin execution.
- Existing Tailscale Serve points to port `3000`, not Jellyfin.
- Use plain private Jellyfin route `http://spirit.tailb69ea6.ts.net:8096`.

Manual check:

- No Tailscale Serve command was run to point HTTPS at Jellyfin.
- No Tailscale Funnel, public DNS, router forwarding, or firewall change was made.

Status: GO_NO_CHANGE
