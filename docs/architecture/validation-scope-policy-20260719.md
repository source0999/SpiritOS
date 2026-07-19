# Validation-scope policy correction — 2026-07-19

**Status:** `ACCEPTED_VALIDATION_SCOPE_CORRECTION`

Validation has three scopes. A failure remains a failure in every scope; scope
defines applicability, not truthfulness.

1. `TRANSACTION`: a failure invalidates the files or authority boundaries of the
   current commit and blocks that commit.
2. `EXTERNAL_DEPENDENCY_HEALTH`: a failure is retained in the result and blocks
   only work that declares the affected dependency.
3. `CAMPAIGN_EXECUTION_GATE`: a failure blocks a specific phase or task that
   declares the gate.

The Campaign 1/2 SpiritFlix continuity validators continue to report
`protected_head_mismatch:spiritflix`; external strict verification also fails.
Those facts are not waived. For this Source Proxy planning-only transaction,
the failure has `scope=EXTERNAL_DEPENDENCY_HEALTH`,
`applies_to_current_transaction=false`, and
`blocks_current_transaction=false`. It has
`blocks_spiritflix_dependent_execution=true`, so it blocks any future
SpiritFlix-backed Campaign 3.5 task, Campaign 4 UI proof, or SpiritFlix action
until the separate repair plan is completed.

Unknown scope or applicability defaults to transaction-blocking. A result may
not omit scope metadata to downgrade a failure. The policy is implemented by
`scripts/validate-campaign-3-5-planning-transaction.py` and tested by
`scripts/test-validation-scope-policy.py`.
