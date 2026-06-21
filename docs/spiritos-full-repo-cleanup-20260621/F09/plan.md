# F09 — Worker / Tool Contract Cleanup

## Goal
Move direct `subprocess` / `urllib` behavior in the decision path (browser,
qwen, ollama calls) behind **typed lane adapters** that Cartographer can
inventory, plus mac-worker contract cleanup.

## Why
Direct process/network calls inside decision.py are uninventoryable, lack
timeouts, and don't classify failures. Typed adapters give every external call a
contract (request/result), a timeout, an attempt count, and an F1 failure class.

## Dependencies
**F1** (failure classification) + **F5** (lane modules — adapters live there).

## Adapter contract (frozen — each adapter must provide)
- typed request/result
- timeout
- attempt count
- failure classification (F1)
- evidence reference
- redacted logs (no secrets)
- ownership metadata

## Increments (≤12 source files each)
1. **9.1** — wrap the **qwen** call in a typed lane adapter in
   `decision/lanes/`; `decision.py` calls the lane. Parity on output + timing;
   `test_coder_agent_repomix_diff` + `test_ollama_route` stay green.
2. **9.2** — wrap remaining direct calls (browser, ollama) + mac-worker contract
   (`scripts/mac-worker/`, `src/lib/mac-worker/`); redaction + ownership metadata.

## Invariants
- Preserve output and timing contracts before retiring direct paths.
- **No new engine.** Adapters wrap existing calls; they are not a new runtime.
- Every adapter emits an F1 `reason_code` on failure.
- No secret in logs (redaction enforced).

## Stop conditions
- Lane timing changes materially (beyond documented tolerance) → NEEDS_FIX.
- Output contract drifts → NEEDS_FIX.
- Any unredacted secret in logs → NEEDS_FIX.

## Rollback
Inline the call again (adapter removed; decision.py calls the subprocess/urllib
directly as before). Each adapter independently removable.

## Approval
Britton. Codex reviews adapter contracts + redaction.
