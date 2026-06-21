# F01 Evidence Summary

**Status:** NOT_STARTED. Populated during F01 execution per `evidence-budget.md`.

## Will record (per-increment)
- baseline commands + outputs + hashes (captured before source edits)
- per-increment focused-check results (exact command, start time, exit code,
  decisive excerpt, raw path, SHA-256)
- receipt parity comparison (existing fields before/after)
- holdout-check results (the 7 generic checks from holdout-manifest.json)
- operator-check.sh run output
- fallback records (none expected for F01 primary capability)
- stage verdict derivation → INTERNAL_GO_PENDING_SECONDARY_REVIEW

## Raw evidence location
Recorded at stage start in `cleanup-state.json` → `evidence_root.chosen`.
Expected layout: `<evidence_root>/F01/raw/<increment>/<command-slug>.{out,err,json,.sha256}`.

## Not yet captured
(none — stage not started)
