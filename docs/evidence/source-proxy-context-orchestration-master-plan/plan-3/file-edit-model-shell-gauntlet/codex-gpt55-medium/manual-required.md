# Manual Required

- Lane: `codex-gpt55-medium`
- Execution shell + model: `codex + gpt-5.5`
- Reason: Codex model and effort selection is not exposed as a safe headless file-edit lane in this environment.

## Steps
- Open a fresh disposable workspace.
- Select exact Codex model `gpt-5.5` with effort `medium` if it exists.
- Send the three exact prompts sequentially with only the allowed safety wrapper.
- Copy the resulting lane workspace and transcripts into this lane folder.
