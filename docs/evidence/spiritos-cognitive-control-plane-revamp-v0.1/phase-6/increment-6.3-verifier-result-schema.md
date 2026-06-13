# Increment 6.3 - Verifier Result Schema

## P - Preflight

Inputs:

- Phase 1 canonical truth labels
- Phase 6.2 proof tiers and fixture contract
- Existing trial diagnostic schema and Source Proxy verifier surfaces

## I - Implement

Created a behavior verifier result schema for future implementation. The schema separates artifact readiness, static checks, behavior proof, and final product verdict.

## V - Verify

Static/manual checks:

- Schema includes canonical labels: `PASS`, `FAIL`, `NEEDS_FIX`, `UNVERIFIED`, `BLOCKED`, and `PARTIAL`.
- Schema includes proof tier, acceptance criteria, evidence paths, observed behavior, expected behavior, and unsupported PASS reasons.
- Schema includes preview-only and no-execution flags.

Unavailable checks:

- Runtime schema validation in production: UNVERIFIED because Phase 6 is evidence-only.

## O - Observe

Changed files:

- `phase-6/increment-6.3-verifier-result-schema.md`
- `phase-6/behavior-verifier-result-schema.json`

## T - Triage

Verdict: GO

Reason:

- Future verifier outputs now have a truth-preserving shape.
- PASS is structurally gated on acceptance-linked behavior proof.

Next authorized increment:

- Increment 6.4 - Dry-run verifier examples
