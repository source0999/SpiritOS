# F05 — Split Decision Transport from Domain Lanes

## Goal
`source_proxy/api/decision.py` (7,971 lines, confirmed) → a **thin router**; the
FIP0–FIP6 domain logic → cohesive `source_proxy/decision/lanes/*` modules:
`receipts.py, context.py, research.py, coder.py, verifier.py, trace.py`.
(`decision/lanes/` is absent today → created here.)

## Why
Audit §7 concentration risk: a 7,971-line file mixing transport, receipts, lane
logic, and tracing is the single largest correctness/honesty risk surface.
Cohesive lanes make each FIP independently testable and inventory-able by
Cartographer.

## Dependencies
**F1** (hard): each lane must emit an F1 `reason_code`. Splitting before taxonomy
exists would propagate untyped failures into every new module.

## Method — safe-first-patch (strict)
1. **Copy** a pure helper/serializer (FIP0 receipt serialize) into
   `decision/lanes/receipts.py`. Do not delete from decision.py yet.
2. Add a **compatibility import** so callers can opt in.
3. **Parity proof**: a test serializes a fixed corpus through both the old and
   new paths; existing-field JSON must be byte-for-byte / normalized-identical.
4. **Switch the canonical call** to the new path.
5. **Exact retirement**: remove the old inline implementation only after parity
   proof passes. Exact-path deletion, no hidden consumer remains.

## Increments (≤12 source files each)
1. **5.1** — `lanes/receipts.py` (FIP0 serialize) extracted; parity proof;
   canonical switch; old retired exactly. Lane-isolation test.
2. **5.2** — `lanes/context.py` + `lanes/research.py` (same copy→import→parity→
   switch→retire cycle).
3. **5.3** — `lanes/coder.py` + `lanes/verifier.py` + `lanes/trace.py`; slim
   decision.py to a thin router (target < 1,500 lines, by cohesion not line count).

## Preserve (compatibility contract — immutable)
route paths; request/response shape; FIP0–FIP6 semantics; receipt fields;
trace/consumer behavior; final status; `fake_go_detected`; preview/advisory/write
boundaries.

## Invariants
- **No line-count-only refactor.** Splits are by responsibility/cohesion.
- **No new parallel engine.** One decision path, relocated.
- **No behavior change.** Observable behavior identical (parity-gated).

## Stop conditions
- Receipt JSON shape changes → NEEDS_FIX.
- Any FIP semantics drift → NEEDS_FIX.
- Parity fails after ≤3 repairs → NEEDS_FIX.

## Rollback
Move functions back into decision.py (or re-point imports). Each increment is
independently reversible because the copy→retire cycle leaves a clean seam.

## Approval
Britton approves the lane layout. Codex reviews parity proofs.
