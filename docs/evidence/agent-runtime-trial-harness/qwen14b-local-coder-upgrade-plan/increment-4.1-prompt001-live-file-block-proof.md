# Increment 4.1: Prompt 001 Live File-Block Proof

Phase 4 integrated the Prompt 001 dummy product-site create path with the file-block parser and repair contract.

## Changes

- Prompt 001 now asks for one file block per file in both the TypeScript prompt bank and JSON fixture definition.
- The dummy product-site create path reports structured output source (`xml_file_blocks`, `delimited_file_blocks`, or `json_create_file_bundle`), repair source, content caps, and safe honesty-gate summary.
- The prompt-packet response now exposes `diagnostics_summary` / `diagnosticsSummary` so the trial runner and grader can recognize the new output contract without scraping `relevant_context`.
- Trial proof keeps the central model-call gate, restores cold-start retry behavior, and supports a test-only opt-out for direct Ollama proof calls.
- Regression tests cover XML file blocks at both helper and prompt-packet surfaces, repair similarity blocking, caps/blacklist blocking, and closed-gate behavior.

## Live Prompt 001 Proof

Command path used a temporary approved gate state file for the process only; the repository gate remained closed afterward.

Result:

- HTTP status: `200`
- status: `preview_ready`
- reason_code: `dummy_product_site_create_bundle`
- provider: `local`
- model: `ollama_chat/qwen2.5-coder:14b`
- provider_call_made: `true`
- target: `tests/ui-agent-trials/fixtures/dummy-product-site/`
- changed files:
  - `tests/ui-agent-trials/fixtures/dummy-product-site/README.md`
  - `tests/ui-agent-trials/fixtures/dummy-product-site/package.json`
  - `tests/ui-agent-trials/fixtures/dummy-product-site/index.html`
  - `tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js`
  - `tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js`
  - `tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css`
- checks_run: `git apply --check`
- proposed_diff_length: `3772`
- structured_output_mode: `xml_file_blocks`
- file_block_repair_source: `xml_file_blocks`
- parsed_output_mode: `create_file_bundle`
- generated_diff_by_backend: `true`
- trial_result_trust_status: `model_authored_diff_proven`
- content_validation: `ok=true`, `file_count=6`, `total_lines=102`
- structured_honesty_gate: `status=passed`, `classifier_model=ollama_chat/phi4-mini:latest`, `phi4_mini_gatekeeper_configured=true`

The live run produced a preview diff only. It did not write the dummy fixture files.

## Verification

Passed:

```powershell
python -m pytest source_proxy/tests/test_coding_regression_pack.py -q
python -m pytest source_proxy/tests/test_coder_agent_repomix_diff.py -q
python -m pytest source_proxy/tests/test_external_gate.py source_proxy/tests/test_external_gate_integration.py source_proxy/tests/test_ollama_route.py -q
node ./scripts/gate-status
```

Observed:

- `source_proxy/tests/test_coding_regression_pack.py`: `62 passed`
- `source_proxy/tests/test_coder_agent_repomix_diff.py`: `51 passed`
- gate/external/ollama tests: `20 passed`
- `node ./scripts/gate-status`: `WAITING_FOR_HUMAN`

Not completed:

```powershell
npx vitest run src/lib/coding/__tests__/dummy-coder-10-prompts.test.ts src/lib/coding/__tests__/dummy-coder-10-grader.test.ts
```

Vitest failed before running tests with a Windows/Z-drive module path error:

```text
Cannot find module 'Z:\@id\Z:\node_modules\vitest\dist\index.js'
```

The timed-out broad `npm test -- --runInBand` process was stopped; no Vitest worker remained afterward.

## Gate State

The central gate remained closed after the live proof:

```json
{
  "status": "WAITING_FOR_HUMAN",
  "approved_increment": null,
  "last_completed_increment": "2.4",
  "approval_token": null
}
```
