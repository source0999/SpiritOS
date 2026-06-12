# Source Proxy Orchestrator Correction Phase 2 Product Verification Summary

## Status

Local/mocked verification executed on `source-server`.

No provider/model calls were run. No benchmark prompts were run. No runtime files or tests were changed for this phase. No real app files were mutated from trial prompts. No git branch, worktree, stash, reset, checkout, clean, stage, commit, or push was performed.

## Python And Test Setup

Host:

```text
source-server
```

Repo:

```text
/home/source/SpiritOS
```

Python:

```text
/home/source/SpiritOS/.venv/bin/python
```

Pytest:

```text
pytest-8.4.2
```

## Commands Run

```bash
source .venv/bin/activate
command -v python
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "task_spec_intake or tool_action or human_messy_homepage or messy_homepage or pure or artifact or protected or fake"
```

Result:

```text
/home/source/SpiritOS/.venv/bin/python
35 passed, 69 deselected in 12.82s
```

```bash
source .venv/bin/activate
command -v python
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "protected or fake or wrong_file or backend_authored or tool_action"
```

Result:

```text
/home/source/SpiritOS/.venv/bin/python
26 passed, 78 deselected in 10.09s
```

```bash
source .venv/bin/activate
python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --help
```

Result:

```text
usage: run-source-proxy-human-messy-homepage-smoke.py [-h] [--run] [--serve]
                                                      [--host HOST]
                                                      [--port PORT]
                                                      [--prompt PROMPT]
                                                      [--model-id MODEL_ID]
                                                      [--mode {product,pure}]
```

Smoke decision:

* The script exposes `--run`, `--serve`, and `--mode`, but no mocked fixture/model-call option.
* No smoke `--run` was executed because that could call a provider/local model.

## Local Mocked Receipt Samples

Created local mocked samples with injected `model_call` lambdas:

* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/product-homepage-receipt.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/product-homepage-score.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/pure-homepage-receipt.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/pure-homepage-score.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/markdown-artifact-receipt.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/markdown-artifact-score.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-blocked-case-receipts/json-wrong-extension-receipt.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-blocked-case-receipts/json-wrong-extension-score.json`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-local-mocked-summary.json`

## Findings

Product homepage:

* `route_type = product`
* `task_shape = disposable_single_file_artifact`
* `task_shape_source = generic_artifact_resolver`
* `proxy_artifact_class_suggested = html_static_page`
* `proxy_exact_target_suggested = ""`
* `allowed_scope_source = artifact_class_extensions`
* `model_authored_targets = ["index.html"]`
* `files_touched = ["index.html"]`
* score `status = GO`
* `benchmark_eligible = false`
* `backend_created_content = false`
* `real_app_touched = false`

Pure homepage:

* `route_type = pure_diagnostic`
* no Product artifact class
* no proxy exact target
* `model_authored_targets = ["site/home.html"]`
* `files_touched = ["site/home.html"]`
* score `status = GO`
* `benchmark_eligible = true`
* `product_helper_used = false`
* `system_preselected_target = false`

Markdown artifact:

* `route_type = product`
* `task_shape = disposable_single_file_artifact`
* `task_shape_source = generic_artifact_resolver`
* `proxy_artifact_class_suggested = markdown_document`
* `proxy_exact_target_suggested = ""`
* `model_authored_targets = ["release-checklist.md"]`
* `files_touched = ["release-checklist.md"]`
* receipt `final_state = completed`
* `backend_created_content = false`
* `real_app_touched = false`

Important scoring note:

* The Markdown receipt proves generic Product orchestration and model-authored execution.
* The legacy `human_messy_homepage` score still reports `status = NO-GO` for Markdown because that scorer requires an openable homepage.
* Treat that as a verification/scoring limitation, not as a runtime executor failure.

JSON wrong-extension trap:

* `route_type = product`
* `task_shape = disposable_single_file_artifact`
* `proxy_artifact_class_suggested = json_example`
* model attempted `config.txt`
* `final_state = blocked`
* `error_code = target_not_allowed`
* `files_touched = []`
* `real_app_touched = false`

## Phase 2 Local/Mocked Decision

GO:

* Product mode is locally verified as an orchestrated route for homepage and non-homepage artifact receipts.
* Pure mode remains diagnostic and receipt-distinct.
* Wrong extension is blocked.
* Protected/fake/wrong-file no-cheat regression slice passed.
* No provider/model calls were used.

NO-GO:

* Live provider/model verification remains blocked until a later explicit approval.
* Benchmark verification remains blocked until a later explicit approval.
* Generic non-homepage product score labels should not be treated as final Product success labels until scoring is generalized or evidence uses receipt-level success explicitly.
