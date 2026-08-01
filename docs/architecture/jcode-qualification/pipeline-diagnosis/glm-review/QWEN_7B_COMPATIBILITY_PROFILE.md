# QWEN_7B_COMPATIBILITY_PROFILE.md

Profile for `qwen2.5-coder:7b` for Gate 2-J.9T section L. Do NOT encode
task-specific answers.

## Identity (proven)

- Registry ID: `qwen2.5-coder:7b`
- Digest: `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`
  (live `ollama list` confirmed in this review)
- Family: qwen2; parameter size 7.6B; quantization Q4_K_M

## Direct baseline (proven)

- Task R (read/grounding): PASS (58.9s)
- Task W (write/tool): PASS (53.6s)

Raw grounding and tiny write capability are proven. Earlier hallucination/
no-edit outcomes do NOT establish incapability.

## Observed tool dialect

Bare or fenced assistant-text JSON calls, NOT native Ollama/OpenAI
`tool_calls`. Lane B evidence (`s1-r-b-7b`): `message.tool_calls: None`,
content `{"name": "read_file", "arguments": {"path": "ledger.py"}}`,
`tool_call_count: 0`.

## Required parser / recovery

Retain native support AND add exact bare/fenced JSON recovery for declared
tools only. Validate schema and path before execution. Preserve prior messages;
return the exact tool result; allow no task/context change and no more than
three total turns.

## Profile parameters

- system prompt: sealed task contract (no commit/self-modify defaults);
- preferred tool dialect: strict textual JSON envelope (native also accepted);
- parser mode: native + strict textual;
- temperature: 0 (observed);
- output budget: >=1024 tokens reserve;
- context limit: per model (7.6B Q4_K_M);
- maximum turns: 3;
- recovery prompt: tool-availability reminder (no answer reveal);
- known limitations: latency modest (no timeouts observed); text-dialect only;
- qualified task classes: read-only direct (proven); tool-mediated pending;
- disqualified task classes: none proven.

## Current outcome

`MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS` (not incapable). Read-only direct
capability proven; tool-mediated qualification requires sub-gate 2-J.9T-F/2-J.9T-G.
