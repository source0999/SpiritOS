# FIP State Reconciliation After Duplicate FIP-4

Status: CAN_RESUME_FIP-7R

Scope: reconciliation only. This did not start FIP-7R, rerun FIP-5, rerun FIP-6, start Integrated Level 3, add TinyFish, create xersearch, commit, or push.

## Authoritative Timeline

- FIP-0 GO
- FIP-1 GO
- FIP-2 GO
- FIP-3 GO
- FIP-4 GO
- FIP-5 GO
- FIP-6 GO
- FIP-7 NO-GO
- Next intended action: FIP-7R remediation only, after this reconciliation

## Required Reads Checked

- `docs/evidence/source-proxy-full-integration-pivot/fip-0-closeout.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-1-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-2-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-3-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-4-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-5-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-6-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-integrated-gauntlet-report.md`
- `scripts/fip7_gauntlet_runner.py`
- `source_proxy/api/decision.py`
- `source_proxy/decision/model_lanes.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`
- `src/app/coding/page.tsx`
- `src/app/v1/decisions/fip0-receipts/latest/trace/route.ts`
- `src/app/v1/decisions/fip0-receipts/[runId]/trace/route.ts`

## Command Results

- `git status --short`: dirty tree; 19 tracked modified files and 145 untracked files.
- `git diff --stat`: tracked diff includes Source Proxy FIP files plus unrelated SpiritFlix/media files; Source Proxy tracked diff is concentrated in `source_proxy/api/decision.py`, `source_proxy/decision/model_lanes.py`, `source_proxy/tests/test_prompt_packet_context_metadata.py`, and `src/app/coding/page.tsx`.
- `git diff --name-status`: no delete/rename of FIP-5/FIP-6/FIP-7 files observed.
- FIP-5 marker search: found verifier/repair-loop symbols in `source_proxy/api/decision.py`, `scripts/fip7_gauntlet_runner.py`, FIP receipts, and tests.
- FIP-6 marker search: found trace route/projection symbols in Source Proxy, app-origin trace routes, FIP docs, receipts, and tests.
- FIP-7 marker search: found `scripts/fip7_gauntlet_runner.py`, FIP-7 gauntlet artifacts, `qwen_coder_call_failed`, `scout_http_status_error`, and the FIP-7 NO-GO report language.
- `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q`: timed out twice from the Windows SMB checkout.
- Linux runtime equivalent: `.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q` passed with `49 passed in 15.34s`.
- `npm run typecheck -- --pretty false`: PASS.
- `git diff --check`: PASS with line-ending warnings only.

## Reconciliation Checks

1. FIP-5 verifier and repair loop code still exists.
   - `source_proxy/api/decision.py` still contains `_fip5_verifier_enabled`, `_fip5_call_hermes_verifier`, `_fip5_call_qwen_repair`, `_run_fip5_verifier_and_repair`, `cannot_turn_unverified_into_pass`, `cannot_override_browser_behavior`, `repair_loop_status`, and `repair_attempt_count`.
   - `source_proxy/tests/test_prompt_packet_context_metadata.py` still contains FIP-5 verifier, repair-loop, browser-authority, and protected-path tests.

2. FIP-6 trace endpoints and projection code still exist.
   - Source Proxy live runtime returned `200` for `https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest/trace`.
   - By-run live runtime trace returned `200` for `fip0-8a633b11eb895d6e` with `trace_version=fip6.operator_trace.v1` and `trace_authority=operational_receipt_projection_no_private_reasoning`.
   - App-origin routes still exist at `src/app/v1/decisions/fip0-receipts/latest/trace/route.ts` and `src/app/v1/decisions/fip0-receipts/[runId]/trace/route.ts`.

3. FIP-7 gauntlet runner and report artifacts still exist.
   - `scripts/fip7_gauntlet_runner.py` exists.
   - `docs/evidence/source-proxy-full-integration-pivot/fip-7-integrated-gauntlet-report.md` exists and records FIP-7 status `NO-GO`.
   - `docs/evidence/source-proxy-full-integration-pivot/fip-7-mini-context-pack.md` exists and says `Integrated Level 3 is not ready`.
   - `docs/evidence/source-proxy-full-integration-pivot/fip-7-gauntlet/` contains raw/results artifacts.

4. Duplicate FIP-4 did not overwrite or regress FIP-5/FIP-6/FIP-7 source.
   - The later FIP-4 pack references only receipts `fip0-36deb32ba4fdb2a0`, `fip0-52e787f2903ff57e`, and `fip0-8a633b11eb895d6e`.
   - FIP-5/FIP-6/FIP-7 source markers and artifacts remain present after the duplicate FIP-4 pack timestamp.
   - No FIP-5/FIP-6/FIP-7 source file is deleted.
   - Current global resume point is still after FIP-7 NO-GO, not after the duplicate FIP-4 pack.

