# Plan 5 Increment 5.1.2 - Phase Verifier Consumption Gate

Status: `GO`.

## Plan Expectation

Increment `5.1.2` requires one required subsystem to become honest, traceable, decision-bearing, and consumed by the canonical workflow. The proof must include real upstream task state, typed output, task id, trace id, invocation event id, consumer event id, consumer subsystem, changed state fields, focused checks, git status, evidence budget status, and no preview-only, advisory-only, read-only, skipped-lane, unconsumed-output, or fake-productive GO.

Because this is the second Phase 5.1 acceptance-harness increment, the bounded improvement is stricter downstream consumption: the subsystem output must be consumed by both the `/coding` operator surface consumer and a Plan 5 phase-verifier consumer on the same causal trace.

## Implemented Change

Added a phase verifier acceptance gate in:

`source_proxy/acceptance/plan5_acceptance.py`

The new gate builds on the 5.1.1 acceptance gate and requires:

- primary subsystem gate status `GO`
- phase verifier subsystem gate status `GO`
- `/coding` operator consumer event
- phase verifier consumer event
- accepted subsystem output hash
- phase verifier upstream state keys for `source_subsystem` and `accepted_output_hash`
- all invocation and consumer events on one trace
- no forbidden Plan 5 completion states

Focused tests were extended in:

`source_proxy/tests/test_plan5_acceptance_harness.py`

The tests prove the phase verifier accepts a consumed `current_research` output only when the accepted output hash is carried into verifier upstream state, and rejects metadata-only verifier consumption that omits the accepted output hash.

## Output Consumption Proof

Proof artifact:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-05/increment-5-1-2-phase-verifier-proof-20260625.json`

The proof was generated from `/home/source/SpiritOS` using temporary long-running task records.

The success gate proves:

- `current_research` output is consumed by `coding_operator_surface`
- `plan5_phase_verifier` consumes the accepted output hash
- operator and phase verifier invocation/consumer events are on the same trace
- required Plan 5 fields are present
- no forbidden completion state is present

The failure gate proves:

- failed `current_research` output is still consumed by the operator surface and phase verifier
- the phase verifier consumes the failed output hash instead of laundering it
- the task status changes to `blocked`
- the architect reason records `plan5_phase_verifier_consumed_blocked_current_research`

## GLM Caveat Handling

F-1 remains enforced from 5.1.1: `/coding` visibility proof uses a render-level operator assertion for key causal fields and authority flags.

F-2 remains enforced for 5.1.2: the focused backend test refresh and proof generation ran from `/home/source/SpiritOS`, not from the Windows mapped drive root.

## Focused Checks

Passed from `/home/source/SpiritOS`:

```text
python3 -m unittest source_proxy.tests.test_plan5_acceptance_harness
Ran 4 tests - OK
```

## Self-Check Against Plan 5

- Real subsystem named: `current_research`.
- Downstream operator consumer named: `coding_operator_surface`.
- Downstream phase verifier named: `plan5_phase_verifier`.
- Phase verifier consumer named: `plan5_phase_acceptance_consumer`.
- Real task records used: yes, temporary long-running task records.
- Causal fields present: yes.
- Output consumed downstream: yes, by operator and phase verifier consumers.
- Failure changes state/verdict: yes, the failure task becomes `blocked`.
- Render-level operator assertions preserved: yes.
- Linux-path focused test refresh: yes.
- Plan 6 started: no.
- Forbidden paths touched: no.

## Verdict

Increment `5.1.2`: `GO`.
