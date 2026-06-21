# Dependency Map — F1–F10 Stage Ordering

Enforces the required ordering. Rationale recorded so deviations are explicit
and reviewable.

## Enforced ordering

```
F1 ──► F3 ──► F4 ──► (old Set A rerun, post-review)
 │      │
 │      └──► F10
 │
 ├──► F5 ──► F9
 │     │
 │     └── (preferably before) ──► F6
 │
 ├──► F6
 │
 └──► F9 (also needs F5)

F2 ──► F10

F7  (only after shared contracts stabilize — i.e. after F1, ideally after F5)

F8 ──► F10

F1..F9 ──► F10
```

## Required rules (from task) + why

| Rule | Why |
|---|---|
| **F1 before F3** | F3's escalation contract must reference F1's typed failure classification; otherwise escalation is decided on free strings. |
| **F1 before F5** | F5 splits lanes; each lane must emit an F1 `reason_code`. Doing the split before taxonomy exists propagates untyped failures into every new module. |
| **F1 before F6** | Long-running failure events in traces must use F1 classes; splitting the engine first would scatter ad-hoc failure strings across new modules. |
| **F1 before F9** | Every typed adapter must emit an F1 failure classification. |
| **F2 before F10** | F10's requalification relies on the independent anti-cheat registry as a negative-corpus gate. |
| **F3 before F4** | Decomposition recommendations (F4) must be expressed via F3's verdict contract (e.g. `LOCAL_DECOMPOSITION_RECOMMENDED`). |
| **F3 before F10** | F10 proves no unapproved API call + brain-switch dry-run; that contract is F3's deliverable. |
| **F4 before old Set A rerun** | Generic decomposition is what could make A5/A9-style prompts locally satisfiable; rerunning Set A before that re-tests the same wall. (Rerun is post-review anyway.) |
| **F5 before F9** | F9 adapters live in the lane modules F5 creates; routing direct calls through adapters before the lane split exists would build throwaway shims. |
| **F5 preferably before F6** | F5 stabilizes the decision surface (receipts/lanes) that F6's apply/trace/recovery modules consume. Doing F6 first risks duplicating receipt logic. |
| **F7 only after shared contracts stabilize** | UI shell cleanup extracts shared types/hooks/components that depend on the receipt/trace/decision contracts F1 and F5 pin down. Wait for those. |
| **F8 before F10** | Headroom/fallback contract checks are part of F10; F8 must have made the scripts consistent first. |
| **F1–F9 before F10** | F10 is the terminal requalification of everything F1–F9 produced. |

## Recommended execution order

`F1 → F2 → F3 → F4 → F5 → F6 → F7 → F8 → F9 → F10`

(F2 has no upstream dep and may be done anytime before F10, but doing it early
gives later stages an independent honesty check to lean on. F8 likewise is
unblocked and can be slotted where convenient before F10; the order above keeps
it after the code-heavy stages so its config-consistency work isn't invalidated
by later file moves.)

## Parallelization (allowed, not required)

- F1 is the hard serialization point; nothing that depends on taxonomy may start first.
- F2 and F8 are independent of the F1→F5→F9 chain and could run in parallel with it.
- F6 and F7 both depend on F5-stable contracts and could overlap if contracts are frozen.

This packet assumes **sequential** execution (one in-flight stage) unless Britton
explicitly authorizes a parallel branch, because the cross-stage execution
protocol's dirty-path guard is simplest to keep honest with one active stage.
