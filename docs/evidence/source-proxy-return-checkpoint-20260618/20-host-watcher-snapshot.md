# Host And Watcher Snapshot

Generated from `raw/20-host-watcher-snapshot.txt`.

## Host

- Uptime at capture: `up 23:15`
- Load average: `5.57, 7.41, 6.45`
- Memory: `15Gi` total, `6.3Gi` used, `924Mi` free, `9.2Gi` available
- Swap: `4.0Gi` total, `3.1Gi` used
- Root disk: `457G` size, `153G` available
- 8TB disk: `7.3T` size, `6.8T` available

## Watchers

- `spiritos-health-snapshot.timer`: active waiting, enabled.
- `spiritos-health-snapshot.service`: inactive after successful oneshot at `20:15:15 EDT`.
- `spiritos-boot-postmortem.service`: inactive after successful run at `19:45:47 EDT`, enabled.
- Fresh logs exist under `/mnt/spirit-8tb/spiritos-health/` at `19:39`, `19:45`, and `20:15`.

One earlier `spiritos-health-snapshot.service` failure appears at `19:44:21`, but the later `20:15` timer run exited `0/SUCCESS`.

## Failed units and warnings

- `mnt-spirit\x2dprojects.mount` remains failed.
- CasaOS has warning logs from an earlier failed start.
- Docker repeatedly logs one container healthcheck failure because `curl` is missing in that container.

## OOM/crash/stall read

No fresh `oom`, `out of memory`, or `Killed process` line was found in the captured last-four-hours grep. There is persistent Docker healthcheck noise and known failed-unit noise.

## Verdicts

- Watcher state: `GO`
- Fresh OOM/crash signs: `NONE`
- Host readiness for proxy: `PARTIAL-GO`

Host readiness is not a clean GO because the failed mount and Docker/CasaOS warning noise remain unresolved, and swap use is high enough to keep runtime reliability under observation.
