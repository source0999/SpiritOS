# Jellyfin Reboot Recovery

After Dell reboot:

```bash
findmnt /mnt/spirit-8tb
docker ps --filter name=spirit-jellyfin
docker compose -f /home/source/SpiritOS/services/jellyfin/docker-compose.yml ps
curl -I http://127.0.0.1:8096
tailscale status --self
```

If Jellyfin did not restart:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml up -d
docker logs --tail 120 spirit-jellyfin
```

If the 8 TB mount is missing, do not start Jellyfin until the mount is restored.
