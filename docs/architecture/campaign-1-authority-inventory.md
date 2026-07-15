# Campaign 1 Authority Inventory and Implementation Map

Schema: `spiritos-campaign-1-authority-inventory/v1`
Scope: Campaign worktree only; product worktrees are read-only references.
Evidence basis: production route registration/imports, bounded call-site search, and named tests.

## Reconciliation checkpoint — 2026-07-14

The tables retain the original discovery context while the top-level classification records current acceptance evidence. The current Campaign implementation checkpoint is `2a273e2a2ece744f8c56e5cfa42a49b60ae71cc8`; protected heads remain pinned in the Campaign state and Campaign GO is not yet claimed.

| AR | Current classification | Action and proof | Acceptance |
| --- | --- | --- | --- |
| AR-001 SpiritFlix | ordinary session plus distinct administrative authority | The ordinary client has only an opaque HTTP-only BFF session. A strict authenticated operator route derives persisted bindings for all seven bounded writers, then the canonical writer consumes/finalizes `spiritflix-admin-executor` approval. | **completed** |
| AR-002 Cartographer | proposal/read-only owner with durable selection transfer | Retired direct routes and helpers fail closed before work; the server-owned proposal selection binds the receiving consumer and records matched consumer/reviewer/verifier/evidence acknowledgement. | **completed** |
| AR-003 Design writeback | canonical durable writeback with acknowledgement envelope | The authenticated operator route resolves a persisted preview; canonical writeback consumes/finalizes and records matched design-writeback/reviewer/verifier/evidence acknowledgement. | **completed** |

Historical rows below are retained for discovery provenance. The final profiles, receipts, secret scan, and protected-head checks are reconciled in the Campaign 1 closeout checkpoint.

## AR-001  SpiritFlix

### Administrative mutation inventory — 2026-07-14

The following production routes were traced after the ordinary session migration. `none` means the route has no authenticated operator, durable approval, CSRF/origin enforcement, or result evidence boundary today; it does not mean the route is safe. Browser-controlled roots, paths, actions, and metadata must be replaced by server-resolved preview bindings before execution.

| Route | Runtime / effect | Current authority and browser control | Verdict |
| --- | --- | --- | --- |
| `admin/actions` POST | `handleSpiritFlixAdminAction`; create, move, delete, restore, rename and Jellyfin action dispatch | `admin.action` preview/action/mode binding is derived by the authenticated operator route; writer consumes/finalizes exact binding | canonical bounded writer |
| `admin/smart/analysis` POST | analysis/review sidecar writes and approved metadata export | `smart.analysis` path/action binding is persisted before issuance; writer consumes/finalizes it | canonical bounded writer |
| `admin/smart/batch` POST | batch review/run and smart-analysis sidecar writes | `smart.batch` target/action binding is persisted before issuance; writer consumes/finalizes it | canonical bounded writer |
| `library-smart-rescan` POST | starts rescan child process | fixed `index.rebuild` binding, authenticated issuance, transactional consume/finalize | canonical bounded writer |
| `videos/[itemId]/model` PUT | manual-model sidecar/index write | `metadata.mutation` item/model binding is server-derived and writer consumes/finalizes it | canonical bounded writer |
| `videos/[itemId]/tags` PUT | manual-tag sidecar/index write | `metadata.mutation` item/tag-count binding is server-derived and writer consumes/finalizes it | canonical bounded writer |
| `videos/[itemId]/face-learning` POST | performer/face sidecar and related-item updates | `face.learning` item/model binding is server-derived and writer consumes/finalizes it | canonical bounded writer |
| `admin/library` POST | Jellyfin metadata listing | ordinary BFF session + CSRF/origin; server resolves credential/user/server | canonical read-only |
| `face-metadata` POST | metadata lookup only | unauthenticated but non-mutating; caller item paths influence lookup | constrain as read-only later |
| `jellyfin`, image, stream, HLS | ordinary media BFF | server-owned credential/session; write methods require CSRF/origin | canonical media transport, not admin authority |

Containment and migration update: ordinary media sessions cannot issue administrative approvals. The seven mutation writers reject missing or forged approvals; their preview action/target/plan bindings are server-derived by the authenticated operator route, and consumption/finalization is transactional through `spiritflix-admin-executor`.

Durable contract update: `source_proxy.approval.spiritflix_admin_authority` persists the exact action/target/configured-root/plan hash in the existing Approval Authority, issues only `spiritflix-admin-executor` approvals for `spiritflix_admin_mutation`, transactionally consumes exact bindings, and finalizes a redacted result. HTTP operator issuance and all seven writer-port migrations are complete.

Lower-level writers include `handleSpiritFlixAdminAction`, `moveSpiritFlixAdminPath`, `writeSmartAnalysis`, `writeApprovedSmartMetadataSidecar`, `setSpiritFlixManualModelForItem`, `setSpiritFlixManualTagsForItem`, and `requestSpiritFlixFaceLearning`. They are directly importable today and therefore require authority context at their canonical execution boundary; route-only checks are insufficient. Rescan, thumbnail, probe, sampler, and smart-processing workers can spawn processes and must retain bound preview/approval/result identities when promoted to execution.

