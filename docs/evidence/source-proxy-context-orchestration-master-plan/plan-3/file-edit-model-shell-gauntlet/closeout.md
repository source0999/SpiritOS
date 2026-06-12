# File Edit Model Shell Gauntlet Closeout

## Exact prompts
1. init a repo for agent lab experiements make me a homepage i can open on my phone dont touch the real spiritos app tho
2. style it light clean minimilist homepage with placeholder navs for futer expermients home calculator tarot deck simulator weather app pong
3. make the calcuator route for this app, calcuator needs to add subtract multiply and divide

## Lane statuses
- continue-qwen: continue + qwen2.5-coder:7b -> NOT_RUN_MANUAL_REQUIRED, score None/30
- terminal-qwen: terminal + qwen2.5-coder:7b -> NO-GO, score 12/30
- source-proxy-qwen: source-proxy + qwen2.5-coder:7b -> NO-GO, score 12/30
- terminal-hermes4: terminal + hermes4:latest -> NOT_RUN_MANUAL_REQUIRED, score None/30
- source-proxy-hermes4: source-proxy + hermes4:latest -> NOT_RUN_MANUAL_REQUIRED, score None/30
- raw-api-gpt4o-mini: raw-api + gpt-4o-mini -> NO-GO, score 12/30
- continue-hermes4: continue + hermes4:latest -> NOT_RUN_MANUAL_REQUIRED, score None/30
- continue-gemma: continue + gemma -> NOT_RUN_MANUAL_REQUIRED, score None/30
- continue-gpt4o-mini: continue + gpt-4o-mini -> NOT_RUN_MANUAL_REQUIRED, score None/30
- terminal-gemma: terminal + gemma -> NOT_RUN_MANUAL_REQUIRED, score None/30
- source-proxy-gemma: source-proxy + gemma -> NOT_RUN_MANUAL_REQUIRED, score None/30
- source-proxy-gpt4o-mini: source-proxy + gpt-4o-mini -> NO-GO, score 12/30
- source-proxy-strong-api: source-proxy + gpt-4o -> NO-GO, score 12/30
- codex-gpt55-low: codex + gpt-5.5 -> NOT_RUN_MANUAL_REQUIRED, score None/30
- codex-gpt55-medium: codex + gpt-5.5 -> NOT_RUN_MANUAL_REQUIRED, score None/30
- codex-gpt55-high: codex + gpt-5.5 -> NOT_RUN_MANUAL_REQUIRED, score None/30
- raw-api-strong-low: raw-api + gpt-4o -> NO-GO, score 12/30
- raw-api-strong-medium: raw-api + gpt-4o -> NO-GO, score 12/30
- raw-api-strong-high: raw-api + gpt-4o -> NO-GO, score 12/30
- raw-api-claude-low: raw-api + claude-3-5-haiku-latest -> NO-GO, score 12/30
- raw-api-claude-medium: raw-api + claude-3-5-sonnet-latest -> NO-GO, score 12/30
- raw-api-claude-high: raw-api + claude-3-7-sonnet-20250219 -> NO-GO, score 12/30
- codex-strong-low: codex + strong -> NOT_RUN_MANUAL_REQUIRED, score None/30
- codex-strong-medium: codex + strong -> NOT_RUN_MANUAL_REQUIRED, score None/30
- codex-strong-high: codex + strong -> NOT_RUN_MANUAL_REQUIRED, score None/30

## Prompt 3 calculator verification
- continue-qwen: not run
- terminal-qwen: explained_only
- source-proxy-qwen: explained_only
- terminal-hermes4: not run
- source-proxy-hermes4: not run
- raw-api-gpt4o-mini: explained_only
- continue-hermes4: not run
- continue-gemma: not run
- continue-gpt4o-mini: not run
- terminal-gemma: not run
- source-proxy-gemma: not run
- source-proxy-gpt4o-mini: explained_only
- source-proxy-strong-api: explained_only
- codex-gpt55-low: not run
- codex-gpt55-medium: not run
- codex-gpt55-high: not run
- raw-api-strong-low: explained_only
- raw-api-strong-medium: explained_only
- raw-api-strong-high: explained_only
- raw-api-claude-low: explained_only
- raw-api-claude-medium: explained_only
- raw-api-claude-high: explained_only
- codex-strong-low: not run
- codex-strong-medium: not run
- codex-strong-high: not run

## File edit behavior
- Actually edited files: none
- Explained only: terminal-qwen, source-proxy-qwen, raw-api-gpt4o-mini, source-proxy-gpt4o-mini, source-proxy-strong-api, raw-api-strong-low, raw-api-strong-medium, raw-api-strong-high, raw-api-claude-low, raw-api-claude-medium, raw-api-claude-high
- Manual-required: continue-qwen, terminal-hermes4, source-proxy-hermes4, continue-hermes4, continue-gemma, continue-gpt4o-mini, terminal-gemma, source-proxy-gemma, codex-gpt55-low, codex-gpt55-medium, codex-gpt55-high, codex-strong-low, codex-strong-medium, codex-strong-high

## Comparison notes
- Continue: manual-required unless exact headless model selection is configured.
- Source Proxy: scored only from produced lane files, not from explanation text.
- Hermes/Qwen/Gemma: compare only lanes with real outputs in `score.json`.
- API models: scored only when model-authored file blocks were applied.
- Source Proxy recommendation: use evidence from lanes that actually edited files; do not inflate raw chat answers.

## Anti-cheat
- Anti-cheat report: `anti-cheat-report.json`
- Corrections applied: no
- Fallbacks applied: no
- Scaffolds applied: no
- Known-good templates used: no
- Prior lane output reused: no
- Real app touched: no
- Confirmation: no Plan 4 was started.

## Phone URLs
- Launcher: run `python scripts\agent-trials\run-file-edit-model-shell-gauntlet.py --serve --host 0.0.0.0 --port 8771`

## Clean command
- `python scripts\agent-trials\run-file-edit-model-shell-gauntlet.py --clean`

## Manual-required steps
- continue-qwen: see `continue-qwen/manual-required.md`
- terminal-hermes4: see `terminal-hermes4/manual-required.md`
- source-proxy-hermes4: see `source-proxy-hermes4/manual-required.md`
- continue-hermes4: see `continue-hermes4/manual-required.md`
- continue-gemma: see `continue-gemma/manual-required.md`
- continue-gpt4o-mini: see `continue-gpt4o-mini/manual-required.md`
- terminal-gemma: see `terminal-gemma/manual-required.md`
- source-proxy-gemma: see `source-proxy-gemma/manual-required.md`
- codex-gpt55-low: see `codex-gpt55-low/manual-required.md`
- codex-gpt55-medium: see `codex-gpt55-medium/manual-required.md`
- codex-gpt55-high: see `codex-gpt55-high/manual-required.md`
- codex-strong-low: see `codex-strong-low/manual-required.md`
- codex-strong-medium: see `codex-strong-medium/manual-required.md`
- codex-strong-high: see `codex-strong-high/manual-required.md`
