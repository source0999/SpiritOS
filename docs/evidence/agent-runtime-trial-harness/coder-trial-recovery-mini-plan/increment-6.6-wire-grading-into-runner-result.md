# Increment 6.6 - Wire Grading Into Runner Result

Status: complete.

Implemented:

- The LumaCart run-one result surface now shows raw backend status, grader result state, score, label, reason, critical failures, changed-file scope status, provenance/trust status, and recommended next action.
- Grader can override backend-looking success to `INVALID` or `NEEDS_FIX`.
- Missing diagnostics are rendered safely.

Verification:

- Typecheck passed.
- Diff check passed.
- Browser smoke was blocked by `net::ERR_BLOCKED_BY_CLIENT`.
