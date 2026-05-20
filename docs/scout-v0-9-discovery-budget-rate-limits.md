# Scout v0.9 Increment 3.3 Discovery Budget and Rate Limits

status: planning/manual-controlled

Status date: 2026-05-20

This increment defines discovery budgets and rate limits for Scout v0.9 Manual-Controlled Lane Expansion. It is documentation only. It does not implement Scout features, enable autonomy, run discovery, extract candidates, activate sources, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

## Gate Before This Increment

Manual closeout check passed before this document was written:

- `scout-v0-5-closeout` returned `result: pass`
- `read_only: true`
- `mutated: false`
- `mode: dry_run_only`
- `ready_for_next_increment: true`
- `would_write_proxy_memory: false`
- `would_write_coding_context: false`
- `would_finalize_promotion: false`
- `head_changed: false`
- `unexpected_status_delta: []`

Scout remains stable, parked, manual-controlled, and not autonomous.

## Goal

Plan conservative discovery budgets before any discovery implementation is considered. Budgets should prevent runaway discovery, reduce review noise, and keep future manual-triggered checks small enough for a human operator to inspect.

## Initial Budget Table

| Budget | Initial Planning Limit | Reason |
| --- | --- | --- |
| Source count per manual run | 1 to 3 allowlisted sources | Keeps evidence reviewable. |
| Candidate count per source | 5 maximum | Prevents a broad queue from forming. |
| Total candidates per run | 10 maximum | Keeps one run small enough for manual review. |
| Frequency | Manual-triggered only | Prevents scheduled or background discovery. |
| Runtime | 5 minutes maximum | Prevents long-running discovery work. |
| Failure limit | Stop after first source failure unless operator retries | Avoids retry loops and unclear partial state. |
| Output size | Summary plus evidence references only | Keeps review concise. |
| Mutation limit | Zero writes outside a future explicitly approved Scout-owned dry-run output | Keeps proxy memory, coding context, source state, and promotion state unchanged. |

## Rate-Limit Rules

- No scheduler may trigger discovery.
- No background worker may trigger discovery.
- One manual run must finish before another starts.
- A failed run must stop and require a human retry decision.
- A run must record its budget before it starts in any future implementation plan.
- A budget overrun must stop the run, not expand the budget automatically.
- Candidate and source counts must be visible in the review output.

## Example Budget Declaration

```yaml
budget_version: scout.v0_9.discovery_budget.v1
run_id: manual-discovery-example-001
source_count_limit: 1
candidate_count_per_source_limit: 5
total_candidate_limit: 5
frequency: manual-triggered-only
runtime_limit: 5 minutes
failure_limit: stop after first source failure
output_limit: summary plus evidence references
writes_allowed: false
execution_status: budget-only, not implemented
next_increment: 3.4 Phase 3 Closeout
```

## Stop Conditions

A future manual discovery run must stop if:

- the source is not allowlisted
- the source is paused, retired, stored-only, or blocked
- the candidate budget is reached
- the runtime budget is reached
- the first source failure occurs
- provenance is missing
- output cannot be summarized for human review
- any path would write proxy memory, coding context, active context, source state, packet state, or promotion state

## Non-Mutation Boundary

Discovery budgets do not authorize:

- scheduled discovery
- broad internet crawling
- background workers
- source activation
- candidate extraction
- packet promotion
- proxy intake calls
- proxy memory writes
- coding context writes
- active context writes
- promotion finalization
- commits
- pushes

## Manual Check

```bash
cd /home/source/SpiritOS
git status -sb
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-source-allowlist-model.md docs/scout-v0-9-discovery-budget-rate-limits.md docs/plan-index.md
grep -n "Discovery Budget and Rate Limits\|manual-triggered-only\|writes_allowed: false\|Phase 3 Closeout" docs/scout-v0-9-discovery-budget-rate-limits.md docs/scout-v0-9-next-phases-plan.md docs/plan-index.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the discovery budget and next increment.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-discovery-budget-rate-limits.md
```

## Closeout

Increment 3.3 is complete when this discovery budget and rate-limit plan is reviewed, indexed, and the closeout runner remains green.

Next increment: **3.4 Phase 3 Closeout**.
