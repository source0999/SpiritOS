# Lane Plumbing Diagnosis

## Findings

- Raw Qwen appeared strong because its transcript included usable HTML. Under the stricter rule, free-floating HTML is not enough; only a path plus content block or a model action can be executed.
- Continue plus Qwen did use Qwen. Round 1 recorded `qwen2.5-coder:7b` as the observed model.
- Continue plus Qwen emitted 2 parseable model action(s) in the inspected transcript: Bash, MultiEdit.
- The old bridge missed valid output when Continue printed more than one JSON action. It tried to parse the whole transcript as one object, so multiple line-delimited actions became `NO_TOOL_CALL`.
- One Continue action used a string as Bash arguments. The adapter must normalize that to a command only when the tool name is `Bash`.
- Source Proxy was advisory-only because the planner returned `FallthroughToLLM(reason='no_explicit_target')`. The messy prompt intentionally has no target file, so the planner never reached a file-edit contract.
- The missing adapter is a workspace-only executor that accepts model-authored Write/Edit/MultiEdit/Bash calls or explicit path plus content blocks, then writes only inside the disposable workspace.
- The smallest honest fix is shared action parsing plus path-contained execution for Continue output, and a Source Proxy Qwen bridge mode that calls the selected model and sends only its model-authored actions or path/content blocks to the same adapter.

## Answers

- Why raw Qwen got a preview: free HTML was extracted into `lanes/raw-ollama-qwen/parsed-preview/index.html` by the previous harness.
- Did Continue emit tool calls: yes.
- Did Continue only chat: no.
- Did model selection use Qwen: yes.
- Did the bridge reject a valid action: yes, multiple JSON actions and string Bash arguments were not handled.
- Why Source Proxy was advisory-only: no explicit target caused planner fallthrough.
- Exact missing adapter: selected-model output to workspace action executor.
- Smallest honest fix: parse model actions, enforce containment, execute in disposable workspace, preserve transcript/diff/events.
