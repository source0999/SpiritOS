# SpiritOS Backup System v0.1 Plan

Date: 2026-05-29

## Goal

Create a dry-run-first backup system for the Dell/source-server 8TB drive, Mac mini support node, and Windows desktop node. v0.1 plans and verifies backups without running real backups or restores.

## Plan Structure

1. Baseline and safety contract: inventory repo/runtime/Docker/node state and define approval gates.
2. Script foundation: shared safety helpers, read-only inventory, and backup candidate manifest.
3. Dell local wrapper: restic-first dry-run wrapper and first-backup approval packet.
4. Database and Docker preparation: dry-run database dump and Docker volume export planners.
5. Mac lane: SSH reachability, Mac path inventory, and first-backup approval packet.
6. Windows lane: scoped PowerShell planner for `C:\Projects` and approval packet.
7. Restore drill: safe dry-run restore helper and verification checklist.
8. Scheduler templates: systemd, launchd, and Windows Task Scheduler examples only.
9. Closeout: full syntax/dry-run validation and operator next-approval packet.

## Runtime Coverage Candidates

- `.spirit-backups`
- `source_proxy/.spirit-backups`
- `source_proxy/data`
- root runtime data after review
- Scout runtime data
- `backend/searxng_data`
- `backend/volumes`
- evidence, receipts, logs, compose files, and config examples
- Docker named volumes: `source_postgres_data`, `ollama_data`, `whisper_cache`, `openedai_voices`, `searxng_data`

## Exclusions

Rebuildable caches and generated artifacts such as `node_modules`, `.next`, `dist`, package caches, Repomix output, and coverage output are excluded from normal source backups.

## Safety

Default behavior is dry-run/read-only. Real backup, restore, restic repo initialization, database dump, Docker volume export, scheduler install, prune/delete, cloud sync, and secret-content handling require separate Britton approval.

## Future Offsite Mirror

rclone/offsite mirror is intentionally future optional. v0.1 does not configure or run cloud sync.
