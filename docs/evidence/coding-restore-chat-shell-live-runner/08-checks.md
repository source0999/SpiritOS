# Checks

- `git diff --check`: PASS
- `npm run typecheck`: PASS
- `npm run test -- visible-result-badge`: PASS, 1 file / 7 tests
- `npm run test -- agent-trials-ui`: PASS, 1 file / 23 tests
- `npm run test:coding-frontend-regression`: PASS, 11 files / 250 tests
- Discovered active coding tests with `find src components tests -iname "*coding*.test.*" -o -iname "*cockpit*.test.*" -o -iname "*agent-trials*.test.*" | sort | sed -n '1,160p'`; `components` does not exist at repo root, and matching tests were under `src/` and `tests/`.
- Focused active route/component test: `npm run test -- src/components/coding/__tests__/coding-cockpit-shell.test.tsx src/app/coding/__tests__/page.test.tsx`: PASS, 2 files / 5 tests
- `source_proxy` was not changed in this correction branch, so no correction-specific pytest target was run.
