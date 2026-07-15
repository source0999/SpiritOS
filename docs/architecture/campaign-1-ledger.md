# Campaign 1 Ledger

> 2026-07-15 Phase 3 checkpoint: owner decision applied. `CodingCockpitShell` is canonical; `/design-demo/coding` delegates to `/coding`; chat embeds the canonical cockpit; old shells are labs-only. `docs/evidence/**` (7,489 paths) and `scripts/media/model_gallery/**` (1,846 paths) are archived under `/mnt/spirit-8tb/migration-evidence/spiritos-campaign-1-20260714/` with SHA-256 manifests, zero byte mismatches, zero unreadable files, zero configured secret matches, and rollback records. Git paths reduced from 12,994 to 3,668 (71.8%). Browser Prompt 1/Coder 10 specs, grader, and fixture probe are now target-plugin-owned; context discovery excludes archived/snapshot docs and authoritative ceiling violations fail visibly. Implementation parent: `893c4b5e`; next gate: Python target adapter, duplicate cleanup, test profiles, then runtime/browser proof. Full GO remains false.

> 2026-07-15 Python target-adapter fixture-reset increment: `285065b8` extends the canonical contract through every Coder 10 prompt/context, and requires the canonical Prompt 1 packet for the only fixture-reset mutation. The Next reset route is a body-preserving compatibility delegator; Python resolves the declared repository, worktree, root, source head, prompt, context, and profile before reset, and records the resolved identity on the reset receipt. Missing identity and non-Prompt-1 reset packets fail closed. Focused Python contract/reset/regression tests: 146 passed; reset-route/cockpit tests: 65 passed; typecheck passed. Full selected-prompt runtime/browser proof and remaining duplicate-path reconciliation are still required.

> 2026-07-15 target-command ownership increment: `489f3737` removes generic decision-route ownership of the Prompt 1–3 command selection and task-spec factories. The resolved adapter now owns target command dispatch, target constraints, and the attached verification identity; the generic route delegates only a previously resolved plugin. Coding regression: 141 passed (existing async-mock warnings). Remaining adapter work: verifier/grader direct-fixture bypass enforcement and runtime/browser lifecycle proof.

> 2026-07-15 test-profile registry increment: `99e2b336` adds the canonical named product registry and a fail-closed validator (`CAMPAIGN_1_TEST_PROFILES_VALID`). Each profile declares a product, command, and claim ceiling; closeout cannot treat the prose table as a substitute.

Next gate ID: `phase3_python_target_adapter_duplicate_paths_and_test_profiles`.

Continuity checkpoint: `893c4b5e` is an ancestor implementation anchor; this atomic ledger/state record preserves that policy.

Authority-validator reconciliation: `87c23b3b` verifies the canonical cockpit and labs-only legacy shell through import/mount semantics; the accepted migration no longer causes a stale path failure.

Python target-adapter increment: `af137da5` adds the fail-closed `source_proxy.target_plugins.adapter` identity resolver. The canonical browser packet now declares schema, plugin, repository, worktree, root, selected prompt/context, and execution profile; Prompt Packet resolves and binds the live source head before dispatch. Missing, unsupported, conflicting, stale-head, repository/worktree/root/context/profile, and direct fixture selections block. This is partial: executor, approval, verifier, grader, and evidence acknowledgement migration remains the active gate.

Continuity policy: `af137da58f64c24a6fe0e50faeb9088622a2de64` is retained as an ancestor implementation anchor of this atomic ledger/state checkpoint.

Preview/execution target-adapter increment: `04b0801f7dc42c048fa5fcb300af4779503ac4c7` carries the canonical browser plugin packet into the approval-preview request, resolves it server-side, persists its identity on the task preview, and blocks selected Coder execution when the persisted identity is absent or names another prompt. Verification remains partial until approval consume/finalize, grader, verifier, and evidence all bind the same identity.

Durable identity acknowledgement increment: `11b1ae096868f9ca31b78070b63d1556d4a33ac7` removes the Python target-path plugin chooser. Persist/consume/finalize use the server-resolved identity; selected fixture execution fails without it; executor, reviewer, verifier, and evidence recorder acknowledgements are validated against the identical identity. Authority and long-running tests: 84 passed. Remaining Gate 1 proof is the full selected-prompt runtime/browser lifecycle plus any residual target-specific helpers outside this chain.

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
