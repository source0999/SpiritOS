# Phase 2 Closeout - Local default routing integration

Date: 2026-05-29

## Result

GO.

## Evidence

- Increment 2.1: env examples and README now document Hermes 4 as the local default, exact Hermes 4 model IDs, Hermes 3 fallback role, Qwen selectable/non-default role, and 8TB storage verification requirements.
- Increment 2.2: Source Proxy local routing defaults to Hermes 4, avoids unconfigured Qwen fallback, prefers installed Hermes models when probing, and exposes requested/resolved/probe/storage truth.
- Increment 2.3: `/coding` provider/model diagnostics use Source Proxy model truth and now prefer the resolved local model field when available.

## Notes

- The repo had pre-existing dirty changes in `src`, `source_proxy`, `docs`, and other paths; manual diff evidence may include unrelated prior work because this gate was run inside that dirty worktree.
- OpenAI, Anthropic, and DeepSeek route support was not removed or changed.
- Qwen remains selectable when explicitly configured.
- `git diff --check` passed at phase closeout.
