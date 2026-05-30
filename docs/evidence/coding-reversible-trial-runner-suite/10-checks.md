# Checks

- `git diff --check`: PASS
- `npm run typecheck`: PASS
- `npm run test -- visible-result-badge`: PASS, 1 file / 7 tests
- `npm run test -- agent-trials-ui`: PASS, 1 file / 23 tests
- `npm run test:coding-frontend-regression`: PASS, 11 files / 250 tests
- Discovered focused tests with `find src components tests -iname "*coding*.test.*" -o -iname "*cockpit*.test.*" -o -iname "*agent-trials*.test.*" | sort | sed -n '1,180p'`; `components` is not a root directory in this repo.
- Focused active component/catalog tests: `npm run test -- src/components/coding/__tests__/coding-cockpit-shell.test.tsx src/app/coding/__tests__/page.test.tsx src/lib/coding/__tests__/reversible-trial-prompts.test.ts`: PASS, 3 files / 7 tests
- Discovered source proxy pytest files with `find source_proxy -iname "test_*.py" -o -iname "*test*.py" | sort | sed -n '1,180p'`.
- `source_proxy` was not changed in this branch, so no source_proxy pytest target was run.
