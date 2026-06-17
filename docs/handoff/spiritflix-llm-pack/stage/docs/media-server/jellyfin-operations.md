# Jellyfin Operations

Compose file:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml ps
docker compose -f services/jellyfin/docker-compose.yml logs --tail 120 jellyfin
docker compose -f services/jellyfin/docker-compose.yml restart jellyfin
docker compose -f services/jellyfin/docker-compose.yml pull jellyfin
docker compose -f services/jellyfin/docker-compose.yml up -d
docker compose -f services/jellyfin/docker-compose.yml down
```

Local health:

```bash
curl -I http://127.0.0.1:8096
docker inspect spirit-jellyfin --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
```

Rollback:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml down
```

Do not delete `/mnt/spirit-8tb/services/jellyfin/config` unless the user explicitly approves losing Jellyfin setup state.
