# Increment 2.6.2 Explicit Mac Advisory Opt-In

Date: 2026-05-28

## Scope

Allowed work for this increment:

- Add a small explicit opt-in bridge if missing.
- Keep bridge clear and safe.
- Do not add default autonomous execution.
- Do not add hidden background work.
- Do not grant write authority.
- Do not route all tasks to Mac.
- Surface Mac used/job/success/failure/candidate files/summary/error/reason/advisory-only state.
- Keep changes minimal.
- Do not redesign `/coding`.

## Files changed

- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.6.2-explicit-mac-advisory-opt-in.md`

## UI behavior added

In the existing Realistic Prompt Tester Mac Mini worker panel, added an explicit button:

```text
Use Mac for context/check support
```

The button:

- is user-clicked only
- calls `POST /api/coding/mac-worker`
- uses job type `source_proxy_context_discovery`
- sends the active draft prompt or selected trial prompt
- requests max 5 results
- updates Mac worker status from the API response
- displays advisory-only result state

Displayed fields:

- advisory only
- run status
- advisory job
- summary
- candidate files
- reason code when present
- error when present

The bridge does not:

- apply fixes
- write files
- commit
- push
- change providers
- start hidden workers
- route all tasks to Mac
- mutate Cartographer
- mutate Scout production data

## Checks run

### Focused component test

Command:

```bash
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx -t "runs explicit Mac advisory" --reporter=dot
```

Result:

```text
Test Files  1 passed (1)
Tests  1 passed | 74 skipped (75)
```

Added test coverage:

- opens Realistic Prompt Tester
- clicks explicit Mac advisory support button
- verifies `POST /api/coding/mac-worker`
- verifies job type `source_proxy_context_discovery`
- verifies advisory-only state
- verifies candidate files are displayed

### Mac worker contract/API tests

Command:

```bash
npx --no-install vitest run src/lib/mac-worker/__tests__/contract.test.ts src/app/api/coding/mac-worker/__tests__/route.test.ts --reporter=dot
```

Result:

```text
Test Files  2 passed (2)
Tests  11 passed (11)
```

### Typecheck

Command:

```bash
npx --no-install tsc --noEmit --pretty false
```

Result:

```text
passed with no output
```

### Whitespace diff check

Command:

```bash
git diff --check
```

Result:

```text
passed with no output
```

### Broad component test note

The first full component test run failed in the new test because the assertion matched the same candidate file in both the new Mac panel and existing prompt preview. The test assertion was narrowed to the `Mac Mini worker usage` panel, and the focused test passed.

Full component test suite is scheduled again in Increment 2.7.2.

## Safety confirmation

- No autonomous Mac execution was added.
- No hidden background work was added.
- No write authority was granted.
- No apply, commit, push, provider change, Cartographer activation, or Scout production mutation path was added.
- No Mac worker job runs unless the user clicks the explicit opt-in button.
- The result is advisory-only.

## GO / NO-GO

GO for Increment 2.6.2 complete.

Next authorized increment: Increment 2.6.3, run realistic proxy flow using Mac context/check support.
