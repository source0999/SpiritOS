# Watcher Staged Files

## Verification

The staged set was inspected after exact-path `git add`. It contains only:

- `scripts/spiritos-health/` approved watcher scripts
- `docs/evidence/spiritos-readonly-watchers-install-20260617/` watcher evidence

No S6 post-commit closeout file, Source Proxy evidence/files, SpiritFlix source files, media/face-organizer files, package files, repomix/headroom/tooling files, or unrelated dirty files are staged.

## `git diff --cached --name-status`

```text
A	docs/evidence/spiritos-readonly-watchers-install-20260617/00-git-status.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/00-preflight.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/10-draft-review.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/20-danger-scan.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/20-installed-scripts.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/30-installed-scripts.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/30-manual-run-results.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/40-manual-run-results.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/40-systemd-install-results.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/50-post-install-verification.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/50-systemd-install-results.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/60-post-install-verification.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/60-removal-rollback.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/70-removal-rollback.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/final-verdict.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/index.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/operator-summary.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/20-danger-scan-installed-and-drafts.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/20-danger-scan.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/20-safety-scan.json
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/21-installed-safety-scan.json
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/30-health-dir-permission-check.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/30-permission-blocker.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/31-health-dir-status.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/31-sudo-check.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/32-script-dir-check.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/50-systemd-permission-check.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/70-closeout-endpoint-check.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/80-current-runtime-probes.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/90-final-git-status.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/manual-runs/.out
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/manual-runs/spiritos-boot-postmortem.sh.out
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/manual-runs/spiritos-host-health-snapshot.sh.out
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/manual-runs/spiritos-model-storage-guard.sh.out
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/manual-runs/spiritos-repo-bloat-report.sh.out
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/manual-runs/spiritos-service-health-snapshot.sh.out
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/watcher-commit/bash-n.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/watcher-commit/danger-scan-literal.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/watcher-commit/danger-scan.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/raw/watcher-commit/systemd-status.txt
A	docs/evidence/spiritos-readonly-watchers-install-20260617/summary.json
A	docs/evidence/spiritos-readonly-watchers-install-20260617/systemd-manual-success-update.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/watcher-commit-file-list.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/watcher-commit-preflight.md
A	docs/evidence/spiritos-readonly-watchers-install-20260617/watcher-commit-verification.md
A	scripts/spiritos-health/spiritos-boot-postmortem.sh
A	scripts/spiritos-health/spiritos-health-lib.sh
A	scripts/spiritos-health/spiritos-host-health-snapshot.sh
A	scripts/spiritos-health/spiritos-model-storage-guard.sh
A	scripts/spiritos-health/spiritos-repo-bloat-report.sh
A	scripts/spiritos-health/spiritos-service-health-snapshot.sh
```

## `git diff --cached --stat`

```text
 .../00-git-status.txt                              |  62 ++++++++++
 .../00-preflight.md                                |  89 ++++++++++++++
 .../10-draft-review.md                             |  36 ++++++
 .../20-danger-scan.md                              |  32 ++++++
 .../20-installed-scripts.md                        |  17 +++
 .../30-installed-scripts.md                        |  22 ++++
 .../30-manual-run-results.md                       |  17 +++
 .../40-manual-run-results.md                       |  28 +++++
 .../40-systemd-install-results.md                  |   7 ++
 .../50-post-install-verification.md                |   5 +
 .../50-systemd-install-results.md                  |  59 ++++++++++
 .../60-post-install-verification.md                |   7 ++
 .../60-removal-rollback.md                         |  23 ++++
 .../70-removal-rollback.md                         |  22 ++++
 .../final-verdict.md                               |  86 ++++++++++++++
 .../index.md                                       |  22 ++++
 .../operator-summary.md                            |  15 +++
 .../raw/20-danger-scan-installed-and-drafts.txt    |  10 ++
 .../raw/20-danger-scan.txt                         |   9 ++
 .../raw/20-safety-scan.json                        |  81 +++++++++++++
 .../raw/21-installed-safety-scan.json              |   4 +
 .../raw/30-health-dir-permission-check.txt         |  10 ++
 .../raw/30-permission-blocker.txt                  |   5 +
 .../raw/31-health-dir-status.txt                   |   5 +
 .../raw/31-sudo-check.txt                          |   8 ++
 .../raw/32-script-dir-check.txt                    |  14 +++
 .../raw/50-systemd-permission-check.txt            |   9 ++
 .../raw/70-closeout-endpoint-check.txt             |  11 ++
 .../raw/80-current-runtime-probes.txt              |  35 ++++++
 .../raw/90-final-git-status.txt                    |  60 ++++++++++
 .../raw/manual-runs/.out                           |   2 +
 .../manual-runs/spiritos-boot-postmortem.sh.out    |   2 +
 .../spiritos-host-health-snapshot.sh.out           |   2 +
 .../spiritos-model-storage-guard.sh.out            |   2 +
 .../manual-runs/spiritos-repo-bloat-report.sh.out  |   2 +
 .../spiritos-service-health-snapshot.sh.out        |   2 +
 .../raw/watcher-commit/bash-n.txt                  |   1 +
 .../raw/watcher-commit/danger-scan-literal.txt     |  94 +++++++++++++++
 .../raw/watcher-commit/danger-scan.txt             |  89 ++++++++++++++
 .../raw/watcher-commit/systemd-status.txt          |  58 ++++++++++
 .../summary.json                                   |  64 +++++++++++
 .../systemd-manual-success-update.md               |  56 +++++++++
 .../watcher-commit-file-list.md                    |  36 ++++++
 .../watcher-commit-preflight.md                    | 128 +++++++++++++++++++++
 .../watcher-commit-verification.md                 |  49 ++++++++
 .../spiritos-health/spiritos-boot-postmortem.sh    |  29 +++++
 scripts/spiritos-health/spiritos-health-lib.sh     |  43 +++++++
 .../spiritos-host-health-snapshot.sh               |  26 +++++
 .../spiritos-model-storage-guard.sh                |  22 ++++
 .../spiritos-health/spiritos-repo-bloat-report.sh  |  28 +++++
 .../spiritos-service-health-snapshot.sh            |  25 ++++
 51 files changed, 1570 insertions(+)
```
