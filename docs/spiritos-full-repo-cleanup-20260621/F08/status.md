# F08 Status

**Stage:** F08 - Context, memory, Headroom, Repomix contract
**Status:** INTERNAL_GO_PENDING_SECONDARY_REVIEW
**Verdict:** INTERNAL_GO_PENDING_SECONDARY_REVIEW

## Completed
- `headroom-proxy-dev.sh` no longer bootstraps a venv or installs packages.
- `headroom-check.sh` reports active only after health success.
- `verify-repomix-context.sh` requires positive `tokens_saved` before accepting `compressed=true`.

## Current state
- Headroom health probe on `127.0.0.1:8797` is inactive.
- Fallback is explicitly labelled tree-sitter-only.
