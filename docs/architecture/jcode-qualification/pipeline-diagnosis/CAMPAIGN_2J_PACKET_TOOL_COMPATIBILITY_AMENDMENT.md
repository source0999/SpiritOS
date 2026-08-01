# Gate 2-J.9T - Human-to-Coder Packet and Tool Compatibility Qualification

## Binding and Placement

Amendment ID: `CAMPAIGN_2J_GATE_9T_PACKET_TOOL_COMPATIBILITY_V1`

Operator authority:
`OPERATOR_AUTHORIZATION__C2J_PIPELINE_DIAGNOSIS_20260731_V1`, prompt SHA-256
`f45bde0f3fd1c4c225f4a896577a0778408d449ebee41b3dc4f57c0171ab7afb`.

Insertion point: immediately after Gate 2-J.9I and before Gate 2-J.9J. This is
the least disruptive insertion because 9I established containment safety but
did not separate raw model capability from packet/tool compatibility.

This artifact is binding for advancement decisions on the audit branch. It is
not merged into the canonical Campaign 2-J branch and does not authorize any
production change, comparison run, or Campaign 4 advancement.

Current decision: `PIPELINE_NOT_READY_FOR_COMPARISON`.

## 1. Canonical Model-Ready Task Packet

Every coder execution MUST use one canonically serialized packet containing:

1. Schema version, task ID, immutable task hash, and one specific coding
   objective.
2. Deterministic acceptance criteria with exact focused checks.
3. Exact writable files, exact read-only supporting files, protected/denied
   files, and the mounted path for every declared file.
4. SHA-256 and byte count for every critical file; full critical contents or an
   explicit excerpt range plus a proof that omitted bytes are noncritical.
5. The minimal tools needed by the criteria, with exact name, description,
   JSON schema, required fields, result role, and invocation dialect.
6. Exact model registry ID, full model digest, provider profile, executor/JCode
   identity, context hash, and task hash.
7. Input, output, timeout, request, and turn budgets. At least 1,024 output
   tokens and 256 context tokens of safety margin MUST remain after input.
8. Prohibited actions: network, credentials, memory/session reuse, undeclared
   files, Git mutation, commit, push, merge, deploy, release, benchmark access,
   fallback, and model substitution unless a later authorization explicitly
   changes one item.

The model-visible body MUST NOT contain unrelated campaign history,
architecture debates, paste-back instructions, phase inheritance, optional
memory metadata, or generic governance text.

## 2. Model-Visible Packet Receipt

Before each provider send, the executor MUST durably record and hash:

- exact canonical request bytes and request body;
- exact ordered messages, roles, system/project instructions, stop sequences,
  and generation parameters;
- ordered file manifest, contents/excerpts, omissions, paths, byte counts, and
  hashes;
- exact tools, `tool_choice`, allowed/denied paths, and command policy;
- token counts/estimates, output reserve, task/criteria/source/test positions,
  and truncation decision;
- model registry ID, full digest, provider-reported model, JCode binary hash,
  adapter, relay, bridge, and context-builder versions;
- every transformation at Proxy, JCode, relay, bridge, and provider boundaries,
  with before/after hashes and a field-loss decision.

After response, the receipt MUST add complete raw bytes, streamed deltas,
reconstructed/native/text tool calls, parser decisions, rejected calls, tool
authorization, executions, returned results, retries, final claim, and
independent evaluation. Missing exact bytes MUST be labeled
`EVIDENCE_INCOMPLETE`; reconstruction is forbidden and the run cannot qualify.

## 3. Tool Compatibility Profiles

Profiles are exact-model-and-digest specific. A profile MUST define expected
native and text dialects, streaming assembly, parser, schema/path validation,
tool-result role/name mapping, recovery prompts, latency/context budget, and
known limitations.

### Qwen 7B Profile

