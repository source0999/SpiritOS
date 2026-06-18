# Installed Scripts

Verdict: `BLOCKED_BEFORE_CHMOD`.

The approved scripts already existed at `scripts/spiritos-health/`, but the install step could not proceed because the required runtime log root `/mnt/spirit-8tb/spiritos-health/` does not exist and `/mnt/spirit-8tb` is root-owned.

`sudo -n` requires a password, so Codex could not create/chown the approved health-log directory. The chmod/manual-run step was not completed because running watchers without the approved log path would either exit early or require an unapproved fallback path.

Raw evidence:

- `raw/30-health-dir-permission-check.txt`
- `raw/31-sudo-check.txt`
- `raw/32-script-dir-check.txt`

Installed script paths observed but not newly chmodded by this run:

- `scripts/spiritos-health/spiritos-host-health-snapshot.sh`
- `scripts/spiritos-health/spiritos-service-health-snapshot.sh`
- `scripts/spiritos-health/spiritos-boot-postmortem.sh`
- `scripts/spiritos-health/spiritos-model-storage-guard.sh`
- `scripts/spiritos-health/spiritos-repo-bloat-report.sh`
- `scripts/spiritos-health/spiritos-health-lib.sh`
