# Tests And Commands Run

All commands were run from `Z:\` on 2026-06-12. No provider/model prompt calls or live benchmark prompts were run.

## Command Log

### `Select-String -Path 'C:\Users\smith\.codex\memories\MEMORY.md' -Pattern 'Source Proxy|/coding|Obsidian|Cartographer|coder_diagnostics|diff_preview_missing|spiritos' -Context 2,2`

Why: quick memory pass for relevant SpiritOS Source Proxy/coding context.

Result: found prior Source Proxy/coding memory entries, including local coder proof, gate behavior, and hard no-provider-call boundaries.

Pass/fail: PASS.

Important output: memory noted local route proof via `/v1/self/status` and `/v1/models`, central gate behavior on `/v1/chat/completions`, and prior coder diagnostics changes.

### `Get-Location; git status --short; git status --branch --short`

Why: record repo path, branch, and dirty tree before audit file creation.

Result: path `Z:\`; branch `master`; no short-status entries.

Pass/fail: PASS.

### `rg --files -g package/test/config files`

Why: detect package managers, test configs, lockfiles, and Python requirements.

Result: found `package.json`, `package-lock.json`, `tsconfig.json`, `vitest.config.mjs`, `playwright.config.mjs`, `requirements*.txt`, and Scout files.

Pass/fail: PASS.

### `rg -n "Source Proxy|source_proxy|..." -S ...`

Why: inventory Source Proxy, model routing, verdict, and artifact references.

Result: found Source Proxy routes, Cartographer docs/modules, model routing, evidence, and coding diagnostics references.

Pass/fail: PASS.

### `rg -n "coding|CodingCockpit|trial|runner|..." -S src app source_proxy scripts tests docs`

Why: inventory `/coding` and runner systems.

Result: found `/coding` tests, runner scripts, durable routes, command-center shell references, and trial diagnostics.

Pass/fail: PARTIAL. `rg` returned an error for missing `app` path but still produced useful matches from existing paths.

### `rg -n "Obsidian|obsidian|vault|Hippocampus|memory|context packet|Cartographer|..." -S`

Why: inventory Obsidian, memory, context, Cartographer, repo map, vector systems.

Result: found real Obsidian code/tests, context-source readiness, Cartographer modules, docs/evidence references.

Pass/fail: PASS.

### `Get-ChildItem` inventory commands

Why: list repo top-level directories and key Source Proxy/app files.

Result: found `docs`, `tests`, `source_proxy`, `src`, `backend`, `config`, `_blueprints`, `data`, `scripts`, and many route/module files.

Pass/fail: PASS.

### `Get-Content source_proxy/main.py`, `source_proxy/api/decision.py`, `source_proxy/self_status.py`, `package.json`

Why: inspect Source Proxy routers, decision entry points, self-status, and package scripts.

Result: confirmed routers, model/tool/context status, and test scripts.

Pass/fail: PASS.

### `Get-Content source_proxy/context/obsidian.py`, `source_proxy/api/obsidian_context.py`, `source_proxy/tests/test_obsidian_context.py`, `source_proxy/decision/prompt_packet.py`; `rg obsidian`

Why: inspect actual Obsidian wiring.

Result: confirmed read-only Obsidian discovery/query/redaction and tests. Prompt packets include diagnostics but not selected notes by default.

Pass/fail: PASS.

### `Get-Content source_proxy/context/source_readiness.py`, selected `decision.py`, `long_running.py`, `test_context_source_readiness.py`

Why: inspect context-source packet generation and whether Obsidian is packetized.

Result: confirmed Cartographer/Obsidian/Scout/design context packet builder, read-only authority, and tests.

Pass/fail: PASS.

### `rg build_context_source_readiness_packet...`; `Get-Content routing/codex/ollama/router files`

Why: determine if source readiness feeds route selection and inspect worker/model routing.

Result: found context-source readiness tests and definitions but no clear main route-decision integration. Local/API/Codex routing inspected.

Pass/fail: PASS.

### `python -m pytest -q source_proxy/tests/test_obsidian_context.py source_proxy/tests/test_context_source_readiness.py source_proxy/tests/test_self_status.py source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_proxy_agent_routing.py source_proxy/tests/test_ollama_route.py`

Why: safe focused backend tests for Obsidian, context, status, routing, and prompt metadata.

Result: `87 passed in 17.70s`.

Pass/fail: PASS.

### `python -m pytest -q source_proxy/tests/test_coding_regression_pack.py source_proxy/tests/test_coder_timing_diagnostics.py source_proxy/tests/test_diff_verification.py source_proxy/tests/test_verification_contracts.py`

Why: safe focused coding/verifier backend regression slice.

Result: `163 passed, 1 skipped, 2 failed`.

Pass/fail: FAIL.

Important output:

- `test_component_trial_warning_uses_live_model_proof_path`: expected payload was unexpectedly `None`.
- `test_provider_model_proof_fields_set_when_provider_call_starts`: central gate approved increment `evaluation-round` did not match expected `1.3`.

### `npm run test:coding-frontend-regression -- --run`

Why: safe frontend coding regression script.

Result: 161 tests passed before 5 suites failed import/setup. Error: `Cannot find module 'Z:\@id\Z:\node_modules\vitest\dist\index.js' imported from Z:\node_modules\vitest\dist\module-evaluator.js`.

Pass/fail: FAIL.

### `npm run typecheck`

Why: TypeScript static check.

Result: `tsc --noEmit` completed successfully.

Pass/fail: PASS.

### Static route/store/verifier inspections

Commands inspected durable run routes/store, Source Proxy chat/Codex/long-running/sandbox/safety files, route declarations, preview/diagnostic references, and design vault files.

Why: understand `/coding`, worker routes, verifier and permission surfaces without live calls.

Result: confirmed durable run store, Source Proxy bridge routes, gate boundaries, and default `data/design-vault`.

Pass/fail: PASS.

### Final `git status --short`

Why: confirm only audit docs are introduced after writing.

Result: only the new audit directory was untracked: `?? docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/`.

Pass/fail: PASS.
