# Scout v0.5 Phase 5.5 Manual Import Audit Receipt Design

status: planning/manual-controlled

Status date: 2026-05-20

This document designs the audit receipt for a future manual Scout-to-Proxy import. It is planning only. It does not call proxy intake, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Current Verified State

The Phase 5.4 manual gate confirmed:

- UI dry-run test passed.
- `Dry Run Import` calls `/api/scout/promotions/import-dry-run`.
- The UI does not call `/api/scout/promotions/finalize` for dry-run.
- Live Scout dry-run remains blocked without `SCOUT_PROMOTION_SIGNING_KEY`.
- Scout Level 1 soak passes with `mutated: false`.
- No proxy intake call occurs.
- No proxy memory write occurs.
- No coding context write occurs.
- No promotion finalization occurs.

This keeps Scout manual-controlled. The next bridge artifact should be a receipt design, not an import implementation.

## Existing Receipt Signals

The current proxy intake path already returns these important safety fields when it is manually called in a future phase:

- `written`
- `path`
- `packet_id`
- `promotion_id`
- `authority: append_only_evidence`
- `applied: false`
- `approved_proxy_action: false`

Those fields are necessary but not sufficient for a complete operator receipt. A future manual import should return a fuller receipt that can be pasted into notes, reviewed later, and rolled back by promotion ID.

## Required Receipt Shape

A future manual import receipt should include:

- `receipt_version`
- `event: scout_manual_import_receipt`
- `imported: true`
- `dry_run: false`
- `manual_controlled: true`
- `operator`
- `promotion_id`
- `packet_id`
- `approved_by`
- `approved_at`
- `written_at`
- `intake_log_path`
- `payload_sha256`
- `signed_payload_sha256`
- `signature_key_id` or `signature_key_hint`
- `verdict_decision`
- `source_uri`
- `source_trust_label`
- `authority: append_only_evidence`
- `applied: false`
- `approved_proxy_action: false`
- `writes`
- `rollback`
- `safety`

The `writes` section must separate evidence writes from active memory writes:

```json
{
  "writes": {
    "append_only_evidence": true,
    "proxy_memory": false,
    "coding_context": false,
    "active_context": false
  }
}
```

The `rollback` section must include:

- `promotion_id`
- `intake_log_path`
- `rollback_action`
- `tombstone_event`
- `delete_allowed`

Default rollback policy:

- Prefer tombstone event.
- Do not delete audit evidence by default.
- Deletion requires a separate operator action and reason.

## Receipt Safety Rules

The receipt must explicitly say:

- no automatic packet promotion occurred
- no proxy memory write occurred
- no coding context write occurred
- no active context was changed
- no source was activated
- no discovery job was created
- no search preview ran
- no candidate extraction ran
- no apply action ran
- no commit occurred
- no push occurred
- no hidden background worker ran
- no scheduled write ran

## Future Manual Import Flow

The future implementation should use this sequence:

1. Operator reviews approved promotion.
2. Operator runs dry-run.
3. Dry-run returns `import_ready: true`.
4. Operator explicitly confirms one manual import.
5. Scout posts signed payload to proxy intake.
6. Proxy writes one append-only evidence record.
7. Proxy returns an audit receipt.
8. UI or CLI displays the receipt.
9. Scout records no automatic memory write.

Any failure must stop the flow and avoid retries.

## Acceptance Criteria For Future Implementation

A later implementation is accepted only when tests prove:

- receipt includes all required identity fields
- receipt includes all safety fields
- receipt says `applied: false`
- receipt says `approved_proxy_action: false`
- receipt says `proxy_memory: false`
- receipt says `coding_context: false`
- receipt includes rollback instructions
- one manual import writes exactly one append-only evidence record
- repeated import of the same promotion is idempotent or blocked
- failed import does not change promotion status
- failed import does not write a partial receipt
- no hidden worker can create receipts
- no scheduler can create receipts
- dry-run does not create receipts
- UI render does not create receipts
- Level 1 soak remains pass

## Manual Check Block

The operator should verify this design with:

```bash
cd /home/source/SpiritOS && grep -n "Manual Import Audit Receipt Design\|append_only_evidence\|approved_proxy_action: false\|proxy_memory: false\|coding_context: false\|tombstone_event\|Next Permission Gate" docs/scout-v0-5-manual-import-audit-receipt-design.md && git diff --check && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-level-1-soak --json | jq '{result,mutated,checks,rank_fields:.summary.rank_fields,warnings:.summary.warnings}'
```

Expected outcome:

- grep shows receipt safety terms
- `git diff --check` prints nothing
- Scout Level 1 soak returns `result: pass`
- `mutated` is `false`
- warnings are empty

## Rollback

```bash
rm docs/scout-v0-5-manual-import-audit-receipt-design.md
```

## Next Permission Gate

Operator approval is required before Phase 5.6 or any code that emits manual import receipts. The recommended next increment is Phase 5.6: Manual Import Receipt Dry-Run Schema, still without proxy intake calls, proxy memory writes, coding context writes, or promotion finalization.
