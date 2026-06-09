# Plan 1 Phase 1.2 - Malformed Block Rejection

Status: GO

## Diagnostics Covered

The parser now rejects and surfaces these required diagnostics:

- `markdown_fence_found`
- `unclosed_file_tag`
- `no_file_block`
- `malformed_file_block`
- `empty_diff`
- `unsafe_path`
- `out-of-scope file`

## Increment Evidence

1.2.1 markdown fence found:

- Test: `test_markdown_fenced_output_is_rejected`
- Result: rejects fenced XML/JSON before recovery.

1.2.2 unclosed file tag:

- Test: `test_unclosed_file_tag_is_rejected`
- Result: rejects `<file ...>` without `</file>`.

1.2.3 no file block:

- Test: `test_no_file_block_prose_is_rejected`
- Result: prose-only messy output blocks after one repair pass.

1.2.4 malformed file block:

- Test: `test_malformed_file_block_is_rejected`
- Result: delimiter block missing closing `>>>` is rejected.

1.2.5 empty diff:

- Test: `test_empty_file_block_content_is_rejected_as_empty_diff`
- Result: empty replacement payload is rejected before diff preview.

1.2.6 unsafe path:

- Test: `test_unsafe_file_block_path_is_rejected`
- Result: traversal path `../.env` is rejected as `unsafe_path`.

1.2.7 out-of-scope file:

- Test: `test_json_with_wrong_target_returns_out_of_scope_file`
- Result: parsed replacement target outside the packet target returns `coder_out_of_scope_file` with `out-of-scope file` diagnostic.

## Checks

Command:

`cd ~/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coder_agent_repomix_diff.py`

Result:

`56 passed in 9.46s`

Command:

`cd ~/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_ollama_route.py source_proxy/tests/test_coder_agent_repomix_diff.py`

Result:

`70 passed in 9.74s`

## Phase Closeout

Phase 1.2 GO. Every required malformed-output diagnostic has a targeted negative test. No malformed output silently continues to diff preview.

