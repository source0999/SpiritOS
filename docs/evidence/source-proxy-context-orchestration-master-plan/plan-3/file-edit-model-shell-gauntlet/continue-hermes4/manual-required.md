# Manual Required

- Lane: `continue-hermes4`
- Execution shell + model: `continue + hermes4:latest`
- Reason: Continue CLI `cn` is not on PATH.

## Steps
- Configure Continue CLI to select exact model `hermes4:latest` explicitly.
- Confirm write tools are enabled in a disposable workspace.
- Run the three prompts sequentially with only the allowed safety wrapper.
- Record the exact Continue command and whether file writes occurred.
