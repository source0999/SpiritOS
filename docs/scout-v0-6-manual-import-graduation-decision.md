# Scout v0.6 Manual Import Graduation Decision

status: planning/manual-controlled

Status date: 2026-05-20

This document plans the Scout v0.6 decision after Scout v0.5 closed out the manual import receipt dry-run lane. It is planning only. It does not call proxy intake, does not emit actual receipts, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Current Verified State

The Scout v0.5 closeout gate passed:

- `scout-v0-5-closeout` returned `result: pass`.
- `read_only` was `true`.
- `mutated` was `false`.
- required receipt docs were present.
- required safety terms were present.
- frontend test passed.
- receipt harness passed.
- Level 1 soak passed.
- parked live dry-run blocked without `SCOUT_PROMOTION_SIGNING_KEY`.
- no proxy memory write was reported.
- no coding context write was reported.
- no promotion finalization was reported.
- no unexpected file changes occurred.
- HEAD did not change.

Scout v0.5 is manual-controlled. It supports recommendations, dry-run validation, receipt preview, UI preview, and closeout checks. It still does not import into proxy memory.

## Decision Question

Scout v0.6 must decide one of three paths:

1. Stay dry-run-only.
2. Add a single explicit append-only evidence write.
3. Defer import work and improve review ergonomics.

No path should add automatic proxy memory writes or coding context writes.

## Option A: Stay Dry-Run-Only

Goal:

- Keep Scout v0.6 as a safer hardening release.

Allowed actions:

- improve docs
- improve receipt preview copy
- improve tests
- improve closeout runner output
- improve UI display of dry-run evidence

Forbidden actions:

- proxy intake call
- append-only intake write
- proxy memory write
- coding context write
- promotion finalization
- hidden worker
- scheduled write

Recommendation:

- safest default if there is any uncertainty about receipt rollback, signing keys, or operator workflow.

## Option B: Single Explicit Append-Only Evidence Write

Goal:

- Allow one operator-confirmed import to write an append-only evidence record.

Required gates before implementation:

- operator chooses one approved promotion
- promotion status is `approved`
- verdict decision is `promote`
- dry-run returns `import_ready: true`
- receipt preview has all required safety fields
- `SCOUT_PROMOTION_SIGNING_KEY` is configured
- `SOURCE_PROXY_SCOUT_INTAKE_LOG` is configured
- operator gives explicit import confirmation

Allowed action:

- one append-only evidence record

Still forbidden:

- proxy memory write
- coding context write
- active context write
- automatic packet promotion
- automatic promotion finalization
- scheduled import
- hidden background worker
- source activation
- discovery execution
- candidate extraction
- apply action
- commit
- push

Required receipt fields:

- `event: scout_manual_import_receipt`
- `manual_controlled: true`
- `authority: append_only_evidence`
- `applied: false`
- `approved_proxy_action: false`
- `writes.proxy_memory: false`
- `writes.coding_context: false`
- `writes.active_context: false`
- rollback tombstone instructions

Recommendation:

- only choose this path if the operator wants a real audit-evidence bridge and accepts append-only log management.

## Option C: Defer Import And Improve Review Ergonomics

Goal:

- Keep imports disabled and improve manual review before any evidence write exists.

Possible increments:

- better promoted packet filtering
- receipt preview copy improvements
- visible reason why dry-run is blocked
- better dry-run CLI receipt formatting
- closeout profile summary improvements

Forbidden actions:

- proxy intake call
- append-only intake write
- proxy memory write
- coding context write
- promotion finalization

Recommendation:

- best if the operator wants more confidence before any import write exists.

## Recommended v0.6 Path

Recommended next step:

**Scout v0.6 Phase 0.1: Graduation Decision Record**

Choose Option A, B, or C in a docs-only decision record before implementing anything.

Default recommendation:

- choose Option A unless the operator explicitly requests a real append-only evidence write
- keep Scout manual-controlled
- keep proxy memory and coding context writes off
- keep all import behavior blocked without a separate permission gate

## Acceptance Criteria For v0.6 Planning

- Scout v0.5 closeout remains reproducible.
- `scout-v0-5-closeout` returns `pass`.
- no proxy intake call occurs.
- no proxy memory write occurs.
- no coding context write occurs.
- no promotion finalization occurs.
- no hidden background worker exists.
- no scheduled write exists.
- a chosen v0.6 option is documented before implementation.
- UI copy does not overclaim autonomy.

## Manual Check

```bash
cd /home/source/SpiritOS && grep -n "Scout v0.6 Manual Import Graduation Decision\|Stay Dry-Run-Only\|Single Explicit Append-Only Evidence Write\|Defer Import\|Scout v0.6 Phase 0.1\|Next Permission Gate" docs/scout-v0-6-manual-import-graduation-decision.md && git diff --check && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{profile,result,read_only,mutated,checks,file_change_verdict:{unexpected_status_delta:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}}'
```

Expected outcome:

- decision options are present
- `git diff --check` prints nothing
- closeout returns `result: pass`
- `mutated` is `false`
- unexpected status delta is empty
- head changed is false

## Rollback

```bash
rm docs/scout-v0-6-manual-import-graduation-decision.md
```

## Next Permission Gate

Operator approval is required before implementing any Scout v0.6 code. The next increment is **Scout v0.6 Phase 0.1: Graduation Decision Record**, docs-only, choosing Option A, B, or C.
