# Increment 2.3 - Evidence Selection and Truth Carry-forward Rules

## P - Preflight

- Repo path: `\\10.0.0.186\SpiritOS\`
- Phase 1 truth contract inspected.
- Existing Obsidian safe-excerpt behavior inspected.

## I - Implement

Created:

- `memory-selection-rules.json`
- `increment-2.3-evidence-selection-rules.md`

## V - Verify

- Obsidian include/exclude behavior captured: PASS
- Evidence doc selection rules captured: PASS
- Durable run handling rules captured: PASS
- Phase 1 truth carry-forward rules captured: PASS
- Unavailable memory rule uses `UNVERIFIED`, not PASS: PASS

## O - Observe

Skipped/unverified checks:

- Live memory query execution: UNVERIFIED, Phase 2 is contract/evidence-only and does not require route calls.

## T - Triage

Verdict: GO

Next authorized increment: Increment 2.4 - Existing-system adapter map.

