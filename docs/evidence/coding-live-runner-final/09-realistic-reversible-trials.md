# Realistic Reversible Live Trials

Environment: `SPIRIT_PROJECT_PATH=/home/source/SpiritOS`, `SOURCE_PROXY_CODER_MODEL_ALIAS=local`, `SOURCE_PROXY_CODER_TIMEOUT_SECONDS=20`.

## Trial 1

- prompt: Make a new soccer scouting intelligence agent card for SpiritOS that can later connect to scouting data. Keep it simple, visible in the relevant scout/agent area, and make the change reversible.
- run_id: task_9a7446477c9a
- provider: local
- model: ollama_chat/hermes4:latest
- provider_call_made: True
- model_called_for_generation: ollama_chat/hermes4:latest
- selected_target: src/components/dashboard/ScoutIntelligenceCenter.tsx
- allowed_files: src/components/dashboard/ScoutIntelligenceCenter.tsx
- generated_diff_present: True
- preview_changed_files: src/components/dashboard/ScoutIntelligenceCenter.tsx
- applied_changed_files: src/components/dashboard/ScoutIntelligenceCenter.tsx
- disk_changed_files: src/components/dashboard/ScoutIntelligenceCenter.tsx
- checks_run: git diff --check
- result_label: PASS
- reversal_available: True
- reverse_diff_present: True
- reverted: True
- revert_verify_hashes_match: True
- failure_reason: none

## Trial 2

- prompt: Change the Source sidebar selected state toward a darker voidcore style while keeping the current light layout intact. Make the change reversible.
- run_id: task_935da7e1d910
- provider: local
- model: ollama_chat/hermes4:latest
- provider_call_made: True
- model_called_for_generation: ollama_chat/hermes4:latest
- selected_target: src/components/chat/ChatThreadListItem.tsx
- allowed_files: src/components/chat/ChatThreadListItem.tsx
- generated_diff_present: True
- preview_changed_files: src/components/chat/ChatThreadListItem.tsx
- applied_changed_files: src/components/chat/ChatThreadListItem.tsx
- disk_changed_files: src/components/chat/ChatThreadListItem.tsx
- checks_run: git diff --check
- result_label: PASS
- reversal_available: True
- reverse_diff_present: True
- reverted: True
- revert_verify_hashes_match: True
- failure_reason: none

## Trial 3

- prompt: Make the coding result card easier to understand when a live apply run fails by adding one clear next-step sentence and keeping diagnostics copy available. Make the change reversible.
- run_id: task_8330c33f3411
- provider: local
- model: ollama_chat/hermes4:latest
- provider_call_made: True
- model_called_for_generation: ollama_chat/hermes4:latest
- selected_target: src/components/coding/CodingCockpitShell.tsx
- allowed_files: src/components/coding/CodingCockpitShell.tsx
- generated_diff_present: True
- preview_changed_files: src/components/coding/CodingCockpitShell.tsx
- applied_changed_files: src/components/coding/CodingCockpitShell.tsx
- disk_changed_files: src/components/coding/CodingCockpitShell.tsx
- checks_run: git diff --check
- result_label: PASS
- reversal_available: True
- reverse_diff_present: True
- reverted: True
- revert_verify_hashes_match: True
- failure_reason: none

## Trial 4

- prompt: Add a small Oracle quick action for daily briefing preparation, wired as a visible UI option but not connected to external services yet. Make the change reversible.
- run_id: task_68548386c29e
- provider: local
- model: ollama_chat/hermes4:latest
- provider_call_made: True
- model_called_for_generation: ollama_chat/hermes4:latest
- selected_target: src/components/dashboard/OracleStagePanel.tsx
- allowed_files: src/components/dashboard/OracleStagePanel.tsx
- generated_diff_present: True
- preview_changed_files: src/components/dashboard/OracleStagePanel.tsx
- applied_changed_files: src/components/dashboard/OracleStagePanel.tsx
- disk_changed_files: src/components/dashboard/OracleStagePanel.tsx
- checks_run: git diff --check
- result_label: PASS
- reversal_available: True
- reverse_diff_present: True
- reverted: True
- revert_verify_hashes_match: True
- failure_reason: none
