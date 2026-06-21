# F03 Codex Review Report

**Status:** PENDING. Filled by independent Codex review after F03 INTERNAL_GO.

## Codex checks for F03 (highest-stakes)
- **No real API/cloud call** anywhere in the contract path (re-verify via
  network monkeypatch + code audit of recommend()).
- Verdicts derived from F1 failure classes + attempt history, never from task
  label or benchmark ID.
- Label-invariance: identical shape, different label → identical recommendation.
- Unavailable provider never reported available.
- recommend() records all required fields (task shape, attempts, privacy/cost,
  authority, evidence IDs).
- Provider policy is advisory-only; no silent escalation.

## Verdict
- [ ] ACCEPT  [ ] NEEDS_REPAIR  [ ] REJECT (any unapproved API call = REJECT → Britton)

## Notes
(filled by reviewer)
