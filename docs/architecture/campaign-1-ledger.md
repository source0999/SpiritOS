# Campaign 1 Ledger

- Schema: `spiritos-campaign-1-ledger/v2`
- Campaign: `spiritos-campaign-1`; plan: [campaign-1-plan.md](campaign-1-plan.md); state: [campaign-1-state.json](campaign-1-state.json)
- Base: `49e58f2982521c46a1a4fc73ef66461a86643792`; final atomic checkpoint parent: `8f9cfd818479a3494e7123697ef36263cf6d184a`.
- Branch/worktree: `codex/spiritos-campaign-1-foundation-20260712` / `/home/source/SpiritOS-campaign-1-20260712`
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`.
- Borrowed worktree: SpiritFlix `_worktrees/` is borrowed and untouched.

## Final checkpoint

- Phase: **Campaign 1 complete**; increment: **phase1 final authority acceptance and closeout**.
- Atomic checkpoint contents: final redacted evidence reconciliation; the authenticated all-writer SpiritFlix authority slice; and the long-lived Source Proxy task-readback BFF dispatcher plus focused regression. No product branch, protected worktree, service, or borrowed worktree was edited.
- Critical blocker: none.
- GO eligibility: `true`.
- Next concrete gate: `campaign1_complete`; Campaign 2 is not started.

## Gate status

| Gate | Status | Evidence / implementation |
| --- | --- | --- |
| Authenticated SpiritFlix no-reversion | completed baseline | protected-head browser baseline and cross-product receipt |
| Approval Authority bootstrap/lifecycle | completed | durable persisted bindings, transactional consume/finalize, redacted evidence |
| AR-001 all seven admin writers | completed | strict authenticated issuer, server-derived bindings, canonical `spiritflix-admin-executor`, 19 route/lifecycle and 3 Source Proxy tests |
| AR-002 Cartographer durable selection/consumer | completed | 263-test profile and durable selection receipt; direct legacy mutations fail closed |
| AR-003 Design durable writeback | completed | 32 production-route tests and 9 receipt-negative cases |
| Canonical coding shell/Prompt 1 | completed | visible operator control, server-issued approval, exact acknowledgement envelope, Coder 10 migration |
| Production task readback | completed | task status and verification BFF use `sourceProxyLongJsonFetch`; 6 focused tests; prevents default 10-second connect cap during real post-apply work |
| Isolated production browser lifecycle | completed | authoritative harness `PASS` / `GO` / `commit_safe=true`: model-authored six-file apply, Chromium six-card proof, undo/reset, clean rerun |
| Final matrix/closeout | completed | current focused profiles, typecheck/build, validators, secret scan, diff check, and protected-head recheck |

## Final verification

- `src/app/v1/operator/spiritflix-admin-approval` lifecycle/route plus all bounded writer/operator-session tests: **8 files, 19 passed**.
- `source_proxy/tests/test_spiritflix_admin_authority.py source_proxy/tests/test_operator_session_assertion.py`: **3 passed**.
- Cartographer API profile: **263 passed**, 3 existing deprecation warnings.
- Approval Authority and long-running task profile: **83 passed**, 1 existing deprecation warning.
- Design production-route profile: **32 passed**; receipt negatives: **9 passed**.
- Coding backend regression: **131 passed**, 10 existing async-mock warnings.
- Coding frontend regression: **11 files, 269 passed**, existing React `act(...)` warnings.
- Long-lived task-readback regression: **2 files, 6 passed**.
- `npm run typecheck`: passed. `npm run build`: passed.
- Isolated managed Chromium harness: **PASS**, authoritative truth **GO**, `commit_safe=true`; no credential, cookie, approval ID, task ID, media path, or raw model output is committed.

The atomic checkpoint validation reruns `npm run campaign-1:validate-authority`, `npm run campaign-1:validate-continuity`, `git diff --check`, scoped secret scan, and protected-head checks. Runtime fixture reset and Campaign-only process cleanup completed before closeout.
