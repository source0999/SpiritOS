# Increment 2.1 Restic Snapshot Inventory

Date/time: 2026-05-29T16:10:41-04:00

## Scope

Read restic snapshot metadata for the Dell/source-server repository.

No backup, dump, export, timer install, cloud sync, prune, delete, forget, container restart, commit, or push was run.

## Restic Environment

Repository path:

`/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server`

Password file path:

`/home/source/.config/spiritos-backup/restic-source-server.pass`

Password file contents were not read or printed.

## Commands Run

```bash
cd /home/source/SpiritOS
export RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server
export RESTIC_PASSWORD_FILE=/home/source/.config/spiritos-backup/restic-source-server.pass

restic snapshots
restic snapshots --json > /tmp/spiritos-restic-snapshots.json
python3 - <<'PY'
import json
p='/tmp/spiritos-restic-snapshots.json'
data=json.load(open(p))
for s in data:
    print(s.get('short_id'), s.get('hostname'), ','.join(s.get('tags') or []), s.get('time'))
PY

git diff --check
```

## Snapshot Inventory

| Snapshot | Host | Tags | Time | Evidence mapping |
|---|---|---|---|---|
| `12865b16` | `source-server` | none shown | `2026-05-29T14:42:27.652676075-04:00` | Dell file-level snapshot, later restore-proven by restore drill repair |
| `cb127b36` | `source-server` | `spiritos-db-dump,source-server` | `2026-05-29T14:53:35.776930075-04:00` | DB dump backup |
| `8e09ed34` | `source-server` | `spiritos-docker-volume-export,source-server` | `2026-05-29T14:55:52.349493419-04:00` | Docker volume export backup |
| `b9761b0c` | `source-server` | `spiritos-mac-node,spirit-mac-mini` | `2026-05-29T15:37:07.505209112-04:00` | Mac node backup |

## Manual Check Results

- Snapshot inventory readable: GO
- Expected tags present for DB dump GO evidence: GO
- Expected tags present for Docker volume export GO evidence: GO
- Expected tags present for Mac node GO evidence: GO
- Dell file-level snapshot present: GO; no tag shown in `restic snapshots`
- Windows node snapshot present: NO; aligns with Windows node NO-GO closeout
- Secrets printed: NO
- `git diff --check`: GO, no output

## Increment Decision

GO for repository metadata verification.

READINESS-NO-GO remains in effect because Windows node backup is not proven.
