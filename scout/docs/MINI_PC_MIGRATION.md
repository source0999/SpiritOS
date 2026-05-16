# Mini-PC Migration

This checklist moves Scout to a second machine or VM without re-fetching source content.

## Prerequisites

- Docker and Docker Compose are installed.
- Disk has enough free space for `scout/data/`, `scout/config/`, and one compressed migration tarball.
- System clock is synchronized with NTP.
- Optional GPU profile is known in advance: `cpu`, `nvidia`, or `amd`.
- The target checkout contains the same Scout code version as the source machine.

## Checklist

1. On the source machine, from the repo root, run `bash scout/scripts/migrate.sh`.
2. Copy the printed `scout-migration-YYYYMMDDHHMM.tar.gz` file to the target machine.
3. On the target machine, place the tarball at the repo root.
4. Confirm `scout/.env` exists on the target and contains the intended local secrets.
5. Run `bash scout/scripts/restore.sh scout-migration-YYYYMMDDHHMM.tar.gz cpu`.
6. For NVIDIA hardware, use `nvidia` instead of `cpu`. For AMD hardware, use `amd`.
7. Run `curl http://localhost:8077/health`.
8. Run `curl http://localhost:8077/v1/scout/status`.
9. Confirm the status response shows scheduled jobs.
10. Scout is healthy on the new machine.

## Troubleshooting

- Clock skew can make ETag and staleness behavior look wrong. Sync the system clock before restoring.
- Host firewall rules can block loopback bridge calls. Confirm `localhost:8077` is reachable from the proxy host.
- File ownership can prevent bind mount writes. If Scout cannot create SQLite WAL files or logs, fix ownership on `scout/data/`.
- Do not start multiple profiles at once on the same host. Stop the active profile before switching CPU/GPU profiles.
