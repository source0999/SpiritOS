# Scout v0.7 Phase 0.4 Review Evidence Grouping Plan

status: planning/manual-controlled

Status date: 2026-05-20

This document plans Scout v0.7 review evidence grouping after the manual gate copy audit and live Scout refresh check. It is planning only. It does not call proxy intake, does not emit actual receipts, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Current Live Checkpoint

The latest Scout soak snapshot was written at:

- `scout/soak-logs/scout-soak-snapshot-2026-05-20T042739Z.json`

Observed live state:

- health status: `200`
- Scout status: `observing`
- active sources: `7`
- pollable sources: `5`
- stored-only sources: `2`
- source candidates: `approved 4`, `recommended 10`, `needs_review 2`, `rejected 1`, `blocked 1`, `stored 0`
- discovery jobs: `5`
- discovery execution: `manual_controlled`
- `automatic_execution: false`
- `worker_registered: false`
- packet synthesis: ready
- backlog: `0`
- closeout mode: `dry_run_only`
- proxy memory writes: `false`
- coding context writes: `false`
- promotion finalization: `false`

Dashboard and `/intelligence` now both use live no-store Scout reads for sources, source candidates, and discovery jobs, and both surfaces display live refresh copy.

## Goal

Plan a small read-only grouping layer that helps the operator scan review evidence faster without changing Scout authority.

The grouping should make it obvious whether a row is:

- existing manual state
- recommended review evidence
- risk evidence
- provenance evidence
- action history
- dry-run-only import evidence

## Proposed Groups

### Source Candidate Evidence

Group existing fields into:

- Review priority: recommended review order, why this first, risk reason
- Trust and source type: trust label, source kind, source origin, poller support
- Provenance: discovered from URI, artifact path, discovery job ID
- Manual state: current status, reviewed by, reviewed at, review history
- Manual next action: manual approve, manual reject, manual block

### Packet Evidence

Group existing fields into:

- Review priority: recommended review order, why this first, risk reason
- Source evidence: source label, source trust, artifact path, synthesized at
- Quality evidence: confidence, quality, findings
- Manual promotion state: queued, approved, rejected, promotion reason
- Manual next action: queue promotion, recheck, manual promote, manual reject

### Discovery Evidence

Group existing fields into:

- Search plan: query, topic anchor, max results, budget
- Manual execution state: status, computed status, safe next action
- Safety boundary: preview does not activate sources, extraction creates candidates only
- Manual next action: manual preview search, manual extract candidates, manual pause plan, manual resume plan

### Import Dry-Run Evidence

Group existing fields into:

- Dry-run status: blocked or passed
- Receipt preview: event, imported in dry run, applied in dry run
- Write flags: proxy memory, coding context, active context, append-only evidence
- Rollback preview: tombstone event, delete allowed
- Safety boundary: no proxy intake, no real receipt, no promotion finalization

## Candidate Implementation Shape

Do not implement in this phase.

If later approved, the smallest implementation should:

- add local UI helper functions only
- reuse existing fields already fetched by the dashboard and Scout page
- avoid new API routes
- avoid new database writes
- avoid new background workers
- keep every mutation-capable action labeled manual
- keep import dry-run-only

Likely files for a later approved implementation:

- `src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`
- `src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`
- optional docs closeout file

## Safety Boundary

This plan does not authorize:

- proxy intake calls
- append-only intake writes
- actual receipt emission
- automatic promotion finalization
- proxy memory writes
- coding context writes
- active context writes
- hidden background workers
- scheduled writes
- automatic packet promotion
- automatic source approval
- automatic source rejection
- automatic source blocking
- source activation
- discovery execution without an operator click
- candidate extraction without an operator click
- apply actions
- commits
- pushes
- self-promotion to a higher autonomy level

## Acceptance Criteria

A later implementation can pass only if:

- it is read-only except existing manual button handlers
- UI copy does not overclaim autonomy
- all mutation-capable actions remain labeled manual
- Scout-to-Proxy import remains parked
- closeout remains `dry_run_only`
- proxy memory writes remain false
- coding context writes remain false
- promotion finalization remains false
- source count does not change during read-only checks
- candidate counts do not change unless an external manual action happens
- widget tests pass
- closeout compressed output passes

## Manual Check

```bash
cd /home/source/SpiritOS && grep -n "Scout v0.7 Phase 0.4 Review Evidence Grouping Plan\|Source Candidate Evidence\|Packet Evidence\|Discovery Evidence\|Import Dry-Run Evidence\|scout-soak-snapshot-2026-05-20T042739Z\|Next Permission Gate" docs/scout-v0-7-review-evidence-grouping-plan.md && git diff --check && CI=1 npm run test -- HomelabScoutIntelligenceWidget && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,blocked:.closeout_summary.parked_dry_run_blocked,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected outcome:

- grouping plan exists
- latest soak snapshot path is recorded
- widget tests pass
- `git diff --check` prints nothing
- closeout compressed output returns `result: pass`
- `ready` is `true`
- `mode` is `dry_run_only`
- `proxy_memory`, `coding_context`, and `finalize` are `false`
- `unexpected` is empty
- `head_changed` is `false`

## Rollback

```bash
rm docs/scout-v0-7-review-evidence-grouping-plan.md
```

## Next Permission Gate

Operator approval is required before implementing Scout v0.7 Phase 0.5. The recommended next increment is **Scout v0.7 Phase 0.5: Diagnostics Summary Copy**, which should improve mobile diagnostics wording without changing Scout authority.
