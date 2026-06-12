# Source Proxy Tool Action Runtime v1 Plan 5 Evidence

Plan: Plan 5/8: Mac/Subagent Advisory Tool Broker.

Status: implemented and verified.

## Phase 5.1 Capability Manifest

Implemented:

- `source_proxy/decision/advisory_broker.py`
  - Adds `advisory_capability_manifest()` with Source Proxy tool capabilities, Mac advisory capability, subagent advisory capabilities, and diagnostic truth snapshot.
  - Adds `advisory_truth_snapshot()` stating Mac/subagents are advisory only, not executors, cannot write/apply, cannot start hidden workers, cannot change provider routing, cannot mutate Cartographer, and cannot read secrets.

Evidence:

- Manifest test asserts Mac worker is advisory-only with no write/apply authority.
- Manifest test asserts all subagents are advisory-only with no write authority.
- Truth snapshot test asserts Mac/subagents are not presented as executors and Source Proxy remains the final gate.

GO/NO-GO: GO.

## Phase 5.2 Mac Adapter Contract

Implemented:

- `validate_mac_advisory_packet(...)`
  - Accepts bounded advisory packet types: `system_status`, `safe_check`, `repo_context`, `search_packet`, `browser_inspection`, and `design_inspection`.
  - Blocks write/apply/commit/push, hidden worker starts, Cartographer workflow requests, provider route changes, and secret reads.
  - Blocks protected or unsafe references such as `.env.local`.
  - Emits advisory-only validation results; accepted packets cannot execute.

Evidence:

- Safe Mac `repo_context` packet accepts with `advisory_only: true`, `can_write: false`.
- Mac packet requesting `write`, `start_hidden_worker`, and `secret_read` blocks.
- Mac packet referencing `.env.local` blocks with `protected_or_unsafe_ref:.env.local`.

GO/NO-GO: GO.

## Phase 5.3 Subagent Contract

Implemented:

- `validate_subagent_advisory_packet(...)`
  - Supports advisory roles:
    - `component_mapper`
    - `safety_reviewer`
    - `test_scribe`
    - `design_reviewer`
    - `scout_research_helper`
    - `tool_steward`
  - Supports bounded packet types:
    - `component_map`
    - `safety_review`
    - `test_notes`
    - `design_review`
    - `scout_research`
    - `tool_audit`
  - Blocks apply/commit and other forbidden advisory actions.

Evidence:

- Component Mapper packet accepts as advisory context.
- Tool Steward packet requesting `apply` and `commit` blocks.
- Built advisory context packet keeps `source_proxy_final_gate: true`.

GO/NO-GO: GO.

## Phase 5.4 Conflict Handling

Implemented:

- `build_advisory_context_packet(...)` combines accepted and blocked advisory validations.
- `detect_advisory_conflicts(...)` surfaces Safety Reviewer blocks as explicit conflicts.
- Conflicts preserve Source Proxy as final gate and explicitly disallow hidden mutation.

Evidence:

- Safety Reviewer block creates conflict `safety_reviewer_blocks_present`.
- Conflict includes safety block text.
- Conflict has `hidden_mutation_allowed: false` and `source_proxy_final_gate: true`.

GO/NO-GO: GO.

## Checks

Executed from `Z:\` PowerShell against `/home/source/SpiritOS`:

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'advisory'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m py_compile source_proxy/decision/advisory_broker.py"
```

Results:

- Plan 5 advisory slice: `4 passed, 85 deselected`.
- `py_compile`: passed on Dell.

Final combined checks are recorded in the Plan 5 closeout.

## Forbidden Scope Avoided

- No Plan 6 UI integration.
- No Mac write authority.
- No subagent apply/write authority.
- No provider/model calls.
- No benchmark or stress tests.
- No safe apply to the real repo.
- No Cartographer mutation.
- No hidden workers.
- No branch, worktree, stash, reset, checkout, clean, commit, or push.
