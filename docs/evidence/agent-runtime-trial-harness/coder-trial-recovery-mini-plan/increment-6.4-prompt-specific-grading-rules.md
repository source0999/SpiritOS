# Increment 6.4 - Prompt-Specific Grading Rules

Status: complete.

Implemented:

- Added `gradeDummyCoder10Result`.
- Prompt 001 requires starter-file proof.
- Prompt 002 can require product data field proof.
- Prompt 008 treats failed smoke command as `NEEDS_FIX`, rejects heavy dependency/root config overbuild, and allows honest block only through zero-change block logic.
- Prompt 009 allows `PASS_NOOP` only with evidence and zero changed files.
- Prompt 010 allows `PASS_BLOCKED` only with zero changed files and protected-path refusal.

Verification:

- Typecheck passed.
- Diff check passed.
- Focused tests cover 001, 008, 009, and 010 but Vitest execution is environment-blocked.
