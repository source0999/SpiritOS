# Native Continue Qwen Smoke Closeout

Status: NO-GO
Score: 2/10
Model target: qwen2.5-coder:7b via isolated Continue ollama config
Model observed: qwen2.5-coder:7b configured; transcript did not print model name
Command: `timeout 300s /usr/bin/cn --config "/home/source/SpiritOS/docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/native-continue-qwen-smoke/continue-qwen-config.yaml" --auto -p "<exact prompt>"`
Elapsed: 13s
Native Continue created files: no
Files changed: none
Openable homepage: no
Launcher: http://10.0.0.186:8778/qwen.html
Preview: none
Anti-cheat: CLEAN
Bridge used: no
Source Proxy used: no
Parser/harness-applied files used: no
Real app touched: no

Conclusion: This does not prove native Continue can perform the task with Qwen. Qwen emitted raw Bash tool-call JSON, but native Continue did not execute it.
