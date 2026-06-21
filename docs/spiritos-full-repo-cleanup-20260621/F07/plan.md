# F07 — Coding UI Shell Cleanup

## Goal
Clean up the coding UI shells without deleting any and without replacing the
canonical `/coding` route. Classify shells; extract shared types / API adapters
+ hooks / timeline+receipt+debug components; add reversible feature metadata.

## Why
Three shells exist (`CodingAgentInterface.tsx`, `CodingCockpitShell.tsx`,
`CodingCommandCenterShell.tsx`) with duplicated types and unclear status.
Cleanup makes the active/legacy/experimental distinction explicit and extracts
shared surface so the shells converge on common contracts (from F1/F5/F6).

## Provisional canonical (verified at P1-prep)
`/coding` (`src/app/coding/page.tsx`) imports **`CodingCockpitShell`**. The final
future-development canonical-shell decision remains **Britton's authority**.

## Dependencies
Only after shared contracts stabilize (F1 + F5 + F6). No hard code dep, but the
receipt/trace/decision types F7 extracts depend on those being pinned.

## Allowed
- classify shells (active/legacy/experimental) + document status
- extract shared types to `*.ts`
- extract API adapters/hooks
- extract timeline/receipt/debug components
- add **reversible** feature metadata

## Forbidden
- deleting any shell
- replacing `/coding` or its canonical import
- choosing between competing product behaviors → if required, `BLOCKED_HUMAN`

## Increments (≤12 source files each)
1. **7.1** — classify shells + add reversible feature-flag metadata; extract
   shared types to `src/lib/coding/shared-types.ts` (or equivalent). No deletion.
   `coding-*-shell.test.tsx` + `page.test.tsx` stay green.
2. **7.2** — extract timeline/receipt/debug components shared across shells;
   each shell imports the shared component (additive; shell-specific behavior
   preserved via props).

## Invariants
- `/coding` still renders `CodingCockpitShell`.
- No shell file deleted.
- Feature flags are reversible (default = current behavior).
- Existing tests green; no behavior regression.

## Stop conditions
- `/coding` regresses → NEEDS_FIX.
- A product-behavior choice is forced → `BLOCKED_HUMAN`.

## Rollback
Flip feature flags to defaults; restore inline types/components. Reversible by
construction.

## Approval
Britton (canonical-shell decision is explicitly deferred — F7 does not make it).
