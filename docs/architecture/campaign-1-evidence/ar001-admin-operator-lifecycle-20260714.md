# AR-001 administrative operator lifecycle receipt

- Schema: `spiritos-campaign-1-evidence/v1`
- Campaign/run: `spiritos-campaign-1` / `phase1-ar001-admin-operator-20260714`
- Mutable source head: `8f9cfd818479a3494e7123697ef36263cf6d184a`
- Protected heads: Source Proxy `594d66ef`; SpiritFlix `5fde4ae0`; architecture audit `05612d2a`
- Profile: committed-HEAD production route/session lifecycle plus bounded writer regressions; not a live media-service claim.

## Result

PASS. The authenticated `spiritos-local-operator` session created a server-owned preview for a bounded manual-model writer after trusted Origin/Host and CSRF validation. The route issued only the persisted preview/generation; the canonical writer consumed and finalized that exact binding. A second consume was rejected, and revocation prevented a subsequent preview.

The same strict server-side binding map covers smart rescan, admin action, smart analysis, smart batch, manual model, manual tags, and face learning. A browser cannot attach an action, target, plan, consumer, approval ID, generation, or writer override to an approve request; unregistered writers and unexpected request keys are rejected.

## Verification

- Committed-HEAD lifecycle/route/admin writer profile: 8 Vitest files, 19 tests passed.
- Authority/session Python profile: 3 tests passed.
- `npm run typecheck`: passed before the atomic gate commit; the route and lifecycle tests were rerun at the committed head.
- `npm run campaign-1:validate-authority`: passed.
- `npm run campaign-1:validate-continuity`: passed.

No credential, session cookie, CSRF value, approval ID, preview ID, raw media path, sidecar value, or secret appears in this receipt.

## Claim ceiling

AR-001 administrative-authority acceptance is complete pending the Campaign-wide final matrix, protected-head recheck, and final closeout decision.
