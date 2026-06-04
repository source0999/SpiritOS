# Increment 4.2 Firewall Diagnosis

Purpose:

- Diagnose local firewall only if MagicDNS resolves but port `8096` fails.

Commands:

```bash
cd /home/source/SpiritOS
ss -tlnp | grep -E '(:8096)\b' || true
sudo -n ufw status verbose 2>&1 || echo SUDO_UFW_STATUS_NOT_AVAILABLE_NONINTERACTIVE
tailscale ping --timeout=5s spiritdesktop || true
```

Output:

```text
LISTEN 0 4096 0.0.0.0:8096
LISTEN 0 4096 [::]:8096
sudo: a password is required
SUDO_UFW_STATUS_NOT_AVAILABLE_NONINTERACTIVE
pong from spiritdesktop (100.82.31.124) via 10.0.0.126:41641 in 1ms
```

Interpretation:

- Jellyfin is listening on port `8096`.
- Tailscale peer reachability to `spiritdesktop` works.
- `ufw` status could not be read non-interactively because sudo requires a password.
- No firewall change was needed because private Jellyfin routes already respond.

Manual check:

- No firewall rule was added.
- No public exposure was configured.

Status: GO
