# F08 Status

**Stage:** F08 — Context / memory / Headroom / repomix consistency
**Status:** NOT_STARTED · **Verdict:** (pending)

## Frozen artifacts
- `acceptance-contract.json` — frozen (3-proof Headroom gate; context shape; 4 gates).
- `holdout-manifest.json` — frozen (6 honest-fallback checks).

## Baseline
`headroom-check.sh` (expect BLOCKED_ENV) + `verify-repomix-context.sh`.

## Increments
- 8.1 — HEADROOM_PORT consistency + Cursor/8797 documentation
- 8.2 — context/memory digest consistency + honest headroom_status probe

## Expected minor caveat
Headroom runtime BLOCKED_ENV while config/docs consistent + tree-sitter honestly labeled (owner: Britton; next: real Headroom enablement, separate decision).

## Gate results / Caveats
(populated during execution)
