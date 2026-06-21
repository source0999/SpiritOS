# F09 Codex Review Report

**Status:** PENDING. Filled by independent Codex review after F09 INTERNAL_GO.

## Codex checks for F09
- Every adapter has the 7 contract fields (typed I/O, timeout, attempts, F1 class, evidence ref, redaction, ownership).
- Output + timing parity vs direct path (within documented tolerance).
- No direct subprocess/urllib for wrapped targets in decision.py.
- No unredacted secret reaches logs or evidence.
- No new engine (adapters wrap, not replace).
- Failures classified with correct F1 code.

## Verdict
- [ ] ACCEPT  [ ] NEEDS_REPAIR  [ ] REJECT

## Notes
(filled by reviewer)
