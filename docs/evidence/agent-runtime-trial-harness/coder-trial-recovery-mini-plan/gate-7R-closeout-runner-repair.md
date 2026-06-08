# Gate 7R Closeout - Runner Repair

Date: 2026-06-08

## Files Changed

Gate 7R edited:

- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`
- `source_proxy/api/decision.py`
- `source_proxy/tasks/long_running.py`
- `source_proxy/tests/test_coding_regression_pack.py`
- this Gate 7R evidence set

The working tree already contained Gate 5/6/7 and unrelated dirty files. They were preserved.

## UI Result

Separate LumaCart panel removed:

```text
Yes
```

Individual controls merged into Trial Runner:

```text
Yes
```

Long text collapsed by default:

```text
Yes - View prompt + boundaries
```

Run button shows immediate state:

```text
Yes - Starting selected prompt, Request sent, Running task <id>, Needs fix, Applied / review, Failed, Cleared
```

Reverse/clear clears selected-prompt result:

```text
Yes
```

Follow-up after mobile review:

```text
Selected-prompt result now renders as a compact trial-style preview row in Trial Runner, with the same Reverse trial edits and clear results button directly below it.
```

## Coder 001 Create Mode

Create-mode validation fixed:

```text
Yes
```

Coder 001 is no longer forced through single-file README replacement validation. It now accepts a model-authored multi-file `create_file_bundle` under:

```text
tests/ui-agent-trials/fixtures/dummy-product-site/
```

It rejects outside-root, root package, Source Proxy, app/component/lib, docs, and env paths.

Follow-up task `task_6e993f1a708c` showed a separate pre-create-mode blocker:

```text
reason_code=target_missing
target=tests/ui-agent-trials/fixtures/dummy-product-site/README.md
```

The allowed-root wildcard check for `tests/ui-agent-trials/fixtures/dummy-product-site/**` was patched so this target is accepted as an allowed create target and can reach Coder 001 create-mode.

## LumaCart Creation

LumaCart was created during the final live Source Proxy check by the Coder 001 model-authored diff, then reversed through the same `execute-approved` authority path.

Live route result:

```text
prompt_packet: preview_ready
reason_code: dummy_product_site_create_bundle
provider/model: openai/gpt-4o-mini
provider_call_made: true
diff_preview: preview_ready
apply: applied_needs_verification
reverse: applied_needs_verification
```

Created files during apply:

```text
tests/ui-agent-trials/fixtures/dummy-product-site/README.md
tests/ui-agent-trials/fixtures/dummy-product-site/package.json
tests/ui-agent-trials/fixtures/dummy-product-site/index.html
tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js
tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js
tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css
```

Final check:

```text
Test-Path tests/ui-agent-trials/fixtures/dummy-product-site
False
```

The dummy root was absent again after reverse. No manual LumaCart scaffold was created.

## Checks

Passed:

```text
python -m py_compile source_proxy/tasks/long_running.py source_proxy/api/decision.py source_proxy/tests/test_coding_regression_pack.py
npx --no-install tsc --noEmit --pretty false
git diff --check
python -m unittest source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_dummy_product_site_create_mode_accepts_model_authored_bundle source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_dummy_product_site_create_mode_rejects_outside_root source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_coder_001_uses_create_mode_not_readme_replacement source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_calculator_create_blocks_fallback_after_invalid_model_tsx_in_live_trial
python -m unittest source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_coder_001_create_bundle_task_spec_preview_allows_dummy_root_wildcard source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_coder_001_create_bundle_task_spec_still_rejects_root_package source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_coder_001_create_mode_can_use_cloud_alias source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_coder_001_uses_create_mode_not_readme_replacement source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_dummy_product_site_create_mode_accepts_model_authored_bundle source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_dummy_product_site_create_mode_rejects_outside_root
```

Blocked:

```text
npx --no-install vitest run src/lib/coding/__tests__/dummy-coder-10-prompts.test.ts src/lib/coding/__tests__/dummy-coder-10-grader.test.ts src/lib/coding/__tests__/dummy-project-summary.test.ts src/components/coding/__tests__/coding-cockpit-shell.test.tsx --reporter=dot

Error: Cannot find module 'Z:\@id\Z:\node_modules\vitest\dist\index.js' imported from Z:\node_modules\vitest\dist\module-evaluator.js
```

Manual browser blocked:

```text
Browser: net::ERR_BLOCKED_BY_CLIENT
Command line: 401 Unauthorized
```

## Recommendation

```text
NO-GO for cloud/mobile retry until the Source Proxy process serving 100.111.32.31 is restarted/redeployed with the patched create-mode code.
```

Local patched Source Proxy is eligible for a selected-prompt-only Coder 001 retry. The cloud/mobile endpoint is not: direct checks against `https://100.111.32.31:8787/v1/decisions/prompt-packet` and `https://100.111.32.31:3000/v1/decisions/prompt-packet` still return `reason_code=target_missing` for `tests/ui-agent-trials/fixtures/dummy-product-site/README.md` and `provider_call_made=false`.

Do not run Coder 002-010 or full Coder 10 until Coder 001 is inspected honestly through the cloud/mobile Trial Runner UI after that process restart/redeploy.

Hard stop honored after Gate 7R closeout. No next gate started.

## Follow-Up: Cloud Block And Run-All Button

Britton reported:

```text
task_9235678820d7
blocked
missing_model_authored_proof
Run all trials button missing
```

UI patch:

```text
Run all trials button restored inside the compact Individual prompt Trial Runner view.
No separate LumaCart panel reintroduced.
No benchmark auto-runs on selection.
```

Local patched Source Proxy check:

```text
POST http://127.0.0.1:8787/v1/decisions/prompt-packet
status=preview_ready
reason_code=dummy_product_site_create_bundle
target=tests/ui-agent-trials/fixtures/dummy-product-site/
provider/model=openai/gpt-4o-mini
provider_call_made=true
task_spec.task_type=create_file_bundle
```

Cloud/mobile checks:

```text
POST https://100.111.32.31:8787/v1/decisions/prompt-packet
status=blocked
reason_code=target_missing
target=tests/ui-agent-trials/fixtures/dummy-product-site/README.md
provider/model=local/ollama_chat/qwen2.5-coder:7b
provider_call_made=false

POST https://100.111.32.31:3000/v1/decisions/prompt-packet
status=blocked
reason_code=target_missing
target=tests/ui-agent-trials/fixtures/dummy-product-site/README.md
provider/model=local/ollama_chat/qwen2.5-coder:7b
provider_call_made=false
```

Cloud access blocker:

```text
SSH to 100.111.32.31 is reachable but denied: Permission denied (publickey,password).
Remote Source Proxy exposes read-only workspace/sandbox inspection but no supported restart/reload endpoint.
```

Updated checks:

```text
python -m unittest source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_coder_001_create_bundle_task_spec_preview_allows_dummy_root_wildcard source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_coder_001_create_bundle_task_spec_still_rejects_root_package source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_coder_001_create_mode_can_use_cloud_alias source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_coder_001_uses_create_mode_not_readme_replacement source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_dummy_product_site_create_mode_accepts_model_authored_bundle source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_dummy_product_site_create_mode_rejects_outside_root
Ran 6 tests
OK

npx --no-install tsc --noEmit --pretty false
passed

git diff --check
passed with CRLF warnings only
```

Vitest remains blocked before importing tests:

```text
Error: Cannot find module 'Z:\@id\Z:\node_modules\vitest\dist\index.js' imported from Z:\node_modules\vitest\dist\module-evaluator.js
```

## Follow-Up: Local Ollama Prompt 001 NO-GO

Britton clarified that Coder 001 must prove the local AI coder path. OpenAI/Anthropic/DeepSeek do not count as Prompt 001 local proof.

Local route setup checked:

```text
Ollama reachable: http://127.0.0.1:11434/api/tags
Available allowed model: qwen2.5-coder:7b
Hermes route: not enabled because hermes4:latest is not installed
SOURCE_PROXY_CODER_MODEL_ALIAS=coder
SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2.5-coder:7b
Source Proxy coder route: enabled
provider/model: local / ollama_chat/qwen2.5-coder:7b
route type: local Ollama
```

Strict Prompt 001 local run:

```text
POST /v1/decisions/prompt-packet
status=blocked
reason_code=coder_file_bundle_validation_failed
provider/model=local / ollama_chat/qwen2.5-coder:7b
SOURCE_PROXY_CODER_MODEL_ALIAS=coder
provider_call_made=true
generation_source=model
diff_source=pending_backend_diff_from_model_file_bundle
trial_result_trust_status=model_output_not_usable
scaffold_used=false
fallback_used=false
generated_diff_by_backend=false
repair_attempted=true
changed_files=none
```

Blocker:

```text
Qwen returned model-authored create_file_bundle JSON, but the JSON was malformed after the repair retry.
Final parse error: Expecting value: line 10 column 50 (char 312)
No diff preview was run.
No apply was run.
No LumaCart files were created.
No cloud/API fallback was used.
```

Checks after local-route repair patch:

```text
python -m unittest source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_dummy_product_site_create_mode_repairs_invalid_local_json_with_model_retry source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_coder_001_uses_create_mode_not_readme_replacement source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_dummy_product_site_create_mode_accepts_model_authored_bundle
Ran 3 tests
OK

npx --no-install tsc --noEmit --pretty false
passed

git diff --check
passed with CRLF warnings only
```

Updated recommendation:

```text
NO-GO retry from UI until local Qwen/Hermes can return a valid create_file_bundle JSON packet. Do not use OpenAI, Anthropic, or DeepSeek as Prompt 001 proof.
```
