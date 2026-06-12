# Manual Required

- Lane: `continue-gemma`
- Target model: `gemma`
- Reason: Ollama model `gemma` is not installed and Continue has no gemma entry in ~/.continue/config.yaml.

## Steps
- Install a Gemma model in Ollama only after Britton approves the download.
- Add a gemma model block to a disposable Continue config or hub slug.
- Re-run `python3 scripts/agent-trials/run-continue-file-edit-stress-test.py --run`.
