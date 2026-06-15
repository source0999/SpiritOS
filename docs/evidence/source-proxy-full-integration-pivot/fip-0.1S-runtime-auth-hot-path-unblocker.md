# FIP-0.1S Runtime/Auth Hot-Path Unblocker

Date: 2026-06-13

## Increment Scope

PLAN: FIP-0 - Supersede + Universal Integration Truth Receipt Foundation
PHASE: Authenticated hot-path proof
INCREMENT: FIP-0.1S

Purpose:
Unblock or precisely diagnose the real authenticated `/coding` hot-path proof without starting FIP-1 or wiring future lanes.

## Hard Stops Preserved

- Did not start FIP-1.
- Did not wire context/search/model/coder/verifier lanes.
- Did not add TinyFish.
- Did not create xersearch.
- Did not use cloud providers.
- Did not commit or push.

## Source Proxy Launch Truth

Repo-approved launch command found in `package.json`, `scripts/source-proxy-dev.mjs`, and `README.md`:

```powershell
npm run proxy:https:lan
```

Script expansion:

```text
node ./scripts/source-proxy-dev.mjs --https --lan
```

Actual uvicorn child command observed:

```text
Z:\.venv-source-proxy-windows\Scripts\python.exe -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 --ssl-certfile Z:\certificates\spirit-dev.pem --ssl-keyfile Z:\certificates\spirit-dev-key.pem
```

Expected URL:

- Source Proxy listener: `https://0.0.0.0:8787`
- Local probe URL used: `https://127.0.0.1:8787`
- Next default fallback bases when `SOURCE_PROXY_ORIGIN` is unset: `http://127.0.0.1:8787`, then `https://127.0.0.1:8787`

Local env/config found:

- `.env.local` contains `SPIRIT_CODING_USE_PROXY=true`.
- No local `SOURCE_PROXY_ORIGIN`, `SOURCE_PROXY_HOST`, `SOURCE_PROXY_PORT`, `SOURCE_PROXY_TLS`, or `SOURCE_PROXY_USE_HTTPS` override was found in `.env.local`.
- `config/source-proxy.example.env` documents `SOURCE_PROXY_HOST=127.0.0.1` and `SOURCE_PROXY_PORT=8787`.

## Runtime Actions

Initial state:

- `8787` was down.
- Only `3000` was listening.

Action:

- Started Source Proxy with `npm run proxy:https:lan`.
- Wrote launch logs:
  - `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-source-proxy-stdout.log`
  - `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-source-proxy-stderr.log`
- Restarted Source Proxy after patching latest-receipt ordering.
- Wrote restart logs:
  - `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-source-proxy-restart-stdout.log`
  - `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-source-proxy-restart-stderr.log`

Runtime result:

- `0.0.0.0:8787` is listening.
- `/v1/self/status` returns `200 OK`.
- `/healthcheck` returns `503` because NVIDIA VRAM metrics are unavailable (`NVML Shared Library Not Found`, `nvidia-smi` missing). This does not block prompt-packet or receipt retrieval.
- Expenditure database connection failed at startup, but logs state the server continued with expenditure logging disabled.

## Patch Targets

- `source_proxy/api/decision.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`
- `src/app/v1/decisions/fip0-receipts/latest/route.ts`
- `src/app/v1/decisions/fip0-receipts/[runId]/route.ts`
- `src/app/v1/decisions/fip0-receipts/__tests__/route.test.ts`
- `src/app/coding/page.tsx`

## Implementation Summary

- Kept the FIP-0 receipt foundation and retrieval routes from FIP-0.1/FIP-0.1R.
- Fixed `GET /v1/decisions/fip0-receipts/latest` to sort by receipt `timestamp` before filesystem mtime. Runtime proof showed mtime ordering on the share could return an older receipt.
- Added a small `/coding` link to `/v1/decisions/fip0-receipts/latest` so an authenticated operator can retrieve the latest receipt from the app-origin session.

## Runtime Proof

Direct Source Proxy prompt-packet proof:

```text
POST https://127.0.0.1:8787/v1/decisions/prompt-packet
```

Result:

- Status: success
- Run ID: `fip0-9445f3d31d301d82`
- Receipt path: `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-9445f3d31d301d82.json`
- Final verdict: `GO: fip0_receipt_foundation_complete_runtime_lanes_not_yet_wired`

Latest receipt retrieval proof:

```text
GET https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest
```

Result:

- Returned run ID: `fip0-9445f3d31d301d82`
- Returned the same receipt path as the prompt-packet response.
- Receipt field verification:
  - `run_id`: present
  - `final_packet_hash`: present
  - `coder_received_packet_hash`: field present
  - all required lane status fields present
  - all required lane status values are one of `used`, `skipped`, `blocked`, or `failed`

By-run retrieval proof:

```text
GET https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-9445f3d31d301d82
```

