# Scout v0.9 Increment 3.1 Manual-Triggered Discovery Boundary

status: planning/manual-controlled

Status date: 2026-05-20

This increment defines the manual-triggered discovery boundary for Scout v0.9 Manual-Controlled Lane Expansion. It is documentation only. It does not implement Scout features, enable autonomy, run discovery, extract candidates, activate sources, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

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

Prepare controlled discovery without turning discovery on automatically. This boundary makes future discovery reviewable, manually triggered, bounded, and easy to stop before any implementation is considered.

## Manual-Triggered Boundary

Discovery can only be considered later if all of these are true:

- an operator explicitly starts the run
- the source is already allowlisted by a separate future gate
- the run has a named purpose
- the run has a small budget
- the output is advisory or dry-run only
- failures stop the run instead of retrying indefinitely
- no source, packet, proxy memory, coding context, or promotion state is mutated

## Forbidden Triggers

Discovery must not start from:

- a scheduler
- a cron job
- a background worker
- application startup
- UI render
- dashboard refresh
- source save
- packet creation
- summary generation
- ranking update
- model output
- another agent's suggestion

## Required Future Run Declaration

Any later implementation plan for manual discovery must define a run declaration before code is written:

| Field | Meaning |
| --- | --- |
| `run_id` | Human-readable dry-run identifier. |
| `triggered_by` | Operator or explicit approved UI action. |
| `source_allowlist_ref` | Reference to the approved source record. |
| `purpose` | Why the run is being requested. |
| `candidate_budget` | Maximum candidates to inspect. |
| `time_budget` | Maximum runtime. |
| `failure_limit` | When the run must stop. |
| `writes_allowed` | Must remain `false` for this planning phase. |
| `execution_status` | Must say dry-run or not implemented until a later gate. |

## Example Run Declaration

```yaml
discovery_boundary_version: scout.v0_9.manual_discovery_boundary.v1
run_id: manual-discovery-example-001
triggered_by: named operator approval
source_allowlist_ref: future allowlist entry, not created here
purpose: inspect one approved source for reviewable design-system references
candidate_budget: 5
time_budget: 5 minutes
failure_limit: stop after first source failure
writes_allowed: false
execution_status: boundary-only, not implemented
next_increment: 3.2 Source Allowlist Model
```

## Non-Mutation Boundary

Manual-triggered discovery planning does not authorize:

- scheduled discovery
- background workers
- source activation
- broad internet crawling
- automatic candidate extraction
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
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-phase-2-closeout.md docs/scout-v0-9-manual-triggered-discovery-boundary.md docs/plan-index.md
grep -n "Manual-Triggered Discovery Boundary\|Forbidden Triggers\|writes_allowed: false\|Source Allowlist Model" docs/scout-v0-9-manual-triggered-discovery-boundary.md docs/scout-v0-9-next-phases-plan.md docs/plan-index.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the manual-triggered boundary and next increment.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-manual-triggered-discovery-boundary.md
```

## Closeout

Increment 3.1 is complete when this manual-triggered discovery boundary is reviewed, indexed, and the closeout runner remains green.

Next increment: **3.2 Source Allowlist Model**.
