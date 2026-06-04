# Increment 2.2 Compose File

Purpose:

- Add a standalone compose file for Jellyfin.

Allowed files changed:

- `services/jellyfin/docker-compose.yml`
- `docs/evidence/media-server/phase-2/increment-2.2-compose-file.md`

Compose validation command:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml config
```

Validation result:

```text
name: jellyfin
services:
  jellyfin:
    container_name: spirit-jellyfin
    environment:
      JELLYFIN_PublishedServerUrl: http://127.0.0.1:8096
    healthcheck:
      test:
        - CMD-SHELL
        - curl -fsS http://localhost:8096/health || exit 1
      timeout: 10s
      interval: 30s
      retries: 5
      start_period: 1m0s
    image: jellyfin/jellyfin:latest
    ports:
      - mode: ingress
        target: 8096
        published: "8096"
        protocol: tcp
    restart: unless-stopped
```

Mount verification:

- `/mnt/spirit-8tb/services/jellyfin/config` mounts to `/config`.
- `/mnt/spirit-8tb/services/jellyfin/cache` mounts to `/cache`.
- `/mnt/spirit-8tb/services/jellyfin/transcodes` mounts to `/transcodes`.
- `/mnt/spirit-8tb/media/movies` mounts to `/media/movies` with `read_only: true`.
- `/mnt/spirit-8tb/media/tv` mounts to `/media/tv` with `read_only: true`.
- `/mnt/spirit-8tb/media/music` mounts to `/media/music` with `read_only: true`.
- `/mnt/spirit-8tb/media/anime` mounts to `/media/anime` with `read_only: true`.
- `/mnt/spirit-8tb/media/other` mounts to `/media/other` with `read_only: true`.

Manual check:

- `backend/docker-compose.yml` was not edited.
- `scout/docker-compose.local.yml` was not edited.
- `scout/docker-compose.scout.yml` was not edited.
- No `.env` or secret file was edited.
- No SpiritOS `/media` UI file was edited.

Rollback:

```bash
rm -f services/jellyfin/docker-compose.yml
rmdir services/jellyfin 2>/dev/null || true
```

Status: GO
