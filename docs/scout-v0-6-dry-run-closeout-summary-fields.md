# Scout v0.6 Phase 0.3 Dry-Run Closeout Summary Fields

status: implemented/manual-controlled

Status date: 2026-05-20

This document records the Scout v0.6 Phase 0.3 dry-run closeout summary fields increment. The increment adds read-only summary fields to the existing `scout-v0-5-closeout` runner output. It does not call proxy intake, does not emit actual receipts, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Goal

Make closeout output easier to review from mobile and terminal checks without changing Scout behavior.

The closeout profile now reports a `closeout_summary` object with:

- `mode: dry_run_only`
- `manual_controlled: true`
- `ready_for_next_increment`
- `parked_dry_run_blocked`
- `blocked_reason`
- `dry_run_endpoint_status`
- `receipt_preview_emitted`
- `would_call_proxy_intake: false`
- `would_write_proxy_memory: false`
- `would_write_coding_context: false`
- `would_finalize_promotion: false`
- `proxy_memory_write_allowed: false`
- `coding_context_write_allowed: false`
- `promotion_finalization_allowed: false`

## Safety Boundary

This increment only changes test-runner reporting. It must not add or trigger:

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

- unit test proves `closeout_summary` reports dry-run-only and manual-controlled
- unit test proves all import, memory, coding context, and finalization capability flags remain false
- closeout profile remains read-only and non-mutating
- parked dry-run remains blocked without `SCOUT_PROMOTION_SIGNING_KEY`

## Manual Check

```bash
cd /home/source/SpiritOS && grep -n "Scout v0.6 Phase 0.3 Dry-Run Closeout Summary Fields\|closeout_summary\|dry_run_only\|would_call_proxy_intake: false\|would_write_proxy_memory: false\|would_write_coding_context: false\|would_finalize_promotion: false\|Next Permission Gate" docs/scout-v0-6-dry-run-closeout-summary-fields.md source_proxy/testing/runner.py source_proxy/tests/test_proxy_runner.py && git diff --check && python3 -m pytest source_proxy/tests/test_proxy_runner.py -q && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{profile,result,read_only,mutated,closeout_summary,checks,file_change_verdict:{unexpected_status_delta:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}}'
```

Expected outcome:

- doc and runner include `closeout_summary`
- `pytest` passes
- `git diff --check` prints nothing
- closeout returns `result: pass`
- `closeout_summary.mode` is `dry_run_only`
- import, memory, coding context, and finalization flags are false
- `mutated` is `false`
- unexpected status delta is empty
- head changed is false

## Rollback

```bash
git restore source_proxy/testing/runner.py source_proxy/tests/test_proxy_runner.py
rm docs/scout-v0-6-dry-run-closeout-summary-fields.md
```

## Next Permission Gate

Operator approval is required before implementing Scout v0.6 Phase 0.4. The recommended next increment is **Scout v0.6 Phase 0.4: Dry-Run Receipt Preview Copy Audit**, which should audit receipt-preview labels and docs only unless a small UI copy fix is explicitly approved.
