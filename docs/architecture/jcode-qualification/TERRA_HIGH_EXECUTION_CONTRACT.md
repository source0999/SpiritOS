# Terra High Execution Contract

status: `SPECIFIED_NOT_RUNTIME_PROVEN`

Terra High is an implementation-work role, not a tracked runtime component and
not an authority source. It is subordinate to `CodingOrchestrator`, parallel to
the JCode candidate, and a consumer of campaign authority artifacts.

## Allowed responsibilities

- Execute a bounded, operator-authorized work packet in its named worktree.
- Read only the packet's referenced artifacts and return durable evidence.
- Run the packet's registered focused tests and commit only explicit paths.
- Stop and escalate on an identity mismatch, scope change, failed mandatory
  test, authority conflict, or missing acceptance decision.

## Forbidden responsibilities

- Create tasks, grant approvals, alter terminal truth, select providers,
  modify benchmarks, operate the daily runtime, merge a primary branch, or
  interpret design presence as runtime integration.

## Required work-packet fields

`campaign_id`, `gate_id`, objective, verified branch/commit, allowed and
protected paths, dependencies, acceptance criteria, tests, evidence, commit
policy, stop conditions, and next handoff target.

Until a traced invocation exists, this document defines no Terra High runtime
claim or model binding.
