# Increment 4.1 MagicDNS Route Verification

Purpose:

- Use Tailscale MagicDNS and port `8096` first.

Dell-side commands:

```bash
tailscale status --self
tailscale ip -4
tailscale status | head -40
hostname
curl -I http://127.0.0.1:8096
curl -I http://spirit:8096
curl -I http://spirit.tailb69ea6.ts.net:8096
curl -I http://100.111.32.31:8096
tailscale serve status || true
```

Dell-side output summary:

```text
100.111.32.31   spirit   linux
tailscale ip -4: 100.111.32.31
hostname: source-server
http://127.0.0.1:8096 -> HTTP/1.1 302 Found, Location: web/
http://spirit:8096 -> HTTP/1.1 302 Found, Location: web/
http://spirit.tailb69ea6.ts.net:8096 -> HTTP/1.1 302 Found, Location: web/
http://100.111.32.31:8096 -> HTTP/1.1 302 Found, Location: web/
```

Windows/Tailscale-side route check:

```text
http://spirit.tailb69ea6.ts.net:8096 -> HTTP/1.1 302 Found
http://100.111.32.31:8096 -> HTTP/1.1 302 Found
http://spirit:8096 -> failed from Windows because short name resolved to the Windows desktop, not the Dell
```

Existing Tailscale Serve status:

```text
https://spirit.tailb69ea6.ts.net (tailnet only)
|-- / proxy http://127.0.0.1:3000
```

Notes:

- Codex did not enable or change Tailscale Serve.
- Existing Tailscale Serve points at port `3000`, not Jellyfin.
- No Tailscale Funnel, public DNS, router forwarding, or firewall change was made.

Best private Jellyfin URL:

```text
http://spirit.tailb69ea6.ts.net:8096
```

Fallback private Jellyfin URL:

```text
http://100.111.32.31:8096
```

Status: PARTIAL-GO
