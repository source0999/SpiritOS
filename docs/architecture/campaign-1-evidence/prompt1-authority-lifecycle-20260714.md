# Campaign 1 Prompt 1 Authority Lifecycle Receipt

- Date: 2026-07-14
- Candidate: isolated Campaign 1 production build on loopback-only HTTPS ports; protected product heads were read-only and unchanged.
- Browser result: `node scripts/run-coding-e2e-loop.mjs --fixture-state=missing` returned `overall: PASS`, `authoritative_truth_status: GO`, `anti_cheat_invariant: PASS`, and `commit_safe: true`.
- Chain: selected Prompt 1 created a Source Proxy task, persisted a server preview, authenticated the local operator, issued a durable server-owned approval, consumed and finalized it during `execute-approved`, then verified the result in managed Chromium.
- Binding proof: task and target matched the preview; canonical diff hash matched; canonical context was consumed; planner, coder, reviewer, verifier, and final receipt builder acknowledged the shared approval generation.
- Rejection proof: direct legacy caller-issued `approved: true` task approval returns `410` with `approval_client_authority_removed`, and leaves the target unchanged.
- Redaction: no credentials, raw approval IDs, session identifiers, task identifiers, or source contents are recorded here.

## Focused validation

- `npm run typecheck`
- focused authority Vitest: 27 passed
- coding regression: 131 passed, 40 subtests passed
- coding frontend regression: 269 passed
- Source Proxy authority/task tests: 78 passed