Result:

- Returned run ID: `fip0-9445f3d31d301d82`
- `final_packet_hash`: present
- `coder_received_packet_hash`: field present

## Next App-Origin/Auth Truth

Next app-origin proxy code inspected:

- `src/app/v1/decisions/prompt-packet/route.ts`
- `src/app/v1/decisions/route/route.ts`
- `src/lib/source-proxy-origin.ts`
- `src/app/v1/decisions/fip0-receipts/latest/route.ts`
- `src/app/v1/decisions/fip0-receipts/[runId]/route.ts`

Next uses:

- `SPIRIT_CODING_USE_PROXY`
- `SOURCE_PROXY_ORIGIN`
- `SOURCE_PROXY_HOST`
- `SOURCE_PROXY_PORT`
- `SOURCE_PROXY_TLS`
- `SOURCE_PROXY_USE_HTTPS`

Configured local state:

- `SPIRIT_CODING_USE_PROXY=true`
- No Source Proxy origin override, so Next should use default fallback bases and reach `https://127.0.0.1:8787` after HTTP fallback fails.

Unauthenticated CLI app-origin probes:

- `http://127.0.0.1:3000/coding`: `401 {"error":"unauthorized"}`
- `http://127.0.0.1:3000/v1/decisions/prompt-packet`: `401 {"error":"unauthorized"}`
- `http://127.0.0.1:3000/v1/decisions/fip0-receipts/latest`: `401 {"error":"unauthorized"}`

Interpretation:

The remaining app-origin blocker is the Codex shell/browser session lacking Britton's authenticated `/coding` session. The Source Proxy runtime and receipt retrieval are now reachable and proven directly. The app-origin route cannot be tested from unauthenticated CLI because the request is rejected before route execution.

## Manual Auth Follow-Up

Britton reported that the authenticated `/coding` browser path passed and successfully reached:

- `/v1/decisions/prompt-packet`
- `/v1/verification/diff-preview`
- `/v1/actions/execute-approved`

Manual `/coding` diagnostic task id:

`task_30470ca94889`

This clears the previous generic 401/auth blocker for the `/coding` hot path.

However, the manual proof prompt was intended to be receipt-only and the system treated it as a coding task. It selected and applied a whitespace-only diff to:

`source_proxy/api/action_preview.py`

Approved action audit receipt:

- `task_id`: `task_30470ca94889`
- `approval_id`: `approval-7d8fa9180bc42ce5`
- `backup_manifest`: `.spirit-backups/2026-06-13/approved-diff-2026-06-13T225247_486310_0000/manifest.json`
- `approved_diff_path`: `.spirit-backups/2026-06-13/approved-diff-2026-06-13T225247_486310_0000/approved.diff`
- `sha256_before`: `f0c94b25750fdd95e68bcfd20edb1ab383990b966e9832ea733c644536717e38`
- `sha256_after`: `87cf099f695760446671ae6a0e64adb1fbb7fb655f4e8f4942905150e8527622`

Revert status:

- `source_proxy/api/action_preview.py` was restored to the pre-apply shape.
- `git diff -- source_proxy/api/action_preview.py` is empty.
- Current SHA256 is `f0c94b25750fdd95e68bcfd20edb1ab383990b966e9832ea733c644536717e38`, matching the audit receipt's `sha256_before`.

Authenticated latest-receipt browser proof status:

- PASSED by Britton manual authenticated browser proof on 2026-06-13.
- Browser hit: `10.0.0.186:3000/v1/decisions/fip0-receipts/latest`.
- Returned real receipt from the app-origin route.
- Run ID: `fip0-9445f3d31d301d82`.
- `final_packet_hash`: present.
- `coder_received_packet_hash`: present but empty by design because Qwen coder is skipped in FIP-0.
- Every lane status used a valid value: `used`, `skipped`, `blocked`, or `failed`.
- Final verdict: `GO: fip0_receipt_foundation_complete_runtime_lanes_not_yet_wired`.
- The previous `HUMAN_AUTH_PROOF_REQUIRED` blocker is resolved by Britton's manual authenticated browser proof.

## Commands Run

