# Phase 3 Closeout - Tool compatibility and safe gating

Date: 2026-05-29

## Result

GO with caution.

## Evidence

- Increment 3.1: Hermes 4 responded through Ollama OpenAI-compatible chat and accepted an OpenAI-compatible tool schema with HTTP 200.
- Increment 3.1: Hermes 4 emitted a noop `tool_calls` entry despite the prompt instructing it not to call tools. This proves schema transport compatibility, not safe autonomous tool behavior.
- Increment 3.2: docs/status comments now keep local tools disabled by default and say to enable `SPIRIT_OLLAMA_SUPPORTS_TOOLS` only after a fresh operator probe approves the exact model/tool policy.

## Notes

- No file edit/dev command tools were enabled by default.
- `git diff --check` passed at phase closeout.
