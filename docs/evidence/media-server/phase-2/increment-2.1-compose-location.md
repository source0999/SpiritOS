# Increment 2.1 Compose Location Decision

Purpose:

- Choose a compose lane without touching existing production compose files.

Commands:

```bash
cd /home/source/SpiritOS
test -d services && echo SERVICES_DIR_EXISTS || echo SERVICES_DIR_MISSING
find . -maxdepth 3 \( -name 'docker-compose.yml' -o -name 'docker-compose.*.yml' -o -name 'compose.yml' \) -print | sort
```

Output:

```text
SERVICES_DIR_MISSING
./backend/docker-compose.yml
./scout/docker-compose.local.yml
./scout/docker-compose.scout.yml
```

Decision:

- Use the plan's standalone compose lane: `services/jellyfin/docker-compose.yml`.
- Create only `services/jellyfin/` in Increment 2.2.
- Do not edit `backend/docker-compose.yml`, `scout/docker-compose.local.yml`, or `scout/docker-compose.scout.yml`.

Manual check:

- No existing production Compose file was edited.
- No `.env` or secret file was edited.
- No SpiritOS `/media` UI file was edited.

Rollback:

- Decision-only. No rollback needed.

Status: GO
