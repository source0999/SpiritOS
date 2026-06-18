# Manual Run Results

Verdict: `GO`

All five read-only watcher scripts were manually run once and exited `0`.

## Runtime Health Logs Created

- `/mnt/spirit-8tb/spiritos-health/spiritos-host-health-snapshot.sh.2026-06-18T19-39-22-04-00.log`
- `/mnt/spirit-8tb/spiritos-health/spiritos-service-health-snapshot.sh.2026-06-18T19-39-37-04-00.log`
- `/mnt/spirit-8tb/spiritos-health/spiritos-boot-postmortem.sh.2026-06-18T19-39-39-04-00.log`
- `/mnt/spirit-8tb/spiritos-health/spiritos-model-storage-guard.sh.2026-06-18T19-40-14-04-00.log`
- `/mnt/spirit-8tb/spiritos-health/spiritos-repo-bloat-report.sh.2026-06-18T19-40-15-04-00.log`

## Verified Behavior

- logs were written under `/mnt/spirit-8tb/spiritos-health/`
- no service restart
- no process kill
- no Docker mutation
- no media mutation
- no Jellyfin mutation
- Source Proxy liveness used `/docs` and `/openapi.json`
- Next liveness used HTTPS `/spiritflix/admin`
- Ollama `/api/tags` and `/api/ps` worked
- known `spirit-whisper` unhealthy and Docker missing-curl healthcheck issue were recorded, not fixed

Raw wrapper outputs are in `raw/manual-runs/`.
