# Backup System v0.1 Scheduler Readiness

Date/time: 2026-05-29T16:13:37-04:00

## Current Decision

READINESS-NO-GO for scheduler install.

This document prepares scheduler readiness only. It does not install timers, launchd jobs, Windows scheduled tasks, cloud sync, prune jobs, or destructive cleanup.

## Recommended Cadence

| Work item | Recommended cadence | Notes |
|---|---|---|
| Dell file-level backup | Daily | Use existing approved Dell file-level backup path and exclusions. |
| Daily DB dump backup | Daily | Requires approved dump command in scheduler install gate; do not run from this document. |
| Docker volume export | Daily or every 2-3 days | Use approved export list; keep Ollama deferred until separately approved. |
| Mac pull backup | Daily if Mac reachable | Mark stale if unreachable; do not retry destructively. |
| Windows backup | Daily if Windows reachable | Current status is NO-GO; needs approved Windows design before scheduling. |
| Weekly lightweight `restic check` | Weekly | Use `restic check` only, not `--read-data`, unless separately approved. |
| Monthly isolated restore drill | Monthly | Restore non-secret known files into isolated restore-drill paths only. |
| Future deeper restic check | Future separately approved gate | Use `restic check --read-data-subset` or `restic check --read-data` only after explicit approval. |

## Safety Gates

- Do not schedule prune yet.
- Do not schedule cloud sync yet.
- Do not schedule destructive cleanup yet.
- Do not schedule `restic forget` yet.
- Do not schedule `restic prune` yet.
- Do not schedule container restarts or service restarts as part of backups.
- Do not install any scheduler until the Scheduler Install Gate is approved.

## Required Secrets Handling

- Restic password files must stay outside the repo.
- Environment files containing secrets must stay outside committed evidence.
- Logs must not include secrets, tokens, passwords, private keys, cert contents, or `.env` contents.
- Evidence may record secret file paths only when needed, never file contents.
- Any scheduled command should fail closed if required password/env files are missing.

## Failure Behavior

- Log the failure with timestamp, lane, host, and non-secret error summary.
- Do not retry destructively.
- Do not delete partial backup artifacts automatically.
- Do not prune or forget snapshots after a failed backup.
- Mark the lane stale until a later successful backup/restore proof updates status.
- Escalate repeated failures to an operator decision gate.

## Proposed Timer Templates Only

Timer files should remain under docs/templates until the Scheduler Install Gate is approved.

Suggested template families:

- Dell systemd service/timer templates for file-level, DB dump, Docker volume export, lightweight check, and restore drill.
- Mac launchd template for an approved pull-trigger or local backup flow if chosen later.
- Windows Task Scheduler or PowerShell template for an approved Windows backup flow if chosen later.

These are templates only. They are not installed by this readiness packet.

## Scheduler Readiness Requirements Before Install

- Windows node backup design is approved and proven, or scheduler install is explicitly scoped to non-Windows lanes.
- Operator confirms the exact user account for each scheduled job.
- Operator confirms password/env file paths and permissions.
- Operator confirms log destination and rotation behavior.
- Operator confirms manual test commands for each timer before enabling it.
- Operator confirms rollback and disable instructions.

## Manual Checks for Scheduler Install Gate

- Verify restic repository path is reachable.
- Verify password file path exists without printing contents.
- Verify staging paths exist and are writable by the scheduled user.
- Verify logs path exists and is writable by the scheduled user.
- Verify each command supports dry-run or safe preflight where applicable.
- Verify no prune/cloud/destructive cleanup is bundled with scheduler install.

## Current Readiness Summary

Scheduler readiness docs can be prepared now. Scheduler installation should not proceed as an all-node backup system until Windows is resolved or explicitly excluded by a new operator-approved scheduler scope.
