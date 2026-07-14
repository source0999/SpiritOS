# Campaign 1 authenticated operator issuance runtime receipt

- Recorded: `2026-07-14T00:54:21Z` to `2026-07-14T01:00:00Z` on the isolated Campaign 1 HTTP lane (`127.0.0.1:8788` Source Proxy and `127.0.0.1:3010` Next).
- Isolation: temporary task, operator-session, gate, and Design-vault runtime state; protected product services and branches were not used. The temporary README patch was explicitly restored after execution proof.

## Coding chain

1. The live operator-session route rejected an invalid credential and established an HTTP-only local operator session with trusted Origin/Host and CSRF checks.
2. The live Source Proxy route persisted a coding preview. The live operator approval route issued a durable generation `1` approval from that persisted preview.
3. The live `/v1/actions/execute-approved` route applied the scoped temporary README patch, then post-apply verification completed the task. The same approval ID/generation was acknowledged by `coding-executor`, `coding-reviewer`, `coding-verifier`, and `evidence-recorder`.
4. Redacted response SHA-256: execution `44464f9442f89d7801f8675babfe3186495a01aa2b6b7d2d6b9c48794ccd8d22`; verification `2132fc83d1118acef5f027402c3c6f29f64103bcb077a6a0502cf5f9e148b20b`.

## Design chain

1. The live Design Studio preview route persisted the Design writeback preview.
2. The live authenticated operator Design route resolved that preview server-side and issued its durable generation `1` Design approval.
3. The canonical approved-writeback route consumed and finalized it, producing the bounded Design-memory receipt in the isolated runtime lane.
4. Redacted response SHA-256: `9fc3b77526a45559a22f0826dc59ac7790d274cfc0c9d7c5743591c06bd486f8`.

No cookies, credentials, approval identifiers, request headers, raw task payloads, or runtime paths are committed in this receipt.

## Verification boundary

Focused backend and frontend route tests plus TypeScript checking passed for this slice. `npm run build` was attempted twice: the first attempt ended in a native segmentation fault during optimized Webpack compilation; the isolated retry timed out after 124 seconds without completion. This receipt does not treat the build as passing.
