# Source Proxy Hardening Closeout

Status date: 2026-05-18
Status: closeout receipt

## Purpose

This closeout summarizes the Source Proxy production hardening run after Increment 10.5.

This document does not open new work. It records review state, verification state, dirty-tree state, and the next safe action.

## Closeout Verdict

The hardening plan is ready for human review and consolidation.

It is not ready to merge as-is because the working tree is intentionally dirty and should be reviewed, grouped, staged, and committed deliberately.

## Completed Scope

Completed during this hardening run:

- retired `proxyCLI.md`
- established `docs/source-proxy-production-hardening-plan.md` as active plan
- clarified historical/reference/deferred plan docs
- hardened Codex route validation and authority boundaries
- improved Source Proxy closeout and regression reporting
- documented remote/manual/mobile operator flow
- improved Cartographer dirty-state, proposal, apply, commit, push, and safety reporting
- added provider capability registry as recommendation-only
- added local Ollama study without execution authority
- added read-only multi-worker evidence lanes
- documented worktree deferral
- reassessed Cowork Console, AionUi bridge, native mobile surface, scheduled provider tasks, and limited autopilot as deferred

## Authority Boundary

No completed increment authorizes:

- apply without explicit Source Proxy approval
- commit without separate approval
- push without separate approval
- Codex promotion to default worker
- provider fallback writes
- scheduled provider tasks
- native mobile execution
- AionUi bridge
- separate Spirit Cowork Console
- limited autopilot
- source edits by autopilot
- secret or certificate edits

## Latest Manual Evidence Accepted

Recent accepted checks include:

- limited autopilot design check passed
- scheduled provider tasks design check passed
- SpiritOS mobile surface decision check passed
- Cowork Console reassessment check passed
- worktree study check passed
- long-running task worker-lane tests passed
- provider registry/routing tests passed
- daily-use runbook check passed
- Cartographer proposal/safety checks passed
- Codex route and path-safety checks passed

The current closeout still requires one final consolidated verification pass before staging or commit.

## Current Dirty State

Observed before writing this closeout:

- modified files: 66
- deleted files: 1
- untracked files: 43
- docs/plan/reference files: 21
- backend files: 49
- frontend files: 26
- evidence snapshots: 14

Known expected dirty classes:

- intentional `proxyCLI.md` deletion
- active and reference docs
- Source Proxy backend hardening
- `/coding`, dashboard, and route bridge frontend updates
- Source Proxy and Cartographer tests
- Scout and Cartographer soak evidence snapshots

This dirty state is expected for review. It is a merge blocker until the changes are reviewed, grouped, and committed intentionally.

## Review Grouping Recommendation

Review in this order:

1. Active plan and reference docs.
2. Safety/verification backend contracts.
3. Cartographer API and proposal/apply/commit/push boundaries.
4. Codex adapter and evidence contracts.
5. Long-running task and worker-lane contracts.
6. `/coding`, dashboard, and route bridge UI.
7. Tests.
8. Evidence snapshots.

Keep evidence snapshots separate from source changes during review.

## Next Safe Action

Run a consolidated closeout pass.

If it passes, stop opening new feature increments and review/stage the completed hardening work.

If it fails, fix only the named closeout blocker before moving on.

## Manual Check

```bash
cd /home/source/SpiritOS
sed -n '1,260p' docs/source-proxy-hardening-closeout.md
grep -n "ready for human review and consolidation\\|not ready to merge as-is\\|No completed increment authorizes\\|Run a consolidated closeout pass" docs/source-proxy-hardening-closeout.md
git diff --check
git status --short docs/source-proxy-hardening-closeout.md docs/source-proxy-production-hardening-plan.md
```

Expected output:

- closeout says ready for review/consolidation
- closeout says not ready to merge as-is
- closeout preserves authority boundaries
- next safe action is consolidated closeout
- `git diff --check` has no output
- status shows closeout/plan docs only for this scoped check

## Final Verification Command

```bash
cd /home/source/SpiritOS
git diff --check
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile proxy-closeout
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile global-safety-regression
git status --short
```

Expected output:

- `git diff --check` has no output
- proxy closeout reports PASS or exact blockers
- global safety regression reports PASS or exact blockers
- no apply, commit, or push runs by default
- any new evidence snapshot is clearly listed

## Rollback

```bash
git restore docs/source-proxy-hardening-closeout.md docs/source-proxy-production-hardening-plan.md
```
