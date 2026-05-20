# Scout v0.5 Phase 5.6 Manual Import Receipt Dry-Run Schema

status: implemented/manual-controlled

Status date: 2026-05-20

This document records the Phase 5.6 manual import receipt dry-run schema. The increment adds a receipt preview to Scout's existing import dry-run response. It does not call proxy intake, does not emit an actual receipt, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Purpose

Phase 5.6 lets the operator inspect the receipt shape before any real Scout-to-Proxy import exists. The preview rehearses the fields that a later manual import receipt should include, while keeping every write flag off.

## Dry-Run Receipt Preview

The dry-run response now includes:

```text
receipt_preview
```

The preview must report:

- `event: scout_manual_import_receipt_preview`
- `imported: false`
- `dry_run: true`
- `manual_controlled: true`
- `authority: append_only_evidence`
- `applied: false`
- `approved_proxy_action: false`
- `writes.append_only_evidence: false`
- `writes.proxy_memory: false`
- `writes.coding_context: false`
- `writes.active_context: false`
- `rollback.tombstone_event: scout_manual_import_tombstone`
- `rollback.delete_allowed: false`
- `safety.proxy_memory_write: false`
- `safety.coding_context_write: false`
- `safety.hidden_background_worker: false`
- `safety.scheduled_write: false`

The preview may include identity and provenance fields such as:

- `promotion_id`
- `packet_id`
- `approved_by`
- `approved_at`
- `payload_sha256`
- `signed_payload_sha256`
- `source_uri`
- `source_trust_label`
- `verdict_decision`

## Safety Boundary

The receipt preview must not:

- call `/v1/scout-intake/promotion`
- write an intake log
- write proxy memory
- write coding context
- update `promotion_queue`
- finalize a promotion
- create an audit log
- queue a promotion
- approve a promotion
- reject a promotion
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

Phase 5.6 is accepted only when:

- compile checks pass
- isolated runtime dry-run includes `receipt_preview`
- receipt preview says `imported: false`
- receipt preview says `applied: false`
- receipt preview says `approved_proxy_action: false`
- receipt preview write flags are all false
- receipt preview includes rollback tombstone fields
- dry-run leaves promotion status unchanged
- dry-run creates no audit file
- live parked route remains blocked without signing key
- `git diff --check` passes
- Scout Level 1 soak passes

## Rollback

```bash
git restore scout/src/scout/packets/promotions.py scout/src/scout/tests/test_promotions.py
rm docs/scout-v0-5-manual-import-receipt-dry-run-schema.md
```

## Next Permission Gate

Operator approval is required before Phase 5.7 or any code that writes actual receipts. The recommended next increment is Phase 5.7: Manual Import Receipt Test Harness, still without proxy intake calls, proxy memory writes, coding context writes, or promotion finalization.
