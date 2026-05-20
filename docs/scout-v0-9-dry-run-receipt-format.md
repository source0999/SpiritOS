# Scout v0.9 Increment 0.3.2 Dry-Run Receipt Format

status: planning/manual-controlled

Status date: 2026-05-20

This increment defines the Scout v0.9 dry-run receipt format for Manual-Controlled Lane Expansion. It is documentation only. It does not implement Scout features, emit real receipts, enable autonomy, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

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

Define the smallest useful receipt shape for Scout recommendations that are reviewed by a human but not executed. A dry-run receipt should make an item easy to inspect, approve for later dry-run review, save for later, reject, or block without mutating Scout, proxy memory, coding context, source state, packet state, or promotion state.

## Receipt Contract

| Field | Required | Meaning | Example |
| --- | --- | --- | --- |
| `receipt_version` | Yes | Human-readable receipt format version. | `scout.v0_9.dry_run_receipt.v1` |
| `receipt_id` | Yes | Stable dry-run receipt identifier. | `dry-run-design-001` |
| `candidate_id` | Yes | Candidate, packet, artifact, or manual reference ID. | `design-intake-example-001` |
| `lane_name` | Yes | Lane that produced or owns the receipt. | `Design Scout Intake Lane` |
| `source` | Yes | Source or provenance for the candidate. | `manual/user-provided-reference` |
| `summary` | Yes | Short factual summary of the item. | `Dashboard navigation pattern worth reviewing.` |
| `proposed_action` | Yes | Advisory action proposed for human review. | `Save as a design packet for later review.` |
| `why_useful` | Yes | Reason this item may matter. | `May improve dashboard navigation density.` |
| `risk` | Yes | Known safety, accuracy, provenance, or noise risk. | `Screenshot may omit mobile and focus states.` |
| `confidence` | Yes | Evidence confidence. | `high`, `medium`, `low`, `needs verification` |
| `manual_approval_required` | Yes | Whether a human approval is required before any later step. | `true` |
| `execution_status` | Yes | Current execution state. | `dry-run-only, not executed` |
| `writes_allowed` | Yes | Whether this receipt authorizes writes. | `false` |
| `next_manual_decision` | Yes | The next human decision requested. | `save_later`, `reject`, `block`, `approve_dry_run_review` |
| `rollback_notes` | Yes | How to undo the planning artifact if rejected. | `remove receipt from docs-only plan` |

## Execution Boundary

A Scout v0.9 dry-run receipt must not imply execution.

Forbidden from a dry-run receipt:

- proxy intake calls
- proxy memory writes
- coding context writes
- active context writes
- source approval, rejection, blocking, or activation
- automatic discovery
- automatic candidate extraction
- automatic packet promotion
- promotion finalization
- receipt emission to runtime storage
- scheduled writes
- hidden background workers
- commits
- pushes

Required receipt language:

- `execution_status: dry-run-only, not executed`
- `manual_approval_required: true`
- `writes_allowed: false`

## Example Receipt

```yaml
receipt_version: scout.v0_9.dry_run_receipt.v1
receipt_id: dry-run-design-001
candidate_id: design-intake-example-001
lane_name: Design Scout Intake Lane
source: manual/user-provided-reference
summary: Dashboard navigation pattern worth reviewing.
proposed_action: Save as a design packet for later manual review.
why_useful: May improve repeatable dashboard layout and navigation decisions.
risk: The reference may be stale, too generic, or missing mobile/focus states.
confidence: medium
manual_approval_required: true
execution_status: dry-run-only, not executed
writes_allowed: false
next_manual_decision: save_later or reject
rollback_notes: Remove the docs-only receipt example if the format is rejected.
```

## Operator Review Checklist

Before a receipt can influence a later implementation plan, the operator should confirm:

- source and provenance are visible
- summary is factual and not vague
- proposed action is advisory only
- risk is explicit
- confidence is not overstated
- manual approval is required
- writes remain false
- receipt does not mutate source, packet, proxy memory, coding context, or promotion state

## Manual Check

```bash
cd /home/source/SpiritOS
git status -sb
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-lane-contract-schema.md docs/scout-v0-9-dry-run-receipt-format.md docs/plan-index.md
grep -n "Dry-Run Receipt Format\|receipt_version\|execution_status\|writes_allowed\|manual_approval_required\|Review Decision Labels" docs/scout-v0-9-dry-run-receipt-format.md docs/scout-v0-9-next-phases-plan.md docs/plan-index.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the dry-run receipt fields and next increment.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-dry-run-receipt-format.md
```

## Closeout

Increment 0.3.2 is complete when this receipt format is reviewed, indexed, and the closeout runner remains green.

Next increment: **0.3.3 Review Decision Labels**.
