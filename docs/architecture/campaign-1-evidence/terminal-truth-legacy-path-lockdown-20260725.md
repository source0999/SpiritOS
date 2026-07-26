# Campaign 1 Terminal Truth and Legacy Path Lockdown

Status: `IMPLEMENTED_PENDING_OPERATOR_REVIEW`

Campaign 1 product scope is Source Proxy. This record is an implementation
inventory for the worktree
`/home/source/SpiritOS-source-proxy-campaign-1-terminal-truth-20260726` on
`codex/source-proxy-campaign-1-terminal-truth-20260726`. It starts from the
accepted Campaign 0 commit `bbe195111e202afe8610cd02adf528f0e92857c7`.

## Canonical contract

`source_proxy/tasks/terminal_truth.py` owns the versioned
`source-proxy.terminal-truth/v1` vocabulary, transition table, sealed-payload
digest, and report-upgrade rejection. A terminal receipt contains the prior
state, transition owner, producer, reason, Coder invocation evidence, artifact
digest, verifier receipt, and its own SHA-256 binding.

`completed_verified` is accepted only through
`verified_completion_truth`: the production proof must be terminal-eligible,
every required independent participant must pass, and the exact artifact and
verifier receipt must be present. A sidecar, report, narration, marker, or
late event cannot create that state.

## Terminal-path matrix

| Path | Producer | Authority | Mutation possible | Completion possible | Independent verification required | Current risk | Required disposition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Authenticated participant finalization | Coding orchestrator | Campaign approval plus production proof | Yes | Yes | Yes | Completion becomes `completed_verified` only with exact artifact and verifier receipt. |
| `/execute-approved` safety preview | Long-running task service | Durable approval | Yes | No | n/a | Unverified applies could be mistaken for completion. | Blocked previews seal `blocked_policy`; successful applies remain pending verification. |
| `/verify` post-apply check | Long-running task service | Canonical finalizer | Yes | No | Yes | Passing checks alone lack full participant proof. | Remain `verification_passed_pending_participants` until canonical finalization. |
| `/advance` legacy Architect/Coder/debugger | Long-running task service | Compatibility-only | Yes | No | Yes | Debugger return code previously marked `completed`. | Stops at pending participant finalization. |
| Fallback or Hermes recovery | Coding orchestrator | Coding orchestrator transition owner | Yes | No | Yes | Narration or partial evidence could imply success. | Pre-Coder block is `not_attempted`; model failure is `blocked_environment`. |
| Participant verifier failure | Coding orchestrator | Coding orchestrator transition owner | Yes | No | Yes | A later report could upgrade a failed attempt. | Seals `verification_failed`; late success is rejected. |
| Cancellation | Long-running task service | Task owner | Yes | No | n/a | Cancellation could be overwritten by a delayed event. | Seals `cancelled` with provenance. |
| Restart/replay | Coding orchestrator receipt restore | Digest validator | Yes | No | Yes | Tampered receipt could resume with altered truth. | Invalid terminal digest is rejected before restore. |
| `/extended-lanes` recovery | Campaign 3 integration recorder | Advisory only | Snapshot only | No | n/a | Advisory `BLOCKED_ENV` previously could poison core state. | Retain receipt but forbid core status mutation. |
| Report or benchmark adapter | Terminal-truth reducer | Producer state | No | No | Yes | Normalizer could infer verified success. | Preserve source state; reject attempted upgrades. |

| Producer or consumer path | Campaign 1 disposition |
| --- | --- |
| Orchestrated participant finalization | `completed_verified` only after durable production proof and independent verifier receipt. |
| Participant failure finalization | Seals `verification_failed`; later success transitions are rejected. |
| Approved-diff safety block | Seals `blocked_policy` with `approved_diff_blocked`. |
| Post-apply verification failure | Seals `verification_failed` with `post_apply_verification_failed`. |
| Operator cancellation | Seals `cancelled` with `operator_cancelled`. |
| Pre-Coder fallback block | Seals `not_attempted`; no Coder invocation is implied. |
| Model/fallback failure | Seals `blocked_environment`, retaining the actual invocation identities. |
| Legacy architect/Coder/debugger advance | Compatibility-only: it now stops at `verification_passed_pending_participants`, never `completed`. |
| Extended-lane recovery | Advisory-only: it retains an attributed `BLOCKED_ENV` receipt but cannot change canonical task status. |
| Task and orchestrator receipts | Expose the sealed `terminal_truth` payload; restart rejects a tampered orchestrator truth payload. |
| Report-side status normalization | `reject_report_upgrade` preserves source state and records `report_upgrade_rejected`. |

## Compatibility policy

No legacy mutation route is permitted to convert its own debugger or sandbox
result into completion. The remaining legacy advance route can produce a
verified diff as local evidence, but it must hand off to canonical independent
participant finalization. Existing read-only status consumers receive a
versioned payload; `commit_safe` remains false until `completed_verified`.

The Campaign 1 implementation does not alter benchmark task selection or
private-oracle inputs. Existing benchmark code remains diagnostic-only and is
not a completion authority for Source Proxy task receipts.

## Required truth regressions

| Case | Evidence in focused tests |
| --- | --- |
| BT05/no Coder attempt | `test_generic_fallback_pre_coder_block_preserves_reason_and_sanitized_provenance` asserts `not_attempted`. |
| BT06/verifier rejection | `test_terminal_truth_transition_table_seals_terminal_failures` asserts the verifier-failure seal cannot be upgraded. |
| BT07/fallback fabrication | `test_completed_verified_requires_independent_artifact_and_verifier` rejects incomplete fallback claims; the fallback block test preserves its true state. |
| Duplicate or late success | The transition-table test rejects a late `completed_verified` event after a sealed failure. |
| Cancellation | `test_router_can_cancel_task` asserts a durable `cancelled` receipt. |
| Restart integrity | `test_sealed_repair_attempt_resumes_without_reusing_or_refinalizing_approval` and receipt-digest validation preserve attempt lineage. |
| Legacy completion bypass | `test_swarm_handoff_keeps_legacy_debugger_output_pending_canonical_finalization` asserts the compatibility handoff cannot complete a task. |
| Extended-lane poisoning | `test_extended_lane_failure_is_advisory_to_canonical_task_state` preserves the core task state while retaining the lane receipt. |

Campaign 1 is intentionally not self-accepted. Operator acceptance must review
the final validation receipts, the known pre-existing isolated fixture failure,
and the scoped diff before issuing `C1_CAMPAIGN_READY_FOR_OPERATOR_ACCEPTANCE`.
