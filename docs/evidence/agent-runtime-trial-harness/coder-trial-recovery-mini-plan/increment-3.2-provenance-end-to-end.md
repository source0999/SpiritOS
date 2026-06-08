# Increment 3.2 - Provenance End-to-End

Status: passed for focused Gate 3 paths.

Implemented/verified provenance fields:
- `generation_source`
- `diff_source`
- `model_output_classification`
- `raw_response_length`
- `raw_response_excerpt_safe`
- `scaffold_used`
- `scaffold_kind`
- `fallback_used`
- `fallback_kind`
- `parser_repair_used`
- `bounded_create_used`
- `known_scaffold_used`
- `generic_scaffold_used`
- `model_raw_diff_used`
- `generated_diff_by_backend`
- `trial_result_trust_status`

Focused tests:
- `test_prompt_packet_agent_lab_create_blocks_known_scaffold_in_live_trial_mode`
- `test_prompt_packet_calculator_create_blocks_fallback_after_invalid_model_tsx_in_live_trial`
- `test_prompt_packet_live_trial_prose_only_is_needs_fix_not_pass`
- `test_existing_file_prose_only_model_output_is_classified_unusable`

Results:
- Focused Coder provenance tests: passed.
- Context/Obsidian/self-status tests: passed.

Manual/self-check:
- Scaffold/fallback rows are blocked from PASS in live trial mode.
- Model prose-only output on an existing target is classified as unusable and does not become an approval-ready diff.
- Copied diagnostics now include a safe summary plus structured diagnostics.

Blocker:
- Full historical `source_proxy.tests.test_coding_regression_pack` is not green in this checkout. Failures include pre-existing/environment-sensitive expectations around model alias availability, timeout value drift, plan-id shape, and older fallback expectations. The focused Gate 3 tests pass.
