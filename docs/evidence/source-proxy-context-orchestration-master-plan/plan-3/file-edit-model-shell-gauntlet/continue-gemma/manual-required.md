# Manual Required

- Lane: `continue-gemma`
- Execution shell + model: `continue + gemma`
- Reason: Continue CLI `cn` is not on PATH.

## Steps
- Configure Continue CLI to select exact model `gemma` explicitly.
- Confirm write tools are enabled in a disposable workspace.
- Run the three prompts sequentially with only the allowed safety wrapper.
- Record the exact Continue command and whether file writes occurred.
