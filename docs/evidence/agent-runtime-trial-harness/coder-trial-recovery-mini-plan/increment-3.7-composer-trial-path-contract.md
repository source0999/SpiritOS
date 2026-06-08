# Increment 3.7 - Composer/Trial Path Contract

Status: documented and partially verified.

Inspected path:
- normal prompt packet route: `source_proxy/api/decision.py`
- bounded/live trial prompt path: `_bounded_coder_diff_or_stub`
- prompt packet construction: `source_proxy/decision/prompt_packet.py`
- Coder execution/provenance path: `source_proxy/tasks/long_running.py`
- durable rows and UI fields: existing dirty work in `src/lib/coding/*` and `src/components/coding/*`

Confirmed:
- Trial mode has stricter scaffold/fallback ban semantics.
- Normal composer path still exposes manual prompt packet or Coder path depending on route decision.
- Shared diagnostics now exist in Coder diagnostics and prompt-packet context metadata.
- Future single-prompt runner can reuse prompt-packet plus Coder diagnostics without inventing a fake proof path.

Manual/self-check:
- No debug-only fake path was introduced.
- No Coder 10/25/50/100 run was executed.
- Designer, Combined, media, SpiritFlix, Scout, Oracle, and 999Playr were not intentionally modified in Gate 3.

Blocker:
- The dirty tree already contains unrelated SpiritFlix and other files. They were not reset or cleaned.
