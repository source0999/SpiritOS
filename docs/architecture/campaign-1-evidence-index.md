# Campaign 1 Evidence Index

Schema: `spiritos-campaign-1-evidence-index/v1`

## Verdict ceiling

- Candidate head: `2a273e2a2ece744f8c56e5cfa42a49b60ae71cc8`
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`.
- Verdict: `NO_GO_CAMPAIGN_1_PHASE3_IN_PROGRESS`.
- Reason: the Phase 1 closeout evidence remains valid only at its documented claim ceiling. Phase 2 is complete and accepted; Phase 3 has accepted shell, externalization, context, adapter, and test-profile increments but still requires duplicate-path reconciliation, full runtime/browser proof, build, and final closeout evidence.

## Accepted baseline receipts

| Receipt | Scope | Redaction / provenance | Claim ceiling |
| --- | --- | --- | --- |
| `campaign-1-baseline/authenticated-browser-proof.json` | authenticated isolated desktop, Fold, player, and `/coding` rendering | schema v3; protected heads, build identity, certificate policy, opaque E2E session; secret redaction pass | no-reversion browser regression only |
| `campaign-1-evidence/phase1-cross-product-browser-20260714.md` | isolated production browser regression | dedicated least-privilege E2E identity, SPKI-only policy, immutable protected heads | completed browser slice, not AR-001 acceptance |
| `campaign-1-evidence/operator-issuance-runtime-20260714.md` | coding and Design HTTP authority chains | redacted response hashes and server-owned lifecycle | runtime slice, not final evidence acceptance |
| `campaign-1-evidence/prompt1-authority-lifecycle-20260714.md` | Prompt 1 selected target-plugin lifecycle | shared approval ID/generation acknowledgement and legacy rejection | Prompt 1 only |
| `campaign-1-evidence/canonical-operator-shell-20260714.md` | canonical shell and Coder 10 lifecycle | no credential/session/approval identifiers committed | canonical shell slice |
| `campaign-1-evidence/ar001-admin-operator-lifecycle-20260714.md` | authenticated admin writer issuance and exact consume/finalize | isolated test-only operator state; no cookie, credential, approval ID, or media path recorded | AR-001 administrative authority slice |

## Current reconciliation evidence

| Item | Result | Proof |
| --- | --- | --- |
| Cartographer direct execution registration | pass | `source_proxy/api/cartographer.py` has no `/safe-write` or `/verification/run` registration; AST validator rejects duplicate method/path pairs. |
| Cartographer legacy mutation entry points | pass, fail closed | docs/git/clutter/starter-blueprint compatibility routes return `410 forbidden_cartographer_mutation`; router imports no executor symbols. |
| Complete Cartographer API regression | pass | `263 passed`; legacy mutable expectations now assert fail-closed routes/helpers and singular canonical selection registration. |
| AR-002 durable selection/consumer | pass, focused production path | [redacted receipt](campaign-1-evidence/cartographer-durable-selection-20260714.md): persisted selection -> authenticated operator issuance -> canonical proposal-only transfer consumer -> consume/finalize with one ID/generation acknowledgement envelope. |
| AR-003 final acknowledgement envelope | pass, focused production path | [redacted receipt](campaign-1-evidence/design-writeback-acknowledgement-20260714.md): persisted Design preview -> authenticated operator issuance -> canonical writeback consume/finalize -> server-built matched acknowledgement envelope. |
| Current BFF/session boundary | pass, focused | 33 tests across the opaque session, BFF route, browser client, and admin client confirm browser-supplied authorization is rejected and server-only authorization is never reflected. |
| Current browser lifecycle harness | pass | [runtime recovery receipt](campaign-1-evidence/phase1-runtime-lane-recovery-20260714.md) records the registered isolated loopback candidate, real model run, browser proof, transactional approval lifecycle, undo/reset, and clean rerun. |
| Final isolated production lifecycle | pass, authoritative `GO` | [final closeout receipt](campaign-1-evidence/phase1-final-closeout-20260714.md): real operator shell session, persisted task/preview, server-issued approval, canonical apply, matched acknowledgements, managed Chromium six-card proof, undo/reset, and clean rerun. |
| Design preview contract tests | pass | 32 tests across preview, authenticated Design approval, and writer guard suites. |
| Design negative receipt fixtures | pass | 9 malformed receipt cases rejected. |
| AR-001 ordinary browser session boundary | pass | [redacted server-owned-session receipt](campaign-1-evidence/ar001-server-owned-session-20260714.md); client credential and target overrides are rejected. |
| AR-001 administrative writer authority | pass, committed-HEAD lifecycle | [redacted admin receipt](campaign-1-evidence/ar001-admin-operator-lifecycle-20260714.md): authenticated session, trusted Origin/Host and CSRF, persisted server-derived preview, server issuance, exact writer consume/finalize, replay rejection, and revocation rejection. |

Every entry is redacted by reference: no secret, cookie, approval ID, task ID, media path, or raw payload is repeated here. New evidence must include schema, campaign/run identity, source and protected heads, test profile, result, secret-redaction result, and a claim ceiling.
