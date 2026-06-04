# Increment 0.3 Docker And Jellyfin Conflict Baseline

Status: GO

Command:

```bash
docker --version
docker compose version
docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' | grep -Ei 'jellyfin|8096|spirit-jellyfin' || true
ss -tlnp | grep -E '(:8096)\b' || true
```

Output:

```text
Docker version 29.4.0, build 9d7ad9f
Docker Compose version v5.1.3
```

Manual check:

- Docker is installed.
- Docker Compose is installed.
- No existing Jellyfin container, `spirit-jellyfin` container, or `8096` container/port conflict was printed.
- No Docker service start, stop, restart, install, or Compose edit was performed.

Rollback:

- Read-only. If Docker were missing, stop and ask for explicit install approval.
