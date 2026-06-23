# Plan 3 Debugger Diagnostic Standard - 2026-06-23

Good Plan 3 debugger output must let Britton tell what failed, where it failed, which lane made the decision, why the final status changed, and the next bounded action without manually digging across unrelated files.

## Required Fields

- `run_id`
- `prompt_id` or `task_id`
- task class / route type
- expected lane
- candidate lanes
- selected lane
- selected model/provider/tool
- local/api/cli distinction
- provider availability
- model call attempted true/false
- model call result or failure class
- timeout vs empty output vs parse failure vs policy block
- fallback used true/false
- fallback reason
- degraded lanes
- productive_status
- productive reasons
- verification_real flags
- browser/functional verifier result
- created/modified files
- protected path block result
- failure_classification
- anti-cheat flags
- receipt path
- trace path
- public/private redaction status
- human action required true/false
- next recommended action

## Adequacy Rule

A Plan 3 failure is not acceptable if the receipt or trace forces Britton to manually inspect five separate places to learn why it failed. The failure must state the prompt/task, lane, provider/model/tool, model-call status, validation failure, productive-output status, verifier status, protected-path result, receipt/trace paths, and next bounded fix.

Do not add diagnostic fields only for noise. Add or repair fields only where the run lacks enough proof to debug the failure honestly.
