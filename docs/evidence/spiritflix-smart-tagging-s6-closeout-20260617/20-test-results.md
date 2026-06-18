# Test Results

## Raw Logs

- Initial logs: `raw/tests/01-typecheck.txt`, `raw/tests/02-vitest-admin-smart.txt`, `raw/tests/03-vitest-home-player.txt`
- Rerun logs: `raw/tests/04-rerun-typecheck.txt`, `raw/tests/05-rerun-vitest-admin-smart.txt`, `raw/tests/06-rerun-vitest-home-player.txt`

## Results

Initial required run:
- `npm run typecheck`: PASS
- `npx vitest run src/lib/spiritflix/admin/smart src/components/spiritflix/admin src/app/api/spiritflix/admin`: FAIL with 5 S6-specific failures in metadata bridge, rename preview, and smart panel assertions.
- `npx vitest run src/components/spiritflix/__tests__/SpiritFlixHome.test.tsx src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx`: PASS

Rerun after focused S6 patch:
- `04-rerun-typecheck.txt`: PASS (exit 0)
- `05-rerun-vitest-admin-smart.txt`: PASS (exit 0)
- `06-rerun-vitest-home-player.txt`: PASS (exit 0)

## Failure Classification

The initial admin/smart Vitest failures were S6-specific and fixed within S6 files only:

- metadata sidecar hash normalization for Windows-style path input
- rename preview traversal warning and unsafe-character whitespace normalization
- smart panel tests still expecting S5 text and using a duplicate text query

No unrelated dirty-tree failure required patching.
