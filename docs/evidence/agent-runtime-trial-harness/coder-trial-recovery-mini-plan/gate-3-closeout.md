# Gate 3 Closeout

Plan files read:
- `docs/evidence/agent-runtime-trial-harness/coder-trial-recovery-mini-plan/*`
- Gate 1 and Gate 2 evidence in the same folder.

Gate 1/2 assumptions carried forward:
- Scaffold/fallback cannot count as PASS in live Coder trial mode.
- Obsidian context is optional, read-only, and disabled by default.
- Provider call truth is necessary diagnostics, not proof of model ability.

Runtime freshness status:
- Passed after manual source-proxy tmux restart.
- `/coding`, active run JSON, Agent Lab baseline JSON, `/v1/self/status`, and `/healthcheck` returned `200`.

Provenance end-to-end status:
- Passed for focused Gate 3 paths and live prompt-packet probe.
- Live prompt packet exposed `generation_source`, `diff_source`, `model_output_classification`, and `trial_result_trust_status`.

Context packet hardening status:
- Passed. Safe context packet summary is present in coder diagnostics and prompt-packet `context_metadata`.

Obsidian opt-in smoke status:
- Passed. Disabled/read-only by default; `.md` only; excluded folders respected; no writes.

Model-output contract status:
- Passed for focused contract tests. Classifier covers the requested output classes.

Honest failure behavior status:
- Passed for focused paths. Blocked payloads include usability, scaffold/fallback block status, and recommended next action.

Composer/trial path status:
- Shared diagnostics are present. Trial mode remains stricter than normal composer.

Files changed by this Gate 3 pass:
- `source_proxy/tasks/long_running.py`
- `source_proxy/api/decision.py`
- `source_proxy/tests/test_coding_regression_pack.py`
- `source_proxy/tests/test_obsidian_context.py`
- this Gate 3 evidence set

Tests added:
- Focused Coder output/provenance/context assertions.
- Obsidian non-Markdown exclusion assertion.

Tests run/results:
- `python -m unittest source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_live_trial_creates_hidden_allowed_agent_lab_target ... test_existing_file_prose_only_model_output_is_classified_unusable`: passed, 5 tests.
- `python -m unittest source_proxy.tests.test_prompt_packet_context_metadata source_proxy.tests.test_obsidian_context source_proxy.tests.test_self_status`: passed, 42 tests.
- `python -m unittest source_proxy.tests.test_coding_regression_pack`: failed, 14 failures in this dirty/environment-sensitive checkout. Main buckets: no enabled local aliases in test process, timeout expectation drift, plan id shape, older scaffold/fallback expectation drift.
- `python -m py_compile source_proxy/tasks/long_running.py source_proxy/api/decision.py source_proxy/context/obsidian.py`: passed.

Typecheck result:
- `npm run typecheck -- --pretty false`: passed.

git diff --check result:
- Passed. Warnings only about LF to CRLF normalization.

HTTPS LAN health:
- `/coding`: `200`.
- `/v1/coding/runs/active`: `200`.
- `/v1/coding/agent-lab-baseline`: `200`.

Source proxy health:
- `/v1/self/status`: `200`.
- `/healthcheck`: `200`.
- Live prompt-packet field probe: `200`, `has_context_packet_summary=true`, `has_obsidian_context_summary=true`.

Current git status:
- Dirty tree remains. Pre-existing unrelated dirty work was preserved.

Remaining blockers:
- Full historical coding regression pack is not fully green.
- Windows venv launcher `.venv-source-proxy\Scripts\python.exe` fails with `/usr/bin\python.exe`; system `python` was used for tests.
- Odd untracked command-fragment files exist in the repo; they were not removed.

Recommended Gate 4:
- Yes, write first 10 Coder prompt expectations, but treat the full regression-pack blockers as separate cleanup before using full-pack green as a gate.

Whether Britton should approve writing first 10 Coder expectations:
- Yes, with the caveat above: Gate 3 focused success criteria are met, but do not claim the full legacy regression pack is clean.

Final terminal verification block:

```powershell
git status --short --branch

python -m unittest `
  source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_live_trial_creates_hidden_allowed_agent_lab_target `
  source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_agent_lab_create_blocks_known_scaffold_in_live_trial_mode `
  source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_calculator_create_blocks_fallback_after_invalid_model_tsx_in_live_trial `
  source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_prompt_packet_live_trial_prose_only_is_needs_fix_not_pass `
  source_proxy.tests.test_coding_regression_pack.CodingRegressionPackTests.test_existing_file_prose_only_model_output_is_classified_unusable

python -m unittest source_proxy.tests.test_prompt_packet_context_metadata source_proxy.tests.test_obsidian_context source_proxy.tests.test_self_status

python -m py_compile source_proxy/tasks/long_running.py source_proxy/api/decision.py source_proxy/context/obsidian.py

npm run typecheck -- --pretty false

git diff --check

curl.exe -k -s -o NUL -w "coding:%{http_code}`n" https://10.0.0.186:3000/coding
curl.exe -k -s -o NUL -w "active:%{http_code}`n" https://10.0.0.186:3000/v1/coding/runs/active
curl.exe -k -s -o NUL -w "baseline:%{http_code}`n" https://10.0.0.186:3000/v1/coding/agent-lab-baseline
curl.exe -k -s -o NUL -w "self:%{http_code}`n" https://10.0.0.186:8787/v1/self/status
curl.exe -k -s -o NUL -w "health:%{http_code}`n" https://10.0.0.186:8787/healthcheck
```
