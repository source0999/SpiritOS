# Campaign 0 Segment 0B - 6616846d Disposition Ledger

status: `SEGMENT_0B_DISPOSITION_LEDGER`

This ledger preserves `6616846d7584af0318fe18fbaf7c3b1195ea03b0` as immutable
candidate work. No production source change from `6616846d` is accepted,
cherry-picked, copied, or pushed onto the Campaign 0 authoritative-base branch
by this ledger.

Comparison range:
`ede643c7e18535125efde807d5937f265dcc75f9..6616846d7584af0318fe18fbaf7c3b1195ea03b0`

Summary: 11 changed files; 1,985 insertions; 23 deletions.

## Disposition Table

| Path | Classification | Affected symbols | Intended generalized value | Known tests | Relationship to LumaCart | Regression risk | Dependencies | Evidence still required | Segment 0C decision point |
|---|---|---|---|---|---|---|---|---|---|
| `docs/evidence/campaign-3.5-basic-backend-10/milestone-13-repair-evidence-20260723.md` | `ARCHIVE_ONLY` | evidence prose only | Preserve historical Campaign 3.5 repair narrative and negative evidence | none; prose evidence | Indirect; records failed/repair context but does not repair LumaCart | Low source risk; high acceptance risk if mistaken for proof | Existing Campaign 3.5 evidence roots | Confirm it is not used as Campaign 0 acceptance evidence | Archive as reference after LumaCart reproduction |
| `source_proxy/benchmarks/campaign_3_5_basic_gate_runner.py` | `REPAIR_BEFORE_CARRY` | `BasicBackendGateRunner`, `_non_mutating_terminal_outcome_valid`, proposal material/status handling | Harden non-mutating terminal disposition and repair-success truth | `source_proxy/tests/test_campaign_3_5_basic_gate_runner.py` additions | Indirect; terminal-truth work could affect how LumaCart/BT failures are represented | High: benchmark authority and terminal reporting | Lifecycle API shape, proposal state, approval state | Re-run focused runner tests and verify no scorer weakening or status inflation | Decide after LumaCart root cause and terminal-disposition checks |
| `source_proxy/coding/orchestrator.py` | `REPAIR_BEFORE_CARRY` | repair path near `CodingOrchestrator`, `_is_truthful_non_mutating_target_result`, `_is_non_mutating_noop_target_result` | Preserve truthful no-op/non-mutating repair behavior without declaring false success | `source_proxy/tests/test_coding_orchestrator.py` additions | Potentially relevant only if LumaCart reaches repair/no-op paths; does not address known semantic binding raise directly | High: core lifecycle behavior | Repair request schema, target-plugin proposal result semantics | Reproduce LumaCart first; prove any carry is generalized and not fixture-specific | Evaluate after LumaCart reproduction and focused orchestrator tests |
| `source_proxy/planning/architect.py` | `REIMPLEMENT_AFTER_ROOT_CAUSE` | `_plan_explicit_shared_helper_refactor_deterministically`, `_shared_refactor_source_symbols`, `_deterministic_shared_helper_artifact_path` | Improve deterministic shared-helper planning and artifact path selection | `source_proxy/tests/test_architect_deterministic.py` additions | No direct relationship observed; may affect BT07/shared-helper class, not LumaCart anchor | Medium/high: deterministic planning may overfit prompt shape | Workspace scope/path validation, unsafe target finding | Establish whether Segment 0C needs this logic at all; verify against non-LumaCart tasks | Reimplement or defer after root cause, not before |
| `source_proxy/planning/reviewer.py` | `REIMPLEMENT_AFTER_ROOT_CAUSE` | `review_diff_deterministically`, `_review_python_shared_helper_contract`, `_python_calls_to_helper_module`, AST helper collectors | Add AST-backed reviewer proof for shared-helper contracts | `source_proxy/tests/test_reviewer_deterministic.py` additions | No direct relationship observed; likely BT07/shared-helper validation, not LumaCart binding | High: large reviewer logic can weaken/alter review outcomes | Python AST parsing, review criteria schema, artifact snapshots | Prove reviewer standards are preserved and no LumaCart special case exists | Evaluate only after LumaCart fix path is known |
| `source_proxy/target_plugins/generic_workspace.py` | `UNKNOWN_REQUIRES_0C_TESTING` | `_multi_file_capability_prompt_lines` | Small prompt capability wording adjustment for multi-file/shared-helper work | `source_proxy/tests/test_generic_workspace_multifile.py` additions | No direct relationship observed | Medium: prompt wording can alter model behavior | Architect/reviewer shared-helper expectations | Diff exact wording and test whether required for generalized repair | Decide after unrelated-path tests |
| `source_proxy/tests/test_architect_deterministic.py` | `CARRY_FORWARD_CANDIDATE` | deterministic architect shared-helper tests | Preserve regression coverage if architect logic is later carried/reimplemented | test file itself | No direct LumaCart relationship | Low as tests; risk if assertions encode overfit behavior | `source_proxy/planning/architect.py` | Confirm tests fail before corresponding accepted implementation and pass after generalized logic | Decide with architect disposition |
| `source_proxy/tests/test_campaign_3_5_basic_gate_runner.py` | `CARRY_FORWARD_CANDIDATE` | `FakeLifecycleClient`, non-mutating terminal proposal tests | Preserve terminal truth regression coverage | test file itself | Indirect terminal-disposition relationship | Low as tests; risk if asserts 3.5-only behavior | `source_proxy/benchmarks/campaign_3_5_basic_gate_runner.py` | Verify tests remain relevant to Campaign 0 receipt/identity boundaries | Decide with runner disposition |
| `source_proxy/tests/test_coding_orchestrator.py` | `CARRY_FORWARD_CANDIDATE` | repair/no-progress orchestrator tests | Preserve lifecycle no-op and no-progress coverage | test file itself | Potentially related if LumaCart repair path enters no-op behavior | Low as tests; risk if target-specific | `source_proxy/coding/orchestrator.py` | Confirm failing-before/passing-after behavior on accepted generalized repair | Decide with orchestrator disposition |
| `source_proxy/tests/test_generic_workspace_multifile.py` | `CARRY_FORWARD_CANDIDATE` | multi-file/shared-helper target-plugin tests | Preserve proof for generic workspace multi-file behavior | test file itself | No direct LumaCart relationship | Low as tests; medium if fixture-specific | `source_proxy/target_plugins/generic_workspace.py` | Confirm applicability after root-cause work | Decide with generic workspace disposition |
| `source_proxy/tests/test_reviewer_deterministic.py` | `CARRY_FORWARD_CANDIDATE` | AST-backed reviewer helper contract tests | Preserve reviewer proof if reviewer logic is accepted or reimplemented | test file itself | No direct LumaCart relationship | Low as tests; risk if tests bless weakened standards | `source_proxy/planning/reviewer.py` | Confirm tests enforce stricter review, not easier acceptance | Decide with reviewer disposition |

## Segment 0C Evidence Requirements

- Reproduce LumaCart on the isolated Campaign 0 branch before any production
  repair.
- Identify whether the root cause is semantic-review binding, fixture shape,
  path/scope normalization, lifecycle repair behavior, or another generalized
  defect.
- Run focused tests for any accepted carry-forward candidate.
- Run unrelated-path checks to reject LumaCart-specific or prompt-specific
  overfitting.
- Preserve negative evidence and record any rejected `6616846d` changes.
