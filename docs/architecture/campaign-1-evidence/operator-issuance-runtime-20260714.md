# Campaign 1 authenticated operator issuance runtime receipt

- Recorded: `2026-07-14T00:54:21Z` to `2026-07-14T01:00:00Z` on the isolated Campaign 1 HTTP lane (`127.0.0.1:8788` Source Proxy and `127.0.0.1:3010` Next).
- Isolation: temporary task, operator-session, and gate runtime state; the canonical Design writeback produced a runtime Design-vault note without touching protected product services or branches. The temporary README patch was explicitly restored after execution proof.

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

## Build reliability follow-up

- The original failure was reproduced only as an environmental/generated-state condition: the Campaign-owned Next dev server was active and `.next` contained 878 MB of mixed dev/build output. No Campaign authority module was evaluated as a build-time dependency and no external service wait occurred.
- After stopping only that Campaign-owned dev process and clearing only generated `.next` output, clean pre-repair builds completed in 145 s and 153 s. After the final profile/authority-boundary repair, two additional clean authoritative `npm run build` runs completed in 136 s (2,360,220 KB peak RSS) and 138 s (2,277,780 KB peak RSS). All four completed with exit `0`; the final pair recorded zero swaps, generated all 133 static pages, and left no build process.
- The 124-second retry was therefore an insufficient observation window, not evidence of a hung build. This receipt records build verification as complete; it does not claim Campaign 1 GO.
