# Scout v0.5 Phase 5.4 Manual Import UI Dry-Run Button

status: implemented/manual-controlled

Status date: 2026-05-20

This document records the Phase 5.4 manual import UI dry-run button. The increment adds a passive dry-run control for approved Scout promotions in the Intelligence Center. It does not call proxy intake, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Operator Surface

Location:

- `/intelligence`
- Promoted tab
- Approved promotion cards

Control:

- `Dry Run Import`

The button calls:

```text
POST /api/scout/promotions/import-dry-run
```

The Next route proxies only to:

```text
POST /v1/scout/promotions/import-dry-run
```

It does not call:

- `/v1/scout-intake/promotion`
- `/v1/scout/promotions/finalize`
- any proxy memory write path
- any coding context write path

## Safety Contract

The UI must present this as a dry run only. A successful response must still report:

- `dry_run: true`
- `read_only: true`
- `mutation_allowed: false`
- `would_call_proxy_intake: false`
- `would_write_proxy_memory: false`
- `would_write_coding_context: false`
- `would_finalize_promotion: false`

The UI must not:

- approve queued promotions
- reject queued promotions
- finalize promotions
- call proxy intake
- write proxy memory
- write coding context
- queue discovery jobs
- run search preview
- extract candidates
- activate sources
- register hidden background workers
- schedule writes
- apply code
- commit
- push

## Parked-State Behavior

In the current parked state, the live dry-run route is expected to block with:

```text
SCOUT_PROMOTION_SIGNING_KEY is required
```

That blocked response is safe. It confirms the UI can reach the dry-run gate while Scout remains unable to import into proxy memory.

## Acceptance Criteria

Phase 5.4 is accepted only when:

- the UI test proves the button calls `/api/scout/promotions/import-dry-run`
- the UI test proves it does not call `/api/scout/promotions/finalize`
- the live dry-run endpoint remains blocked without the signing key
- `git diff --check` passes
- Scout Level 1 soak passes
- no proxy intake call occurs
- no proxy memory write occurs
- no coding context write occurs
- no promotion finalization occurs

## Rollback

```bash
git restore src/components/dashboard/HomelabScoutIntelligenceWidget.tsx src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
rm -rf src/app/api/scout/promotions/import-dry-run
rm docs/scout-v0-5-manual-import-ui-dry-run-button.md
```

## Next Permission Gate

Operator approval is required before Phase 5.5 or any UI/control that can call proxy intake. The recommended next increment is Phase 5.5: Manual Import Audit Receipt Design, still without enabling proxy memory writes.
