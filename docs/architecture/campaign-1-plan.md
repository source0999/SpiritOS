# SpiritOS Campaign 1 Plan

## Identity, status, and firewall

- Campaign: `spiritos-campaign-1`, structural authority foundation across Phases 0-3.
- Mutable root: `/home/source/SpiritOS-campaign-1-20260712` on `codex/spiritos-campaign-1-foundation-20260712`; base `49e58f2982521c46a1a4fc73ef66461a86643792`.
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`.
- Never mutate protected product worktrees, product branches, services, or SpiritFlix's borrowed `_worktrees/`. Do not push or begin Campaign 2.

Status vocabulary: `completed` means committed and verified; `not_started` means no accepted implementation exists; `partial` means bounded work exists but is not accepted; `blocked` means an external prerequisite is required; `invalidated` means current evidence contradicts the recorded claim.

## Campaign phase map

Campaign 1 was originally scoped as Phases 0-3. The Phase 1 closeout at `4e1f849f` is a verified P0 authority GO, not a full Campaign 1 GO. Full Campaign 1 remains open until Phases 2 and 3 are implemented and verified.

| Phase | Name | Status | Evidence / next gate |
| --- | --- | --- | --- |
| Phase 0 | Neutral truth and characterization | COMPLETED | Baseline characterization, no-reversion constraints, provenance anchors, borrowed-worktree containment, and protected-head policy established. |
| Phase 1 | P0 authority and deployment enforcement | COMPLETED | Commit range `8d17286d..4e1f849f`; AR-001/002/003 closed with fail-closed proofs and durable authority evidence. |
| Phase 2 | Shared contracts and enforced boundaries | NOT_STARTED | Next gate: `phase2_shared_contracts_creation`. |
| Phase 3 | Context reduction and canonical ownership | NOT_STARTED | Must follow Phase 2 or a recorded dependency decision. |

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

Status: **NOT_STARTED**.

Purpose: convert duplicated Python/TypeScript boundary knowledge into shared, enforceable contracts that services and tests consume from one source of truth.

Required deliverables:

- Create `packages/contracts/`.
- Add OpenAPI and JSON Schema contracts for `source-proxy`, `spiritflix`, `scout`, `cartographer`, `mac-worker`, `design`, `verification`, `deployment`, and shared primitives.
- Replace manual Python/TypeScript duplication for task, verdict, provider, receipt, approval, identity, and deployment boundary schemas with generated or contract-backed definitions.
- Choose exactly one minimum boundary enforcement tool for the first accepted implementation slice, then document why it is the minimum viable enforcement surface.
- Add violation tests that fail when a route, worker, shell, or helper bypasses the shared contract or drifts from it.
- Keep Phase 1 authority invariants intact while moving schemas and client/server bindings behind contracts.

Phase 2 acceptance requires committed contracts, generated or contract-backed consumers on both sides of each selected boundary, focused violation tests, and continuity validation. No Phase 2 implementation is present at `4e1f849f`.

## Phase 3 - Context reduction and canonical ownership

Status: **NOT_STARTED**.

Purpose: reduce repository/context load, declare canonical ownership surfaces, and quarantine non-production experiments so future agents and humans can reason from the same small set of authoritative paths.

Required deliverables:

- Externalize evidence to `SPIRITOS_EVIDENCE_ROOT`, retaining only manifests, hashes, and redacted receipts in Git. Target approximately 72% fewer tracked paths; current audit observed 12,976 tracked paths with 7,489 still evidence.
- Exclude docs/evidence from TypeScript and Vitest discovery where they are not intended source inputs.
- Declare one canonical coding shell and quarantine alternate coding shells under `labs/`.
- Create a `labs/` directory for non-canonical shells, experiments, and deprecated proof harnesses.
- Extract Prompt 1 behind the target-plugin adapter instead of leaving prompt-specific logic in duplicate shell or route surfaces.
- Remove duplicate routes/helpers that survived Phase 1 because they were not part of the P0 authority enforcement slice.
- Create a test-profiles registry that truthfully labels unit, source-text, route, production-path, browser, and runtime proof.

Phase 3 acceptance requires measurable tracked-path/context reduction, canonical ownership declarations, quarantined alternates, duplicate-removal proof, test-profile enforcement, continuity validation, and evidence-root checks. No Phase 3 implementation is present at `4e1f849f`.

## GO, failures, and turn ends

- `GO_PHASE_1_AUTHORITY_COMPLETE`: verified at `4e1f849f`. Phase 1 P0 authority enforcement is genuinely complete and well-tested.
- `GO_CAMPAIGN_1_COMPLETE`: **not currently valid** for the full campaign. Full Campaign 1 GO requires Phase 2 shared contracts and Phase 3 context reduction/canonical ownership to be implemented, tested, documented, and committed.
- Any future closeout must distinguish Phase-level GO from full-campaign GO and must not reuse the Phase 1 GO label as full Campaign 1 completion.
- Campaign 2 must not begin from the Phase 1 checkpoint alone.

The next recorded gate is `phase2_shared_contracts_creation`.