- Identity: `qwen2.5-coder:7b`, digest
  `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.
- Direct baseline: Task R PASS; Task W PASS.
- Observed tool dialect: bare or fenced assistant-text JSON calls, not native
  Ollama/OpenAI `tool_calls`.
- Required parser: retain native support and add exact bare/fenced JSON recovery
  for declared tools only. Validate schema and path before execution.
- Recovery: preserve prior messages; return the exact tool result; allow no
  task/context change and no more than three total turns.
- Current outcome: `MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS`.

### Qwen 14B Profile

- Identity: `qwen2.5-coder:14b`, digest
  `9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849`.
- Direct baseline: Task R PASS. Task W model output is behaviorally correct but
  requires evaluator alignment before the direct baseline is formally closed.
- Observed tool dialect: assistant-text JSON calls, not native tool calls.
- Required parser/recovery: same as 7B, plus a qualified latency/context budget
  that does not treat a provider timeout as model incapability.
- Current outcome: `MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS`.

The current JCode tool set is incomplete for write tasks because it lacks the
sealed focused-test tool. No profile can be ready until that tool and result
reinjection are proven.

## 4. Context Quality Gate

For each qualification run all conditions MUST pass:

- critical source presence: 100 percent;
- critical test/support presence: 100 percent;
- path consistency between packet, mount, and tool dispatcher: 100 percent;
- critical-file truncation: zero bytes, or an independently proven noncritical
  omission explicitly accepted by the task manifest;
- relevant-context ratio: at least 0.40 for the bounded qualification tasks;
- task objective and acceptance criteria: both begin within the first 1,024
  model-visible bytes and precede source/context bodies;
- unrelated campaign/governance markers in the model-visible coder body: zero;
- every included tool is required by the task and every required capability is
  exposed;
- input tokens plus 1,024 output tokens plus 256 safety tokens do not exceed
  the selected profile's context limit;
- exact truncation/allocation receipt: present and complete.

Any failure yields `PIPELINE_NOT_READY_FOR_COMPARISON`.

## 5. Agent-Loop Recovery Gate

The loop MUST:

1. Parse either a native allowed call or the model profile's exact bounded text
   convention.
2. Authorize paths/commands before execution and return denials/errors to the
   model under the expected role and tool name.
3. After every productive read, preserve all prior messages and reinject the
   exact observation before deciding completion.
4. When the model requests files already mounted, remind it of the existing
   read tool without changing task, context, criteria, files, or expected
   answer.
5. Retry only for parser/recovery/verification reasons defined before the run;
   never tune a retry to observed task content.
6. Stop truthfully at three total model turns, retaining every failed attempt.
7. Require a valid final answer for read tasks and a scoped diff plus passing
   focused test for write tasks.

The current baseline loop fails item 3. Current JCode/Qwen profiles fail item 1.

## 6. Direct Capability Baseline

Before expensive campaign execution, each exact model/digest and task class
MUST pass a new immutable, non-benchmark inline task containing all relevant
source, test, and criteria. No tools are used and no candidate is applied.

Raw capability and tool compatibility are separate gates. A raw failure may
limit/disqualify a model for that task class only after the evaluator is proven
behaviorally aligned. A tool failure MUST NOT be labeled model incapability
when the direct baseline passes.

## 7. Campaign Advancement Rule

Gate 2-J.9J, Gate 2-J.9K, the sealed 20-task diagnostics, the 80-run comparison,
and Campaign 4 MUST remain blocked until all selected task classes receive:

- `SYSTEM_PACKET_READY`;
- `JCODE_TOOL_COMPATIBILITY_READY`; and
- `MODEL_PROFILE_READY` for every selected exact model/digest.

The decision outcomes are:

- `SYSTEM_PACKET_READY`: packet and context gates pass with complete receipts.
- `JCODE_TOOL_COMPATIBILITY_READY`: roles/tools survive every boundary and the
  bounded read/edit/test/reinjection loop passes.
- `MODEL_PROFILE_READY`: direct capability and separate tool compatibility pass
  for one exact model/digest and task class.
- `MODEL_LIMITED_TO_READ_ONLY`: read profile passes while a proven raw write
  baseline fails with a valid evaluator.
- `MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS`: direct capability may pass, but tool
  dialect/parser/execution qualification does not.
- `PIPELINE_NOT_READY_FOR_COMPARISON`: any required packet, JCode, evidence, or
  selected profile gate remains open.

## 8. Anti-Cheating Rules

- no frozen benchmark task, fixture, oracle, or hidden expectation;
- no task-specific prompt, parser branch, retry, or expected patch;
- no answer leakage into model-visible context;
- no cross-run session, memory, output, or response reuse;
- identical immutable tasks/context across paired model and lane comparisons;
- fresh worktree, overlay, HOME, `JCODE_HOME`, and session per run;
- exact model/digest and no fallback/substitution;
- immutable manifests sealed before requests;
- independent evaluator with behaviorally valid expectations;
- all failed and incomplete runs retained.

## 9. Existing Gate Status

Retained without expansion:

- Gates 2-J.9B through 2-J.9E Batch 1;
- Runtime Gates 2-J.9G-D through 2-J.9H technical acceptance;
- Gate 2-J.9I containment/safety-path finding and its no-unauthorized-mutation
  evidence.

Gate 2-J.9I's statement that the observed no-tool result established a model
quality failure is refined: the raw response bytes were not retained and this
audit proves the bridge did not expose tools to the provider. It MUST NOT be
used as evidence of model incapability. The safety-path acceptance remains
unchanged.

Blocked or unstarted:

- Gate 2-J.9T qualification itself;
- Gate 2-J.9J;
- Gate 2-J.9K;
- sealed 20-task diagnostics;
- 80-run comparison;
- Campaign 4 advancement.

No gate is automatically unpaused by this amendment.
