# Scout v0.9 Increment 2.3 Operator Decision Flow

status: planning/manual-controlled

Status date: 2026-05-20

This increment plans the operator decision flow for Scout v0.9 Manual-Controlled Lane Expansion. It is documentation only. It does not implement Scout features, enable autonomy, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

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

Define a human decision flow for Scout review items. The flow should support approve-for-dry-run, reject, save later, block, or convert into a Codex prompt without automatically mutating code, Scout runtime state, proxy memory, coding context, source state, packet state, or promotion state.

## Decision Flow

1. Review source, summary, risk, confidence, and evidence.
2. Choose one advisory decision.
3. Record the reason for the decision in human-readable form.
4. If converting into a Codex prompt, draft text only for human review.
5. If approving dry-run review, run only a separately approved dry-run path.
6. Keep all writes disabled unless a later implementation plan explicitly authorizes one bounded write path.

## Decision Table

| Decision | Meaning | Allowed Result | Mutation Allowed |
| --- | --- | --- | --- |
| `approve_dry_run_review` | Human says the item may be used in a dry-run review. | Draft or run a separately approved dry-run check. | No |
| `reject` | Human says the item is not useful or trustworthy. | Exclude from current review notes. | No |
| `save_later` | Human says the item may be useful later. | Keep as advisory reference. | No |
| `block` | Human says the item is unsafe, unclear, or missing evidence. | Stop the item until new evidence exists. | No |
| `convert_to_codex_prompt` | Human wants a prompt draft for later work. | Produce text only, with risks and evidence attached. | No |

## Codex Prompt Draft Boundary

When an operator converts an item into a Codex prompt, the prompt draft must:

- name the source evidence
- include risk and confidence
- state that Scout is not authorizing implementation
- state that writes remain disabled unless separately approved
- avoid hidden tasks or background work
- avoid saying Scout has approved, applied, promoted, committed, or pushed anything

## Example Decision Record

```yaml
decision_version: scout.v0_9.operator_decision.v1
item_id: design-review-001
decision: convert_to_codex_prompt
reason: The dashboard navigation pattern may help a later UI comparison, but needs mobile and focus-state verification.
evidence:
  - docs/scout-v0-9-design-review-packet-format.md
risk: Missing mobile, hover, focus, loading, and error-state evidence.
confidence: medium
prompt_draft_allowed: true
dry_run_allowed: false
writes_allowed: false
execution_status: decision-only, not implemented
next_increment: 2.4 Phase 2 Closeout
```

## Non-Mutation Boundary

Operator decisions do not authorize:

- source approval, rejection, blocking, or activation in runtime storage
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
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-better-summaries-plan.md docs/scout-v0-9-operator-decision-flow.md docs/plan-index.md
grep -n "Operator Decision Flow\|convert_to_codex_prompt\|writes_allowed: false\|Phase 2 Closeout" docs/scout-v0-9-operator-decision-flow.md docs/scout-v0-9-next-phases-plan.md docs/plan-index.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the operator decision flow and next increment.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-operator-decision-flow.md
```

## Closeout

Increment 2.3 is complete when this operator decision flow is reviewed, indexed, and the closeout runner remains green.

Next increment: **2.4 Phase 2 Closeout**.
