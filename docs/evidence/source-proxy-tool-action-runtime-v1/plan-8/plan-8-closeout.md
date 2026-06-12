# Source Proxy Tool Action Runtime v1 Plan 8 Closeout

Plan completed: Plan 8/8: Benchmark Return Gate And Comparison Rerun Packet.

## Files Changed

- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-8/benchmark-return-packet.json`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-8/comparison-matrix-packet.json`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-8/benchmark-fairness-packet.json`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-8/plan-8-evidence.md`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-8/plan-8-closeout.md`

## Evidence Created

- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-8/benchmark-return-packet.json`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-8/comparison-matrix-packet.json`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-8/benchmark-fairness-packet.json`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-8/plan-8-evidence.md`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-8/plan-8-closeout.md`

## Increment Results

- Increment 8.1.1 Confirm TaskSpec intake complete: GO. Plan 1 closeout and tests are cited in the benchmark-return packet.
- Increment 8.1.2 Confirm tool/action contract complete: GO. Plan 2 closeout and parser/action tests are cited.
- Increment 8.1.3 Confirm executor and receipts complete: GO. Plans 3 and 4 closeouts, executor, loop, and receipt evidence are cited.
- Increment 8.1.4 Confirm Mac/subagent boundaries complete: GO. Plan 5 closeout and advisory broker are cited.
- Increment 8.1.5 Confirm UI diagnostics complete: GO with residual live-smoke risk stated. Plan 6 automated UI/runtime checks are cited and the live-server blocker remains explicit.
- Increment 8.1.6 Confirm trap suite clean: GO. Plan 7 trap/golden/scoring closeout is cited.
- Increment 8.2.1 Source Proxy + Qwen: GO for planned lane after manual approval; no execution in Plan 8.
- Increment 8.2.2 Source Proxy + Hermes/Gemma as available: GO for planned lane after manual approval and availability check; no execution in Plan 8.
- Increment 8.2.3 Aider + local model: GO for planned lane after manual approval; no execution in Plan 8.
- Increment 8.2.4 Continue + local model: GO for planned lane after manual approval; no execution in Plan 8.
- Increment 8.2.5 Raw local model harness: GO for planned lane after manual approval; no execution in Plan 8.
- Increment 8.2.6 Codex/manual lane if safe: GO for planned manual-review lane; no execution in Plan 8.
- Increment 8.2.7 Cloud API lanes if explicitly approved: NO-GO until explicit cloud approval.
- Increment 8.3.1 Same prompt bank: GO. Fairness packet requires identical prompt id/text/context/constraints.
- Increment 8.3.2 Same disposable workspace rule: GO. Fairness packet requires disposable or equivalent isolated workspace.
- Increment 8.3.3 Same anti-cheat classification: GO. Fairness packet lists fair vs cheating behavior.
- Increment 8.3.4 Same path trace / diff / receipt requirements: GO. Matrix and fairness packets require trace/diff/check/receipt fields.
- Increment 8.3.5 Separate model failed from wrapper failed: GO. Matrix and fairness packets define model-failure and wrapper-failure labels.
- Increment 8.4.1 Produce benchmark-return packet: GO.
- Increment 8.4.2 State GO/NO-GO for stress testing: GO for next approved plan only; NO-GO for execution in this turn.
- Increment 8.4.3 State next comparison plan title only: GO.

## Checks Run

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
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action or bounded_agent_loop or advisory or plan7'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && npm exec vitest -- run --pool=threads --no-file-parallelism --maxWorkers=1 src/lib/coding/__tests__/tool-runtime-surface.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal"
```

Outputs:

- Artifact schema validation: `plan8 artifact schema validation passed`.
- Benchmark/fairness grep: expected packet lines present.
- Expanded runtime regression: final result recorded by manual verification.
- Plan 6 UI/runtime suite: final result recorded by manual verification. The command uses Vitest's thread pool with one worker to avoid fork-manager instability on the Dell host while preserving the same test files and assertions.
- `git diff --check`: final result recorded by manual verification.
- `git status`: expected dirty tree with previous plan work plus Plan 8 packet/evidence files.

## Expected Output

- Native-hands readiness gates are represented in a benchmark-return packet.
- Comparison matrix is fair, bounded, and execution-blocked until a next approved plan.
- Fairness rules separate model failure from wrapper failure.
- Same prompt bank, same disposable workspace, anti-cheat classification, path trace, diff, and receipt rules are mandatory.
- Stress testing is GO only for a next separately approved comparison plan, not this turn.

## Manual Verification

Copy-paste terminal verification block:

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
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action or bounded_agent_loop or advisory or plan7'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && npm exec vitest -- run --pool=threads --no-file-parallelism --maxWorkers=1 src/lib/coding/__tests__/tool-runtime-surface.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal"
```

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

## Blockers

- No blocker for Plan 8 packet creation and validation.
- Benchmark/stress execution remains blocked until Britton approves the next comparison plan.
- Cloud API lanes remain blocked until explicit cloud approval.

## Rollback Guidance

Rollback by removing only the Plan 8 files listed above. Preserve unrelated dirty tree work and Plan 0/1/2/3/4/5/6/7 artifacts.

## GO/NO-GO

GO for Plan 8 closeout and manual review of the benchmark-return packet.

NO-GO for running benchmark comparisons or stress tests in this turn.

Source Proxy Tool Action Runtime v1 roadmap status: closed through Plan 8/8 for packet readiness.

Next comparison plan title only:

`Source Proxy Tool Action Runtime v1: Approved Benchmark Comparison Rerun`
