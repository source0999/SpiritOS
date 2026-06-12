# Ultimate Agent Comparison Round 1

| Lane | Shell | Model Target | Model Observed | Execution Mode | Status | Score | Time | Files Changed | Preview | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| continue-qwen-bridged | continue | qwen2.5-coder:7b | qwen2.5-coder:7b | continue-tool-bridge | NO-GO | 3 | 78.141 | none | none | bridge=NO_TOOL_CALL; explanation-only |
| continue-default | continue | default | gemini-2.5-flash | continue-tool-bridge | GO | 10 | 12.007 | index.html | lanes/continue-default/workspace/index.html | bridge=NO_TOOL_CALL |
| continue-gpt4o-mini | continue | gpt-4o-mini | gpt-4o-mini | continue-tool-bridge | GO | 10 | 17.01 | agent-lab-experiments/.git.bak/HEAD, agent-lab-experiments/.git.bak/config, agent-lab-experiments/.git.bak/description, agent-lab-experiments/.git.bak/hooks/applypatch-msg.sample, agent-lab-experiments/.git.bak/hooks/commit-msg.sample, agent-lab-experiments/.git.bak/hooks/fsmonitor-watchman.sample, agent-lab-experiments/.git.bak/hooks/post-update.sample, agent-lab-experiments/.git.bak/hooks/pre-applypatch.sample, agent-lab-experiments/.git.bak/hooks/pre-commit.sample, agent-lab-experiments/.git.bak/hooks/pre-merge-commit.sample, agent-lab-experiments/.git.bak/hooks/pre-push.sample, agent-lab-experiments/.git.bak/hooks/pre-rebase.sample, agent-lab-experiments/.git.bak/hooks/pre-receive.sample, agent-lab-experiments/.git.bak/hooks/prepare-commit-msg.sample, agent-lab-experiments/.git.bak/hooks/push-to-checkout.sample, agent-lab-experiments/.git.bak/hooks/sendemail-validate.sample, agent-lab-experiments/.git.bak/hooks/update.sample, agent-lab-experiments/.git.bak/info/exclude, agent-lab-experiments/index.html | lanes/continue-gpt4o-mini/workspace/agent-lab-experiments/index.html | bridge=NO_TOOL_CALL |
| continue-hermes4 | continue | hermes4:latest | unknown | manual-pending | MANUAL_REQUIRED | None | 0.0 | none | none | hermes4 smoke over 90s or unavailable |
| continue-gemma | continue | gemma3n:e4b | gemma | continue-tool-bridge | BLOCKED | None | 2.005 | none | none | command failed |
| raw-ollama-qwen | raw | qwen2.5-coder:7b | qwen2.5-coder:7b | raw-output-harness-applied | GO | 10 | 15.192 | parsed-preview/index.html | lanes/raw-ollama-qwen/parsed-preview/index.html |  |
| raw-ollama-hermes4 | raw | hermes4:latest | unknown | manual-pending | MANUAL_REQUIRED | None | 0.0 | none | none | hermes4 smoke over 90s or unavailable |
| raw-ollama-gemma | raw | gemma3n:e4b | gemma3n:e4b | raw-output-harness-applied | GO | 10 | 104.477 | parsed-preview/index.html | lanes/raw-ollama-gemma/parsed-preview/index.html |  |
| raw-api-gpt4o-mini | raw-api | gpt-4o-mini | gpt-4o-mini | raw-output-harness-applied | GO | 10 | 14.456 | parsed-preview/index.html | lanes/raw-api-gpt4o-mini/parsed-preview/index.html |  |
| raw-api-strong | raw-api | gpt-4o | gpt-4o | raw-output-harness-applied | GO | 10 | 7.396 | parsed-preview/index.html | lanes/raw-api-strong/parsed-preview/index.html |  |
| source-proxy-qwen | source-proxy | qwen2.5-coder:7b | qwen2.5-coder:7b | source-proxy-advisory-only | BLOCKED | None | 11.418 | none | none | planner returned fallthrough |
| source-proxy-hermes4 | source-proxy | hermes4:latest | unknown | manual-pending | MANUAL_REQUIRED | None | 0.0 | none | none | hermes4 smoke over 90s or unavailable |
| source-proxy-gemma | source-proxy | gemma3n:e4b | gemma3n:e4b | source-proxy-advisory-only | BLOCKED | None | 3.832 | none | none | planner returned fallthrough |
| source-proxy-gpt4o-mini | source-proxy | gpt-4o-mini | gpt-4o-mini | source-proxy-advisory-only | BLOCKED | None | 3.835 | none | none | planner returned fallthrough |
| source-proxy-strong-api | source-proxy | gpt-4o | gpt-4o | source-proxy-advisory-only | BLOCKED | None | 3.855 | none | none | planner returned fallthrough |
| manual-terminal-qwen | manual | qwen2.5-coder:7b | unknown | manual-pending | MANUAL_REQUIRED | None | 0.0 | none | none | manual intake pending |
| manual-terminal-hermes4 | manual | hermes4 | unknown | manual-pending | MANUAL_REQUIRED | None | 0.0 | none | none | manual intake pending |
| manual-terminal-gemma | manual | gemma | unknown | manual-pending | MANUAL_REQUIRED | None | 0.0 | none | none | manual intake pending |
