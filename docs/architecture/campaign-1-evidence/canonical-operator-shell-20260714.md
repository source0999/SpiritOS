# Campaign 1 Canonical Operator Shell Receipt

- Date: 2026-07-14
- Canonical owner: `src/components/coding/CodingCockpitShell.tsx`; no other coding shell issues approval requests.
- UI boundary: the shell removes native credential prompts, keeps the operator credential only for the session POST, clears it before awaiting the response, and retains only in-memory CSRF/session status.
- Server boundary: the existing HTTP-only cookie, server session state, Origin/Host validation, CSRF, expiry, and revocation remain authoritative. The UI submits no approval binding beyond persisted preview ID, generation, action, task ID, and CSRF.
- Coder 10 fixture: authenticates through the visible control before strict apply/reverse assertions; no session, approval, or `approved: true` injection is used.
- Browser proof: the rebuilt loopback production candidate completed Prompt 1 with `overall: PASS`, `authoritative_truth_status: GO`, `anti_cheat_invariant: PASS`, and matching planner/coder/reviewer/verifier/final-receipt acknowledgement.
- Build: clean `npm run build` completed in 3:00.89 with 2,093,416 KB peak RSS and exit 0.
- Regression: shell 61 passed; operator/session and approval routes 5 passed; Source Proxy authority/task 78 passed; coding regression 131 passed with 40 subtests; frontend coding regression 269 passed.
- Redaction: no credential, session identifier, CSRF value, approval ID, task ID, or source content is recorded.
