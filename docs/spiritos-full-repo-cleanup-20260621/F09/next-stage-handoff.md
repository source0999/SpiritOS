# F09 → F10 Handoff

**Status:** NOT_STARTED (finalized when F09 verdict set).

## F09 hands to F10
- Direct subprocess/urllib calls in the decision path are wrapped in typed lane
  adapters with the 7-field contract; mac-worker contract cleaned up.
- Output/timing parity proven; redaction enforced; failures F1-classified.

## F10 can begin once
- F09 verdict == INTERNAL_GO_PENDING_SECONDARY_REVIEW.
- **F01–F09 all GO.** F10 is the terminal requalification of everything prior.

## Carry-forward for F10
- F10 runs the complete requalification battery (see F10/acceptance-contract.json).
- F10 MUST include the benchmark-tailoring scan over runtime paths (constitution §A).
- F10 MUST prove no unapproved API call occurred across the whole cleanup.
- **Do NOT run Set A/B/C. Do NOT use known battery prompts for cleanup acceptance.**
- On F10 GO: write `secondary-review-handoff.md` (top-level, replacing the DRAFT),
  set `cleanup-state.json` → `ready_for_secondary_review=true`,
  `current_stage=SECONDARY_REVIEW`, and STOP for independent Codex review.
