# Increment 7R.4 - Coder 001 Create-Mode Validation

Date: 2026-06-08

## Changes

Updated:

- `source_proxy/api/decision.py`
- `source_proxy/tasks/long_running.py`
- `source_proxy/tests/test_coding_regression_pack.py`

## Request Metadata

`PromptPacketRequest` now accepts the Gate 5/6 selected-prompt metadata:

- `dummy_coder_10_packet`
- `expected_result_state`
- `primary_expected_targets`
- `forbidden_files`
- `selected_prompt_id`
- `trial_prompt_id`

Coder 001 create mode is selected when:

```text
selected_prompt_id == coder-001-init-dummy-product-site
or expected_result_state == PASS_DUMMY_PROJECT_INIT
or dummy_coder_10_packet.expected_result_state == PASS_DUMMY_PROJECT_INIT
```

## Create-Mode Behavior

Coder 001 now uses a narrow create-mode branch:

```text
propose_dummy_product_site_create_diff
```

The model is asked for JSON:

```text
action: create_file_bundle
files[].path
files[].content_lines
```

Expected root:

```text
tests/ui-agent-trials/fixtures/dummy-product-site/
```

Required starter files:

- `README.md`
- `package.json`
- `index.html`
- `src/main.js`
- `src/products.js`
- `src/styles.css`

Validation accepts new files under the dummy root without requiring exact old text. It rejects:

- any path outside the dummy root
- root package mutation
- Source Proxy paths
- app/component/lib production paths
- docs paths
- env paths

The branch is model-authored only. It does not use scaffold or fallback content as a pass path.

## Route Result

When valid, the backend returns:

```text
reason_code: dummy_product_site_create_bundle
target: tests/ui-agent-trials/fixtures/dummy-product-site/
task_spec.allowed_files: tests/ui-agent-trials/fixtures/dummy-product-site/**
```

This replaces the old README replacement validation failure:

```text
coder_replacement_content_validation_failed
missing exact text: tests/ui-agent-trials/fixtures/dummy-product-site/
```

## Tests

Focused backend tests cover:

- create-mode accepts new dummy-root file bundle
- create-mode rejects outside-root/root package files
- prompt-packet Coder 001 route uses create mode, not README replacement
- normal single-target replacement validation still blocks invalid Agent Lab create content

`tests/ui-agent-trials/fixtures/dummy-product-site/` remains absent until a real selected-prompt model run is triggered and applied.

## Follow-Up: task_6e993f1a708c

Mobile diagnostics showed:

```text
selected_prompt_task_id: task_6e993f1a708c
run_status: blocked
raw_backend_status: blocked
changed_files: none
grader_reason: Result is not PASS-compatible: missing_model_authored_proof.
```

The persisted task record in `data/long_running_tasks.sqlite3` showed the backend stopped earlier than create-mode:

```text
reason_code=target_missing
target=tests/ui-agent-trials/fixtures/dummy-product-site/README.md
needed_context=Create the missing file or fix the path spelling, then retry.
```

Root cause:

```text
_trial_path_allowed treated tests/ui-agent-trials/fixtures/dummy-product-site/** as tests/ui-agent-trials/fixtures/dummy-product-site//...
```

The wildcard allowed-root check now accepts targets that start with the normalized root prefix from `/**`, so Coder 001 can reach the create-mode branch instead of stopping at `target_missing`.
