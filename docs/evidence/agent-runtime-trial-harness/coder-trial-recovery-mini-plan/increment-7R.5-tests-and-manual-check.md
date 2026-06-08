# Increment 7R.5 - Tests And Manual Check

Date: 2026-06-08

## Checks Run

Passed:

```text
python -m py_compile source_proxy/tasks/long_running.py source_proxy/api/decision.py source_proxy/tests/test_coding_regression_pack.py
npx --no-install tsc --noEmit --pretty false
git diff --check
python -m unittest source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_dummy_product_site_create_mode_accepts_model_authored_bundle source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_dummy_product_site_create_mode_rejects_outside_root source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_coder_001_uses_create_mode_not_readme_replacement source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_calculator_create_blocks_fallback_after_invalid_model_tsx_in_live_trial
```

Backend focused test result:

```text
Ran 4 tests
OK
```

Still blocked:

```text
npx --no-install vitest run src/lib/coding/__tests__/dummy-coder-10-prompts.test.ts src/lib/coding/__tests__/dummy-coder-10-grader.test.ts src/lib/coding/__tests__/dummy-project-summary.test.ts src/components/coding/__tests__/coding-cockpit-shell.test.tsx --reporter=dot
```

Vitest failed before importing tests:

```text
Error: Cannot find module 'Z:\@id\Z:\node_modules\vitest\dist\index.js' imported from Z:\node_modules\vitest\dist\module-evaluator.js
Test Files 4 failed
Tests no tests
```

This is the same `Z:\@id\...` blocker recorded in Gate 7. Tests were not claimed passed.

## Manual Browser Check

Existing server:

```text
0.0.0.0:3000 owned by node.exe
```

In-app Browser attempt:

```text
http://127.0.0.1:3000/coding
net::ERR_BLOCKED_BY_CLIENT
```

Command-line request:

```text
Invoke-WebRequest http://127.0.0.1:3000/coding
401 Unauthorized
```

Manual browser verification could not be completed through automation because the in-app browser is blocked and unauthenticated command-line access is 401. No auth bypass was added.

## LumaCart

Checked after implementation:

```text
Test-Path tests/ui-agent-trials/fixtures/dummy-product-site
False
```

No Coder 001 manual run was performed in the browser because `/coding` could not be reached through the available automation surface.

## Acceptance Status

Verified by source/tests:

- UI is compact in source and tests.
- Individual prompt controls are merged into Trial Runner.
- Prompt details are collapsed by default in tests.
- Run button has immediate pending/running state in tests.
- Reverse/clear clears selected-prompt state in tests.
- Coder 001 create-mode validation is fixed in backend focused tests.

Not manually browser-verified because of the browser/auth blockers above.

## Live Source Proxy Retest After Mobile Blocker

Britton reported another blocked selected prompt:

```text
task_bec70802f121
run_status: blocked
grader_reason: missing_model_authored_proof
```

SQLite showed the cloud-facing task was still hitting the old path:

```text
reason_code=target_missing
target=tests/ui-agent-trials/fixtures/dummy-product-site/README.md
```

The live Source Proxy route was tested directly on `127.0.0.1:8787` with the Coder 001 payload. After the create-mode/cloud-alias/apply-gate fixes:

```text
prompt_packet: preview_ready
reason_code: dummy_product_site_create_bundle
provider: openai
model: gpt-4o-mini
provider_call_made: true
changed_files:
- tests/ui-agent-trials/fixtures/dummy-product-site/README.md
- tests/ui-agent-trials/fixtures/dummy-product-site/package.json
- tests/ui-agent-trials/fixtures/dummy-product-site/index.html
- tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js
- tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js
- tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css
```

Full live route check:

```text
before_exists False
create_task task_5c48c83c09e2
prompt_packet preview_ready dummy_product_site_create_bundle openai gpt-4o-mini True
diff_preview preview_ready high []
apply applied_needs_verification
after_apply_exists True
after_apply files: README.md, index.html, package.json, src/main.js, src/products.js, src/styles.css
reverse applied_needs_verification
after_reverse_exists False
remaining []
```

The apply used the model-authored Coder 001 diff. The reverse used the same Source Proxy `execute-approved` path with a bounded delete diff for the model-created dummy-root files. No manual LumaCart scaffold was created.

Final focused checks:

