# Increment 2.3 Start Container

Purpose:

- Start Jellyfin after compose validation.

Commands:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml up -d
docker compose -f services/jellyfin/docker-compose.yml ps
docker inspect spirit-jellyfin --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
docker logs --tail 80 spirit-jellyfin
curl -I http://127.0.0.1:8096 || true
ss -tlnp | grep -E '(:8096)\b' || true
```

Result summary:

```text
Container spirit-jellyfin Started
spirit-jellyfin   jellyfin/jellyfin:latest   Up 58 seconds (healthy)   0.0.0.0:8096->8096/tcp, [::]:8096->8096/tcp
running healthy
HTTP/1.1 302 Found
Location: web/
LISTEN 0 4096 0.0.0.0:8096
LISTEN 0 4096 [::]:8096
```

Log summary:

- Jellyfin database migrations completed.
- Cache path is `/cache`.
- Kestrel is listening.
- FFmpeg was found.
- Core startup completed.

Manual check:

- `spirit-jellyfin` is running and healthy.
- Local HTTP responds on `127.0.0.1:8096`.
- No public DNS, router forwarding, Tailscale Serve, Tailscale Funnel, firewall rule, or SpiritOS `/media` UI change was made.

Rollback:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml down
```

Status: GO
