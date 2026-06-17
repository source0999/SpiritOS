# Jellyfin Access

Primary private route:

```text
http://spirit.tailb69ea6.ts.net:8096
```

Fallback private route:

```text
http://100.111.32.31:8096
```

Short-name route on the Dell:

```text
http://spirit:8096
```

The short `spirit` route may not work from every device because local DNS can resolve that name differently. Use the MagicDNS FQDN above when in doubt.

This service is private Tailscale/LAN access only. Do not configure public router forwarding, Tailscale Funnel, or public DNS for this Jellyfin lane.
