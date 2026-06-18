# Watcher Commit File List

## Eligible Watcher Files Found

- `scripts/spiritos-health/spiritos-host-health-snapshot.sh`: present
- `scripts/spiritos-health/spiritos-service-health-snapshot.sh`: present
- `scripts/spiritos-health/spiritos-boot-postmortem.sh`: present
- `scripts/spiritos-health/spiritos-model-storage-guard.sh`: present
- `scripts/spiritos-health/spiritos-repo-bloat-report.sh`: present
- `scripts/spiritos-health/spiritos-health-lib.sh`: present
- `docs/evidence/spiritos-readonly-watchers-install-20260617/`: present

## Explicitly Excluded From This Commit

- `docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617/s6-commit-closeout.md`
- `docs/evidence/repo-host-cleanup-stability-audit-20260617/`
- `docs/evidence/repo-cleanup-manifest-watchers-20260617/`
- `docs/evidence/live-hiccup-triage-20260617/`
- `docs/evidence/source-proxy-*`
- `docs/media/spiritflix-smart-tagging-rename-plan.md`
- `src/`
- `source_proxy/`
- `scripts/media/`
- `package.json`
- `package-lock.json`
- `repomix.config.json`
- `README.md`
- `any unrelated dirty file`

## Missing Required Files

None

## Scope Note

This commit is limited to `scripts/spiritos-health/` watcher scripts and `docs/evidence/spiritos-readonly-watchers-install-20260617/` evidence. Systemd unit files under `/etc/systemd/system/` are outside the repo and cannot be committed.
