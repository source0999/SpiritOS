# Scout v0.5 Phase 5.9 Manual Import Receipt Closeout Gate

status: implemented/manual-controlled

Status date: 2026-05-20

This document records the Phase 5.9 manual import receipt closeout gate. The increment adds a read-only closeout profile for the Scout v0.5 manual import receipt lane. It does not call proxy intake, does not emit an actual receipt, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Runner Profile

Profile:

```bash
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json
```

The profile checks:

- required receipt docs exist
- receipt docs contain safety terms
- `HomelabScoutIntelligenceWidget` test passes
- `scout-import-receipt-harness` passes
- `scout-level-1-soak` passes
- parked live dry-run blocks without `SCOUT_PROMOTION_SIGNING_KEY`
- no proxy memory write is reported
- no coding context write is reported
- no promotion finalization is reported
- no unexpected file changes occur
- HEAD does not change

## Safety Boundary

The closeout profile must not:

- call `/v1/scout-intake/promotion`
- call `/api/scout/promotions/finalize`
- write an intake log
- write proxy memory
- write coding context
- update live `promotion_queue`
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

Phase 5.9 is accepted only when:

- `scout-v0-5-closeout` returns `result: pass`
- `read_only: true`
- `mutated: false`
- frontend test passes
- receipt harness passes
- Level 1 soak passes
- parked dry-run remains blocked without signing key
- `git diff --check` passes
- closeout profile reports no unexpected file changes
- closeout profile reports `head_changed: false`

## Manual Check

```bash
cd /home/source/SpiritOS && grep -n "Manual Import Receipt Closeout Gate\|scout-v0-5-closeout\|SCOUT_PROMOTION_SIGNING_KEY\|proxy memory\|coding context\|Next Permission Gate" docs/scout-v0-5-manual-import-receipt-closeout-gate.md && git diff --check && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{profile,result,read_only,mutated,checks,parked_dry_run:.parked_dry_run,receipt_harness:.receipt_harness,level_1_soak:.level_1_soak,file_change_verdict:{unexpected_status_delta:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}}'
```

Expected outcome:

- closeout returns `result: pass`
- `mutated` is `false`
- parked dry-run detail is `SCOUT_PROMOTION_SIGNING_KEY is required`
- receipt harness passes
- Level 1 soak passes
- unexpected status delta is empty
- head changed is false

## Rollback

```bash
git restore source_proxy/testing/runner.py
rm docs/scout-v0-5-manual-import-receipt-closeout-gate.md
```

## Next Permission Gate

Operator approval is required before Scout v0.6 or any code that can call proxy intake. Recommended next increment: Scout v0.6 planning only, focused on whether manual import should remain dry-run-only or graduate to a single explicit append-only evidence write.
