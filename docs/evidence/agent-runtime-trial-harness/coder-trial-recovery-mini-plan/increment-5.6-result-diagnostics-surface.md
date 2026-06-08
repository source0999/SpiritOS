# Increment 5.6 - Result Diagnostics Surface

Status: complete.

Implemented:

- Added post-result surface for selected prompt ID, raw backend status, changed files, checks run, verification status, provenance fields, scaffold/fallback flags, grader output, file scope, provenance status, critical failures, and recommended next action.
- Added `Copy prompt diagnostics`.
- Missing fields render as `none` or `not graded` instead of crashing.
- Scaffold/fallback/backend-generated states are passed to the Gate 6 grader and cannot appear as green PASS through the new mapper.

Verification:

- `npx --no-install tsc --noEmit --pretty false` passed.
- `git diff --check` passed.
- Browser visual verification was blocked by `net::ERR_BLOCKED_BY_CLIENT`; command-line request to `http://127.0.0.1:3000/coding` reached the server but returned `401 Unauthorized`.
