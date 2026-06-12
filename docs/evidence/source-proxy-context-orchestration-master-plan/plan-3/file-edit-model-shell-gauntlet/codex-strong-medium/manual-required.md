# Manual Required

- Lane: `codex-strong-medium`
- Execution shell + model: `codex + strong`
- Reason: Codex model and effort selection is not exposed as a safe headless file-edit lane in this environment.

## Steps
- Open a fresh disposable workspace.
- Select exact Codex model `strong` with effort `medium` if it exists.
- Send the three exact prompts sequentially with only the allowed safety wrapper.
- Copy the resulting lane workspace and transcripts into this lane folder.
