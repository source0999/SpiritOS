# Jellyfin Update And Rollback

Update after user approval:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml pull jellyfin
docker compose -f services/jellyfin/docker-compose.yml up -d
docker logs --tail 120 spirit-jellyfin
curl -I http://127.0.0.1:8096
```

Rollback options:

1. If the old image is still local, pin the previous image tag in `services/jellyfin/docker-compose.yml` and run `docker compose up -d`.
2. Restore `/mnt/spirit-8tb/services/jellyfin/config` from an approved backup only if configuration corruption is confirmed.
3. Stop the service without deleting state:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml down
```

Never delete media folders as part of a Jellyfin app rollback.