```text
python -m unittest source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_coder_001_create_bundle_task_spec_preview_allows_dummy_root_wildcard source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_coder_001_create_bundle_task_spec_still_rejects_root_package source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_coder_001_create_mode_can_use_cloud_alias source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_coder_001_uses_create_mode_not_readme_replacement source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_dummy_product_site_create_mode_accepts_model_authored_bundle source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_dummy_product_site_create_mode_rejects_outside_root

Ran 6 tests
OK

npx --no-install tsc --noEmit --pretty false
passed

git diff --check
passed with CRLF warnings only
```

## Follow-Up After `task_9235678820d7`

Britton reported another blocked cloud/mobile selected prompt:

```text
task_9235678820d7
run_status: blocked
grader_reason: missing_model_authored_proof
```

The durable task database on this workspace recorded the actual backend blocker:

```text
status=blocked
reason_code=target_missing
target=tests/ui-agent-trials/fixtures/dummy-product-site/README.md
needed_context=Create the missing file or fix the path spelling, then retry.
```

Direct Coder 001 prompt-packet checks were run without running Coder 002-010 or a full Coder 10 benchmark.

Local patched Source Proxy:

```text
POST http://127.0.0.1:8787/v1/decisions/prompt-packet
status=preview_ready
reason_code=dummy_product_site_create_bundle
target=tests/ui-agent-trials/fixtures/dummy-product-site/
provider/model=openai/gpt-4o-mini
provider_call_made=true
task_spec.task_type=create_file_bundle
task_spec.allowed_files=tests/ui-agent-trials/fixtures/dummy-product-site/**
proposed_diff contains LumaCart and src/products.js
```

Cloud/mobile Source Proxy:

```text
POST https://100.111.32.31:8787/v1/decisions/prompt-packet
status=blocked
reason_code=target_missing
target=tests/ui-agent-trials/fixtures/dummy-product-site/README.md
provider/model=local/ollama_chat/qwen2.5-coder:7b
provider_call_made=false
task_spec.task_type=create_new_file
task_spec.allowed_files=tests/ui-agent-trials/fixtures/dummy-product-site/README.md
```

Cloud/mobile Next proxy:

```text
POST https://100.111.32.31:3000/v1/decisions/prompt-packet
status=blocked
reason_code=target_missing
target=tests/ui-agent-trials/fixtures/dummy-product-site/README.md
provider/model=local/ollama_chat/qwen2.5-coder:7b
provider_call_made=false
task_spec.task_type=create_new_file
task_spec.allowed_files=tests/ui-agent-trials/fixtures/dummy-product-site/README.md
```

Cloud reachability:

```text
100.111.32.31:3000 reachable
100.111.32.31:8787 reachable
100.111.32.31:22 reachable but SSH denied: Permission denied (publickey,password).
```

The cloud runtime still serves the old single-file target-missing path. The available remote Source Proxy APIs expose read-only workspace and sandbox inspection, but no supported restart/reload endpoint. The cloud/mobile path is therefore **not verified fixed** until the Source Proxy process serving `100.111.32.31` is restarted/redeployed with the patched create-mode code.

Additional focused checks after restoring the visible run-all button:

```text
python -m unittest source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_coder_001_create_bundle_task_spec_preview_allows_dummy_root_wildcard source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_coder_001_create_bundle_task_spec_still_rejects_root_package source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_coder_001_create_mode_can_use_cloud_alias source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_coder_001_uses_create_mode_not_readme_replacement source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_dummy_product_site_create_mode_accepts_model_authored_bundle source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_dummy_product_site_create_mode_rejects_outside_root

Ran 6 tests
OK

npx --no-install tsc --noEmit --pretty false
passed

git diff --check
passed with CRLF warnings only
```

Frontend focused Vitest still failed before importing tests:

```text
npx --no-install vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx src/lib/coding/__tests__/dummy-coder-10-prompts.test.ts src/lib/coding/__tests__/dummy-coder-10-grader.test.ts src/lib/coding/__tests__/reversible-trial-runner.test.ts --reporter=dot

Error: Cannot find module 'Z:\@id\Z:\node_modules\vitest\dist\index.js' imported from Z:\node_modules\vitest\dist\module-evaluator.js
Test Files 4 failed
Tests no tests
```

LumaCart remains absent after the preview-only checks:

```text
Test-Path tests/ui-agent-trials/fixtures/dummy-product-site
False
```
