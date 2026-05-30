# Backup System v0.1 Master Status

Date/time: 2026-05-29T16:13:37-04:00

## Current Decision

READINESS-GO for current local backup lane proof.

Scheduler install remains a separate approval gate.

All current local backup lanes with evidence are proven GO. Scheduler install is still a separate approval gate.

## Repository

- Restic repository: `/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server`
- Restic password file path: `/home/source/.config/spiritos-backup/restic-source-server.pass`
- Password file contents must never be printed, copied into evidence, or committed.

## Snapshot Inventory

| Snapshot | Host | Tags | Lane |
|---|---|---|---|
| `12865b16` | `source-server` | none shown | Dell file-level |
| `cb127b36` | `source-server` | `spiritos-db-dump,source-server` | Dell DB dump |
| `8e09ed34` | `source-server` | `spiritos-docker-volume-export,source-server` | Dell Docker volume exports |
| `b9761b0c` | `source-server` | `spiritos-mac-node,spirit-mac-mini` | Mac node |

## Lane Status

| Lane | Status | Restore proof | Evidence |
|---|---:|---|---|
| Dell file-level | GO after repair | GO | `docs/evidence/backup-system/restore-drill-repair/restore-drill-repair-closeout.md` |
| Dell DB dump | GO | GO | `docs/evidence/backup-system/db-docker-volume-backup/db-docker-volume-backup-closeout.md` |
| Dell Docker volume exports | GO | GO | `docs/evidence/backup-system/db-docker-volume-backup/db-docker-volume-backup-closeout.md` |
| Mac node | GO | GO | `docs/evidence/backup-system/mac-node-backup/mac-node-backup-closeout-final.md` |
| Windows node | GO | GO | `docs/evidence/backup-system/windows-node-backup/windows-node-backup-closeout-final.md` |
| Ollama data | Deferred | Not applicable | Deferred from Docker volume exports |
| Timers | Not installed | Not applicable | Templates/planning only |
| Offsite mirror | Not configured | Not applicable | No cloud sync configured |
| Pruning | Not configured | Not applicable | No retention/prune policy installed |

## Restore Proof Summary

- Dell file-level restore proof: snapshot `12865b16` restored one non-secret runbook markdown file after the restore helper repair.
- DB dump restore proof: snapshot `cb127b36` restored into an isolated restore-drill directory and passed recorded integrity checks in prior evidence.
- Docker volume export restore proof: snapshot `8e09ed34` restored into an isolated restore-drill directory and passed recorded integrity checks in prior evidence.
- Mac node restore proof: snapshot `b9761b0c` restored staged Mac files into an isolated restore-drill directory.
- Windows node restore proof: snapshot `83c72fd5` restored one known non-secret planner file into an isolated Windows restore-drill directory.

## Not Yet Protected

- Ollama model/data volume `backend_ollama_data` is deferred.
- Offsite encrypted mirror is not configured.
- Retention/prune policy is not configured.
- Scheduler automation is not installed.
- Full disaster recovery has not been proven.

## Never Print Into Evidence

- `.env` or `.env.local` contents
- Restic password file contents
- SSH keys
- API tokens
- Certificates or private keys
- Database passwords
- Any secret-bearing logs or command output

## Operator Quick Answer

How backed up are we right now?

The Dell/source-server file-level lane, DB dump lane, Docker volume export lane, Mac node lane, and Windows node lane have restic snapshots plus restore proof. Ollama data, offsite mirror, pruning, and timers are not configured. The system has core local backup proof, but scheduler/offsite/retention remain future gates.
