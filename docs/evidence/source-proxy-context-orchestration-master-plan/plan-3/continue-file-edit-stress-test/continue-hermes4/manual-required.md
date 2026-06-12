# Manual Required

- Lane: `continue-hermes4`
- Target model: `hermes4`
- Reason: Stress test run aborted during prompt 1. Hermes 4 via Ollama is very slow (~15–40+ min per prompt). Partial workspace artifacts exist (`index.html`, `README.md`) but prompts 2–3 were not completed.

## Steps

- Re-run only this lane when long Ollama inference time is acceptable.
- Command pattern: `cn --config <lane-config.yaml> --auto -p "<prompt>"` from `workspace/`.
