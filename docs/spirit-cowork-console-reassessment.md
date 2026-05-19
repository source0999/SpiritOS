# Spirit Cowork Console Reassessment

Status date: 2026-05-18
Status: decision document only

## Purpose

This document decides whether Spirit Cowork Console is still needed after the `/coding` operator console matured during Source Proxy hardening.

No Cowork Console was built for this reassessment. No source code was changed for this reassessment.

## Decision

Do not build a separate Spirit Cowork Console now.

Merge useful Cowork ideas into `/coding` over time only when they are backed by real Source Proxy contracts.

## Why

`/coding` now covers the important operator-console jobs:

- read-only unified task queue
- task status and blockers
- artifact/evidence shelf
- Codex evidence display
- diff preview and reviewer/verifier cards
- approval guard checklist
- post-apply verification status
- commit and push blocking evidence
- task history lanes
- multi-worker evidence lanes
- mobile-friendly manual-check workflow through Codex mobile and SSH

The missing Cowork-style features are mostly polish or future orchestration, not a reason to fork the interface.

## Remaining Gaps

These can be added to `/coding` later if they remain useful:

- better live step streaming
- richer task search/filtering
- notification lane for blocked tasks
- provider configuration summary
- cost/token accounting for paid providers
- replayable evidence bundles with stronger UX
- optional split-pane history for long sessions

These should not be added yet:

- autonomous provider tasks
- scheduled provider writes
- separate apply controls per worker
- separate commit or push controls per worker
- Cowork-specific provider marketplace
- AionUi bridge

## Comparison

| Cowork Goal | `/coding` Current State | Decision |
| --- | --- | --- |
| See active work | Unified task queue and task history lanes exist. | Keep in `/coding`. |
| See worker responsibility | Agent transcript and worker evidence lanes exist. | Keep in `/coding`. |
| Review evidence | Artifact shelf, Codex evidence, verifier/reviewer cards exist. | Keep in `/coding`. |
| Approve safely | Approval guard and Source Proxy gates exist. | Keep in `/coding`; do not duplicate. |
| Track commit/push readiness | Cartographer and post-apply evidence expose blockers. | Keep in Source Proxy/Cartographer. |
| Manage providers | Provider capability registry is recommendation-only. | Do not build Cowork provider controls yet. |
| Mobile operation | Codex mobile and SSH runbook cover review flow. | Keep review-only. |

## Build/Borrow/Drop

Build now:

- nothing for a separate Cowork Console

Borrow into `/coding` later:

- clearer timeline labels
- compact task cards
- richer evidence filtering
- blocked-task notification language

Drop for now:

- separate Cowork Console app
- separate provider control plane
- any worker-specific apply/commit/push UI

## Safety Boundary

This reassessment does not authorize:

- new routes
- source code changes
- provider adapter implementation
- AionUi integration
- scheduled tasks
- autonomous writes
- apply, commit, or push controls

Any future Cowork-like feature must preserve Source Proxy authority:

- review does not equal approval
- approval does not equal apply
- apply does not equal commit
- commit does not equal push
- push requires separate approval

## Recommendation

Keep `/coding` as the operator console.

Reassess a separate Cowork Console only if `/coding` becomes too crowded after daily-use alpha, and only with a concrete list of workflows that cannot fit inside the existing Source Proxy console.

## Manual Check

```bash
cd /home/source/SpiritOS
sed -n '1,260p' docs/spirit-cowork-console-reassessment.md
grep -n "Do not build a separate Spirit Cowork Console now\\|Keep .*/coding.*operator console\\|does not authorize" docs/spirit-cowork-console-reassessment.md
git diff --check
```

Expected output:

- decision document only
- decision says no separate Cowork Console now
- `/coding` remains the operator console
- no source code changed by this reassessment
- `git diff --check` has no output

## Rollback

```bash
git restore docs/spirit-cowork-console-reassessment.md docs/source-proxy-production-hardening-plan.md
```
