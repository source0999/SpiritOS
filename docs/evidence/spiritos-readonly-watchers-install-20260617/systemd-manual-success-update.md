# Systemd Manual Success Update

Updated: 2026-06-18

## Baseline

The previous packet state was accurate at the time:

- Watcher install verdict: `PARTIAL-GO`
- Manual watcher scripts: `GO`
- Systemd timer installation: `BLOCKED` because non-interactive sudo required a password

Britton then completed the sudo/systemd installation manually from an interactive SSH terminal and provided terminal proof.

## Manual Proof Provided

- `spiritos-health-snapshot.timer`: loaded, enabled, active waiting.
- `spiritos-health-snapshot.service`: inactive dead after successful oneshot run.
- `spiritos-health-snapshot.service` ExecStart results:
  - `spiritos-host-health-snapshot.sh` exited `0/SUCCESS`
  - `spiritos-service-health-snapshot.sh` exited `0/SUCCESS`
  - `spiritos-model-storage-guard.sh` exited `0/SUCCESS`
  - `spiritos-repo-bloat-report.sh` exited `0/SUCCESS`
- `spiritos-boot-postmortem.service`: loaded and enabled.
- `spiritos-boot-postmortem.service` was manually started and exited `0/SUCCESS`.
- Boot postmortem wrote `/mnt/spirit-8tb/spiritos-health/spiritos-boot-postmortem.sh.2026-06-18T19-45-46-04-00.log`.
- New logs were written under `/mnt/spirit-8tb/spiritos-health/`.

## Updated Verdict

Watcher install verdict: `GO`

- Manual watcher scripts: `GO`
- Systemd health snapshot timer: `GO`
- Boot postmortem service: `GO`
- Automatic outage snapshots: `enabled`

## Remaining Unresolved But Not Fixed

- `mnt-spirit\x2dprojects.mount` remains failed.
- CasaOS crash/restart from prior logs remains unresolved.
- `spirit-whisper` unhealthy remains unresolved.
- Docker healthcheck missing `curl` remains unresolved.

These issues are separate from watcher install GO.

## Safety Confirmation

- no cleanup
- no app/source patch
- no process kill
- no service restart except approved watcher service starts
- no Docker mutation
- no media mutation
- no Jellyfin mutation
- no git stage/commit/push/reset/checkout/clean/stash
