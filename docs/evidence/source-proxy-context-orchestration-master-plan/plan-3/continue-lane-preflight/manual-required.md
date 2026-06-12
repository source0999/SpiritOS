# Continue Lane Preflight — Manual Steps

**Status: not required for basic CLI invocation and file edit proof.**

Continue CLI (`cn` 1.5.44) is on PATH at `/usr/bin/cn`. Headless file edit succeeded with `cn --auto -p` in the disposable workspace.

## Optional follow-ups before full gauntlet (not blockers for preflight GO)

1. **Per-lane model selection** — Gauntlet lanes target qwen2.5-coder, hermes4, gemma, and gpt-4o-mini. Preflight used default `gemini-2.5-flash`. Harness should pass `cn --model <slug>` or update config for each lane.
2. **Qwen in Continue config** — `qwen2.5-coder:7b` is in Ollama but not in `~/.continue/config.yaml`.
3. **Gemma** — Not installed in Ollama; not in Continue config.
4. **gpt-4o-mini** — Not in Continue config; would need hub slug or config entry.

No interactive approval was required when using `--auto`.
