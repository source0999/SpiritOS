# Scout v0.5 Phase 5.2 Manual Import Dry-Run Contract

status: implemented/manual-controlled

Status date: 2026-05-20

This document records the Phase 5.2 manual import dry-run contract. The increment validates one approved Scout promotion payload without calling proxy intake, without finalizing the promotion, without writing proxy memory, without writing coding context, without registering workers, without scheduled writes, without applying code, without committing, and without pushing.

## Purpose

Phase 5.2 gives the operator a safe preflight before any Scout-to-Proxy import is allowed. It answers one question: is this approved promotion payload structurally ready for a later manual import?

It does not import anything.

## Contract

Endpoint:

```text
POST /v1/scout/promotions/import-dry-run
```

Input:

```json
{
  "promotion_id": "approved-promotion-id",
  "requested_by": "operator-name"
}
```

Required preconditions:

- promotion exists
- promotion status is `approved`
- packet exists
- verdict exists
- verdict decision is `promote`
- stored promotion payload SHA-256 still matches the current packet payload
- `SCOUT_PROMOTION_SIGNING_KEY` is configured

Output must include:

- `dry_run: true`
- `import_ready: true`
- `read_only: true`
- `mutation_allowed: false`
- `would_call_proxy_intake: false`
- `would_write_proxy_memory: false`
- `would_write_coding_context: false`
- `would_finalize_promotion: false`
- `approval_required_before`
- `forbidden_actions`

## Safety Boundary

The dry-run must not:

- call `/v1/scout-intake/promotion`
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

## Validation Notes

The dry-run builds the same signed payload shape used by a later import path, but it never sends the payload. It returns a signature preview and signed payload hash so the operator can confirm the preflight without exposing the full signature.

The dry-run rejects stale payloads by comparing the stored promotion payload hash to the current packet hash. This prevents a previously approved promotion from silently importing changed packet content.

## Acceptance Criteria

Phase 5.2 is accepted only when:

- compile checks pass
- isolated runtime dry-run validates an approved `promote` promotion
- isolated runtime dry-run leaves the promotion status unchanged
- no audit file is created by dry-run
- live Scout service exposes the route
- Level 1 soak still passes
- promotion queue remains stable
- no proxy memory write occurs
- no coding context write occurs

## Rollback

```bash
git restore scout/src/scout/api/promotions.py scout/src/scout/packets/promotions.py scout/src/scout/tests/test_promotions.py
rm docs/scout-v0-5-manual-import-dry-run-contract.md
```

## Next Permission Gate

Operator approval is required before Phase 5.3 or any code that calls proxy intake. The recommended next increment is Phase 5.3: Manual Import Operator UI or CLI Gate, still with proxy intake calls disabled by default until a separate explicit approval.
