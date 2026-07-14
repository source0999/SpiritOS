# Campaign 1 Evidence Index

Schema: `spiritos-campaign-1-evidence-index/v1`

## Verdict ceiling

- Candidate head: `e8e26978bb2bb94fdc3c041672ab9633e6de177e`
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`.
- Verdict ceiling: `NO_GO_VERIFICATION_FAILURE`.
- Reason: the ordinary SpiritFlix browser client still has a compatibility path that supplies a Jellyfin authorization header to the BFF, and the Design/Cartographer final acknowledgement and selection evidence is incomplete. The isolated E2E broker does not erase either gap.

## Accepted baseline receipts

| Receipt | Scope | Redaction / provenance | Claim ceiling |
| --- | --- | --- | --- |
| `campaign-1-baseline/authenticated-browser-proof.json` | authenticated isolated desktop, Fold, player, and `/coding` rendering | schema v3; protected heads, build identity, certificate policy, opaque E2E session; secret redaction pass | no-reversion browser regression only |
| `campaign-1-evidence/phase1-cross-product-browser-20260714.md` | isolated production browser regression | dedicated least-privilege E2E identity, SPKI-only policy, immutable protected heads | completed browser slice, not AR-001 acceptance |
| `campaign-1-evidence/operator-issuance-runtime-20260714.md` | coding and Design HTTP authority chains | redacted response hashes and server-owned lifecycle | runtime slice, not final evidence acceptance |
| `campaign-1-evidence/prompt1-authority-lifecycle-20260714.md` | Prompt 1 selected target-plugin lifecycle | shared approval ID/generation acknowledgement and legacy rejection | Prompt 1 only |
| `campaign-1-evidence/canonical-operator-shell-20260714.md` | canonical shell and Coder 10 lifecycle | no credential/session/approval identifiers committed | canonical shell slice |

## Current reconciliation evidence

| Item | Result | Proof |
| --- | --- | --- |
| Cartographer direct execution registration | pass | `source_proxy/api/cartographer.py` has no `/safe-write` or `/verification/run` registration; AST validator rejects duplicate method/path pairs. |
| Cartographer legacy mutation entry points | pass, fail closed | docs/git/clutter/starter-blueprint compatibility routes return `410 forbidden_cartographer_mutation`; router imports no executor symbols. |
| Complete Cartographer API regression | fail, expected migration backlog | legacy mutable-route fixtures still expect now-forbidden `200` writes. No legacy bypass was restored; the AR-002 focused lifecycle profile is authoritative for this slice. |
| AR-002 durable selection/consumer | pass, focused production path | [redacted receipt](campaign-1-evidence/cartographer-durable-selection-20260714.md): persisted selection -> authenticated operator issuance -> canonical proposal-only transfer consumer -> consume/finalize with one ID/generation acknowledgement envelope. |
| Design preview contract tests | pass | 32 tests across preview, authenticated Design approval, and writer guard suites. |
| Design negative receipt fixtures | pass | 9 malformed receipt cases rejected. |
| AR-001 ordinary browser session boundary | pass for session slice | [redacted server-owned-session receipt](campaign-1-evidence/ar001-server-owned-session-20260714.md); client credential and target overrides are rejected. Administrative mutation authority remains unaccepted. |

Every entry is redacted by reference: no secret, cookie, approval ID, task ID, media path, or raw payload is repeated here. New evidence must include schema, campaign/run identity, source and protected heads, test profile, result, secret-redaction result, and a claim ceiling.
