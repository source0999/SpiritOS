# Increment 5.2 - Dummy Coder 10 Prompt Bank

Status: complete.

Implemented:

- Added `src/lib/coding/dummy-coder-10-prompts.ts`.
- Defined all 10 LumaCart prompts with required IDs, prompt text, fixture root, allowed write root, forbidden files, expected state, targets, pass/fail expectations, and zero-change/no-op/block flags.
- Added `buildDummyCoder10RunnerPacket` for the structured runner context packet.
- Added tests in `src/lib/coding/__tests__/dummy-coder-10-prompts.test.ts`.

Boundaries:

- Dummy root is exactly `tests/ui-agent-trials/fixtures/dummy-product-site/`.
- Allowed write root is exactly `tests/ui-agent-trials/fixtures/dummy-product-site/**`.
- Forbidden files include real app paths, Source Proxy, backend, docs, env files, root package/lockfiles, `node_modules/**`, and `.git/**`.
- `tests/ui-agent-trials/fixtures/dummy-product-site/` was not created.

Verification:

- `npx --no-install tsc --noEmit --pretty false` passed.
- `git diff --check` passed for the touched Gate 5/6 files.
- Focused Vitest did not run due to environment resolver failure: `Cannot find module 'Z:\@id\Z:\node_modules\vitest\dist\index.js'`.