5. Dirty file classification follows below.

6. Only one active Source Proxy runtime process/session was found.
   - `ps` on `source-server` showed one active Source Proxy process:
     `/home/source/SpiritOS/.venv-source-proxy/bin/python -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 ...`

7. Active runtime is the Linux `source-server` checkout.
   - `ssh source@10.0.0.186 hostname` returned `source-server`.
   - Active process command points at `/home/source/SpiritOS`.

8. Current runtime has FIP-6 trace endpoints available.
   - Latest trace endpoint returned `200`.
   - By-run trace endpoint returned `200`, `fip6.operator_trace.v1`, and `operational_receipt_projection_no_private_reasoning`.

## Dirty File Classification

Accepted current timeline work:

- `source_proxy/api/decision.py`
- `source_proxy/decision/model_lanes.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`
- `src/app/coding/page.tsx`
- `src/app/v1/decisions/fip0-receipts/[runId]/route.ts`
- `src/app/v1/decisions/fip0-receipts/[runId]/trace/route.ts`
- `src/app/v1/decisions/fip0-receipts/__tests__/route.test.ts`
- `src/app/v1/decisions/fip0-receipts/latest/route.ts`
- `src/app/v1/decisions/fip0-receipts/latest/trace/route.ts`
- `scripts/fip7_gauntlet_runner.py`
- `docs/evidence/source-proxy-context-orchestration-master-plan/SUPERSEDED_BY_FIP.md`
- `docs/evidence/source-proxy-full-integration-pivot/README.md`
- `docs/evidence/source-proxy-full-integration-pivot/active-context.md`
- `docs/evidence/source-proxy-full-integration-pivot/bootstrap-cleanout-receipt.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-closeout.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1-universal-truth-receipt-foundation.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1R-authed-hot-path-proof.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1R-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1R-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-runtime-auth-hot-path-unblocker.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-source-proxy-restart-stderr.log`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-source-proxy-restart-stdout.log`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-source-proxy-stderr.log`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.1S-source-proxy-stdout.log`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0.2-receipt-truth-semantics-and-runtime-discipline.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-1-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-1-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-2-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-2-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-3-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-3-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-5-browser-proof.html`
- `docs/evidence/source-proxy-full-integration-pivot/fip-5-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-5-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-5-runtime-target.txt`
- `docs/evidence/source-proxy-full-integration-pivot/fip-6-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-6-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-gauntlet/fip-7-gauntlet-raw.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-gauntlet/fip-7-gauntlet-rerun-raw.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-gauntlet/fip-7-gauntlet-rerun-results.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-gauntlet/fip-7-gauntlet-results.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-integrated-gauntlet-report.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/cartographer-note.txt`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/design-context-note.txt`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/noop-note.txt`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/repair-note.txt`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/repo-context-note.txt`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/scout-note.txt`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/search-note.txt`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/skipped-lane-note.txt`
- `docs/evidence/source-proxy-full-integration-pivot/master-plan.md`
- `docs/evidence/source-proxy-full-integration-pivot/new-chat-handoff.md`
- `docs/evidence/source-proxy-full-integration-pivot/superseded-index.md`
- FIP receipt files in `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/`, except the duplicate/stale FIP-4 receipts called out below.

Duplicate/stale FIP-4 work:

- `docs/evidence/source-proxy-full-integration-pivot/fip-4-mini-context-pack.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-4-mini-context-pack.xml`
- `docs/evidence/source-proxy-full-integration-pivot/fip-4-runtime-target.txt`
- `docs/fip4-runtime-target.txt`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-36deb32ba4fdb2a0.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-52e787f2903ff57e.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-8a633b11eb895d6e.json`

Unrelated pre-existing dirty work:

