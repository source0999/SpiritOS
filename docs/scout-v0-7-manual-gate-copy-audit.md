# Scout v0.7 Phase 0.3 Manual Gate Copy Audit

status: implemented/manual-controlled

Status date: 2026-05-20

This document records the Scout v0.7 Phase 0.3 manual gate copy audit. The increment only clarifies visible `/intelligence` button labels so mutation-capable Scout controls read as manual operator actions. It does not call proxy intake, does not emit actual receipts, does not finalize promotions automatically, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Goal

Make manual authority visible at the point of action.

Updated labels:

- `Manual Promote Packet`
- `Manual Reject Packet`
- `Manual Approve Source`
- `Manual Reject Source`
- `Manual Block Source`
- `Manual Approve Selected Sources`
- `Manual Pause Plan`
- `Manual Resume Plan`
- `Manual Preview Search`
- `Manual Extract Candidates`
- `Save Manual Plan`

## Safety Boundary

This increment changes UI copy only and keeps existing handlers unchanged. It must not add or trigger:

- proxy intake calls
- append-only intake writes
- actual receipt emission
- automatic promotion finalization
- proxy memory writes
- coding context writes
- active context writes
- hidden background workers
- scheduled writes
- automatic packet promotion
- automatic source approval
- automatic source rejection
- automatic source blocking
- source activation
- discovery execution without an operator click
- candidate extraction without an operator click
- apply actions
- commits
- pushes
- self-promotion to a higher autonomy level

## Verification

Required checks:

- frontend test proves mutation-capable Scout gates are labeled as manual
- frontend test proves older bare action labels are absent
- existing dry-run import tests still pass
- closeout remains read-only and dry-run-only

## Manual Check

```bash
cd /home/source/SpiritOS && grep -n "Scout v0.7 Phase 0.3 Manual Gate Copy Audit\|Manual Promote Packet\|Manual Approve Source\|Manual Preview Search\|Manual Extract Candidates\|Save Manual Plan\|Next Permission Gate" docs/scout-v0-7-manual-gate-copy-audit.md src/components/dashboard/HomelabScoutIntelligenceWidget.tsx src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx && git diff --check && CI=1 npm run test -- HomelabScoutIntelligenceWidget && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,blocked:.closeout_summary.parked_dry_run_blocked,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected outcome:

- doc and UI contain manual gate labels
- frontend test passes
- `git diff --check` prints nothing
- closeout compressed output returns `result: pass`
- `ready` is `true`
- `mode` is `dry_run_only`
- `proxy_memory`, `coding_context`, and `finalize` are `false`
- `unexpected` is empty
- `head_changed` is `false`

## Rollback

```bash
git restore src/components/dashboard/HomelabScoutIntelligenceWidget.tsx src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
rm docs/scout-v0-7-manual-gate-copy-audit.md
```

## Next Permission Gate

Operator approval is required before implementing Scout v0.7 Phase 0.4. The recommended next increment is **Scout v0.7 Phase 0.4: Review Evidence Grouping Plan**, docs-only unless a later gate approves a small read-only UI grouping change.
