# Scout v0.6 Phase 0.5 Dry-Run Closeout Manual Check Compression

status: implemented/manual-controlled

Status date: 2026-05-20

This document records the Scout v0.6 Phase 0.5 dry-run closeout manual check compression increment. The increment is documentation only. It gives the operator a shorter mobile-friendly closeout command that reads the existing `closeout_summary` fields from `scout-v0-5-closeout`. It does not call proxy intake, does not emit actual receipts, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Goal

Reduce the manual check from a wide closeout payload to the minimum fields needed to decide whether Scout v0.6 can continue:

- `result`
- `read_only`
- `mutated`
- `ready`
- `mode`
- `blocked`
- `proxy_memory`
- `coding_context`
- `finalize`
- `unexpected`
- `head_changed`

## Compressed Manual Check

```bash
cd /home/source/SpiritOS && git diff --check && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,blocked:.closeout_summary.parked_dry_run_blocked,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected passing output shape:

```json
{
  "result": "pass",
  "read_only": true,
  "mutated": false,
  "ready": true,
  "mode": "dry_run_only",
  "blocked": true,
  "proxy_memory": false,
  "coding_context": false,
  "finalize": false,
  "unexpected": [],
  "head_changed": false
}
```

## Safety Boundary

This increment only compresses the operator check. It must not add or trigger:

- proxy intake calls
- append-only intake writes
- actual receipt emission
- promotion finalization
- proxy memory writes
- coding context writes
- active context writes
- hidden background workers
- scheduled writes
- automatic packet promotion
- automatic source approval
- source activation
- discovery execution
- candidate extraction
- apply actions
- commits
- pushes

## Verification

Required checks:

- doc contains the compressed closeout check
- `git diff --check` passes
- focused receipt harness passes
- closeout compressed output returns pass, ready, dry-run-only, false write flags, empty unexpected status delta, and unchanged head

## Manual Check

```bash
cd /home/source/SpiritOS && grep -n "Scout v0.6 Phase 0.5 Dry-Run Closeout Manual Check Compression\|Compressed Manual Check\|ready_for_next_increment\|dry_run_only\|would_write_proxy_memory\|would_write_coding_context\|would_finalize_promotion\|Next Permission Gate" docs/scout-v0-6-dry-run-closeout-manual-check-compression.md && git diff --check && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-import-receipt-harness --json | jq '{profile,result,read_only,mutated,checks,file_change_verdict:{unexpected_status_delta:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}}' && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{result,read_only,mutated,ready:.closeout_summary.ready_for_next_increment,mode:.closeout_summary.mode,blocked:.closeout_summary.parked_dry_run_blocked,proxy_memory:.closeout_summary.would_write_proxy_memory,coding_context:.closeout_summary.would_write_coding_context,finalize:.closeout_summary.would_finalize_promotion,unexpected:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}'
```

Expected outcome:

- doc contains the compressed manual check
- `git diff --check` prints nothing
- receipt harness returns `result: pass`
- closeout compressed output returns `result: pass`
- `ready` is `true`
- `mode` is `dry_run_only`
- `proxy_memory`, `coding_context`, and `finalize` are `false`
- `unexpected` is empty
- `head_changed` is `false`

## Rollback

```bash
rm docs/scout-v0-6-dry-run-closeout-manual-check-compression.md
```

## Next Permission Gate

Operator approval is required before implementing Scout v0.6 Phase 0.6. The recommended next increment is **Scout v0.6 Phase 0.6: Dry-Run Closeout Index And Stop Point**, which should index the v0.6 dry-run-only docs and declare the current lane parked unless a later operator decision reopens real import work.
