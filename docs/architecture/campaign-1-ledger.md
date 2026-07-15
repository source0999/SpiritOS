# Campaign 1 Ledger

- Schema: `spiritos-campaign-1-ledger/v2`
- Campaign: `spiritos-campaign-1`; plan: [campaign-1-plan.md](campaign-1-plan.md); state: [campaign-1-state.json](campaign-1-state.json)
- Base: `49e58f2982521c46a1a4fc73ef66461a86643792`; Phase 1 atomic checkpoint parent: `8f9cfd818479a3494e7123697ef36263cf6d184a`; Phase 1 closeout checkpoint: `4e1f849ff34f0f2c5c0d5e34160e9108d969c92b`.
- Branch/worktree: `codex/spiritos-campaign-1-foundation-20260712` / `/home/source/SpiritOS-campaign-1-20260712`
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`.
- Borrowed worktree: SpiritFlix `_worktrees/` is borrowed and untouched.

## Current checkpoint

- Phase: **Phase 1** - P0 authority complete; Campaign 1 full scope open.
- Increment: **campaign1_full_scope_restored_after_phase1_closeout**.
- Atomic checkpoint contents: documentation/state correction only. Restores the original Phase 0-3 Campaign 1 scope, records Phase 1 GO as verified, and reopens full-campaign GO until Phase 2 and Phase 3 are complete.
- Product code changed: none.
- Critical blocker: none.
- GO eligibility: `false` for full Campaign 1; `true` only for Phase 1 authority enforcement.
- Next concrete gate: `phase2_shared_contracts_creation`; Campaign 2 is not started.

## Phase status

| Phase | Status | Evidence / implementation |
| --- | --- | --- |
| Phase 0 - Neutral truth and characterization | completed | baseline characterization, provenance, no-reversion constraints, protected-head policy, and borrowed-worktree containment accepted |
| Phase 1 - P0 authority and deployment enforcement | completed | commit range `8d17286d..4e1f849f`; AR-001/002/003 closed; durable Approval Authority, operator sessions, seven admin writers, Cartographer separation, Design writeback, canonical shell lifecycle, and final browser proof verified |
| Phase 2 - Shared contracts and enforced boundaries | not_started | no `packages/contracts/`; shared OpenAPI/JSON Schema contracts, generated or contract-backed consumers, one minimum enforcement tool, and violation tests remain future work |
| Phase 3 - Context reduction and canonical ownership | not_started | evidence externalization, docs/test discovery exclusions, canonical shell declaration, `labs/` quarantine, Prompt 1 target-plugin extraction, duplicate removal, and test-profile registry remain future work |

## Phase 1 verification retained

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

The Phase 1 checkpoint validation ran `npm run campaign-1:validate-authority`, `npm run campaign-1:validate-continuity`, `git diff --check`, scoped secret scan, and protected-head checks. This ledger correction does not claim new implementation proof for Phases 2 or 3.

## Next gate

`phase2_shared_contracts_creation`

Required start condition: create the shared contract package and first enforcement slice without modifying protected product branches, borrowed `_worktrees/`, or beginning Campaign 2.