- `Get-Content -Raw package.json`
- `Get-Content -Raw scripts/source-proxy-dev.mjs`
- `Get-Content -Raw config/source-proxy.example.env`
- `rg -n "proxy:dev|proxy:https|SOURCE_PROXY_ORIGIN|SOURCE_PROXY_HOST|SOURCE_PROXY_PORT|8787|source-proxy-dev|uvicorn|source proxy" ...`
- `Get-ChildItem -Force .env,.env.local,config/source-proxy.env,certificates/spirit-dev.pem,certificates/spirit-dev-key.pem`
- `Select-String` for Source Proxy env names in `.env.local`
- `Get-NetTCPConnection -State Listen`
- `curl.exe -k -sS -i --max-time 10 https://127.0.0.1:8787/healthcheck`
- `npm run proxy:https:lan`
- `curl.exe -k -sS -i --max-time 20 https://127.0.0.1:8787/v1/self/status`
- `curl.exe -k -sS --max-time 60 ... https://127.0.0.1:8787/v1/decisions/prompt-packet`
- `curl.exe -k -sS --max-time 20 https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest`
- `curl.exe -k -sS --max-time 20 https://127.0.0.1:8787/v1/decisions/fip0-receipts/fip0-9445f3d31d301d82`
- `curl.exe -i --max-time 15 http://127.0.0.1:3000/coding`
- `curl.exe -i --max-time 15 http://127.0.0.1:3000/v1/decisions/fip0-receipts/latest`
- `git diff -- source_proxy/api/action_preview.py`
- `Select-String -Path data\approved_actions.audit.jsonl -Pattern 'task_30470ca94889|source_proxy/api/action_preview.py'`
- `Get-FileHash -Algorithm SHA256 source_proxy/api/action_preview.py`
- `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q`
- `npm run typecheck -- --pretty false`
- `git diff --check`

## Check Results

- `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q`: PASS, 25 passed.
- `npm run typecheck -- --pretty false`: PASS.
- `git diff --check`: PASS with line-ending warnings only.
- Source Proxy reachability using configured URL: PASS on `https://127.0.0.1:8787/v1/self/status`.
- Source Proxy prompt-packet receipt write: PASS.
- Source Proxy latest receipt retrieval: PASS after timestamp-ordering fix.
- App-origin `/coding` route from CLI: expected unauthenticated 401; Britton manual authenticated browser proof is authoritative.
- App-origin receipt route from CLI: expected unauthenticated 401; Britton manual authenticated browser proof is authoritative.
- Human-authenticated `/coding` path: PASSED per Britton manual report.
- Human-authenticated app-origin `/v1/decisions/fip0-receipts/latest`: PASSED per Britton manual report for run `fip0-9445f3d31d301d82`.
- Accidental mutation revert: PASSED.
- Authenticated browser `/v1/decisions/fip0-receipts/latest`: PASSED by Britton manual browser proof.

## Files Changed

- `source_proxy/api/decision.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`
- `source_proxy/api/action_preview.py` was accidentally changed by the manual run and then restored to pre-apply SHA; no final diff remains.
- `src/app/v1/decisions/fip0-receipts/latest/route.ts`
- `src/app/v1/decisions/fip0-receipts/[runId]/route.ts`
- `src/app/v1/decisions/fip0-receipts/__tests__/route.test.ts`
- `src/app/coding/page.tsx`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-runtime-auth-hot-path-unblocker.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-9445f3d31d301d82.json`
- Source Proxy launch/restart logs under `docs/evidence/source-proxy-full-integration-pivot/`

Unrelated pre-existing tracked change observed and not touched:

- `scripts/media/face_organizer.py`

## Verdict

INCREMENT VERDICT: GO

Reason:
The accidental `source_proxy/api/action_preview.py` mutation was reverted and runtime FIP-0 receipt retrieval is valid. Britton's manual authenticated browser proof confirms the app-origin `/v1/decisions/fip0-receipts/latest` route returned the real receipt for run `fip0-9445f3d31d301d82`, with `final_packet_hash` present, `coder_received_packet_hash` present but empty by FIP-0 design, valid lane statuses, and final verdict `GO: fip0_receipt_foundation_complete_runtime_lanes_not_yet_wired`. The previous `HUMAN_AUTH_PROOF_REQUIRED` blocker is resolved.

## Accepted Manual Britton Proof

- Browser hit: `10.0.0.186:3000/v1/decisions/fip0-receipts/latest`
- Run ID: `fip0-9445f3d31d301d82`
- App-origin receipt route: PASSED
- FIP-0.1S status: GO

## Restart Discipline For Next Increment

1. Keep Source Proxy running with:

   ```powershell
   npm run proxy:https:lan
   ```

2. Restart the runtime on the Linux `source-server` host from the real runtime checkout, not only from the Windows share path.
3. Verify the reachable Source Proxy URL:

   ```text
   https://127.0.0.1:8787
   ```

4. Direct receipt write/retrieve checks should target `https://127.0.0.1:8787`.
5. App-origin checks on `10.0.0.186:3000` require Britton's authenticated browser session; unauthenticated CLI 401 does not invalidate the manual proof.

## FIP-0.2 Follow-Up Required

Before any deeper FIP work, harden receipt truth semantics so foundation-only receipts do not imply live SearXNG execution and empty coder hashes are allowed only with explicit skipped Qwen status.

## Stop Gate

Do not start FIP-1.
Stop after FIP-0.2 and wait for Britton.

Next permitted action:

`FIP-0.2 only`
