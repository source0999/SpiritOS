# Cartographer Level 14.7 Safe Docs Evidence Maintenance Boundary

status: safe-docs-evidence-maintenance-boundary-only

Status date: 2026-05-21

Owner: Britton

## Purpose

Level 14.7 defines the future boundary for safe docs and evidence maintenance.

This increment is docs-only and does not write docs beyond this contract, write evidence, write receipts, or implement maintenance runtime.

## Starting Point

Level 14.6 defined blueprint refresh proposal boundaries.

Level 14.7 defines docs/evidence maintenance contracts only.

## Scope

Allowed:

- define future maintenance packet shape.
- define allowed future maintenance classes.
- define block rules.
- run doc-only verification commands.

Forbidden:

- evidence writes.
- receipt writes.
- runtime docs mutation.
- Source Proxy stress mutation.
- `/coding` UI mutation.
- source, API, service, test, package, or runtime edits.

## Maintenance Packet Preview

Future maintenance packets must include:

- maintenance_packet_id.
- run_id.
- maintenance_class.
- lane.
- target_files.
- allowed_files.
- forbidden_files.
- proposed_diff_preview.
- approval_required.
- verification_required.
- rollback_required.
- blocked_reason.

## Allowed Future Maintenance Classes

Future classes may include docs typo proposals, stale manual-check proposal notes, evidence index proposal notes, and closeout summary proposals.

They are proposals only unless a future approved safe-task class grants scoped write authority.

## Maintenance Block Rules

Future maintenance must block protected paths, Source Proxy stress files, `/coding` UI files without a separate lane, source code, tests, package files, APIs, services, runtime files, secrets, evidence deletion, receipt deletion, run-history deletion, cleanup, commit, push, merge, and self-approval.

## Required Future Implementation Shape

Future Level 14 work must remain incremental:

- Level 14.8: Autonomous Escalation And Closeout Proposal Boundary
- Level 14.9: Level 14 Closeout And Final Review Gate

Do not implement any of these in Level 14.7.

## Required Future Tests

Future tests must prove maintenance packets do not mutate files without scoped approval, evidence and receipts are not deleted, protected paths remain blocked, Source Proxy stress files remain blocked, `/coding` UI files remain blocked unless separately allowed, and no commit, push, merge, cleanup, or self-approval exists.

## Manual Checks

```bash
cd /home/source/SpiritOS

git status --branch --short
git rev-parse HEAD
git diff --stat
git diff --check

git diff --check -- docs/cartographer-level-14-safe-docs-evidence-maintenance-boundary.md

grep -n "Safe Docs Evidence Maintenance Boundary\|Maintenance Packet Preview\|Allowed Future Maintenance Classes\|Maintenance Block Rules\|Level 14.8: Autonomous Escalation And Closeout Proposal Boundary" docs/cartographer-level-14-safe-docs-evidence-maintenance-boundary.md

git status --branch --short
```

Do not run pytest in this docs-only increment unless a non-doc file is changed, which should not happen.

## Rollback Notes

Rollback is limited to removing:

docs/cartographer-level-14-safe-docs-evidence-maintenance-boundary.md

No source rollback, API rollback, test rollback, evidence cleanup, receipt cleanup, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or run-history cleanup should be needed because this increment is docs-only.

## Expected Outcome

Level 14.7 creates the Safe Docs Evidence Maintenance Boundary only.

No maintenance runtime, evidence writing, receipt writing, write authority, local execution authority, commit/push/merge authority, self-approval, cleanup, Source Proxy stress mutation, or `/coding` UI mutation is enabled.

## Next Increment

Level 14.8: Autonomous Escalation And Closeout Proposal Boundary
