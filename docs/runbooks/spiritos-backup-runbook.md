# SpiritOS Backup Runbook

## Purpose

Run a dry-run-first backup process for SpiritOS source, docs, runtime data, Docker/database state, Mac support-node state, and Windows project state.

## What Is Protected

- Source and docs: repo source, scripts, runbooks, evidence, config examples, compose files, receipts, and logs.
- Runtime data: `.spirit-backups`, `source_proxy/.spirit-backups`, `source_proxy/data`, Scout runtime data, backend runtime data, and SearXNG runtime data.
- Docker/database state: planned database dumps and Docker named volume exports after approval.
- Node state: Mac worker checkout and Windows `C:\Projects` scope.

## What Is Excluded

- Rebuildable files such as `node_modules`, `.next`, `dist`, caches, and Repomix output.
- Secret contents by default. Secret paths may be recorded by name/presence only.
- Whole-machine Windows scans.

## First Manual Backup Gate

The first real Dell backup requires explicit Britton approval for installing missing tools, initializing the restic repo, creating target directories on `/mnt/spirit-8tb`, and running `restic backup`.

## Restore Drill

Before declaring the first backup usable, run an approved restore drill into an isolated `/mnt/spirit-8tb/spiritos-backups/restore-drills/YYYY-MM-DD/` path and record evidence.

## Critical Action Approval Checklist

- Install tools
- Initialize restic repo
- Read or copy secrets
- Dump live databases
- Export Docker volumes
- Stop or modify containers
- Run real backup or restore
- Install timers
- Prune, delete, expire, or clean backups
- Sync cloud/offsite
- Commit or push

## Maintenance Plan

Daily: dry-run inventory review and mount health check.

Weekly: approved backup run and snapshot list, once v0.1 is promoted.

Monthly: approved restore drill and operator evidence review.

No automation is installed by this runbook.
