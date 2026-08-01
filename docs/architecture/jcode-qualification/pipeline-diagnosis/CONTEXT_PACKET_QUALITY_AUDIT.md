# Context Packet Quality Audit

## Decision

The current full Proxy packet is not model-ready for these coder tasks. It
contains the relevant diagnostic source and test in the controlled Lane E
construction, but surrounds them with human workflow, governance, broker,
route, phase, and paste-back material. Production intake also does not require
acceptance criteria or complete supporting test content.

## Measured Packet Noise

| Task/lane packet | Bytes | Estimated input tokens | Relevant ratio lower bound | Governance hits | Task byte position | Source/test byte positions | Output budget |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| R minimal | 524 | 131 | 0.456107 | 0 | 26 | 34, 48 | 1,024 |
| R full | 12,579 | 3,145 | 0.019000 | 12 | 5,807 | 2,538, 2,575 | 1,024 |
| W minimal | 505 | 126 | 0.455446 | 0 | 26 | 34, 47 | 1,024 |
| W full | 14,016 | 3,504 | 0.016410 | 12 | 6,663 | 2,991, 3,051 | 1,024 |

The R full packet is 24.0 times the minimal packet by bytes; W is 27.8 times.
The relevant lower-bound ratio falls from about 45.5 percent to 1.6-1.9
percent. Task text moves from byte 26 to byte 5,807 or 6,663. This is packet
attention pressure even before provider context limits are considered.

## Construction Findings

- `TaskSpecIntake` has no acceptance-criteria field. The legacy form emits
  `literal_requirements: []`; verification policy is not an equivalent task
  contract. Classification: `PACKET_ACCEPTANCE_CRITERIA_MISSING`.
- `_build_canonical_context_packet` can include the explicit target, but it
  slices text at 6,000 characters and does not prove that all critical bytes or
  the relevant focused test are present. Classifications:
  `PACKET_CONTEXT_TRUNCATION`, `PACKET_TEST_CONTENT_ABSENT`.
- `build_prompt_packet` adds phase checks, passivity/repo-first questions,
  generic requested-output sections, and paste-back instructions. These are
  useful for a human advisory packet but conflict with a coder execution
  packet. Classifications: `PACKET_CONTEXT_BLOAT`,
  `PACKET_INSTRUCTION_CONFLICT`, `PACKET_TASK_BURIED`,
  `CONTEXT_BUDGET_MISALLOCATED`.
- The full diagnostic packets contained exact source and test bytes and did not
  expose expected answers. The failure is therefore not caused by missing
  fixture content in Lane E. Both E cells timed out instead of returning a
  grounded answer.
- The E7 provider service telemetry observed an input allocation of 4,147
  tokens reduced to `n_ctx=4096`. The exact E7 request body is the audit's one
  declared capture gap, so this is supporting truncation evidence, not a
  byte-complete reconstruction. Classification: `EVIDENCE_INCOMPLETE`.
- E14 preserved its exact request and timed out with a rendered model prompt of
  15,490 characters. This independently supports full-packet pressure without
  relying on E7's missing body.
- JCode D and F first-turn backend prompts are both 2,801 characters for Task R
  because JCode sees mounted task/context paths and hashes, not their contents.
  Full packet content cannot influence the model until the read tool works.
  Thus D/F equivalence on turn one is expected and must not be used to clear the
  full Proxy packet.

## Required Model-Ready Shape

The coder packet must put the concise task and deterministic acceptance
criteria first, followed by exact writable and read-only paths, minimal tool
schemas, prohibited actions, identity/hash bindings, and only the critical
source/test bytes. Campaign history, architecture discussion, paste-back
instructions, optional memory metadata, and unrelated research receipts are
excluded unless the task itself requires them.

Gate 2-J.9T sets the binding thresholds: all critical files and bytes present,
100 percent path consistency, no critical truncation, relevant-context ratio at
least 0.40 for qualification fixtures, zero campaign/governance markers in the
coder task body, task and acceptance criteria before context, and at least
1,024 output tokens reserved.
