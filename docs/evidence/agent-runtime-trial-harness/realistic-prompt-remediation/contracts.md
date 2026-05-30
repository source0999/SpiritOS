# Realistic Prompt Remediation Contracts

Generated: 2026-05-28

## Increment 1.1: Prompt separation contract

Contract source:

- `tests/ui-agent-trials/trial-result-schema.ts`
- `PromptSeparationContract`
- `promptSeparationContractFields`

Required fields:

- `operator_command`: shell command the operator runs.
- `operator_run_request`: human-readable request to run a batch.
- `submitted_prompt`: exact task prompt submitted into the `/coding` composer.
- `prompt_fixture_id`: stable id of the task fixture.
- `prompt_profile`: `britton-realistic` or `clean-control`.
- `submitted_through_ui`: boolean proving the prompt was entered through UI automation.
- `composer_selector_used`: selector Playwright used for the composer.
- `transcript_match`: boolean proving `submitted_prompt` appeared in a truthful UI state.
- `prompt_preview_matches_submitted_prompt`: boolean proving the preview is the task prompt, not the operator prompt.
- `meta_prompt_leak`: boolean that must be false when the submitted prompt is not a batch-run/operator request.

Check run:

```bash
npx --no-install vitest run tests/ui-agent-trials/trial-result-schema.test.ts
```

Result:

- Test files: 1 passed.
- Tests: 2 passed.

GO / NO-GO:

- GO. Contract fields exist and have a targeted schema test.

## Increment 1.2: Blocked/failed diagnostics contract

Contract source:

- `tests/ui-agent-trials/trial-result-schema.ts`
- `TrialDiagnosticContract`
- `trialDiagnosticContractFields`

Every blocked or failed realistic trial must produce a plain-text `copy_paste_block` with these fields:

- `diagnostic_version`
- `trial_id`
- `run_id`
- `agent_type`
- `viewport`
- `profile`
- `submitted_prompt`
- `parsed_intent`
- `task_type`
- `status`
- `reason_code`
- `missing_fields`
- `target_file`
- `target_candidates`
- `allowed_files`
- `forbidden_files`
- `route_or_endpoint`
- `provider`
- `model`
- `safety_state`
- `git_status_before`
- `git_status_after`
- `artifact_paths`
- `screenshot_paths`
- `trace_path`
- `next_recommended_action`
- `copy_paste_block`

Check run:

```bash
npx --no-install vitest run tests/ui-agent-trials/trial-result-schema.test.ts
```

Result:

- Test files: 1 passed.
- Tests: 2 passed.

GO / NO-GO:

- GO. Diagnostics contract fields exist and have a targeted schema test.

