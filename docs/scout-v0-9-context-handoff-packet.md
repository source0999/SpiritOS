# Scout v0.9 Increment 4.1 Context Handoff Packet

status: planning/manual-controlled

Status date: 2026-05-20

This increment defines a read-only context handoff packet for Scout v0.9 Manual-Controlled Lane Expansion. It is documentation only. It does not implement Scout features, enable autonomy, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

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

Define a read-only packet Scout could later hand to Source Proxy or the coding UI as advisory context. The packet is meant to help a human decide whether something is useful. It must not become active memory, coding context, a proxy intake payload, or an apply instruction.

## Handoff Packet Fields

| Field | Required | Meaning | Example |
| --- | --- | --- | --- |
| `handoff_version` | Yes | Human-readable packet version. | `scout.v0_9.context_handoff.v1` |
| `handoff_id` | Yes | Stable dry-run identifier. | `handoff-design-001` |
| `source_packet_id` | Yes | Scout packet, design packet, or manual reference. | `design-review-001` |
| `source` | Yes | Provenance for the handoff. | `manual/user-provided-reference` |
| `summary` | Yes | Short human-readable summary. | Dashboard navigation reference worth comparing later. |
| `suggested_use` | Yes | Advisory use only. | Use in a human-reviewed design-system prompt. |
| `evidence` | Yes | File, URL, packet, screenshot, or note reference. | `docs/scout-v0-9-design-review-packet-format.md` |
| `risk` | Yes | Known limitations. | Missing mobile, hover, focus, loading, and error-state evidence. |
| `confidence` | Yes | Evidence confidence. | `medium` |
| `manual_decision_needed` | Yes | Human decision required before use. | Approve prompt draft or save later. |
| `advisory_only` | Yes | Must be true in this phase. | `true` |
| `writes_allowed` | Yes | Must be false in this phase. | `false` |
| `execution_status` | Yes | Current execution state. | `handoff-only, not implemented` |

## Example Handoff Packet

```yaml
handoff_version: scout.v0_9.context_handoff.v1
handoff_id: handoff-design-001
source_packet_id: design-review-001
source: manual/user-provided-reference
summary: Dashboard navigation reference with compact labels and visible active state.
suggested_use: Use as evidence in a later human-reviewed design-system comparison prompt.
evidence:
  - docs/scout-v0-9-design-review-packet-format.md
risk: Missing mobile, hover, focus, loading, and error-state evidence.
confidence: medium
manual_decision_needed: approve prompt draft or save later
advisory_only: true
writes_allowed: false
execution_status: handoff-only, not implemented
next_increment: 4.2 Approval Gate Requirements
```

## Handoff Boundary

A context handoff packet must not:

- call proxy intake
- write proxy memory
- write coding context
- write active context
- create a prompt automatically
- apply code
- promote packets
- finalize promotions
- schedule work
- create hidden background workers
- commit
- push

## Future Implementation Requirements

Before a handoff packet can be implemented, a later plan must define:

- exact packet storage or transport location
- exact UI or API surface, if any
- tests proving advisory-only behavior
- tests proving proxy memory writes remain false
- tests proving coding context writes remain false
- tests proving no proxy intake call occurs
- rollback behavior
- human approval requirements

## Manual Check

```bash
cd /home/source/SpiritOS
git status -sb
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-phase-3-closeout.md docs/scout-v0-9-context-handoff-packet.md docs/plan-index.md
grep -n "Context Handoff Packet\|advisory_only: true\|writes_allowed: false\|Approval Gate Requirements" docs/scout-v0-9-context-handoff-packet.md docs/scout-v0-9-next-phases-plan.md docs/plan-index.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the handoff packet and next increment.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy memory, coding context, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-context-handoff-packet.md
```

## Closeout

Increment 4.1 is complete when this context handoff packet is reviewed, indexed, and the closeout runner remains green.

Next increment: **4.2 Approval Gate Requirements**.
