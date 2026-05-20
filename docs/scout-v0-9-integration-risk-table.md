# Scout v0.9 Increment 4.3 Integration Risk Table

status: planning/manual-controlled

Status date: 2026-05-20

This increment lists the risks that must be handled before any future Scout-to-proxy integration can move beyond advisory planning. It is documentation only. It does not implement Scout features, enable autonomy, run discovery, extract candidates, promote packets, call proxy intake, write proxy memory, write coding context, register workers, schedule writes, apply code, commit, push, or create hidden background workers.

## Gate Before This Increment

Manual closeout check passed before this document was written:

- `scout-v0-5-closeout` returned `result: pass`
- `read_only: true`
- `mutated: false`
- `mode: dry_run_only`
- `manual_controlled: true`
- `ready_for_next_increment: true`
- `would_call_proxy_intake: false`
- `would_write_proxy_memory: false`
- `would_write_coding_context: false`
- `would_finalize_promotion: false`
- `head_changed: false`
- `unexpected_status_delta: []`

Scout remains stable, parked, manual-controlled, and not autonomous.

## Goal

Define the integration risks and mitigations that must stay visible before any later plan considers proxy handoff implementation. Every risk below must have an explicit mitigation before work can move to Phase 4 closeout.

## Integration Risk Table

| Risk | Why It Matters | Mitigation | Current Status |
| --- | --- | --- | --- |
| Stale information | Old summaries can steer future prompts or reviews toward outdated assumptions. | Require review date, source date, and manual re-check for time-sensitive items. | Planned only. |
| Bad source | Weak provenance can make Scout appear more confident than the evidence supports. | Require visible source, source lifecycle state, and operator review before use. | Planned only. |
| Hallucinated summary | A packet can overstate what evidence actually says. | Require evidence references, confidence labels, and human review before handoff. | Planned only. |
| Accidental mutation | A handoff packet could be mistaken for permission to write. | Keep `writes_allowed: false`, require explicit approval records, and test no-write paths. | Planned only. |
| Noisy context | Too many low-value packets can degrade operator decisions and prompt quality. | Add usefulness labels, risk grouping, and manual save/reject/block decisions. | Planned only. |
| Unsafe automation | Convenience pressure can turn advisory receipts into hidden work. | Forbid auto-approval, scheduled work, background workers, commits, pushes, and final promotion. | Planned only. |
| Proxy intake ambiguity | A packet may look like a proxy intake payload even when it is advisory. | Use explicit `advisory_only: true`, `would_call_proxy_intake: false`, and separate future implementation gates. | Planned only. |
| Coding context contamination | Unreviewed Scout notes could be treated as active coding context. | Keep coding context writes false and require named human approval for any future context target. | Planned only. |

## Mitigation Completeness Rule

Phase 4 cannot close unless each listed risk has:

- a named mitigation
- a manual check
- an expected output
- rollback notes
- no current write permission
- no implied autonomy

## Manual Check

```bash
cd /home/source/SpiritOS
git status -sb
git diff -- docs/scout-v0-9-next-phases-plan.md docs/scout-v0-9-approval-gate-requirements.md docs/scout-v0-9-integration-risk-table.md docs/plan-index.md
grep -n "Integration Risk Table\|Stale information\|Accidental mutation\|Unsafe automation\|4.4 Phase 4 Closeout" docs/scout-v0-9-integration-risk-table.md docs/scout-v0-9-next-phases-plan.md docs/plan-index.md
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,manual:.closeout_summary.manual_controlled,proxy_intake:.closeout_summary.would_call_proxy_intake,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected output:

- Diff is docs-only.
- Grep finds the risk table, major risks, and next increment.
- Closeout returns `result: pass`, `read_only: true`, `mutated: false`, and `mode: dry_run_only`.
- Proxy intake, proxy memory, coding context, and promotion finalization remain `false`.

## Rollback

```bash
git restore docs/plan-index.md docs/scout-v0-9-next-phases-plan.md
rm docs/scout-v0-9-integration-risk-table.md
```

## Closeout

Increment 4.3 is complete when this risk table is reviewed, indexed, and the closeout runner remains green.

Next increment: **4.4 Phase 4 Closeout**.
