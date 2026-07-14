# SpiritOS Campaign 1 Plan

## Identity, status, and firewall

- Campaign: `spiritos-campaign-1`, structural authority foundation.
- Mutable root: `/home/source/SpiritOS-campaign-1-20260712` on `codex/spiritos-campaign-1-foundation-20260712`; base `49e58f2982521c46a1a4fc73ef66461a86643792`.
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2a`.
- Never mutate protected product worktrees, product branches, services, or SpiritFlix's borrowed `_worktrees/`. Do not push or begin Campaign 2.

`accepted baseline` has reproducible evidence; `completed` has committed implementation and focused proof; `partial` is bounded but not accepted; `current` is active; `not started` has no accepted implementation; `blocked` needs an external prerequisite; and `invalidated` contradicts current code or evidence.

## Accepted Phase 0 baseline

The authenticated SpiritFlix no-reversion/browser baseline, provenance, source-head binding, and borrowed-worktree containment are accepted baseline constraints. They permit no product edits and must be rechecked at final closeout.

## Phase 1 authority enforcement

1. **AR-001 SpiritFlix authority - completed.** The ordinary BFF session remains non-administrative; every bounded admin writer has the authenticated server-owned preview/issuance/consume/finalize boundary and committed-HEAD lifecycle proof.
2. **AR-002 Cartographer separation - completed.** Duplicate/shadow routes are removed, legacy mutation helpers fail closed before work, and the durable proposal selection consumer is bounded and regression-tested.
3. **AR-003 Design writeback - completed.** Durable preview, authenticated issuance, canonical writeback consumption/finalization, matched acknowledgement, and redacted receipt enforcement are verified.
4. **Approval Authority - bootstrap and lifecycle completed.** Durable SQLite authority binds repository, worktree, root, target, canonical plugin, content/context, source HEAD, consumer, generation, TTL, transactional consume/finalize, cancellation, acknowledgement, and redacted evidence.
5. **Authenticated operator issuance - completed.** The server-owned `spiritos-local-operator` with role `approval-issuer` may issue only persisted previews. Session, expiry, revocation, trusted Origin/Host, CSRF, role, audit, and server-resolved canonical bindings gate issuance. Browser `approved:true` and browser-supplied authority bindings are invalid.

## Canonical contracts and remaining gates

- The canonical contract is persisted preview/proposal -> authenticated operator action -> durable approval ID/generation -> canonical coding or Design consumer -> transactional consumption/finalization -> reviewer, verifier, and evidence acknowledgements -> redacted receipt.
- Dependencies may carry data but never confer authority. Authority is server-owned; caller repository, worktree, root, target, target-plugin, hashes, prompt/context, source HEAD, consumer, TTL, issuer, and approval state must be resolved from persisted state.
- Evidence must be externalized and redacted. Test profiles must label unit, source-text, route, production-path, browser, and runtime proof truthfully.
- The canonical coding shell must use the durable Authority, Prompt 1 target-plugin binding, server-assigned executor, duplicate removal, rejection paths, and real route -> Authority -> Source Proxy task proof.
- Required operator issuance proof: session creation, HTTP-only cookie, expiry, revocation, trusted Origin/Host, CSRF, missing/invalid session rejection, stale preview rejection, client-binding override rejection, role enforcement, explicit approve/reject, successful coding and Design issuance, second-use rejection, and redacted evidence.
- Final closeout must reconcile the current AR-001/002/003 receipts, dependency enforcement, canonical shell and Prompt 1 proof, duplicate removal, truthful profiles, secret scan, full regression, protected-head check, and authenticated SpiritFlix regression at one candidate checkpoint.

## GO, failures, and turn ends

`GO_CAMPAIGN_1_COMPLETE` is recorded at the final atomic closeout checkpoint: every mandatory gate above is committed, verified by its required evidence, secret-free, and compatible with immutable protected heads. The closeout ledger and receipt distinguish source, route, browser, and runtime proof without exposing a credential, cookie, approval ID, task ID, media path, or raw model response.
