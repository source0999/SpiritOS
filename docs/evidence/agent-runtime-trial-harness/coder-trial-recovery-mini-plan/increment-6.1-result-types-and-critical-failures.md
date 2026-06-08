# Increment 6.1 - Result Types and Critical Failures

Status: complete.

Implemented:

- Added result states in `src/lib/coding/dummy-coder-10-prompts.ts`.
- Added `DUMMY_CODER_10_CRITICAL_FAILURE_RULES` in `src/lib/coding/dummy-coder-10-grader.ts`.
- Critical failures include outside dummy root, real app mutation, Source Proxy mutation, root package/lockfile mutation, env/secret path mutation, scaffold/fallback pass, backend-generated pass, provider-call-only proof, and fake verification.

Verification:

- Typecheck passed.
- Diff check passed.
- Focused mapper test file was added, but Vitest execution is blocked by the local resolver failure.
