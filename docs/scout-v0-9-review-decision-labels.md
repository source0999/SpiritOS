# Scout v0.9 Increment 0.3.3 Review Decision Labels

status: planning/manual-controlled

Status date: 2026-05-20

This increment defines review decision labels for Scout v0.9 Manual-Controlled Lane Expansion. It is documentation only. It does not implement Scout features, enable autonomy, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

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

Standardize labels a human operator can use while reviewing Scout intelligence. These labels describe intent only. They do not mutate source state, packet state, promotion state, proxy memory, coding context, files, commits, pushes, or scheduled work.

## Label Table

| Label | Meaning | Allowed Use | Mutation Allowed |
| --- | --- | --- | --- |
| `needs_review` | Human has not made a decision yet. | Default queue state for unresolved items. | No |
| `useful_now` | Item is useful for the current planning, review, or prompt-drafting task. | Human may reference it manually. | No |
| `saved_later` | Item is worth retaining as reference but is not needed now. | Human may revisit it later. | No |
| `rejected` | Item is not useful, not relevant, duplicated, stale, or too weak. | Human may exclude it from current review. | No |
| `blocked` | Item cannot proceed because of safety, provenance, missing evidence, or policy boundary. | Human may require more evidence or leave it stopped. | No |
| `promoted_pending` | Item may deserve a later promotion review. | Human may create a future review task. | No |
| `approved_dry_run` | Human approves dry-run validation only. | Dry-run review may be planned, but no execution or write is authorized by the label itself. | No |

## Label Boundaries

Labels are advisory review metadata only.

Labels must not:

- approve a source
- reject or block a source in runtime storage
- activate discovery
- extract candidates
- promote packets
- finalize promotions
- call proxy intake
- write proxy memory
- write coding context
- write active context
- emit runtime receipts
- schedule work
- create background workers
- apply code
- commit
- push

## Operator Flow

1. Read the source, summary, risk, and evidence.
2. Choose one label.
3. If the label is `useful_now`, manually copy or reference the item in a human-reviewed plan or prompt.
4. If the label is `approved_dry_run`, run only a separately approved dry-run path.
5. If the label is `promoted_pending`, require a future explicit approval gate before any promotion work.
6. Keep all writes disabled unless a later implementation plan explicitly changes one bounded path.

## Example Review Record

```yaml
review_version: scout.v0_9.review_label.v1
item_id: design-intake-example-001
label: saved_later
reason: Useful dashboard-navigation reference, but not needed for the current Scout planning increment.
evidence:
  - docs/scout-v0-9-dry-run-receipt-format.md
manual_decision_needed: revisit during Design Scout Intake Lane
writes_allowed: false
execution_status: advisory-only, not executed
next_increment: 0.3.4 Phase 0.3 Closeout
```

## Manual Check

```bash
cd /home/source/SpiritOS
git status -sb
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-lane-contract-schema.md docs/scout-v0-9-dry-run-receipt-format.md docs/scout-v0-9-review-decision-labels.md docs/plan-index.md
grep -n "Review Decision Labels\|needs_review\|approved_dry_run\|writes_allowed\|Phase 0.3 Closeout" docs/scout-v0-9-review-decision-labels.md docs/scout-v0-9-next-phases-plan.md docs/plan-index.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the review labels and next increment.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-review-decision-labels.md
```

## Closeout

Increment 0.3.3 is complete when these labels are reviewed, indexed, and the closeout runner remains green.

Next increment: **0.3.4 Phase 0.3 Closeout**.
