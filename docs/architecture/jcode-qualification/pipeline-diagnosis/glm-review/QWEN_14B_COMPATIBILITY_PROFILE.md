# QWEN_14B_COMPATIBILITY_PROFILE.md

Profile for `qwen2.5-coder:14b` for Gate 2-J.9T section L. Do NOT encode
task-specific answers.

## Identity (proven)

- Registry ID: `qwen2.5-coder:14b`
- Digest: `9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849`
  (live `ollama list` confirmed in this review)
- Family: qwen2; parameter size 14.8B; quantization Q4_K_M

## Direct baseline (proven)

- Task R (read/grounding): PASS (125.8s)
- Task W (write/tool): model output is behaviorally correct; this review ran
  the model's `re.sub(r'\s+', '-', value.strip()).lower()` against the actual
  `focused_check.py` — BOTH assertions PASS. The diagnostic AST evaluator
  rejected it (`inline_patch_capability_fail`) on import/assignment nodes.
  Formal direct-baseline close requires evaluator alignment (2-J.9T-E).

Raw grounding proven; write capability is behaviorally present pending
evaluator alignment.

## Observed tool dialect

Assistant-text JSON calls, NOT native `tool_calls`. Same pattern as 7B.

## Required parser / recovery

Same as 7B, PLUS a qualified latency/context budget. Four cells (D14, E14,
F14, plus one) reached the 300-second timeout. A provider timeout MUST NOT be
labeled model incapability.

## Profile parameters

- system prompt: sealed task contract;
- preferred tool dialect: strict textual JSON envelope (native also accepted);
- parser mode: native + strict textual;
- temperature: 0 (observed);
- output budget: >=1024 tokens reserve;
- context limit: per model (14.8B Q4_K_M);
- maximum turns: 3;
- recovery prompt: tool-availability reminder (no answer reveal);
- known limitations: materially higher latency; context/timeouts on full packets
  (E14 rendered 15,490-char model prompt);
- qualified task classes: read-only direct (proven); write direct
  (behaviorally proven, evaluator-aligned pending);
- disqualified task classes: none proven.

## Current outcome

`MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS` (incapability NOT proven). Requires
sub-gate 2-J.9T-F/2-J.9T-G plus evaluator alignment (2-J.9T-E) and a qualified
latency/context budget.
