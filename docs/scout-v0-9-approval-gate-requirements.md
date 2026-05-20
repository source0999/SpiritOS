# Scout v0.9 Increment 4.2 Approval Gate Requirements

status: planning/manual-controlled

Status date: 2026-05-20

This increment defines the human approval gates that would be required before any future Scout-to-proxy write path could be considered. It is documentation only. It does not implement Scout features, enable autonomy, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

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
- `would_call_proxy_intake: false`
- `head_changed: false`
- `unexpected_status_delta: []`

Scout remains stable, parked, manual-controlled, and not autonomous.

## Goal

Define what a human would need to approve before any later plan could propose proxy memory writes, coding context writes, or proxy intake. These gates are future criteria only. They are not current permission to write.

## Approval Gate Requirements

| Gate | Required Evidence | Current Status |
| --- | --- | --- |
| Named operator approval | Human operator, date, exact target, and scope. | Future-only; not approved. |
| Exact write target | Specific proxy memory, coding context, or intake surface. | Future-only; no target selected. |
| Source evidence packet | Packet ID, source, provenance, and review status. | Future-only; advisory packet only. |
| Dry-run receipt | Proposed action, risk, confidence, and no-write preview. | Future-only; no execution. |
| Test command list | Repo-specific tests that prove boundaries hold. | Future-only; closeout runner remains the current gate. |
| Rollback plan | Exact restore, disable, or remove action for the approved target. | Future-only; no write path exists. |
| Scope limit | One approved target, one approved action, one manual run. | Future-only; no blanket permission. |
| Final human confirmation | Explicit approval after dry-run output is reviewed. | Future-only; no approval granted. |

## Non-Negotiable Boundaries

Until a separate future implementation plan explicitly changes these with human approval, Scout must keep:

- `proxy_memory_write_allowed: false`
- `coding_context_write_allowed: false`
- `promotion_finalization_allowed: false`
- `would_call_proxy_intake: false`
- `would_write_proxy_memory: false`
- `would_write_coding_context: false`
- `would_finalize_promotion: false`

Scout still cannot:

- auto-approve candidates
- auto-discover sources
- extract candidates automatically
- schedule writes
- call proxy intake
- write proxy memory
- write coding context
- finalize promotion
- commit
- push
- create hidden workers

## Approval Record Format

```yaml
approval_record_version: scout.v0_9.approval_gate.v1
approval_id: approval-not-granted
operator: needs_explicit_human_name
approval_status: not_approved
target_type: none
target_path: none
source_packet_id: none
dry_run_receipt_id: none
approved_action: none
scope_limit: one target, one action, one manual run
rollback_plan: required before any future implementation
proxy_memory_write_allowed: false
coding_context_write_allowed: false
promotion_finalization_allowed: false
manual_final_confirmation_required: true
next_increment: 4.3 Integration Risk Table
```

## Manual Check

```bash
cd /home/source/SpiritOS
git status -sb
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-context-handoff-packet.md docs/scout-v0-9-approval-gate-requirements.md docs/plan-index.md
grep -n "Approval Gate Requirements\|approval_status: not_approved\|proxy_memory_write_allowed: false\|coding_context_write_allowed: false\|4.3 Integration Risk Table" docs/scout-v0-9-approval-gate-requirements.md docs/scout-v0-9-next-phases-plan.md docs/plan-index.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,proxy_intake:.closeout_summary.would_call_proxy_intake,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the approval gate doc, false write fields, and next increment.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, proxy intake, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-approval-gate-requirements.md
```

## Closeout

Increment 4.2 is complete when this approval gate requirement document is reviewed, indexed, and the closeout runner remains green.

Next increment: **4.3 Integration Risk Table**.
