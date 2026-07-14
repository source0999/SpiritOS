# Campaign 1 Isolated Runtime Recovery Receipt

- Date: 2026-07-14
- Scope: Campaign-owned loopback HTTPS candidate only. Protected product heads and the live port-3000 process were read-only and unchanged.
- Candidate: Source Proxy on `127.0.0.1:8877`; Campaign production frontend on `127.0.0.1:3200` behind its Campaign HTTPS proxy on `127.0.0.1:3201`.
- Session/gate isolation: temporary mode-0700 state only; a test-only operator credential and increment-`1.3` gate receipt were never added to the repository, logs, screenshots, evidence, or Git.
- Browser lifecycle: `run-coding-e2e-loop` passed with `overall: PASS`, `authoritative_truth_status: GO`, `commit_safe: true`, and anti-cheat invariant `PASS`.
- Proven chain: visible shell operator control -> HTTP-only session and CSRF -> persisted Source Proxy task/preview -> server-issued durable approval -> canonical `execute-approved` consume/finalize -> reviewer, verifier, evidence, and context acknowledgements -> managed Chromium storefront verification.
- Lifecycle proof: real Prompt 1 applied six bounded fixture files, verified six rendered product cards, performed manifest-backed undo, reset to the clean baseline, and completed a distinct clean rerun.
- Rejection preservation: missing/malformed gate state blocked model execution; no direct caller approval or approval-ID fabrication was used.

## Focused validation

- `npm run typecheck` - passed.
- `npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx` - 61 passed (existing React `act` warnings only).
- `npm run build` - passed in 172.8 s.
- `SPIRITOS_E2E_FRONTEND_ORIGIN=https://127.0.0.1:3201 E2E_LOOP_ISOLATED_CANDIDATE=true ... node scripts/run-coding-e2e-loop.mjs --fixture-state=missing` - passed.

Redaction: no credential value, approval ID, session ID, task ID, model response, or fixture source is recorded in this receipt.
