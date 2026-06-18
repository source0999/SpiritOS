# Danger Scan

Scanner: Python literal text scanner to avoid shell interpretation of dangerous pattern strings.

Raw output: `raw/20-danger-scan.txt` and `raw/20-danger-scan-installed-and-drafts.txt`.

## Verdict

`GO`: no real executable dangerous behavior was found in the installed watcher scripts.

## Findings Explained

- Draft README contains safety prose saying watchers do not restart/kill/dump env.
- Draft shebang lines matched `env`; this is interpreter selection, not environment dumping.
- Draft boot postmortem reads historical `last -x reboot shutdown`; this is log inspection, not reboot/shutdown execution.
- Draft model guard included `systemctl show ollama -p Environment`; this was not used for the installed script because the task forbids env dumps.
- Installed model guard contains only the phrase `no environment dump`; no environment command is run.

## Raw Matches

```text
docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/README.md:3:These files are drafts only. They are not installed, not executable by chmod from this phase, and not copied into `scripts/`. If approved later, install outside the repo and write logs under `/mnt/spirit-8tb/spiritos-health/`. They do not restart services, kill processes, mutate media, or dump environment variables.
docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-boot-postmortem.sh:1:#!/usr/bin/env bash
docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-boot-postmortem.sh:18:run last -x reboot shutdown
docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-host-health-snapshot.sh:1:#!/usr/bin/env bash
docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-model-storage-guard.sh:1:#!/usr/bin/env bash
docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-model-storage-guard.sh:15:echo "OLLAMA_MODELS path evidence only; no env dump."
docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-model-storage-guard.sh:16:run systemctl show ollama -p Environment -p FragmentPath
docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-repo-bloat-report.sh:1:#!/usr/bin/env bash
docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts/spiritos-service-health-snapshot.sh:1:#!/usr/bin/env bash
scripts/spiritos-health/spiritos-model-storage-guard.sh:14:  echo "OLLAMA model storage evidence only; no environment dump."
```
