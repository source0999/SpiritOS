# PACKET_READINESS_ACCEPTANCE_MATRIX.md

PASS/FAIL acceptance matrix for Gate 2-J.9T. Each rule is an independent gate;
ALL must pass for `PACKET_READY`. Relevant-context ratio alone is not a quality
measure (a packet can satisfy >=0.40 while omitting a critical test or leaking
an answer).

## Packet readiness rules

| Rule | Threshold | PASS condition | FAIL consequence | Evidence basis |
| --- | --- | --- | --- | --- |
| relevant_context_ratio | >= 0.40 | minimal-packet floor ~0.455 measured | PIPELINE_NOT_READY | R/W minimal vs full receipts |
| first_critical_content_position | task + acceptance within first 1024 bytes | minimal at byte 26 | PIPELINE_NOT_READY | full packets bury task at ~5807/~6663 |
| unrelated_governance_markers | 0 | minimal 0 | PIPELINE_NOT_READY | full packets have 12 |
| critical_source_test_presence | 100% files/bytes | verified | PIPELINE_NOT_READY | Lane E failure was burial, not missing content |
| path_consistency_packet_mount_dispatcher | 100% | all diagnostic receipts true | PIPELINE_NOT_READY | must be preserved |
| critical_truncation_bytes | 0 (or proven-noncritical omission with receipt) | receipt present | PIPELINE_NOT_READY | production 6000-char silent slice; E7 4147->4096 |
| contradictory_instructions | 0 | task-aligned prompt | PIPELINE_NOT_READY | JCode 2004-char prompt conflicts with sealed task |
| hidden_answer_leakage | 0 | verified | PIPELINE_NOT_READY | full packets did not expose answers |
| deterministic_packet_reproduction | byte-identical recomputation | yes | PIPELINE_NOT_READY | anti-cheat/reproducibility |
| paired_lane_packet_identity | identical canonical bytes | yes | PIPELINE_NOT_READY | fair comparison |
| context_output_budget_sufficiency | input + 1024 output + 256 safety <= profile context limit | yes | PIPELINE_NOT_READY | failures must not be labeled model incapability |

## Component readiness matrix

| Outcome | Sub-gate that proves it | Current status |
| --- | --- | --- |
| PACKET_READY | 2-J.9T-A | NOT_READY (<2% relevant, task buried) |
| BRIDGE_READY | 2-J.9T-B | NOT_READY (legacy drops roles/tools; corrected profile diagnostic-only) |
| TOOL_DIALECT_READY | 2-J.9T-C | NOT_READY (text dialect unparseable) |
| AGENT_LOOP_READY | 2-J.9T-D | NOT_READY (reinjection defect proven) |
| FOCUSED_TEST_TOOL_READY | 2-J.9T-E | NOT_READY (no bounded test tool in JCode) |
| EVALUATOR_READY | 2-J.9T-E | NOT_READY (AST overconstraint rejects correct code) |
| QWEN_7B_PROFILE_READY | 2-J.9T-F | NOT_READY (MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS) |
| QWEN_14B_PROFILE_READY | 2-J.9T-F | NOT_READY (MODEL_NOT_QUALIFIED_FOR_TOOL_TASKS) |
| BASELINE_HARNESS_READY | 2-J.9T-G | NOT_READY (reinjection defect) |
| JCODE_HARNESS_READY | 2-J.9T-H | NOT_READY (prompt/bridge/parser/test-tool) |
| READY_FOR_BOUNDED_COMPARISON_REVIEW | 2-J.9T-I | NOT_READY (all above required first) |

## Advancement gates

| Gate | Requires | Current |
| --- | --- | --- |
| 20-task sealed diagnostics | all readiness outcomes pass + operator authorization | BLOCKED |
| 80-run comparison | independent reviewer accepts 2-J.9T + READY_FOR_BOUNDED_COMPARISON_REVIEW | BLOCKED |
| Campaign 4 | 2-J.9T accepted + 2-J.9J/9K closed | BLOCKED |
| Production JCode promotion | full 2-J.9T pass + explicit production authorization | BLOCKED |
| Production-default bridge change | 2-J.9T qualification pass | BLOCKED |
