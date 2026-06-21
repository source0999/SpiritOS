# F02 — Independent Anti-Cheat Registry

## Goal
A standalone `source_proxy/verification/anticheat/` package with independent
detectors that guard the system's honesty **from outside** the system under test.
Independence by process, not just by function.

## Why
The system must not grade its own honesty. Today's selftests live alongside the
code they check; an independent package run as a separate process gives a
stronger guarantee. This is the constitutional backbone (§B, §C, §E, §F).

## Primary new dir
`source_proxy/verification/anticheat/`
(`verification/` exists with `contracts.py, deterministic.py, diff.py`;
`anticheat/` is absent → created here.)

## Method — COPY, do not move
1. Copy the existing selftest lineage (4R2/4R4/4R7 anti-cheat checks) into the
   new package. The originals stay.
2. Run legacy + new **in parallel**.
3. Require **parity** (identical verdicts on the same inputs) **plus** the new
   negative cases below.
4. Do **not** retire legacy behavior in the first increment.

## Negative corpus (frozen before implementation — see holdout-manifest.json)
canned output; static research labeled live; route existence labeled
integration; status ping labeled behavior; repo context labeled internet;
fixture/mock labeled live; preview/advisory labeled executed; fallback labeled
primary success; renderer-created decisions; manual PASS/JSON manipulation;
canned output with consumer event; unavailable provider labeled success;
summary/raw contradiction; benchmark-specific runtime branch; test-only
production branch.

## Increments (≤12 source files)
1. **2.1** — create `verification/anticheat/` package; copy detectors; parity
   harness; parity test asserts legacy==new on shared corpus.
2. **2.2** — add new independent detectors for the negative corpus above; wire
   Set A runner to import from the package (additive, legacy still used); tests.

## Invariants
- Legacy detectors remain callable and unchanged in 2.1.
- New detectors run as an independent process/harness, not in-process with the
  code under test where avoidable.
- Parity must hold; a divergence is a finding, not silently resolved.
- `fake_go_detected` is read, never redefined or hardcoded false.

## Stop conditions
- Parity fails and cannot be explained by a genuine new detection (i.e. the new
  detector is wrong) → NEEDS_FIX.
- Any protected path touched → NEEDS_FIX.

## Rollback
Delete the new package; legacy detectors are untouched. Exact, complete.

## Approval
Britton + Codex. Highest-honesty stage alongside F3.