| Path | Runtime owner / operation | Authority finding | Implementation map |
| --- | --- | --- | --- |
| `src/app/api/spiritflix/admin/actions/route.ts` | Next route -> `handleSpiritFlixAdminAction`; filesystem/Jellyfin/process-capable action dispatch | Caller JSON is the only current authority; no identity, origin, CSRF, operation capability, or durable receipt boundary | Canonical owner: new server-only SpiritFlix authority service. Migrate this route first; forbid direct action-handler callers. |
| `admin/library/route.ts`, `admin/smart/{analysis,batch}/route.ts` | Admin discovery and smart-batch preview/run/review | POST shape is not sufficient; smart batch `run` can mutate | Classify preview/listing read-only; put run/review and any write action behind the same authority. |
| `library-smart-rescan/route.ts` | starts a child rescan process | POST directly starts process | Authority operation `index.rebuild`; require server-owned capability and receipt. |
| `face-metadata/route.ts`, `videos/[itemId]/{model,tags,face-learning}/route.ts` | metadata/index writes | no shared caller/operation boundary | Authority operations `metadata.write` and `face.learn`; migrate after action/rescan routes. |
| `jellyfin/route.ts`, `jellyfin-image/route.ts` | BFF reads/proxy | E2E broker already keeps raw credential server-side | Preserve as read/session transport; it is not the mutation authority. |

Required negative tests: anonymous, forged caller/capability, wrong method/origin/CSRF, and denied operation make no state/process change. Required evidence: redacted durable allow/deny receipt.

## AR-002  Cartographer

| Path | Runtime owner / operation | Authority finding | Implementation map |
| --- | --- | --- | --- |
| `source_proxy/api/cartographer.py` | mounted by `source_proxy/main.py`; discovery plus safe-write/verification endpoints | Real duplicate registrations exist for `GET/POST /safe-write` and `GET/POST /verification/run` (first at 493-560, shadow copy at 1313-1379). POST receives caller-supplied approval/context fields. | Canonical observation owner remains Cartographer. Delete shadow registrations; move mutation transfer to a distinct executor contract with server-owned approval lookup. |
| `source_proxy/cartographer/safe_write.py` | bounded docs safe write | has path/receipt guards but explicitly reports authority false; does not make caller-supplied token authority safe | Retain only as executor port after server-owned approval binding. |
| `source_proxy/cartographer/verification_runner.py` | allowed command execution | invoked from Cartographer route | Treat as executor-only; Cartographer observations/proposals must not reach it directly. |

Required negative tests: router has one registration per method/path; observations do not call executor; forged/stale/mismatched approval cannot write or run a command.

## AR-003  Design approved writeback

| Path | Runtime owner / operation | Authority finding | Implementation map |
| --- | --- | --- | --- |
| `src/app/v1/coding/design-studio/approved-writeback/route.ts` | production POST route | forwards entirely caller-owned input | Replace caller-owned root/gate/approval assertions with server-owned approval lookup and bound request contract. |
| `src/lib/coding/design-studio-approved-writeback-runtime.ts` | runtime coordinator | checks values but accepts caller `vault_root`, gate and approval identity | Canonical authority coordinator; accept only a validated server-side approval record. |
| `src/lib/coding/design-studio-obsidian-writeback.ts` | actual file writer | validates destination but accepts arbitrary vault root from runtime | executor-only; canonical root/path/hash/plugin/approval binding must precede it. |

No other tracked production caller of `runDesignStudioApprovedWriteback` or `writeApprovedDesignMemoryNote` was found. Required tests cover root/path/plugin/hash/caller mismatch, stale/reused approval, symlink escape, and a bounded approved write with byte receipt.

## Coding shell, Prompt 1, and evidence

- Canonical-shell candidate: `src/app/coding/page.tsx -> CodingCockpitShell`, which is the production UI shell and calls the Source Proxy bridge. `CodingAgentInterface` and `CodingCommandCenterShell` are consumers/candidates, not independently proven canonical executors.
- Prompt 1 production chain spans `CodingCockpitShell` and `source_proxy/tasks/long_running.py`; current LumaCart rules are embedded in the long-running subsystem. Required extraction is a typed target-plugin resolver and packet acknowledgement at coder, reviewer, verifier, and receipt boundaries.
- Current evidence is distributed across route responses, console/runtime artifacts, and helper receipts. Canonical external evidence writer and validator are missing.

## Execution order

1. Remove the proven Cartographer route shadow and add registration regression coverage.
2. Introduce shared versioned authority/provenance/approval/evidence contracts.
3. Migrate AR-001 mutations to canonical server-only authority.
4. Split Cartographer observation from the mutation transfer/executor port.
5. Harden AR-003 with a server-owned approval/root/hash/plugin binding.
6. Establish the coding shell and Prompt 1 plugin resolver; migrate real caller chain.
7. Add evidence validator, duplicate/dependency checks, named profiles, and full closeout.

This inventory is descriptive only; it does not treat existing comments, tests, or preview status as authority.
