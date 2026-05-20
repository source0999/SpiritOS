# Scout v0.6 Phase 0.2 Dry-Run Blocked-State UX Copy

status: implemented/manual-controlled

Status date: 2026-05-20

This document records the Scout v0.6 Phase 0.2 dry-run blocked-state UX copy increment. The increment only clarifies operator-facing copy when the Scout manual import dry-run is blocked. It does not call proxy intake, does not emit actual receipts, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Goal

Make the blocked dry-run state explicit enough for mobile and console review:

- dry-run remains blocked when required preconditions are missing
- Scout remains dry-run-only
- no proxy intake call occurred
- no proxy memory write occurred
- no coding context write occurred
- no promotion finalization occurred

## Change

Updated the blocked import dry-run UI message from a short memory-only statement to a fuller safety statement:

```text
Import dry run blocked: SCOUT_PROMOTION_SIGNING_KEY is required. Scout remains dry-run-only. No proxy intake call, proxy memory write, coding context write, or promotion finalization occurred.
```

## Files

- `src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`
- `src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`
- `docs/scout-v0-6-dry-run-blocked-state-ux-copy.md`

## Safety Boundary

This increment must not add or trigger:

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

- frontend test proves the blocked state names dry-run-only status and all no-write guarantees
- frontend test proves no receipt preview is rendered for the blocked state
- frontend test proves no promotion finalize call is made from dry-run
- `scout-v0-5-closeout` remains read-only and non-mutating

## Manual Check

```bash
cd /home/source/SpiritOS && grep -n "Scout v0.6 Phase 0.2 Dry-Run Blocked-State UX Copy\|Scout remains dry-run-only\|No proxy intake call\|proxy memory write\|coding context write\|promotion finalization\|Next Permission Gate" docs/scout-v0-6-dry-run-blocked-state-ux-copy.md src/components/dashboard/HomelabScoutIntelligenceWidget.tsx src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx && git diff --check && CI=1 npm run test -- HomelabScoutIntelligenceWidget && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{profile,result,read_only,mutated,checks,file_change_verdict:{unexpected_status_delta:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}}'
```

Expected outcome:

- doc and UI include the dry-run-only blocked-state copy
- frontend test passes
- `git diff --check` prints nothing
- closeout returns `result: pass`
- `mutated` is `false`
- unexpected status delta is empty
- head changed is false

## Rollback

```bash
git restore src/components/dashboard/HomelabScoutIntelligenceWidget.tsx src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
rm docs/scout-v0-6-dry-run-blocked-state-ux-copy.md
```

## Next Permission Gate

Operator approval is required before implementing Scout v0.6 Phase 0.3. The recommended next increment is **Scout v0.6 Phase 0.3: Dry-Run Closeout Summary Fields**, which should improve read-only closeout reporting without proxy intake, proxy memory writes, coding context writes, or promotion finalization.
