# Scout v0.9 Increment 2.1 Review Grouping Plan

status: planning/manual-controlled

Status date: 2026-05-20

This increment plans review grouping for Scout v0.9 Manual-Controlled Lane Expansion. It is documentation only. It does not implement Scout features, enable autonomy, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

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

Plan how Scout review items should be grouped so a human operator can make clearer decisions. Grouping should improve scan quality and prioritization without hiding provenance or authorizing any mutation.

## Grouping Model

| Group | Purpose | Example Values | Operator Benefit |
| --- | --- | --- | --- |
| Usefulness | Sort by likely immediate value. | `useful_now`, `saved_later`, `low_value`, `needs_review` | Helps focus attention on items worth reading first. |
| Risk | Surface safety, provenance, or noise concerns. | `low`, `medium`, `high`, `blocked` | Prevents unsafe or weak items from blending into useful evidence. |
| Source | Preserve where the item came from. | `manual`, `allowlisted_source`, `packet`, `design_reference` | Keeps provenance visible during review. |
| Project | Route items to the right work area. | `SpiritOS`, `Scout`, `Source Proxy`, `Cartographer`, `Design System` | Reduces cross-project confusion. |
| Component | Tie evidence to a UI or system component. | `dashboard`, `coding`, `intelligence_center`, `navigation` | Helps convert review into a later bounded task. |
| Time sensitivity | Identify freshness requirements. | `urgent`, `current`, `durable`, `stale`, `needs_recheck` | Avoids treating stale facts as current decisions. |

## Review Grouping Rules

- A review item should have one primary grouping reason.
- Source and risk should always remain visible.
- A grouping label is advisory only.
- Grouping must not approve, reject, block, promote, or mutate runtime state.
- Grouping should make manual decisions easier, not create a hidden priority queue.
- Stale or uncertain evidence should use `needs_recheck` or `needs_review` instead of guessing.

## Example Grouped Review Item

```yaml
grouping_version: scout.v0_9.review_grouping.v1
item_id: design-review-001
primary_group: usefulness
usefulness: useful_now
risk: medium
source: manual/user-provided-reference
project: SpiritOS
component: dashboard
time_sensitivity: durable
reason: Dashboard navigation reference may help a later design-system review.
manual_decision_needed: summarize or save later
writes_allowed: false
execution_status: grouping-only, not implemented
next_increment: 2.2 Better Summaries
```

## Non-Mutation Boundary

Review grouping does not authorize:

- source approval, rejection, blocking, or activation
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
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-review-grouping-plan.md docs/plan-index.md
grep -n "Review Grouping Plan\|Usefulness\|Time sensitivity\|writes_allowed: false\|Better Summaries" docs/scout-v0-9-review-grouping-plan.md docs/scout-v0-9-next-phases-plan.md docs/plan-index.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the grouping model and next increment.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-review-grouping-plan.md
```

## Closeout

Increment 2.1 is complete when this review grouping plan is reviewed, indexed, and the closeout runner remains green.

Next increment: **2.2 Better Summaries**.
