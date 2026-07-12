# ADR 0001: Adopt Option B hybrid monorepo

Decision: retain one repository while creating explicit contract seams; use the final hybrid layout only in Campaign 2.
Reason: preserve current integrated behavior while reducing cross-product authority ambiguity.
Consequences: Campaign 1 may add `packages/contracts` and enforcement, but no broad directory migration.
Campaign 2 dependency: approved per-file and layout migration plans.
Revision condition: independent verification shows a contract boundary cannot preserve required runtime behavior.