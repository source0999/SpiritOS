# Codex Source Verification Notes

Review mode: ARPA independent review, read-only except this `codex-review/` artifact set.

## Baseline

- Date: `2026-06-19T23:28:39.2233603-04:00`
- Hostname: `Spirit`
- PWD: `Z:\`
- Branch: `master`
- Current HEAD: `a9ce0c2c feat: simplify SpiritFlix smart tagging operator view`
- Recent history: `a9ce0c2c`, `faa33358`, `fbe976cf`, `f5638db1`, `537b1044`, `328b3f3b`, `007ea217`, `ae2afdca`.
- Staged files: none (`git diff --cached --name-status` returned no output).
- Working tree: dirty before this review. Dirty files include unrelated SpiritFlix/media/runtime files and the untracked Plan 0 artifact directory. I did not stage, reset, restore, stash, move, delete, commit, or push anything.

Because no files were staged, I do not block on the Stage 0 staged-file gate. The broader dirty tree remains a risk for future live proof and is reported here.

## Artifact Completeness

Required Plan 0 artifacts present under `plan-00/artifacts/`:

- `README.md`
- `0.1-canonical-active-route.md`
- `0.2-machinery-health-check.md`
- `0.3-reuse-adapt-retire-matrix.md`
- `0.4-human-brain-integration-contract.md`
- `0.5-mvi-contract-and-feasibility.md`
- `0.6-risk-evidence-reviews-authority.md`
- `0.7-compression-decision.md`
- `plan-00-closeout-verdict.md`

JSON syntax check passed for all `*.json` files under `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/`.

## Active Route

`src/app/coding/page.tsx` confirms the active `/coding` page imports and renders `CodingCockpitShell`:

- `src/app/coding/page.tsx:5` imports `CodingCockpitShell`.
- `src/app/coding/page.tsx:28` renders `<CodingCockpitShell />`.

Older `CodingCommandCenterShell` and `CodingAgentInterface` files still exist, but the active route does not render them.

## Advisory Route

`src/app/v1/decisions/route/route.ts` is a thin Next proxy:

- `src/app/v1/decisions/route/route.ts:5-9` returns `409` unless `SPIRIT_CODING_USE_PROXY` is true.
- `src/app/v1/decisions/route/route.ts:15-21` forwards the request body to Source Proxy `/v1/decisions/route`.
- `src/app/v1/decisions/route/route.ts:33-46` returns the proxied response with optional repo-first research-source merge.

`source_proxy/api/decision.py` implements `/route` as route-decision enrichment only:

- `source_proxy/api/decision.py:6134-6142` builds a `DecisionInput`, calls `decide_route(...)`, enriches it with research, and returns `_with_bridge_route(decision.as_payload())`.

I found no evidence that this route applies diffs, changes task state, writes approval records, or mutates the workspace. It is advisory-only from current source.

## Decision-Bearing Apply Path

The decision-bearing apply path is the long-running task execute-approved path plus central gate:

- `source_proxy/api/long_running_tasks.py:110-129` exposes `POST /long-running/{task_id}/execute-approved`, requires `approved is True`, and delegates to `execute_approved_action(...)`.
- `source_proxy/approval/gate.py:54-78` delegates approved action execution to `execute_approved_long_running_task(...)`; the gate wrapper itself does not apply edits.
- `source_proxy/tasks/long_running.py:842-858` begins `execute_approved_long_running_task(...)` and calls `central_gate_check("apply", run_id=f"execute_approved_long_running_task:{task_id}")` before lookup and approval verification.
- `source_proxy/tasks/long_running.py:860-869` recomputes the expected `approval_id` from task/diff/target and rejects mismatches with `approval_id_mismatch`.

Central gate fail-closed behavior is confirmed:

- `source_proxy/approval/external_gate.py:71-76` rejects malformed, blocked, or closed gate state.
- `source_proxy/approval/external_gate.py:77-90` rejects increment mismatch, missing approval token, or an action not allowed for the increment.
- `source_proxy/approval/external_gate.py:93-101` returns `ExternalGateReceipt` only after all checks pass.

## Identifier Findings

Safe search across `source_proxy/**/*.py`:

- `task_id`: 49 files
- `approval_id`: 17 files
- `run_id`: 37 files
- `trace_id`: 0 files
- `invocation_event_id`: 0 files
- `consumer_event_id`: 0 files
- `consumer_subsystem`: 0 files

The current live apply path therefore carries `task_id`, `approval_id`, and `run_id`, but it does not carry the four required causal proof fields.

## Machinery Classification Notes

- Central gate: healthy/fail-closed from `external_gate.py`; blocks before apply when state, increment, token, or action is invalid.
- Cartographer: reusable machinery, but preview/approval-bounded at public API. `source_proxy/api/cartographer.py` repeatedly returns `api_preview_only: True`, `commit_enabled: False`, `push_enabled: False`, and `git_mutation_authority_granted: False` on commit/push-related surfaces. It also exposes safe-write paths, so Plan 1 must avoid treating Cartographer as autonomous authority.
- Runtime/self status: source status manifests are read-only/advisory surfaces.
- Obsidian: `source_proxy/context/obsidian.py` reports `obsidian_read_only: True`; `source_proxy/context/source_readiness.py` reports `can_write_memory: False`, `hidden_memory_writes: False`, and `hidden_code_writes: False`.
- Mac worker: `scripts/mac-worker/spirit_mac_worker.py` and `.mjs` are real worker scripts. They include advisory context/search/scout/browser-check packets and `run_safe_check`; first-write/use remains a hard stop under this task, and I did not invoke them.
- Scout/SearXNG: Scout exists as a separate package and Source Proxy has Scout/SearXNG diagnostics/profile code. SearXNG is represented in `backend/docker-compose.yml` and diagnostics, not as a core `source_proxy` subsystem. GLM's caution on SearXNG as not core decision-bearing is fair, though wording should distinguish "not in source_proxy" from "not tracked anywhere."
- Model lanes: Qwen/Hermes/Gemma lane metadata and Ollama routing are present in `source_proxy/decision/model_lanes.py`, `source_proxy/routing/ollama_route.py`, `source_proxy/routing/litellm_router.py`, tests, and status surfaces. I did not run model calls.
