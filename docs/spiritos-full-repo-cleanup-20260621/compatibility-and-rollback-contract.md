# Compatibility & Rollback Contract

The cleanup must preserve these public contracts byte-for-byte (where
deterministic) or via normalized-JSON parity. Any stage that changes them is
NEEDS_FIX — no exceptions, no "improvements" to the contract mid-cleanup
(constitution §8: no moving goalposts).

## 1. Public route paths

All Source Proxy / coding HTTP route paths must remain unchanged. The canonical
`/coding` route target is `CodingCockpitShell` (verified via
`src/app/coding/page.tsx` import). No route path may be renamed, repointed, or
removed. New routes may be added (additive only, explicitly labeled).

## 2. Request/response fields

Existing request and response fields on every public endpoint must be preserved.
New fields are additive. No field may be removed or semantically redefined.

## 3. FIP0 receipt shape

The FIP0 receipt is the canonical decision artifact. Its JSON shape — field
names, nesting, types of existing fields — must not change. F1 *adds* a
top-level `failure_classification` field (additive); it does not alter existing
fields. Parity test: serialize a fixed set of inputs before and after a stage;
the existing fields must match byte-for-byte; only additive fields may differ.

## 4. FIP1–FIP6 semantics

Each FIP (field/intent/policy) stage's semantics — what it accepts, what it
rejects, what it emits — must be behavior-identical. F5 moves their
*implementation* into `decision/lanes/*` but their observable behavior is frozen.

## 5. trace_id semantics

`trace_id` generation, propagation, and correlation semantics are frozen. Causal
ordering of trace events is preserved (relevant to F1, F6). A failure event
(F1) is *added* to traces; existing trace fields/events are unchanged.

## 6. consumer_event_id semantics

`consumer_event_id` semantics — dedup, ordering, consumer-side correlation — are
frozen. F6 (engine split) and any recovery path changes preserve idempotence and
duplicate-action protection.

## 7. Policy behavior

All policy decisions (approval boundaries, write/preview/advisory boundaries,
safety gating) are behavior-identical. No policy may be silently relaxed.

## 8. fake_go_detected

`fake_go_detected` semantics and its place in the verdict surface are **frozen**.
F1 does not touch it. F2's anti-cheat registry reads it; it does not redefine it.
The field must never be hardcoded false, default-passed, or manually flipped
(constitution §3).

## 9. Verifier/grader shape

The verifier and grader input/output contracts are frozen. Anti-cheat detectors
(F2) wrap or parallel them; they do not alter their observable shape.

## 10. Approval boundaries

Human-approval-required boundaries, apply authority, and the approval gate
semantics are frozen. F6 preserves apply authority and recovery idempotence.

## 11. Apply behavior

`apply` (git-apply / next-router) behavior — what it applies, how it reports,
how it fails — is frozen. F6 may relocate the code; it may not change behavior.
Timing tolerances are documented; material timing regressions are NEEDS_FIX.

## 12. Operator-check behavior

Each stage's `operator-check.sh` must remain runnable with the same invocation
and must produce a deterministic pass/fail. Operator-check scripts may gain new
assertions (additive, frozen once the stage's contract is frozen) but existing
assertions are not weakened.

## Parity method

- **Byte-for-byte** where output is deterministic (e.g. receipt serialization of
  existing fields from fixed input).
- **Normalized-JSON parity** where ordering/whitespace is non-deterministic:
  parse both, sort keys, compare existing-field subsets.

## Rollback

Every stage documents an exact rollback in its `plan.md` (e.g. "revert enum
module; fallback strings still work"). Rollback must restore the pre-stage
contract exactly. Compatibility drift that cannot be rolled back cleanly is a
stop condition (`BLOCKED_HUMAN`).
