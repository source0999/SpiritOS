# Scout v0.5 Phase 5.8 Manual Import Receipt UI Preview

status: implemented/manual-controlled

Status date: 2026-05-20

This document records the Phase 5.8 manual import receipt UI preview. The increment displays the dry-run `receipt_preview` on approved promotion cards after the operator clicks `Dry Run Import`. It does not call proxy intake, does not emit an actual receipt, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Operator Surface

Location:

- `/intelligence`
- Promoted tab
- Approved promotion card
- `Dry Run Import`

After a successful dry-run response, the UI displays:

- receipt event
- imported state
- applied state
- approved proxy action state
- append-only evidence write flag
- proxy memory write flag
- coding context write flag
- active context write flag
- rollback tombstone event
- delete allowed flag

## Safety Contract

The UI preview is passive. It must not:

- call `/v1/scout-intake/promotion`
- call `/api/scout/promotions/finalize`
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

The UI preview must visibly show that:

- `imported: false`
- `applied: false`
- `approved_proxy_action: false`
- `proxy_memory: false`
- `coding_context: false`
- `active_context: false`

## Acceptance Criteria

Phase 5.8 is accepted only when:

- frontend test proves `Dry Run Import` calls `/api/scout/promotions/import-dry-run`
- frontend test proves it does not call `/api/scout/promotions/finalize`
- frontend test proves receipt preview fields render
- frontend test proves proxy memory write remains false in the preview
- live parked dry-run remains blocked without signing key
- `scout-import-receipt-harness` passes
- `git diff --check` passes
- Scout Level 1 soak passes

## Rollback

```bash
git restore src/components/dashboard/HomelabScoutIntelligenceWidget.tsx src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
rm docs/scout-v0-5-manual-import-receipt-ui-preview.md
```

## Next Permission Gate

Operator approval is required before Phase 5.9 or any UI/control that can emit actual receipts. The recommended next increment is Phase 5.9: Manual Import Receipt Closeout Gate, still without proxy intake calls, proxy memory writes, coding context writes, or promotion finalization.
