# AGENT_LOOP_CONTRACT.md

Detailed contract for Gate 2-J.9T section I. The controlling spec is
`PACKET_AMENDMENT.md`; this file elaborates the loop mechanics.

## Required bounded loop

```text
Model turn
  -> normalize tool request (native OR strict textual envelope)
  -> authorize tool (path/command before execution)
  -> execute tool
  -> record observation
  -> inject observation under the correct role and tool name
  -> next model turn
  -> repeat until completion or budget stop
```

## Mandatory behaviors

- **Observation reinjection.** After every productive read/edit/test, the exact
  observation MUST reenter the model under the tool role/name before the loop
  decides completion. (Proven defect: Lane C executed a read and exited on
  empty `recommended_checks` without returning the observation.)
- **Prior-turn preservation.** All prior messages are retained across turns.
- **Bounded turn count.** <= 3 total model turns.
- **Bounded tool calls.** defined per task; no unbounded tool fan-out.
- **Truthful tool errors.** Denials/errors return to the model under the
  expected role/tool name; never silently swallowed.
- **Retry policy.** Retry ONLY for parser/recovery/verification reasons defined
  before the run. Never tune a retry to observed task content.
- **Final-answer handling.** Valid final answer for read tasks; scoped diff +
  passing focused test for write tasks.
- **Cancellation / timeout / evidence.** Cancellation honored; timeouts
  recorded; complete evidence per turn.
- **No premature exit.** Do NOT exit immediately after the first tool unless the
  task is genuinely complete.

## Recovery: model requests files already available

1. Do NOT terminate immediately.
2. Return a standardized tool-availability reminder.
3. Include the exact available tool names and file manifest.
4. Preserve the task unchanged.
5. Permit one bounded recovery turn.
6. Record failure if the model still refuses tools.

Do NOT reveal the answer.

## Truthful termination outcomes

- `COMPLETED` (valid final answer / passing focused test);
- `STOPPED_BUDGET` (turn or tool budget exhausted, all attempts retained);
- `STOPPED_TIMEOUT` (provider timeout; MUST NOT be labeled model incapability);
- `STOPPED_REFUSAL` (model refused tools after bounded recovery);
- `STOPPED_EVIDENCE_INCOMPLETE` (exact bytes unavailable; cannot qualify).

A provider timeout is a system/latency signal, not a model-quality verdict;
qualify a latency/context budget separately (see QWEN_14B profile).