- `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T02-19-36-375Z-design-mobile-britton-realistic/design/design-design-002-mobile-overlap-detection/design-design-002-mobile-overlap-detection.png`
- `docs/media/spiritflix-anime-importer.md`
- `scripts/media-ingest-worker.mjs`
- `scripts/media/face_organizer.py`
- `scripts/media/model_index.json`
- `scripts/media/performer_verification.json`
- `source_proxy/decision/research.py`
- `source_proxy/decision/scout_research.py`
- `source_proxy/tests/test_scout_research_bridge.py`
- `src/app/api/spiritflix/face-metadata/route.ts`
- `src/components/spiritflix/SpiritFlixApp.tsx`
- `src/components/spiritflix/SpiritFlixHome.tsx`
- `src/components/spiritflix/SpiritFlixPlayer.tsx`
- `src/lib/spiritflix-jellyfin-client.ts`
- `src/lib/spiritflix-types.ts`
- `docs/evidence/media/face-organizer-plan-8-review-ui-correction-audit-20260613.md`
- `docs/evidence/media/face-organizer-plan-9-enrollment-queue-route-20260613.md`
- `docs/plans/media/face-organizer-full-system-integration-20260613.md`
- `docs/plans/media/face-organizer-full-system-integration-handoff-20260613.md`
- `scripts/media/face_enrolled_performers.html`
- `scripts/media/face_enrolled_performers.json`
- `scripts/media/face_enrollment_queue.html`
- `scripts/media/face_enrollment_queue.json`
- `scripts/media/face_organizer_context_packet.xml`
- `scripts/media/face_organizer_mini_packet.md`
- `scripts/media/face_organizer_mini_packet.xml`
- `scripts/media/face_organizer_system_diag.md`
- `scripts/media/face_verification_full_audit.html`
- `scripts/media/known_db_audit.html`
- `scripts/media/known_db_audit.json`
- `scripts/media/manual_crop.html`
- `scripts/media/test_face_organizer_schema.py`

Unknown/risky divergence:

- `docs/evidence/source-proxy-full-integration-pivot/fip-7R-closeout.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7R-failure-audit.md`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7R-gauntlet/fip-7R-gauntlet-interrupted-raw.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7R-gauntlet/fip-7R-gauntlet-interrupted-results.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7R-gauntlet/fip-7R-gauntlet-rerun-raw.json`
- `docs/evidence/source-proxy-full-integration-pivot/fip-7R-gauntlet/fip-7R-gauntlet-rerun-results.json`

These FIP-7R files are present even though the authoritative next action is "FIP-7R remediation only, after reconciliation." They should not be treated as accepted unless Britton explicitly accepts them.

## Verdict

CAN_RESUME_FIP-7R

Reason: current source still contains FIP-5 verifier/repair work, FIP-6 trace endpoints/projection, and FIP-7 gauntlet runner/report artifacts. The duplicate/stale FIP-4 pack did not regress the repo back to FIP-4. The active runtime is the Linux `source-server` checkout and currently serves FIP-6 trace endpoints.

## Exact Next Copy-Paste Prompt For FIP-7R Only

```text
BRITTON GO FIP-7R ONLY

Purpose:
Remediate the accepted FIP-7 NO-GO blockers only, using docs/evidence/source-proxy-full-integration-pivot/fip-state-reconciliation-after-duplicate-fip4.md as the resume authority.

Do not start Integrated Level 3.
Do not rerun FIP-5 as a phase.
Do not rerun FIP-6 as a phase.
Do not add TinyFish.
Do not create xersearch.
Do not commit or push.
Do not treat existing fip-7R-* artifacts as accepted unless this run verifies and supersedes them.

Allowed scope:
Fix only the FIP-7 NO-GO causes identified in docs/evidence/source-proxy-full-integration-pivot/fip-7-integrated-gauntlet-report.md and fip-7-mini-context-pack.md:
- qwen_coder_call_failed / local Ollama Qwen empty-output or timeout behavior
- scout_http_status_error / Scout HTTP 422 or no-allowed-packets truth issue
- any trace/receipt projection defects directly exposed while verifying those two blockers

Required verification:
- Confirm one active Source Proxy runtime on Linux source-server /home/source/SpiritOS.
- Restart runtime only if needed for FIP-7R fixes.
- Run focused tests for touched code.
- Run python Source Proxy receipt/trace tests using the Linux .venv-source-proxy command if Windows SMB pytest is too slow.
- Run npm run typecheck -- --pretty false.
- Run git diff --check.
- Rerun the FIP-7 gauntlet only after fixes and write fresh FIP-7R evidence that clearly supersedes any earlier unaccepted fip-7R artifacts.

Write:
- docs/evidence/source-proxy-full-integration-pivot/fip-7R-closeout.md

Verdict options:
- FIP-7R GO: FIP-7 blockers remediated and gauntlet passes with durable receipts and FIP-6 traces.
- FIP-7R NO-GO: blockers remain, with exact receipts/traces and next remediation target.
- CONFIG-BLOCKED: runtime, model inventory, Scout service, or tests cannot be checked.

Stop after FIP-7R. Do not start Integrated Level 3.
```
