# F10 — Full Cleanup Requalification

## Goal
After F1–F9, run the complete requalification battery that proves the cleanup is
honestly ready for independent secondary review. This is the **terminal gate**:
on F10 GO, the cleanup writes the secondary-review handoff and STOPS.

## Why
F10 is the single point where the whole cleanup's anti-cheat, compatibility, and
scope discipline are verified together. No stage is accepted on its own
assertion; F10 re-derives the verdict from raw evidence.

## Dependencies
**F1–F9 all GO.** F10 does not introduce capability; it verifies.

## Battery (frozen — see acceptance-contract.json for the full command list)
- all taxonomy tests (F1)
- all failure-class tests (F1)
- anti-cheat negative corpus (F2)
- legacy/new parity where applicable (F2, F5, F6, F9)
- brain-switch dry-run tests (F3)
- proof no unapproved provider call occurred (F3, whole-cleanup)
- generic packet decomposition holdouts (F4)
- **benchmark-tailoring scan** over runtime paths (constitution §A)
- receipt compatibility (F1/F5)
- trace/consumer compatibility (F5/F6)
- apply/recovery tests (F6)
- focused Python tests
- bounded broader Python tests
- lint, typecheck, build
- canonical `/coding` tests (F7)
- bounded non-battery browser smoke if available
- Plan 2 operator
- Plan 3 operator
- Headroom/fallback contract checks (F8)
- protected-path checks (no protected path edited)
- dirty-tree checks
- `git diff --check`

## Forbidden in F10
- **Do NOT run Set A, Set B, or Set C.**
- **Do NOT use known battery prompts for cleanup acceptance.**
- Old Set A is rerun only after independent review + Britton approval.

## Increments
1. **10.1** — assemble the battery harness; run backend (taxonomy, failure-class,
   anti-cheat negatives, parity, brain-switch dry-run, decomposition holdouts,
   apply/recovery, focused + bounded broader Python).
2. **10.2** — run frontend + operator (lint, typecheck, build, /coding tests,
   browser smoke if available, Plan 2 + Plan 3 operators, Headroom/fallback,
   protected-path, dirty-tree, git diff --check, tailoring scan, no-API proof).
3. **10.3** — write `secondary-review-handoff.md`; set `cleanup-state.json` →
   `ready_for_secondary_review=true`; STOP.

## Invariants
- Every battery item reports exact command, exit code, raw path, SHA-256,
  conclusion (constitution §10).
- A skipped/timed-out/fallback-relied test is reported PARTIAL/BLOCKED_ENV/
  NEEDS_FIX, never PASS (constitution §I).
- No minor caveat may hide a required-test failure, receipt/trace drift,
  anti-cheat regression, default/canned PASS, protected-path edit, benchmark
  tailoring, hidden fallback, missing evidence, unapproved API call, or
  apply/recovery regression.

## Stop conditions
- Any battery item red → NEEDS_FIX (repair under the existing frozen contracts;
  no weakening).
- Tailoring scan finds a benchmark-specific production branch → automatic NEEDS_FIX.
- Any unapproved API call detected → NEEDS_FIX + human review.

## Approval
F10 INTERNAL_GO_PENDING_SECONDARY_REVIEW is the cleanup's terminal state. Final
acceptance is independent Codex review + Britton + merge authority (all separate
from this cleanup). GLM does NOT self-accept.
