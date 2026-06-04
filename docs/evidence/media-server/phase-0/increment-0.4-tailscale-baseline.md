# Increment 0.4 Tailscale Baseline

Status: GO

Command:

```bash
tailscale version
tailscale status --self
tailscale ip -4
tailscale status | head -40
```

Output:

```text
1.98.3
  tailscale commit: a16e0f20cff0acd5617fd1b315df32cdad17a8fa
  long version: 1.98.3-ta16e0f20c-ge0c644472
  other commit: e0c6444725a27ff911a18cc4b18575d8700339d5
  go version: go1.26.3 (tailscale/go e877d97384)
100.111.32.31   spirit            smith.britton999@  linux    -
100.78.185.122  brittons-z-fold7  smith.britton999@  android  idle, tx 19138165240 rx 125992560
100.73.44.110   iphone171         smith.britton999@  iOS      offline, last seen 6h ago
100.117.164.42  sources-mac-mini  smith.britton999@  macOS    -
100.82.31.124   spiritdesktop     smith.britton999@  windows  active; direct 10.0.0.126:41641, tx 71317124 rx 8916316
100.111.32.31
100.111.32.31   spirit            smith.britton999@  linux    -
100.78.185.122  brittons-z-fold7  smith.britton999@  android  idle, tx 19138165240 rx 125992560
100.73.44.110   iphone171         smith.britton999@  iOS      offline, last seen 6h ago
100.117.164.42  sources-mac-mini  smith.britton999@  macOS    -
100.82.31.124   spiritdesktop     smith.britton999@  windows  active; direct 10.0.0.126:41641, tx 71318660 rx 8916620
```

Manual check:

- Tailscale is installed.
- Dell/source server is logged in as Tailscale machine `spirit`.
- Dell Tailscale IPv4 is `100.111.32.31`.
- No Tailscale login, logout, up, serve, funnel, ACL, DNS, or firewall change was performed.

Rollback:

- Read-only. If Tailscale were missing or logged out, mark later private-access work blocked until setup approval.
