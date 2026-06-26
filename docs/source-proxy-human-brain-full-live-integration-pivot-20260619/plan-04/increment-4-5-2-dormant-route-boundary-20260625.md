# Increment 4.5.2 Dormant Route Boundary - 2026-06-25

Status: `GO`

## Plan Expectation

Increment 4.5.2 required Phase 4.5 consolidation to become true at the route boundary, not only in documentation or UI. Dormant parallel routes needed explicit non-canonical status without deleting them or treating their output as live apply proof.

## Implemented Change

Dormant/advisory `/v1/coding` routes now return `x-spiritos-plan4-route-status: dormant` and `x-spiritos-plan4-canonical-replacement` headers:

- `/v1/coding/codex`;
- `/v1/coding/bounded-diff-preview`;
- `/v1/coding/research-preview`;
- `/v1/coding/helper-agents/preview`.

The advisory local routes also include `plan4_route_status: dormant` in their JSON bodies. The legacy proxy routes preserve dormant headers even when forwarding Source Proxy responses or returning feature-flag/config-blocked packets.

No route was deleted, no authority was expanded, and no package/env/generated XML path was touched.

## Focused Check

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && npm test -- --run src/app/v1/coding/codex/__tests__/route.test.ts src/app/v1/coding/bounded-diff-preview/__tests__/route.test.ts src/app/v1/coding/research-preview/__tests__/route.test.ts src/app/v1/coding/helper-agents/preview/__tests__/route.test.ts"
PASS: 11 tests
```

## Live Route Proof

Live route proof passed:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-04/increment-4-5-2-live-route-proof-20260625.json`

Proof summary:

- `POST /v1/coding/research-preview` returned dormant route headers and `plan4_route_status: dormant`.
- `POST /v1/coding/helper-agents/preview` returned dormant route headers and `plan4_route_status: dormant`.
- `POST /v1/coding/codex` returned dormant route headers.
- `POST /v1/coding/bounded-diff-preview` returned dormant route headers.
- Every route returned an `x-spiritos-plan4-canonical-replacement` header pointing back to the canonical route sequence.
- No apply-success phrase appeared in the live route responses.

## Verdict

Increment 4.5.2 is `GO`.
