# SpiritOS Campaign 1 Plan

## Identity, status, and firewall

- Campaign: `spiritos-campaign-1`, structural authority foundation across Phases 0-3.
- Mutable root: `/home/source/SpiritOS-campaign-1-20260712` on `codex/spiritos-campaign-1-foundation-20260712`; base `49e58f2982521c46a1a4fc73ef66461a86643792`.
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`.
- Never mutate protected product worktrees, product branches, services, or SpiritFlix's borrowed `_worktrees/`. Do not push or begin Campaign 2.

Status vocabulary: `completed` means committed and verified; `not_started` means no accepted implementation exists; `partial` means bounded work exists but is not accepted; `blocked` means an external prerequisite is required; `invalidated` means current evidence contradicts the recorded claim.

## Campaign phase map

Campaign 1 was originally scoped as Phases 0-3. The Phase 1 closeout at `4e1f849f` is a verified P0 authority GO, not a full Campaign 1 GO. Phase 2 and Phase 3 are now implemented and verified; this plan records full Campaign 1 closure without starting Campaign 2.

| Phase | Name | Status | Evidence / next gate |
| --- | --- | --- | --- |
| Phase 0 | Neutral truth and characterization | COMPLETED | Baseline characterization, no-reversion constraints, provenance anchors, borrowed-worktree containment, and protected-head policy established. |
| Phase 1 | P0 authority and deployment enforcement | COMPLETED | Commit range `8d17286d..4e1f849f`; AR-001/002/003 closed with fail-closed proofs and durable authority evidence. |
| Phase 2 | Shared contracts and enforced boundaries | COMPLETED | Commit `a36c4437`; shared OpenAPI/JSON Schema package, Python/Next schema consumers, ESLint boundaries, and deliberate violation tests pass. |
| Phase 3 | Context reduction and canonical ownership | COMPLETED | Canonical target adapter, duplicate-path reconciliation, truthful test-profile registry, isolated authenticated browser lifecycle, build, and closeout reconciliation verified. |

## Phase 0 - Neutral truth and characterization

Status: **COMPLETED**.

The authenticated SpiritFlix no-reversion/browser baseline, provenance, source-head binding, and borrowed-worktree containment are accepted baseline constraints. They permit no product edits and must be rechecked before future phase closeouts.

## Phase 1 - P0 authority and deployment enforcement

Status: **COMPLETED**.

Commit range: `8d17286d..4e1f849f`.

1. **AR-001 SpiritFlix authority - completed.** The ordinary BFF session remains non-administrative; all seven bounded admin writers migrated from fail-closed placeholders to authenticated server-owned preview/issuance/consume/finalize execution through the canonical `spiritflix-admin-executor`.
2. **AR-002 Cartographer separation - completed.** Duplicate/shadow routes are removed, legacy mutation helpers fail closed before work, and the durable proposal selection consumer is bounded and regression-tested.
3. **AR-003 Design writeback - completed.** Durable preview, authenticated issuance, canonical writeback consumption/finalization, matched acknowledgement, and redacted receipt enforcement are verified.
4. **Approval Authority - completed.** Durable SQLite authority binds repository, worktree, root, target, canonical plugin, content/context, source HEAD, consumer, generation, TTL, transactional consume/finalize, cancellation, acknowledgement, and redacted evidence.
5. **Authenticated operator issuance - completed.** The server-owned `spiritos-local-operator` with role `approval-issuer` may issue only persisted previews. Session, expiry, revocation, trusted Origin/Host, CSRF, role, audit, and server-resolved canonical bindings gate issuance. Browser `approved:true` and browser-supplied authority bindings are invalid.
6. **Canonical coding shell lifecycle - completed.** The visible in-shell operator control, real `/coding` lifecycle, Prompt 1 target-plugin binding, server-assigned executor, durable acknowledgement envelope, and production browser proof are recorded.

Phase 1 GO is verified complete. This does not close Phases 2 or 3.

## Phase 2 - Shared contracts and enforced boundaries

Status: **COMPLETED** at `a36c4437`.

Purpose: convert duplicated Python/TypeScript boundary knowledge into shared, enforceable contracts that services and tests consume from one source of truth.

Required deliverables:

- Create `packages/contracts/`.
- Add OpenAPI and JSON Schema contracts for `source-proxy`, `spiritflix`, `scout`, `cartographer`, `mac-worker`, `design`, `verification`, `deployment`, and shared primitives.
- Replace manual Python/TypeScript duplication for task, verdict, provider, receipt, approval, identity, and deployment boundary schemas with generated or contract-backed definitions.
- Choose exactly one minimum boundary enforcement tool for the first accepted implementation slice, then document why it is the minimum viable enforcement surface.
- Add violation tests that fail when a route, worker, shell, or helper bypasses the shared contract or drifts from it.
- Keep Phase 1 authority invariants intact while moving schemas and client/server bindings behind contracts.

Phase 2 acceptance is met at `a36c4437`: `packages/contracts/` provides OpenAPI and nine JSON Schema surfaces; Python validates task and verification lifecycle payloads, Next maps receipt transport casing then validates the canonical shared schema, and ESLint rejects contract/product/labs/fixture/product-crossing violations. Focused Python and Vitest violation tests and `npm run typecheck` pass.

## Phase 3 - Context reduction and canonical ownership

Status: **COMPLETED**. `/coding` is canonical, `/design-demo/coding` delegates, chat embeds the constrained canonical cockpit, and legacy shells are labs-only.

Purpose: reduce repository/context load, declare canonical ownership surfaces, and quarantine non-production experiments so future agents and humans can reason from the same small set of authoritative paths.

Required deliverables:

- Externalize evidence to `SPIRITOS_EVIDENCE_ROOT`, retaining only manifests, hashes, and redacted receipts in Git. Target approximately 72% fewer tracked paths; current audit observed 12,976 tracked paths with 7,489 still evidence.
- Exclude docs/evidence from TypeScript and Vitest discovery where they are not intended source inputs.
- Declare one canonical coding shell and quarantine alternate coding shells under `labs/`.
- Create a `labs/` directory for non-canonical shells, experiments, and deprecated proof harnesses.
- Extract Prompt 1 behind the target-plugin adapter instead of leaving prompt-specific logic in duplicate shell or route surfaces.
- Remove duplicate routes/helpers that survived Phase 1 because they were not part of the P0 authority enforcement slice.
- Create a test-profiles registry that truthfully labels unit, source-text, route, production-path, browser, and runtime proof.

The historic no-caller blocker was resolved by the owner decision and implementation. Final acceptance proved the fail-closed Python target adapter across execution/verification/evidence, reconciled the classified duplicate inventory, ran the truthful production test profiles, completed the isolated authenticated Prompt 1 browser lifecycle (including undo/reset and clean rerun), passed the build, reconciled protected heads, and refreshed the Campaign handoff artifacts.

## GO, failures, and turn ends

- `GO_PHASE_1_AUTHORITY_COMPLETE`: verified at `4e1f849f`. Phase 1 P0 authority enforcement is genuinely complete and well-tested.
- `GO_CAMPAIGN_1_COMPLETE`: **valid**. Phase 2 shared contracts and Phase 3 context reduction/canonical ownership are implemented, tested, documented, committed, and reconciled at the Campaign closeout checkpoint.
- Closeout integrity is fail-closed: the live Campaign autoloop reads only the strict JSON terminal state, requires every mandatory phase/gate and AR acceptance plus `commit_safe`, and cannot be reopened by superseded Markdown history.
- The Phase 1 GO label remains a narrower historical authority claim; the terminal Campaign 1 verdict is the only full-campaign claim.
- Terminal gate: `campaign1_complete`. Campaign 2 is not started by this closeout.
- Do not push or mutate protected product worktrees from this Campaign checkout.

The next recorded gate is `campaign1_complete`.
