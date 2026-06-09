# Plan 1 Corrective - Output Contract Usability

Status: GO

## Why This Corrective Pass Exists

The first Plan 1 pass was too narrow. It rejected markdown fences instead of recovering from the common local-model behavior where a valid file block is wrapped in an outer markdown fence.

This corrective pass makes the output contract more usable inside Source Proxy while preserving fail-closed behavior for malformed output.

## Increment C1.1 - Strip outer markdown fences

Change:

- Added `_strip_outer_markdown_fence_for_contract`.
- The parser now strips a single outer markdown fence around XML file blocks, delimiter blocks, or legacy JSON.
- The parser records diagnostics:
  - `markdown_fence_found`
  - `markdown_fence_stripped`
  - `markdown_fence_language`

Tests:

- `test_markdown_fenced_json_output_is_stripped_and_used`
- `test_markdown_fenced_xml_file_block_is_stripped_and_used`

Result:

- fenced JSON is parsed and converted to a backend diff
- fenced XML file block is parsed and converted to a backend diff
- diagnostics prove the fence was seen and stripped

Decision: GO.

## Increment C1.2 - Reject broken fence shapes

Change:

Malformed fence shapes still block:

- `markdown_fence_unclosed`
- `markdown_fence_trailing_content`
- `markdown_fence_nested`
- `markdown_fence_empty`

Test:

- `test_unclosed_markdown_fence_is_rejected_with_diagnostic`

Decision: GO.

## Increment C1.3 - Improve malformed file-block diagnostics

Existing malformed block diagnostics remain covered:

- `unclosed_file_tag`
- `malformed_file_block`
- `empty_diff`
- `unsafe_path`
- `out-of-scope file`

The parser distinguishes outer markdown fence repair from actual malformed file blocks.

Decision: GO.

## Increment C1.4 - Strengthen 7B prompt and run actual Source Proxy flow

Change:

The coder system prompt now explicitly says:

`Do not wrap the file block or JSON in markdown fences.`

Live 7B check:

Ran a messy Britton-style task through `propose_coder_agent_diff_payload_from_plan` with `ollama run qwen2.5-coder:7b`.

Result:

- blocked: `false`
- validation status: `preview_ready`
- structured output mode: `xml_file_block`
- markdown fence found: `false`
- markdown fence stripped: `false`
- JSON attempts: `1`
- repair attempts: `0`
- raw model output started with `<file path="src/app/demo/page.tsx">`

Decision: GO.

## Verification

Command:

`cd ~/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coder_agent_repomix_diff.py`

Result:

`58 passed in 9.92s`

Command:

`cd ~/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_ollama_route.py source_proxy/tests/test_coder_agent_repomix_diff.py source_proxy/tests/test_context_source_readiness.py source_proxy/tests/test_research_preview.py source_proxy/tests/test_scout_research_bridge.py source_proxy/tests/test_self_status.py`

Result:

`106 passed in 11.10s`

## Phase Closeout

Corrective Plan 1 GO. Source Proxy now recovers from outer markdown fences with visible diagnostics, still blocks malformed output, and the 7B route produced a clean raw XML file block in the actual coder-packet flow.
