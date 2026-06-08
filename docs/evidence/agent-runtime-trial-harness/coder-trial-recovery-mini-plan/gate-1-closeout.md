# Gate 1 Closeout

## Fallback/scaffold locations found

- `source_proxy/planning/bounded_create.py`
- `source_proxy/planning/architect.py`
- `source_proxy/tasks/long_running.py`
- `src/lib/coding/durable-run-types.ts`
- `src/lib/coding/durable-run-store.ts`
- `src/components/coding/CodingCockpitShell.tsx`
- `scripts/coder-frontend-acceptance-v2.js`

## Trial-mode ban contract

- `allow_known_scaffold=false`
- `allow_generic_scaffold=false`
- `allow_deterministic_stub=false`
- `allow_backend_generated_page=false`
- `allow_fallback_to_pass=false`
- `require_model_authored_diff=true`

## Files changed

See final closeout for full current diff. Gate 1 code changes are concentrated in source-proxy bounded create/long-running/provenance tests and frontend durable trial provenance surfaces.

## Tests added

- Source proxy scaffold/fallback no-PASS tests in `source_proxy/tests/test_coding_regression_pack.py`.
- Frontend no-diff/provenance/durable-row focused tests in existing Vitest files.

## Tests run

- Gate 1 exact Python scaffold tests: passed.
- Verification contracts/diff verification: passed, `Ran 50 tests ... OK`.
- Frontend focused trial tests: passed, `59 passed`.

## Whether scaffold can still count as PASS

No. Scaffold/fallback/provenance-missing rows must be INVALID or NEEDS_FIX in trial mode.

## Whether provider_call_made=true can still be treated as model proof

No. Provider-call truth is only call evidence; model-authored diff provenance is required.

## Whether suite-mq4in5v9 is marked invalid

Yes, marked invalid in Increment 1.1 evidence and final closeout.

## Current git status

Dirty worktree, all changes preserved. No reset/stash/clean/delete.

## Gate 1 result

GO for Gate 2.
