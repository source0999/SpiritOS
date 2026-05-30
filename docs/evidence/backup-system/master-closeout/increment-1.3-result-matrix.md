# Increment 1.3 Result Matrix

Date/time: 2026-05-29T16:10:41-04:00

## Scope

Consolidated backup lane outcomes from existing evidence. This matrix does not run any backup action and does not overclaim missing or failed lanes.

## Result Matrix

| Backup lane | GO/NO-GO | Snapshot ID or evidence pointer | Restore proof status | What was excluded/deferred | Next action |
|---|---:|---|---|---|---|
| Dell file-level | GO after repair | Snapshot `12865b16`; `docs/evidence/backup-system/first-real-dell-backup/first-real-dell-backup-closeout-final.md`; repaired by `docs/evidence/backup-system/restore-drill-repair/restore-drill-repair-closeout.md` | GO in restore drill repair gate | Secret-shaped files were excluded by backup rules; original first-real closeout was NO-GO until repair | Include in scheduler only after scheduler install gate approval |
| Dell restore drill | GO | `docs/evidence/backup-system/restore-drill-repair/restore-drill-repair-closeout.md` | GO: one non-secret runbook markdown file restored from snapshot `12865b16` | Full disaster recovery drill deferred | Schedule monthly isolated restore drill only after scheduler gate |
| DB dump | GO | Snapshot `cb127b36`; `docs/evidence/backup-system/db-docker-volume-backup/db-docker-volume-backup-closeout.md` | GO | DB dump contents were not printed; future scheduled dumps require approval/install gate | Prepare daily cadence; do not run new dump in this closeout |
| Docker volume exports | GO | Snapshot `8e09ed34`; `docs/evidence/backup-system/db-docker-volume-backup/db-docker-volume-backup-closeout.md` | GO | `backend_ollama_data` deferred; volume contents not printed | Prepare daily or every 2-3 day cadence; do not export in this closeout |
| Mac node | GO | Snapshot `b9761b0c`; `docs/evidence/backup-system/mac-node-backup/mac-node-backup-closeout-final.md` | GO | Secret-shaped files excluded from staging; live Mac files not modified | Prepare daily pull only if Mac reachable; do not pull in this closeout |
| Windows node | NO-GO | `docs/evidence/backup-system/windows-node-backup/windows-node-backup-closeout.md` | Missing | Windows bridge/config unavailable; no Windows backup ran | Operator must approve Windows-side backup or Dell-side bridge/pull design |
| Ollama data | Deferred | `docs/evidence/backup-system/db-docker-volume-backup/db-docker-volume-backup-closeout.md` | Not applicable | `backend_ollama_data` deferred as large/rebuildable and needing separate approval | Future Ollama model backup/export decision gate |
| Timers | NO-GO / not installed | Planning evidence under `docs/evidence/backup-system/plan-8/`; current closeout docs to be created | Not applicable | Scheduler install intentionally deferred | Scheduler install gate required |
| Offsite mirror | NO-GO / not configured | Planning only | Not applicable | No cloud sync/rclone/offsite mirror | Offsite encrypted mirror planning gate |
| Retention/prune | NO-GO / not configured | Planning only | Not applicable | No prune/delete/forget; no retention policy installed | Retention/prune simulation gate before any real prune gate |

## Manual Check Commands

```bash
cd /home/source/SpiritOS
grep -n "Dell file-level\|DB dump\|Docker volume\|Mac node\|Windows node\|Offsite\|Retention" \
  docs/evidence/backup-system/master-closeout/increment-1.3-result-matrix.md
git diff --check
```

## Increment Decision

GO for matrix creation.

READINESS-NO-GO remains in effect because Windows node backup is explicitly NO-GO and scheduler install has not been approved.
