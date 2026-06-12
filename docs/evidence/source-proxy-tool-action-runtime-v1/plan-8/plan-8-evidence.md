# Source Proxy Tool Action Runtime v1 Plan 8 Evidence

Plan: Plan 8/8: Benchmark Return Gate And Comparison Rerun Packet.

Status: benchmark-return artifacts created and schema-validated. No benchmark, stress test, provider/model call, route change, or comparison execution occurred in Plan 8.

## Phase 8.1 Return Gate

Implemented:

- `benchmark-return-packet.json`
  - Confirms TaskSpec intake gate.
  - Confirms tool/action contract gate.
  - Confirms executor and receipt gate.
  - Confirms Mac/subagent advisory boundary gate.
  - Confirms UI diagnostics gate with the Plan 6 live-smoke residual risk stated explicitly.
  - Confirms Plan 7 trap-suite gate.
  - States `benchmark_execution_in_plan_8: false`.
  - States `provider_or_model_calls_in_plan_8: false`.

Evidence:

- Plans 1 through 7 have closeout artifacts under `docs/evidence/source-proxy-tool-action-runtime-v1/`.
- Artifact schema validation passed.
- Benchmark-return grep found no hidden benchmark execution claim.

GO/NO-GO: GO for the return-gate packet. NO-GO for benchmark execution in Plan 8.

## Phase 8.2 Comparison Matrix

Implemented:

- `comparison-matrix-packet.json`
  - Defines Source Proxy + Qwen.
  - Defines Source Proxy + Hermes/Gemma as available.
  - Defines Aider + local model.
  - Defines Continue + local model.
  - Defines raw local model harness.
  - Defines Codex/manual lane if safe.
  - Defines cloud API lanes as blocked until explicit cloud approval.
  - Requires availability checks before execution.
  - Requires provider approval before execution.
  - Sets `execution_allowed_in_plan_8: false` for every lane.

Evidence:

- Schema validation asserts every lane has `execution_allowed_in_plan_8: false`.
- Matrix requires same prompt bank, same disposable workspace rule, and same receipt requirements.

GO/NO-GO: GO for comparison planning packet. NO-GO for executing comparisons in Plan 8.

## Phase 8.3 Benchmark Fairness

Implemented:

- `benchmark-fairness-packet.json`
  - Requires same prompt bank.
  - Requires same disposable workspace rule.
  - Requires same anti-cheat classification.
  - Requires path trace, diff, and receipt evidence.
  - Separates model failure from wrapper failure.
  - Lists no-go conditions including hidden mutation, real app mutation, provider/model calls without approval, cloud lanes without approval, safe apply, commit/push, Cartographer mutation, and Mac/subagent write authority.

Evidence:

- Schema validation asserts anti-cheat hidden mutation rule is present.
- Grep confirms `backend-created task answer`, `hidden scaffold or hidden mutation`, and `wrapper_failed` language.

GO/NO-GO: GO for fairness packet.

## Phase 8.4 Closeout

Implemented:

- Benchmark-return packet produced.
- Stress testing decision stated as `go_for_next_approved_plan_only`.
- Next comparison plan title only: `Source Proxy Tool Action Runtime v1: Approved Benchmark Comparison Rerun`.

Evidence:

- Artifact schema validation passed.
- `git diff --check` passed.
- Final closeout records no benchmark execution and no provider/model calls.

GO/NO-GO: GO for Plan 8 closeout. NO-GO for running the next comparison plan in this turn.

## Checks

Executed from `Z:\` PowerShell against `/home/source/SpiritOS`:

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python - <<'PY'
import json
from pathlib import Path
base = Path('docs/evidence/source-proxy-tool-action-runtime-v1/plan-8')
required = {
    'benchmark-return-packet.json': ['artifact_type','schema_version','status','benchmark_execution_in_plan_8','provider_or_model_calls_in_plan_8','native_hands_gate','stress_testing_decision','next_plan_title_only'],
    'comparison-matrix-packet.json': ['artifact_type','schema_version','status','same_prompt_bank_required','comparison_lanes','minimum_artifacts_per_trial'],
    'benchmark-fairness-packet.json': ['artifact_type','schema_version','status','same_prompt_bank','same_anti_cheat_classification','model_failed_vs_wrapper_failed','no_go_conditions'],
}
for name, keys in required.items():
    data = json.loads((base / name).read_text(encoding='utf-8'))
    missing = [key for key in keys if key not in data]
    assert not missing, (name, missing)
    assert data['schema_version'] == 1, name
    if name == 'benchmark-return-packet.json':
        assert data['benchmark_execution_in_plan_8'] is False
        assert data['provider_or_model_calls_in_plan_8'] is False
        gates = data['native_hands_gate']['gates']
        assert len(gates) == 6
        assert all(gate['status'].startswith('go') for gate in gates)
    if name == 'comparison-matrix-packet.json':
        assert all(lane['execution_allowed_in_plan_8'] is False for lane in data['comparison_lanes'])
        assert data['same_prompt_bank_required'] is True
    if name == 'benchmark-fairness-packet.json':
        assert 'hidden scaffold or hidden mutation' in data['same_anti_cheat_classification']['cheating']
print('plan8 artifact schema validation passed')
PY"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && grep -R -n -E 'benchmark_execution_in_plan_8|provider_or_model_calls_in_plan_8|same_prompt_bank|required|hidden mutation|backend-created|wrapper_failed|go_for_next_approved_plan_only|blocked_until_explicit_cloud_approval' docs/evidence/source-proxy-tool-action-runtime-v1/plan-8 | sed -n '1,220p'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check"
```

Results:

- Artifact schema validation: `plan8 artifact schema validation passed`.
- Benchmark/fairness grep: expected packet lines present.
- `git diff --check`: passed.

Final combined checks are recorded in the Plan 8 closeout.

## Forbidden Scope Avoided

- No benchmark rerun.
- No stress test.
- No provider/model calls.
- No route changes.
- No cloud lane execution.
- No safe apply to the real repo.
- No real app mutation.
- No Cartographer mutation.
- No Mac/subagent write authority.
- No hidden workers.
- No branch, worktree, stash, reset, checkout, clean, commit, or push.
