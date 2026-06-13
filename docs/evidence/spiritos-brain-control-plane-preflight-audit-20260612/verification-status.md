# Verification Status

## Available Tests

Python:

- Source Proxy unit/regression tests under `source_proxy/tests/**`
- Obsidian/context/self-status/routing tests
- coding regression, diff verification, long-running, Codex adapter, Cartographer tests

TypeScript/Vitest:

- `/coding` page and component tests
- coding route tests
- durable run store and invariants
- approval gate and proxy payload tests
- dashboard/component tests

Browser/Playwright:

- `tests/e2e/coding-ui.spec.mjs`
- `tests/ui-agent-trials/**`
- Playwright config exists

Static checks:

- `npm run typecheck`
- `npm run lint`
- package scripts for coding regression and frontend regression

## Behavior Audit Patterns

Existing verifier patterns include:

- diff parsing and preview
- protected-path/secret-path blocking
- replacement content validation
- subjective visual materiality checks
- changed-file diagnostics
- durable run invariant checks
- terminal reopen blocking
- duplicate running row demotion
- approval preview vs apply separation

## Screenshot/Preview Support

Playwright tests and prior evidence support browser proofs. This audit did not run browser screenshots. Current frontend regression command failed on a mapped-drive Vitest module-resolution problem, so UI proof is incomplete in this run.

## Diff/File Mutation Checks

`source_proxy/verification/diff.py` checks diff size, path safety, high-risk files, patch structure, and deterministic checks. Apply is separated into approval-gated long-running task execution.

## False-Positive Prevention

Improving but incomplete. The code has stronger diagnostics for no diff, shallow visual diffs, target mismatch, protected paths, changed files, and runtime provenance. Product behavior is still not universally tested. Recent examples show calculator/theme/static-habit false positives can happen if only artifact/runtime existence is scored.

## GO/PASS/FAIL Representation

Current labels are distributed:

- `PASS`, `FAIL`, `NEEDS FIX`, `INVALID`, `RUNNING` in coding runner/result UI.
- `GO`/`NO-GO` in evidence docs.
- `preview_ready`, `blocked`, `requires_human_approval`, reason codes in route/verification payloads.

Risk: no single canonical result schema guarantees that product behavior PASS means runtime, artifact, apply, and behavior all passed.

## Product Behavior Testing

Partial. Some tests inspect UI states, diff materiality, changed files, and route payloads. Full product behavior proof for arbitrary generated apps is missing. Cerebellum v0.1 must run behavior-specific probes, not just check files exist.

## Memory/Context Claims

Tested:

- Obsidian disabled/missing/select/exclude/redact/default-vault.
- context-source readiness packet shape.
- self-status includes memory diagnostics.

Not tested:

- Obsidian context injection into actual route/model/worker decisions.
- stale/conflict handling.
- automatic memory learning.

## Obsidian Context Injection Tests

`source_proxy/tests/test_obsidian_context.py` and `test_context_source_readiness.py` prove read-only query/packet behavior. They do not prove the main Source Proxy execution path uses selected Obsidian notes.

## Audit Test Results

Passed:

- 87 Python tests for Obsidian/context/self-status/prompt metadata/routing/Ollama route.
- `npm run typecheck`.

Failed:

- 2 failures in focused coding backend regression slice:
  - `test_component_trial_warning_uses_live_model_proof_path`: expected payload was `None`.
  - `test_provider_model_proof_fields_set_when_provider_call_starts`: central gate increment mismatch.
- frontend coding regression: 161 tests passed but 5 suites failed importing Vitest from `Z:\@id\Z:\node_modules\vitest\dist\index.js`.

## Cerebellum v0.1 Requires

- Canonical verdict contract separating runtime/artifact/apply/product behavior.
- Product-specific probes for generated tasks.
- Browser screenshot/click/type/assert support for UI tasks.
- Diff + behavior checks tied to the same task.
- Memory/context claim tests.
- Obsidian injection tests if Obsidian is promoted.
- False-positive fixtures for calculator, theme, static tracker, no-op, and shallow visual changes.
