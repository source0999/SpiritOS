# Scout v0.5 Phase 5.7 Manual Import Receipt Test Harness

status: implemented/manual-controlled

Status date: 2026-05-20

This document records the Phase 5.7 manual import receipt test harness. The increment adds a read-only runner profile that validates Scout's receipt preview schema inside an isolated temporary Scout database. It does not call proxy intake, does not emit an actual receipt, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Runner Profile

Profile:

```bash
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-import-receipt-harness --json
```

The profile runs:

```text
scout/scripts/receipt_preview_harness.py
```

inside the Scout container image with the repository `scout/` directory mounted read-only.

## Harness Contract

The harness creates only temporary data outside the repository:

- temporary Scout database
- temporary packet
- temporary `promote` verdict
- temporary queued promotion
- temporary approved promotion

Then it calls Scout's dry-run function and verifies:

- `receipt_preview` exists
- `event: scout_manual_import_receipt_preview`
- `imported: false`
- `applied: false`
- `approved_proxy_action: false`
- `writes.append_only_evidence: false`
- `writes.proxy_memory: false`
- `writes.coding_context: false`
- `writes.active_context: false`
- `rollback.tombstone_event: scout_manual_import_tombstone`
- `rollback.delete_allowed: false`
- `safety.hidden_background_worker: false`
- `safety.scheduled_write: false`
- promotion status is unchanged
- no audit file is created

## Safety Boundary

The harness must not:

- call `/v1/scout-intake/promotion`
- call live Scout mutation endpoints
- write an intake log
- write proxy memory
- write coding context
- update the live `promotion_queue`
- finalize a promotion
- create live audit logs
- queue live promotions
- approve live promotions
- reject live promotions
- create discovery jobs
- run search preview
- extract candidates
- activate sources
- register hidden background workers
- schedule writes
- apply code
- commit
- push

## Acceptance Criteria

Phase 5.7 is accepted only when:

- compile checks pass
- `scout-import-receipt-harness` returns `result: pass`
- harness reports `read_only: true`
- harness reports `mutated: false`
- harness write flags are false
- harness rollback tombstone field is present
- `git diff --check` passes
- Scout Level 1 soak passes
- no unexpected file changes occur during the harness

## Rollback

```bash
git restore source_proxy/testing/runner.py
rm scout/scripts/receipt_preview_harness.py docs/scout-v0-5-manual-import-receipt-test-harness.md
```

## Next Permission Gate

Operator approval is required before Phase 5.8 or any code that can write actual receipts. The recommended next increment is Phase 5.8: Manual Import Receipt UI Preview, still without proxy intake calls, proxy memory writes, coding context writes, or promotion finalization.
