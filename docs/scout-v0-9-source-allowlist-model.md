# Scout v0.9 Increment 3.2 Source Allowlist Model

status: planning/manual-controlled

Status date: 2026-05-20

This increment defines the source allowlist model for Scout v0.9 Manual-Controlled Lane Expansion. It is documentation only. It does not implement Scout features, enable autonomy, run discovery, extract candidates, activate sources, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

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

Define how future discovery sources should be reviewed, allowlisted, paused, retired, or kept stored-only before any manual-triggered discovery implementation is considered.

This model does not create or modify source records. It is a planning boundary for later implementation review.

## Source Lifecycle Table

| State | Meaning | Allowed Action | Forbidden Action |
| --- | --- | --- | --- |
| `proposed` | Source is suggested but not trusted. | Human review only. | No fetching, activation, discovery, or candidate extraction. |
| `allowlisted` | Source is approved for a bounded future manual check. | Manual-triggered dry-run checks only after a later implementation gate. | No scheduled discovery, no automatic extraction, no auto-activation. |
| `paused` | Source is temporarily stopped. | Keep visible as stopped. | No fetching or discovery. |
| `retired` | Source is no longer used. | Historical reference only. | No new discovery or reactivation without a new decision. |
| `stored_only` | Source may be referenced but not fetched. | Manual notes and provenance only. | No network access or crawling. |
| `blocked` | Source is unsafe, unclear, or missing required evidence. | Keep blocked reason visible. | No discovery, extraction, activation, or promotion. |

## Allowlist Review Fields

| Field | Meaning |
| --- | --- |
| `source_id` | Human-readable identifier. |
| `source_name` | Name shown to the operator. |
| `source_type` | RSS, GitHub, docs page, design reference, manual note, or stored-only reference. |
| `source_url_or_ref` | URL or local/manual reference. |
| `lifecycle_state` | One of the source lifecycle states. |
| `review_reason` | Why the source is being considered. |
| `risk` | Provenance, freshness, safety, quality, license, or noise concern. |
| `allowed_future_action` | Explicit future action, usually manual dry-run review only. |
| `forbidden_actions` | Actions that remain blocked. |
| `reviewed_by` | Operator or reviewer name if later implemented. |
| `reviewed_at` | Review date if later implemented. |
| `writes_allowed` | Must remain `false` for this planning phase. |

## Example Source Record

```yaml
allowlist_model_version: scout.v0_9.source_allowlist.v1
source_id: design-reference-example-001
source_name: Manual dashboard reference
source_type: stored-only reference
source_url_or_ref: user-provided screenshot or note
lifecycle_state: stored_only
review_reason: Preserve provenance for a later design-system review.
risk: Reference may be stale, incomplete, or missing mobile and focus-state evidence.
allowed_future_action: manual review only
forbidden_actions:
  - scheduled discovery
  - broad crawling
  - automatic candidate extraction
  - source activation
  - packet promotion
  - proxy memory writes
  - coding context writes
reviewed_by: needs verification
reviewed_at: needs verification
writes_allowed: false
execution_status: model-only, not implemented
next_increment: 3.3 Discovery Budget and Rate Limits
```

## Source Review Rules

- Every source must have a lifecycle state before future discovery is considered.
- `allowlisted` does not mean autonomous or scheduled.
- `stored_only` means no network access.
- `blocked` must include a reason before any later reconsideration.
- A later implementation plan must define how source state is stored and rolled back before any source records are written.
- No source may become active because of a model summary, packet rank, UI render, dashboard refresh, or scheduler.

## Non-Mutation Boundary

The source allowlist model does not authorize:

- creating source records
- changing source state
- source activation
- discovery execution
- candidate extraction
- packet promotion
- proxy intake calls
- proxy memory writes
- coding context writes
- active context writes
- promotion finalization
- scheduled writes
- hidden workers
- commits
- pushes

## Manual Check

```bash
cd /home/source/SpiritOS
git status -sb
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-manual-triggered-discovery-boundary.md docs/scout-v0-9-source-allowlist-model.md docs/plan-index.md
grep -n "Source Allowlist Model\|stored_only\|blocked\|writes_allowed: false\|Discovery Budget and Rate Limits" docs/scout-v0-9-source-allowlist-model.md docs/scout-v0-9-next-phases-plan.md docs/plan-index.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the source lifecycle model and next increment.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-source-allowlist-model.md
```

## Closeout

Increment 3.2 is complete when this source allowlist model is reviewed, indexed, and the closeout runner remains green.

Next increment: **3.3 Discovery Budget and Rate Limits**.
