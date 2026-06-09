# Plan 1 Phase 1.4 - Messy Prompt Model Contract Tests

Status: GO with 14B comparison blocked by unavailable model

## Increment 1.4.1 - Messy Britton-style prompt fixtures

Covered in focused parser tests with messy/prose cases:

- prose-only output: `hey make it shiny and fix the page thanks`
- markdown-fenced output
- missing closing file tag
- malformed delimiter block
- wrong target path
- unsafe traversal path

Result: parser rejects each unsafe or malformed shape with explicit diagnostics.

Decision: GO.

## Increment 1.4.2 - 7B baseline output-contract test

Command:

Inline Python on the Dell host ran `propose_coder_agent_diff_payload_from_plan` with a tiny `src/app/demo/page.tsx` CoderPacket and an `ollama run qwen2.5-coder:7b` LLM callback.

Result summary:

- model: `qwen2.5-coder:7b`
- status: `ok`
- target: `src/app/demo/page.tsx`
- diff length: `183`
- validation status: `preview_ready`
- structured output mode: `xml_file_block`
- file block repair source: `xml_file_block`
- parser repair used: `false`
- parser diagnostics: no parse error

Notes:

- A separate raw minimal prompt to `qwen2.5-coder:7b` returned a markdown-fenced XML block and was correctly rejected with `markdown_fence_found`.
- The real coder prompt path produced strict XML file-block output and passed preview validation.

Decision: GO for 7B baseline.

## Increment 1.4.3 - 14B comparison after parser stability

Parser stability gate passed first:

`70 passed in 9.74s`

Comparison status:

- `qwen2.5-coder:14b` is not installed according to `ollama list`.
- No pull, default switch, Coder 50, Coder 100, hidden worker, apply, commit, push, or continuation was run.
- Comparison is blocked by unavailable local model.

Decision: GO to record blocked comparison; no model route change.

## Increment 1.4.4 - 14B remains non-default

Result:

- `qwen2.5-coder:7b` remains the approved default coder route from Plan 0.
- `qwen2.5-coder:14b` remains comparison-only and did not pass the same contract because it is unavailable locally.

Decision: GO.

## Phase Closeout

Phase 1.4 GO. The 7B baseline passes the strict file-block contract through the real coder prompt path. 14B comparison was attempted only after parser stability and is recorded as blocked by missing local model, with no default switch.

