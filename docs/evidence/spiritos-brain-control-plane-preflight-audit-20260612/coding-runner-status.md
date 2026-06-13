# Coding Runner Status

## Frontend Components And Routes

Main `/coding` route:

- `src/app/coding/page.tsx`
- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/CodingAgentInterface.tsx`
- `src/components/coding/approval-gate-binding.ts`

Supporting tests and fixtures:

- `src/app/coding/__tests__/page.test.tsx`
- `src/components/coding/__tests__/**`
- `src/lib/coding/__tests__/**`
- `tests/e2e/coding-ui.spec.mjs`
- `tests/ui-agent-trials/**`

## Backend/API Routes Used By Runner

Next app routes:

- `/v1/coding/runs`
- `/v1/coding/runs/active`
- `/v1/coding/runs/recent`
- `/v1/coding/runs/{runId}`
- `/v1/coding/runs/{runId}/rows/{promptId}`
- `/v1/coding/codex`
- `/v1/coding/bounded-diff-preview`
- `/v1/coding/self-tests/run`
- `/v1/coding/research-preview`
- `/v1/coding/design-vault/preview`
- `/v1/coding/cartographer/preview`
- `/v1/coding/gauntlet/preview`
- `/v1/coding/mac-advisory`

Source Proxy routes:

- `/v1/coding/codex`
- `/v1/coding/bounded-diff-preview`
- `/v1/coding/self-tests/run`
- `/v1/decisions/prompt-packet`
- `/v1/verification/diff-preview`
- `/v1/actions/preview`
- `/v1/tasks/long-running/{task_id}/execute-approved`

## Persistence, Refresh, Mobile/Desktop Sync

`src/lib/coding/durable-run-store.ts` persists runs to `SPIRIT_CODING_RUNS_STORE` or `data/coding-runs.json`. It has atomic writes through temp file + rename, a mutation queue, recent run listing, active run lookup, run patching, row upsert, duplicate running row demotion, terminal reopen protection, write-debug records, and invariant violations.

Active runs can survive refresh if they are written to the durable store and not only held in component state. Some legacy UI state still uses localStorage for activity logs and local cockpit state, so not every UI detail is durable.

Mobile/desktop sync is plausible through the shared server store, but this audit did not run a live two-browser sync test.

## Result Diagnostics

Diagnostics are visible in runner-related code: reason codes, receipt classes, changed files, applied files, disk files, endpoint statuses, provider/model proof fields, coder diagnostics, write debug, invariant violations, and copy-run-diagnostics UI text. Durable rows carry provenance fields separating scaffold/fallback/parser repair/model output.

## Output Previews

The command center has preview/diff paths and verification target inference. This audit did not prove clickable preview links end-to-end in a browser. Existing route tests cover preview-only route payloads.

## Multiple Lanes/Workers

The UI and docs reference several lanes: coder, research, design vault, Cartographer preview, Mac worker, helper agents, combined gauntlet. Many are preview/advisory. The durable store defaults `lane: "coder"` in empty runs. Real concurrent multi-lane worker execution is not proven.

## Evidence/Memory Write-Back

Runner results are saved to durable run JSON and evidence docs exist from prior runs. This audit did not find direct automatic ingestion from runner results into Obsidian. Future memory ingestion should treat durable runs and evidence docs as proof sources, then write to Obsidian only through approval-gated summaries.

## Readiness For Multi-Lane Testing

Current readiness: PARTIAL

Ready for: local preview, durable run tracking, row-level diagnostics, selected backend regressions, approval-gated apply paths.

Not ready for: unattended multi-lane Codex/local/API testing, automatic memory write-back, or product-behavior PASS without browser/verifier proof.

## Audit Checks

Backend/context checks passed. Typecheck passed. Coding backend regression slice had 2 failures. Frontend coding regression command failed due Vitest module resolution on `Z:\` after reporting 161 passed tests and 5 failed suites.
