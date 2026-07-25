# Campaign 0 Segment 0C Registered Regression Green Addendum - 2026-07-25

## Status

Addendum to `segment-0c-lumacart-repair-evidence-20260725.md`.

The earlier Segment 0C evidence recorded two blockers:

- `.venv-campaign1/bin/python` missing for the exact registered npm runner.
- Three fallback `test_coding_regression_pack.py` failures.

Both were traced to missing ignored dependency bindings in the isolated Campaign 0 checkout, not to Segment 0C production code:

- `.venv-campaign1` was absent, so `npm run test:coding-regression` could not start.
- `node_modules` was absent, so TypeScript-backed validation failed with `Cannot find module 'typescript'`.

## Dependency Binding

Local ignored bindings added in the isolated checkout:

```text
.venv-campaign1 -> /home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy
node_modules -> /home/source/SpiritOS/node_modules
```

Ignore state:

- `node_modules` is ignored by repository `.gitignore`.
- `.venv-campaign1` is ignored through the linked worktree local exclude at `/home/source/.campaign-3-5-execution-repository-20260719.git/info/exclude`.

No dependency symlink is committed.

## Exact Registered Regression

Command:

```bash
cd /home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725
npm run test:coding-regression
```

Result:

```text
139 passed, 46 subtests passed in 38.27s
```

The exact registered command now runs through `.venv-campaign1/bin/python` as declared in `package.json`.

## Frontend Regression

Command:

```bash
cd /home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725
npm run test:coding-frontend-regression
```

Result:

```text
Test Files 10 passed (10)
Tests 193 passed (193)
```

Observed stderr:

- React `act(...)` warnings from `src/app/coding/__tests__/page.test.tsx`.
- Warnings did not fail the registered frontend regression command.

## Build Lane Note

Command:

```bash
cd /home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725
npm run build
```

Result:

```text
next build --webpack
Creating an optimized production build ...
Segmentation fault (core dumped)
```

The same `npm run build` segfault reproduces in the established Source Proxy worktree `/home/source/SpiritOS-source-proxy-20260711` at `594d66ef8280953af767a273d7c91be765d1a6eb`, so this is recorded as an inherited build/toolchain lane note rather than a Segment 0C acceptance blocker or Segment 0C repair regression.

## Segment 0C Gate Update

Segment 0C LumaCart repair remains as committed in:

- `b727c6d23b3fcfab3af4e4691e3fb2b98b319e73`

Registered Python coding regression now passes with the exact registered command after restoring ignored dependency bindings. Frontend coding regression also passes. The inherited build segfault is documented as a separate lane note and does not block Segment 0C acceptance.
