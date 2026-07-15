# Campaign 1 Ledger

> 2026-07-15 Phase 3 checkpoint: owner decision applied. `CodingCockpitShell` is canonical; `/design-demo/coding` delegates to `/coding`; chat embeds the canonical cockpit; old shells are labs-only. `docs/evidence/**` (7,489 paths) and `scripts/media/model_gallery/**` (1,846 paths) are archived under `/mnt/spirit-8tb/migration-evidence/spiritos-campaign-1-20260714/` with SHA-256 manifests, zero byte mismatches, zero unreadable files, zero configured secret matches, and rollback records. Git paths reduced from 12,994 to 3,668 (71.8%). Browser Prompt 1/Coder 10 specs, grader, and fixture probe are now target-plugin-owned; context discovery excludes archived/snapshot docs and authoritative ceiling violations fail visibly. Implementation parent: `893c4b5e`; next gate: Python target adapter, duplicate cleanup, test profiles, then runtime/browser proof. Full GO remains false.

Next gate ID: `phase3_python_target_adapter_duplicate_paths_and_test_profiles`.

- Schema: `spiritos-campaign-1-ledger/v2`
- Campaign: `spiritos-campaign-1`; plan: [campaign-1-plan.md](campaign-1-plan.md); state: [campaign-1-state.json](campaign-1-state.json)
- Base: `49e58f2982521c46a1a4fc73ef66461a86643792`; Phase 1 atomic checkpoint parent: `8f9cfd818479a3494e7123697ef36263cf6d184a`; Phase 1 closeout checkpoint: `4e1f849ff34f0f2c5c0d5e34160e9108d969c92b`.
- Branch/worktree: `codex/spiritos-campaign-1-foundation-20260712` / `/home/source/SpiritOS-campaign-1-20260712`
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`.
- Borrowed worktree: SpiritFlix `_worktrees/` is borrowed and untouched.

## Current checkpoint

- Phase: **Phase 3** - context reduction and canonical ownership.
- Increment: **phase2_shared_contracts_complete_phase3_canonical_shell_discovery**.
- Atomic checkpoint contents: records the Phase 2 implementation commit `a36c4437` and the first Phase 3 gate result; no Phase 3 product or evidence mutation was made.
- Product code changed: Phase 2 only — schema-backed shared contracts and ESLint import boundaries.
- Critical blocker: `CodingAgentInterface.tsx` is live-mounted by `src/app/design-demo/coding/page.tsx` and `src/components/chat/SpiritTrinityChatShell.tsx`. Moving it to `labs/` would break both callers; the campaign plan designates this as an owner decision.
- GO eligibility: `false` for full Campaign 1; Phase 2 only is complete.
- Next concrete gate: `phase3_canonical_shell_owner_decision`; Campaign 2 is not started.
- Continuity repair: active-phase validation accepts a documented ancestor implementation checkpoint only from an atomic ledger/state checkpoint; this checkpoint revalidates `a36c4437` as the Phase 2 implementation anchor.

## Phase status

| Phase | Status | Evidence / implementation |
| --- | --- | --- |
| Phase 0 - Neutral truth and characterization | completed | baseline characterization, provenance, no-reversion constraints, protected-head policy, and borrowed-worktree containment accepted |
| Phase 1 - P0 authority and deployment enforcement | completed | commit range `8d17286d..4e1f849f`; AR-001/002/003 closed; durable Approval Authority, operator sessions, seven admin writers, Cartographer separation, Design writeback, canonical shell lifecycle, and final browser proof verified |
| Phase 2 - Shared contracts and enforced boundaries | completed | `a36c4437`; `packages/contracts/` OpenAPI + nine schemas, Python task/retest validation, Next receipt validation, one ESLint enforcement surface, and deliberate violation tests |
| Phase 3 - Context reduction and canonical ownership | blocked | verified two live `CodingAgentInterface.tsx` production callers; owner decision is required before the required labs move. No Phase 3 mutation has occurred. |

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

`phase3_canonical_shell_owner_decision`

Required start condition: Britton decides whether `/design-demo/coding` and the embedded Spirit Trinity chat should migrate to the canonical cockpit, be retired, or remain supported. Do not move a live shell to `labs/` before that decision.
