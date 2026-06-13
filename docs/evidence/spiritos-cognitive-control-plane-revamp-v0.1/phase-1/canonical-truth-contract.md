# Canonical Truth Contract

## Purpose

The canonical truth contract defines how SpiritOS labels product, route, worker, and verification outcomes. It prevents fake-green closeouts by separating real behavior proof from weaker signals such as artifact existence, preview availability, route liveness, static rendering, or unit-test-only scaffolding.

This Phase 1 artifact is evidence-only. Runtime adapters are deferred to later authorized phases.

## Core Principle

A product PASS requires verified behavior against the requested acceptance criteria. Anything less must be labeled with the strongest honest non-PASS state.

## Canonical Labels

| Label | Meaning | May Close GO? |
| --- | --- | --- |
| `PASS` | Required behavior was directly verified against the acceptance criteria. | Yes, if scope is complete and evidence is attached. |
| `FAIL` | Required behavior was executed or inspected and did not meet acceptance criteria. | No. |
| `NEEDS_FIX` | The system path, route, worker, environment, or proof pipeline failed before product behavior could be judged. | No. |
| `UNVERIFIED` | The check was not run, unavailable, unsafe, or outside the authorized scope. | No, unless explicitly accepted as a partial evidence baseline. |
| `BLOCKED` | A required gate, permission, dependency, or operator choice prevents progress. | No. |
| `PARTIAL` | Some required criteria passed, but at least one required criterion remains failed, blocked, or unverified. | No for the whole phase; may close only a narrower increment if the missing part is explicitly out of scope. |

## Evidence Strength

| Evidence Type | Strength | Product PASS Eligible? |
| --- | --- | --- |
| Behavior interaction proof | Strong | Yes |
| Computed state proof | Strong | Yes, if mapped to visible/user-relevant behavior |
| Screenshot/video proof | Medium | Yes only when acceptance is visual and the capture proves it |
| Test output | Medium | Yes if the test covers the requested behavior |
| Diff preview | Medium-low | No by itself |
| Route liveness | Low | No |
| Artifact exists | Low | No |
| Preview opens | Low | No |
| Static content renders | Low | No |
| Unit tests for unused classes | Low | No |
| Model/provider response says success | Low | No |

## Required Result Fields

Every future truth-labeled result should carry:

- `label`: one canonical label.
- `scope`: product, route, worker, verifier, permission, artifact, or phase.
- `acceptance_criteria`: concrete behavior or contract being judged.
- `evidence`: links, command output summaries, screenshots, traces, logs, or fixture IDs.
- `reason_codes`: stable machine-readable reasons.
- `raw_diagnostics_ref`: pointer to raw evidence when available.
- `unverified_checks`: checks not run, with reasons.
- `protected_flow`: existing SpiritOS/Source Proxy flow protected or prepared.

## Non-PASS Rules

- Artifact existence does not imply product PASS.
- Preview opens does not imply behavior PASS.
- Static content does not imply app behavior.
- Route liveness does not imply worker/product behavior.
- A model/provider response claiming success is not proof by itself.
- Passing unit tests for unused classes does not prove integration.
- Missing preview/artifact cases are FAIL for artifact readiness and UNVERIFIED for behavior.
- Route/proxy/model unavailability should be NEEDS_FIX when product behavior could not be judged.
- No-diff or empty productive output must not collapse to PASS.
- Corrected behavior diagnostics are proof inputs for future phases.

## PASS Requirements

To label product behavior `PASS`, the result must include:

1. The exact acceptance criterion.
2. A direct behavior interaction, computed state check, or test that covers the behavior.
3. Observed result matching expected result.
4. Evidence reference.
5. No unresolved blocker for the judged scope.

## FAIL Requirements

Use `FAIL` when:

- The artifact/app exists but behavior is wrong.
- UI controls are missing for a task that requires interaction.
- Visual state toggles do not produce visible/computed change.
- Generated output is not the requested product type.
- A required preview/artifact is missing for artifact-readiness evaluation.

## NEEDS_FIX Requirements

Use `NEEDS_FIX` when:

- Source Proxy, route, worker, preview route, timeout, or environment failure prevents behavior judgment.
- Provider/model truth is missing or contradictory for a run that depends on provider/model proof.
- The proof pipeline drops diagnostics and leaves only generic missing-proof output.

## UNVERIFIED Requirements

Use `UNVERIFIED` when:

- A check was not run.
- The check is outside current phase authorization.
- The check would require forbidden provider calls, live worker starts, Obsidian writes, or generated artifact mutation.
- The available evidence is too weak to judge product behavior.

## Phase Closeout Rule

A GO closeout must state the real existing flow protected, wrapped, or prepared. Evidence-only phases may GO only when their artifact is complete and the later integration requirement is explicit.

