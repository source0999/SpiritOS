# TERRA_HIGH_GATE_2J_9T_HANDOFF.md

Gate-by-gate implementation handoff for Terra High under Gate 2-J.9T. The
controlling spec is `PACKET_AMENDMENT.md`. Terra High works ONLY under a new
prospective operator authorization for a bounded sub-gate batch.

## Bounded autonomy

Terra High may use bounded autonomy for ordinary implementation defects INSIDE
an already-authorized sub-gate. Terra High MUST STOP and request authorization
for: model/provider expansion; new write scope; network expansion; containment
weakening; benchmark access; campaign advancement; missing evidence; scope
ambiguity.

## Sub-gate sequence (dependency-ordered)

| Sub-gate | Objective | Requests | Deliverables |
| --- | --- | --- | --- |
| 2-J.9T-A | Canonical packet schema + packet-quality validator | none | MODEL_READY_PACKET_SCHEMA validator; packet-noise analyzer; unit tests on fixtures |
| 2-J.9T-B | Chat-preserving bridge contract | fake backend only | bridge that preserves roles/tools/tool_choice via /api/chat; fake-backend contract tests |
| 2-J.9T-C | Native/textual tool normalizer | deterministic fixtures only | normalizer per TOOL_DIALECT_NORMALIZATION_SCHEMA; tests for native, bare JSON, fenced JSON, malformed, multi-call |
| 2-J.9T-D | Observation reinjection + bounded agent loop | fake model/tool fixtures first | loop per AGENT_LOOP_CONTRACT; reinjection + recovery tests; fixes the Lane-C exit defect |
| -> GLM review (Batch 1) | | | |
| 2-J.9T-E | Focused-test tool + evaluator alignment | qualification fixture only | sealed focused_test tool; behaviorally-aligned evaluator; 14B re.sub now passes |
| 2-J.9T-F | Qwen model compatibility profiles | small real-model diagnostics | QWEN_7B/14B profiles; parser proven on real Qwen text dialect |
| 2-J.9T-G | Baseline harness qualification | minimal + corrected packets | BASELINE_HARNESS_READY; read+reinject+answer; write+diff+test |
| 2-J.9T-H | JCode compatibility qualification | minimal + corrected packets | JCODE_HARNESS_READY; sealed prompt; corrected bridge+parser+loop+test tool |
| -> GLM review (Batch 2) | | | |
| 2-J.9T-I | Independent readiness review | none (no automatic comparison start) | decision: accept/block; READY_FOR_BOUNDED_COMPARISON_REVIEW |

## Per-sub-gate required fields

Each sub-gate deliverable records: objective; dependencies; allowed files;
forbidden files; implementation requirements; tests; controlled failures;
evidence; acceptance; stop condition; commit policy; next authorized action.

## Stop boundaries (do NOT cross without authorization)

- Do NOT start 2-J.9J/9K.
- Do NOT run the 20-task diagnostics or 80-run comparison.
- Do NOT change production defaults (legacy bridge stays default until
  qualification).
- Do NOT access frozen benchmarks.
- Do NOT weaken containment, network policy, or model binding.
- Do NOT merge to the canonical Campaign 2-J branch.

## First authorized batch

`Operator review and adoption of PACKET_AMENDMENT.md, followed by a prospective
Terra High authorization for Gate 2-J.9T-A through Gate 2-J.9T-D only.`
