# Manual Required

- Lane: `continue-qwen`
- Execution shell + model: `continue + qwen2.5-coder:7b`
- Reason: Continue CLI `cn` is not on PATH.

## Steps
- Configure Continue CLI to select exact model `qwen2.5-coder:7b` explicitly.
- Confirm write tools are enabled in a disposable workspace.
- Run the three prompts sequentially with only the allowed safety wrapper.
- Record the exact Continue command and whether file writes occurred.
