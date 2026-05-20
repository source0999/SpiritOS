# Scout v0.6 Phase 0.1 Graduation Decision Record

status: decided/manual-controlled

Status date: 2026-05-20

This document records the Scout v0.6 graduation decision after Scout v0.5 closed out the manual import receipt dry-run lane. It is documentation only. It does not call proxy intake, does not emit actual receipts, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Decision

Chosen path:

**Option A: Stay Dry-Run-Only**

Scout v0.6 will remain manual-controlled and dry-run-only for the Scout-to-Proxy import bridge.

This means v0.6 may improve review evidence, dry-run receipts, tests, docs, closeout reporting, and UI copy. It must not add a real proxy intake call or append-only evidence write.

## Rationale

Scout v0.5 proved the receipt preview lane without allowing imports:

- `scout-v0-5-closeout` passed.
- frontend dry-run UI passed.
- receipt harness passed.
- Level 1 soak passed.
- parked live dry-run blocked without `SCOUT_PROMOTION_SIGNING_KEY`.
- no proxy memory write occurred.
- no coding context write occurred.
- no promotion finalization occurred.
- no unexpected file changes occurred.

The safest next move is to harden the dry-run lane before any real append-only evidence write exists.

## Explicitly Rejected For v0.6

These are not authorized in Scout v0.6:

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

## Allowed v0.6 Work

Scout v0.6 may include small dry-run-only increments:

- clearer receipt preview labels
- better blocked-state explanation when signing key is missing
- stronger closeout profile output
- more focused receipt-preview tests
- UI copy that makes dry-run-only status obvious
- docs that explain rollback and tombstone policy
- manual checks that prove imports remain disabled

Every increment must keep:

- `would_call_proxy_intake: false`
- `would_write_proxy_memory: false`
- `would_write_coding_context: false`
- `would_finalize_promotion: false`
- `mutated: false` for runner profiles

## Required Continuing Gates

Before and after any v0.6 increment, run:

```bash
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json
```

The gate must return:

- `result: pass`
- `read_only: true`
- `mutated: false`
- `parked_dry_run_blocked: true`
- `no_proxy_memory_write: true`
- `no_coding_context_write: true`
- `no_promotion_finalization: true`
- `head_changed: false`

## Next Increment

Recommended next increment:

**Scout v0.6 Phase 0.2: Dry-Run Blocked-State UX Copy**

Goal:

- improve the operator-facing explanation when dry-run is blocked by missing signing key
- keep imports disabled
- keep the response passive
- avoid proxy intake calls, proxy memory writes, coding context writes, and promotion finalization

## Manual Check

```bash
cd /home/source/SpiritOS && grep -n "Scout v0.6 Phase 0.1 Graduation Decision Record\|Option A: Stay Dry-Run-Only\|proxy intake calls\|proxy memory writes\|coding context writes\|Scout v0.6 Phase 0.2" docs/scout-v0-6-graduation-decision-record.md && git diff --check && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{profile,result,read_only,mutated,checks,file_change_verdict:{unexpected_status_delta:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}}'
```

Expected outcome:

- decision record shows Option A
- forbidden actions are present
- `git diff --check` prints nothing
- closeout returns `result: pass`
- `mutated` is `false`
- unexpected status delta is empty
- head changed is false

## Rollback

```bash
rm docs/scout-v0-6-graduation-decision-record.md
```

## Next Permission Gate

Operator approval is required before implementing Scout v0.6 Phase 0.2. The next increment is dry-run UX copy only and must not add proxy intake, proxy memory, coding context, or promotion finalization behavior.
