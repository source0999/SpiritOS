# FIP-0.1S Mini Context Pack

Use this with:

- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-runtime-auth-hot-path-unblocker.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-9445f3d31d301d82.json`

## Scope

PLAN: FIP-0
PHASE: Authenticated hot-path proof
INCREMENT: FIP-0.1S
VERDICT: GO

## Source Proxy Truth

Exact launch command:

```powershell
npm run proxy:https:lan
```

Expected/reachable URL:

```text
https://127.0.0.1:8787
```

Listener observed:

```text
0.0.0.0:8787
```

`/v1/self/status` returned `200 OK`. `/healthcheck` returned `503` only because GPU metrics are unavailable.

## Next Proxy Truth

Next route config lives in:

- `src/lib/source-proxy-origin.ts`
- `src/app/v1/decisions/prompt-packet/route.ts`
- `src/app/v1/decisions/fip0-receipts/latest/route.ts`
- `src/app/v1/decisions/fip0-receipts/[runId]/route.ts`

Local env:

- `SPIRIT_CODING_USE_PROXY=true`
- No local `SOURCE_PROXY_ORIGIN`, `SOURCE_PROXY_HOST`, or `SOURCE_PROXY_PORT` override found.

Fallback bases:

- `http://127.0.0.1:8787`
- `https://127.0.0.1:8787`

## Runtime Receipt Proof

Source Proxy prompt-packet wrote:

- Run ID: `fip0-9445f3d31d301d82`
- Receipt: `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-9445f3d31d301d82.json`
- Final verdict: `GO: fip0_receipt_foundation_complete_runtime_lanes_not_yet_wired`

Latest retrieval returned the same run after fixing timestamp-based ordering.

## App-Origin Auth Boundary

CLI probes to app-origin routes still return `401 {"error":"unauthorized"}`:

- `http://127.0.0.1:3000/coding`
- `http://127.0.0.1:3000/v1/decisions/prompt-packet`
- `http://127.0.0.1:3000/v1/decisions/fip0-receipts/latest`

This is expected for unauthenticated CLI. Britton's authenticated browser proof is the authority for the app-origin route.

## Manual Auth Follow-Up

Britton reported the authenticated `/coding` path passed for manual task:

`task_30470ca94889`

The run reached:

- `/v1/decisions/prompt-packet`
- `/v1/verification/diff-preview`
- `/v1/actions/execute-approved`

But the prompt was intended to be receipt-only and was treated as a coding task. It applied a whitespace-only diff to:

`source_proxy/api/action_preview.py`

Revert status:

- `source_proxy/api/action_preview.py` has no remaining git diff.
- Current SHA256 matches the approved-action audit `sha256_before`: `f0c94b25750fdd95e68bcfd20edb1ab383990b966e9832ea733c644536717e38`.
- Audit manifest: `.spirit-backups/2026-06-13/approved-diff-2026-06-13T225247_486310_0000/manifest.json`

Authenticated browser receipt proof status:

- PASSED by Britton manual authenticated browser proof on 2026-06-13.
- Browser hit: `10.0.0.186:3000/v1/decisions/fip0-receipts/latest`.
- Returned real app-origin receipt.
- Run ID: `fip0-9445f3d31d301d82`.
- `final_packet_hash`: present.
- `coder_received_packet_hash`: present but empty by FIP-0 design because Qwen coder is skipped.
- Every lane status was valid: `used`, `skipped`, `blocked`, or `failed`.
- Final verdict: `GO: fip0_receipt_foundation_complete_runtime_lanes_not_yet_wired`.
- Previous `HUMAN_AUTH_PROOF_REQUIRED` blocker is resolved.

## Checks

- PASS: `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q`
- PASS: `npm run typecheck -- --pretty false`
- PASS with line-ending warnings: `git diff --check`
- PASS: Source Proxy direct prompt-packet receipt write
- PASS: Source Proxy direct latest receipt retrieval
- EXPECTED_UNAUTHENTICATED_401: app-origin `/coding` and receipt route from CLI
- PASS: accidental `source_proxy/api/action_preview.py` mutation reverted
- PASS: authenticated browser `/latest` receipt retrieval confirmed by Britton manual proof

## FIP-0.2 Runtime Discipline

- Launch command: `npm run proxy:https:lan`.
- Reachable Source Proxy URL: `https://127.0.0.1:8787`.
- Restart must happen on the Linux `source-server` runtime checkout, not only from the Windows share path.
- Direct Source Proxy receipt write/retrieve checks should target `https://127.0.0.1:8787`.
- App-origin latest receipt proof still requires Britton's authenticated browser session if CLI is blocked by 401.

## Stop Gate

NEXT ACTION:
FIP-0.2 only. Do not start FIP-1.
