# Scout v0.5 Phase 5.3 Manual Import CLI Gate

status: implemented/manual-controlled

Status date: 2026-05-20

This document records the Phase 5.3 manual import CLI gate. The increment adds a dry-run-only operator command for one approved Scout promotion. It does not call proxy intake, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Operator Command

```bash
python3 scout/scripts/import_promotion_dry_run.py --promotion-id PROMOTION_ID --requested-by Britton --json
```

For parked-state checks where the live service intentionally has no signing key:

```bash
python3 scout/scripts/import_promotion_dry_run.py --promotion-id 00000000-0000-0000-0000-000000000000 --requested-by manual-check --json --allow-blocked
```

## Safety Contract

The command is dry-run only. It must always report:

- `dry_run: true`
- `read_only: true`
- `mutated: false`
- `mutation_allowed: false`
- `would_call_proxy_intake: false`
- `would_write_proxy_memory: false`
- `would_write_coding_context: false`
- `would_finalize_promotion: false`

The command must not:

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

## Blocked State

When a safety precondition is missing, the command returns:

- `result: blocked`
- `detail`
- `dry_run: true`
- `read_only: true`
- `mutated: false`

The `--allow-blocked` flag exists for parked-state checks. It lets the command exit 0 when the dry-run is safely blocked by missing configuration or missing promotion data. It does not bypass any safety precondition.

## Acceptance Criteria

Phase 5.3 is accepted only when:

- compile checks pass
- the CLI returns a safe blocked response for the parked live state
- the dry-run contract terms are present in this document
- `git diff --check` passes
- Level 1 soak still passes
- no proxy intake call occurs
- no proxy memory write occurs
- no coding context write occurs
- no promotion finalization occurs

## Rollback

```bash
rm docs/scout-v0-5-manual-import-cli-gate.md scout/scripts/import_promotion_dry_run.py
```

## Next Permission Gate

Operator approval is required before Phase 5.4 or any implementation that can call proxy intake. The recommended next increment is Phase 5.4: Manual Import UI Dry-Run Button, still dry-run only and still blocked from proxy intake calls.
